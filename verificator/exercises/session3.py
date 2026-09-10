"""Catalogue enseignant : contrats et tests des dix exercices de séance 3.

Ce fichier peut être copié dans verificator/exercises/session3.py.
Les constructions de ce correcteur ne sont pas demandées aux étudiants.
"""
from copy import deepcopy
from dataclasses import dataclass
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np


@dataclass(frozen=True)
class Exercise:
    id: str
    session: str
    title: str
    filename: str
    function_name: str
    test_module: callable


def resultats_egaux(obtenu, attendu):
    if isinstance(attendu, np.ndarray):
        return (
            isinstance(obtenu, np.ndarray)
            and obtenu.shape == attendu.shape
            and np.allclose(obtenu, attendu, rtol=1e-9, atol=1e-9)
        )
    if isinstance(attendu, (tuple, list)):
        return (
            type(obtenu) is type(attendu)
            and len(obtenu) == len(attendu)
            and all(resultats_egaux(a, b) for a, b in zip(obtenu, attendu))
        )
    if isinstance(attendu, (int, float, np.number)):
        return (
            isinstance(obtenu, (int, float, np.number))
            and not isinstance(obtenu, (bool, np.bool_))
            and isclose(float(obtenu), float(attendu), rel_tol=1e-9, abs_tol=1e-9)
        )
    return type(obtenu) is type(attendu) and obtenu == attendu


def donnees_egales(gauche, droite):
    if isinstance(gauche, np.ndarray) or isinstance(droite, np.ndarray):
        return (
            isinstance(gauche, np.ndarray)
            and isinstance(droite, np.ndarray)
            and np.array_equal(gauche, droite)
        )
    if isinstance(gauche, (tuple, list)) and isinstance(droite, type(gauche)):
        return (
            len(gauche) == len(droite)
            and all(donnees_egales(a, b) for a, b in zip(gauche, droite))
        )
    return gauche == droite


def resultat(nom, correct, message):
    return {"name": nom, "passed": bool(correct), "message": message}


def fonction_du_module(module, nom):
    fonction = getattr(module, nom, None)
    if not callable(fonction):
        return None, [
            resultat("fonction " + nom, False, "Fonction absente.")
        ]
    return fonction, None


def creer_test(nom, cas):
    def tester(module):
        fonction, erreur = fonction_du_module(module, nom)
        if erreur:
            return erreur
        resultats = []
        for description, arguments, attendu in cas:
            entrees = deepcopy(arguments)
            reference = deepcopy(arguments)
            try:
                obtenu = fonction(*entrees)
                correct = resultats_egaux(obtenu, attendu)
                intact = donnees_egales(entrees, reference)
                message = "Réponse correcte."
                if not correct:
                    message = f"Résultat incorrect : {obtenu!r}."
                elif not intact:
                    message = "Les données reçues ne doivent pas être modifiées."
                resultats.append(resultat(description, correct and intact, message))
            except Exception as exc:
                resultats.append(resultat(
                    description,
                    False,
                    f"Erreur : {type(exc).__name__}: {exc}",
                ))
        return resultats
    return tester


def test_lire_valeurs(module):
    fonction, erreur = fonction_du_module(module, "lire_valeurs")
    if erreur:
        return erreur
    cas = [
        ("plusieurs valeurs", "12.5\n15\n-3.25\n", [12.5, 15.0, -3.25]),
        ("une valeur", "0\n", [0.0]),
    ]
    resultats = []
    with TemporaryDirectory() as dossier:
        for numero, (description, contenu, attendu) in enumerate(cas):
            chemin = Path(dossier) / f"valeurs_{numero}.txt"
            chemin.write_text(contenu, encoding="utf-8")
            try:
                obtenu = fonction(str(chemin))
                correct = resultats_egaux(obtenu, attendu)
                message = "Réponse correcte." if correct else f"Résultat incorrect : {obtenu!r}."
                resultats.append(resultat(description, correct, message))
            except Exception as exc:
                resultats.append(resultat(
                    description, False, f"Erreur : {type(exc).__name__}: {exc}"
                ))
    return resultats


