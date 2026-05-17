from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
 
# ──────────────────────────────────────────────
# Datos de entrenamiento
# ──────────────────────────────────────────────
frases = [
    # EMERGENCY
    "ayuda urgente", "necesito ayuda", "auxilio", "socorro",
    "estoy en peligro", "tengo miedo", "llama a alguien", "save me",
    "emergencia", "ambulancia", "accidente", "me lastimé",
 
    # MUSIC
    "pon musica", "reproduce musica", "pon una cancion", "musica relajante",
    "musica triste", "pon rock", "pon reggaeton", "quiero escuchar algo",
 
    # PRODUCTIVITY
    "tengo tarea", "tengo examen", "recuérdame algo", "haz una lista",
    "anota esto", "quiero enfocarme", "ayudame a estudiar", "pon una alarma",
    "necesito organizarme", "tengo pendientes",
 
    # EMOTIONAL
    "estoy triste", "me siento solo", "quiero llorar", "tengo ansiedad",
    "me siento mal", "estoy estresado", "me siento agotado",
    "necesito apoyo", "me siento perdido",
 
    # SYSTEM
    "abre calculadora", "abre spotify", "abre navegador", "cierra ventana",
    "sube volumen", "baja volumen", "silencia la computadora", "reinicia",
 
    # TIME
    "que hora es", "que dia es hoy", "pon temporizador",
    "cronometro de 5 minutos", "cuanto tiempo falta",
 
    # FUN
    "cuentame un chiste", "di algo divertido", "hazme reir",
    "cuenta una historia", "juguemos algo",
 
    # NOTES
    "crear nota", "guarda esto", "escribe esto",
    "guardar recordatorio", "anota una idea", "quiero guardar esto",
 
    # GENERAL
    "hola", "como estas", "que puedes hacer", "quien eres",
    "ayudame", "buenos dias", "buenas noches",
]
 
labels = [
    # EMERGENCY (12)
    "emergency","emergency","emergency","emergency",
    "emergency","emergency","emergency","emergency",
    "emergency","emergency","emergency","emergency",
 
    # MUSIC (8)
    "music","music","music","music",
    "music","music","music","music",
 
    # PRODUCTIVITY (10)
    "productivity","productivity","productivity","productivity",
    "productivity","productivity","productivity","productivity",
    "productivity","productivity",
 
    # EMOTIONAL (9)
    "emotional","emotional","emotional","emotional",
    "emotional","emotional","emotional","emotional","emotional",
 
    # SYSTEM (8)
    "system","system","system","system",
    "system","system","system","system",
 
    # TIME (5)
    "time","time","time","time","time",
 
    # FUN (5)
    "fun","fun","fun","fun","fun",
 
    # NOTES (6)
    "notes","notes","notes","notes","notes","notes",
 
    # GENERAL (7)
    "general","general","general","general",
    "general","general","general",
]
 
# ──────────────────────────────────────────────
# Entrenamiento
# ──────────────────────────────────────────────
_vectorizer = CountVectorizer()
_X = _vectorizer.fit_transform(frases)
 
_model = MultinomialNB()
_model.fit(_X, labels)
 
 
# ──────────────────────────────────────────────
# Función pública
# ──────────────────────────────────────────────
def classify(text: str) -> tuple[str, float]:
    """
    Recibe un texto en español y devuelve (intent, confidence).
    intent es uno de: emergency, music, productivity, emotional,
                      system, time, fun, notes, general
    """
    vector = _vectorizer.transform([text.lower()])
    intent = _model.predict(vector)[0]
    probs  = _model.predict_proba(vector)[0]
    confidence = float(max(probs))
    return intent, round(confidence, 4)