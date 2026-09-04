import json
import sqlite3
from pathlib import Path


QUESTION_COUNT = 15
CHOICES = ("A", "B", "C", "D")


def save_submission(database_path, student_name, answers):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS qcm_submissions (
                    id INTEGER PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    answers TEXT NOT NULL,
                    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.execute(
                "INSERT INTO qcm_submissions (student_name, answers) VALUES (?, ?)",
                (student_name, json.dumps(answers)),
            )
    finally:
        connection.close()
