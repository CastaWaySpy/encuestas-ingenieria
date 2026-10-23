import os
from google import genai
from google.genai import types

class GeminiServiceError(Exception):
    pass

def generate_strategy(stats):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()
    if not api_key:
        raise GeminiServiceError("No se configuró GEMINI_API_KEY (archivo .env en local o variables de entorno en Render).")
    if not model:
        raise GeminiServiceError("No se configuró GEMINI_MODEL. Indica un modelo de Gemini disponible para tu clave API.")
    if not stats.get("total_surveys"):
        raise GeminiServiceError("No hay encuestas para analizar.")
    client = genai.Client(api_key=api_key)
    prompt = f"""
Actúa como especialista en marketing educativo y análisis estadístico en Guatemala.
Genera en español una estrategia de marketing práctica para aumentar el alcance de la carrera de Ingeniería en Sistemas de la Universidad Mariano Gálvez de Guatemala.

DATOS ESTADÍSTICOS CALCULADOS POR LA APLICACIÓN (fuente de verdad):
{stats}

Reglas:
- Basa los hallazgos únicamente en estos datos.
- Diferencia hallazgos, interpretación y recomendaciones.
- No inventes encuestados, porcentajes ni campañas previas.
- No confundas frecuencia de menciones con alcance real ni causalidad.
- El total actual de encuestas es {stats.get('total_surveys')}; advierte que una muestra pequeña puede no ser representativa.
- Presupuestos en quetzales son estimaciones de planificación, no cotizaciones oficiales.
- Si faltan datos, indícalo y propone cómo obtenerlos.
- No recibiste datos individuales ni comentarios; no inventes citas.
- No devuelvas HTML. Usa Markdown seguro con títulos, listas y tablas sencillas.

Incluye: 1) resumen ejecutivo, 2) diagnóstico estadístico, 3) público objetivo e información por validar,
4) objetivo general y al menos cuatro objetivos específicos medibles, con línea base y plazos,
5) estrategias por canal justificadas, 6) tabla de plan de acción con actividad, canal, objetivo, público,
responsable sugerido, recursos, presupuesto Q, periodo, KPI y resultado esperado, 7) calendario de 90 días,
8) presupuesto bajo/medio/alto, 9) KPI y método de medición, 10) evaluación y mejora continua,
11) riesgos y limitaciones, 12) recomendaciones prioritarias.
Cuando no exista una línea base de marketing, propone medirla antes de fijar metas numéricas definitivas.
"""
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.35,
                max_output_tokens=7000
            )
        )
        content = (response.text or "").strip()
        if not content:
            raise GeminiServiceError("Gemini respondió sin contenido. Inténtalo nuevamente.")
        return content, model
    except GeminiServiceError:
        raise
    except Exception as exc:
        # Do not expose API keys, request headers or provider internals to the browser.
        message = str(exc).lower()
        if "api key" in message or "unauthenticated" in message or "permission" in message:
            raise GeminiServiceError("Gemini rechazó la autenticación. Verifica GEMINI_API_KEY y los permisos de tu proyecto.")
        if "quota" in message or "rate" in message or "resource_exhausted" in message:
            raise GeminiServiceError("Se alcanzó un límite de uso de Gemini. Revisa las cuotas y vuelve a intentarlo más tarde.")
        raise GeminiServiceError("No se pudo conectar con Gemini. Comprueba tu conexión, el nombre del modelo y la configuración de la API.")
