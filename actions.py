"""
actions.py
──────────────────────────────────────────────
Sentinel AI — Capa de acciones locales.

Filosofía: local-first. Las funciones críticas NO dependen de internet ni
de APIs externas. Las integraciones web como YouTube o Google son
extras opcionales que se activan cuando el usuario las pide.

Función pública:
    execute_action(intent, text) -> dict | None
"""

import os
import random
import platform
import subprocess
import webbrowser
import unicodedata
import urllib.parse
from datetime import datetime

import class_mode as cm
import assistant_modes as modes


# ──────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────
def _normalize(text: str) -> str:
    """Convierte texto a minúsculas y quita acentos para matching robusto."""
    if not text:
        return ""

    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    return text


def _contains_any(text: str, keywords) -> bool:
    t = _normalize(text)
    return any(_normalize(k) in t for k in keywords)


def _is_windows() -> bool:
    return platform.system().lower() == "windows"


def _is_macos() -> bool:
    return platform.system().lower() == "darwin"


def _is_linux() -> bool:
    return platform.system().lower() == "linux"


def _run_command(command, shell: bool = False):
    """
    Ejecuta comandos sin bloquear Flask.
    Devuelve (ok, error).
    """
    try:
        subprocess.Popen(command, shell=shell)
        return True, None
    except Exception as e:
        return False, e


# ──────────────────────────────────────────────
# Días y meses en español
# ──────────────────────────────────────────────
_DIAS = [
    "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo"
]

_MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


# ──────────────────────────────────────────────
# Chistes / datos curiosos locales
# ──────────────────────────────────────────────
_FUN_LINES = [
    "¿Sabes qué le dice un bit a otro bit? Nos vemos en el bus.",
    "¿Por qué los programadores prefieren el modo oscuro? Porque la luz atrae bugs.",
    "Dato curioso: el pulpo tiene tres corazones y sangre azul.",
    "¿Qué hace una abeja en el gimnasio? Zum-ba.",
    "Dato curioso: en Júpiter, un día dura menos de 10 horas terrestres.",
    "¿Por qué la computadora fue al médico? Porque tenía un virus.",
    "Era tan tímido el teclado que solo se atrevía a hablar con las teclas.",
    "Dato curioso: los flamingos son rosados por lo que comen, no por nacimiento.",
    "¿Cómo se llama el campeón mundial de buceo japonés? Tokofondo.",
    "Dato curioso: una cucharadita de estrella de neutrones pesaría unos 6 mil millones de toneladas.",
    "¿Qué le dice un jaguar a otro jaguar? Jaguar you?",
    "Dato curioso: los koalas duermen hasta 22 horas al día. Mood.",
    "¿Por qué los peces no usan computadora? Porque les da miedo la red.",
    "Dato curioso: el corazón de una ballena azul pesa más que un coche pequeño.",
]


