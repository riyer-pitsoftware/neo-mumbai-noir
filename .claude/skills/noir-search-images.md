# /noir-search-images

Search stock photo APIs for character reference images.

## Steps
1. Run `python image_search.py` for basic search
2. Or `python smart_image_search.py <character>` for Ollama-enhanced search
3. Review results in `characters/image_search_results.json`
4. Run `python download_selected_images.py` to download

## Prerequisites
- `.env` must have `PEXELS_API_KEY` and/or `UNSPLASH_ACCESS_KEY`
- Run `/extract-characters` first
