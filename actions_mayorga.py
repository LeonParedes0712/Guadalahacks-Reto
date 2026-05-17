"""
actions.py
──────────────────────────────────────────────
Sentinel AI — Capa de acciones locales (Windows + macOS + Linux).

Filosofía: local-first. Las funciones críticas NO dependen de internet ni
de APIs externas. Las integraciones web (Spotify, YouTube, Google) son
extras opcionales que se activan SOLO cuando el usuario las pide
explícitamente por nombre.

Función pública:
    execute_action(intent, text) -> dict | None

Devuelve un dict con:
    {
        "response": str,             # qué decirle al usuario
        "action_executed": bool,     # si se ejecutó algo real
        "action_type": str           # local_app | local_info | local_protocol
                                     # | local_support | web_extra | none
    }

O None si no hay acción concreta y app.py debe usar su lógica por defecto
(por ejemplo, notes y productivity siguen guardándose en app.py).
"""

import os
import random
import platform
import subprocess
import webbrowser
import unicodedata
import urllib.parse
from datetime import datetime


# ──────────────────────────────────────────────
# Utilidades de texto
# ──────────────────────────────────────────────
def _normalize(text: str) -> str:
    """Lowercase, sin acentos, sin signos. Para hacer matching robusto."""
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def _contains_any(text: str, keywords) -> bool:
    t = _normalize(text)
    return any(_normalize(k) in t for k in keywords)


# ──────────────────────────────────────────────
# Detección de sistema operativo
# ──────────────────────────────────────────────
def _is_windows() -> bool:
    return platform.system().lower() == "windows"


def _is_macos() -> bool:
    return platform.system().lower() == "darwin"


def _is_linux() -> bool:
    return platform.system().lower() == "linux"


# ──────────────────────────────────────────────
# Helper genérico para correr comandos
# ──────────────────────────────────────────────
def _run_command(command, shell: bool = False) -> tuple[bool, Exception | None]:
    """
    Ejecuta un comando con subprocess.Popen sin bloquear Flask.

    `command` puede ser:
      - string (cuando shell=True, p.ej. "calc.exe")
      - lista (cuando shell=False, p.ej. ["open", "-a", "Calculator"])

    Devuelve (ok, error). Nunca lanza excepción.
    """
    try:
        subprocess.Popen(command, shell=shell)
        return True, None
    except Exception as e:
        return False, e


