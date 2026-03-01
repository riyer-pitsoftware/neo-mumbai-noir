# /noir-generate-images

Generate character images using ComfyUI.

## Steps
1. Ensure ComfyUI is running on the host (port 8188)
2. Run `python local_generation_comfy.py` for txt2img
3. Or `python img2img_generator_comfy.py <image> <prompt> [denoise]` for img2img

## Prerequisites
- ComfyUI running at localhost:8188 (or host.docker.internal:8188 in Docker)
- `characters/image_generation_prompts.json` exists (run `/extract-characters` + generate_prompts.py)
