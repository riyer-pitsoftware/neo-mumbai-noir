#!/usr/bin/env python3
"""
Lightweight HTTP server wrapping FaceFusion CLI.
Runs on the host (alongside Ollama and ComfyUI) so FaceFusion
can use native GPU and its conda environment.

Usage:
    /opt/homebrew/Caskroom/miniconda/base/bin/python facefusion_server.py
"""
import json
import os
import subprocess
import tempfile
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

FACEFUSION_DIR = os.getenv("FACEFUSION_DIR", os.path.expanduser("~/code/facefusion"))
FACEFUSION_PYTHON = os.getenv(
    "FACEFUSION_PYTHON", "/opt/homebrew/Caskroom/miniconda/base/bin/python"
)
PORT = int(os.getenv("FACEFUSION_PORT", "7870"))
# Project dir — shared with Docker container via volume mount
PROJECT_DIR = os.getenv("PROJECT_DIR", os.path.dirname(os.path.abspath(__file__)))


class FaceFusionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/swap":
            self._handle_swap()
        else:
            self._respond(404, {"error": "not found"})

    def _handle_swap(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception as e:
            self._respond(400, {"error": f"bad request: {e}"})
            return

        source = body.get("source")  # path relative to project dir
        target = body.get("target")
        output = body.get("output")
        model = body.get("model", "inswapper_128")
        pixel_boost = body.get("pixel_boost", "512x512")
        enhancer = body.get("enhancer")  # optional face enhancer

        if not all([source, target, output]):
            self._respond(400, {"error": "source, target, and output are required"})
            return

        # Resolve paths relative to project directory
        source_path = os.path.join(PROJECT_DIR, source)
        target_path = os.path.join(PROJECT_DIR, target)
        output_path = os.path.join(PROJECT_DIR, output)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Build FaceFusion command
        processors = ["face_swapper"]
        if enhancer:
            processors.append("face_enhancer")

        cmd = [
            FACEFUSION_PYTHON,
            os.path.join(FACEFUSION_DIR, "facefusion.py"),
            "headless-run",
            "-s", source_path,
            "-t", target_path,
            "-o", output_path,
            "--processors", *processors,
            "--face-swapper-model", model,
            "--face-swapper-pixel-boost", pixel_boost,
            "--log-level", "info",
        ]

        if enhancer:
            cmd.extend(["--face-enhancer-model", enhancer])

        print(f"[facefusion] Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=FACEFUSION_DIR, timeout=300
        )

        if result.returncode == 0 and os.path.exists(output_path):
            self._respond(200, {
                "success": True,
                "output": output,
                "stdout": result.stdout[-500:] if result.stdout else "",
            })
        else:
            self._respond(500, {
                "success": False,
                "error": result.stderr[-1000:] if result.stderr else "unknown error",
                "stdout": result.stdout[-500:] if result.stdout else "",
                "returncode": result.returncode,
            })

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        print(f"[facefusion] {args[0]}")


def main():
    print(f"[facefusion] Server starting on port {PORT}")
    print(f"[facefusion] FaceFusion dir: {FACEFUSION_DIR}")
    print(f"[facefusion] Python: {FACEFUSION_PYTHON}")
    print(f"[facefusion] Project dir: {PROJECT_DIR}")
    server = HTTPServer(("0.0.0.0", PORT), FaceFusionHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[facefusion] Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
