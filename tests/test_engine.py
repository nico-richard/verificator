from io import BytesIO

import pytest

from verificator import create_app
from verificator.correction.engine import CorrectionEngine
from verificator.exercises import EXERCISES


SOLUTIONS = {
    "s2-convertir-c-en-k": "def convertir_c_en_k(temperature): return temperature + 273.15",
    "s2-convertir-depuis-m": """def convertir_depuis_m(valeur, unite="m"):
    if unite == "cm": resultat = valeur * 100
    elif unite == "km": resultat = valeur / 1000
    else: resultat = valeur
    return round(resultat, 1)
""",
    "s2-deplacer": """def deplacer(position, dx, dy):
    x, y = position
    return (x + dx, y + dy)
""",
    "s2-moyenne": "def moyenne(valeurs): return round(sum(valeurs) / len(valeurs), 2)",
    "s2-analyser-phrase": """def analyser_phrase(phrase):
    return (phrase[:1], phrase[:5], phrase[-5:], phrase.split())
""",
    "s2-generer-mesures": """def generer_mesures(debut, pas, nombre):
    mesures = []
    for indice in range(nombre): mesures.append(debut + indice * pas)
    return mesures
""",
    "s2-maximum": """def maximum(valeurs):
    resultat = valeurs[0]
    for valeur in valeurs[1:]:
        if valeur > resultat: resultat = valeur
    return resultat
""",
    "s2-nettoyer-noms": """def nettoyer_noms(texte):
    noms = []
    for morceau in texte.split(";"):
        nom = morceau.strip()
        if nom != "": noms.append(nom)
    return noms
""",
    "s2-atteindre-objectif": """def atteindre_objectif(initial, ajout, objectif):
    etapes = 0
    while initial < objectif:
        initial += ajout
        etapes += 1
    return (etapes, initial)
""",
    "s2-premiere-mesure-superieure": """def premiere_mesure_superieure(mesures, seuil):
    indice = 0
    while indice < len(mesures):
        if mesures[indice] < 0:
            indice += 1
            continue
        if mesures[indice] > seuil: return indice
        indice += 1
    return -1
""",
}


def run(source, exercise_id="s2-moyenne"):
    return CorrectionEngine(timeout=2).correct(EXERCISES[exercise_id], source.encode())


@pytest.mark.parametrize("exercise_id", SOLUTIONS)
def test_correct_submissions(exercise_id):
    result = run(SOLUTIONS[exercise_id], exercise_id)
    assert result["status"] == "ok"
    assert all(test["passed"] for test in result["tests"])


@pytest.mark.parametrize(
    ("exercise_id", "source"),
    [
        (
            "s2-convertir-depuis-m",
            """def convertir_depuis_m(valeur, unite="m"):
    if unite == "cm": return valeur * 100
    if unite == "km": return valeur / 1000
    return valeur
""",
        ),
        (
            "s2-moyenne",
            "def moyenne(valeurs): return sum(valeurs) / len(valeurs)",
        ),
    ],
)
def test_unrounded_submissions_are_rejected(exercise_id, source):
    result = run(source, exercise_id)
    assert result["status"] == "ok"
    assert any(not test["passed"] for test in result["tests"])


@pytest.mark.parametrize(
    ("exercise_id", "source"),
    [
        (
            "s2-convertir-c-en-k",
            "def convertir_c_en_k(temperature): return round(temperature + 273.15, 2)",
        ),
        (
            "s2-generer-mesures",
            """def generer_mesures(debut, pas, nombre):
    return [debut + indice * pas for indice in range(min(nombre, 4))]
""",
        ),
        (
            "s2-maximum",
            "def maximum(valeurs): return int(max(valeurs))",
        ),
        (
            "s2-nettoyer-noms",
            """def nettoyer_noms(texte):
    return [nom.strip().title() for nom in texte.split(";") if nom.strip()]
""",
        ),
    ],
)
def test_submissions_that_violate_statements_are_rejected(exercise_id, source):
    result = run(source, exercise_id)
    assert result["status"] == "ok"
    assert any(not test["passed"] for test in result["tests"])


def test_missing_function():
    result = run("x = 1")
    assert result["tests"][0]["message"] == "Fonction absente."


def test_python_error():
    result = run("raise RuntimeError('boom')")
    assert result["status"] == "python_error"


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("def moyenne(valeurs):\n    print(valeurs)\n    return 0", "print()"),
        ("def moyenne(valeurs):\n    return input()", "input()"),
        (
            "def moyenne(valeurs): return 0\nmoyenne([1, 2, 3])",
            "chargement du fichier",
        ),
    ],
)
def test_forbidden_calls_are_rejected(source, message):
    result = run(source)
    assert result["status"] == "python_error"
    assert message in result["message"]


