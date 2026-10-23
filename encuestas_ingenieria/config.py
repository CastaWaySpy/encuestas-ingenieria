import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

EN_RENDER = bool(os.getenv("RENDER"))  # Render define esta variable automáticamente


def _database_uri():
    """Devuelve la URI de PostgreSQL.

    - En Render, Neon o Supabase basta con la variable DATABASE_URL.
    - En local puedes usar DATABASE_URL o las variables DB_HOST, DB_PORT, DB_USER,
      DB_PASSWORD y DB_NAME.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # Algunos proveedores entregan "postgres://", que SQLAlchemy 2.x no acepta.
        for prefijo in ("postgres://", "postgresql://"):
            if url.startswith(prefijo):
                return "postgresql+psycopg2://" + url[len(prefijo):]
        if url.startswith("postgresql+psycopg2://"):
            return url
        raise RuntimeError(
            "DATABASE_URL debe ser una URL de PostgreSQL (empieza con postgresql://). "
            "Si todavía tienes una URL de MySQL en tu archivo .env, reemplázala o bórrala."
        )
    usuario = quote_plus(os.getenv("DB_USER", "postgres"))
    clave = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "localhost")
    puerto = os.getenv("DB_PORT", "5432")
    nombre = os.getenv("DB_NAME", "encuestas_ingenieria")
    return f"postgresql+psycopg2://{usuario}:{clave}@{host}:{puerto}/{nombre}"


def _secret_key():
    clave = os.getenv("FLASK_SECRET_KEY", "").strip()
    if clave:
        return clave
    if EN_RENDER:
        raise RuntimeError("Falta FLASK_SECRET_KEY en las variables de entorno de Render.")
    return "cambia-esta-clave-local"


class Config:
    SECRET_KEY = _secret_key()
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Las bases gratuitas cierran conexiones inactivas; esto las revalida antes de usarlas.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    WTF_CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = EN_RENDER  # solo HTTPS en producción
