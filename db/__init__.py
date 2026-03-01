"""
Neo-Mumbai Noir database public API.

Backward-compatible functions (same signatures and return types as the old
JSON-loading helpers in unified_ui.py):
    load_story()          -> str
    load_character_data() -> {"characters": [...]} dict or None
    load_prompts()        -> {"slug_scene": {...}} dict
    character_names()     -> ["Name1", "Name2"] list

New functions for DB writes:
    save_story(text)
    save_character(char_dict, story_id)
    save_search_queries(queries_list, char_id_map)
    save_prompts(prompts_dict, char_id_map)
    register_image(file_path, **kwargs) -> int
    create_face_swap(source_image_id, target_image_id) -> int
    complete_face_swap(swap_id, result_path) -> int
    get_active_project() -> dict or None
"""
from pathlib import Path

from db.connection import ConnectionManager
from db.utils import slugify, from_json
from db.repositories.project import ProjectRepo
from db.repositories.story import StoryRepo
from db.repositories.character import CharacterRepo
from db.repositories.search_query import SearchQueryRepo
from db.repositories.scene import SceneRepo
from db.repositories.image_prompt import ImagePromptRepo
from db.repositories.image import ImageRepo
from db.repositories.face_swap import FaceSwapRepo

# Auto-initialize schema on first import
ConnectionManager.init_schema()


# ---------------------------------------------------------------------------
# Backward-compatible read API
# ---------------------------------------------------------------------------

def load_story() -> str:
    """Return the latest story content, falling back to story.txt."""
    row = StoryRepo.get_latest()
    if row:
        return row["content"]
    # Fallback to flat file
    try:
        return Path("story.txt").read_text()
    except FileNotFoundError:
        return ""


def load_character_data():
    """Return {"characters": [...]} dict matching the old JSON format, or None."""
    row = StoryRepo.get_latest()
    if row:
        chars = CharacterRepo.get_by_story(row["id"])
    else:
        chars = CharacterRepo.get_all()
    if not chars:
        return None
    return {"characters": [CharacterRepo.to_dict(c) for c in chars]}


def load_prompts() -> dict:
    """Return {"slug_scene": {character, scene, scene_description, prompt}} dict."""
    prompts = ImagePromptRepo.get_all()
    result = {}
    for p in prompts:
        char_row = CharacterRepo.get_by_id(p["character_id"]) if p["character_id"] else None
        scene_row = SceneRepo.get_by_id(p["scene_id"]) if p["scene_id"] else None

        char_name = char_row["name"] if char_row else "unknown"
        scene_key = scene_row["scene_key"] if scene_row else "unknown"
        scene_desc = scene_row["description"] if scene_row else ""

        key = f"{slugify(char_name)}_{scene_key}"
        result[key] = {
            "character": char_name,
            "scene": scene_key,
            "scene_description": scene_desc,
            "prompt": p["prompt_text"],
        }
    return result


def character_names() -> list:
    """Return list of character name strings."""
    data = load_character_data()
    if not data:
        return []
    return [c.get("name", "Unknown") for c in data.get("characters", [])]


# ---------------------------------------------------------------------------
# Write API
# ---------------------------------------------------------------------------

def save_story(content: str, title: str = "", ollama_model: str = "llama3.2") -> int:
    """Save story text to DB. Returns story_id."""
    # Also write to story.txt for backward compat
    Path("story.txt").write_text(content)
    existing = StoryRepo.get_latest()
    if existing:
        StoryRepo.update_content(existing["id"], content)
        return existing["id"]
    return StoryRepo.create(content=content, title=title, ollama_model=ollama_model)


