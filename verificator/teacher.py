import csv
import hmac
import io
import sqlite3

from flask import Blueprint, Response, current_app, redirect, render_template, request, session, url_for

from .qcm import QUESTION_COUNT, get_submissions


teacher = Blueprint("teacher", __name__, url_prefix="/enseignant")


@teacher.before_request
def require_teacher_login():
    password = current_app.config["TEACHER_PASSWORD"]
    if not password or password == current_app.config["ACCESS_PASSWORD"]:
        return render_template(
            "teacher_login.html",
            unavailable=True,
            error="L’espace enseignant n’est pas configuré. Définissez un mot de passe enseignant distinct du mot de passe étudiant.",
        ), 503
    if not current_app.secret_key or current_app.secret_key == "change-me":
        return render_template(
            "teacher_login.html", unavailable=True,
            error="L’espace enseignant nécessite une clé de session privée configurée par l’administrateur.",
        ), 503
    if request.endpoint != "teacher.login" and not session.get("teacher_authenticated"):
        return redirect(url_for("teacher.login"))


@teacher.after_request
def prevent_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@teacher.route("/connexion", methods=["GET", "POST"])
def login():
    if session.get("teacher_authenticated"):
        return redirect(url_for("teacher.results"))
    error = None
    if request.method == "POST":
        password = request.form.get("password", "").encode("utf-8")
        expected = current_app.config["TEACHER_PASSWORD"].encode("utf-8")
        if hmac.compare_digest(password, expected):
            session["teacher_authenticated"] = True
            return redirect(url_for("teacher.results"))
        error = "Mot de passe enseignant incorrect."
    return render_template("teacher_login.html", error=error)


@teacher.post("/deconnexion")
def logout():
    session.pop("teacher_authenticated", None)
    return redirect(url_for("teacher.login"))


@teacher.get("/qcm")
def results():
    try:
        submissions = get_submissions(current_app.config["QCM_DATABASE"])
    except (OSError, sqlite3.Error, ValueError):
        current_app.logger.exception("Impossible de consulter les réponses au QCM")
        return render_template(
            "teacher_results.html", submissions=[], question_count=QUESTION_COUNT,
            error="Les réponses sont temporairement indisponibles. Veuillez réessayer.",
        ), 503
    return render_template("teacher_results.html", submissions=submissions,
                           question_count=QUESTION_COUNT)


@teacher.get("/qcm/export.csv")
def export_csv():
    try:
        submissions = get_submissions(current_app.config["QCM_DATABASE"])
    except (OSError, sqlite3.Error, ValueError):
        current_app.logger.exception("Impossible d’exporter les réponses au QCM")
        return "L’export est temporairement indisponible. Veuillez réessayer.", 503
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Envoi", "Nom et prénom", "Date (UTC)"]
                    + [f"Q{number}" for number in range(1, QUESTION_COUNT + 1)])
    for submission in submissions:
        name = submission["student_name"]
        # Empêcher les tableurs d'interpréter un nom comme une formule.
        if name.lstrip().startswith(("=", "+", "-", "@")) or name.startswith(("\t", "\r", "\n")):
            name = "'" + name
        writer.writerow([submission["id"], name, submission["submitted_at"]]
                        + [submission["answers"].get(str(number), "")
                           for number in range(1, QUESTION_COUNT + 1)])
    return Response("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="resultats-qcm.csv"'})
