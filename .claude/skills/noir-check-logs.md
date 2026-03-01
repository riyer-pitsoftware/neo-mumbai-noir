# /noir-check-logs

Check logs for all Neo-Mumbai Noir services.

## Steps

1. Check Gradio UI container logs:
   ```bash
   docker compose logs --since 5m --no-log-prefix 2>&1 | tail -50
   ```

2. Check ComfyUI host logs:
   ```bash
   tail -30 logs/noir-comfyui.log
   ```

3. Check Ollama is responding:
   ```bash
   curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print('Ollama OK -', len(d.get('models',[])), 'models')" 2>&1 || echo "Ollama: NOT RUNNING"
   ```

4. Check ComfyUI is responding:
   ```bash
   curl -s http://localhost:8188/system_stats | python3 -c "import sys,json; d=json.load(sys.stdin); print('ComfyUI OK -', d['devices'][0]['name'])" 2>&1 || echo "ComfyUI: NOT RUNNING"
   ```

5. Check FaceFusion server logs:
   ```bash
   tail -30 logs/noir-facefusion.log
   ```

6. Check FaceFusion server is responding:
   ```bash
   curl -s http://localhost:7870/health 2>&1 || echo "FaceFusion: NOT RUNNING"
   ```

7. Summarize: report any errors, tracebacks, or services that are down. If everything is clean, say so.

## Log file locations
- Gradio UI: `docker compose logs`
- ComfyUI: `logs/noir-comfyui.log`
- Ollama: `logs/noir-ollama.log`
- FaceFusion: `logs/noir-facefusion.log`

## When to use
- After any operation that might fail (generation, face swap, search)
- When the user reports an error in the UI
- To verify all services are healthy
