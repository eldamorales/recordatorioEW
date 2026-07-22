# Recordatorios por Telegram (tarea programada con GitHub Actions)

Paquete para enviarte **recordatorios automáticos a Telegram** en el horario que tú definas, sin mantener ninguna computadora encendida. Está pensado para compartirse: cada colaborador hace su propia copia, pone sus credenciales y edita sus recordatorios.

Autora del paquete base: **Dra. Elda C. Morales** — proyecto *Agentes de negocio*.

---

## 1. Objetivo

Que a una hora programada (por ejemplo, 8:00 a. m. todos los días) llegue a tu Telegram uno o varios recordatorios definidos por ti. El horario y los mensajes se editan en dos archivos de texto; no necesitas saber programar.

## 2. Resultado esperado

Recibes en el chat con tu bot un mensaje como:

> 🔔 Recordatorio: revisar el pipeline de agentes y los pendientes del día.

…en los días y a la hora que hayas configurado.

## 3. Cómo funciona (dos capas de horario)

Hay **dos niveles** que juntos deciden cuándo llega cada mensaje. Es importante entenderlos:

| Capa | Archivo | Qué controla |
|---|---|---|
| **1. Hora** | `.github/workflows/recordatorio.yml` (línea `cron`) | A qué **hora** se despierta el sistema cada día. |
| **2. Días y contenido** | `recordatorios.json` | **Qué días** se envía cada recordatorio y **qué dice**. |

Ejemplo: si el `cron` es a las 8:00 y un recordatorio tiene `"dias": ["lun","mie","vie"]`, ese mensaje llegará a las 8:00 solo lunes, miércoles y viernes.

## 4. Requisitos previos

