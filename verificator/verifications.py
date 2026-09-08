import sqlite3
from pathlib import Path


def get_verifications(database_path):
    database_path = Path(database_path)
    if not database_path.exists():
        return []
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'verifications'"
        ).fetchone():
            return []
        rows = connection.execute(
            "SELECT * FROM verifications ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def save_verification(database_path, student_name, ip_address, exercise_id, source_code):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    exercise_id TEXT NOT NULL,
                    source_code TEXT NOT NULL,
                    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.execute(
                """INSERT INTO verifications
                   (student_name, ip_address, exercise_id, source_code)
                   VALUES (?, ?, ?, ?)""",
                (student_name, ip_address, exercise_id, source_code),
            )
    finally:
        connection.close()
