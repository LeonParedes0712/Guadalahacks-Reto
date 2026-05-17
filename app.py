"""
app.py
──────────────────────────────────────────────
Sentinel AI — backend Flask local-first.

Endpoints:
    GET  /                       → sirve templates/index.html
    POST /transcribe             → recibe audio, devuelve texto
    POST /intent                 → clasifica intención y ejecuta acción
    GET  /history                → historial de interacciones
    GET  /notes                  → lista de notas guardadas
    GET  /tasks                  → lista de tareas
    POST /tasks/<index>/done     → marcar tarea como hecha
"""

import os
import tempfile
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from transcriber import transcribe_audio
from intent_engine2 import classify
from actions import execute_action


# ──────────────────────────────────────────────
# Configuración Flask
# ──────────────────────────────────────────────
app = Flask(__name__)
CORS(app)


# ──────────────────────────────────────────────
# Estado en memoria (suficiente para hackathon)
# ──────────────────────────────────────────────
HISTORY: list[dict] = []   # {timestamp, intent, text, response, action_executed}
NOTES:   list[dict] = []   # {timestamp, text}
TASKS:   list[dict] = []   # {timestamp, text, done}


def _now_ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ──────────────────────────────────────────────
# Respuestas fallback por intent (cuando actions.py devuelve None)
# ──────────────────────────────────────────────
def _fallback_response(intent: str, text: str) -> str:
    if intent == "notes":
        return "Nota guardada."
    if intent == "productivity":
        return "Tarea agregada a tus pendientes."
    if intent == "general":
        return "Hola, soy Sentinel. ¿En qué te puedo ayudar?"
    return "Entendido."


# ──────────────────────────────────────────────
# Página principal
# ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ──────────────────────────────────────────────
# /transcribe
# ──────────────────────────────────────────────
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"text": "", "error": "no audio file"}), 400

    audio_file = request.files["audio"]

    # Guardar a archivo temporal porque faster-whisper espera ruta
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    try:
        audio_file.save(tmp.name)
        tmp.close()
        text = transcribe_audio(tmp.name)
    except Exception as e:
        return jsonify({"text": "", "error": str(e)}), 500
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return jsonify({"text": text})


# ──────────────────────────────────────────────
# /intent — clasifica y ejecuta acción real si aplica
# ──────────────────────────────────────────────
@app.route("/intent", methods=["POST"])
def intent_route():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({
            "intent": "general",
            "confidence": 0.0,
            "response": "No detecté texto.",
            "action_executed": False,
        })

    # 1) Clasificar
    intent, confidence = classify(text)

    # 2) Intentar ejecutar acción real
    action_result = execute_action(intent, text)

    if action_result is not None:
        response = action_result.get("response", "")
        action_executed = action_result.get("action_executed", False)
    else:
        # 3) Fallback a lógica del propio app.py
        response = _fallback_response(intent, text)
        action_executed = False

        # Guardar nota si aplica
        if intent == "notes":
            NOTES.append({"timestamp": _now_ts(), "text": text})

        # Guardar tarea si aplica
        if intent == "productivity":
            TASKS.append({"timestamp": _now_ts(), "text": text, "done": False})

    # 4) Historial enriquecido
    HISTORY.append({
        "timestamp": _now_ts(),
        "intent": intent,
        "text": text,
        "response": response,
        "action_executed": action_executed,
    })

    return jsonify({
        "intent": intent,
        "confidence": confidence,
        "response": response,
        "action_executed": action_executed,
    })


# ──────────────────────────────────────────────
# /history
# ──────────────────────────────────────────────
@app.route("/history", methods=["GET"])
def history_route():
    # Más recientes primero, máx 50
    return jsonify({"history": list(reversed(HISTORY[-50:]))})


# ──────────────────────────────────────────────
# /notes
# ──────────────────────────────────────────────
@app.route("/notes", methods=["GET"])
def notes_route():
    return jsonify({"notes": list(reversed(NOTES))})


# ──────────────────────────────────────────────
# /tasks
# ──────────────────────────────────────────────
@app.route("/tasks", methods=["GET"])
def tasks_route():
    return jsonify({"tasks": TASKS})


@app.route("/tasks/<int:index>/done", methods=["POST"])
def tasks_done_route(index: int):
    if 0 <= index < len(TASKS):
        TASKS[index]["done"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "index out of range"}), 404


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)