# Neo-Mumbai Noir — Product Requirements Document

## 1. Product Vision

**Neo-Mumbai Noir** is a local-first, open source pipeline that turns a written story into a visual storyboard with consistent character faces.

**Problem:** Creating a visual storyboard from a narrative requires juggling multiple disconnected tools — text analysis, image search, AI image generation, face swapping, and layout assembly. Each step loses context from the last, and maintaining visual consistency across characters is nearly impossible without manual effort.

**Solution:** A single Gradio-based interface that chains together LLM character extraction, stock photo search, Stable Diffusion image generation, FaceFusion face swapping, and storyboard assembly — all running locally on your hardware.

---

## 2. User Roles

### Writer / Storyteller
The primary user. Has a narrative (short story, screenplay, game script) and wants to see their characters visualized. Uses the pipeline left-to-right: paste story, extract characters, find reference images, generate scenes, and assemble a storyboard.

### Concept Artist
Uses AI generation as a rapid ideation tool. Leans heavily on img2img refinement and face swapping to iterate on character designs. May skip the story extraction step entirely and work directly with prompts.

### Producer / Director
Needs a storyboard for production planning — comics, games, animation, or film pre-visualization. Cares most about the Storyboard and Gallery tabs for reviewing and exporting visual sequences.

---

## 3. Core Features (5 Pillars)

### 3.1 Story Intelligence — Tab 1: Story & Characters

**What it does:** Paste any narrative text and the pipeline uses a local LLM (via Ollama) to extract structured character data — names, ages, ethnicities, genders, facial features, clothing, and emotions. It also generates optimized search queries for finding reference images.

**How to use it:**
1. Paste your story into the text box (or it auto-loads from `story.txt`)
2. Click **Extract Characters** — this sends the text to Ollama and takes 30-60 seconds
3. Review the character summary that appears below
4. Click **Validate Data** to check for any extraction issues

### 3.2 Reference Discovery — Tab 2: Image Search & Selection

**What it does:** Searches stock photo APIs (Pexels, Unsplash) for reference images matching each character's description. Smart Search mode uses the LLM to generate better search keywords from your scene prompts.

**How to use it:**
1. Select a character from the dropdown
2. Toggle **Smart Search** on for LLM-enhanced keyword extraction (recommended)
3. Click **Search** — results appear as a thumbnail gallery
4. Select images you want to keep
5. Choose a destination folder (characters or scenes) and click **Download Selected**

### 3.3 Image Generation — Tab 3: Image Generation (ComfyUI)

**What it does:** Generates new images using Stable Diffusion via ComfyUI. Supports both txt2img (from text prompts) and img2img (refining an existing image with a text prompt).

**How to use it:**
1. **txt2img:** Select a saved prompt from the dropdown or write your own, adjust steps and CFG, click **Generate**
2. **img2img:** Upload a base image, write a refinement prompt, adjust denoise strength (lower = closer to original), click **Generate**
3. Generated images are saved to your chosen folder and automatically available in the FaceFusion tab

### 3.4 Face Consistency — Tab 4: FaceFusion

**What it does:** Swaps a source face onto a target scene image, ensuring your characters look consistent across different scenes. Supports single swaps and batch mode.

**How to use it:**
1. Click **Refresh image lists** to load the latest images
2. Select a **Source Face** (a clear character portrait) and a **Target Scene**
3. Click **Swap Face** — processing takes 15-60 seconds
4. For batch mode: select one source face and multiple target scenes, then click **Batch Swap**

### 3.5 Storyboard & Gallery — Tabs 5-6

**What it does:** The Storyboard tab assembles a visual overview linking each character to their scenes and images. The Gallery tab provides a filterable view of all project images.

**How to use it:**
1. **Storyboard:** Click **Build Storyboard** to generate a character-by-character breakdown with linked images and scene descriptions
2. **Gallery:** Use the filter dropdown (All, Characters, Scenes, Outputs) and click **Refresh** to browse all project images

---

## 4. Getting Started

### Prerequisites

