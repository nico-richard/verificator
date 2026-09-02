from io import BytesIO

from verificator import create_app
from verificator.correction.engine import CorrectionEngine
from verificator.exercises import EXERCISES


def run(source):
    return CorrectionEngine(timeout=2).correct(EXERCISES["s2-moyenne"], source.encode())


def test_correct_submission():
    result = run("def moyenne(valeurs): return sum(valeurs) / len(valeurs)")
    assert result["status"] == "ok"
    assert all(test["passed"] for test in result["tests"])


def test_missing_function():
    result = run("x = 1")
    assert result["tests"][0]["message"] == "Fonction absente."


def test_python_error():
    result = run("raise RuntimeError('boom')")
    assert result["status"] == "python_error"


def test_upload_validation():
    client = create_app({"TESTING": True}).test_client()
    response = client.post("/corriger", data={"exercise": "s2-moyenne", "file": (BytesIO(b"x"), "notes.txt")}, content_type="multipart/form-data")
    assert "extension .py" in response.get_data(as_text=True)
