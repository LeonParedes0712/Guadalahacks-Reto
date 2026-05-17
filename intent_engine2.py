import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline

# ──────────────────────────────────────────────
# Palabras críticas de emergencia
# OJO: NO poner "ayuda" sola, porque frases como
# "necesito ayuda con mi tarea" no son emergencia.
# ──────────────────────────────────────────────
_EMERGENCY_KEYWORDS = {
    "auxilio",
    "socorro",
    "emergencia",
    "peligro",
    "ambulancia",
    "accidente",
    "lastime",
    "lastimo",
    "herido",
    "herida",
    "sangre",
    "no puedo respirar",
    "no respiro",
    "me cai",
    "me golpee",
    "desmaye",
    "desmayo",
    "inconsciente",
    "muerto",
    "muerta",
    "ataque",
    "robo",
    "asalto",
    "violencia",
    "agresion",
    "quemadura",
    "intoxicado",
    "intoxicada",
    "veneno",
    "overdose",
    "me estan atacando",
    "llamen a emergencias",
    "llama a emergencias",
    "llama a una ambulancia",
    "necesito ayuda urgente",
    "ayuda urgente",
    "alguien ayuda",
    "me duele el pecho",
    "me voy a desmayar",
    "hay alguien herido",
    "hay un incendio",
}

CONFIDENCE_THRESHOLD = 0.30


# ──────────────────────────────────────────────
# Limpieza de texto
# ──────────────────────────────────────────────
def _normalize(text: str) -> str:
    text = text.lower().strip()

    # Quitar wake word si aparece al inicio
    text = re.sub(r"^sentinel[,\s]*", "", text)

    # Quitar acentos
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # Quitar signos comunes
    text = re.sub(r"[¿?¡!.,;:()\"'\-]", " ", text)

    # Normalizar espacios
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _has_emergency_keyword(text: str) -> bool:
    """
    Revisa palabras/frases críticas ya normalizadas.
    Esto permite que 'me caí' y 'me cai' funcionen igual.
    """
    t = _normalize(text)

    for kw in _EMERGENCY_KEYWORDS:
        if _normalize(kw) in t:
            return True

    return False

def _rule_based_intent(text: str):
    """
    Reglas directas para comandos muy claros.
    Esto mejora frases largas o naturales que el modelo puede clasificar con baja confianza.
    """
    t = _normalize(text)

    # NOTAS: comandos explícitos de guardar información
    note_starters = [
        "anota",
        "apunta",
        "guarda esto",
        "guarda que",
        "escribe esto",
        "registra",
        "crea una nota",
        "crear una nota",
        "haz una nota",
        "quiero anotar",
        "necesito anotar",
        "no quiero olvidar",
    ]

    for starter in note_starters:
        if t.startswith(starter):
            return "notes", 0.95

    # PRODUCTIVIDAD: recordatorios, tareas, pendientes, estudio
    productivity_starters = [
        "recuerdame",
        "recordarme",
        "ponme un recordatorio",
        "crea un recordatorio",
        "agrega una tarea",
        "agrega esto a mis tareas",
        "tengo tarea",
        "tengo examen",
        "necesito estudiar",
        "quiero estudiar",
        "ayudame a estudiar",
        "necesito enfocarme",
        "quiero enfocarme",
    ]

    for starter in productivity_starters:
        if t.startswith(starter):
            return "productivity", 0.95

    # MÚSICA
    music_starters = [
        "pon musica",
        "reproduce musica",
        "pon una cancion",
        "pon algo",
        "quiero escuchar musica",
        "musica relajante",
    ]

    for starter in music_starters:
        if t.startswith(starter):
            return "music", 0.95

    # FUN
    fun_starters = [
        "cuentame un chiste",
        "dime un chiste",
        "hazme reir",
        "di algo divertido",
        "cuentame algo gracioso",
        "dime una adivinanza",
    ]

    for starter in fun_starters:
        if t.startswith(starter):
            return "fun", 0.95

    return None