| Component | Purpose | Install |
|-----------|---------|---------|
| **Docker** | Runs the pipeline container | [docker.com](https://docs.docker.com/get-docker/) |
| **Ollama** | Local LLM for character extraction | [ollama.com](https://ollama.com/) — pull a model like `llama3.2` |
| **ComfyUI** | Stable Diffusion image generation | [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) |
| **FaceFusion** | Face swapping server | [github.com/facefusion/facefusion](https://github.com/facefusion/facefusion) |
| **API Keys** | Pexels and/or Unsplash for image search | Free tiers available — add to `.env` file |

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/neo-mumbai-noir.git
cd neo-mumbai-noir

# 2. Set up your .env file with API keys
cp .env.example .env
# Edit .env with your Pexels/Unsplash API keys

# 3. Start everything
./start.sh

# 4. Open the UI
open http://localhost:7860
```

### Walkthrough

Follow the tabs left-to-right for the standard workflow:

1. **Guide** — You are here. Read the docs.
2. **Story & Characters** — Paste your story, extract characters
3. **Image Search** — Find reference photos for each character
4. **Image Generation** — Generate scenes with Stable Diffusion
5. **FaceFusion** — Swap character faces for consistency
6. **Storyboard** — Review the assembled visual narrative
7. **Gallery** — Browse and manage all project images

---

## 5. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Host Machine                      │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  Ollama   │  │ ComfyUI  │  │   FaceFusion      │  │
│  │ :11434    │  │ :8188    │  │   :7870            │  │
│  └─────┬────┘  └────┬─────┘  └────────┬──────────┘  │
│        │             │                 │              │
│  ······│·············│·················│···········   │
│  :     │             │                 │         :   │
│  :  ┌──┴─────────────┴─────────────────┴──────┐ :   │
│  :  │         Docker Container                 │ :   │
│  :  │                                          │ :   │
│  :  │  ┌────────────────────────────────────┐  │ :   │
│  :  │  │     Gradio UI (:7860)              │  │ :   │
│  :  │  │                                    │  │ :   │
│  :  │  │  Guide │ Story │ Search │ Generate │  │ :   │
│  :  │  │  FaceFusion │ Storyboard │ Gallery │  │ :   │
│  :  │  └────────────────────────────────────┘  │ :   │
│  :  │                                          │ :   │
│  :  │  Python pipeline scripts                 │ :   │
│  :  │  extract_characters.py                   │ :   │
│  :  │  image_search.py / smart_image_search.py │ :   │
│  :  │  local_generation_comfy.py               │ :   │
│  :  │  face_fusion_pipeline.py                 │ :   │
│  :  └──────────────────────────────────────────┘ :   │
│  :                                               :   │
│  :  Volumes: ./characters, ./scenes, ./outputs   :   │
│  :...............................................:   │
│                                                      │
│  External APIs (BYOK):                               │
│  - Pexels API (image search)                         │
│  - Unsplash API (image search)                       │
└─────────────────────────────────────────────────────┘
```

---

## 6. Open Source Guardrails

### Ethical Use Policy

This tool generates and manipulates images, including face swapping. Users **must**:

- **Never** create deepfake content of real people without their explicit, informed consent
- **Never** generate CSAM or any exploitative imagery
- **Never** use generated content for impersonation, fraud, or harassment
- **Never** create non-consensual intimate imagery

Violations of these principles are not just policy violations — they may be criminal offenses in your jurisdiction.

### Model Attribution

This project builds on the work of several open source projects:

| Model / Project | License | Usage |
|----------------|---------|-------|
| [Stable Diffusion](https://github.com/Stability-AI/stablediffusion) | CreativeML Open RAIL-M | Image generation via ComfyUI |
| [FaceFusion](https://github.com/facefusion/facefusion) | See FaceFusion license | Face swapping |
| [Ollama](https://ollama.com/) | MIT | LLM inference server |
| LLM models (e.g., Llama) | Varies by model | Character extraction |

Users are responsible for complying with each upstream project's license terms.

### API Key Responsibility (BYOK)

This project uses a Bring Your Own Key model for external APIs:

- **Pexels** and **Unsplash** API keys are provided by the user
- Keys are stored locally in your `.env` file and never transmitted beyond the respective APIs
- Free API tiers have rate limits — respect them
- You are responsible for your API usage and any associated costs

### Content Moderation

This is a local-first tool with no centralized content moderation. **Users are solely responsible for all content they generate.** If you deploy this tool for others (e.g., in a team or public setting), implement your own content review process.

### FaceFusion License Compliance

FaceFusion has its own license terms that may impose additional restrictions on face-swapping functionality. Before using the FaceFusion integration, review the [FaceFusion license](https://github.com/facefusion/facefusion/blob/master/LICENSE.md) and ensure your use case is compliant.

---

## 7. Future Roadmap / Potential Paid Features

These features are not currently implemented but represent directions the project could grow — particularly if a hosted or commercial version is explored.

| Feature | Description |
|---------|-------------|
| **Cloud-hosted version** | No local GPU required — run the full pipeline on cloud infrastructure |
| **Team collaboration** | Shared projects with comments, approvals, and version history |
| **Video / animation generation** | Generate animated sequences from storyboard panels |
| **Voice synthesis** | AI-generated character dialogue audio from story text |
| **Custom model fine-tuning** | Train Stable Diffusion on a specific art style for consistent aesthetics |
| **Export formats** | PDF storyboard export, screenplay integration, asset packs for game engines |
| **Priority generation queue** | Faster generation for paid users in a hosted environment |
| **Pre-built character style libraries** | Curated character templates (noir, anime, realistic, etc.) ready to use |

---

*This document is available in-app under the Guide tab and at `docs/PRD.md` in the repository.*
