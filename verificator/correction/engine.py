import json
import subprocess
import sys
import tempfile
from pathlib import Path


class CorrectionEngine:
    def __init__(self, timeout=3):
        self.timeout = timeout

    def correct(self, exercise, source: bytes):
        with tempfile.TemporaryDirectory(prefix="verificator-") as directory:
            student_file = Path(directory) / "student.py"
            student_file.write_bytes(source)
            try:
                completed = subprocess.run(
                    [sys.executable, "-m", "verificator.correction.runner", str(student_file), exercise.id],
                    capture_output=True, text=True, timeout=self.timeout,
                    cwd=str(Path(__file__).parents[2]),
                )
            except subprocess.TimeoutExpired:
                return {"status": "timeout", "message": "Le délai maximal est dépassé.", "tests": []}
            if completed.returncode != 0:
                detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "Erreur inconnue."
                return {"status": "python_error", "message": detail, "tests": []}
            try:
                return json.loads(completed.stdout)
            except json.JSONDecodeError:
                return {"status": "python_error", "message": "La sortie du correcteur est invalide.", "tests": []}
