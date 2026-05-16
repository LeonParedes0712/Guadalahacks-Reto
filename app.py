from flask import Flask, request, jsonify
from transcriber import transcribe_audio

app = Flask(__name__)

@app.route("/")
def home():
    return "Sentinel AI Running"

@app.route("/test")
def test():
    return "Ruta test funcionando"

@app.route("/transcribe", methods=["POST"])
def transcribe():

    audio = request.files["audio"]

    path = "uploads/audio.wav"

    audio.save(path)

    texto = transcribe_audio(path)

    return jsonify({
        "text": texto
    })

if __name__ == "__main__":
    app.run(debug=True)