from .session2 import EXERCICES_SEANCE2
from .session3 import EXERCICES_SEANCE3
from .session4 import EXERCICES_SEANCE4

EXERCISES = {
    exercise.id: exercise
    for exercise in EXERCICES_SEANCE2 + EXERCICES_SEANCE3 + EXERCICES_SEANCE4
}
SESSIONS = {"2": "Séance 2", "3": "Séance 3", "4": "Séance 4"}
