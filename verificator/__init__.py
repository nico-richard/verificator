import hmac
import os
from flask import Flask, redirect, render_template, request, session, url_for

from .correction.engine import CorrectionEngine
from .exercises import EXERCISES, SESSIONS


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(MAX_UPLOAD_BYTES=64 * 1024, EXECUTION_TIMEOUT=3,
                            ACCESS_PASSWORD=os.environ.get("VERIFICATOR_PASSWORD", ""),
                            SECRET_KEY=os.environ.get("VERIFICATOR_SECRET_KEY", "change-me"))
    if test_config:
        app.config.update(test_config)
    engine = CorrectionEngine(timeout=app.config["EXECUTION_TIMEOUT"])

    @app.before_request
    def require_login():
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

    @app.post("/corriger")
    def correct():
        exercise_id = request.form.get("exercise", "")
        uploaded = request.files.get("file")
        error = None
        result = None
        exercise = EXERCISES.get(exercise_id)
        if not exercise:
            error = "Séance ou exercice inconnu."
        elif not uploaded or not uploaded.filename:
            error = "Veuillez sélectionner un fichier Python."
        elif not uploaded.filename.lower().endswith(".py"):
            error = "Le fichier doit avoir l'extension .py."
        else:
            data = uploaded.read()
            if len(data) > app.config["MAX_UPLOAD_BYTES"]:
                error = "Le fichier dépasse la taille maximale autorisée (64 Ko)."
            else:
                result = engine.correct(exercise, data)
        return render_template("index.html", sessions=SESSIONS, exercises=EXERCISES,
                               selected=exercise_id, error=error, result=result)

    return app
