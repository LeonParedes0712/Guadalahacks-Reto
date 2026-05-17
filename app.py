from flask import Flask, render_template, request, jsonify
from transcriber import transcribe_audio
import os

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Carpeta para guardar audios subidos
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Base de datos temporal en memoria para simular el historial
db_history = []


@app.route("/")
def home():
    return render_template("index.html")


# Ruta para recibir archivo de audio y transcribirlo
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"text": "No se envió ningún archivo de audio"}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"text": "El archivo de audio está vacío"}), 400

    path = os.path.join(UPLOAD_FOLDER, "audio.wav")
    audio_file.save(path)

    print(f"Audio recibido y guardado en: {path}")

    try:
        texto = transcribe_audio(path)

        if not texto or texto.strip() == "":
            texto = "No se detectó texto en el audio."

        return jsonify({"text": texto})

    except Exception as e:
        print("Error al transcribir:", e)
        return jsonify({"text": "Error al transcribir el audio"}), 500


# Ruta para procesar el texto y decidir la intención
@app.route("/intent", methods=["POST"])
def detect_intent():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se recibió JSON"}), 400

    transcript = data.get("text", "")

    if transcript == "":
        return jsonify({"error": "No se recibió texto"}), 400

    texto_lower = transcript.lower()

    palabras_emergencia = [
        "emergencia",
        "ayuda",
        "auxilio",
        "médica",
        "medica",
        "ambulancia",
        "peligro",
        "accidente",
        "me siento mal",
        "urgente"
    ]

    if any(palabra in texto_lower for palabra in palabras_emergencia):
        intent_detectado = "EMERGENCY"
        confianza = 0.98
        respuesta_sistema = "Llamando a los servicios de emergencia del campus..."
    else:
        intent_detectado = "NORMAL"
        confianza = 0.85
        respuesta_sistema = "Hola, soy Sentinel AI. Estoy listo para ayudarte."

    registro = {
        "intent": intent_detectado,
        "text": transcript,
        "confidence": confianza,
        "response": respuesta_sistema
    }

    db_history.append(registro)

    return jsonify({
        "intent": intent_detectado,
        "confidence": confianza,
        "response": respuesta_sistema
    })


# Ruta para cargar historial
@app.route("/history", methods=["GET"])
def get_history():
    return jsonify({"history": list(reversed(db_history))})


# Ruta simple para comprobar que Flask vive
@app.route("/test")
def test():
    return "Ruta test funcionando"


if __name__ == "__main__":
    app.run(debug=True)