def test_lire_mesures_csv(module):
    fonction, erreur = fonction_du_module(module, "lire_mesures_csv")
    if erreur:
        return erreur
    cas = [
        (
            "journal complet",
            "temps;temperature\n0;20.1\n1.5;20.8\n3;-2.0\n",
            ([0.0, 1.5, 3.0], [20.1, 20.8, -2.0]),
        ),
        (
            "une observation",
            "temps;temperature\n12;18.25\n",
            ([12.0], [18.25]),
        ),
    ]
    resultats = []
    with TemporaryDirectory() as dossier:
        for numero, (description, contenu, attendu) in enumerate(cas):
            chemin = Path(dossier) / f"mesures_{numero}.csv"
            chemin.write_text(contenu, encoding="utf-8")
            try:
                obtenu = fonction(str(chemin))
                correct = resultats_egaux(obtenu, attendu)
                message = "Réponse correcte." if correct else f"Résultat incorrect : {obtenu!r}."
                resultats.append(resultat(description, correct, message))
            except Exception as exc:
                resultats.append(resultat(
                    description, False, f"Erreur : {type(exc).__name__}: {exc}"
                ))
    return resultats


def test_ecrire_rapport(module):
    fonction, erreur = fonction_du_module(module, "ecrire_rapport")
    if erreur:
        return erreur
    cas = [
        (
            "valeurs décimales",
            [19.25, 20.5, 21.75],
            "Moyenne : 20.50 °C\nMinimum : 19.25 °C\nMaximum : 21.75 °C\n",
        ),
        (
            "arrondis et valeurs négatives",
            [-2.345, 0, 1.234],
            "Moyenne : -0.37 °C\nMinimum : -2.35 °C\nMaximum : 1.23 °C\n",
        ),
    ]
    resultats = []
    with TemporaryDirectory() as dossier:
        for numero, (description, temperatures, attendu) in enumerate(cas):
            chemin = Path(dossier) / f"rapport_{numero}.txt"
            reference = deepcopy(temperatures)
            try:
                retour = fonction(str(chemin), temperatures)
                contenu = chemin.read_text(encoding="utf-8")
                correct = retour is None and contenu == attendu
                intact = temperatures == reference
                message = "Réponse correcte."
                if retour is not None:
                    message = "La fonction ne doit rien renvoyer."
                elif contenu != attendu:
                    message = f"Contenu incorrect : {contenu!r}."
                elif not intact:
                    message = "Les températures reçues ne doivent pas être modifiées."
                resultats.append(resultat(description, correct and intact, message))
            except Exception as exc:
                resultats.append(resultat(
                    description, False, f"Erreur : {type(exc).__name__}: {exc}"
                ))
    return resultats


def test_charger_mesures_numpy(module):
    fonction, erreur = fonction_du_module(module, "charger_mesures_numpy")
    if erreur:
        return erreur
    cas = [
        (
            "colonnes décimales",
            "temps;temperature\n0;20.1\n1.5;20.8\n3;-2.0\n",
            (np.array([0.0, 1.5, 3.0]), np.array([20.1, 20.8, -2.0])),
        ),
        (
            "deux observations",
            "temps;temperature\n10;18\n20;19.5\n",
            (np.array([10.0, 20.0]), np.array([18.0, 19.5])),
        ),
    ]
    resultats = []
    with TemporaryDirectory() as dossier:
        for numero, (description, contenu, attendu) in enumerate(cas):
            chemin = Path(dossier) / f"numpy_{numero}.csv"
            chemin.write_text(contenu, encoding="utf-8")
            try:
                obtenu = fonction(str(chemin))
                correct = resultats_egaux(obtenu, attendu)
                message = "Réponse correcte." if correct else f"Résultat incorrect : {obtenu!r}."
                resultats.append(resultat(description, correct, message))
            except Exception as exc:
                resultats.append(resultat(
                    description, False, f"Erreur : {type(exc).__name__}: {exc}"
                ))
    return resultats


