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


# ──────────────────────────────────────────────
# Palabras clave de modo clase (para detección rápida)
# ──────────────────────────────────────────────
_CLASS_MODE_KEYWORDS = [
    "modo clase",
    "grabar la clase",
    "graba la clase",
    "empieza a grabar",
    "activa modo clase",
    "empieza modo clase",
    "deten modo clase",
    "detener modo clase",
    "termina la clase",
    "terminar la clase",
    "resume la clase",
    "resumen de la clase",
    "que tareas dejo el profesor",
    "que tareas hay de clase",
    "tareas de la clase",
    "desactiva modo clase",
    "inicia modo clase",
    "guarda esta explicacion",
    "guarda esta explicación",
]


def _has_class_mode_keyword(text: str) -> bool:
    t = _normalize(text)
    return any(_normalize(k) in t for k in _CLASS_MODE_KEYWORDS)


# ──────────────────────────────────────────────
# Palabras clave Nivel 2
# ──────────────────────────────────────────────
_FOCUS_MODE_KEYWORDS = [
    "modo enfoque", "modo estudiar", "modo programar", "empieza pomodoro",
    "inicia pomodoro", "activa modo enfoque", "necesito enfocarme",
    "quiero enfocarme", "descanso de cinco minutos", "termina modo enfoque",
    "cuanto falta del pomodoro", "termina pomodoro", "pausa enfoque",
]

_PRESENTATION_MODE_KEYWORDS = [
    "modo presentacion",
    "modo presentación",
    "modo demo",
    "prepara demo",
    "prepara la demo",
    "activa modo presentacion",
    "activa modo presentación",
    "abre la app",
    "abre sentinel",
    "abre la demo",
    "termina modo demo",
]


_MEDIA_KEYWORDS = [
    "sube volumen", "baja volumen", "silencia", "mute",
    "pausa musica", "pausa música", "reproduce musica", "reproduce música",
    "play pause", "siguiente cancion", "siguiente canción",
    "cancion anterior", "canción anterior",
]

_FILES_KEYWORDS = [
    "abre descargas", "abre documentos", "abre escritorio", "abre carpeta de apuntes",
    "abre mis apuntes", "crea una carpeta para la clase",
    "guarda esto como archivo", "guarda esta nota como archivo",
]

_ROUTINE_KEYWORDS = [
    "modo descanso", "modo estudiar", "modo programar", "modo demo",
    "prepara demo", "rutina estudiar", "rutina programar",
]

_WEB_SEARCH_KEYWORDS = [
    "busca", "buscar", "buscame", "búscame", "investiga"
]

_WEB_SHORTCUT_KEYWORDS = [
    "abre gmail", "abre correo", "abre drive", "abre google drive",
    "abre calendario", "abre google calendar",

    # GitHub normal + errores comunes de transcripción
    "abre github", "abrir github", "github", "git hub", "guit hub",
    "githab", "gitjab", "kit hub", "kithub", "kid hu", "kidhu",
    "kitho", "vit hub", "vithub", "vitzhub", "gijub",

    # ChatGPT normal + errores comunes de transcripción
    "abre chatgpt", "abrir chatgpt", "chatgpt", "chat gpt",
    "chat g p t", "chet gpt", "chetpiti", "chetipiti",
    "cheetum", "chit gpt", "chad gpt",

    # Claude
    "abre claude", "abrir claude", "claude", "clod", "cloud",

    "abre google", "abre youtube"
]


