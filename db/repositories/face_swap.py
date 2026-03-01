"""FaceSwap CRUD operations."""
from db.connection import ConnectionManager as CM


class FaceSwapRepo:

    @staticmethod
    def create(source_image_id: int, target_image_id: int) -> int:
        return CM.execute_insert(
            """INSERT INTO face_swaps (source_image_id, target_image_id, status)
               VALUES (?, ?, 'pending')""",
            (source_image_id, target_image_id),
        )

    @staticmethod
    def complete(swap_id: int, result_image_id: int):
        CM.execute(
            """UPDATE face_swaps
               SET result_image_id = ?, status = 'completed',
                   completed_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (result_image_id, swap_id),
        )

    @staticmethod
    def fail(swap_id: int):
        CM.execute(
            "UPDATE face_swaps SET status = 'failed' WHERE id = ?", (swap_id,),
        )

    @staticmethod
    def get_all() -> list:
        return CM.execute("SELECT * FROM face_swaps ORDER BY created_at DESC")

    @staticmethod
    def get_by_id(swap_id: int):
        rows = CM.execute("SELECT * FROM face_swaps WHERE id = ?", (swap_id,))
        return rows[0] if rows else None
