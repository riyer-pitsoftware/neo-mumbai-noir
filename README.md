# Neo-Mumbai Noir

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A local-first, open source pipeline that turns a written story into a visual storyboard with consistent character faces.**

## Features

- **Story Intelligence** — LLM-powered character extraction from any narrative text
- **Reference Discovery** — AI-enhanced stock photo search (Pexels, Unsplash)
- **Image Generation** — txt2img and img2img via Stable Diffusion (ComfyUI)
- **Face Consistency** — FaceFusion face swapping for character consistency across scenes
- **Storyboard Assembly** — Visual narrative builder linking characters to scenes
- **Gallery** — Browse and manage all project images

## Quick Start

```bash
# Clone and configure
git clone https://github.com/YOUR_USERNAME/neo-mumbai-noir.git
cd neo-mumbai-noir
cp .env.example .env  # Add your Pexels/Unsplash API keys

# Start
./start.sh

# Open
open http://localhost:7860
```

## Prerequisites

| Component | Purpose |
|-----------|---------|
| [Docker](https://docs.docker.com/get-docker/) | Runs the pipeline container |
| [Ollama](https://ollama.com/) | Local LLM for character extraction |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | Stable Diffusion image generation |
| [FaceFusion](https://github.com/facefusion/facefusion) | Face swapping server |
| Pexels / Unsplash API keys | Stock photo search (free tiers available) |

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  Host Machine                     │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  Ollama   │  │ ComfyUI  │  │  FaceFusion    │  │
│  │  :11434   │  │  :8188   │  │  :7870         │  │
│  └─────┬────┘  └────┬─────┘  └───────┬────────┘  │
│        │             │                │            │
│  ┌─────┴─────────────┴────────────────┴─────────┐ │
│  │           Docker Container                    │ │
│  │  ┌────────────────────────────────────────┐   │ │
│  │  │         Gradio UI (:7860)              │   │ │
│  │  │  Guide │ Story │ Search │ Generate     │   │ │
│  │  │  FaceFusion │ Storyboard │ Gallery     │   │ │
│  │  └────────────────────────────────────────┘   │ │
│  │  Python pipeline + mounted volumes            │ │
│  └───────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

## Documentation

Full documentation is available in-app under the **Guide** tab (first tab when you open the UI), or in [`docs/PRD.md`](docs/PRD.md).

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a pull request

Be kind. This is a creative tool — contributions that expand what storytellers can do are especially welcome.

## License

[MIT](LICENSE)
