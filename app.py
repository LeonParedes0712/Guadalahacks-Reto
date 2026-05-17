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
    GET  /class/state            → estado del modo clase
    GET  /class/summary          → resumen de la clase activa
    GET  /modes/state            → estado de modos nivel 2
"""

import os
import tempfile
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from transcriber import transcribe_audio
from intent_engine2 import classify
from actions import execute_action
import class_mode as cm
import assistant_modes as modes


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
    if intent == "class_mode":
        return "Modo clase procesado."
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

    # 2) Variables extra para modos avanzados
    class_mode_active = False
    class_notes = []
    class_summary = None
    class_file_path = None
    detected_class_tasks = []

    focus_mode_active = False
    focus_timer = None
    presentation_mode_active = False
    presentation_checklist = []
    media_status = None
    saved_file_path = None
    active_modes = []

    # 3) Intentar ejecutar acción real
    action_result = execute_action(intent, text)

    if action_result is not None:
        response = action_result.get("response", "")
        action_executed = action_result.get("action_executed", False)

        # Campos extra opcionales de actions.py / módulos nivel 2
        class_mode_active = action_result.get("class_mode_active", cm.get_class_state()["active"])
        class_notes = action_result.get("class_notes", [])
        class_summary = action_result.get("class_summary", None)
        class_file_path = action_result.get("class_file_path", None)
        detected_class_tasks = action_result.get("detected_class_tasks", [])

        focus_mode_active = action_result.get("focus_mode_active", False)
        focus_timer = action_result.get("focus_timer", None)
        presentation_mode_active = action_result.get("presentation_mode_active", False)
        presentation_checklist = action_result.get("presentation_checklist", [])
        media_status = action_result.get("media_status", None)
        saved_file_path = action_result.get("saved_file_path", None)
        active_modes = action_result.get("active_modes", [])

    else:
        # 4) Fallback a lógica del propio app.py
        response = _fallback_response(intent, text)
        action_executed = False

        # Guardar nota si aplica
        if intent == "notes":
            NOTES.append({"timestamp": _now_ts(), "text": text})

        # Guardar tarea si aplica
        if intent == "productivity":
            TASKS.append({"timestamp": _now_ts(), "text": text, "done": False})

        class_mode_active = cm.get_class_state()["active"]

    # 5) Si modo clase está activo, agregar transcripción a apuntes.
    # OJO: no guardamos comandos de control como "activa modo clase" o "resume la clase"
    # para que los apuntes no se ensucien con instrucciones del asistente.
    if cm.get_class_state()["active"] and intent != "class_mode":
        result = cm.add_class_transcript(text)
        class_mode_active = True

        # Agregar tarea detectada en clase a TASKS
        if result.get("detected_task"):
            task = result["detected_task"]
            task["done"] = False
            TASKS.append(task)
            detected_class_tasks.append(task)

        # Agregar nota detectada en clase a NOTES
        if result.get("detected_note"):
            NOTES.append(result["detected_note"])
            class_notes.append(result["detected_note"])

    # 6) Historial enriquecido
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
        # Campos de modo clase
        "class_mode_active": class_mode_active,
        "class_notes": class_notes,
        "class_summary": class_summary,
        "class_file_path": class_file_path,
        "detected_class_tasks": detected_class_tasks,
        "class_state": cm.get_class_state(),
        # Campos de modos nivel 2
        "focus_mode_active": focus_mode_active or modes.get_focus_state()["active"],
        "focus_timer": focus_timer or modes.get_focus_state(),
        "presentation_mode_active": presentation_mode_active or modes.get_presentation_state()["active"],
        "presentation_checklist": presentation_checklist or modes.get_presentation_checklist(),
        "media_status": media_status,
        "saved_file_path": saved_file_path,
        "active_modes": active_modes or modes.get_active_modes(),
        "modes_state": modes.get_modes_state(),
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
# /class/state  — estado actual del modo clase
# ──────────────────────────────────────────────
@app.route("/class/state", methods=["GET"])
def class_state_route():
    return jsonify(cm.get_class_state())


# ──────────────────────────────────────────────
# /class/summary — resumen de la clase activa
# ──────────────────────────────────────────────
@app.route("/class/summary", methods=["GET"])
def class_summary_route():
    summary = cm.get_class_summary()
    return jsonify({"summary": summary})


# ──────────────────────────────────────────────
# /modes/state — estado actual de modos nivel 2
# ──────────────────────────────────────────────
@app.route("/modes/state", methods=["GET"])
def modes_state_route():
    return jsonify(modes.get_modes_state())


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)