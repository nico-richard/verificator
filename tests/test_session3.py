import pytest
from markupsafe import escape

from verificator import create_app
from verificator.correction.engine import CorrectionEngine
from verificator.exercises import EXERCISES


SOLUTIONS = {
    "s3-calculer-distance": """import math

def calculer_distance(horizontal, vertical):
    return math.sqrt(horizontal ** 2 + vertical ** 2)
""",
    "s3-lire-valeurs": """def lire_valeurs(chemin):
    valeurs = []
    with open(chemin, "r", encoding="utf-8") as fichier:
        for ligne in fichier:
            valeurs.append(float(ligne.strip()))
    return valeurs
""",
    "s3-lire-mesures-csv": """import csv

def lire_mesures_csv(chemin):
    temps = []
    temperatures = []
    with open(chemin, newline="", encoding="utf-8") as fichier:
        lecteur = csv.reader(fichier, delimiter=";")
        next(lecteur)
        for ligne in lecteur:
            temps.append(float(ligne[0]))
            temperatures.append(float(ligne[1]))
    return (temps, temperatures)
""",
    "s3-ecrire-rapport": """def ecrire_rapport(chemin, temperatures):
    moyenne = sum(temperatures) / len(temperatures)
    with open(chemin, "w", encoding="utf-8") as fichier:
        fichier.write(f"Moyenne : {moyenne:.2f} °C\\n")
        fichier.write(f"Minimum : {min(temperatures):.2f} °C\\n")
        fichier.write(f"Maximum : {max(temperatures):.2f} °C\\n")
""",
    "s3-convertir-en-kelvins": """import numpy as np

def convertir_en_kelvins(temperatures):
    return np.array(temperatures) + 273.15
""",
    "s3-creer-instants": """import numpy as np

def creer_instants(duree, nombre):
    return np.linspace(0, duree, nombre)
""",
    "s3-charger-mesures-numpy": """import numpy as np

def charger_mesures_numpy(chemin):
    donnees = np.loadtxt(chemin, delimiter=";", skiprows=1)
    return (donnees[:, 0], donnees[:, 1])
""",
    "s3-corriger-mesures": """import numpy as np

def corriger_mesures(mesures, coefficient, decalage):
    tableau = np.array(mesures)
    return tableau * coefficient + decalage
""",
    "s3-calculer-statistiques": """import numpy as np

def calculer_statistiques(mesures):
    tableau = np.array(mesures)
    return (tableau.mean(), tableau.std(), tableau.min(), tableau.max())
""",
    "s3-calculer-moyennes": """def calculer_moyennes(tableau):
    return (tableau.mean(axis=1), tableau.mean(axis=0))
""",
}


def run(source, exercise_id):
    return CorrectionEngine(timeout=3).correct(
        EXERCISES[exercise_id],
        source.encode(),
    )


@pytest.mark.parametrize("exercise_id", SOLUTIONS)
def test_correct_session_3_submissions(exercise_id):
    result = run(SOLUTIONS[exercise_id], exercise_id)
    assert result["status"] == "ok"
    assert all(test["passed"] for test in result["tests"])


@pytest.mark.parametrize(
    ("exercise_id", "source"),
    [
        (
            "s3-convertir-en-kelvins",
            "def convertir_en_kelvins(temperatures): return [x + 273.15 for x in temperatures]",
        ),
        (
            "s3-creer-instants",
            "def creer_instants(duree, nombre): return [0, duree]",
        ),
        (
            "s3-calculer-statistiques",
            """def calculer_statistiques(mesures):
    return (sum(mesures) / len(mesures), 0, min(mesures), max(mesures))
""",
        ),
    ],
)
def test_invalid_session_3_submissions_are_rejected(exercise_id, source):
    result = run(source, exercise_id)
    assert result["status"] == "ok"
    assert any(not test["passed"] for test in result["tests"])


def test_session_3_exercises_define_expected_filenames():
    session_3 = [
        exercise for exercise in EXERCISES.values()
        if exercise.session == "3"
    ]
    assert [exercise.filename for exercise in session_3] == [
        f"s3_ex{number}.py" for number in range(1, 11)
    ]


def test_index_lists_the_ten_session_3_exercises():
    client = create_app({
        "TESTING": True,
        "ACCESS_PASSWORD": "test",
    }).test_client()
    with client.session_transaction() as current_session:
        current_session["authenticated"] = True
    html = client.get("/").get_data(as_text=True)
    session_3 = {
        exercise_id: exercise
        for exercise_id, exercise in EXERCISES.items()
        if exercise.session == "3"
    }
    assert len(session_3) == 10
    for exercise_id, exercise in session_3.items():
        assert f'value="{exercise_id}"' in html
        assert str(escape(exercise.title)) in html
