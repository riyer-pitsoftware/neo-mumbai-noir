#!/usr/bin/env python3
"""
Simple web UI for the story-to-visual pipeline
"""
import gradio as gr
import subprocess
import json
from pathlib import Path

def process_story(story_text):
    """Process story through the pipeline"""
    
    # Save story
    with open("story.txt", "w") as f:
        f.write(story_text)
    
    # Run extraction
    result = subprocess.run(
        ["python", "extract_characters.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return f"Error: {result.stderr}", None
    
    # Load results
    with open("characters/character_data.json", "r") as f:
        char_data = json.load(f)
    
    with open("characters/search_queries.json", "r") as f:
        queries = json.load(f)
    
    summary = f"Found {len(char_data['characters'])} characters:\n\n"
    for char in char_data['characters']:
        summary += f"**{char['name']}**\n"
        summary += f"- Age: {char.get('age', 'N/A')}\n"
        summary += f"- Ethnicity: {char.get('ethnicity', 'N/A')}\n"
        summary += f"- Features: {', '.join(char.get('facial_features', []))}\n\n"
    
    return summary, json.dumps(queries, indent=2)

# Create Gradio interface
with gr.Blocks(title="Neo-Mumbai Noir Visual Pipeline") as demo:
    gr.Markdown("# 🎬 Story-to-Visual Pipeline")
    gr.Markdown("Transform your noir story into character references using FaceFusion + Ollama")
    
    with gr.Tab("Extract Characters"):
        story_input = gr.Textbox(
            label="Paste your story here",
            lines=20,
            placeholder="Paste 'The Monsoon Directive' or your own story..."
        )
        
        extract_btn = gr.Button("Extract Characters", variant="primary")
        
        char_summary = gr.Markdown(label="Character Summary")
        search_queries = gr.Textbox(label="Generated Search Queries", lines=10)
        
        extract_btn.click(
            fn=process_story,
            inputs=[story_input],
            outputs=[char_summary, search_queries]
        )
    
    with gr.Tab("Instructions"):
        gr.Markdown("""
        ## How to Use This Pipeline
        
        ### Step 1: Extract Characters
        1. Paste your story in the "Extract Characters" tab
        2. Click "Extract Characters"
        3. Review the character descriptions and search queries
        
        ### Step 2: Source Images (Manual)
        Use the generated search queries to find images:
        - **Pexels** (pexels.com) - free stock photos
        - **Unsplash** (unsplash.com) - free high-res photos
        - **Midjourney/DALL-E** - generate custom images
        
        Save images to the correct folders:
```
        characters/vijay_base_face.jpg
        characters/rukmini_base_face.jpg
        scenes/detective_weary.jpg
        scenes/woman_sad_sari.jpg
```
        
        ### Step 3: Run FaceFusion
```bash
        python face_fusion_pipeline.py
```
        
        ### Step 4: Review Outputs
        Check `outputs/` folder for your character gallery!
        """)

demo.launch()