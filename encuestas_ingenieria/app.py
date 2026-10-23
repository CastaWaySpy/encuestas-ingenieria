import os
import hmac
from functools import wraps
from datetime import datetime, date
import json
import markdown
import bleach
from flask import Flask, Response, render_template, request, redirect, url_for, flash, jsonify, abort
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from extensions import db
from models import Survey, SurveyAdditionalMedium, Strategy
from services.estadisticas_service import build_statistics
from services.gemini_service import generate_strategy, GeminiServiceError
from markupsafe import Markup

def render_markdown_seguro(texto):
    html = markdown.markdown(
        texto,
        extensions=["extra", "nl2br"]
    )

    etiquetas_permitidas = [
        "p", "br", "h1", "h2", "h3", "h4",
        "strong", "em", "ul", "ol", "li",
        "blockquote", "code", "pre", "hr"
    ]

    return bleach.clean(
        html,
        tags=etiquetas_permitidas,
        attributes={},
        strip=True
    )

app = Flask(__name__)
app.config.from_object(Config)
# Render pone un proxy delante de la app: así Flask detecta HTTPS y la IP real.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
db.init_app(app)
CSRFProtect(app)

# Crea las tablas si no existen (equivale a ejecutar schema.sql). Es seguro repetirlo.
with app.app_context():
    try:
        db.create_all()
    except SQLAlchemyError:
        app.logger.exception("No se pudieron crear las tablas. Revisa DATABASE_URL.")


