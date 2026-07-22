"""
obtener_chat_id.py
==================
Ayuda a descubrir tu TELEGRAM_CHAT_ID (el número del chat al que el bot
enviará los recordatorios).

Cómo usarlo:
  1) Crea tu bot con @BotFather y copia el token.
  2) En Telegram, ábrele conversación a TU bot y envíale cualquier mensaje
     (por ejemplo "hola"). Esto es indispensable: un bot no puede escribirte
     primero.
  3) Ejecuta:  TELEGRAM_BOT_TOKEN=tu_token  python obtener_chat_id.py
     (o pon el token en .env y ejecuta:  python obtener_chat_id.py)
  4) Copia el "chat_id" que aparezca y guárdalo como TELEGRAM_CHAT_ID.

Se ejecuta en: terminal / VS Code / cualquier entorno con Python 3.9+.
"""

import json
import os
import sys
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not token:
    sys.exit("ERROR: define TELEGRAM_BOT_TOKEN (en .env o como variable de entorno).")

url = f"https://api.telegram.org/bot{token}/getUpdates"
try:
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
except Exception as e:  # noqa: BLE001
    sys.exit(f"ERROR al consultar Telegram: {e}")

if not data.get("ok"):
    sys.exit(f"Telegram respondió con error: {data}")

updates = data.get("result", [])
if not updates:
    print("No hay mensajes recientes. Envíale un mensaje a tu bot desde Telegram "
          "y vuelve a ejecutar este script.")
    sys.exit(0)

vistos = set()
print("Chats encontrados (usa el 'chat_id' que corresponda a tu conversación):\n")
for u in updates:
    msg = u.get("message") or u.get("edited_message") or {}
    chat = msg.get("chat", {})
    cid = chat.get("id")
    if cid is None or cid in vistos:
        continue
    vistos.add(cid)
    nombre = chat.get("title") or chat.get("first_name") or chat.get("username") or "(sin nombre)"
    tipo = chat.get("type", "?")
    print(f"  chat_id = {cid}   ·   {nombre}   ·   tipo: {tipo}")

print("\nGuarda el número como TELEGRAM_CHAT_ID en tu .env o en los Secrets de GitHub.")
