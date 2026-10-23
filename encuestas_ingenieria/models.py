from datetime import datetime
from zoneinfo import ZoneInfo
from extensions import db


def ahora_gt():
    """Hora local de Guatemala (UTC-6). Render corre en UTC, así que se fija aquí
    para que las fechas guardadas y mostradas sean las mismas que usabas en local."""
    return datetime.now(ZoneInfo("America/Guatemala")).replace(tzinfo=None)


class Survey(db.Model):
    __tablename__ = "surveys"

    MEDIUM_OPTIONS = [
        "Facebook", "Instagram", "TikTok", "YouTube",
        "Página web oficial de la universidad", "Publicidad digital",
        "Recomendación de amigos", "Recomendación de familiares",
        "Recomendación de docentes", "Ferias educativas o visitas a centros educativos",
        "Información proporcionada directamente por la universidad", "Otro medio"
    ]
    CONTENT_OPTIONS = [
        "Videos sobre proyectos de programación", "Testimonios de estudiantes",
        "Historias de graduados y oportunidades laborales", "Información sobre el pensum",
        "Demostraciones de laboratorios y actividades prácticas",
        "Información sobre becas y opciones de financiamiento",
        "Publicaciones sobre tecnología e innovación",
        "Invitaciones a talleres o actividades universitarias", "Otro"
    ]

    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.SmallInteger, nullable=True)
    sex = db.Column(db.String(40), nullable=True)
    main_medium = db.Column(db.String(120), nullable=False, index=True)
    influence_medium = db.Column(db.String(120), nullable=False, index=True)
    content_preference = db.Column(db.String(160), nullable=False, index=True)
    comments = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=ahora_gt, index=True)
    additional_media = db.relationship(
        "SurveyAdditionalMedium", backref="survey",
        cascade="all, delete-orphan", lazy="select"
    )

class SurveyAdditionalMedium(db.Model):
    __tablename__ = "survey_additional_media"
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    medium = db.Column(db.String(120), nullable=False, index=True)
    __table_args__ = (db.UniqueConstraint("survey_id", "medium", name="uq_survey_additional_medium"),)

class Strategy(db.Model):
    __tablename__ = "strategies"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=ahora_gt, index=True)
    stats_json = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
