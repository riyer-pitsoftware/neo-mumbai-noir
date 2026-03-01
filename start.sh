#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

echo "=== Neo-Mumbai Noir: Starting Services ==="

# --- Start Ollama if not running ---
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[ok] Ollama already running"
else
    echo "[..] Starting Ollama..."
    ollama serve > $LOGS_DIR/noir-ollama.log 2>&1 &
    for i in {1..15}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "[ok] Ollama started"
            break
        fi
        sleep 1
    done
fi

# --- Start ComfyUI if not running ---
if curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
    echo "[ok] ComfyUI already running"
else
    COMFYUI_DIR="${COMFYUI_DIR:-$HOME/code/ComfyUI}"
    if [ -f "$COMFYUI_DIR/main.py" ]; then
        echo "[..] Starting ComfyUI..."
        cd "$COMFYUI_DIR" && python main.py --listen 0.0.0.0 --port 8188 > $LOGS_DIR/noir-comfyui.log 2>&1 &
        cd - > /dev/null
        for i in {1..30}; do
            if curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
                echo "[ok] ComfyUI started"
                break
            fi
            if [ "$i" -eq 30 ]; then
                echo "[!!] ComfyUI failed to start (check $LOGS_DIR/noir-comfyui.log)"
            fi
            sleep 1
        done
    else
        echo "[!!] ComfyUI not found at $COMFYUI_DIR"
    fi
fi

# --- Start FaceFusion server if not running ---
FACEFUSION_PYTHON="${FACEFUSION_PYTHON:-/opt/homebrew/Caskroom/miniconda/base/bin/python}"
if curl -s http://localhost:7870/health > /dev/null 2>&1; then
    echo "[ok] FaceFusion server already running"
else
    if [ -f "$SCRIPT_DIR/facefusion_server.py" ]; then
        echo "[..] Starting FaceFusion server..."
        "$FACEFUSION_PYTHON" "$SCRIPT_DIR/facefusion_server.py" > "$LOGS_DIR/noir-facefusion.log" 2>&1 &
        for i in {1..10}; do
            if curl -s http://localhost:7870/health > /dev/null 2>&1; then
                echo "[ok] FaceFusion server started"
                break
            fi
            if [ "$i" -eq 10 ]; then
                echo "[!!] FaceFusion server failed to start (check $LOGS_DIR/noir-facefusion.log)"
            fi
            sleep 1
        done
    else
        echo "[!!] facefusion_server.py not found"
    fi
fi

# --- Start Docker stack ---
echo "[..] Starting Gradio UI..."
docker compose up --build -d

# Wait for Gradio
for i in {1..20}; do
    if curl -s http://localhost:7860/ > /dev/null 2>&1; then
        echo "[ok] Gradio UI ready"
        break
    fi
    sleep 1
done

echo ""
echo "=== All services running ==="
echo "  Gradio UI:   http://localhost:7860"
echo "  ComfyUI:     http://localhost:8188"
echo "  FaceFusion:  http://localhost:7870"
echo "  Ollama:      http://localhost:11434"
echo ""
echo "To stop: ./stop.sh"
