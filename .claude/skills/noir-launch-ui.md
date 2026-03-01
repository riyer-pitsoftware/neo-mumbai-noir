# /noir-launch-ui

Launch the full Neo-Mumbai Noir stack (Ollama + ComfyUI + Gradio UI).

## Steps
1. Run `./start.sh` from project root
   - Starts Ollama if not running
   - Starts ComfyUI if not running
   - Builds and starts the Gradio Docker container
   - Waits for all services to be ready

2. Open http://localhost:7860 in browser

## To stop
- `./stop.sh`

## Without Docker
- `pip install -r requirements.txt && python unified_ui.py`
