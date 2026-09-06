import json
import sqlite3
from unittest.mock import patch

import pytest
from werkzeug.datastructures import MultiDict

from verificator import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "ACCESS_PASSWORD": "test",
        "SECRET_KEY": "test-secret",
        "QCM_DATABASE": tmp_path / "instance" / "qcm.sqlite3",
    })


@pytest.fixture
def client(app):
    client = app.test_client()
    with client.session_transaction() as current_session:
        current_session["authenticated"] = True
    return client


def submission():
    return {"student_name": "  Camille Dupont  ", "questionnaire": "seance2", "version": "A",
            **{f"question_{number}": "ABCD"[(number - 1) % 4]
               for number in range(1, 16)}}


def test_qcm_form(client):
    response = client.get("/qcm")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert html.count('<fieldset class="qcm-question">') == 15
    assert html.count('type="radio"') == 60
    assert 'name="student_name"' in html
    for number in range(1, 16):
        assert html.count(f'name="question_{number}"') == 4
    assert 'href="/qcm"' in client.get("/").get_data(as_text=True)


@pytest.mark.parametrize("method", ["get", "post"])
def test_qcm_requires_login(app, method):
    response = getattr(app.test_client(), method)("/qcm")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/connexion")
    assert not app.config["QCM_DATABASE"].exists()


def test_qcm_saves_answers_and_refresh_does_not_resubmit(client, app):
    data = submission()
    response = client.post("/qcm", data=data)
    assert response.status_code == 302
    confirmation = client.get(response.headers["Location"])
    assert "Vos réponses ont bien été enregistrées" in confirmation.get_data(as_text=True)
    client.get("/qcm")
    connection = sqlite3.connect(app.config["QCM_DATABASE"])
    try:
        rows = connection.execute(
            "SELECT student_name, answers, submitted_at FROM qcm_submissions"
        ).fetchall()
    finally:
        connection.close()
    assert len(rows) == 1
    assert rows[0][0] == "Camille Dupont"
    assert json.loads(rows[0][1]) == {
        str(number): data[f"question_{number}"] for number in range(1, 16)
    }
    assert rows[0][2]


@pytest.mark.parametrize("field,value", [
    ("student_name", "   "),
    ("student_name", "a" * 121),
    ("question_1", ""),
    ("question_15", "E"),
])
def test_qcm_rejects_invalid_submission(client, app, field, value):
    data = submission()
    data[field] = value
    response = client.post("/qcm", data=data)
    assert 'role="alert"' in response.get_data(as_text=True)
    assert not app.config["QCM_DATABASE"].exists()


def test_qcm_rejects_missing_answer_and_keeps_form_values(client, app):
    data = submission()
    del data["question_15"]
    html = client.post("/qcm", data=data).get_data(as_text=True)
    assert "Veuillez choisir une seule réponse" in html
    assert 'value="Camille Dupont"' in html
    assert html.count("checked") == 14
    assert not app.config["QCM_DATABASE"].exists()


def test_qcm_rejects_multiple_answers_to_one_question(client, app):
    data = MultiDict(submission())
    data.add("question_1", "B")
    html = client.post("/qcm", data=data).get_data(as_text=True)
    assert "Veuillez choisir une seule réponse" in html
    assert not app.config["QCM_DATABASE"].exists()


def test_qcm_storage_failure_keeps_answers(client):
    with patch("verificator.save_submission", side_effect=sqlite3.OperationalError("disk full")):
        response = client.post("/qcm", data=submission())
    html = response.get_data(as_text=True)
    assert "L’enregistrement a échoué" in html
    assert 'value="Camille Dupont"' in html
    assert html.count("checked") == 15
    assert "Vos réponses ont bien été enregistrées" not in html


@pytest.mark.parametrize("version", ["A", "B"])
@pytest.mark.parametrize("questionnaire", ["seance1", "seance2", "seance3", "seance4"])
def test_version_scores_match_selected_questionnaire(client, app, version, questionnaire):
    from verificator.qcm import QCM_KEYS, get_submissions
    key = QCM_KEYS[questionnaire][version]
    data = submission()
    data.update(questionnaire=questionnaire, version=version)
    data.update({f"question_{i}": correct or "A" for i, correct in enumerate(key, 1)})
    assert client.post("/qcm", data=data).status_code == 302
    saved = get_submissions(app.config["QCM_DATABASE"])[0]
    assert saved["version"] == version
    assert saved["questionnaire"] == questionnaire
    assert saved["score"] == saved["total"] == sum(x is not None for x in key)


@pytest.mark.parametrize("field,value", [("version", ""), ("version", "C"), ("questionnaire", ""), ("questionnaire", "invalid")])
def test_missing_or_unknown_version_rejected(client, app, field, value):
    data = submission()
    data[field] = value
    assert "Veuillez sélectionner le questionnaire" in client.post("/qcm", data=data).get_data(as_text=True)
    assert not app.config["QCM_DATABASE"].exists()


def test_legacy_database_keeps_ungraded_answers(app):
    from verificator.qcm import save_submission, get_submissions
    database = app.config["QCM_DATABASE"]
    database.parent.mkdir(parents=True)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE qcm_submissions (id INTEGER PRIMARY KEY, student_name TEXT, answers TEXT, submitted_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        connection.execute("INSERT INTO qcm_submissions (student_name, answers) VALUES ('Ancien', '{}')")
    assert get_submissions(database)[0]["student_name"] == "Ancien"
    save_submission(database, "Nouveau", {i: "A" for i in range(1, 16)}, "seance2", "B")
    rows = get_submissions(database)
    assert rows[1]["score"] is None and rows[1]["version"] is None
    assert rows[0]["version"] == "B" and rows[0]["score"] is not None
