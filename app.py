"""Private Gradio API for a Hugging Face ZeroGPU Space."""
import hmac
import os

import gradio as gr
from PIL import Image, UnidentifiedImageError
from rembg import new_session, remove
import spaces

MAX_PIXELS = 25_000_000
API_TOKEN = os.getenv("PPS_API_TOKEN", "")
MODEL_NAME = os.getenv("PPS_MODEL_NAME", "u2netp")
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

if len(API_TOKEN) < 24:
    raise RuntimeError("Add a random PPS_API_TOKEN secret with at least 24 characters in Space Settings.")

# u2netp is the smaller CPU-friendly model. Set PPS_MODEL_NAME=u2net in Space
# Settings for finer hair detail, at the cost of a larger download and slower runs.
SESSION = new_session(MODEL_NAME)


@spaces.GPU(duration=120)
def remove_background(image_path, api_token):
    if not api_token or not hmac.compare_digest(str(api_token), API_TOKEN):
        raise gr.Error("Invalid API token.")
    if not image_path:
        raise gr.Error("Choose an image first.")
    try:
        with Image.open(image_path) as source:
            if source.width * source.height > MAX_PIXELS:
                raise gr.Error("Image exceeds the 25 megapixel limit.")
            source = source.convert("RGB")
            result = remove(source, session=SESSION)
            if isinstance(result, Image.Image):
                return result.convert("RGBA")
            from io import BytesIO
            return Image.open(BytesIO(result)).convert("RGBA")
    except gr.Error:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise gr.Error("Could not decode this image.") from exc


demo = gr.Interface(
    fn=remove_background,
    inputs=[
        gr.Image(type="filepath", label="Photo"),
        gr.Textbox(type="password", label="Private API token"),
    ],
    outputs=gr.Image(type="pil", label="Transparent result"),
    title="Passport Photo Background API",
    description="Private, authenticated background removal. Images are temporarily cached by Gradio and regularly cleaned.",
    api_name="remove",
    flagging_mode="never",
    delete_cache=(60, 60),
    analytics_enabled=False,
)

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch(server_name="0.0.0.0", server_port=7860)
