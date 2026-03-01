"""Project CRUD operations."""
from db.connection import ConnectionManager as CM


class ProjectRepo:

    @staticmethod
    def get_active():
        """Return the active project row, or None."""
        rows = CM.execute(
            "SELECT * FROM projects WHERE is_active = 1 LIMIT 1"
        )
        return rows[0] if rows else None

    @staticmethod
    def create(name: str, description: str = "", user_id: int = 1) -> int:
        return CM.execute_insert(
            "INSERT INTO projects (user_id, name, description) VALUES (?, ?, ?)",
            (user_id, name, description),
        )

    @staticmethod
    def set_active(project_id: int):
        CM.execute("UPDATE projects SET is_active = 0")
        CM.execute("UPDATE projects SET is_active = 1 WHERE id = ?", (project_id,))
