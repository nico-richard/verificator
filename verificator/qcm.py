import json
import sqlite3
from pathlib import Path


QUESTION_COUNT = 15
CHOICES = ("A", "B", "C", "D")
QCM_KEYS = json.loads(Path(__file__).with_name("qcm_keys.json").read_text(encoding="utf-8"))


def grade_answers(questionnaire, version, answers):
    key = QCM_KEYS[questionnaire][version]
    return sum(answers.get(str(i), answers.get(i)) == correct
               for i, correct in enumerate(key, 1) if correct is not None), sum(
                   correct is not None for correct in key)



def get_submissions(database_path):
    database_path = Path(database_path)
    if not database_path.exists():
        return []
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'qcm_submissions'"
        ).fetchone():
            return []
        rows = connection.execute(
            "SELECT * FROM qcm_submissions ORDER BY id DESC"
        ).fetchall()
        return [{**dict(row), "answers": json.loads(row["answers"])} for row in rows]
    finally:
        connection.close()


def save_submission(database_path, student_name, answers, questionnaire=None, version=None):
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
            columns = {row[1] for row in connection.execute("PRAGMA table_info(qcm_submissions)")}
            for column, kind in (("questionnaire", "TEXT"), ("version", "TEXT"), ("score", "INTEGER"), ("total", "INTEGER")):
                if column not in columns:
                    connection.execute(f"ALTER TABLE qcm_submissions ADD COLUMN {column} {kind}")
            score, total = grade_answers(questionnaire, version, answers) if questionnaire else (None, None)
            connection.execute(
                "INSERT INTO qcm_submissions (student_name, answers, questionnaire, version, score, total) VALUES (?, ?, ?, ?, ?, ?)",
                (student_name, json.dumps(answers), questionnaire, version, score, total),
            )
    finally:
        connection.close()
