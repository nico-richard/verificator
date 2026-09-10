"""Catalogue enseignant : contrats et tests des dix exercices de séance 4.

Ce fichier peut être copié dans verificator/exercises/session4.py.
Les constructions de ce correcteur ne sont pas demandées aux étudiants.
"""
from copy import deepcopy
from dataclasses import dataclass
from math import isclose

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class Exercise:
    id: str
    session: str
    title: str
    filename: str
    function_name: str
    test_module: callable


def resultat(nom, correct, message="Réponse correcte."):
    return {"name": nom, "passed": bool(correct), "message": message}


def fonction_du_module(module, nom):
    fonction = getattr(module, nom, None)
    if callable(fonction):
        return fonction, None
    return None, [resultat("fonction " + nom, False, "Fonction absente.")]


def egal(gauche, droite):
    try:
        return np.allclose(gauche, droite, rtol=1e-9, atol=1e-9)
    except (TypeError, ValueError):
        return gauche == droite


def verifier_graphique(obtenu, nombre_zones=1):
    if obtenu is not None:
        return None, "La fonction ne doit rien renvoyer."
    numeros = plt.get_fignums()
    if len(numeros) != 1:
        return None, "La fonction doit produire un seul graphique."
    zones = plt.gcf().axes
    if len(zones) != nombre_zones:
        return None, f"Le graphique doit contenir {nombre_zones} zone(s) de tracé."
    return zones, None


def executer_test_graphique(module, nom, controle, cas):
    fonction, erreur = fonction_du_module(module, nom)
    if erreur:
        return erreur
    resultats = []
    for description, arguments in cas:
        entrees = deepcopy(arguments)
        reference = deepcopy(arguments)
        plt.close("all")
        try:
            obtenu = fonction(*entrees)
            correct, message = controle(obtenu, entrees)
            intact = all(egal(a, b) for a, b in zip(entrees, reference))
            if correct and not intact:
                correct = False
                message = "Les données reçues ne doivent pas être modifiées."
            resultats.append(resultat(description, correct, message))
        except Exception as exc:
            resultats.append(resultat(
                description,
                False,
                f"Erreur : {type(exc).__name__}: {exc}",
            ))
        finally:
            plt.close("all")
    return resultats


def controle_evolution(obtenu, arguments):
    axes, erreur = verifier_graphique(obtenu)
    if erreur:
        return False, erreur
    lignes = axes[0].lines
    correct = (
        len(lignes) == 1
        and egal(lignes[0].get_xdata(), arguments[0])
        and egal(lignes[0].get_ydata(), arguments[1])
    )
    return correct, "Courbe incorrecte." if not correct else "Réponse correcte."


def controle_annotations(obtenu, arguments):
    axes, erreur = verifier_graphique(obtenu)
    if erreur:
        return False, erreur
    ax = axes[0]
    lignes = ax.lines
    legende = ax.get_legend()
    correct = (
        len(lignes) == 1
        and egal(lignes[0].get_xdata(), arguments[0])
        and egal(lignes[0].get_ydata(), arguments[1])
        and lignes[0].get_color() == "tab:blue"
        and lignes[0].get_marker() == "o"
        and lignes[0].get_label() == "Température"
        and ax.get_xlabel() == "Temps (s)"
        and ax.get_ylabel() == "Température (°C)"
        and ax.get_title() == "Évolution de la température"
        and legende is not None
        and any(ligne.get_visible() for ligne in ax.get_xgridlines())
    )
    return correct, "Tracé ou annotations incorrects." if not correct else "Réponse correcte."


def controle_nuage(obtenu, arguments):
    axes, erreur = verifier_graphique(obtenu)
    if erreur:
        return False, erreur
    collections = axes[0].collections
    attendu = np.column_stack(arguments)
    correct = len(collections) == 1 and egal(collections[0].get_offsets(), attendu)
    return correct, "Nuage de points incorrect." if not correct else "Réponse correcte."


