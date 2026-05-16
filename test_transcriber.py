from transcriber import transcribe_audio

texto = transcribe_audio("uploads/prueba.wav.m4a")

print("Texto detectado:")
print(texto)