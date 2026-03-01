#!/usr/bin/env bash
set -euo pipefail

echo "=== Neo-Mumbai Noir Pipeline ==="
echo ""

echo "[1/3] Extracting characters from story..."
python extract_characters.py
if [ $? -ne 0 ]; then
    echo "ERROR: Character extraction failed."
    exit 1
fi

echo ""
echo "[2/3] Validating character data..."
python verify_output.py
if [ $? -ne 0 ]; then
    echo "ERROR: Validation failed. Fix character_data.json and retry."
    exit 2
fi

echo ""
echo "[3/3] Generating image prompts..."
python generate_prompts.py
if [ $? -ne 0 ]; then
    echo "ERROR: Prompt generation failed."
    exit 3
fi

echo ""
echo "=== Pipeline complete ==="
echo "Next steps:"
echo "  - Review characters/image_generation_prompts.json"
echo "  - Run image search or ComfyUI generation via the UI"
echo "  - Launch UI: docker-compose up"
