from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")

def transcribe_audio(audio_path):
    segments, info = model.transcribe(audio_path, language="es")

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text.strip()