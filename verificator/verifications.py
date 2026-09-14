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


def get_student_progress(database_path, exercise_ids):
    database_path = Path(database_path)
    exercise_ids = tuple(exercise_ids)
    if not database_path.exists() or not exercise_ids:
        return []
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'verifications'"
        ).fetchone():
            return []
        placeholders = ", ".join("?" for _ in exercise_ids)
        rows = connection.execute(
            f"""
                SELECT student_name, exercise_id,
                       MAX(CASE WHEN succeeded = 1 THEN 1 ELSE 0 END) AS succeeded
                FROM verifications
                WHERE exercise_id IN ({placeholders})
                GROUP BY student_name, exercise_id
                ORDER BY student_name COLLATE NOCASE, student_name, exercise_id
            """,
            exercise_ids,
        ).fetchall()
        students = {}
        for row in rows:
            student = students.setdefault(
                row["student_name"],
                {"student_name": row["student_name"], "validated": set()},
            )
            if row["succeeded"] == 1:
                student["validated"].add(row["exercise_id"])
        return [
            {**student, "validated_count": len(student["validated"])}
            for student in students.values()
        ]
    finally:
        connection.close()


def save_verification(database_path, student_name, ip_address, exercise_id, source_code, succeeded):
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
                    succeeded INTEGER,
                    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(verifications)")}
            if "succeeded" not in columns:
                connection.execute("ALTER TABLE verifications ADD COLUMN succeeded INTEGER")
            connection.execute(
                """INSERT INTO verifications
                   (student_name, ip_address, exercise_id, source_code, succeeded)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_name, ip_address, exercise_id, source_code, succeeded),
            )
    finally:
        connection.close()
