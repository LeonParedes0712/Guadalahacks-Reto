"""
assistant_modes.py
──────────────────────────────────────────────
Sentinel AI — funciones Nivel 2.

Incluye:
- Modo enfoque / Pomodoro
- Modo presentación / demo
- Control multimedia básico
- Herramientas de archivos/carpetas
- Rutinas inteligentes

Diseñado para ser local-first y seguro: no borra archivos, no ejecuta
comandos arbitrarios dictados por voz y no depende de APIs externas.
"""

import os
import re
import platform
import subprocess
import webbrowser
import unicodedata
import urllib.parse
from datetime import datetime, timedelta


# ══════════════════════════════════════════════
# Estado interno simple para hackathon
# ══════════════════════════════════════════════
_focus_active = False
_focus_started_at: datetime | None = None
_pomodoro_active = False
_pomodoro_started_at: datetime | None = None
_pomodoro_minutes = 25
_break_active = False
_break_started_at: datetime | None = None
_break_minutes = 5

_presentation_active = False
_presentation_started_at: datetime | None = None

_last_saved_file: str | None = None
_last_media_status: str | None = None

PROJECT_GITHUB_URL = "https://github.com/LeonParedes0712/Guadalahacks-Reto"
LOCAL_APP_URL = "http://127.0.0.1:5000"


