import sounddevice as sd
import soundfile as sf

DURATION = 5
SAMPLE_RATE = 16000
OUTPUT_FILE = "audio_capture.wav"

print("Grabando... habla ahora")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32"
)

sd.wait()

sf.write(OUTPUT_FILE, audio, SAMPLE_RATE)

print(f"Audio guardado como {OUTPUT_FILE}")