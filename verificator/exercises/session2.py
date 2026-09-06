"""Contrats et tests des dix exercices de la séance 2."""
from copy import deepcopy
from dataclasses import dataclass
from math import isclose


@dataclass(frozen=True)
class Exercise:
    id: str
    session: str
    title: str
    function_name: str
    test_module: callable


CAS_EXERCICES = [('s2-convertir-c-en-k',
  'Démarrer le capteur de température',
  'convertir_c_en_k',
  [('valeur positive', (20,), 293.15),
   ('zéro Celsius', (0,), 273.15),
   ('zéro absolu', (-273.15,), 0.0),
   ('valeur décimale', (12.5,), 285.65)]),
 ('s2-convertir-depuis-m',
  'Adapter les unités de distance',
  'convertir_depuis_m',
  [('unité par défaut', (2.5,), 2.5),
   ('mètres', (3, 'm'), 3),
   ('centimètres', (2.5, 'cm'), 250.0),
   ('kilomètres', (500, 'km'), 0.5),
   ('zéro', (0, 'cm'), 0)]),
 ('s2-deplacer',
  'Positionner un capteur',
  'deplacer',
 [('déplacement', ((2, 3), -1, 4), (1, 7)),
   ('nul', ((1, -2), 0, 0), (1, -2)),
   ('négatifs', ((-3, -4), -2, 1), (-5, -3)),
   ('décimaux', ((1.5, 2.5), 0.5, -0.5), (2.0, 2.0))]),
 ('s2-moyenne',
  'Produire le premier bilan',
  'moyenne',
  [('série simple', ([10, 12, 14],), 12.0),
   ('valeur unique', ([5],), 5.0),
   ('négatifs', ([-8, -4],), -6.0),
   ('moyenne non entière', ([1, 2, 2],), 1.6666666666666667),
   ('décimaux', ([1.5, 2.5],), 2.0)]),
 ('s2-analyser-phrase',
  'Lire un message de la station',
  'analyser_phrase',
  [('deux mots', ('alpha beta',), ('a', 'alpha', ' beta', ['alpha', 'beta'])),
   ('texte court', ('abc',), ('a', 'abc', 'abc', ['abc'])),
   ('vide', ('',), ('', '', '', [])),
   ('espaces', ('  a  b c  ',), (' ', '  a  ', 'b c  ', ['a', 'b', 'c'])),
   ('mot long', ('abcdef',), ('a', 'abcde', 'bcdef', ['abcdef']))]),
 ('s2-generer-mesures',
  'Simuler une campagne de mesures',
  'generer_mesures',
  [('croissante', (10, 3, 4), [10, 13, 16, 19]),
   ('décroissante', (5, -2, 3), [5, 3, 1]),
   ('vide', (10, 3, 0), []),
   ('unique', (5, 2, 1), [5]),
   ('constant', (2, 0, 3), [2, 2, 2])]),
 ('s2-maximum',
  'Repérer le pic de mesure',
  'maximum',
  [('milieu', ([3, 1, 8, 2],), 8),
   ('négatifs', ([-4, -2, -9],), -2),
   ('unique', ([7],), 7),
   ('début', ([9, 2, 1],), 9),
   ('fin', ([1, 2, 9],), 9),
   ('doublons', ([4, 4, 2],), 4)]),
 ('s2-nettoyer-noms',
  'Enregistrer les capteurs',
  'nettoyer_noms',
  [('nettoyage', ('  Alice ; ; Bob ;Charlie  ',), ['Alice', 'Bob', 'Charlie']),
   ('vide', ('',), []),
   ('séparateurs', (' ; ; ',), []),
   ('doublons', ('Alice;Alice',), ['Alice', 'Alice']),
   ('espace intérieur', (' Jean Paul ; Bob ',), ['Jean Paul', 'Bob'])]),
 ('s2-atteindre-objectif',
  'Suivre la recharge de la batterie',
  'atteindre_objectif',
  [('dépassement', (10, 7, 30), (3, 31)),
   ('déjà dépassé', (40, 7, 30), (0, 40)),
   ('égalité initiale', (10, 2, 10), (0, 10)),
   ('exact', (0, 5, 20), (4, 20)),
   ('une étape', (0, 10, 3), (1, 10))]),
 ('s2-premiere-mesure-superieure',
  'Déclencher la première alerte',
  'premiere_mesure_superieure',
  [('première alerte', ([-2, 5, 4, 7, 9], 5), 3),
   ('vide', ([], 5), -1),
   ('aucune', ([1, 4, 5], 5), -1),
   ('négatives', ([-4, -2], -3), -1),
   ('seuil négatif', ([-2, 0], -3), 1),
   ('début', ([8, 9], 5), 0),
   ('fin', ([-1, 2, 9], 5), 2)])]


def resultats_egaux(obtenu, attendu):
    if isinstance(attendu, (tuple, list)):
        return (type(obtenu) is type(attendu)
                and len(obtenu) == len(attendu)
                and all(resultats_egaux(a, b) for a, b in zip(obtenu, attendu)))
    if isinstance(attendu, (int, float)):
        return (type(obtenu) in (int, float)
                and isclose(obtenu, attendu, rel_tol=1e-9, abs_tol=1e-9))
    return type(obtenu) is type(attendu) and obtenu == attendu


def creer_test(nom, cas):
    def tester(module):
        fonction = getattr(module, nom, None)
        if not callable(fonction):
            return [{"name": "fonction " + nom, "passed": False,
                     "message": "Fonction absente."}]
        resultats = []
        for description, arguments, attendu in cas:
            entrees = deepcopy(arguments)
            try:
                obtenu = fonction(*entrees)
                correct = resultats_egaux(obtenu, attendu)
                intact = entrees == arguments
                message = "Réponse correcte."
                if not correct:
                    message = f"Attendu : {attendu!r}, obtenu : {obtenu!r}."
                elif not intact:
                    message = "Les données reçues ne doivent pas être modifiées."
                resultats.append({"name": description, "passed": correct and intact,
                                  "message": message})
            except Exception as exc:
                resultats.append({"name": description, "passed": False,
                                  "message": f"Erreur : {type(exc).__name__}: {exc}"})
        return resultats
    return tester


EXERCICES_SEANCE2 = [
    Exercise(identifiant, "2", f"Exercice {numero} — {titre}", nom,
             creer_test(nom, cas))
    for numero, (identifiant, titre, nom, cas)
    in enumerate(CAS_EXERCICES, start=1)
]
# Compatibilité avec l'identifiant et l'import historiques de Verificator.
moyenne_exercise = next(
    exercice for exercice in EXERCICES_SEANCE2
    if exercice.function_name == "moyenne"
)
test_moyenne = moyenne_exercise.test_module