# ══════════════════════════════════════════════
# Utils
# ══════════════════════════════════════════════
def normalize(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[¿?¡!.,;:()\"'\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def contains_any(text: str, keywords: list[str]) -> bool:
    t = normalize(text)
    return any(normalize(k) in t for k in keywords)


def _system() -> str:
    return platform.system().lower()


def is_windows() -> bool:
    return _system() == "windows"


def is_macos() -> bool:
    return _system() == "darwin"


def is_linux() -> bool:
    return _system() == "linux"


def run_command(command, shell: bool = False) -> tuple[bool, str | None]:
    try:
        subprocess.Popen(command, shell=shell)
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def open_url(url: str) -> dict:
    try:
        webbrowser.open(url)
        return {"ok": True, "message": f"Abriendo {url}"}
    except Exception as e:
        return {"ok": False, "message": f"No pude abrir el navegador. ({type(e).__name__})"}


def _open_vscode() -> bool:
    if is_macos():
        ok, _ = run_command(["open", "-a", "Visual Studio Code"])
        if ok:
            return True
        ok, _ = run_command("code", shell=True)
        return ok
    ok, _ = run_command("code", shell=True)
    return ok


# ══════════════════════════════════════════════
# Web shortcuts / búsquedas
# ══════════════════════════════════════════════
WEB_SHORTCUTS = {
    "gmail": "https://mail.google.com/",
    "correo": "https://mail.google.com/",
    "drive": "https://drive.google.com/",
    "google drive": "https://drive.google.com/",
    "calendar": "https://calendar.google.com/",
    "calendario": "https://calendar.google.com/",
    "github": PROJECT_GITHUB_URL,
    "chatgpt": "https://chat.openai.com/",
    "claude": "https://claude.ai/new",
    "google": "https://www.google.com/",
    "youtube": "https://www.youtube.com/",
}


def open_web_shortcut(text: str) -> dict | None:
    t = normalize(text)
    # Orden: claves largas primero para evitar que "google drive" caiga en google.
    for key in sorted(WEB_SHORTCUTS.keys(), key=len, reverse=True):
        if key in t:
            url = WEB_SHORTCUTS[key]
            result = open_url(url)
            label = key.title()
            return {
                "response": f"Abriendo {label}.",
                "action_executed": result["ok"],
                "action_type": "web_extra",
            }
    return None


def _extract_search_query(text: str, engine: str) -> str:
    t = normalize(text)
    patterns = [
        rf"busca (.+) en {engine}",
        rf"buscar (.+) en {engine}",
        rf"buscame (.+) en {engine}",
        rf"investiga (.+) en {engine}",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            return m.group(1).strip()
    # Fallback: limpia comandos comunes.
    q = t
    q = re.sub(r"\b(busca|buscar|buscame|investiga|en google|en youtube|en github)\b", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q or text


def web_search(text: str) -> dict | None:
    t = normalize(text)
    if "busca" not in t and "buscar" not in t and "buscame" not in t and "investiga" not in t:
        return None

    if "youtube" in t or "you tube" in t:
        query = _extract_search_query(text, "youtube")
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        open_url(url)
        return {"response": f"Buscando '{query}' en YouTube.", "action_executed": True, "action_type": "web_search"}

    if "github" in t:
        query = _extract_search_query(text, "github")
        url = "https://github.com/search?q=" + urllib.parse.quote_plus(query)
        open_url(url)
        return {"response": f"Buscando '{query}' en GitHub.", "action_executed": True, "action_type": "web_search"}

    query = _extract_search_query(text, "google")
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    open_url(url)
    return {"response": f"Buscando '{query}' en Google.", "action_executed": True, "action_type": "web_search"}


# ══════════════════════════════════════════════
# Archivos y carpetas
# ══════════════════════════════════════════════
def _folder_path(name: str) -> str:
    home = os.path.expanduser("~")
    mapping = {
        "desktop": os.path.join(home, "Desktop"),
        "escritorio": os.path.join(home, "Desktop"),
        "downloads": os.path.join(home, "Downloads"),
        "descargas": os.path.join(home, "Downloads"),
        "documents": os.path.join(home, "Documents"),
        "documentos": os.path.join(home, "Documents"),
        "apuntes": os.path.join(os.getcwd(), "recordings", "classes"),
        "clases": os.path.join(os.getcwd(), "recordings", "classes"),
        "notas": os.path.join(os.getcwd(), "notes"),
    }
    return mapping.get(name, home)


def open_folder(path: str) -> tuple[bool, str | None]:
    try:
        os.makedirs(path, exist_ok=True)
        if is_windows():
            os.startfile(path)  # type: ignore[attr-defined]
        elif is_macos():
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def handle_files(text: str) -> dict:
    global _last_saved_file
    t = normalize(text)

    if contains_any(t, ["abre descargas", "abrir descargas", "carpeta descargas", "downloads"]):
        path = _folder_path("descargas")
        ok, err = open_folder(path)
        return _file_response(ok, "Abriendo Descargas.", path, err)

    if contains_any(t, ["abre documentos", "abrir documentos", "carpeta documentos", "documents"]):
        path = _folder_path("documentos")
        ok, err = open_folder(path)
        return _file_response(ok, "Abriendo Documentos.", path, err)

    if contains_any(t, ["abre escritorio", "abrir escritorio", "desktop"]):
        path = _folder_path("escritorio")
        ok, err = open_folder(path)
        return _file_response(ok, "Abriendo Escritorio.", path, err)

    if contains_any(t, ["abre carpeta de apuntes", "abre mis apuntes", "carpeta de clase", "apuntes"]):
        path = _folder_path("apuntes")
        ok, err = open_folder(path)
        return _file_response(ok, "Abriendo carpeta de apuntes.", path, err)

    if contains_any(t, ["crea una carpeta para la clase", "crear carpeta para la clase"]):
        path = _folder_path("apuntes")
        os.makedirs(path, exist_ok=True)
        return _file_response(True, "Carpeta de clase lista.", path, None)

    if contains_any(t, ["guarda esto como archivo", "guarda esta nota como archivo", "guardar nota como archivo"]):
        content = _clean_save_text(text)
        path = save_text_note(content)
        _last_saved_file = path
        return {
            "response": f"Nota guardada como archivo: {path}",
            "action_executed": True,
            "action_type": "file_tool",
            "saved_file_path": path,
        }

    return {
        "response": "Puedo abrir Descargas, Documentos, Escritorio, apuntes o guardar una nota como archivo.",
        "action_executed": False,
        "action_type": "file_tool",
    }


def _clean_save_text(text: str) -> str:
    cleaned = re.sub(r"(?i)guarda(r)?\s+(esto|esta nota)?\s*(como archivo)?", "", text).strip()
    return cleaned or text


def save_text_note(content: str) -> str:
    folder = os.path.join(os.getcwd(), "notes")
    os.makedirs(folder, exist_ok=True)
    filename = datetime.now().strftime("note_%Y-%m-%d_%H-%M-%S.txt")
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    return path


def _file_response(ok: bool, message: str, path: str, err: str | None) -> dict:
    if ok:
        return {
            "response": message,
            "action_executed": True,
            "action_type": "file_tool",
            "saved_file_path": path,
        }
    return {
        "response": f"No pude abrir esa carpeta. ({err})",
        "action_executed": False,
        "action_type": "file_tool",
        "saved_file_path": path,
    }


# ══════════════════════════════════════════════
# Modo enfoque / Pomodoro
# ══════════════════════════════════════════════
def handle_focus_mode(text: str) -> dict:
    global _focus_active, _focus_started_at, _pomodoro_active, _pomodoro_started_at
    global _break_active, _break_started_at

    t = normalize(text)

    if contains_any(t, ["termina modo enfoque", "desactiva modo enfoque", "pausa enfoque", "deten enfoque"]):
        _focus_active = False
        _pomodoro_active = False
        _break_active = False
        return _mode_response("Modo enfoque detenido.")

    if contains_any(t, ["termina pomodoro", "deten pomodoro", "pausa pomodoro"]):
        _pomodoro_active = False
        return _mode_response("Pomodoro detenido.")

    if contains_any(t, ["cuanto falta", "cuanto queda", "tiempo restante"]):
        remaining = get_focus_state().get("timer_remaining")
        msg = f"Quedan aproximadamente {remaining}." if remaining else "No hay un temporizador activo."
        return _mode_response(msg)

    opened = []

    if contains_any(t, ["modo programar", "programar", "codigo", "code"]):
        if _open_vscode():
            opened.append("VS Code")
        open_url(PROJECT_GITHUB_URL)
        opened.append("GitHub")

    elif contains_any(t, ["modo estudiar", "modo enfoque", "activa modo enfoque", "estudiar", "enfocarme"]):
        open_folder(_folder_path("documentos"))
        opened.append("Documentos")

    if contains_any(t, ["lofi", "musica", "con musica", "estudiar"]):
        open_url("https://www.youtube.com/results?search_query=lofi+focus+music")
        opened.append("música lofi")

    _focus_active = True
    _focus_started_at = datetime.now()

    if contains_any(t, ["pomodoro", "25 minutos", "veinticinco minutos"]):
        _pomodoro_active = True
        _pomodoro_started_at = datetime.now()
        _break_active = False
        msg = "Modo enfoque activado con Pomodoro de 25 minutos."
    elif contains_any(t, ["descanso", "cinco minutos", "5 minutos"]):
        _break_active = True
        _break_started_at = datetime.now()
        _pomodoro_active = False
        msg = "Descanso de 5 minutos iniciado."
    else:
        msg = "Modo enfoque activado."

    if opened:
        msg += " Abrí: " + ", ".join(opened) + "."

    return _mode_response(msg)


def _mode_response(message: str) -> dict:
    state = get_focus_state()
    return {
        "response": message,
        "action_executed": True,
        "action_type": "focus_mode",
        "focus_mode_active": state["active"],
        "focus_timer": state,
        "active_modes": get_active_modes(),
    }


def get_focus_state() -> dict:
    timer_type = None
    timer_remaining = None
    timer_done = False

    if _pomodoro_active and _pomodoro_started_at:
        timer_type = "pomodoro"
        end = _pomodoro_started_at + timedelta(minutes=_pomodoro_minutes)
        timer_remaining, timer_done = _format_remaining(end)
    elif _break_active and _break_started_at:
        timer_type = "break"
        end = _break_started_at + timedelta(minutes=_break_minutes)
        timer_remaining, timer_done = _format_remaining(end)

    return {
        "active": _focus_active,
        "started_at": _focus_started_at.strftime("%H:%M:%S") if _focus_started_at else None,
        "timer_type": timer_type,
        "timer_remaining": timer_remaining,
        "timer_done": timer_done,
    }


def _format_remaining(end: datetime) -> tuple[str, bool]:
    remaining = end - datetime.now()
    seconds = int(remaining.total_seconds())
    if seconds <= 0:
        return "00:00", True
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}", False


# ══════════════════════════════════════════════
# Modo presentación / demo
# ══════════════════════════════════════════════
def handle_presentation_mode(text: str) -> dict:
    global _presentation_active, _presentation_started_at

    t = normalize(text)
    if contains_any(t, ["termina modo presentacion", "termina modo demo", "desactiva modo demo"]):
        _presentation_active = False
        return {
            "response": "Modo presentación detenido.",
            "action_executed": True,
            "action_type": "presentation_mode",
            "presentation_mode_active": False,
            "presentation_checklist": get_presentation_checklist(),
            "active_modes": get_active_modes(),
        }

    _presentation_active = True
    _presentation_started_at = datetime.now()

    opened = []
    if open_url(LOCAL_APP_URL)["ok"]:
        opened.append("app local")
    if open_url(PROJECT_GITHUB_URL)["ok"]:
        opened.append("GitHub")
    if _open_vscode():
        opened.append("VS Code")

    msg = "Modo presentación activado. Checklist de demo listo."
    if opened:
        msg += " Abrí: " + ", ".join(opened) + "."

    return {
        "response": msg,
        "action_executed": True,
        "action_type": "presentation_mode",
        "presentation_mode_active": True,
        "presentation_checklist": get_presentation_checklist(),
        "active_modes": get_active_modes(),
    }


def get_presentation_checklist() -> list[str]:
    return [
        "Probar grabación de voz",
        "Probar abrir una app o página",
        "Probar modo clase",
        "Probar notas y tareas",
        "Probar emergencia",
        "Cerrar con privacidad/local-first",
    ]


def get_presentation_state() -> dict:
    return {
        "active": _presentation_active,
        "started_at": _presentation_started_at.strftime("%H:%M:%S") if _presentation_started_at else None,
        "checklist": get_presentation_checklist(),
    }


# ══════════════════════════════════════════════
# Multimedia
# ══════════════════════════════════════════════
def handle_media(text: str) -> dict:
    global _last_media_status
    t = normalize(text)

    if contains_any(t, ["sube volumen", "subir volumen", "volumen arriba"]):
        ok, msg = _media_key("volume_up")
    elif contains_any(t, ["baja volumen", "bajar volumen", "volumen abajo"]):
        ok, msg = _media_key("volume_down")
    elif contains_any(t, ["silencia", "mute", "silenciar"]):
        ok, msg = _media_key("mute")
    elif contains_any(t, ["pausa musica", "reproduce musica", "play pause", "play", "pause"]):
        ok, msg = _media_key("play_pause")
    elif contains_any(t, ["siguiente cancion", "siguiente pista", "next"]):
        ok, msg = _media_key("next")
    elif contains_any(t, ["cancion anterior", "pista anterior", "previous"]):
        ok, msg = _media_key("previous")
    else:
        ok, msg = False, "Acción multimedia no reconocida."

    _last_media_status = msg
    return {
        "response": msg,
        "action_executed": ok,
        "action_type": "media_control",
        "media_status": msg,
        "active_modes": get_active_modes(),
    }


def _media_key(action: str) -> tuple[bool, str]:
    try:
        if is_windows():
            key_map = {
                "mute": 173,
                "volume_down": 174,
                "volume_up": 175,
                "next": 176,
                "previous": 177,
                "play_pause": 179,
            }
            code = key_map[action]
            cmd = f'$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]{code})'
            subprocess.Popen(["powershell", "-NoProfile", "-Command", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, _media_success_message(action)

        if is_macos():
            # Volumen del sistema por AppleScript; multimedia vía Spotify si está abierto.
            if action == "volume_up":
                subprocess.Popen(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 10)"])
                return True, "Subiendo volumen."
            if action == "volume_down":
                subprocess.Popen(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 10)"])
                return True, "Bajando volumen."
            if action == "mute":
                subprocess.Popen(["osascript", "-e", "set volume with output muted"])
                return True, "Silenciando audio."
            spotify_action = {
                "play_pause": "playpause",
                "next": "next track",
                "previous": "previous track",
            }.get(action)
            if spotify_action:
                subprocess.Popen(["osascript", "-e", f'tell application "Spotify" to {spotify_action}'])
                return True, _media_success_message(action)

        if is_linux():
            linux_cmds = {
                "volume_up": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
                "volume_down": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"],
                "mute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
                "play_pause": ["playerctl", "play-pause"],
                "next": ["playerctl", "next"],
                "previous": ["playerctl", "previous"],
            }
            subprocess.Popen(linux_cmds[action])
            return True, _media_success_message(action)

    except Exception:
        pass

    return False, "Esta acción multimedia no está disponible en este sistema."


def _media_success_message(action: str) -> str:
    return {
        "volume_up": "Subiendo volumen.",
        "volume_down": "Bajando volumen.",
        "mute": "Silenciando audio.",
        "play_pause": "Pausando o reproduciendo música.",
        "next": "Saltando a la siguiente canción.",
        "previous": "Regresando a la canción anterior.",
    }.get(action, "Acción multimedia ejecutada.")


# ══════════════════════════════════════════════
# Rutinas inteligentes
# ══════════════════════════════════════════════
def handle_routine(text: str) -> dict:
    t = normalize(text)

    if contains_any(t, ["modo estudiar"]):
        return handle_focus_mode("activa modo enfoque estudiar pomodoro musica")

    if contains_any(t, ["modo programar"]):
        return handle_focus_mode("activa modo enfoque modo programar pomodoro")

    if contains_any(t, ["modo demo", "prepara demo"]):
        return handle_presentation_mode(text)

    if contains_any(t, ["modo descanso", "descanso de cinco minutos", "descanso 5 minutos"]):
        return handle_focus_mode("descanso de cinco minutos")

    return {
        "response": "Rutina detectada. Puedo activar modo estudiar, programar, demo o descanso.",
        "action_executed": False,
        "action_type": "routine",
        "active_modes": get_active_modes(),
    }


def get_active_modes() -> list[str]:
    modes = []
    if _focus_active:
        modes.append("focus")
    if _pomodoro_active:
        modes.append("pomodoro")
    if _break_active:
        modes.append("break")
    if _presentation_active:
        modes.append("presentation")
    return modes


def get_modes_state() -> dict:
    return {
        "focus": get_focus_state(),
        "presentation": get_presentation_state(),
        "last_saved_file": _last_saved_file,
        "last_media_status": _last_media_status,
        "active_modes": get_active_modes(),
    }
