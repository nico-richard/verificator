import ast
import importlib.util
import json
import sys

from verificator.exercises import EXERCISES


def verifier_consignes(source):
    arbre = ast.parse(source)

    for noeud in ast.walk(arbre):
        if (isinstance(noeud, ast.Call) and isinstance(noeud.func, ast.Name)
                and noeud.func.id in {"input", "print"}):
            return f"L'appel à {noeud.func.id}() n'est pas autorisé dans le fichier remis."

    for instruction in arbre.body:
        if isinstance(instruction, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if any(isinstance(noeud, ast.Call) for noeud in ast.walk(instruction)):
            return "Aucun appel de fonction ne doit être exécuté au chargement du fichier."

    return None


def main():
    path, exercise_id = sys.argv[1:3]
    exercise = EXERCISES[exercise_id]
    try:
        with open(path, encoding="utf-8") as fichier:
            source = fichier.read()
        erreur = verifier_consignes(source)
    except (OSError, SyntaxError, UnicodeError) as exc:
        print(json.dumps({"status": "python_error",
                          "message": f"{type(exc).__name__}: {exc}", "tests": []},
                         ensure_ascii=False))
        return
    if erreur:
        print(json.dumps({"status": "python_error", "message": erreur, "tests": []},
                         ensure_ascii=False))
        return
    spec = importlib.util.spec_from_file_location("student_submission", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        print(json.dumps({"status": "ok", "tests": exercise.test_module(module)}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"status": "python_error", "message": f"{type(exc).__name__}: {exc}", "tests": []}, ensure_ascii=False))


if __name__ == "__main__":
    main()
