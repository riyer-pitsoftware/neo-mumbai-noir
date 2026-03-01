"""Story CRUD operations."""
from db.connection import ConnectionManager as CM


class StoryRepo:

    @staticmethod
    def get_latest(project_id: int = 1):
        """Return the most recent story for the project, or None."""
        rows = CM.execute(
            "SELECT * FROM stories WHERE project_id = ? ORDER BY id DESC LIMIT 1",
            (project_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def get_by_id(story_id: int):
        rows = CM.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
        return rows[0] if rows else None

    @staticmethod
    def create(content: str, title: str = "", project_id: int = 1,
               ollama_model: str = "llama3.2") -> int:
        return CM.execute_insert(
            "INSERT INTO stories (project_id, title, content, ollama_model) VALUES (?, ?, ?, ?)",
            (project_id, title, content, ollama_model),
        )

    @staticmethod
    def update_content(story_id: int, content: str):
        CM.execute("UPDATE stories SET content = ? WHERE id = ?", (content, story_id))
