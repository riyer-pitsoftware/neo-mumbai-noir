#!/usr/bin/env python3
"""
img2img generation using ComfyUI API.
Uploads a base image, applies denoising-controlled KSampler, returns result.
"""
import json
import os
import time
import uuid
import io
import requests
import websocket
from pathlib import Path
from PIL import Image

COMFYUI_HOST = os.getenv("COMFYUI_HOST", "host.docker.internal:8188")


class ComfyUIImg2ImgGenerator:
    def __init__(self, server_address=None):
        self.server_address = server_address or COMFYUI_HOST
        self.client_id = str(uuid.uuid4())

    def upload_image(self, image_path):
        """Upload an image to ComfyUI's input directory."""
        url = f"http://{self.server_address}/upload/image"
        filename = Path(image_path).name

        with open(image_path, "rb") as f:
            files = {"image": (filename, f, "image/png")}
            response = requests.post(url, files=files)
            response.raise_for_status()

        result = response.json()
        return result.get("name", filename)

    def queue_prompt(self, workflow):
        """Queue a prompt workflow for generation."""
        payload = {"prompt": workflow, "client_id": self.client_id}
        response = requests.post(
            f"http://{self.server_address}/prompt",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    def wait_for_completion(self, prompt_id):
        """Wait for generation to complete via websocket."""
        ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
        try:
            ws = websocket.create_connection(ws_url)
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message["type"] == "executing":
                        data = message["data"]
                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            break
            ws.close()
            return True
        except Exception as e:
            print(f"Error waiting for completion: {e}")
            return False

    def get_output_images(self, prompt_id):
        """Retrieve generated images from completed prompt."""
        response = requests.get(f"http://{self.server_address}/history/{prompt_id}")
        response.raise_for_status()
        history = response.json()

        images = []
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            for node_id, node_output in outputs.items():
                for img_info in node_output.get("images", []):
                    img_url = (
                        f"http://{self.server_address}/view?"
                        f"filename={img_info['filename']}"
                        f"&subfolder={img_info.get('subfolder', '')}"
                        f"&type={img_info.get('type', 'output')}"
                    )
                    resp = requests.get(img_url)
                    images.append(Image.open(io.BytesIO(resp.content)))
        return images

    def generate_img2img(self, prompt, image_path, denoise=0.5, steps=6, cfg=1.5,
                         negative_prompt="", save_path=None):
        """
        Run img2img: load base image, encode, denoise with KSampler, decode, save.

        Args:
            prompt: Text prompt for generation
            image_path: Path to source image
            denoise: Denoising strength (0.3-0.8 recommended)
            steps: Number of sampling steps
            cfg: CFG scale
            negative_prompt: Negative prompt
            save_path: Optional path to save output
        """
        denoise = max(0.3, min(0.8, denoise))

        # Upload the source image
        uploaded_name = self.upload_image(image_path)
        print(f"   Uploaded: {uploaded_name}")

        workflow = {
            "1": {
                "inputs": {"image": uploaded_name, "upload": "image"},
                "class_type": "LoadImage",
            },
            "2": {
                "inputs": {"ckpt_name": "realvisxlV50_v50LightningBakedvae.safetensors"},
                "class_type": "CheckpointLoaderSimple",
            },
            "3": {
                "inputs": {"pixels": ["1", 0], "vae": ["2", 2]},
                "class_type": "VAEEncode",
            },
            "4": {
                "inputs": {
                    "text": prompt,
                    "clip": ["2", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "5": {
                "inputs": {
                    "text": negative_prompt or "blurry, bad quality, distorted, deformed",
                    "clip": ["2", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "6": {
                "inputs": {
                    "seed": int(time.time()),
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "dpmpp_sde",
                    "scheduler": "karras",
                    "denoise": denoise,
                    "model": ["2", 0],
                    "positive": ["4", 0],
                    "negative": ["5", 0],
                    "latent_image": ["3", 0],
                },
                "class_type": "KSampler",
            },
            "7": {
                "inputs": {"samples": ["6", 0], "vae": ["2", 2]},
                "class_type": "VAEDecode",
            },
            "8": {
                "inputs": {
                    "filename_prefix": "neo_mumbai_img2img",
                    "images": ["7", 0],
                },
                "class_type": "SaveImage",
            },
        }

        print(f"   Generating (denoise={denoise}, steps={steps})...")
        result = self.queue_prompt(workflow)
        if not result:
            return None

        if "prompt_id" not in result:
            print(f"   ComfyUI error: {result}")
            return None

        prompt_id = result["prompt_id"]
        if self.wait_for_completion(prompt_id):
            images = self.get_output_images(prompt_id)
            if images and save_path:
                images[0].save(save_path)
                print(f"   Saved to: {save_path}")
            return images
        return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python img2img_generator_comfy.py <image_path> <prompt> [denoise]")
        sys.exit(1)

    image_path = sys.argv[1]
    prompt = sys.argv[2]
    denoise = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5

    # Check ComfyUI
    try:
        requests.get(f"http://{COMFYUI_HOST}/system_stats", timeout=5)
    except Exception:
        print(f"ComfyUI not running at {COMFYUI_HOST}")
        sys.exit(1)

    gen = ComfyUIImg2ImgGenerator()
    output = Path("outputs") / f"img2img_{Path(image_path).stem}.png"
    gen.generate_img2img(prompt, image_path, denoise=denoise, save_path=str(output))
