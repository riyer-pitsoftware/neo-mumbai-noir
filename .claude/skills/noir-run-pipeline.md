# /noir-run-pipeline

Run the full character extraction pipeline end-to-end.

## Steps
1. Run `bash run_pipeline.sh`
   - Extracts characters from story.txt
   - Validates character_data.json
   - Generates image prompts

## Prerequisites
- Ollama running on host (port 11434)
- story.txt exists in project root
