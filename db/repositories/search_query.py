"""SearchQuery CRUD operations."""
from db.connection import ConnectionManager as CM


class SearchQueryRepo:

    @staticmethod
    def get_by_character(character_id: int) -> list:
        return CM.execute(
            "SELECT * FROM search_queries WHERE character_id = ? ORDER BY id",
            (character_id,),
        )

    @staticmethod
    def get_all() -> list:
        return CM.execute("SELECT * FROM search_queries ORDER BY id")

    @staticmethod
    def create(character_id: int, query_type: str, query_text: str,
               notes: str = "") -> int:
        return CM.execute_insert(
            """INSERT INTO search_queries
               (character_id, query_type, query_text, notes)
               VALUES (?, ?, ?, ?)""",
            (character_id, query_type, query_text, notes),
        )

    @staticmethod
    def mark_executed(query_id: int, results_count: int = 0):
        CM.execute(
            "UPDATE search_queries SET executed = 1, results_count = ? WHERE id = ?",
            (results_count, query_id),
        )

    @staticmethod
    def to_dict(row) -> dict:
        """Convert a sqlite3.Row to legacy dict format."""
        return {
            "character": "",  # filled by caller with character name
            "type": row["query_type"],
            "query": row["query_text"],
            "notes": row["notes"],
        }
