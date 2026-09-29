# Low-memory Render CPU API

This deployment is separate from the Hugging Face ZeroGPU `app.py`. It uses a
small FastAPI server, CPU-only `u2netp`, one inference at a time, a 1024-pixel
inference image, an 8-megapixel source limit, and a 12 MB upload limit.

## Render settings

Create a Web Service from this repository, with **Root Directory** set to
`background_api`:

- Python version: pinned to `3.12.11` by `.python-version`
- Build command: `pip install -r requirements-render.txt`
- Start command: `uvicorn render_app:app --host 0.0.0.0 --port $PORT --workers 1 --limit-concurrency 2`
- Instance type: Free
- Environment variable: `PPS_API_TOKEN` set to a random secret with at least 24 characters

After deployment, the endpoint URL is the Render service URL, for example
`https://your-service.onrender.com`. `/health` reports readiness; `/remove`
accepts a multipart `file` and requires the `X-API-Token` header.

## Desktop app

Open Background API Settings and enter the Render service URL in the first
field, leave the Hugging Face token blank, and enter the same `PPS_API_TOKEN`
in the API token field. The desktop app confirms before sending each photo.

Free Render services sleep after 15 minutes without incoming requests, take
about a minute to wake, and have limited monthly instance hours. The 0.1 CPU /
512 MB free instance can be slow or run out of memory under load; this endpoint
reduces memory use but cannot guarantee all images fit. Photos over the limits
are rejected. Render free instances are intended for testing and hobby use.
