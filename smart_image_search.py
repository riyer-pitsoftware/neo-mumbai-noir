#!/usr/bin/env python3
"""
Smart image search: use Ollama to extract visual keywords from AI prompts,
then feed keywords into ImageSearcher for better stock matches.
"""
import json
import os
import requests
import sys
from image_search import ImageSearcher

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "host.docker.internal:11434")


class SmartImageSearcher:
    """Wraps ImageSearcher with Ollama-powered keyword extraction."""

    def __init__(self):
        self.searcher = ImageSearcher()
        self.ollama_host = OLLAMA_HOST

    def extract_keywords(self, ai_prompt, model="llama3.2"):
        """Use Ollama to extract concise visual search keywords from a verbose AI prompt."""
        extraction_prompt = f"""Extract 3-5 concise stock photo search keywords from this image description.
Focus on: ethnicity, gender, age, clothing, emotion, setting.
Output ONLY a comma-separated list of keywords, nothing else.

Description: {ai_prompt}"""

        url = f"http://{self.ollama_host}/api/generate"
        payload = {"model": model, "prompt": extraction_prompt, "stream": False}

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            keywords = response.json().get("response", "").strip()
            # Clean up: remove quotes, extra whitespace
            keywords = keywords.strip('"\'')
            return keywords
        except Exception as e:
            print(f"Keyword extraction failed: {e}")
            return None

    def smart_search(self, ai_prompt, per_page=5, model="llama3.2"):
        """Extract keywords from an AI prompt and search for matching stock photos."""
        print(f"   Extracting search keywords from prompt...")
        keywords = self.extract_keywords(ai_prompt, model)

        if not keywords:
            print("   Falling back to first 10 words of prompt...")
            keywords = " ".join(ai_prompt.split()[:10])

        print(f"   Keywords: {keywords}")
        return self.searcher.search_all(keywords, per_page)

    def search_for_character(self, character_name, prompts_data, per_page=3):
        """Search for all scenes of a character using smart keyword extraction."""
        results = {}

        for prompt_key, prompt_data in prompts_data.items():
            char_field = prompt_data.get("character", "").lower()
            name_lower = character_name.lower()
            if name_lower not in char_field and name_lower.replace(" ", "_") not in prompt_key.lower():
                continue

            scene = prompt_data.get("scene", "unknown")
            ai_prompt = prompt_data.get("prompt", "")

            print(f"\n   Scene: {scene}")
            scene_results = self.smart_search(ai_prompt, per_page)
            results[scene] = scene_results
            print(f"   Found {len(scene_results)} images")

        return results


if __name__ == "__main__":
    # Load prompts
    try:
        with open("characters/image_generation_prompts.json") as f:
            prompts = json.load(f)
    except FileNotFoundError:
        print("Run generate_prompts.py first!")
        sys.exit(1)

    searcher = SmartImageSearcher()

    character = sys.argv[1] if len(sys.argv) > 1 else "vijay"
    print(f"\nSmart searching for: {character}")
    results = searcher.search_for_character(character, prompts)

    # Save results
    output_file = f"characters/smart_search_{character}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")
