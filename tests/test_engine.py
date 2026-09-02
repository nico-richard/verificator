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
    client = create_app({"TESTING": True, "ACCESS_PASSWORD": "test"}).test_client()
    with client.session_transaction() as current_session:
        current_session["authenticated"] = True
    response = client.post("/corriger", data={"exercise": "s2-moyenne", "file": (BytesIO(b"x"), "notes.txt")}, content_type="multipart/form-data")
    assert "extension .py" in response.get_data(as_text=True)


def test_login_required():
    client = create_app({"TESTING": True, "ACCESS_PASSWORD": "secret"}).test_client()
    assert client.get("/").status_code == 302
    response = client.post("/connexion", data={"password": "secret"})
    assert response.status_code == 302


def test_network_restriction():
    app = create_app({"TESTING": True, "ALLOWED_NETWORKS": "10.0.0.0/8"})
    response = app.test_client().get("/", environ_base={"REMOTE_ADDR": "192.168.1.5"})
    assert response.status_code == 403
