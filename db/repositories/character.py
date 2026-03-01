"""Character CRUD operations."""
import json
from db.connection import ConnectionManager as CM
from db.utils import slugify, to_json, from_json


class CharacterRepo:

    @staticmethod
    def get_by_story(story_id: int) -> list:
        return CM.execute(
            "SELECT * FROM characters WHERE story_id = ? ORDER BY id", (story_id,)
        )

    @staticmethod
    def get_by_id(character_id: int):
        rows = CM.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        return rows[0] if rows else None

    @staticmethod
    def get_by_slug(slug: str, story_id: int = None):
        if story_id is not None:
            rows = CM.execute(
                "SELECT * FROM characters WHERE slug = ? AND story_id = ?",
                (slug, story_id),
            )
        else:
            rows = CM.execute(
                "SELECT * FROM characters WHERE slug = ? ORDER BY id DESC LIMIT 1",
                (slug,),
            )
        return rows[0] if rows else None

    @staticmethod
    def get_all() -> list:
        return CM.execute("SELECT * FROM characters ORDER BY id")

    @staticmethod
    def create(story_id: int, name: str, age: str = "", ethnicity: str = "",
               gender: str = "", facial_features=None, clothing: str = "",
               key_scenes=None, emotions=None) -> int:
        slug = slugify(name)
        return CM.execute_insert(
            """INSERT OR REPLACE INTO characters
               (story_id, name, slug, age, ethnicity, gender,
                facial_features, clothing, key_scenes, emotions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (story_id, name, slug, age, ethnicity, gender,
             to_json(facial_features), clothing,
             to_json(key_scenes), to_json(emotions)),
        )

    @staticmethod
    def to_dict(row) -> dict:
        """Convert a sqlite3.Row to the legacy dict format."""
        return {
            "name": row["name"],
            "age": row["age"],
            "ethnicity": row["ethnicity"],
            "gender": row["gender"],
            "facial_features": from_json(row["facial_features"]),
            "clothing": row["clothing"],
            "key_scenes": from_json(row["key_scenes"]),
            "emotions": from_json(row["emotions"]),
        }
