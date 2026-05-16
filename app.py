from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Base de datos temporal en memoria para simular el historial
db_history = []

@app.route("/")
def home():
    return render_template("index.html")

# 1. Ruta para recibir el archivo de audio (.wav)
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({"text": "No se envió ningún archivo de audio"}), 400
        
    audio_file = request.files['audio']
    print(f"Audio recibido: {audio_file.filename}") # Verás esto en tu terminal
    
    # NOTA: Aquí tu equipo integrará el modelo de IA Whisper o similar.
    # Por ahora, simularemos que la IA escuchó una orden.
    texto_simulado = "Necesito ayuda médica de emergencia inmediatamente"
    
    return jsonify({"text": texto_simulado})

# 2. Ruta para procesar el texto y decidir la intención (Intent)
@app.route("/intent", methods=["POST"])
def detect_intent():
    data = request.get_json()
    transcript = data.get("text", "")
    
    # Lógica de simulación para activar la alerta si detecta la palabra emergencia
    if "emergencia" in transcript.lower() or "ayuda" in transcript.lower():
        intent_detectado = "EMERGENCY"
        confianza = 0.98  # <--- Esta es la variable
        respuesta_sistema = "Llamando a los servicios de emergencia del campus..."
    else:
        intent_detectado = "SALUDO"
        confianza = 0.85  # <--- Esta es la variable
        respuesta_sistema = "Hola, soy Sentinel AI. Estoy listo para ayudarte."

    # Guardamos en nuestra lista local para simular la base de datos
    registro = {"intent": intent_detectado, "text": transcript}
    db_history.append(registro)

    return jsonify({
        "intent": intent_detectado,
        "confidence": confianza,  # <--- AQUÍ DEBE DECIR confianza (en español)
        "response": respuesta_sistema
    })

# 3. Ruta para cargar el historial de comandos en pantalla
@app.route("/history", methods=["GET"])
def get_history():
    # Devolvemos los registros guardados ordenados (los más recientes primero)
    return jsonify({"history": list(reversed(db_history))})

if __name__ == "__main__":
    app.run(debug=True)
