#!/usr/bin/env python3
"""
Automate FaceFusion operations for character generation.
Calls the FaceFusion HTTP server running on the host.
"""
import json
import os
import requests
from pathlib import Path

FACEFUSION_HOST = os.getenv("FACEFUSION_HOST", "host.docker.internal:7870")


class FaceFusionPipeline:
    def __init__(self, server_address=None):
        self.server_address = server_address or FACEFUSION_HOST
        self.base_url = f"http://{self.server_address}"

    def is_available(self):
        """Check if FaceFusion server is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def swap_face(self, source_face, target_image, output_path,
                  model="inswapper_128", pixel_boost="512x512", enhancer=None):
        """
        Run FaceFusion to swap faces via HTTP server.

        Args:
            source_face: Path to the face image (relative to project dir or absolute)
            target_image: Path to the target/scene image
            output_path: Where to save the result
            model: Face swapper model name
            pixel_boost: Upscale resolution
            enhancer: Optional face enhancer model (e.g. 'gfpgan_1.4')
        """
        print(f"🎭 Swapping face: {Path(source_face).name} -> {Path(target_image).name}")

        payload = {
            "source": str(source_face),
            "target": str(target_image),
            "output": str(output_path),
            "model": model,
            "pixel_boost": pixel_boost,
        }
        if enhancer:
            payload["enhancer"] = enhancer

        try:
            resp = requests.post(
                f"{self.base_url}/swap",
                json=payload,
                timeout=300,
            )
            data = resp.json()
        except requests.ConnectionError:
            print("❌ FaceFusion server not reachable. Is it running on the host?")
            print("   Start it with: ./start.sh")
            return False
        except Exception as e:
            print(f"❌ Error calling FaceFusion server: {e}")
            return False

        if data.get("success"):
            print(f"✅ Saved to: {output_path}")
            return True
        else:
            print(f"❌ FaceFusion error: {data.get('error', 'unknown')}")
            return False

    def create_character_variants(self, character_name, base_face, emotion_bodies):
        """
        Create multiple emotion variants for a character.
        """
        output_dir = Path("outputs") / character_name.lower().replace(" ", "_")
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}
        for emotion, body_image in emotion_bodies.items():
            output_file = output_dir / f"{emotion}.png"
            success = self.swap_face(
                source_face=base_face,
                target_image=body_image,
                output_path=str(output_file),
            )
            results[emotion] = {
                "success": success,
                "path": str(output_file) if success else None,
            }
        return results


def load_character_config():
    """Load character configuration"""
    with open("characters/character_data.json", "r") as f:
        return json.load(f)


if __name__ == "__main__":
    pipeline = FaceFusionPipeline()
    if pipeline.is_available():
        print("✅ FaceFusion server is running")
    else:
        print("❌ FaceFusion server not reachable")
