"""
Migration runner and JSON-to-DB importer.
Imports existing flat JSON files into the SQLite database.
"""
import json
from pathlib import Path

from db.connection import ConnectionManager
from db.utils import slugify, to_json
from db.repositories.story import StoryRepo
from db.repositories.character import CharacterRepo
from db.repositories.search_query import SearchQueryRepo
from db.repositories.scene import SceneRepo
from db.repositories.image_prompt import ImagePromptRepo


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def migrate_json_to_db():
    """Import existing JSON files into the database."""
    ConnectionManager.init_schema()

    imported = {}

    # 1. Import story.txt
    story_path = BASE_DIR / "story.txt"
    if story_path.exists():
        content = story_path.read_text().strip()
        if content:
            existing = StoryRepo.get_latest()
            if not existing:
                story_id = StoryRepo.create(content=content, title="Imported Story")
                imported["story"] = story_id
                print(f"  Imported story (id={story_id})")
            else:
                story_id = existing["id"]
                print(f"  Story already exists (id={story_id}), skipping")
        else:
            story_id = None
    else:
        story_id = None

    # 2. Import character_data.json
    char_path = BASE_DIR / "characters" / "character_data.json"
    char_id_map = {}  # name -> db id
    if char_path.exists():
        with open(char_path) as f:
            data = json.load(f)
        for char in data.get("characters", []):
            name = char.get("name", "Unknown")
            slug = slugify(name)
            existing = CharacterRepo.get_by_slug(slug, story_id)
            if existing:
                char_id_map[name] = existing["id"]
                print(f"  Character '{name}' already exists (id={existing['id']}), skipping")
                continue
            cid = CharacterRepo.create(
                story_id=story_id,
                name=name,
                age=char.get("age", ""),
                ethnicity=char.get("ethnicity", ""),
                gender=char.get("gender", ""),
                facial_features=char.get("facial_features"),
                clothing=char.get("clothing", ""),
                key_scenes=char.get("key_scenes"),
                emotions=char.get("emotions"),
            )
            char_id_map[name] = cid
            print(f"  Imported character '{name}' (id={cid})")
        imported["characters"] = len(char_id_map)

    # 3. Import search_queries.json
    query_path = BASE_DIR / "characters" / "search_queries.json"
    if query_path.exists() and char_id_map:
        with open(query_path) as f:
            queries = json.load(f)
        count = 0
        for q in queries:
            char_name = q.get("character", "")
            char_id = char_id_map.get(char_name)
            if not char_id:
                continue
            SearchQueryRepo.create(
                character_id=char_id,
                query_type=q.get("type", ""),
                query_text=q.get("query", ""),
                notes=q.get("notes", ""),
            )
            count += 1
        imported["search_queries"] = count
        print(f"  Imported {count} search queries")

    # 4. Import image_generation_prompts.json (scenes + prompts)
    prompts_path = BASE_DIR / "characters" / "image_generation_prompts.json"
    if prompts_path.exists() and char_id_map:
        with open(prompts_path) as f:
            prompts = json.load(f)
        scene_count = 0
        prompt_count = 0
        for key, pdata in prompts.items():
            char_name = pdata.get("character", "")
            char_id = char_id_map.get(char_name)
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
            scene_count += 1

            prompt_text = pdata.get("prompt", "")
            if prompt_text:
                ImagePromptRepo.create(
                    character_id=char_id,
                    scene_id=scene_id,
                    prompt_text=prompt_text,
                )
                prompt_count += 1

        imported["scenes"] = scene_count
        imported["image_prompts"] = prompt_count
        print(f"  Imported {scene_count} scenes, {prompt_count} image prompts")

    print(f"\nMigration complete: {imported}")
    return imported


if __name__ == "__main__":
    print("Running JSON -> DB migration...")
    migrate_json_to_db()
