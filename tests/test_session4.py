import pytest
from markupsafe import escape

from verificator import create_app
from verificator.correction.engine import CorrectionEngine
from verificator.exercises import EXERCISES


SOLUTIONS = {
    "s4-tracer-evolution": """import matplotlib.pyplot as plt

def tracer_evolution(temps, mesures):
    plt.plot(temps, mesures)
""",
    "s4-annoter-courbe": """import matplotlib.pyplot as plt

def annoter_courbe(temps, temperatures):
    plt.plot(temps, temperatures, color="tab:blue", marker="o", label="Température")
    plt.xlabel("Temps (s)")
    plt.ylabel("Température (°C)")
    plt.title("Évolution de la température")
    plt.grid(alpha=0.3)
    plt.legend()
""",
    "s4-tracer-nuage": """import matplotlib.pyplot as plt

def tracer_nuage(tensions, courants):
    plt.scatter(tensions, courants)
""",
    "s4-tracer-histogramme": """import matplotlib.pyplot as plt

def tracer_histogramme(mesures, nombre_classes=5):
    plt.hist(mesures, bins=nombre_classes)
""",
    "s4-creer-comparaison": """import matplotlib.pyplot as plt

def creer_comparaison(temps, temperatures):
    plt.subplot(1, 2, 1)
    plt.plot(temps, temperatures)
    plt.subplot(1, 2, 2)
    plt.hist(temperatures, bins=5)
    plt.tight_layout()
""",
    "s4-exporter-courbe": """import matplotlib.pyplot as plt

def exporter_courbe(chemin, temps, temperatures):
    plt.plot(temps, temperatures)
    plt.xlabel("Temps (s)")
    plt.ylabel("Température (°C)")
    plt.savefig(chemin, dpi=300, bbox_inches="tight")
""",
    "s4-decoder-mesure": """def decoder_mesure(donnees):
    return float(donnees.decode("utf-8").strip())
""",
    "s4-encoder-commande": """def encoder_commande(commande):
    return (commande + "\\n").encode("utf-8")
""",
    "s4-lire-mesures": """def lire_mesures(port, nombre):
    mesures = []
    for _ in range(nombre):
        mesures.append(float(port.readline().decode("utf-8").strip()))
    return mesures
""",
    "s4-interroger-instrument": """def interroger_instrument(port, commande):
    port.write((commande + "\\n").encode("utf-8"))
    return port.readline().decode("utf-8").strip()
""",
}


def run(source, exercise_id):
    return CorrectionEngine(timeout=5).correct(
        EXERCISES[exercise_id],
        source.encode(),
    )


@pytest.mark.parametrize("exercise_id", SOLUTIONS)
def test_correct_session_4_submissions(exercise_id):
    result = run(SOLUTIONS[exercise_id], exercise_id)
    assert result["status"] == "ok"
    assert all(test["passed"] for test in result["tests"])


@pytest.mark.parametrize(
    ("exercise_id", "source"),
    [
        (
            "s4-tracer-histogramme",
            """import matplotlib.pyplot as plt
def tracer_histogramme(mesures, nombre_classes=5):
    plt.hist(mesures, bins=10)
""",
        ),
        (
            "s4-encoder-commande",
            "def encoder_commande(commande): return commande.encode('utf-8')",
        ),
        (
            "s4-interroger-instrument",
            "def interroger_instrument(port, commande): return port.readline()",
        ),
    ],
)
def test_invalid_session_4_submissions_are_rejected(exercise_id, source):
    result = run(source, exercise_id)
    assert result["status"] == "ok"
    assert any(not test["passed"] for test in result["tests"])


def test_session_4_exercises_define_expected_filenames():
    session_4 = [
        exercise for exercise in EXERCISES.values()
        if exercise.session == "4"
    ]
    assert [exercise.filename for exercise in session_4] == [
        f"s4_ex{number}.py" for number in range(1, 11)
    ]


def test_index_lists_the_ten_session_4_exercises():
    client = create_app({
        "TESTING": True,
        "ACCESS_PASSWORD": "test",
    }).test_client()
    with client.session_transaction() as current_session:
        current_session["authenticated"] = True
    html = client.get("/").get_data(as_text=True)
    session_4 = {
        exercise_id: exercise
        for exercise_id, exercise in EXERCISES.items()
        if exercise.session == "4"
    }
    assert len(session_4) == 10
    for exercise_id, exercise in session_4.items():
        assert f'value="{exercise_id}"' in html
        assert str(escape(exercise.title)) in html