# ──────────────────────────────────────────────
# Localización manual (días y meses en español)
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
# Chistes / datos curiosos locales (sin internet)
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
# SYSTEM — abrir apps locales (multiplataforma)
# ══════════════════════════════════════════════
def _open_calculator() -> dict:
    if _is_windows():
        ok, _ = _run_command("calc.exe", shell=True)
    elif _is_macos():
        ok, _ = _run_command(["open", "-a", "Calculator"])
    elif _is_linux():
        ok, _ = _run_command(["gnome-calculator"])
    else:
        ok = False

    if ok:
        return {
            "response": "Abriendo calculadora.",
            "action_executed": True,
            "action_type": "local_app",
        }
    return {
        "response": "No pude abrir la calculadora. Puede que no esté instalada en este sistema.",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_notepad() -> dict:
    if _is_windows():
        ok, _ = _run_command("notepad.exe", shell=True)
        app_name = "el bloc de notas"
    elif _is_macos():
        ok, _ = _run_command(["open", "-a", "TextEdit"])
        app_name = "TextEdit"
    elif _is_linux():
        ok, _ = _run_command(["gedit"])
        app_name = "el editor de texto"
    else:
        ok, app_name = False, "el editor de texto"

    if ok:
        return {
            "response": f"Abriendo {app_name}.",
            "action_executed": True,
            "action_type": "local_app",
        }
    return {
        "response": f"No pude abrir {app_name}. Puede que no esté instalado.",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_explorer() -> dict:
    if _is_windows():
        ok, _ = _run_command("explorer.exe", shell=True)
        app_name = "el explorador de archivos"
    elif _is_macos():
        ok, _ = _run_command(["open", "-a", "Finder"])
        app_name = "Finder"
    elif _is_linux():
        ok, _ = _run_command(["xdg-open", os.path.expanduser("~")])
        app_name = "la carpeta personal"
    else:
        ok, app_name = False, "el explorador de archivos"

    if ok:
        return {
            "response": f"Abriendo {app_name}.",
            "action_executed": True,
            "action_type": "local_app",
        }
    return {
        "response": f"No pude abrir {app_name}.",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_vscode() -> dict:
    if _is_macos():
        # En macOS usar el bundle por nombre — más confiable que depender del PATH
        ok, _ = _run_command(["open", "-a", "Visual Studio Code"])
    else:
        # Windows y Linux: requiere que 'code' esté en PATH
        # (Windows: opción del instalador. Linux: paquete oficial.)
        ok, _ = _run_command("code", shell=True)

    if ok:
        return {
            "response": "Abriendo Visual Studio Code.",
            "action_executed": True,
            "action_type": "local_app",
        }
    return {
        "response": "No pude abrir Visual Studio Code. Puede que no esté instalado o no esté en PATH.",
        "action_executed": False,
        "action_type": "local_app",
    }


def _open_browser_google() -> dict:
    """Abrir navegador en Google — acción web extra (multiplataforma vía webbrowser)."""
    try:
        webbrowser.open("https://www.google.com")
        return {
            "response": "Abriendo Google en el navegador (extra web).",
            "action_executed": True,
            "action_type": "web_extra",
        }
    except Exception as e:
        return {
            "response": f"No pude abrir el navegador. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "web_extra",
        }


def _handle_system(text: str) -> dict | None:
    """
    Detecta qué app quiere abrir el usuario dentro del intent system.
    Devuelve None si no se reconoce ningún subcomando claro.
    """

    # Redirección: si el intent engine manda Spotify/YouTube como system,
    # lo pasamos a música.
    if _contains_any(text, ["spotify", "youtube", "you tube"]):
        return _handle_music(text)

    if _contains_any(text, ["calculadora", "calculator", "calc"]):
        return _open_calculator()

    if _contains_any(text, ["bloc de notas", "notepad", "notas de windows", "textedit"]):
        return _open_notepad()

    if _contains_any(text, ["explorador", "archivos", "carpeta", "file explorer", "finder"]):
        return _open_explorer()

    if _contains_any(text, ["vs code", "visual studio code", "vscode"]):
        return _open_vscode()

    if _contains_any(text, ["navegador", "google", "browser", "chrome"]):
        return _open_browser_google()

    return {
        "response": (
            "Modo sistema detectado. Puedo abrir calculadora, bloc de notas, "
            "explorador de archivos, VS Code o el navegador. ¿Cuál?"
        ),
        "action_executed": False,
        "action_type": "none",
    }


# ══════════════════════════════════════════════
# TIME — hora y fecha locales
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
        response = f"Hoy es {dia_semana}, {now.day} de {mes} de {now.year}."
        return {
            "response": response,
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
# FUN — chiste / dato curioso aleatorio local
# ══════════════════════════════════════════════
def _handle_fun(text: str) -> dict:
    line = random.choice(_FUN_LINES)
    return {
        "response": line,
        "action_executed": True,
        "action_type": "local_info",
    }


# ══════════════════════════════════════════════
# MUSIC — local-first, web opcional
# ══════════════════════════════════════════════
def _handle_music(text: str) -> dict:
    t = _normalize(text)

    if "spotify" in t:
        if _is_macos():
            ok, _ = _run_command(["open", "-a", "Spotify"])
        elif _is_windows():
            ok, _ = _run_command("spotify", shell=True)
        elif _is_linux():
            ok, _ = _run_command(["spotify"])
        else:
            ok = False

        if ok:
            return {
                "response": "Abriendo Spotify.",
                "action_executed": True,
                "action_type": "local_app",
            }

        return {
            "response": "No pude abrir Spotify. Puede que no esté instalado.",
            "action_executed": False,
            "action_type": "local_app",
        }

    if "youtube" in t or "you tube" in t:
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

    return {
        "response": "Modo música detectado. Di 'abre Spotify' o 'abre YouTube'.",
        "action_executed": False,
        "action_type": "none",
    }


# ══════════════════════════════════════════════
# EMERGENCY — protocolo visual local (NO llamadas reales)
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
# EMOTIONAL — apoyo básico seguro (sin diagnóstico)
# ══════════════════════════════════════════════
def _handle_emotional(text: str) -> dict:
    return {
        "response": (
            "Estoy contigo. Respira lento: inhala 4 segundos, sostén 4 y "
            "exhala 4. Si estás en peligro inmediato, pide ayuda a alguien "
            "cercano."
        ),
        "action_executed": True,
        "action_type": "local_support",
    }


# ══════════════════════════════════════════════
# Función pública
# ══════════════════════════════════════════════
def execute_action(intent: str, text: str) -> dict | None:
    """
    Ejecuta acción real para el intent dado, si aplica.

    Devuelve dict con response/action_executed/action_type, o None si no
    hay acción concreta y app.py debe usar su lógica por defecto.

    Intents manejados:
        system, time, fun, music, emergency, emotional
    Intents que devuelven None (lógica en app.py):
        notes, productivity, general
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

        # notes, productivity, general → app.py se encarga
        return None

    except Exception as e:
        # Última red de seguridad: jamás dejar que Flask explote por esto
        return {
            "response": f"Ocurrió un error al ejecutar la acción. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "none",
        }