def controle_histogramme(obtenu, arguments):
    axes, erreur = verifier_graphique(obtenu)
    if erreur:
        return False, erreur
    nombre_classes = arguments[1] if len(arguments) == 2 else 5
    correct = len(axes[0].patches) == nombre_classes
    return correct, "Nombre de classes incorrect." if not correct else "Réponse correcte."


def controle_comparaison(obtenu, arguments):
    axes, erreur = verifier_graphique(obtenu, nombre_zones=2)
    if erreur:
        return False, erreur
    lignes = axes[0].lines
    correct = (
        len(lignes) == 1
        and egal(lignes[0].get_xdata(), arguments[0])
        and egal(lignes[0].get_ydata(), arguments[1])
        and len(axes[1].patches) == 5
    )
    return correct, "Sous-graphiques incorrects." if not correct else "Réponse correcte."


def test_tracer_evolution(module):
    return executer_test_graphique(
        module,
        "tracer_evolution",
        controle_evolution,
        [
            ("valeurs décimales", ([0, 1, 2], [20.1, 20.4, 20.2])),
            ("une mesure", ([5], [-2.5])),
        ],
    )


def test_annoter_courbe(module):
    return executer_test_graphique(
        module,
        "annoter_courbe",
        controle_annotations,
        [("courbe annotée", ([0, 2, 4], [18.0, 19.5, 21.0]))],
    )


def test_tracer_nuage(module):
    return executer_test_graphique(
        module,
        "tracer_nuage",
        controle_nuage,
        [
            ("relation croissante", ([1, 2, 3], [0.1, 0.2, 0.31])),
            ("valeurs négatives", ([-1, 0, 1], [2, -2, 3])),
        ],
    )


def test_tracer_histogramme(module):
    return executer_test_graphique(
        module,
        "tracer_histogramme",
        controle_histogramme,
        [
            ("nombre par défaut", ([1, 2, 2, 3, 4],)),
            ("trois classes", ([0, 1, 2, 3], 3)),
        ],
    )


def test_creer_comparaison(module):
    return executer_test_graphique(
        module,
        "creer_comparaison",
        controle_comparaison,
        [("deux représentations", ([0, 1, 2, 3], [20, 21, 19, 22]))],
    )


def test_exporter_courbe(module):
    fonction, erreur = fonction_du_module(module, "exporter_courbe")
    if erreur:
        return erreur
    appels = []
    originale = plt.savefig

    def memoriser(chemin, *arguments, **options):
        appels.append((chemin, options))

    plt.savefig = memoriser
    plt.close("all")
    try:
        retour = fonction("resultat.png", [0, 1], [20.0, 21.0])
        figures = [plt.figure(numero) for numero in plt.get_fignums()]
        ax = figures[-1].axes[0] if figures and figures[-1].axes else None
        correct = (
            retour is None
            and len(appels) == 1
            and str(appels[0][0]) == "resultat.png"
            and appels[0][1].get("dpi") == 300
            and appels[0][1].get("bbox_inches") == "tight"
            and ax is not None
            and ax.get_xlabel() == "Temps (s)"
            and ax.get_ylabel() == "Température (°C)"
        )
        message = "Export ou annotations incorrects." if not correct else "Réponse correcte."
        return [resultat("export PNG", correct, message)]
    except Exception as exc:
        return [resultat("export PNG", False, f"Erreur : {type(exc).__name__}: {exc}")]
    finally:
        plt.savefig = originale
        plt.close("all")


class FauxPort:
    def __init__(self, reponses=()):
        self.reponses = list(reponses)
        self.ecritures = []

    def readline(self):
        return self.reponses.pop(0)

    def write(self, donnees):
        self.ecritures.append(donnees)
        return len(donnees)