def save_character(char_dict: dict, story_id: int = None) -> int:
    """Save a single character dict to DB. Returns character_id.

    char_dict keys: name, age, ethnicity, gender, facial_features, clothing,
                    key_scenes, emotions
    """
    if story_id is None:
        row = StoryRepo.get_latest()
        story_id = row["id"] if row else None
    return CharacterRepo.create(
        story_id=story_id,
        name=char_dict.get("name", "Unknown"),
        age=char_dict.get("age", ""),
        ethnicity=char_dict.get("ethnicity", ""),
        gender=char_dict.get("gender", ""),
        facial_features=char_dict.get("facial_features"),
        clothing=char_dict.get("clothing", ""),
        key_scenes=char_dict.get("key_scenes"),
        emotions=char_dict.get("emotions"),
    )


def save_characters(characters_dict: dict, story_id: int = None) -> dict:
    """Save all characters from {"characters": [...]} dict.
    Returns {name: character_id} map.
    """
    id_map = {}
    for char in characters_dict.get("characters", []):
        cid = save_character(char, story_id)
        id_map[char.get("name", "Unknown")] = cid
    return id_map


def save_search_queries(queries: list, char_id_map: dict = None):
    """Save search queries list. If char_id_map is None, looks up by name."""
    for q in queries:
        char_name = q.get("character", "")
        if char_id_map and char_name in char_id_map:
            char_id = char_id_map[char_name]
        else:
            row = CharacterRepo.get_by_slug(slugify(char_name))
            char_id = row["id"] if row else None
        if char_id:
            SearchQueryRepo.create(
                character_id=char_id,
                query_type=q.get("type", ""),
                query_text=q.get("query", ""),
                notes=q.get("notes", ""),
            )


def save_prompts(prompts_dict: dict, char_id_map: dict = None):
    """Save prompts from {"slug_scene": {character, scene, scene_description, prompt}} dict."""
    for key, pdata in prompts_dict.items():
        char_name = pdata.get("character", "")
        if char_id_map and char_name in char_id_map:
            char_id = char_id_map[char_name]
        else:
            row = CharacterRepo.get_by_slug(slugify(char_name))
            char_id = row["id"] if row else None
        if not char_id:
            continue

        scene_key = pdata.get("scene", key)
        scene_desc = pdata.get("scene_description", "")
        scene_id = SceneRepo.create(
            character_id=char_id,
            scene_key=scene_key,
            scene_name=scene_key,
            description=scene_desc,
        )
        prompt_text = pdata.get("prompt", "")
        if prompt_text:
            ImagePromptRepo.create(
                character_id=char_id,
                scene_id=scene_id,
                prompt_text=prompt_text,
            )


def register_image(file_path: str, image_type: str = "", character_id: int = None,
                    scene_id: int = None, image_prompt_id: int = None,
                    source: str = "", photographer: str = "",
                    source_url: str = "", width: int = None,
                    height: int = None) -> int:
    """Register an image file in the database. Returns image_id."""
    file_name = Path(file_path).name
    return ImageRepo.create(
        file_path=file_path,
        file_name=file_name,
        image_type=image_type,
        character_id=character_id,
        scene_id=scene_id,
        image_prompt_id=image_prompt_id,
        width=width,
        height=height,
        source=source,
        photographer=photographer,
        source_url=source_url,
    )


def create_face_swap(source_image_id: int, target_image_id: int) -> int:
    """Create a face swap record. Returns swap_id."""
    return FaceSwapRepo.create(source_image_id, target_image_id)


def complete_face_swap(swap_id: int, result_path: str, **image_kwargs) -> int:
    """Mark a face swap as completed and register the result image."""
    img_id = register_image(result_path, image_type="faceswap", source="facefusion",
                            **image_kwargs)
    FaceSwapRepo.complete(swap_id, img_id)
    return img_id


def get_active_project():
    """Return the active project row dict, or None."""
    row = ProjectRepo.get_active()
    if row:
        return dict(row)
    return None


def get_character_id_by_name(name: str):
    """Look up a character ID by name. Returns int or None."""
    slug = slugify(name)
    row = CharacterRepo.get_by_slug(slug)
    return row["id"] if row else None
