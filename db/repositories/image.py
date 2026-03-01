"""Image metadata CRUD operations."""
from db.connection import ConnectionManager as CM


class ImageRepo:

    @staticmethod
    def get_by_character(character_id: int) -> list:
        return CM.execute(
            "SELECT * FROM images WHERE character_id = ? ORDER BY id",
            (character_id,),
        )

    @staticmethod
    def get_by_type(image_type: str) -> list:
        return CM.execute(
            "SELECT * FROM images WHERE image_type = ? ORDER BY id",
            (image_type,),
        )

    @staticmethod
    def get_by_path(file_path: str):
        rows = CM.execute(
            "SELECT * FROM images WHERE file_path = ?", (file_path,)
        )
        return rows[0] if rows else None

    @staticmethod
    def get_all() -> list:
        return CM.execute("SELECT * FROM images ORDER BY created_at DESC")

    @staticmethod
    def create(file_path: str, file_name: str = "", image_type: str = "",
               character_id: int = None, scene_id: int = None,
               image_prompt_id: int = None, width: int = None,
               height: int = None, source: str = "",
               photographer: str = "", source_url: str = "") -> int:
        return CM.execute_insert(
            """INSERT OR IGNORE INTO images
               (character_id, scene_id, image_prompt_id, image_type,
                file_path, file_name, width, height, source,
                photographer, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character_id, scene_id, image_prompt_id, image_type,
             file_path, file_name, width, height, source,
             photographer, source_url),
        )

    @staticmethod
    def get_by_id(image_id: int):
        rows = CM.execute("SELECT * FROM images WHERE id = ?", (image_id,))
        return rows[0] if rows else None
