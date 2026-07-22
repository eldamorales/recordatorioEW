"""
enviar_recordatorio.py
=======================
Envía recordatorios a Telegram según lo definido en `recordatorios.json`.

Soporta tres tipos de recordatorio (se pueden mezclar en el mismo archivo):
  - "fijo" : envía un mensaje de texto tal cual.
  - "lista": no es un tipo por separado; simplemente pon varios recordatorios
             en el arreglo del JSON, cada uno con su propio horario/días.
  - "ia"   : genera el mensaje con la API de Claude en cada ejecución
             (requiere ANTHROPIC_API_KEY; si falta, se omite con aviso).

¿Dónde se ejecuta?
  - En GitHub Actions (nube, programado) — ver .github/workflows/recordatorio.yml
  - También localmente:  python enviar_recordatorio.py
  - Prueba sin enviar nada:  python enviar_recordatorio.py --simular

Credenciales (nunca en el código):
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  y opcional  ANTHROPIC_API_KEY
  En local viven en un archivo .env; en GitHub, en Settings → Secrets.

Autora del paquete base: Dra. Elda C. Morales — proyecto "Agentes de negocio".
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

# --- Carga opcional de .env para ejecución local -----------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # En GitHub Actions no hace falta dotenv: las llaves llegan como env vars.
    pass

# Lunes=0 ... Domingo=6  ->  abreviatura usada en recordatorios.json
DIAS_SEMANA = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
LIMITE_TELEGRAM = 4096  # máximo de caracteres por mensaje de Telegram


# ---------------------------------------------------------------------------
# 1. Utilidades
# ---------------------------------------------------------------------------
def cargar_config(ruta: str) -> dict:
    """Lee y valida el archivo de configuración de recordatorios."""
    if not os.path.exists(ruta):
        sys.exit(f"ERROR: no se encontró el archivo de configuración: {ruta}")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: el JSON tiene un error de sintaxis: {e}")
    if "recordatorios" not in config or not isinstance(config["recordatorios"], list):
        sys.exit('ERROR: el archivo debe tener una lista bajo la clave "recordatorios".')
    return config


def hoy_abreviado(zona: str) -> str:
    """Devuelve la abreviatura del día actual ('lun', 'mar', ...) en la zona dada."""
    try:
        from zoneinfo import ZoneInfo
        ahora = dt.datetime.now(ZoneInfo(zona))
    except Exception:
        # Si la zona no es válida o no hay tzdata, usa hora del sistema (UTC en Actions).
        ahora = dt.datetime.utcnow()
        print(f"AVISO: no se pudo usar la zona '{zona}'; se usa hora del sistema.")
    return DIAS_SEMANA[ahora.weekday()]


def toca_hoy(recordatorio: dict, hoy: str) -> bool:
    """Decide si un recordatorio debe enviarse hoy según su campo 'dias'."""
    dias = recordatorio.get("dias", "diario")
    if dias in ("diario", ["diario"]) or dias is None:
        return True
    if isinstance(dias, str):
        dias = [dias]
    return hoy in [d.lower() for d in dias]


# ---------------------------------------------------------------------------
# 2. Generación del texto (fijo o con IA)
# ---------------------------------------------------------------------------
def texto_con_ia(recordatorio: dict) -> str:
    """Genera el mensaje con la API de Claude. Devuelve texto o None si no se pudo."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print(f"  · [{recordatorio['id']}] tipo 'ia' omitido: falta ANTHROPIC_API_KEY.")
        return None
    prompt = recordatorio.get("prompt")
    if not prompt:
        print(f"  · [{recordatorio['id']}] tipo 'ia' sin 'prompt' definido; se omite.")
        return None
    # Modelo por defecto: el de menor costo. Verifica el nombre vigente en
    # https://platform.claude.com/docs/en/about-claude/models/overview
    modelo = recordatorio.get("modelo", "claude-haiku-4-5")
    try:
        import anthropic
        cliente = anthropic.Anthropic(api_key=api_key)
        resp = cliente.messages.create(
            model=modelo,
            max_tokens=recordatorio.get("max_tokens", 300),
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except ImportError:
        print("  · Falta la librería 'anthropic' (pip install anthropic); se omite el de IA.")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"  · [{recordatorio['id']}] error al llamar a la API de Claude: {e}")
        return None


