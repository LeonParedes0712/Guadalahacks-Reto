from flask import Flask
from faster_whisper import WhisperModel

app = Flask(__name__)

model = WhisperModel("tiny", device="cpu", compute_type="int8")

@app.route("/")
def home():
    return "Sentinel AI Running"

@app.route("/test")
def test():

    segments, info = model.transcribe("audio.wav.mp3", language="es")

    texto = ""

    for segment in segments:
        texto += segment.text

    return texto

if __name__ == "__main__":
    app.run(debug=True)