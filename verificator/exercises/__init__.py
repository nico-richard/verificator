from .session2 import EXERCICES_SEANCE2
from .session3 import EXERCICES_SEANCE3

EXERCISES = {
    exercise.id: exercise
    for exercise in EXERCICES_SEANCE2 + EXERCICES_SEANCE3
}
SESSIONS = {"2": "Séance 2", "3": "Séance 3"}
