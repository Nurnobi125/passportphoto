---
title: Passport Photo Background API
emoji: 🪄
colorFrom: blue
colorTo: indigo
sdk: gradio
app_file: app.py
python_version: 3.12
---

# Passport Photo Background API

Private Gradio API for the Passport Photo Studio Pro desktop application. It
uses the small CPU-friendly `u2netp` model by default and returns a transparent PNG.

## Space setup

This app targets the private ZeroGPU Space `nurnobi/passport-photo-bg-api`.
In Space Settings → Variables and secrets, add a secret named `PPS_API_TOKEN`
with a random value of at least 24 characters. Never put that token in this
repository. Keep the Space private.

The desktop app also needs a Hugging Face fine-grained read token scoped to
this Space. Enter the Space ID, Hugging Face token, and matching `PPS_API_TOKEN`
under Background API Settings in Passport Photo Studio Pro. The app asks before
sending each photo. Use `nurnobi/passport-photo-bg-api` as the Space ID.

The first call can take longer while a sleeping Space starts and the model
downloads. The ZeroGPU runtime requires the API function to request GPU time;
the small `u2netp` model itself runs on CPU, so the GPU does not accelerate
processing even though each API call uses ZeroGPU quota. Processing is slower
than a dedicated GPU server. The Space can sleep when unused and take time to
wake. Free accounts have a limited daily ZeroGPU quota.
Gradio temporarily caches uploaded and result images and is configured to
delete that cache regularly. Do not use this Space for photos you cannot send
to Hugging Face.

For better fine hair detail, add `PPS_MODEL_NAME=u2net` as a Space variable.
This downloads a larger model and runs more slowly. No model guarantees perfect
edges for every photo.
