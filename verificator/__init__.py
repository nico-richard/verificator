import hmac
import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for

from .correction.engine import CorrectionEngine
from .exercises import EXERCISES, SESSIONS
from .qcm import CHOICES, QUESTION_COUNT, QCM_KEYS, save_submission
from .teacher import teacher as teacher_blueprint


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(MAX_UPLOAD_BYTES=64 * 1024, EXECUTION_TIMEOUT=3,
                            ACCESS_PASSWORD=os.environ.get("VERIFICATOR_PASSWORD", ""),
                            TEACHER_PASSWORD=os.environ.get("VERIFICATOR_TEACHER_PASSWORD", ""),
                            SECRET_KEY=os.environ.get("VERIFICATOR_SECRET_KEY", "change-me"),
                            QCM_DATABASE=os.environ.get("VERIFICATOR_QCM_DATABASE")
                            or os.path.join(app.instance_path, "qcm.sqlite3"))
    if test_config:
        app.config.update(test_config)
    engine = CorrectionEngine(timeout=app.config["EXECUTION_TIMEOUT"])
    app.register_blueprint(teacher_blueprint)

    @app.before_request
    def require_login():
        if request.blueprint == "teacher":
            return None
        if not app.config["ACCESS_PASSWORD"]:
            return "Le mot de passe Verificator n'est pas configuré.", 503
        if request.endpoint not in {"login", "static"} and not session.get("authenticated"):
            return redirect(url_for("login"))

    @app.route("/connexion", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            if hmac.compare_digest(request.form.get("password", ""), app.config["ACCESS_PASSWORD"]):
                session["authenticated"] = True
                return redirect(url_for("index"))
            error = "Mot de passe incorrect."
        return render_template("login.html", error=error)

    @app.get("/deconnexion")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    def index():
        return render_template("index.html", sessions=SESSIONS, exercises=EXERCISES)

    @app.route("/qcm", methods=["GET", "POST"])
    def qcm():
        student_name = request.form.get("student_name", "").strip()
        questionnaire = request.form.get("questionnaire", "")
        version = request.form.get("version", "")
        answers = {number: request.form.get(f"question_{number}", "")
                   for number in range(1, QUESTION_COUNT + 1)}
        error = None
        if request.method == "POST":
            if (len(request.form.getlist("questionnaire")) != 1 or questionnaire not in QCM_KEYS
                    or len(request.form.getlist("version")) != 1 or version not in ("A", "B")):
                error = "Veuillez sélectionner le questionnaire et la version A ou B présentés en cours."
            elif not student_name or len(student_name) > 120:
                error = "Veuillez renseigner votre nom et prénom (120 caractères maximum)."
            elif any(len(request.form.getlist(f"question_{number}")) != 1
                     or answer not in CHOICES for number, answer in answers.items()):
                error = "Veuillez choisir une seule réponse par question, parmi A, B, C et D, pour les 15 questions."
            else:
                try:
                    save_submission(app.config["QCM_DATABASE"], student_name, answers, questionnaire, version)
                except (OSError, sqlite3.Error):
                    app.logger.exception("Impossible d'enregistrer les réponses au QCM")
                    error = "L’enregistrement a échoué. Vos réponses sont conservées dans le formulaire : veuillez réessayer."
                else:
                    flash("Vos réponses ont bien été enregistrées. Merci !", "qcm_success")
                    return redirect(url_for("qcm"))
        return render_template("qcm.html", question_count=QUESTION_COUNT, choices=CHOICES,
                               student_name=student_name, answers=answers, error=error,
                               questionnaires=QCM_KEYS, questionnaire=questionnaire, version=version)

    @app.post("/corriger")
    def correct():
        exercise_id = request.form.get("exercise", "")
        uploaded = request.files.get("file")
        error = None
        result = None
        source_code = None
        exercise = EXERCISES.get(exercise_id)
        if not exercise:
            error = "Séance ou exercice inconnu."
        elif not uploaded or not uploaded.filename:
            error = "Veuillez sélectionner un fichier Python."
        elif not uploaded.filename.lower().endswith(".py"):
            error = "Le fichier doit avoir l'extension .py."
        elif uploaded.filename != exercise.filename:
            error = (
                f"Le fichier de cet exercice doit s'appeler {exercise.filename}."
            )
        else:
            data = uploaded.read()
            if len(data) > app.config["MAX_UPLOAD_BYTES"]:
                error = "Le fichier dépasse la taille maximale autorisée (64 Ko)."
            else:
                source_code = data.decode("utf-8", errors="replace")
                result = engine.correct(exercise, data)
        return render_template("index.html", sessions=SESSIONS, exercises=EXERCISES,
                               selected=exercise_id, error=error, result=result,
                               source_code=source_code)

    return app