# ──────────────────────────────────────────────
# Datos de entrenamiento
# ──────────────────────────────────────────────
_TRAINING = [
    # EMERGENCY
    ("ayuda urgente", "emergency"),
    ("necesito ayuda urgente", "emergency"),
    ("auxilio por favor", "emergency"),
    ("socorro alguien", "emergency"),
    ("estoy en peligro", "emergency"),
    ("tengo miedo llama a alguien", "emergency"),
    ("llama a emergencias", "emergency"),
    ("emergencia medica", "emergency"),
    ("llama a una ambulancia", "emergency"),
    ("hubo un accidente", "emergency"),
    ("me lastimé", "emergency"),
    ("me caí y me duele mucho", "emergency"),
    ("estoy sangrando", "emergency"),
    ("no puedo respirar", "emergency"),
    ("me están atacando", "emergency"),
    ("alguien me está persiguiendo", "emergency"),
    ("hay un incendio", "emergency"),
    ("me golpearon", "emergency"),
    ("me robaron", "emergency"),
    ("perdí el conocimiento", "emergency"),
    ("me siento muy mal y necesito ayuda urgente", "emergency"),
    ("hay alguien herido aquí", "emergency"),
    ("necesito una ambulancia ahora", "emergency"),
    ("estoy solo y tengo miedo", "emergency"),
    ("esto es una emergencia", "emergency"),
    ("sentinel ayuda urgente", "emergency"),
    ("sentinel llama a emergencias", "emergency"),
    ("sentinel hay un accidente", "emergency"),
    ("sentinel estoy en peligro", "emergency"),
    ("sentinel necesito ayuda ahora mismo", "emergency"),
    ("me duele el pecho", "emergency"),
    ("creo que me voy a desmayar", "emergency"),
    ("me mordió un animal", "emergency"),
    ("hay alguien inconsciente", "emergency"),
    ("me intoxiqué", "emergency"),

    # MUSIC
    ("pon musica", "music"),
    ("reproduce musica", "music"),
    ("pon una cancion", "music"),
    ("quiero escuchar musica", "music"),
    ("musica relajante por favor", "music"),
    ("pon algo de musica triste", "music"),
    ("pon rock", "music"),
    ("pon reggaeton", "music"),
    ("pon jazz", "music"),
    ("pon musica clasica", "music"),
    ("reproduce algo tranquilo", "music"),
    ("quiero escuchar algo", "music"),
    ("pon mi playlist", "music"),
    ("reproduce la siguiente cancion", "music"),
    ("salta esta cancion", "music"),
    ("pausa la musica", "music"),
    ("sube el volumen de la musica", "music"),
    ("pon algo para estudiar", "music"),
    ("musica para dormir", "music"),
    ("pon algo animado", "music"),
    ("quiero escuchar bachata", "music"),
    ("reproduce trap", "music"),
    ("pon lo que sea", "music"),
    ("necesito musica ahora", "music"),
    ("sentinel pon musica", "music"),
    ("sentinel reproduce algo relajante", "music"),
    ("sentinel pon reggaeton", "music"),
    ("sentinel musica para estudiar", "music"),
    ("activa el modo musica", "music"),
    ("quiero canciones en ingles", "music"),
    ("pon algo de los 80", "music"),
    ("reproduce una lista de reproduccion", "music"),

    # PRODUCTIVITY
    ("tengo tarea pendiente", "productivity"),
    ("tengo examen manana", "productivity"),
    ("recuerdame entregar el proyecto", "productivity"),
    ("haz una lista de pendientes", "productivity"),
    ("quiero enfocarme en estudiar", "productivity"),
    ("ayudame a estudiar", "productivity"),
    ("necesito ayuda con mi tarea", "productivity"),
    ("ayudame con mi tarea", "productivity"),
    ("pon una alarma a las ocho", "productivity"),
    ("necesito organizarme", "productivity"),
    ("tengo muchos pendientes", "productivity"),
    ("quiero ser mas productivo", "productivity"),
    ("ayudame a planear mi dia", "productivity"),
    ("tengo que terminar esto hoy", "productivity"),
    ("agenda una tarea para manana", "productivity"),
    ("necesito hacer una lista", "productivity"),
    ("quiero hacer mis tareas", "productivity"),
    ("organiza mis prioridades", "productivity"),
    ("tengo reunion en una hora", "productivity"),
    ("necesito concentrarme", "productivity"),
    ("modo estudio activado", "productivity"),
    ("tengo deadline hoy", "productivity"),
    ("quiero terminar mi proyecto", "productivity"),
    ("ayudame a no distraerme", "productivity"),
    ("bloquea las notificaciones", "productivity"),
    ("necesito hacer un repaso", "productivity"),
    ("sentinel tengo tarea", "productivity"),
    ("sentinel pon una alarma", "productivity"),
    ("sentinel necesito enfocarme", "productivity"),
    ("sentinel agenda esto", "productivity"),
    ("sentinel tengo examen", "productivity"),
    ("sentinel necesito ayuda con mi tarea", "productivity"),
    ("guarda esta tarea", "productivity"),
    ("agrega esto a mis pendientes", "productivity"),
    ("quiero repasar para el examen", "productivity"),

    # EMOTIONAL
    ("estoy triste", "emotional"),
    ("me siento muy solo", "emotional"),
    ("quiero llorar", "emotional"),
    ("tengo mucha ansiedad", "emotional"),
    ("me siento muy mal emocionalmente", "emotional"),
    ("estoy muy estresado", "emotional"),
    ("me siento agotado", "emotional"),
    ("necesito apoyo emocional", "emotional"),
    ("me siento perdido en la vida", "emotional"),
    ("no se que hacer con mi vida", "emotional"),
    ("siento que nada sale bien", "emotional"),
    ("me siento incomprendido", "emotional"),
    ("no tengo animos de nada", "emotional"),
    ("todo me sale mal", "emotional"),
    ("me siento vacio", "emotional"),
    ("necesito que alguien me escuche", "emotional"),
    ("estoy pasando un momento muy dificil", "emotional"),
    ("siento mucha presion", "emotional"),
    ("no puedo mas", "emotional"),
    ("me siento abrumado", "emotional"),
    ("tengo miedo de fallar", "emotional"),
    ("me siento inseguro", "emotional"),
    ("sentinel estoy triste", "emotional"),
    ("sentinel necesito apoyo emocional", "emotional"),
    ("sentinel me siento solo", "emotional"),
    ("necesito hablar con alguien", "emotional"),
    ("me siento deprimido", "emotional"),
    ("no tengo motivacion", "emotional"),
    ("siento que no valgo nada", "emotional"),
    ("estoy muy ansioso hoy", "emotional"),

    # SYSTEM
    ("abre la calculadora", "system"),
    ("abre spotify", "system"),
    ("abre el navegador", "system"),
    ("cierra esta ventana", "system"),
    ("sube el volumen", "system"),
    ("baja el volumen", "system"),
    ("silencia la computadora", "system"),
    ("reinicia el sistema", "system"),
    ("apaga la pantalla", "system"),
    ("abre el correo", "system"),
    ("toma una captura de pantalla", "system"),
    ("abre el explorador de archivos", "system"),
    ("cierra todas las aplicaciones", "system"),
    ("conecta el bluetooth", "system"),
    ("activa el wifi", "system"),
    ("abre el gestor de tareas", "system"),
    ("pon el brillo al maximo", "system"),
    ("sentinel abre el navegador", "system"),
    ("sentinel sube el volumen", "system"),
    ("sentinel silencia todo", "system"),
    ("cambia de ventana", "system"),
    ("minimiza la ventana", "system"),
    ("abre una nueva pestana", "system"),
    ("cierra la aplicacion", "system"),

    # TIME
    ("que hora es", "time"),
    ("que dia es hoy", "time"),
    ("pon un temporizador de diez minutos", "time"),
    ("ponme un cronometro de cinco minutos", "time"),
    ("cuanto tiempo falta", "time"),
    ("en cuanto tiempo es mi clase", "time"),
    ("que dia de la semana es", "time"),
    ("pon un timer", "time"),
    ("cuanto tiempo llevo estudiando", "time"),
    ("ponme una alarma en treinta minutos", "time"),
    ("dime la fecha de hoy", "time"),
    ("que hora es en mexico", "time"),
    ("sentinel que hora es", "time"),
    ("sentinel pon un temporizador", "time"),
    ("cuantos dias faltan para el fin de semana", "time"),
    ("pon una alarma para manana a las siete", "time"),
    ("deten el cronometro", "time"),
    ("cuanto es una hora en minutos", "time"),

    # FUN
    ("cuentame un chiste", "fun"),
    ("dime un chiste", "fun"),
    ("di algo divertido", "fun"),
    ("hazme reir", "fun"),
    ("cuenta una historia graciosa", "fun"),
    ("juguemos algo", "fun"),
    ("dime algo curioso", "fun"),
    ("sabes alguna adivinanza", "fun"),
    ("dime un dato curioso", "fun"),
    ("hazme una pregunta divertida", "fun"),
    ("quiero jugar", "fun"),
    ("dime algo interesante", "fun"),
    ("tienes algun chiste malo", "fun"),
    ("cuentame algo gracioso", "fun"),
    ("pon algo divertido", "fun"),
    ("quiero entretenerme", "fun"),
    ("juega conmigo", "fun"),
    ("dime una adivinanza", "fun"),
    ("hazme una trivia", "fun"),
    ("quiero reir un rato", "fun"),
    ("sentinel cuentame un chiste", "fun"),
    ("sentinel dime un chiste", "fun"),
    ("sentinel hazme reir", "fun"),
    ("sentinel di algo divertido", "fun"),
    ("sentinel cuentame algo gracioso", "fun"),
    ("que chistes sabes", "fun"),
    ("sabes jugar veinte preguntas", "fun"),
    ("dime algo random", "fun"),
    ("cuentame algo loco", "fun"),
    ("quiero saber algo raro", "fun"),

    # NOTES
    ("crear una nota", "notes"),
    ("guarda esto en mis notas", "notes"),
    ("escribe esto", "notes"),
    ("guardar recordatorio", "notes"),
    ("anota esta idea", "notes"),
    ("quiero guardar esta idea", "notes"),
    ("anade una nota", "notes"),
    ("registra esto", "notes"),
    ("guarda que tengo que llamar al doctor", "notes"),
    ("recuerda que necesito comprar leche", "notes"),
    ("anota que tengo cita el jueves", "notes"),
    ("escribe un recordatorio para manana", "notes"),
    ("guarda mi idea de negocio", "notes"),
    ("quiero anotar algo importante", "notes"),
    ("no quiero olvidar esto", "notes"),
    ("guarda esta informacion", "notes"),
    ("sentinel crea una nota", "notes"),
    ("sentinel guarda esto", "notes"),
    ("sentinel anota esto", "notes"),
    ("sentinel registra esta idea", "notes"),
    ("pon una nota sobre mi proyecto", "notes"),
    ("necesito anotar algo", "notes"),
    ("guarda este pensamiento", "notes"),
    ("anota el numero de telefono", "notes"),
    ("escribe la direccion", "notes"),
    ("recuerda este dato", "notes"),

    # GENERAL
    ("hola", "general"),
    ("como estas", "general"),
    ("que puedes hacer", "general"),
    ("quien eres", "general"),
    ("buenos dias", "general"),
    ("buenas noches", "general"),
    ("buenas tardes", "general"),
    ("hola sentinel", "general"),
    ("que tal", "general"),
    ("como te llamas", "general"),
    ("que eres", "general"),
    ("para que sirves", "general"),
    ("dime algo", "general"),
    ("necesito ayuda con algo", "general"),
    ("oye sentinel", "general"),
    ("estas ahi", "general"),
    ("me escuchas", "general"),
    ("cuentame algo", "general"),
    ("que hay de nuevo", "general"),
    ("sentinel hola", "general"),
    ("ok sentinel", "general"),
    ("sentinel aqui estoy", "general"),
    ("habla conmigo", "general"),
]

