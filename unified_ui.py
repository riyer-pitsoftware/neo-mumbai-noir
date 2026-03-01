#!/usr/bin/env python3
"""
Neo-Mumbai Noir: Unified Gradio UI
7-tab pipeline: Guide, Story, Search, Generate, FaceFusion, Storyboard, Gallery
"""
import json
import os
import re
import time
import glob as glob_mod
import tempfile
import requests
from pathlib import Path
from PIL import Image

import gradio as gr

from extract_characters import extract_characters, generate_search_queries, query_ollama
from verify_output import verify_character_data, print_results
from image_search import ImageSearcher
from smart_image_search import SmartImageSearcher
from local_generation_comfy import ComfyUIGenerator
from img2img_generator_comfy import ComfyUIImg2ImgGenerator
from face_fusion_pipeline import FaceFusionPipeline

import db

COMFYUI_HOST = os.getenv("COMFYUI_HOST", "host.docker.internal:8188")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "host.docker.internal:11434")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def list_images(directory):
    """List image files in a directory."""
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    files = []
    for ext in exts:
        files.extend(glob_mod.glob(str(Path(directory) / ext)))
    return sorted(files)


def slugify(name):
    """Turn a name into a filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# Delegate to db module (backward-compatible signatures)
load_story = db.load_story
load_character_data = db.load_character_data
load_prompts = db.load_prompts
character_names = db.character_names


# ---------------------------------------------------------------------------
# Tab 1: Story & Characters
# ---------------------------------------------------------------------------

def extract_characters_action(story_text, progress=gr.Progress(track_tqdm=False)):
    if not story_text.strip():
        return "Please paste a story first.", ""

    progress(0, desc="Saving story...")
    story_id = db.save_story(story_text)

    # Also keep JSON files for backward compatibility
    Path("characters").mkdir(exist_ok=True)

    progress(0.1, desc="Connecting to Ollama...")
    try:
        requests.get(f"http://{OLLAMA_HOST}/api/tags", timeout=5)
    except Exception:
        return "Error: Cannot reach Ollama. Is it running on the host?", ""

    progress(0.2, desc="Extracting characters (this takes 30-60s)...")
    try:
        characters = extract_characters(story_text)
    except SystemExit:
        return "Error: Could not parse Ollama response.", ""

    progress(0.7, desc="Saving character data...")
    with open("characters/character_data.json", "w") as f:
        json.dump(characters, f, indent=2)

    # Save to DB
    char_id_map = db.save_characters(characters, story_id)

    progress(0.8, desc="Generating search queries...")
    queries = generate_search_queries(characters)
    with open("characters/search_queries.json", "w") as f:
        json.dump(queries, f, indent=2)

    # Save to DB
    db.save_search_queries(queries, char_id_map)

    progress(0.95, desc="Building summary...")
    summary = f"Found {len(characters['characters'])} characters:\n\n"
    for char in characters["characters"]:
        summary += f"**{char.get('name', 'Unknown')}**\n"
        summary += f"- Age: {char.get('age', 'N/A')}\n"
        summary += f"- Ethnicity: {char.get('ethnicity', 'N/A')}\n"
        summary += f"- Gender: {char.get('gender', 'N/A')}\n"
        features = char.get("facial_features", [])
        if features:
            summary += f"- Features: {', '.join(features)}\n"
        summary += "\n"

    progress(1.0, desc="Done!")
    return summary, f"Generated {len(queries)} search queries."


def validate_action():
    results = verify_character_data()
    lines = []
    status = "PASS" if results["passed"] else "FAIL"
    lines.append(f"**Verification: {status}**\n")
    lines.append(f"Characters: {results['characters']}\n")
    if results["errors"]:
        lines.append(f"\n**Errors ({len(results['errors'])}):**")
        for e in results["errors"]:
            lines.append(f"- {e}")
    if results["warnings"]:
        lines.append(f"\n**Warnings ({len(results['warnings'])}):**")
        for w in results["warnings"]:
            lines.append(f"- {w}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tab 2: Image Search & Selection
# ---------------------------------------------------------------------------

def search_images_action(character_name, use_smart, progress=gr.Progress(track_tqdm=False)):
    if not character_name:
        return [], "Select a character first."

    all_results = []

    if use_smart:
        prompts = load_prompts()
        if not prompts:
            return [], "No prompts found. Run Extract Characters + generate_prompts.py first."

        searcher = SmartImageSearcher()
        matching_keys = [
            k for k, v in prompts.items()
            if character_name.lower() in v.get("character", "").lower()
            or character_name.lower().replace(" ", "_") in k.lower()
        ]
        total_scenes = len(matching_keys)
        if total_scenes == 0:
            return [], f"No scenes found for '{character_name}'."

        progress(0, desc=f"Smart searching {total_scenes} scenes for {character_name}...")
        scene_idx = 0
        for prompt_key, prompt_data in prompts.items():
            char_field = prompt_data.get("character", "").lower()
            name_lower = character_name.lower()
            if name_lower not in char_field and name_lower.replace(" ", "_") not in prompt_key.lower():
                continue

            scene = prompt_data.get("scene", "unknown")
            ai_prompt = prompt_data.get("prompt", "")
            scene_idx += 1
            progress(scene_idx / (total_scenes + 1),
                     desc=f"Scene {scene_idx}/{total_scenes}: extracting keywords for '{scene}'...")

            keywords = searcher.extract_keywords(ai_prompt)
            if not keywords:
                keywords = " ".join(ai_prompt.split()[:10])

            progress(scene_idx / (total_scenes + 1),
                     desc=f"Scene {scene_idx}/{total_scenes}: searching '{keywords[:40]}...'")
            scene_results = searcher.searcher.search_all(keywords, per_page=3)
            all_results.extend(scene_results)
    else:
        try:
            with open("characters/search_queries.json") as f:
                queries = json.load(f)
        except FileNotFoundError:
            return [], "Run Extract Characters first."

        searcher = ImageSearcher()
        matching = [q for q in queries if character_name.lower() in q.get("character", "").lower()]
        total_queries = len(matching)
        for i, q in enumerate(matching):
            progress((i + 1) / (total_queries + 1),
                     desc=f"Query {i+1}/{total_queries}: '{q['query'][:40]}...'")
            results = searcher.search_all(q["query"], per_page=2)
            all_results.extend(results)

    if not all_results:
        return [], "No results found. Check API keys in .env."

    with open("characters/image_search_results_ui.json", "w") as f:
        json.dump(all_results, f, indent=2)

    progress(0.85, desc=f"Downloading {len(all_results)} thumbnails...")
    thumbnails = []
    for i, r in enumerate(all_results):
        progress(0.85 + 0.15 * (i + 1) / len(all_results),
                 desc=f"Downloading thumbnail {i+1}/{len(all_results)}...")
        try:
            resp = requests.get(r["url"], timeout=10, stream=True)
            if resp.status_code == 200:
                tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, dir="characters")
                for chunk in resp.iter_content(8192):
                    tmp.write(chunk)
                tmp.close()
                thumbnails.append(tmp.name)
        except Exception:
            continue

    status = f"Found {len(all_results)} images, downloaded {len(thumbnails)} thumbnails."
    return thumbnails, status


def download_selected_action(selected_indices, character_name, save_to,
                             progress=gr.Progress(track_tqdm=False)):
    if not selected_indices:
        return "No images selected."
    try:
        with open("characters/image_search_results_ui.json") as f:
            all_results = json.load(f)
    except FileNotFoundError:
        return "No search results found. Search first."

    save_dir = Path(save_to)
    save_dir.mkdir(parents=True, exist_ok=True)
    searcher = ImageSearcher()
    char_slug = slugify(character_name)
    downloaded = 0
    total = len(selected_indices)

    char_db_id = db.get_character_id_by_name(character_name)

    for i, sel in enumerate(selected_indices):
        if i >= len(all_results):
            break
        progress((i + 1) / total, desc=f"Downloading {i+1}/{total}...")
        url = all_results[i]["url"]
        filename = f"{char_slug}_{save_to}_{i+1}.jpg"
        save_path = save_dir / filename
        if searcher.download_image(url, str(save_path)):
            downloaded += 1
            db.register_image(
                file_path=str(save_path),
                image_type="scene_reference" if save_to == "scenes" else "portrait",
                character_id=char_db_id,
                source=all_results[i].get("source", ""),
                photographer=all_results[i].get("photographer", ""),
                source_url=url,
            )

    return f"Downloaded {downloaded}/{total} images to {save_to}/."


# ---------------------------------------------------------------------------
# Tab 3: Image Generation (ComfyUI)
# ---------------------------------------------------------------------------

def check_comfyui():
    try:
        resp = requests.get(f"http://{COMFYUI_HOST}/system_stats", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def generate_txt2img_action(prompt, negative_prompt, steps, cfg, save_to, image_name,
                            progress=gr.Progress(track_tqdm=False)):
    progress(0, desc="Checking ComfyUI connection...")
    if not check_comfyui():
        return None, "ComfyUI not running. Start it on the host."
    if not prompt.strip():
        return None, "Enter a prompt."

    progress(0.1, desc="Queuing generation prompt...")
    gen = ComfyUIGenerator()

    save_dir = Path(save_to)
    save_dir.mkdir(parents=True, exist_ok=True)

    fname = slugify(image_name) if image_name.strip() else f"txt2img_{int(time.time())}"
    output_path = save_dir / f"{fname}.png"
    # Avoid overwriting
    if output_path.exists():
        output_path = save_dir / f"{fname}_{int(time.time())}.png"

    progress(0.2, desc="Generating image (this may take 5-15s)...")
    result = gen.generate_portrait(prompt, negative_prompt or "", str(output_path))

    if result:
        progress(1.0, desc="Done!")
        db.register_image(
            file_path=str(output_path),
            image_type="generated",
            source="comfyui",
        )
        return str(output_path), f"Saved to {output_path}"
    return None, "Generation failed."


def generate_img2img_action(prompt, negative_prompt, base_image, denoise, steps, cfg,
                            save_to, image_name, progress=gr.Progress(track_tqdm=False)):
    progress(0, desc="Checking ComfyUI connection...")
    if not check_comfyui():
        return None, "ComfyUI not running. Start it on the host."
    if not prompt.strip():
        return None, "Enter a prompt."
    if base_image is None:
        return None, "Upload a base image."

    progress(0.1, desc="Uploading base image to ComfyUI...")
    gen = ComfyUIImg2ImgGenerator()
    save_dir = Path(save_to)
    save_dir.mkdir(parents=True, exist_ok=True)

    fname = slugify(image_name) if image_name.strip() else f"img2img_{int(time.time())}"
    output_path = save_dir / f"{fname}.png"
    if output_path.exists():
        output_path = save_dir / f"{fname}_{int(time.time())}.png"

    progress(0.2, desc=f"Running img2img (denoise={denoise}, steps={int(steps)})...")
    images = gen.generate_img2img(
        prompt=prompt, image_path=base_image, denoise=denoise,
        steps=int(steps), cfg=cfg, negative_prompt=negative_prompt or "",
        save_path=str(output_path),
    )

    if images:
        progress(1.0, desc="Done!")
        db.register_image(
            file_path=str(output_path),
            image_type="generated",
            source="comfyui",
        )
        return str(output_path), f"Saved to {output_path}"
    return None, "img2img generation failed."


# ---------------------------------------------------------------------------
# Tab 4: FaceFusion
# ---------------------------------------------------------------------------

def swap_face_action(source_face, target_scene, progress=gr.Progress(track_tqdm=False)):
    if not source_face or not target_scene:
        return None, "Select both a source face and target scene."

    progress(0, desc="Connecting to FaceFusion server...")
    pipeline = FaceFusionPipeline()
    if not pipeline.is_available():
        return None, ("FaceFusion server not reachable at "
                       f"{pipeline.server_address}. "
                       "Make sure it's running on the host (./start.sh).")

    output_dir = Path("outputs") / "faceswap"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"swap_{Path(source_face).stem}_{Path(target_scene).stem}.png"

    progress(0.2, desc="Swapping face (this may take 15-60s)...")
    success = pipeline.swap_face(source_face, target_scene, str(output_path))

    if success:
        progress(1.0, desc="Done!")
        db.register_image(
            file_path=str(output_path),
            image_type="faceswap",
            source="facefusion",
        )
        return str(output_path), "Face swap complete!"
    return None, "Face swap failed. Check FaceFusion server logs."


def batch_swap_action(source_face, target_scenes, progress=gr.Progress(track_tqdm=False)):
    if not source_face or not target_scenes:
        return "Select a source face and at least one target scene."

    pipeline = FaceFusionPipeline()
    if not pipeline.is_available():
        return (f"FaceFusion server not reachable at {pipeline.server_address}. "
                "Make sure it's running on the host (./start.sh).")

    output_dir = Path("outputs") / "faceswap"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(target_scenes)
    for i, scene_path in enumerate(target_scenes):
        progress((i + 1) / total, desc=f"Swapping face {i+1}/{total}: {Path(scene_path).name}...")
        output_path = output_dir / f"swap_{Path(source_face).stem}_{Path(scene_path).stem}.png"
        success = pipeline.swap_face(source_face, scene_path, str(output_path))
        status = "OK" if success else "FAIL"
        results.append(f"{status}: {Path(scene_path).name}")

    return "\n".join(results)


# ---------------------------------------------------------------------------
# Tab 5: Storyboard
# ---------------------------------------------------------------------------

def build_storyboard():
    """Build a markdown storyboard tying characters to their images."""
    data = load_character_data()
    prompts = load_prompts()
    if not data:
        return "No character data found. Run Extract Characters first."

    md = ""
    for char in data.get("characters", []):
        name = char.get("name", "Unknown")
        slug = slugify(name)
        md += f"## {name}\n"
        md += f"**Age:** {char.get('age', 'N/A')} | "
        md += f"**Ethnicity:** {char.get('ethnicity', 'N/A')} | "
        md += f"**Gender:** {char.get('gender', 'N/A')}\n\n"

        clothing = char.get("clothing")
        if clothing:
            md += f"**Style:** {clothing}\n\n"

        emotions = char.get("emotions", [])
        if emotions:
            md += f"**Emotions:** {', '.join(emotions)}\n\n"

        # Find images for this character
        char_images = []
        for d in ["characters", "scenes", "outputs", "outputs/faceswap"]:
            for img in list_images(d):
                if slug in Path(img).stem.lower() or name.lower().split()[0] in Path(img).stem.lower():
                    char_images.append(img)

        if char_images:
            md += f"**Images ({len(char_images)}):** "
            md += ", ".join(f"`{Path(p).name}`" for p in char_images[:10])
            if len(char_images) > 10:
                md += f" ... and {len(char_images) - 10} more"
            md += "\n\n"
        else:
            md += "**Images:** None yet - generate or search for images\n\n"

        # Show scenes from prompts
        scene_count = 0
        for key, pdata in prompts.items():
            if name.lower() in pdata.get("character", "").lower():
                scene_count += 1
                scene = pdata.get("scene", "unknown")
                desc = pdata.get("scene_description", "")
                md += f"- **{scene}**: {desc[:100]}{'...' if len(desc) > 100 else ''}\n"
        if scene_count == 0:
            md += "- No scenes defined\n"

        md += "\n---\n\n"

    return md


def get_storyboard_images():
    """Get all character-related images for storyboard gallery."""
    data = load_character_data()
    if not data:
        return []

    images = []
    for char in data.get("characters", []):
        name = char.get("name", "Unknown")
        slug = slugify(name)
        for d in ["characters", "scenes", "outputs", "outputs/faceswap"]:
            for img in list_images(d):
                stem = Path(img).stem.lower()
                if slug in stem or name.lower().split()[0] in stem:
                    images.append((img, f"{name}: {Path(img).name}"))

    return images


# ---------------------------------------------------------------------------
# Tab 6: Gallery
# ---------------------------------------------------------------------------

def refresh_gallery(filter_type):
    dirs = {
        "All": ["outputs", "characters", "scenes"],
        "Characters": ["characters"],
        "Scenes": ["scenes"],
        "Outputs": ["outputs"],
    }
    scan_dirs = dirs.get(filter_type, ["outputs", "characters", "scenes"])
    images = []
    for d in scan_dirs:
        images.extend(list_images(d))
        for subdir in Path(d).glob("*/"):
            if subdir.is_dir():
                images.extend(list_images(str(subdir)))
    return images


# ---------------------------------------------------------------------------
# Build Gradio UI
# ---------------------------------------------------------------------------

def load_guide_markdown():
    """Load the PRD markdown for the Guide tab."""
    try:
        return Path("docs/PRD.md").read_text()
    except FileNotFoundError:
        return "*Guide not found. Expected at `docs/PRD.md`.*"


def create_ui():
    with gr.Blocks(title="Neo-Mumbai Noir Pipeline") as demo:
        gr.Markdown("# Neo-Mumbai Noir: Visual Pipeline")
        gr.Markdown("Story-to-character pipeline with Ollama, ComfyUI, and FaceFusion")

        # Shared state: track last generated image path for FaceFusion tab
        last_generated = gr.State(value=None)

        # ---- Guide Tab (first position) ----
        with gr.Tab("Guide"):
            gr.Markdown(load_guide_markdown())

        # ---- Tab 1: Story & Characters ----
        with gr.Tab("Story & Characters"):
            story_box = gr.Textbox(label="Story", value=load_story(), lines=15, interactive=True)
            with gr.Row():
                extract_btn = gr.Button("Extract Characters", variant="primary")
                validate_btn = gr.Button("Validate Data")

            char_summary = gr.Markdown(label="Characters")
            query_status = gr.Textbox(label="Search Queries Status", interactive=False)
            validation_result = gr.Markdown(label="Validation")

            extract_btn.click(
                fn=extract_characters_action,
                inputs=[story_box],
                outputs=[char_summary, query_status],
            )
            validate_btn.click(fn=validate_action, outputs=[validation_result])

        # ---- Tab 2: Image Search & Selection ----
        with gr.Tab("Image Search & Selection"):
            with gr.Row():
                char_dropdown = gr.Dropdown(choices=character_names(), label="Character", interactive=True)
                smart_toggle = gr.Checkbox(label="Smart Search (Ollama keywords)", value=True)
                search_btn = gr.Button("Search", variant="primary")

            search_status = gr.Textbox(label="Status", interactive=False)
            search_gallery = gr.Gallery(label="Search Results (click to select)", columns=4, height=400)

            with gr.Row():
                save_to_dropdown = gr.Dropdown(choices=["characters", "scenes"], value="characters", label="Save to")
                download_btn = gr.Button("Download Selected")
            download_status = gr.Textbox(label="Download Status", interactive=False)

            search_btn.click(
                fn=search_images_action,
                inputs=[char_dropdown, smart_toggle],
                outputs=[search_gallery, search_status],
            )
            download_btn.click(
                fn=download_selected_action,
                inputs=[search_gallery, char_dropdown, save_to_dropdown],
                outputs=[download_status],
            )

        # ---- Tab 3: Image Generation (ComfyUI) ----
        with gr.Tab("Image Generation (ComfyUI)"):
            prompts_data = load_prompts()
            prompt_keys = ["-- Select prompt --"] + list(prompts_data.keys()) if prompts_data else []

            def load_prompt_action(key):
                if key and key != "-- Select prompt --" and prompts_data and key in prompts_data:
                    p = prompts_data[key]
                    # Auto-fill name from the prompt key
                    return p.get("prompt", ""), key.replace("-- Select prompt --", "")
                return "", ""

            gr.Markdown("### txt2img")
            with gr.Row():
                with gr.Column():
                    prompt_selector = gr.Dropdown(
                        choices=prompt_keys,
                        value="-- Select prompt --" if prompt_keys else None,
                        label="Load Saved Prompt",
                    )
                    prompt_box = gr.Textbox(label="Prompt", lines=5)
                    neg_prompt_box = gr.Textbox(
                        label="Negative Prompt",
                        value="blurry, bad quality, distorted, deformed", lines=2,
                    )
                    txt2img_name = gr.Textbox(
                        label="Image Name",
                        placeholder="e.g. vijay_rain_scene",
                        info="Used as filename. Leave blank for auto-name.",
                    )
                    with gr.Row():
                        steps_slider = gr.Slider(4, 20, value=6, step=1, label="Steps")
                        cfg_slider = gr.Slider(1.0, 5.0, value=1.5, step=0.5, label="CFG")
                    txt2img_save = gr.Dropdown(
                        choices=["characters", "scenes", "outputs"], value="characters", label="Save to",
                    )
                    txt2img_btn = gr.Button("Generate (txt2img)", variant="primary")
                with gr.Column():
                    txt2img_output = gr.Image(label="Generated Image", type="filepath")
                    txt2img_status = gr.Textbox(label="Status", interactive=False)

            prompt_selector.change(
                fn=load_prompt_action, inputs=[prompt_selector],
                outputs=[prompt_box, txt2img_name],
            )

            def txt2img_and_track(*args):
                img, status = generate_txt2img_action(*args)
                return img, status, img

            txt2img_btn.click(
                fn=txt2img_and_track,
                inputs=[prompt_box, neg_prompt_box, steps_slider, cfg_slider, txt2img_save, txt2img_name],
                outputs=[txt2img_output, txt2img_status, last_generated],
            )

            gr.Markdown("---")
            gr.Markdown("### img2img")
            with gr.Row():
                with gr.Column():
                    i2i_prompt_selector = gr.Dropdown(
                        choices=prompt_keys,
                        value="-- Select prompt --" if prompt_keys else None,
                        label="Load Saved Prompt",
                    )
                    i2i_prompt = gr.Textbox(label="Prompt", lines=3)
                    i2i_neg = gr.Textbox(
                        label="Negative Prompt",
                        value="blurry, bad quality, distorted, deformed", lines=2,
                    )
                    i2i_image = gr.Image(label="Base Image", type="filepath")
                    i2i_name = gr.Textbox(
                        label="Image Name",
                        placeholder="e.g. vijay_interrogation_refined",
                        info="Used as filename. Leave blank for auto-name.",
                    )
                    with gr.Row():
                        denoise_slider = gr.Slider(0.3, 0.8, value=0.5, step=0.05, label="Denoise")
                        i2i_steps = gr.Slider(4, 20, value=6, step=1, label="Steps")
                        i2i_cfg = gr.Slider(1.0, 5.0, value=1.5, step=0.5, label="CFG")
                    i2i_save = gr.Dropdown(
                        choices=["scenes", "characters", "outputs"], value="scenes", label="Save to",
                    )
                    img2img_btn = gr.Button("Generate (img2img)", variant="primary")
                with gr.Column():
                    img2img_output = gr.Image(label="Generated Image", type="filepath")
                    img2img_status = gr.Textbox(label="Status", interactive=False)

            def i2i_load_prompt(key):
                if key and key != "-- Select prompt --" and prompts_data and key in prompts_data:
                    return prompts_data[key].get("prompt", ""), key
                return "", ""

            i2i_prompt_selector.change(
                fn=i2i_load_prompt, inputs=[i2i_prompt_selector],
                outputs=[i2i_prompt, i2i_name],
            )

            def img2img_and_track(*args):
                img, status = generate_img2img_action(*args)
                return img, status, img

            img2img_btn.click(
                fn=img2img_and_track,
                inputs=[i2i_prompt, i2i_neg, i2i_image, denoise_slider, i2i_steps, i2i_cfg, i2i_save, i2i_name],
                outputs=[img2img_output, img2img_status, last_generated],
            )

        # ---- Tab 4: FaceFusion ----
        with gr.Tab("FaceFusion"):
            def refresh_face_choices():
                faces = list_images("characters")
                scenes = list_images("scenes")
                return (
                    gr.update(choices=faces),
                    gr.update(choices=scenes),
                    gr.update(choices=faces),
                    gr.update(choices=scenes),
                )

            gr.Markdown("### Latest Generated Image")
            latest_img_preview = gr.Image(label="Latest from Generation tab", type="filepath", interactive=False)

            # Update preview when tab is selected via last_generated state
            def show_latest(last_gen):
                return last_gen

            refresh_faces_btn = gr.Button("Refresh image lists")

            gr.Markdown("---")
            with gr.Row():
                with gr.Column():
                    face_dropdown = gr.Dropdown(
                        choices=list_images("characters"), label="Source Face", interactive=True,
                    )
                    face_preview = gr.Image(label="Source Face Preview", type="filepath")
                with gr.Column():
                    scene_dropdown = gr.Dropdown(
                        choices=list_images("scenes"), label="Target Scene", interactive=True,
                    )
                    scene_preview = gr.Image(label="Target Scene Preview", type="filepath")

            face_dropdown.change(fn=lambda x: x, inputs=[face_dropdown], outputs=[face_preview])
            scene_dropdown.change(fn=lambda x: x, inputs=[scene_dropdown], outputs=[scene_preview])

            swap_btn = gr.Button("Swap Face", variant="primary")
            with gr.Row():
                swap_output = gr.Image(label="Result", type="filepath")
                swap_status = gr.Textbox(label="Status", interactive=False)

            swap_btn.click(
                fn=swap_face_action,
                inputs=[face_dropdown, scene_dropdown],
                outputs=[swap_output, swap_status],
            )

            gr.Markdown("---")
            gr.Markdown("### Batch Mode")
            batch_face = gr.Dropdown(choices=list_images("characters"), label="Source Face")
            batch_scenes = gr.CheckboxGroup(choices=list_images("scenes"), label="Target Scenes")
            batch_btn = gr.Button("Batch Swap")
            batch_result = gr.Textbox(label="Batch Results", lines=10, interactive=False)

            batch_btn.click(
                fn=batch_swap_action,
                inputs=[batch_face, batch_scenes],
                outputs=[batch_result],
            )

            refresh_faces_btn.click(
                fn=refresh_face_choices,
                outputs=[face_dropdown, scene_dropdown, batch_face, batch_scenes],
            )

            # Show latest generated image when refresh is clicked
            refresh_faces_btn.click(
                fn=show_latest,
                inputs=[last_generated],
                outputs=[latest_img_preview],
            )

        # ---- Tab 5: Storyboard ----
        with gr.Tab("Storyboard"):
            gr.Markdown("### Character Storyboard")
            gr.Markdown("Links characters from the story to their images and scenes.")
            storyboard_refresh = gr.Button("Build Storyboard", variant="primary")
            storyboard_md = gr.Markdown()
            storyboard_gallery = gr.Gallery(
                label="Character Images",
                columns=4,
                height=500,
            )

            def refresh_storyboard():
                return build_storyboard(), get_storyboard_images()

            storyboard_refresh.click(
                fn=refresh_storyboard,
                outputs=[storyboard_md, storyboard_gallery],
            )

        # ---- Tab 6: Gallery ----
        with gr.Tab("Gallery"):
            with gr.Row():
                filter_dropdown = gr.Dropdown(
                    choices=["All", "Characters", "Scenes", "Outputs"],
                    value="All", label="Filter",
                )
                refresh_btn = gr.Button("Refresh")

            gallery_display = gr.Gallery(label="Project Images", columns=4, height=600)

            refresh_btn.click(fn=refresh_gallery, inputs=[filter_dropdown], outputs=[gallery_display])
            demo.load(fn=lambda: refresh_gallery("All"), outputs=[gallery_display])

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
