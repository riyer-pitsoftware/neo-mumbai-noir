"""Scene CRUD operations."""
from db.connection import ConnectionManager as CM


class SceneRepo:

    @staticmethod
    def get_by_character(character_id: int) -> list:
        return CM.execute(
            "SELECT * FROM scenes WHERE character_id = ? ORDER BY id",
            (character_id,),
        )

    @staticmethod
    def get_by_key(character_id: int, scene_key: str):
        rows = CM.execute(
            "SELECT * FROM scenes WHERE character_id = ? AND scene_key = ?",
            (character_id, scene_key),
        )
        return rows[0] if rows else None

    @staticmethod
    def create(character_id: int, scene_key: str, scene_name: str = "",
               description: str = "") -> int:
        return CM.execute_insert(
            """INSERT OR REPLACE INTO scenes
               (character_id, scene_key, scene_name, description)
               VALUES (?, ?, ?, ?)""",
            (character_id, scene_key, scene_name or scene_key, description),
        )

    @staticmethod
    def get_by_id(scene_id: int):
        rows = CM.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
        return rows[0] if rows else None
