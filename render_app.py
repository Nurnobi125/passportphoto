"""Low-memory CPU background-removal API for small Render instances."""
import asyncio
import hmac
import os
from io import BytesIO

# Keep native CPU libraries from starting a thread pool per request.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from rembg import new_session, remove

API_TOKEN = os.getenv("PPS_API_TOKEN", "")
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 8_000_000
INFERENCE_SIDE = 1024
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

if len(API_TOKEN) < 24:
    raise RuntimeError("Set PPS_API_TOKEN to a private random value of at least 24 characters.")

app = FastAPI(title="Passport Photo CPU Background API", docs_url=None, redoc_url=None)
inference_lock = asyncio.Semaphore(1)
session = None


def _get_session():
    global session
    if session is None:
        session = new_session("u2netp", providers=["CPUExecutionProvider"])
    return session


def _process_image(data: bytes) -> bytes:
    try:
        with Image.open(BytesIO(data)) as opened:
            if opened.width * opened.height > MAX_PIXELS:
                raise HTTPException(status_code=413, detail="Image exceeds the 8 megapixel limit.")
            original = opened.convert("RGB")
    except HTTPException:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Could not decode this image.") from exc

    inference_image = original.copy()
    inference_image.thumbnail((INFERENCE_SIDE, INFERENCE_SIDE), Image.Resampling.LANCZOS)
    try:
        cutout = remove(inference_image, session=_get_session(), alpha_matting=False, post_process_mask=False)
        if not isinstance(cutout, Image.Image):
            cutout = Image.open(BytesIO(cutout))
        alpha = cutout.convert("RGBA").getchannel("A")
        if alpha.size != original.size:
            alpha = alpha.resize(original.size, Image.Resampling.LANCZOS)
        output = original.convert("RGBA")
        output.putalpha(alpha)
        result = BytesIO()
        output.save(result, format="PNG", optimize=True)
        return result.getvalue()
    finally:
        inference_image.close()
        original.close()


@app.get("/health")
def health():
    return {"status": "ok", "model": "u2netp", "device": "cpu"}


@app.post("/remove")
async def remove_background(
    file: UploadFile = File(...),
    x_api_token: str = Header(default=""),
):
    if not x_api_token or not hmac.compare_digest(x_api_token, API_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid API token.")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds the 12 MB limit.")
    async with inference_lock:
        result = await asyncio.to_thread(_process_image, data)
    return Response(content=result, media_type="image/png", headers={"Cache-Control": "no-store"})