_SYSTEM_KEYWORDS = [
    # calculadora
    "abre calculadora",
    "abre la calculadora",
    "abrir calculadora",
    "abrir la calculadora",
    "calculadora",
    "calculator",
    "calculador",
    "calc",

    # notas / editores
    "abre bloc de notas",
    "abre el bloc de notas",
    "abrir bloc de notas",
    "bloc de notas",
    "notepad",
    "notepads",
    "nota pad",
    "notas de windows",
    "textedit",
    "editor de texto",

    # archivos / explorer / finder
    "abre explorador",
    "abre el explorador",
    "abre explorador de archivos",
    "abre el explorador de archivos",
    "abrir explorador",
    "explorador",
    "explorador de archivos",
    "abre archivos",
    "abrir archivos",
    "file explorer",
    "finder",

    # vscode
    "abre vs code",
    "abrir vs code",
    "vs code",
    "visual studio code",
    "vscode",

    # spotify
    "abre spotify",
    "abrir spotify",
    "spotify",

    # office
    "abre excel",
    "abre microsoft excel",
    "abrir excel",
    "excel",
    "hoja de calculo",
    "hoja de cálculo",

    "abre word",
    "abre microsoft word",
    "abrir word",
    "word",
    "documento de word",

    "abre powerpoint",
    "abre power point",
    "abre microsoft powerpoint",
    "abrir powerpoint",
    "powerpoint",
    "power point",
    "presentacion",
    "presentación",
    "diapositivas",

    "abre outlook",
    "abrir outlook",
    "outlook",
    "correo de outlook",

    "abre teams",
    "abrir teams",
    "microsoft teams",
    "teams",

    "abre onenote",
    "abre one note",
    "abrir onenote",
    "onenote",
    "one note",

    # web normal
    "abre google",
    "abrir google",
    "abre youtube",
    "abrir youtube",
    "youtube",
    "google",
    "navegador",
    "browser",
    "chrome",

    "abre gmail",
    "abrir gmail",
    "abre correo",
    "abrir correo",
    "abre drive",
    "abrir drive",
    "abre google drive",
    "abre calendario",
    "abre google calendar",
    "abre github",
    "abrir github",
    "abre chatgpt",
    "abrir chatgpt",
    "abre claude",
    "abrir claude",

    # carpetas
    "abre descargas",
    "abrir descargas",
    "downloads",
    "abre documentos",
    "abrir documentos",
    "documents",
    "abre escritorio",
    "abrir escritorio",
    "desktop",
    "abre apuntes",
    "abrir apuntes",
        # GitHub aliases
    "github",
    "git hub",
    "guit hub",
    "githab",
    "gitjab",
    "kit hub",
    "kithub",
    "kid hu",
    "kidhu",
    "kitho",
    "vit hub",
    "vithub",
    "vitzhub",
    "gijub",

    # ChatGPT aliases
    "chatgpt",
    "chat gpt",
    "chat g p t",
    "chet gpt",
    "chetpiti",
    "chetipiti",
    "cheetum",
    "chit gpt",
    "chad gpt",

    # Claude aliases
    "claude",
    "clod",
    "cloud",
        # Claude / IA aliases
    "abre inteligencia artificial",
    "abrir inteligencia artificial",
    "inteligencia artificial",
    "abre ia",
    "abrir ia",
    "ia",
    "abre el asistente",
    "abrir el asistente",
    "asistente",
    "asistente naranja",
    "abre asistente naranja",
    "abrir asistente naranja",
    "chatbot",
    "chat bot",
    "abre chatbot",
    "abrir chatbot",
    "claude",
    "clod",
    "cloud",
    "anthropic",
    "antropic",
]


def _has_any_keyword(text: str, keywords: list[str]) -> bool:
    t = _normalize(text)
    return any(_normalize(k) in t for k in keywords)


