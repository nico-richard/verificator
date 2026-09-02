import importlib.util
import json
import sys

from verificator.exercises import EXERCISES


def main():
    path, exercise_id = sys.argv[1:3]
    exercise = EXERCISES[exercise_id]
    spec = importlib.util.spec_from_file_location("student_submission", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        print(json.dumps({"status": "ok", "tests": exercise.test_module(module)}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"status": "python_error", "message": f"{type(exc).__name__}: {exc}", "tests": []}, ensure_ascii=False))


if __name__ == "__main__":
    main()