def construir_texto(recordatorio: dict) -> str | None:
    """Devuelve el texto final del recordatorio según su tipo."""
    tipo = recordatorio.get("tipo", "fijo").lower()
    if tipo == "ia":
        texto = texto_con_ia(recordatorio)
        # Si la IA falla y hay un 'mensaje' de respaldo, se usa ese.
        return texto or recordatorio.get("mensaje")
    # tipo 'fijo' (o cualquier otro): usa el campo 'mensaje'
    return recordatorio.get("mensaje")


# ---------------------------------------------------------------------------
# 3. Envío a Telegram
# ---------------------------------------------------------------------------
def enviar_telegram(token: str, chat_id: str, texto: str) -> bool:
    """Envía un mensaje usando la Bot API de Telegram (método sendMessage)."""
    if len(texto) > LIMITE_TELEGRAM:
        texto = texto[: LIMITE_TELEGRAM - 20] + "\n… (mensaje recortado)"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    datos = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": texto,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    try:
        with urllib.request.urlopen(url, data=datos, timeout=30) as r:
            respuesta = json.loads(r.read().decode("utf-8"))
        if not respuesta.get("ok"):
            print(f"  · Telegram rechazó el envío: {respuesta}")
            return False
        return True
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "ignore")
        print(f"  · Error HTTP {e.code} al enviar a Telegram: {detalle}")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"  · No se pudo conectar con Telegram: {e}")
        return False


# ---------------------------------------------------------------------------
# 4. Flujo principal
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Envía recordatorios a Telegram.")
    parser.add_argument("--config", default="recordatorios.json",
                        help="Ruta al archivo de configuración (por defecto recordatorios.json).")
    parser.add_argument("--simular", action="store_true",
                        help="No envía nada: solo imprime lo que enviaría.")
    parser.add_argument("--forzar", action="store_true",
                        help="Ignora el filtro de días y procesa todos los recordatorios activos.")
    args = parser.parse_args()

    config = cargar_config(args.config)
    zona = config.get("zona_horaria", "America/Mexico_City")
    hoy = hoy_abreviado(zona)
    print(f"Zona horaria: {zona} · Día de hoy: {hoy} · "
          f"{'MODO SIMULACIÓN' if args.simular else 'ENVÍO REAL'}")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not args.simular and (not token or not chat_id):
        sys.exit("ERROR: faltan TELEGRAM_BOT_TOKEN y/o TELEGRAM_CHAT_ID "
                 "(revisa tu .env o los Secrets de GitHub).")

    enviados, omitidos = 0, 0
    for r in config["recordatorios"]:
        rid = r.get("id", "sin-id")
        if not r.get("activo", True):
            omitidos += 1
            continue
        if not args.forzar and not toca_hoy(r, hoy):
            omitidos += 1
            continue
        texto = construir_texto(r)
        if not texto:
            print(f"  · [{rid}] sin texto para enviar; se omite.")
            omitidos += 1
            continue
        if args.simular:
            print(f"\n[SIMULACIÓN] [{rid}] enviaría a chat {chat_id or '(no definido)'}:\n{texto}\n")
            enviados += 1
        else:
            ok = enviar_telegram(token, chat_id, texto)
            print(f"  · [{rid}] {'enviado OK' if ok else 'FALLO'}")
            enviados += 1 if ok else 0
            omitidos += 0 if ok else 1

    print(f"\nResumen: {enviados} enviado(s), {omitidos} omitido(s).")


if __name__ == "__main__":
    main()
