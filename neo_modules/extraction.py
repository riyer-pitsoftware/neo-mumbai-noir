"""Character extraction and search query generation.

Importable module for use by chrono-canvas workers or standalone via CLI.
"""

import asyncio
import json
import os
from typing import Awaitable, Callable

import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "host.docker.internal:11434")

EXTRACTION_PROMPT = """You are a character description extractor for visual reference generation.

Analyze this story and extract detailed visual descriptions for each main character.

STORY:
{story_text}

For each character, provide:
1. Name
2. Age/appearance
3. Ethnicity/features
4. Clothing style
5. Key facial features
6. Emotional states shown in story

Output ONLY valid JSON in this exact format:
{{
  "characters": [
    {{
      "name": "Character Name",
      "age": "age range",
      "ethnicity": "specific ethnicity",
      "gender": "male/female/other",
      "facial_features": ["feature1", "feature2"],
      "clothing": "description",
      "key_scenes": ["scene1", "scene2"],
      "emotions": ["emotion1", "emotion2"]
    }}
  ]
}}
"""


def _query_ollama_sync(prompt: str, model: str = "llama3.2") -> str:
    """Sync Ollama call for backward compatibility."""
    url = f"http://{OLLAMA_HOST}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json().get("response", "").strip()


def _parse_json_response(response: str) -> dict:
    """Extract JSON from an LLM response string."""
    json_start = response.find("{")
    json_end = response.rfind("}") + 1
    if json_start == -1 or json_end == 0:
        raise ValueError(f"No JSON found in LLM response: {response[:200]}")
    return json.loads(response[json_start:json_end])


async def extract_characters(
    story_text: str,
    llm_fn: Callable[[str], Awaitable[str]] | None = None,
) -> dict:
    """Extract character descriptions from story text.

    Args:
        story_text: The story to extract characters from.
        llm_fn: Optional async function ``(prompt) -> response_text``.
                If *None*, falls back to local Ollama.

    Returns:
        Dict with ``{"characters": [...]}``.
    """
    prompt = EXTRACTION_PROMPT.format(story_text=story_text)

    if llm_fn is not None:
        response = await llm_fn(prompt)
    else:
        response = await asyncio.to_thread(_query_ollama_sync, prompt)

    return _parse_json_response(response)


def generate_search_queries(character_data: dict) -> list[dict]:
    """Generate image search queries for each character.

    Pure function — no LLM or network calls.
    """
    queries: list[dict] = []

    for char in character_data["characters"]:
        ethnicity = char.get("ethnicity") or "person"
        gender = char.get("gender") or "person"
        age = char.get("age") or "adult"

        # Base portrait query
        base_query = f"{ethnicity} {gender} {age} portrait professional photo"
        queries.append({
            "character": char.get("name", "Unknown"),
            "type": "base_portrait",
            "query": base_query,
            "notes": f"Base face for {char.get('name', 'Unknown')}",
        })

        # Emotion-specific queries
        emotions = char.get("emotions") or []
        if isinstance(emotions, list):
            for emotion in emotions:
                if emotion:
                    emotion_query = f"{ethnicity} {gender} {emotion} expression portrait"
                    queries.append({
                        "character": char.get("name", "Unknown"),
                        "type": f"emotion_{emotion}",
                        "query": emotion_query,
                        "notes": f"{emotion} expression",
                    })

        # Clothing/style query
        clothing = char.get("clothing")
        if clothing:
            style_query = f"{ethnicity} {gender} wearing {clothing} full body photo"
            queries.append({
                "character": char.get("name", "Unknown"),
                "type": "full_body_style",
                "query": style_query,
                "notes": f"Full body with clothing: {clothing}",
            })

    return queries