def authenticated_client(tmp_path):
    client = create_app({
        "TESTING": True,
        "ACCESS_PASSWORD": "test",
        "QCM_DATABASE": tmp_path / "verificator.sqlite3",
    }).test_client()
    with client.session_transaction() as current_session:
        current_session["authenticated"] = True
    return client


def test_upload_rejects_non_python_file(tmp_path):
    response = authenticated_client(tmp_path).post(
        "/corriger",
        data={"student_name": "Camille", "exercise": "s2-moyenne",
              "file": (BytesIO(b"x"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert "extension .py" in response.get_data(as_text=True)


def test_upload_rejects_wrong_python_filename(tmp_path):
    response = authenticated_client(tmp_path).post(
        "/corriger",
        data={"student_name": "Camille", "exercise": "s2-moyenne",
              "file": (BytesIO(b"x"), "moyenne.py")},
        content_type="multipart/form-data",
    )
    assert "s2_ex4.py" in response.get_data(as_text=True)


def test_uploaded_source_is_displayed_as_read_only_escaped_code(tmp_path):
    source = b"def moyenne(valeurs):\n    return 1 < 2\n"
    response = authenticated_client(tmp_path).post(
        "/corriger",
        data={"student_name": "Camille", "exercise": "s2-moyenne",
              "file": (BytesIO(source), "s2_ex4.py")},
        content_type="multipart/form-data",
    )
    html = response.get_data(as_text=True)
    assert "Programme chargé" in html
    assert "def moyenne(valeurs):" in html
    assert "return 1 &lt; 2" in html
    assert "<textarea" not in html


def test_correction_requires_student_name(tmp_path):
    response = authenticated_client(tmp_path).post(
        "/corriger",
        data={"student_name": "   ", "exercise": "s2-moyenne",
              "file": (BytesIO(b"def moyenne(valeurs): return 0"), "s2_ex4.py")},
        content_type="multipart/form-data",
    )
    assert "Veuillez renseigner votre nom et prénom" in response.get_data(as_text=True)
    assert not (tmp_path / "verificator.sqlite3").exists()


def test_correction_saves_name_ip_exercise_and_source(tmp_path):
    import sqlite3

    source = b"def moyenne(valeurs):\n    return round(sum(valeurs) / len(valeurs), 2)\n"
    response = authenticated_client(tmp_path).post(
        "/corriger",
        data={"student_name": "  Camille Dupont  ", "exercise": "s2-moyenne",
              "file": (BytesIO(source), "s2_ex4.py")},
        content_type="multipart/form-data",
        environ_base={"REMOTE_ADDR": "192.0.2.42"},
    )
    assert response.status_code == 200
    with sqlite3.connect(tmp_path / "verificator.sqlite3") as connection:
        row = connection.execute(
            "SELECT student_name, ip_address, exercise_id, source_code, succeeded, submitted_at FROM verifications"
        ).fetchone()
    assert row[:4] == ("Camille Dupont", "192.0.2.42", "s2-moyenne", source.decode())
    assert row[4] == 1
    assert row[5]


def test_correction_saves_failed_result(tmp_path):
    import sqlite3

    authenticated_client(tmp_path).post(
        "/corriger",
        data={"student_name": "Camille", "exercise": "s2-moyenne",
              "file": (BytesIO(b"def moyenne(valeurs): return 0"), "s2_ex4.py")},
        content_type="multipart/form-data",
    )
    with sqlite3.connect(tmp_path / "verificator.sqlite3") as connection:
        succeeded = connection.execute("SELECT succeeded FROM verifications").fetchone()[0]
    assert succeeded == 0


def test_session_2_exercises_define_expected_filenames():
    assert [exercise.filename for exercise in EXERCISES.values()] == [
        f"s2_ex{number}.py" for number in range(1, 11)
    ]

def test_index_lists_the_ten_session_2_exercises():
    client = create_app({"TESTING": True, "ACCESS_PASSWORD": "test"}).test_client()
    with client.session_transaction() as current_session:
        current_session["authenticated"] = True
    html = client.get("/").get_data(as_text=True)
    assert len(EXERCISES) == 10
    for exercise_id, exercise in EXERCISES.items():
        assert f'value="{exercise_id}"' in html
        assert exercise.title in html


def test_login_required():
    client = create_app({"TESTING": True, "ACCESS_PASSWORD": "secret"}).test_client()
    assert client.get("/").status_code == 302
    response = client.post("/connexion", data={"password": "secret"})
    assert response.status_code == 302


def test_network_restriction():
    app = create_app({"TESTING": True, "ALLOWED_NETWORKS": "10.0.0.0/8"})
    response = app.test_client().get("/", environ_base={"REMOTE_ADDR": "192.168.1.5"})
    assert response.status_code == 403
