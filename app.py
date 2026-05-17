from flask import Flask, render_template, request, jsonify
from transcriber import transcribe_audio
from intent_engine2 import classify
import os
from datetime import datetime

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ──────────────────────────────────────────────
# Almacenamiento en memoria
# ──────────────────────────────────────────────
db_history = []
db_notes   = []
db_tasks   = []

# ──────────────────────────────────────────────
# Respuestas por intent
# ──────────────────────────────────────────────
RESPONSES = {
    "emergency":    "🚨 Activando protocolo de emergencia. Contactando servicios del campus.",
    "music":        "🎵 Activando módulo de música. Buscando algo para ti.",
    "productivity": "📋 Entendido. Guardando tu tarea y activando modo enfoque.",
    "emotional":    "💙 Estoy aquí contigo. Respira profundo. No estás solo.",
    "system":       "⚙️ Ejecutando comando del sistema.",
    "time":         "🕐 Consultando información de tiempo.",
    "fun":          "😄 ¡Claro! Vamos a divertirnos un poco.",
    "notes":        "📝 Nota guardada correctamente en tu panel.",
    "general":      "👋 Hola, soy Sentinel AI. ¿En qué puedo ayudarte?",
}


def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")


# ──────────────────────────────────────────────
# Rutas
# ──────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"text": "No se envió ningún archivo de audio"}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"text": "El archivo de audio está vacío"}), 400

    path = os.path.join(UPLOAD_FOLDER, "audio.wav")
    audio_file.save(path)

    try:
        texto = transcribe_audio(path)
        if not texto or texto.strip() == "":
            texto = "No se detectó texto en el audio."
        return jsonify({"text": texto})
    except Exception as e:
        print("Error al transcribir:", e)
        return jsonify({"text": "Error al transcribir el audio"}), 500


@app.route("/intent", methods=["POST"])
def detect_intent():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibió JSON"}), 400

    transcript = data.get("text", "").strip()
    if not transcript:
        return jsonify({"error": "No se recibió texto"}), 400

    intent, confidence = classify(transcript)
    response = RESPONSES.get(intent, "Sentinel AI procesó tu solicitud.")

    # Acciones secundarias
    action = None
    if intent == "notes":
        db_notes.append({
            "text": transcript,
            "timestamp": get_timestamp()
        })
        action = "note_saved"
    elif intent == "productivity":
        db_tasks.append({
            "text": transcript,
            "done": False,
            "timestamp": get_timestamp()
        })
        action = "task_saved"
    elif intent == "time":
        now = datetime.now()
        response = f"🕐 Son las {now.strftime('%H:%M')} del {now.strftime('%A %d de %B de %Y')}."

    registro = {
        "timestamp": get_timestamp(),
        "intent":     intent,
        "text":       transcript,
        "confidence": confidence,
        "response":   response,
        "action":     action,
    }
    db_history.append(registro)

    return jsonify({
        "intent":     intent,
        "confidence": confidence,
        "response":   response,
        "action":     action,
    })


@app.route("/history", methods=["GET"])
def get_history():
    return jsonify({"history": list(reversed(db_history))})


@app.route("/notes", methods=["GET"])
def get_notes():
    return jsonify({"notes": list(reversed(db_notes))})


@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify({"tasks": list(reversed(db_tasks))})


@app.route("/tasks/<int:index>/done", methods=["POST"])
def mark_task_done(index):
    real_index = len(db_tasks) - 1 - index
    if 0 <= real_index < len(db_tasks):
        db_tasks[real_index]["done"] = True
        return jsonify({"ok": True})
    return jsonify({"error": "Tarea no encontrada"}), 404


@app.route("/test")
def test():
    return "Ruta test funcionando"


if __name__ == "__main__":
    app.run(debug=True)