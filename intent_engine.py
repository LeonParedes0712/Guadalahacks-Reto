from sklearn.feature_extraction.text import CountVectorizer

def detectar_ayuda(texto):
    texto = texto.lower()

    palabras_ayuda = [
        "ayuda",
        "auxilio",
        "socorro",
        "emergencia",
        "ayudame",
        "necesito ayuda",
        "me ayudas",
        "help",
        "save me",
        "sos",
        "apoyo",
        "urgente",
        "estoy en peligro",
        "llama a alguien",
        "necesito apoyo",
        "ayuda por favor",
        "por favor ayuda",
        "me siento mal",
        "estoy asustado",
        "tengo miedo"
    ]

    for palabra in palabras_ayuda:
        if palabra in texto:
            return True

    return False


def detectar_emocional(texto):
    texto = texto.lower()

    palabras = [
        "estoy triste",
        "me siento solo",
        "quiero llorar",
        "me siento mal",
        "tengo ansiedad",
        "estoy deprimido",
        "no puedo mas",
        "me siento vacío",
        "me siento horrible",
        "estoy cansado de todo",
        "nadie me entiende",
        "me siento perdido",
        "tengo miedo",
        "estoy estresado",
        "me siento agotado"
    ]

    for palabra in palabras:
        if palabra in texto:
            return True

    return False


def detectar_musica(texto):
    texto = texto.lower()

    palabras = [
        "pon musica",
        "quiero escuchar musica",
        "reproduce musica",
        "pon una cancion",
        "musica relajante",
        "musica triste",
        "musica feliz",
        "spotify",
        "play music",
        "quiero una playlist",
        "pon reggaeton",
        "pon rock",
        "pon algo tranquilo",
        "quiero escuchar algo"
    ]

    for palabra in palabras:
        if palabra in texto:
            return True

    return False


def detectar_productividad(texto):
    texto = texto.lower()

    palabras = [
        "recuérdame",
        "tengo tarea",
        "tengo examen",
        "organiza mi dia",
        "haz una lista",
        "agenda",
        "calendario",
        "quiero ser productivo",
        "ayudame a estudiar",
        "necesito concentrarme",
        "pomodoro",
        "crear nota",
        "anota esto",
        "recordatorio",
        "programa esto",
        "gestion de tiempo",
        "quiero enfocarme"
    ]

    for palabra in palabras:
        if palabra in texto:
            return True

    return False


def audiovector(text):

    if detectar_ayuda(text):
        return {
            "intent": "emergency",
            "confidence": 0.9,
            "response": "Detecté una posible emergencia.",
            "action": "emergency_mode"
        }

    elif detectar_emocional(text):
        return {
            "intent": "emotional",
            "confidence": 0.8,
            "response": "Parece que necesitas apoyo emocional.",
            "action": "emotional_support"
        }

    elif detectar_productividad(text):
        return {
            "intent": "productivity",
            "confidence": 0.8,
            "response": "Te ayudaré a organizar eso.",
            "action": "productivity_mode"
        }

    elif detectar_musica(text):
        return {
            "intent": "music",
            "confidence": 0.8,
            "response": "Claro, reproduciendo música.",
            "action": "open_music"
        }

    return {
        "intent": "general",
        "confidence": 0.5,
        "response": "No detecté una intención específica.",
        "action": "none"
    }


resultado = audiovector("ayuda por favor tengo miedo")

print(resultado)