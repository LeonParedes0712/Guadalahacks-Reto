from faster_whisper import WhisperModel

model = WhisperModel("tiny", device="cpu", compute_type="int8")

segments, info = model.transcribe("audio.wav.mp3")

print("Idioma detectado:", info.language)

for segment in segments:
    print(segment.text)