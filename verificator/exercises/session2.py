from dataclasses import dataclass


@dataclass(frozen=True)
class Exercise:
    id: str
    session: str
    title: str
    function_name: str
    test_module: callable


def test_moyenne(module):
    function = getattr(module, "moyenne", None)
    if not callable(function):
        return [{"name": "fonction moyenne", "passed": False, "message": "Fonction absente."}]
    cases = [("liste simple", [10, 20, 30], 20), ("valeur unique", [7], 7), ("décimaux", [1, 2, 2], 5 / 3)]
    results = []
    for name, values, expected in cases:
        try:
            actual = function(values)
            passed = actual == expected
            results.append({"name": name, "passed": passed, "message": "Réponse correcte." if passed else f"Attendu : {expected}, obtenu : {actual}."})
        except Exception as exc:
            results.append({"name": name, "passed": False, "message": f"Erreur : {type(exc).__name__}: {exc}"})
    return results


moyenne_exercise = Exercise("s2-moyenne", "2", "Calculer une moyenne", "moyenne", test_moyenne)