# ══════════════════════════════════════════════
# Apps locales
# ══════════════════════════════════════════════
def _open_calculator() -> dict:
    if _is_windows():
        ok, error = _run_command("calc.exe", shell=True)

    elif _is_macos():
        ok, error = _run_command(["open", "-a", "Calculator"])

        if not ok:
            ok, error = _run_command(["open", "/System/Applications/Calculator.app"])

    elif _is_linux():
        ok, error = _run_command(["gnome-calculator"])

    else:
        ok, error = False, None

    if ok:
        return {
            "response": "Abriendo calculadora.",
            "action_executed": True,
            "action_type": "local_app",
        }

    return {
        "response": f"No pude abrir la calculadora. ({type(error).__name__ if error else 'UnsupportedOS'})",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_notepad() -> dict:
    if _is_windows():
        ok, error = _run_command("notepad.exe", shell=True)
        app_name = "bloc de notas"

    elif _is_macos():
        ok, error = _run_command(["open", "-a", "TextEdit"])
        app_name = "TextEdit"

    elif _is_linux():
        ok, error = _run_command(["gedit"])
        app_name = "editor de texto"

    else:
        ok, error = False, None
        app_name = "editor de texto"

    if ok:
        return {
            "response": f"Abriendo {app_name}.",
            "action_executed": True,
            "action_type": "local_app",
        }

    return {
        "response": f"No pude abrir {app_name}. ({type(error).__name__ if error else 'UnsupportedOS'})",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_explorer() -> dict:
    if _is_windows():
        ok, error = _run_command("explorer.exe", shell=True)
        app_name = "explorador de archivos"

    elif _is_macos():
        ok, error = _run_command(["open", "-a", "Finder"])
        app_name = "Finder"

        if not ok:
            ok, error = _run_command(["open", os.path.expanduser("~")])

    elif _is_linux():
        ok, error = _run_command(["xdg-open", os.path.expanduser("~")])
        app_name = "carpeta personal"

    else:
        ok, error = False, None
        app_name = "explorador de archivos"

    if ok:
        return {
            "response": f"Abriendo {app_name}.",
            "action_executed": True,
            "action_type": "local_app",
        }

    return {
        "response": f"No pude abrir {app_name}. ({type(error).__name__ if error else 'UnsupportedOS'})",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_vscode() -> dict:
    if _is_macos():
        ok, error = _run_command(["open", "-a", "Visual Studio Code"])

        if not ok:
            ok, error = _run_command("code", shell=True)

    elif _is_windows():
        ok, error = _run_command("code", shell=True)

    elif _is_linux():
        ok, error = _run_command("code", shell=True)

    else:
        ok, error = False, None

    if ok:
        return {
            "response": "Abriendo Visual Studio Code.",
            "action_executed": True,
            "action_type": "local_app",
        }

    return {
        "response": f"No pude abrir VS Code. ({type(error).__name__ if error else 'No encontrado'})",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_spotify() -> dict:
    if _is_windows():
        ok, error = _run_command("spotify", shell=True)

    elif _is_macos():
        ok, error = _run_command(["open", "-a", "Spotify"])

    elif _is_linux():
        ok, error = _run_command(["spotify"])

    else:
        ok, error = False, None

    if ok:
        return {
            "response": "Abriendo Spotify.",
            "action_executed": True,
            "action_type": "local_app",
        }

    return {
        "response": f"No pude abrir Spotify. ({type(error).__name__ if error else 'No instalado'})",
        "action_executed": False,
        "action_type": "local_app",
    }


# ══════════════════════════════════════════════
# Extras web opcionales
# ══════════════════════════════════════════════
def _open_browser_google() -> dict:
    try:
        webbrowser.open("https://www.google.com")

        return {
            "response": "Abriendo Google en el navegador.",
            "action_executed": True,
            "action_type": "web_extra",
        }

    except Exception as e:
        return {
            "response": f"No pude abrir el navegador. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "web_extra",
        }


def _open_youtube_search(text: str) -> dict:
    try:
        query = urllib.parse.quote_plus(text.strip())
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)

        return {
            "response": "Abriendo YouTube con tu búsqueda.",
            "action_executed": True,
            "action_type": "web_extra",
        }

    except Exception as e:
        return {
            "response": f"No pude abrir YouTube. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "web_extra",
        }


# ══════════════════════════════════════════════
# SYSTEM
# ══════════════════════════════════════════════
def _handle_system(text: str) -> dict | None:
    """
    Detecta qué app/página/carpeta quiere abrir el usuario dentro del intent system.
    """

    # Búsquedas web y accesos rápidos se revisan primero.
    search_result = modes.web_search(text)
    if search_result is not None:
        return search_result

    web_result = modes.open_web_shortcut(text)
    if web_result is not None:
        return web_result

    if _contains_any(text, ["descargas", "downloads", "documentos", "documents", "escritorio", "desktop", "apuntes"]):
        return modes.handle_files(text)

    if _contains_any(text, ["sube volumen", "baja volumen", "silencia", "mute", "play pause", "pausa musica", "siguiente cancion", "cancion anterior"]):
        return modes.handle_media(text)

    if _contains_any(text, ["calculadora", "calculator", "calc"]):
        return _open_calculator()

    if _contains_any(text, ["bloc de notas", "notepad", "notas de windows", "textedit"]):
        return _open_notepad()

    if _contains_any(text, ["explorador", "archivos", "carpeta", "file explorer", "finder"]):
        return _open_explorer()

    if _contains_any(text, ["vs code", "visual studio code", "vscode"]):
        return _open_vscode()

    if _contains_any(text, ["spotify"]):
        return _open_spotify()

    if _contains_any(text, ["youtube", "you tube"]):
        return _open_youtube_search(text)

    if _contains_any(text, ["navegador", "google", "browser", "chrome"]):
        return _open_browser_google()

    return {
        "response": (
            "Modo sistema detectado. Puedo abrir calculadora, bloc de notas, "
            "explorador de archivos, VS Code, Spotify, YouTube o el navegador."
        ),
        "action_executed": False,
        "action_type": "none",
    }


# ══════════════════════════════════════════════
# TIME
# ══════════════════════════════════════════════
def _handle_time(text: str) -> dict:
    now = datetime.now()
    t = _normalize(text)

    fecha_keywords = ["fecha", "dia", "que dia", "hoy"]
    hora_keywords = ["hora", "horas", "que hora"]

    asks_fecha = any(k in t for k in fecha_keywords)
    asks_hora = any(k in t for k in hora_keywords)

    if asks_fecha and not asks_hora:
        dia_semana = _DIAS[now.weekday()]
        mes = _MESES[now.month]

        return {
            "response": f"Hoy es {dia_semana}, {now.day} de {mes} de {now.year}.",
            "action_executed": True,
            "action_type": "local_info",
        }

    hora_str = now.strftime("%H:%M")

    if asks_fecha and asks_hora:
        dia_semana = _DIAS[now.weekday()]
        mes = _MESES[now.month]
        response = f"Son las {hora_str}. Hoy es {dia_semana}, {now.day} de {mes}."
    else:
        response = f"Son las {hora_str}."

    return {
        "response": response,
        "action_executed": True,
        "action_type": "local_info",
    }


# ══════════════════════════════════════════════
# FUN
# ══════════════════════════════════════════════
def _handle_fun(text: str) -> dict:
    line = random.choice(_FUN_LINES)

    return {
        "response": line,
        "action_executed": True,
        "action_type": "local_info",
    }


# ══════════════════════════════════════════════
# MUSIC
# ══════════════════════════════════════════════
def _handle_music(text: str) -> dict:
    t = _normalize(text)

    if "spotify" in t:
        return _open_spotify()

    if "youtube" in t or "you tube" in t:
        return _open_youtube_search(text)

    return {
        "response": "Modo música detectado. Di 'abre Spotify' o 'abre YouTube'.",
        "action_executed": False,
        "action_type": "none",
    }


# ══════════════════════════════════════════════
# EMERGENCY
# ══════════════════════════════════════════════
def _handle_emergency(text: str) -> dict:
    return {
        "response": (
            "Emergencia detectada. Activando protocolo visual local y "
            "preparando opciones de contacto."
        ),
        "action_executed": True,
        "action_type": "local_protocol",
    }


# ══════════════════════════════════════════════
# EMOTIONAL
# ══════════════════════════════════════════════
def _handle_emotional(text: str) -> dict:
    return {
        "response": (
            "Estoy contigo. Respira lento: inhala 4 segundos, sostén 4 y "
            "exhala 4. Si estás en peligro inmediato, pide ayuda a alguien cercano."
        ),
        "action_executed": True,
        "action_type": "local_support",
    }


# ══════════════════════════════════════════════
# CLASS MODE
# ══════════════════════════════════════════════
def _handle_class_mode(text: str) -> dict:
    t = _normalize(text)

    # Activar modo clase
    if any(k in t for k in [
        "activa modo clase", "empieza modo clase",
        "empieza a grabar la clase", "graba la clase",
        "inicia modo clase", "modo clase on",
    ]):
        result = cm.start_class_session()
        return {
            "response": result["message"],
            "action_executed": result["ok"],
            "action_type": "class_mode",
            "class_mode_active": result["ok"],
            "class_file_path": result.get("file_path"),
            "class_notes": [],
            "class_summary": None,
            "detected_class_tasks": [],
        }

    # Detener modo clase
    if any(k in t for k in [
        "deten modo clase", "detener modo clase",
        "termina la clase", "terminar la clase",
        "desactiva modo clase", "modo clase off",
        "para la clase", "detén modo clase",
    ]):
        result = cm.stop_class_session()
        return {
            "response": result["message"],
            "action_executed": result["ok"],
            "action_type": "class_mode",
            "class_mode_active": False,
            "class_file_path": result.get("file_path"),
            "class_notes": [],
            "class_summary": None,
            "detected_class_tasks": [],
        }

    # Resumir clase
    if any(k in t for k in [
        "resume la clase", "resumen de la clase",
        "que se vio en clase", "que dijeron en clase",
        "resume mis apuntes",
    ]):
        summary = cm.get_class_summary()
        return {
            "response": summary,
            "action_executed": True,
            "action_type": "class_mode",
            "class_mode_active": cm.get_class_state()["active"],
            "class_file_path": cm.get_class_state()["file_path"],
            "class_notes": [],
            "class_summary": summary,
            "detected_class_tasks": [],
        }

    # Tareas detectadas en clase
    if any(k in t for k in [
        "que tareas dejo el profesor", "que tareas hay",
        "tareas de la clase", "que tarea nos dejaron",
    ]):
        state = cm.get_class_state()
        return {
            "response": "Revisando tareas detectadas durante la clase. Consulta el panel de tareas.",
            "action_executed": True,
            "action_type": "class_mode",
            "class_mode_active": state["active"],
            "class_file_path": state["file_path"],
            "class_notes": [],
            "class_summary": None,
            "detected_class_tasks": [],
        }

    # Genérico: estado actual
    state = cm.get_class_state()
    if state["active"]:
        msg = f"Modo clase activo. Llevo {state['duration']} grabando."
    else:
        msg = "Modo clase inactivo. Di 'activa modo clase' para comenzar."

    return {
        "response": msg,
        "action_executed": True,
        "action_type": "class_mode",
        "class_mode_active": state["active"],
        "class_file_path": state["file_path"],
        "class_notes": [],
        "class_summary": None,
        "detected_class_tasks": [],
    }




# ══════════════════════════════════════════════
# FOCUS / PRESENTATION / MEDIA / FILES / ROUTINES
# ══════════════════════════════════════════════
def _handle_focus_mode(text: str) -> dict:
    return modes.handle_focus_mode(text)


def _handle_presentation_mode(text: str) -> dict:
    return modes.handle_presentation_mode(text)


def _handle_media(text: str) -> dict:
    return modes.handle_media(text)


def _handle_files(text: str) -> dict:
    return modes.handle_files(text)


def _handle_routine(text: str) -> dict:
    return modes.handle_routine(text)

# ══════════════════════════════════════════════
# Función pública
# ══════════════════════════════════════════════
def execute_action(intent: str, text: str) -> dict | None:
    """
    Ejecuta acción real para el intent dado, si aplica.

    Devuelve dict con:
        response
        action_executed
        action_type

    O None si app.py debe usar su lógica por defecto.
    """

    if not intent:
        return None

    intent = intent.lower().strip()

    try:
        if intent == "system":
            return _handle_system(text)

        if intent == "time":
            return _handle_time(text)

        if intent == "fun":
            return _handle_fun(text)

        if intent == "music":
            return _handle_music(text)

        if intent == "emergency":
            return _handle_emergency(text)

        if intent == "emotional":
            return _handle_emotional(text)

        if intent == "class_mode":
            return _handle_class_mode(text)

        if intent == "focus_mode":
            return _handle_focus_mode(text)

        if intent == "presentation_mode":
            return _handle_presentation_mode(text)

        if intent == "media":
            return _handle_media(text)

        if intent == "files":
            return _handle_files(text)

        if intent == "routine":
            return _handle_routine(text)

        # notes, productivity, general → app.py se encarga
        return None

    except Exception as e:
        return {
            "response": f"Ocurrió un error al ejecutar la acción. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "none",
        }