# ──────────────────────────────────────────────
# Entrenamiento
# ──────────────────────────────────────────────
_texts = [_normalize(t) for t, _ in _TRAINING]
_labels = [label for _, label in _TRAINING]

_pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    )),
    ("clf", ComplementNB(alpha=0.3)),
])

_pipeline.fit(_texts, _labels)


# ──────────────────────────────────────────────
# Función pública
# ──────────────────────────────────────────────
def classify(text: str) -> tuple[str, float]:
    """
    Recibe texto en español y devuelve (intent, confidence).

    Intents posibles:
        emergency, music, productivity, emotional,
        system, time, fun, notes, general
    """
    if not text or text.strip() == "":
        return "general", 0.0

    # Emergencia clara siempre gana
    if _has_emergency_keyword(text):
        return "emergency", 0.99

    # Reglas directas para comandos claros
    rule_result = _rule_based_intent(text)
    if rule_result is not None:
        return rule_result

    # Modelo ML como fallback inteligente
    clean = _normalize(text)

    probs = _pipeline.predict_proba([clean])[0]
    classes = _pipeline.classes_

    idx = probs.argmax()
    intent = classes[idx]
    confidence = round(float(probs[idx]), 4)

    if confidence < CONFIDENCE_THRESHOLD:
        return "general", confidence

    return intent, confidence