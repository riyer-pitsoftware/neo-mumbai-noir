#!/usr/bin/env bash
echo "=== Stopping Neo-Mumbai Noir ==="

echo "[..] Stopping Gradio UI..."
docker compose down 2>/dev/null || true

echo "[..] Stopping ComfyUI..."
pkill -f "ComfyUI/main.py" 2>/dev/null && echo "[ok] ComfyUI stopped" || echo "[--] ComfyUI was not running"

echo "[..] Stopping FaceFusion server..."
pkill -f "facefusion_server.py" 2>/dev/null && echo "[ok] FaceFusion server stopped" || echo "[--] FaceFusion server was not running"

echo ""
echo "=== Stopped ==="
echo "(Ollama left running — it's lightweight)"
