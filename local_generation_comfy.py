#!/usr/bin/env python3
"""
Local image generation using ComfyUI API
"""
import json
import os
import requests
import time
import websocket
import uuid
from pathlib import Path
from PIL import Image
import io

COMFYUI_HOST = os.getenv("COMFYUI_HOST", "host.docker.internal:8188")

class ComfyUIGenerator:
    def __init__(self, server_address=None):
        self.server_address = server_address or COMFYUI_HOST
        self.client_id = str(uuid.uuid4())
    
    def queue_prompt(self, prompt_workflow):
        """Queue a prompt for generation"""
        p = {"prompt": prompt_workflow, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        
        try:
            response = requests.post(
                f"http://{self.server_address}/prompt",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            return response.json()
        except Exception as e:
            print(f"Error queuing prompt: {e}")
            return None
    
    def get_image(self, filename, subfolder, folder_type):
        """Get generated image"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = requests.utils.quote(json.dumps(data))
        
        try:
            response = requests.get(
                f"http://{self.server_address}/view?{url_values}"
            )
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            print(f"Error getting image: {e}")
            return None
    
    def wait_for_completion(self, prompt_id):
        """Wait for generation to complete"""
        ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
        
        try:
            ws = websocket.create_connection(ws_url)
            
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break  # Execution complete
            
            ws.close()
            return True
        except Exception as e:
            print(f"Error waiting for completion: {e}")
            return False
    
    def get_output_images(self, prompt_id):
        """Retrieve generated images from completed prompt via API."""
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

    def generate_portrait(self, prompt, negative_prompt="", save_path=None):
        """Generate a portrait using ComfyUI"""

        # Basic SDXL workflow for portrait generation
        workflow = {
            "3": {
                "inputs": {
                    "seed": int(time.time()),
                    "steps": 6,
                    "cfg": 1.5,
                    "sampler_name": "dpmpp_sde",
                    "scheduler": "karras",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "ckpt_name": "realvisxlV50_v50LightningBakedvae.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "width": 832,
                    "height": 1216,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": negative_prompt or "blurry, bad quality, distorted, deformed",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {
                    "filename_prefix": "neo_mumbai",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage"
            }
        }
        
        print(f"   ⏳ Generating image...")
        result = self.queue_prompt(workflow)
        
        if not result:
            return None

        if 'prompt_id' not in result:
            print(f"   ComfyUI error: {result}")
            return False

        prompt_id = result['prompt_id']
        
        if self.wait_for_completion(prompt_id):
            images = self.get_output_images(prompt_id)
            if images and save_path:
                images[0].save(save_path)
                print(f"   ✅ Saved to: {save_path}")
            elif images:
                print(f"   ✅ Generation complete!")
            return images if images else True

        return False


def generate_all_characters():
    """Generate images for all characters using local SD"""
    
    # Check if ComfyUI is running
    try:
        response = requests.get(f"http://{COMFYUI_HOST}/system_stats")
        if response.status_code != 200:
            print("❌ ComfyUI not running!")
            print("Start it with: cd ~/projects/ComfyUI && python main.py")
            return
    except:
        print("❌ ComfyUI not running!")
        print("Start it with: cd ~/projects/ComfyUI && python main.py")
        return
    
    # Load prompts
    try:
        with open("characters/image_generation_prompts.json", "r") as f:
            prompts = json.load(f)
    except FileNotFoundError:
        print("❌ Run generate_prompts.py first!")
        return
    
    generator = ComfyUIGenerator()
    
    print("\n" + "="*70)
    print("LOCAL IMAGE GENERATION (COMFYUI)")
    print("="*70 + "\n")
    
    for prompt_key, prompt_data in prompts.items():
        character = prompt_data.get('character', 'Unknown')
        scene = prompt_data.get('scene', 'unknown')
        prompt = prompt_data.get('prompt', '')
        
        print(f"\n🎨 {character} - {scene}")
        print(f"   Prompt: {prompt[:80]}...")
        
        success = generator.generate_portrait(prompt)
        
        if success:
            print(f"   💾 Saved to ComfyUI/output/")
        else:
            print(f"   ❌ Generation failed")
        
        time.sleep(2)  # Brief pause between generations
    
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
    print("="*70)
    print("\nImages saved to: ~/projects/ComfyUI/output/")
    print("Next: Move selected images to characters/ and scenes/")


if __name__ == "__main__":
    generate_all_characters()