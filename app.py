<<<<<<< Updated upstream
from flask import Flask
from faster_whisper import WhisperModel

app = Flask(__name__)

model = WhisperModel("tiny", device="cpu", compute_type="int8")

@app.route("/")
def home():
    return "Sentinel AI Running"

@app.route("/test")
def test():

    segments, info = model.transcribe("audio_capture.wav", language="es")

    texto = ""

    for segment in segments:
        texto += segment.text

    return texto

if __name__ == "__main__":
    app.run(debug=True)
=======
from flask import Flask, request, jsonify
from transcriber import transcribe_audio

app = Flask(__name__)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio = request.files["audio"]
    path = "uploads/audio.wav"
    audio.save(path)

    texto = transcribe_audio(path)

    return jsonify({
        "text": texto
    })
>>>>>>> Stashed changes
