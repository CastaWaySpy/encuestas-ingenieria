# Encuestas de Ingeniería en Sistemas

Aplicación web (Flask + PostgreSQL) para recopilar encuestas, calcular estadísticas y generar una estrategia de marketing con Gemini API.

## Publicar en Render (GitHub → Render)

### 1. Sube el proyecto a GitHub
Desde la carpeta `encuestas_ingenieria` (la que contiene `app.py`):

```bash
git init
git add .
git commit -m "Versión PostgreSQL lista para Render"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/encuestas-ingenieria.git
git push -u origin main
```

Antes del `git add .` confirma que `.env` y `.venv/` **no** aparezcan en `git status` (el `.gitignore` ya los excluye).

### 2. Crea la base de datos PostgreSQL
Elige una opción y copia su **URL de conexión** (empieza con `postgresql://`):

- **Render PostgreSQL (plan Free):** Dashboard → New → PostgreSQL. Usa la *Internal Database URL* si la base y la app están en la misma región. Ojo: la base gratuita de Render **expira a los 30 días** de crearse, así que no sirve para guardar datos reales de forma permanente.
- **Neon o Supabase (plan gratuito):** su base gratuita no expira. Copia la cadena de conexión y, si no la incluye, añade `?sslmode=require` al final.

### 3. Crea el servicio web en Render
1. Dashboard → New → **Blueprint** → elige tu repositorio (Render lee `render.yaml`).
   También puedes usar New → Web Service con: *Build* `pip install -r requirements.txt` y *Start* `gunicorn app:app --workers 1 --threads 4 --timeout 120`.
2. Completa las variables de entorno que te pida:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | la URL del paso 2 |
| `GEMINI_API_KEY` | tu clave de Google AI Studio |
| `GEMINI_MODEL` | `gemini-2.5-flash` (o el que tengas disponible) |
| `ADMIN_PASSWORD` | contraseña para entrar a "Estrategia con IA" (recomendado) |
| `FLASK_SECRET_KEY` | se genera sola con el Blueprint |

3. Deploy. Las tablas se crean automáticamente al primer arranque.
4. Verifica `https://TU-APP.onrender.com/healthz` (debe responder `ok`) y luego la página principal.

Notas del plan gratuito de Render: el servicio se duerme tras ~15 minutos sin visitas y la primera petición posterior tarda cerca de un minuto en despertar.

## Seguridad
- La app no tiene inicio de sesión. Si defines `ADMIN_PASSWORD`, la sección **Estrategia con IA** (la que consume tu cuota de Gemini) pide contraseña; el usuario puede ser cualquiera. Sin esa variable queda abierta.
- Nunca subas `.env` a GitHub. Si una clave se compartió por error, genera una nueva.

## Uso local (Windows)
Requisitos: Python 3.12 y PostgreSQL.

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

Edita `.env` (`DB_*` con tu PostgreSQL local, o `DATABASE_URL`), crea una base vacía llamada `encuestas_ingenieria` y ejecuta:

```bat
python app.py
```

Abre http://127.0.0.1:5000. Las tablas se crean solas; `schema.sql` es opcional.

## Pruebas
```bat
pytest
```
