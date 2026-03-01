"""ImagePrompt CRUD operations."""
from db.connection import ConnectionManager as CM


class ImagePromptRepo:

    @staticmethod
    def get_by_character(character_id: int) -> list:
        return CM.execute(
            "SELECT * FROM image_prompts WHERE character_id = ? ORDER BY id",
            (character_id,),
        )

    @staticmethod
    def get_by_scene(scene_id: int) -> list:
        return CM.execute(
            "SELECT * FROM image_prompts WHERE scene_id = ? ORDER BY id",
            (scene_id,),
        )

    @staticmethod
    def get_all() -> list:
        return CM.execute("SELECT * FROM image_prompts ORDER BY id")

    @staticmethod
    def create(character_id: int, prompt_text: str, scene_id: int = None,
               negative_prompt: str = "", ollama_model: str = "llama3.2") -> int:
        return CM.execute_insert(
            """INSERT INTO image_prompts
               (scene_id, character_id, prompt_text, negative_prompt, ollama_model)
               VALUES (?, ?, ?, ?, ?)""",
            (scene_id, character_id, prompt_text, negative_prompt, ollama_model),
        )

    @staticmethod
    def get_by_id(prompt_id: int):
        rows = CM.execute("SELECT * FROM image_prompts WHERE id = ?", (prompt_id,))
        return rows[0] if rows else None