def creer_test_simple(nom, cas):
    def tester(module):
        fonction, erreur = fonction_du_module(module, nom)
        if erreur:
            return erreur
        resultats = []
        for description, arguments, attendu in cas:
            try:
                obtenu = fonction(*deepcopy(arguments))
                correct = type(obtenu) is type(attendu) and egal(obtenu, attendu)
                message = "Réponse correcte." if correct else f"Attendu : {attendu!r}, obtenu : {obtenu!r}."
                resultats.append(resultat(description, correct, message))
            except Exception as exc:
                resultats.append(resultat(
                    description, False, f"Erreur : {type(exc).__name__}: {exc}"
                ))
        return resultats
    return tester


def test_lire_mesures(module):
    fonction, erreur = fonction_du_module(module, "lire_mesures")
    if erreur:
        return erreur
    cas = [
        ("trois mesures", [b"20.1\r\n", b"21\n", b"-2.5\r\n"], 3,
         [20.1, 21.0, -2.5]),
        ("aucune mesure", [], 0, []),
    ]
    resultats = []
    for description, reponses, nombre, attendu in cas:
        port = FauxPort(reponses)
        try:
            obtenu = fonction(port, nombre)
            correct = type(obtenu) is list and egal(obtenu, attendu) and not port.reponses
            message = "Réponse correcte." if correct else f"Résultat incorrect : {obtenu!r}."
            resultats.append(resultat(description, correct, message))
        except Exception as exc:
            resultats.append(resultat(
                description, False, f"Erreur : {type(exc).__name__}: {exc}"
            ))
    return resultats


def test_interroger_instrument(module):
    fonction, erreur = fonction_du_module(module, "interroger_instrument")
    if erreur:
        return erreur
    port = FauxPort([b"ACME,MODEL 1,123\r\n"])
    try:
        obtenu = fonction(port, "*IDN?")
        correct = obtenu == "ACME,MODEL 1,123" and port.ecritures == [b"*IDN?\n"]
        message = "Réponse correcte." if correct else "Commande envoyée ou réponse incorrecte."
        return [resultat("requête d'identification", correct, message)]
    except Exception as exc:
        return [resultat(
            "requête d'identification", False,
            f"Erreur : {type(exc).__name__}: {exc}",
        )]


DEFINITIONS = [
    ("s4-tracer-evolution", "Tracer l'évolution d'une mesure",
     "tracer_evolution", test_tracer_evolution),
    ("s4-annoter-courbe", "Produire un graphique scientifique",
     "annoter_courbe", test_annoter_courbe),
    ("s4-tracer-nuage", "Étudier la relation entre deux grandeurs",
     "tracer_nuage", test_tracer_nuage),
    ("s4-tracer-histogramme", "Observer une distribution",
     "tracer_histogramme", test_tracer_histogramme),
    ("s4-creer-comparaison", "Comparer deux représentations",
     "creer_comparaison", test_creer_comparaison),
    ("s4-exporter-courbe", "Exporter une courbe",
     "exporter_courbe", test_exporter_courbe),
    ("s4-decoder-mesure", "Décoder une mesure reçue", "decoder_mesure",
     creer_test_simple("decoder_mesure", [
         ("fin de ligne Windows", (b"20.5\r\n",), 20.5),
         ("espaces et valeur négative", (b"  -2.25\n",), -2.25),
     ])),
    ("s4-encoder-commande", "Préparer une commande", "encoder_commande",
     creer_test_simple("encoder_commande", [
         ("identification", ("*IDN?",), b"*IDN?\n"),
         ("mesure", ("MEAS:TEMP?",), b"MEAS:TEMP?\n"),
     ])),
    ("s4-lire-mesures", "Lire une série de mesures",
     "lire_mesures", test_lire_mesures),
    ("s4-interroger-instrument", "Interroger un instrument",
     "interroger_instrument", test_interroger_instrument),
]


EXERCICES_SEANCE4 = [
    Exercise(
        identifiant,
        "4",
        f"Exercice {numero} — {titre}",
        f"s4_ex{numero}.py",
        nom,
        test,
    )
    for numero, (identifiant, titre, nom, test)
    in enumerate(DEFINITIONS, start=1)
]