def admin_requerido(vista):
    """Si defines ADMIN_PASSWORD, protege la vista con contraseña (HTTP Basic).
    Si no la defines, la vista queda abierta como en la versión local."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        clave = os.getenv("ADMIN_PASSWORD", "")
        if not clave:
            return vista(*args, **kwargs)
        auth = request.authorization
        ingresada = (auth.password or "") if auth else ""
        if not auth or not hmac.compare_digest(ingresada.encode(), clave.encode()):
            return Response("Acceso restringido.", 401,
                            {"WWW-Authenticate": 'Basic realm="Encuestas UMG"'})
        return vista(*args, **kwargs)
    return envoltura

@app.context_processor
def inject_form_options():
    return {"medium_options": Survey.MEDIUM_OPTIONS, "content_options": Survey.CONTENT_OPTIONS}

@app.template_filter("from_json")
def from_json_filter(value):
    try:
        return json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}

@app.template_filter("markdown_safe")
def markdown_safe(texto):
    if not texto:
        return Markup("")

    html = markdown.markdown(
        texto,
        extensions=["extra", "nl2br"]
    )

    etiquetas_permitidas = [
        "h1", "h2", "h3", "h4", "p", "br", "hr",
        "strong", "b", "em", "i", "ul", "ol", "li",
        "blockquote", "code", "pre"
    ]

    html_limpio = bleach.clean(
        html,
        tags=etiquetas_permitidas,
        attributes={},
        strip=True
    )

    return Markup(html_limpio)

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/")
def index():
    stats = build_statistics(db.session)
    return render_template("index.html", stats=stats)

@app.route("/encuesta", methods=["GET", "POST"])
def encuesta():
    if request.method == "POST":
        main_medium = request.form.get("main_medium", "").strip()
        influence_medium = request.form.get("influence_medium", "").strip()
        content_preference = request.form.get("content_preference", "").strip()
        age_raw = request.form.get("age", "").strip()
        sex = request.form.get("sex", "").strip() or None
        comments = request.form.get("comments", "").strip() or None
        additional = request.form.getlist("additional_medium")
        allowed_main = set(Survey.MEDIUM_OPTIONS)
        allowed_content = set(Survey.CONTENT_OPTIONS)
        allowed_sex = {"Femenino", "Masculino", "Otro", "Prefiero no responder"}
        errors = []
        if main_medium not in allowed_main:
            errors.append("Selecciona un medio principal válido.")
        if influence_medium not in allowed_main:
            errors.append("Selecciona un medio de mayor influencia válido.")
        if content_preference not in allowed_content:
            errors.append("Selecciona un tipo de contenido válido.")
        if any(x not in allowed_main for x in additional):
            errors.append("Hay un medio adicional no válido.")
        if sex and sex not in allowed_sex:
            errors.append("Selecciona una opción válida para sexo.")
        age = None
        if age_raw:
            try:
                age = int(age_raw)
                if not 15 <= age <= 100:
                    errors.append("La edad debe estar entre 15 y 100.")
            except ValueError:
                errors.append("La edad debe ser un número entero.")
        if comments and len(comments) > 1000:
            errors.append("Los comentarios no pueden superar 1000 caracteres.")
        if errors:
            for error in errors:
                flash(error, "danger")
            values = request.form.to_dict(flat=True)
            values["additional_medium"] = request.form.getlist("additional_medium")
            return render_template("encuesta.html", values=values)
        try:
            survey = Survey(
                age=age, sex=sex, main_medium=main_medium,
                influence_medium=influence_medium,
                content_preference=content_preference,
                comments=comments
            )
            db.session.add(survey)
            db.session.flush()
            # A medium chosen as the primary discovery channel should not be counted
            # again as an additional medium for this same response.
            for medium in sorted(set(additional) - {main_medium}):
                db.session.add(SurveyAdditionalMedium(survey_id=survey.id, medium=medium))
            db.session.commit()
            flash("La encuesta se registró correctamente. ¡Gracias por participar!", "success")
            return redirect(url_for("encuesta"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("No fue posible guardar la encuesta. Verifica la conexión con la base de datos e inténtalo nuevamente.", "danger")
    return render_template("encuesta.html", values={"additional_medium": []})

@app.get("/resultados")
def resultados():
    stats = build_statistics(db.session)
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = 15
    query = db.select(Survey).order_by(Survey.created_at.desc())
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    medium = request.args.get("medium", "").strip()
    try:
        if start:
            query = query.where(Survey.created_at >= datetime.combine(date.fromisoformat(start), datetime.min.time()))
        if end:
            query = query.where(Survey.created_at < datetime.combine(date.fromisoformat(end), datetime.max.time()))
    except ValueError:
        flash("El rango de fechas no es válido.", "warning")
    if medium in Survey.MEDIUM_OPTIONS:
        query = query.where(Survey.main_medium == medium)
    total = db.session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.session.scalars(query.offset((page - 1) * per_page).limit(per_page)).all()
    return render_template(
        "resultados.html", stats=stats, rows=rows, page=page,
        pages=max(1, (total + per_page - 1) // per_page), total=total,
        start=start, end=end, medium=medium, mediums=Survey.MEDIUM_OPTIONS
    )

@app.get("/api/estadisticas")
def api_estadisticas():
    return jsonify(build_statistics(db.session))

@app.route("/estrategia", methods=["GET", "POST"])
@admin_requerido
def estrategia():
    latest = None
    if request.method == "POST":
        stats = build_statistics(db.session)
        if stats["total_surveys"] == 0:
            flash("Primero registra encuestas reales para generar una estrategia basada en resultados.", "warning")
            return redirect(url_for("estrategia"))
        if stats["total_surveys"] < 5:
            flash("Hay menos de 5 encuestas. Se generará un diagnóstico preliminar con una advertencia sobre el tamaño de la muestra.", "warning")
        try:
            content, model_name = generate_strategy(stats)
            # Store the pending result server-side in the database; keep only its ID in the session cookie.
            item = Strategy(
                stats_json=json.dumps(stats, ensure_ascii=False),
                content=content, model_name=model_name, status="pending"
            )
            db.session.add(item)
            db.session.commit()
            from flask import session
            session["pending_strategy_id"] = item.id
            flash("La estrategia se generó. Revísala y guárdala si deseas conservarla.", "success")
        except GeminiServiceError as exc:
            flash(str(exc), "danger")
        except Exception:
            app.logger.exception("Unexpected error generating Gemini strategy")
            flash("Ocurrió un error inesperado al generar la estrategia. Revisa la configuración y los registros del servidor.", "danger")
    from flask import session
    pending_id = session.get("pending_strategy_id")
    pending = db.session.get(Strategy, pending_id) if pending_id else None
    if pending and pending.status != "pending":
        pending = None
    history = db.session.scalars(select(Strategy).where(Strategy.status == "saved").order_by(Strategy.created_at.desc()).limit(10)).all()
    return render_template("estrategia.html", pending=pending, history=history)

@app.post("/estrategia/guardar")
@admin_requerido
def guardar_estrategia():
    from flask import session
    pending_id = session.get("pending_strategy_id")
    item = db.session.get(Strategy, pending_id) if pending_id else None
    if not item or item.status != "pending":
        flash("No hay una estrategia pendiente para guardar. Genera una primero.", "warning")
        return redirect(url_for("estrategia"))
    try:
        item.status = "saved"
        db.session.commit()
        session.pop("pending_strategy_id", None)
        flash("La estrategia se guardó correctamente.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No se pudo guardar la estrategia en la base de datos.", "danger")
    return redirect(url_for("estrategia"))

@app.get("/estrategias/<int:strategy_id>")
@admin_requerido
def ver_estrategia(strategy_id):
    item = db.get_or_404(Strategy, strategy_id)
    return render_template("ver_estrategia.html", item=item)

@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="No encontramos la página solicitada."), 404

@app.errorhandler(500)
def server_error(_error):
    return render_template("error.html", code=500, message="Ocurrió un error interno. Inténtalo nuevamente."), 500

if __name__ == "__main__":
    # Solo desarrollo local. En Render se usa gunicorn (ver render.yaml).
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
