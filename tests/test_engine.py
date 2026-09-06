from io import BytesIO

import pytest

from verificator import create_app
from verificator.correction.engine import CorrectionEngine
from verificator.exercises import EXERCISES


SOLUTIONS = {
    "s2-convertir-c-en-k": "def convertir_c_en_k(temperature): return temperature + 273.15",
    "s2-convertir-depuis-m": """def convertir_depuis_m(valeur, unite="m"):
    if unite == "cm": return valeur * 100
    if unite == "km": return valeur / 1000
    return valeur
""",
    "s2-deplacer": """def deplacer(position, dx, dy):
    x, y = position
    return (x + dx, y + dy)
""",
    "s2-moyenne": "def moyenne(valeurs): return sum(valeurs) / len(valeurs)",
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


def test_missing_function():
    result = run("x = 1")
    assert result["tests"][0]["message"] == "Fonction absente."


def test_python_error():
    result = run("raise RuntimeError('boom')")
    assert result["status"] == "python_error"


def authenticated_client():
    client = create_app({"TESTING": True, "ACCESS_PASSWORD": "test"}).test_client()
    with client.session_transaction() as current_session:
        current_session["authenticated"] = True
    return client


def test_upload_rejects_non_python_file():
    response = authenticated_client().post(
        "/corriger",
        data={"exercise": "s2-moyenne", "file": (BytesIO(b"x"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert "extension .py" in response.get_data(as_text=True)


def test_upload_rejects_wrong_python_filename():
    response = authenticated_client().post(
        "/corriger",
        data={"exercise": "s2-moyenne", "file": (BytesIO(b"x"), "moyenne.py")},
        content_type="multipart/form-data",
    )
    assert "s2_ex4.py" in response.get_data(as_text=True)


def test_uploaded_source_is_displayed_as_read_only_escaped_code():
    source = b"def moyenne(valeurs):\n    return 1 < 2\n"
    response = authenticated_client().post(
        "/corriger",
        data={"exercise": "s2-moyenne", "file": (BytesIO(source), "s2_ex4.py")},
        content_type="multipart/form-data",
    )
    html = response.get_data(as_text=True)
    assert "Programme chargé" in html
    assert "def moyenne(valeurs):" in html
    assert "return 1 &lt; 2" in html
    assert "<textarea" not in html


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
