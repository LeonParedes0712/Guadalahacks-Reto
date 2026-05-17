"""
actions.py
──────────────────────────────────────────────
Sentinel AI — Capa de acciones locales.

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
# Utilidades
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


def _is_windows() -> bool:
    return platform.system().lower() == "windows"


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
# SYSTEM — abrir apps locales (Windows)
# ══════════════════════════════════════════════
def _open_calculator() -> dict:
    try:
        if _is_windows():
            subprocess.Popen("calc.exe", shell=True)
        else:
            # Fallback no-Windows para desarrollo local
            subprocess.Popen(["gnome-calculator"])
        return {
            "response": "Abriendo calculadora.",
            "action_executed": True,
            "action_type": "local_app",
        }
    except Exception as e:
        return {
            "response": f"No pude abrir la calculadora automáticamente. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "local_app",
        }


def _open_notepad() -> dict:
    try:
        if _is_windows():
            subprocess.Popen("notepad.exe", shell=True)
        else:
            subprocess.Popen(["gedit"])
        return {
            "response": "Abriendo bloc de notas.",
            "action_executed": True,
            "action_type": "local_app",
        }
    except Exception as e:
        return {
            "response": f"No pude abrir el bloc de notas. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "local_app",
        }


def _open_explorer() -> dict:
    try:
        if _is_windows():
            subprocess.Popen("explorer.exe", shell=True)
        else:
            subprocess.Popen(["xdg-open", os.path.expanduser("~")])
        return {
            "response": "Abriendo el explorador de archivos.",
            "action_executed": True,
            "action_type": "local_app",
        }
    except Exception as e:
        return {
            "response": f"No pude abrir el explorador de archivos. ({type(e).__name__})",
            "action_executed": False,
            "action_type": "local_app",
        }


def _open_vscode() -> dict:
    try:
        # 'code' debe estar en PATH. En Windows VS Code lo agrega como opción
        # durante la instalación.
        subprocess.Popen("code", shell=True)
        return {
            "response": "Abriendo Visual Studio Code.",
            "action_executed": True,
            "action_type": "local_app",
        }
    except Exception:
        return {
            "response": "No pude abrir VS Code automáticamente. Puede que no esté instalado o no esté en PATH.",
            "action_executed": False,
            "action_type": "local_app",
        }


def _open_browser_google() -> dict:
    """Abrir navegador en Google — acción web extra."""
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
    if _contains_any(text, ["calculadora", "calculator", "calc"]):
        return _open_calculator()

    if _contains_any(text, ["bloc de notas", "notepad", "notas de windows"]):
        return _open_notepad()

    if _contains_any(text, ["explorador", "archivos", "carpeta", "file explorer"]):
        return _open_explorer()

    if _contains_any(text, ["vs code", "visual studio code", "vscode"]):
        return _open_vscode()

    if _contains_any(text, ["navegador", "google", "browser", "chrome"]):
        return _open_browser_google()

    # Subcomando no reconocido — dejar respuesta genérica
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

    # Fecha / día
    fecha_keywords = ["fecha", "dia", "que dia", "hoy"]
    hora_keywords = ["hora", "horas", "que hora"]

    asks_fecha = any(k in t for k in fecha_keywords)
    asks_hora = any(k in t for k in hora_keywords)

    if asks_fecha and not asks_hora:
        dia_semana = _DIAS[now.weekday()]
        mes = _MESES[now.month]
        response = (
            f"Hoy es {dia_semana}, {now.day} de {mes} de {now.year}."
        )
        return {
            "response": response,
            "action_executed": True,
            "action_type": "local_info",
        }

    # Por defecto: hora (también si pregunta hora y fecha combinadas)
    hora_str = now.strftime("%H:%M")
    if asks_fecha and asks_hora:
        dia_semana = _DIAS[now.weekday()]
        mes = _MESES[now.month]
        response = (
            f"Son las {hora_str}. Hoy es {dia_semana}, {now.day} de {mes}."
        )
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
        try:
            webbrowser.open("https://open.spotify.com")
            return {
                "response": "Abriendo Spotify en el navegador (extra web, requiere internet).",
                "action_executed": True,
                "action_type": "web_extra",
            }
        except Exception as e:
            return {
                "response": f"No pude abrir Spotify. ({type(e).__name__})",
                "action_executed": False,
                "action_type": "web_extra",
            }

    if "youtube" in t or "you tube" in t:
        try:
            # Buscar el texto completo del usuario en YouTube
            query = urllib.parse.quote_plus(text.strip())
            url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(url)
            return {
                "response": "Abriendo YouTube con tu búsqueda (extra web, requiere internet).",
                "action_executed": True,
                "action_type": "web_extra",
            }
        except Exception as e:
            return {
                "response": f"No pude abrir YouTube. ({type(e).__name__})",
                "action_executed": False,
                "action_type": "web_extra",
            }

    # Sin mención explícita de servicio web — respuesta local-first
    return {
        "response": (
            "Modo música detectado. Puedo abrir Spotify o YouTube si hay "
            "internet, o usar una carpeta local de música en una versión futura."
        ),
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