CAS_SIMPLES = {
    "calculer_distance": [
        ("triangle 3-4-5", (3, 4), 5.0),
        ("distance nulle", (0, 0), 0.0),
        ("valeurs décimales", (1.5, 2.0), 2.5),
        ("un seul déplacement", (0, 7.25), 7.25),
    ],
    "convertir_en_kelvins": [
        ("températures usuelles", ([0, 20, -40],), np.array([273.15, 293.15, 233.15])),
        ("liste vide", ([],), np.array([])),
        ("valeurs décimales", ([12.5, 18.25],), np.array([285.65, 291.4])),
    ],
    "creer_instants": [
        ("cinq instants", (10, 5), np.array([0, 2.5, 5, 7.5, 10])),
        ("deux bornes", (3, 2), np.array([0, 3])),
        ("durée nulle", (0, 4), np.array([0, 0, 0, 0])),
    ],
    "corriger_mesures": [
        ("relation affine", ([1, 2, 3], 2, -1), np.array([1, 3, 5])),
        ("coefficient décimal", ((-2, 0, 4), 0.5, 1.5), np.array([0.5, 1.5, 3.5])),
        ("séquence vide", ([], 3, 2), np.array([])),
    ],
    "calculer_statistiques": [
        ("série simple", ([1, 2, 3],), (2.0, np.std([1, 2, 3]), 1, 3)),
        ("valeur unique", ([5.5],), (5.5, 0.0, 5.5, 5.5)),
        ("valeurs négatives", ([-4, -2, 0, 2],), (-1.0, np.std([-4, -2, 0, 2]), -4, 2)),
    ],
    "calculer_moyennes": [
        (
            "tableau deux par trois",
            (np.array([[1, 2, 3], [4, 5, 6]]),),
            (np.array([2.0, 5.0]), np.array([2.5, 3.5, 4.5])),
        ),
        (
            "une ligne",
            (np.array([[2.0, 4.0, 8.0]]),),
            (np.array([14 / 3]), np.array([2.0, 4.0, 8.0])),
        ),
        (
            "une colonne",
            (np.array([[1.0], [3.0], [8.0]]),),
            (np.array([1.0, 3.0, 8.0]), np.array([4.0])),
        ),
    ],
}


DEFINITIONS = [
    ("s3-calculer-distance", "Calculer une distance", "calculer_distance",
     creer_test("calculer_distance", CAS_SIMPLES["calculer_distance"])),
    ("s3-lire-valeurs", "Relire les profondeurs", "lire_valeurs",
     test_lire_valeurs),
    ("s3-lire-mesures-csv", "Décoder le journal CSV", "lire_mesures_csv",
     test_lire_mesures_csv),
    ("s3-ecrire-rapport", "Rédiger le bilan de plongée", "ecrire_rapport",
     test_ecrire_rapport),
    ("s3-convertir-en-kelvins", "Convertir la série en kelvins",
     "convertir_en_kelvins",
     creer_test("convertir_en_kelvins", CAS_SIMPLES["convertir_en_kelvins"])),
    ("s3-creer-instants", "Construire l'axe du temps", "creer_instants",
     creer_test("creer_instants", CAS_SIMPLES["creer_instants"])),
    ("s3-charger-mesures-numpy", "Charger les colonnes avec NumPy",
     "charger_mesures_numpy", test_charger_mesures_numpy),
    ("s3-corriger-mesures", "Corriger l'étalonnage", "corriger_mesures",
     creer_test("corriger_mesures", CAS_SIMPLES["corriger_mesures"])),
    ("s3-calculer-statistiques", "Résumer la campagne", "calculer_statistiques",
     creer_test("calculer_statistiques", CAS_SIMPLES["calculer_statistiques"])),
    ("s3-calculer-moyennes", "Comparer les capteurs", "calculer_moyennes",
     creer_test("calculer_moyennes", CAS_SIMPLES["calculer_moyennes"])),
]


EXERCICES_SEANCE3 = [
    Exercise(
        identifiant,
        "3",
        f"Exercice {numero} — {titre}",
        f"s3_ex{numero}.py",
        nom,
        test,
    )
    for numero, (identifiant, titre, nom, test)
    in enumerate(DEFINITIONS, start=1)
]