- Una cuenta de **Telegram** (app en el celular o escritorio).
- Una cuenta de **GitHub** (gratuita) — [github.com](https://github.com).
- *(Opcional, solo para recordatorios con IA)* una llave de la **API de Claude** — [console.anthropic.com](https://console.anthropic.com).

No necesitas instalar nada en tu computadora para la versión en la nube. Todo corre en GitHub.

## 5. Contenido del paquete

```
recordatorios-telegram/
├── enviar_recordatorio.py     # El programa que arma y envía los mensajes.
├── obtener_chat_id.py         # Utilidad para descubrir tu chat_id.
├── recordatorios.json         # TUS recordatorios (edítalo). 
├── requirements.txt           # Dependencias.
├── .env.example               # Plantilla de credenciales (para uso local).
├── .gitignore                 # Evita subir el .env por accidente.
├── README.md                  # Esta guía.
└── .github/
    └── workflows/
        └── recordatorio.yml   # La tarea programada (aquí se cambia la HORA).
```

---

## 6. Procedimiento paso a paso

### Paso 1 — Crear tu bot de Telegram (5 minutos, sin código)

1. En Telegram, busca **@BotFather** (es el bot oficial de Telegram) y ábrele conversación.
2. Envía `/newbot`.
3. Escribe un **nombre** para tu bot (ej. *Recordatorios Elda*).
4. Escribe un **username** que termine en `bot` (ej. `recordatorios_elda_bot`).
5. BotFather te responde con un **token** parecido a `123456789:AAG...`. **Cópialo y guárdalo**; es secreto.

### Paso 2 — Obtener tu `chat_id`

El bot no puede escribirte primero: tú debes iniciar la conversación.

1. En Telegram, abre el chat con **tu bot** y envíale cualquier mensaje (por ejemplo `hola`).
2. Abre en tu navegador esta dirección, **reemplazando `TU_TOKEN`** por el token del paso 1:

   ```
   https://api.telegram.org/botTU_TOKEN/getUpdates
   ```

3. Verás un texto con `"chat":{"id":123456789,...}`. Ese número (`123456789`) es tu **chat_id**. Cópialo.

> Alternativa: si prefieres, ejecuta en tu computadora `python obtener_chat_id.py` (necesitas Python y el token en un `.env`). Hace lo mismo de forma más cómoda.

### Paso 3 — Subir el proyecto a tu GitHub

1. Entra a [github.com](https://github.com) → botón **New** para crear un repositorio nuevo (puede ser **privado**).
2. Sube esta carpeta completa. La forma más simple sin usar la terminal:
   - En el repositorio vacío, haz clic en **uploading an existing file**.
   - Arrastra todos los archivos **y también la carpeta `.github`**. (Si GitHub no deja arrastrar carpetas, crea el archivo manualmente: **Add file → Create new file**, escribe la ruta `.github/workflows/recordatorio.yml` y pega el contenido.)

> ⚠️ No subas nunca tu archivo `.env`. Este paquete ya lo excluye con `.gitignore`. En la nube, las credenciales van en *Secrets* (paso 4), no en archivos.

### Paso 4 — Guardar tus credenciales como *Secrets*

En tu repositorio de GitHub:

1. Ve a **Settings → Secrets and variables → Actions**.
2. Botón **New repository secret** y crea estos (nombre exacto, respetando mayúsculas):

   | Name | Secret (valor) |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | el token del Paso 1 |
   | `TELEGRAM_CHAT_ID` | el número del Paso 2 |
   | `ANTHROPIC_API_KEY` | *(solo si usarás IA; si no, omítelo)* |

### Paso 5 — Definir la HORA

Abre `.github/workflows/recordatorio.yml` en GitHub (**clic en el lápiz** para editar) y cambia la línea del `cron`.

El cron está en **UTC**. México (CDMX) es **UTC-6**, así que **suma 6 horas** a la hora local:

| Hora local (CDMX) | cron (UTC) |
|---|---|
| 07:00 | `"0 13 * * *"` |
| 08:00 | `"0 14 * * *"` |
| 12:00 | `"0 18 * * *"` |
| 18:00 | `"0 0 * * *"` |
| 20:30 | `"30 2 * * *"` |

Formato: `"minuto hora díaDelMes mes díaDeLaSemana"`. El `* * *` significa "todos los días". Guarda con **Commit changes**.

### Paso 6 — Definir los recordatorios

Abre `recordatorios.json` y edítalo. Cada bloque `{ ... }` es un recordatorio:

```json
{
  "id": "revisar-pipeline",
  "tipo": "fijo",
  "activo": true,
  "dias": ["lun", "mie", "vie"],
  "mensaje": "🔔 Recordatorio: revisar el pipeline de agentes."
}
```

Campos:

- **id**: nombre corto único (sin espacios).
- **tipo**: `"fijo"` (mensaje de texto) o `"ia"` (lo redacta Claude, ver más abajo).
- **activo**: `true` lo enciende, `false` lo apaga sin borrarlo.
- **dias**: `"diario"` o una lista como `["lun","mar","mie","jue","vie","sab","dom"]`.
- **mensaje**: el texto a enviar.

Para tener **varios recordatorios (modo lista)**, agrega más bloques separados por comas dentro de `"recordatorios": [ ... ]`.

### Paso 7 — Probarlo sin esperar a la hora

En GitHub, ve a la pestaña **Actions → recordatorio-telegram → Run workflow**. Esto lo ejecuta al instante. En segundos deberías recibir el mensaje en Telegram. Si no llega, revisa la sección *Errores frecuentes*.

---

## 7. Recordatorios con IA (opcional) — cómo son

Un recordatorio `"tipo": "ia"` **no** tiene un texto fijo: en cada ejecución, el programa le pide a la API de Claude que **redacte el mensaje** a partir de una instrucción (`prompt`) que tú escribes. Sirve para que el aviso no sea siempre idéntico.

Ejemplo del paquete:

```json
{
  "id": "arranque-motivador-ia",
  "tipo": "ia",
  "activo": false,
  "dias": ["lun"],
  "prompt": "Escribe un recordatorio breve (máx 3 líneas) para arrancar la semana con foco en el proyecto de agentes. Incluye una micro-acción concreta.",
  "modelo": "claude-haiku-4-5",
  "max_tokens": 300,
  "mensaje": "🚀 Nueva semana: define tu prioridad #1 y arranca por ahí."
}
```

Qué pasa al ejecutarse los lunes:
- El programa manda tu `prompt` a Claude y Claude devuelve, por ejemplo:
  > *"Arranca la semana con claridad: elige la tarea que más mueve tu proyecto de agentes y dedícale los primeros 45 minutos, sin distracciones. Hoy revisa el estado del pipeline. Tú marcas el ritmo."*
- Ese texto es el que llega a tu Telegram (distinto cada semana).

Notas importantes:
- Requiere `ANTHROPIC_API_KEY` en los Secrets. Si falta, ese recordatorio **se omite** (o usa el `mensaje` de respaldo si lo pusiste).
- **Tiene costo** (mínimo). Con **Claude Haiku 4.5** el precio es aproximadamente **$1 USD por millón de tokens de entrada y $5 por millón de salida** (referencia julio 2026; verifica el precio y el nombre del modelo vigente en la documentación oficial, enlaces al final). Un recordatorio corto consume pocos cientos de tokens, del orden de fracciones de centavo por envío.
- `mensaje` aquí es **respaldo**: se envía solo si la IA falla, para que nunca te quedes sin aviso.

---

## 8. Interpretación de la salida (registro de ejecución)

En **Actions**, al abrir una ejecución verás algo como:

```
Zona horaria: America/Mexico_City · Día de hoy: mie · ENVÍO REAL
  · [revisar-pipeline] enviado OK
Resumen: 1 enviado(s), 3 omitido(s).
```

- **enviado OK** = llegó a Telegram.
- **omitido** = ese recordatorio estaba apagado (`activo: false`) o no tocaba ese día.

## 9. Validación (checklist)

- [ ] `/newbot` completado y token guardado.
- [ ] `chat_id` obtenido y guardado.
- [ ] Los 2 (o 3) Secrets creados con el nombre exacto.
- [ ] `Run workflow` manual entregó el mensaje en Telegram.
- [ ] La línea `cron` refleja tu hora local (recuerda +6 para UTC).
- [ ] El `.env` **no** está en el repositorio.

## 10. Errores frecuentes y solución

| Síntoma | Causa probable | Solución |
|---|---|---|
| No llega ningún mensaje | Falta enviarle un mensaje al bot primero | Escríbele `hola` a tu bot y repite el Paso 2. |
| `ERROR: faltan TELEGRAM_BOT_TOKEN...` | Secret mal nombrado o ausente | Revisa que el nombre sea exacto en Settings → Secrets. |
| `chat not found` / `400` | `chat_id` incorrecto | Vuelve a obtenerlo con el Paso 2. |
| El de IA no llega | Falta `ANTHROPIC_API_KEY` o el nombre del modelo cambió | Agrega el Secret o pon `activo:false`; verifica el modelo vigente. |
| Llega a una hora distinta | Confusión UTC vs. local | Recalcula: hora_UTC = hora_CDMX + 6. |
| Se retrasa unos minutos | Normal en GitHub Actions | Los cron gratuitos no son exactos al segundo. |

## 11. Opciones de ejecución (comparativa)

| Opción | Costo | Máquina encendida | Dificultad | Ideal para |
|---|---|---|---|---|
| **GitHub Actions** (este paquete) | Gratis | No | Media | Operación real y compartir |
| APScheduler local (Python) | Gratis | Sí | Baja | Pruebas y demos |
| Servicio de nube (Render, etc.) | Gratis/pago | No | Media-alta | Bots que además responden 24/7 |

## 12. Recomendación final

- **Recomendación principal:** GitHub Actions. No requiere servidor ni tener la computadora prendida, es gratis para este uso y el horario se edita en un archivo de texto. Es también lo más fácil de **compartir**: cada colaborador hace un *fork* o copia del repo, pone sus propios Secrets y listo.
- **Alternativa sencilla (estudiantes):** ejecutar `python enviar_recordatorio.py --simular` en la computadora para ver los mensajes sin credenciales, y luego correrlo manualmente cuando se quiera.
- **Alternativa profesional:** desplegar el envío junto a un bot interactivo (que además reciba comandos) en Render o un VPS, con las llaves en variables de entorno del proveedor y control de costos si se usa IA.

## 13. Compartir con colaboradores

Dos formas:
1. **Repositorio plantilla:** en GitHub, marca tu repo como *Template repository* (Settings → General). Tus colaboradores harán clic en **Use this template**, obtendrán su propia copia y solo pondrán sus Secrets y sus recordatorios.
2. **Skill de Claude:** este paquete incluye una *skill* (`recordatorio-telegram.skill`) para colaboradores que usan Claude/Cowork. Al instalarla, pueden pedirle a Claude que los guíe para armar y personalizar su propio recordatorio. Ver el archivo `SKILL.md` incluido.

## 14. Fuentes

- Telegram Bot API — métodos `sendMessage` y `getUpdates` (documentación oficial): https://core.telegram.org/bots/api
- Claude — modelos y nombres vigentes (documentación oficial): https://platform.claude.com/docs/en/about-claude/models/overview
- Claude — precios de la API (documentación oficial): https://docs.anthropic.com/en/docs/about-claude/pricing
- GitHub Actions — sintaxis de `schedule`/`cron` (documentación oficial): https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule

*Consultado el 22 de julio de 2026. Los precios y nombres de modelo pueden cambiar; verifícalos en las fuentes oficiales antes de operar con IA.*
