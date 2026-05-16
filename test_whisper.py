from faster_whisper import WhisperModel

print("Cargando modelo tiny...")
model = WhisperModel("tiny", device="cpu", compute_type="int8")
print("Modelo tiny cargado correctamente")