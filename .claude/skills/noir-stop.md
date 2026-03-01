# /noir-stop

Stop all Neo-Mumbai Noir services.

## Steps
1. Run `./stop.sh` from project root
   - Stops the Gradio Docker container
   - Stops ComfyUI on the host
   - Leaves Ollama running (lightweight, shared by other projects)
