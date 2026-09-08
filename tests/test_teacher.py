import csv
import io
import sqlite3
from unittest.mock import patch

import pytest

from verificator import create_app
from verificator.qcm import save_submission
from verificator.verifications import save_verification


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "ACCESS_PASSWORD": "student-password",
        "TEACHER_PASSWORD": "teacher-password",
        "SECRET_KEY": "test-secret",
        "QCM_DATABASE": tmp_path / "instance" / "qcm.sqlite3",
    })


@pytest.fixture
def teacher_client(app):
    client = app.test_client()
    client.post("/enseignant/connexion", data={"password": "teacher-password"})
    return client


@pytest.mark.parametrize("path", ["/enseignant/qcm", "/enseignant/qcm/export.csv", "/enseignant/verifications"])
@pytest.mark.parametrize("student_logged_in", [False, True])
def test_results_and_export_require_teacher_login(app, path, student_logged_in):
    client = app.test_client()
    if student_logged_in:
        client.post("/connexion", data={"password": "student-password"})
    response = client.get(path)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/enseignant/connexion")
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("password", ["", "student-password", "incorrect", "échec"])
def test_teacher_login_rejects_invalid_password(app, password):
    client = app.test_client()
    response = client.post("/enseignant/connexion", data={"password": password})
    assert "Mot de passe enseignant incorrect" in response.get_data(as_text=True)
    assert client.get("/enseignant/qcm/export.csv").status_code == 302


@pytest.mark.parametrize("password", ["", "student-password"])
def test_teacher_password_must_be_configured_and_distinct(app, password):
    app.config["TEACHER_PASSWORD"] = password
    client = app.test_client()
    for path in ("/enseignant/connexion", "/enseignant/qcm", "/enseignant/qcm/export.csv", "/enseignant/verifications"):
        assert client.get(path).status_code == 503
    assert client.post("/enseignant/connexion", data={"password": password}).status_code == 503


def test_teacher_access_requires_private_session_key(app):
    app.config["SECRET_KEY"] = "change-me"
    assert app.test_client().get("/enseignant/qcm").status_code == 503


def test_teacher_login_does_not_require_student_login_and_supports_unicode(app):
    app.config["TEACHER_PASSWORD"] = "mot-de-passe-privé"
    client = app.test_client()
    response = client.post("/enseignant/connexion", data={"password": "mot-de-passe-privé"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/enseignant/qcm")
    assert client.get("/enseignant/qcm").status_code == 200
    assert client.get("/qcm").status_code == 302


def test_teacher_login_returns_to_requested_verifications_page(app):
    client = app.test_client()
    client.get("/enseignant/verifications")
    response = client.post("/enseignant/connexion", data={"password": "teacher-password"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/enseignant/verifications")


def test_empty_results_do_not_create_database(teacher_client, app):
    response = teacher_client.get("/enseignant/qcm")
    assert response.status_code == 200
    assert "Aucune réponse enregistrée" in response.get_data(as_text=True)
    assert not app.config["QCM_DATABASE"].exists()
    export = teacher_client.get("/enseignant/qcm/export.csv")
    rows = list(csv.reader(io.StringIO(export.data.decode("utf-8-sig")), delimiter=";"))
    assert len(rows) == 1
    assert len(rows[0]) == 22


def test_results_show_answers_newest_first_and_escape_names(teacher_client, app):
    save_submission(app.config["QCM_DATABASE"], "Camille", {number: "A" for number in range(1, 16)})
    save_submission(app.config["QCM_DATABASE"], "<script>alert(1)</script>", {number: "D" for number in range(1, 16)})
    response = teacher_client.get("/enseignant/qcm")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "2 envoi(s)" in html
    assert html.index("&lt;script&gt;") < html.index("Camille")
    assert "<script>alert(1)</script>" not in html
    assert html.count("<td>D</td>") == 15
    assert html.count("<td>A</td>") == 15
    assert response.headers["Cache-Control"] == "no-store"


def test_teacher_can_view_python_verifications_newest_first(teacher_client, app):
    save_verification(app.config["QCM_DATABASE"], "Camille", "192.0.2.1", "s2-moyenne", "x = 1")
    save_verification(
        app.config["QCM_DATABASE"], "<script>Nom</script>", "2001:db8::1",
        "s2-maximum", "if x < 2:\n    print('<test>')",
    )
    response = teacher_client.get("/enseignant/verifications")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "2 vérification(s)" in html
    assert html.index("2001:db8::1") < html.index("192.0.2.1")
    assert "&lt;script&gt;Nom&lt;/script&gt;" in html
    assert "if x &lt; 2:" in html
    assert "<script>Nom</script>" not in html
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("name,exported_name", [
    ('Élodie; "Dupont"', 'Élodie; "Dupont"'),
    ("=1+1", "'=1+1"),
    ("+1", "'+1"),
    ("-1", "'-1"),
    ("@SUM(1)", "'@SUM(1)"),
    ("  =1+1", "'  =1+1"),
    ("\tNom", "'\tNom"),
])
def test_csv_preserves_answers_and_neutralizes_formulas(teacher_client, app, name, exported_name):
    answers = {number: "ABCD"[(number - 1) % 4] for number in range(1, 16)}
    save_submission(app.config["QCM_DATABASE"], name, answers)
    response = teacher_client.get("/enseignant/qcm/export.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert 'attachment; filename="resultats-qcm.csv"' == response.headers["Content-Disposition"]
    assert response.headers["Cache-Control"] == "no-store"
    assert response.data.startswith(b"\xef\xbb\xbf")
    rows = list(csv.reader(io.StringIO(response.data.decode("utf-8-sig")), delimiter=";"))
    assert rows[0] == ["Envoi", "Nom et prénom", "Date (UTC)", "Questionnaire", "Version", "Score", "Total"] + [f"Q{number}" for number in range(1, 16)]
    assert len(rows) == 2
    assert rows[1][1] == exported_name
    assert rows[1][2]
    assert rows[1][7:] == list(answers.values())


def test_teacher_logout_revokes_results_and_export_but_preserves_student_login(teacher_client):
    teacher_client.post("/connexion", data={"password": "student-password"})
    assert teacher_client.post("/enseignant/deconnexion").status_code == 302
    assert teacher_client.get("/enseignant/qcm").status_code == 302
    assert teacher_client.get("/enseignant/qcm/export.csv").status_code == 302
    assert teacher_client.get("/enseignant/verifications").status_code == 302
    assert teacher_client.get("/qcm").status_code == 200


@pytest.mark.parametrize("path", ["/enseignant/qcm", "/enseignant/qcm/export.csv"])
def test_storage_failure_does_not_show_empty_results_or_download(teacher_client, path):
    with patch("verificator.teacher.get_submissions", side_effect=sqlite3.OperationalError("unavailable")):
        response = teacher_client.get(path)
    assert response.status_code == 503
    assert "indisponible" in response.get_data(as_text=True)
    assert "Content-Disposition" not in response.headers


def test_verification_storage_failure_does_not_show_empty_results(teacher_client):
    with patch("verificator.teacher.get_verifications", side_effect=sqlite3.OperationalError("unavailable")):
        response = teacher_client.get("/enseignant/verifications")
    assert response.status_code == 503
    assert "indisponibles" in response.get_data(as_text=True)