def _rule_based_intent(text: str):
    """
    Reglas directas para comandos muy claros.
    Esto evita que comandos como 'abre la calculadora' caigan en general.
    """
    t = _normalize(text)

    # CLASS MODE primero porque tiene comandos muy específicos
    if _has_class_mode_keyword(text):
        return "class_mode", 0.97

    # PRESENTATION / DEMO solo con frases claras de demo
    if _has_any_keyword(text, _PRESENTATION_MODE_KEYWORDS):
        return "presentation_mode", 0.96

    # SYSTEM: apps locales, Office, web shortcuts y comandos normales
    if _has_any_keyword(text, _SYSTEM_KEYWORDS):
        return "system", 0.97

    # Rutinas compuestas
    if _has_any_keyword(text, _ROUTINE_KEYWORDS):
        if _has_any_keyword(text, ["modo demo", "prepara demo", "prepara la demo"]):
            return "presentation_mode", 0.96
        if _has_any_keyword(text, ["modo descanso"]):
            return "routine", 0.94
        return "focus_mode", 0.96

    # Enfoque / Pomodoro
    if _has_any_keyword(text, _FOCUS_MODE_KEYWORDS):
        return "focus_mode", 0.96

    # Multimedia
    if _has_any_keyword(text, _MEDIA_KEYWORDS):
        return "media", 0.96

    # Archivos
    if _has_any_keyword(text, _FILES_KEYWORDS):
        return "files", 0.96

    # Búsquedas web
    if _has_any_keyword(text, _WEB_SEARCH_KEYWORDS) or _has_any_keyword(text, _WEB_SHORTCUT_KEYWORDS):
        return "system", 0.94

    # NOTAS
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

    # PRODUCTIVIDAD
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


    # FOCUS MODE
    ("activa modo enfoque", "focus_mode"),
    ("modo estudiar", "focus_mode"),
    ("modo programar", "focus_mode"),
    ("empieza pomodoro", "focus_mode"),
    ("inicia pomodoro", "focus_mode"),
    ("cuanto falta del pomodoro", "focus_mode"),
    ("termina pomodoro", "focus_mode"),
    ("descanso de cinco minutos", "focus_mode"),

    # PRESENTATION MODE
    ("activa modo presentacion", "presentation_mode"),
    ("modo demo", "presentation_mode"),
    ("prepara demo", "presentation_mode"),
    ("abre la app", "presentation_mode"),

    # MEDIA
    ("sube volumen", "media"),
    ("baja volumen", "media"),
    ("silencia", "media"),
    ("pausa musica", "media"),
    ("siguiente cancion", "media"),
    ("cancion anterior", "media"),

    # FILES
    ("abre descargas", "files"),
    ("abre documentos", "files"),
    ("abre escritorio", "files"),
    ("abre carpeta de apuntes", "files"),
    ("guarda esto como archivo", "files"),

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

    # CLASS MODE
    ("activa modo clase", "class_mode"),
    ("empieza modo clase", "class_mode"),
    ("empieza a grabar la clase", "class_mode"),
    ("graba la clase", "class_mode"),
    ("inicia el modo clase", "class_mode"),
    ("deten modo clase", "class_mode"),
    ("termina la clase", "class_mode"),
    ("terminar la clase ahora", "class_mode"),
    ("desactiva modo clase", "class_mode"),
    ("resume la clase", "class_mode"),
    ("resumen de la clase", "class_mode"),
    ("que tareas dejo el profesor", "class_mode"),
    ("que tareas hay de clase", "class_mode"),
    ("tareas de la clase de hoy", "class_mode"),
    ("guarda esta explicacion", "class_mode"),
    ("modo clase activado", "class_mode"),
    ("quiero grabar la clase", "class_mode"),
    ("sentinel activa modo clase", "class_mode"),
    ("sentinel graba la clase", "class_mode"),
    ("sentinel termina la clase", "class_mode"),
    ("sentinel resume la clase", "class_mode"),
        ("abre excel", "system"),
    ("abre microsoft excel", "system"),
    ("abre una hoja de calculo", "system"),
    ("abre una hoja de cálculo", "system"),
    ("quiero abrir excel", "system"),

    ("abre word", "system"),
    ("abre microsoft word", "system"),
    ("abre un documento de word", "system"),
    ("quiero escribir en word", "system"),

    ("abre powerpoint", "system"),
    ("abre power point", "system"),
    ("abre una presentacion", "system"),
    ("abre una presentación", "system"),
    ("abre diapositivas", "system"),

    ("abre outlook", "system"),
    ("abre correo de outlook", "system"),
    ("abre mi correo", "system"),

    ("abre onenote", "system"),
    ("abre one note", "system"),
    ("abre mis notas de onenote", "system"),

    ("abre teams", "system"),
    ("abre microsoft teams", "system"),
    ("abre una reunion en teams", "system"),
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
        system, time, fun, notes, general, class_mode,
        focus_mode, presentation_mode, media, files, routine
    """
    if not text or text.strip() == "":
        return "general", 0.0

    # Emergencia clara siempre gana
    if _has_emergency_keyword(text):
        return "emergency", 0.99

    # Reglas directas para comandos claros (incluye class_mode)
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