"""
class_mode.py
──────────────────────────────────────────────
Sentinel AI — Modo Clase (Class Mode)

Maneja:
- Iniciar / detener sesión de clase
- Guardar fragmentos transcritos con timestamp
- Generar resumen simple (local, sin APIs)
- Detectar tareas y notas automáticamente
- Persistir apuntes en recordings/classes/
"""

import os
import re
import unicodedata
from datetime import datetime
from collections import Counter


# ──────────────────────────────────────────────
# Estado interno
# ──────────────────────────────────────────────
_class_active = False
_class_start_time: datetime | None = None
_class_file_path: str | None = None
_class_fragments: list[dict] = []   # {timestamp, text}
_class_file_handle = None


# ──────────────────────────────────────────────
# Frases que indican tarea detectada en clase
# ──────────────────────────────────────────────
_TASK_PHRASES = [
    "la tarea es",
    "para la proxima clase",
    "para la siguiente clase",
    "entregar",
    "fecha limite",
    "fecha de entrega",
    "examen",
    "proyecto",
    "investigacion",
    "trabajo",
    "quizz",
    "quiz",
    "evaluacion",
    "entrega",
    "para manana",
    "para el viernes",
    "para el lunes",
    "para el martes",
    "para el miercoles",
    "para el jueves",
]

# ──────────────────────────────────────────────
# Frases que indican definición o explicación
# ──────────────────────────────────────────────
_NOTE_PHRASES = [
    "esto significa",
    "se define como",
    "es importante porque",
    "en resumen",
    "la definicion es",
    "el concepto es",
    "es decir",
    "o sea que",
    "significa que",
    "se refiere a",
    "es un tipo de",
    "se clasifica como",
    "ejemplo de esto",
    "como ejemplo",
    "por ejemplo",
]


def _normalize(text: str) -> str:
    t = text.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t


def _contains_any(text: str, phrases: list) -> bool:
    t = _normalize(text)
    return any(_normalize(p) in t for p in phrases)


# ──────────────────────────────────────────────
# Asegurar carpeta de clases
# ──────────────────────────────────────────────
def _ensure_dir():
    path = os.path.join("recordings", "classes")
    os.makedirs(path, exist_ok=True)
    return path


# ──────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────
def start_class_session() -> dict:
    global _class_active, _class_start_time, _class_file_path, _class_fragments, _class_file_handle

    if _class_active:
        return {
            "ok": True,
            "already_active": True,
            "file_path": _class_file_path,
            "message": "El modo clase ya está activo.",
        }

    _class_active = True
    _class_start_time = datetime.now()
    _class_fragments = []

    folder = _ensure_dir()
    filename = _class_start_time.strftime("class_%Y-%m-%d_%H-%M.txt")
    _class_file_path = os.path.join(folder, filename)

    try:
        _class_file_handle = open(_class_file_path, "w", encoding="utf-8")
        _class_file_handle.write(f"=== Clase iniciada: {_class_start_time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        _class_file_handle.flush()
    except Exception as e:
        _class_active = False
        return {"ok": False, "error": str(e)}

    return {
        "ok": True,
        "already_active": False,
        "file_path": _class_file_path,
        "message": "Modo clase activado. Empezaré a grabar y transcribir tus apuntes.",
    }


def stop_class_session() -> dict:
    global _class_active, _class_file_handle

    if not _class_active:
        return {"ok": False, "message": "El modo clase no está activo."}

    _class_active = False
    file_path = _class_file_path

    if _class_file_handle:
        try:
            _class_file_handle.write(f"\n=== Clase terminada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            _class_file_handle.close()
        except Exception:
            pass
        _class_file_handle = None

    return {
        "ok": True,
        "file_path": file_path,
        "fragments_count": len(_class_fragments),
        "message": f"Modo clase desactivado. Apuntes guardados en: {file_path}",
    }


def add_class_transcript(text: str) -> dict:
    """
    Agrega un fragmento transcrito a la sesión de clase activa.
    Retorna tareas y notas detectadas automáticamente.
    """
    if not _class_active:
        return {"ok": False}

    ts = datetime.now().strftime("%H:%M:%S")
    fragment = {"timestamp": ts, "text": text}
    _class_fragments.append(fragment)

    # Escribir al archivo
    if _class_file_handle:
        try:
            _class_file_handle.write(f"[{ts}] {text}\n")
            _class_file_handle.flush()
        except Exception:
            pass

    detected_task = None
    detected_note = None

    if _contains_any(text, _TASK_PHRASES):
        detected_task = {"timestamp": ts, "text": text, "source": "class_mode"}

    if _contains_any(text, _NOTE_PHRASES):
        detected_note = {"timestamp": ts, "text": text, "source": "class_mode"}

    return {
        "ok": True,
        "timestamp": ts,
        "detected_task": detected_task,
        "detected_note": detected_note,
    }


def get_class_summary() -> str:
    """
    Genera un resumen simple local sin APIs externas.
    Estrategia: palabras clave repetidas + frases relevantes.
    """
    if not _class_fragments:
        return "No hay apuntes de clase para resumir."

    all_text = " ".join(f["text"] for f in _class_fragments)

    # Palabras clave: las más repetidas, filtrando stopwords básicas
    stopwords = {
        "de", "la", "el", "en", "que", "y", "a", "los", "las", "un", "una",
        "es", "se", "del", "con", "por", "para", "su", "lo", "al", "como",
        "son", "pero", "o", "fue", "si", "mas", "ya", "este", "esta", "esto",
        "le", "me", "te", "nos", "les", "nos", "hay", "muy", "tan", "bien",
        "todo", "todas", "todos", "aqui", "ahi", "puede", "tiene", "tienen",
        "ser", "estar", "era", "han", "cuando", "donde", "cual", "quien",
    }

    words = re.findall(r"\b[a-záéíóúüñ]{4,}\b", _normalize(all_text))
    freq = Counter(w for w in words if w not in stopwords)
    top_keywords = [w for w, _ in freq.most_common(8)]

    # Frases relevantes: las que contienen palabras clave o frases de nota
    sentences = re.split(r"[.!?]", all_text)
    relevant = []

    for s in sentences:
        s = s.strip()
        if len(s) < 15:
            continue
        sn = _normalize(s)
        if any(kw in sn for kw in top_keywords[:5]) or _contains_any(s, _NOTE_PHRASES):
            relevant.append(s)

    relevant = relevant[:5]  # máximo 5 frases en el resumen

    summary_parts = []
    if top_keywords:
        summary_parts.append(f"Temas principales: {', '.join(top_keywords)}.")
    if relevant:
        summary_parts.append("Puntos clave: " + " | ".join(relevant))
    else:
        summary_parts.append("No se identificaron puntos clave suficientes. Revisa los apuntes completos.")

    return " ".join(summary_parts)


def detect_class_tasks(text: str) -> bool:
    return _contains_any(text, _TASK_PHRASES)


def detect_class_notes(text: str) -> bool:
    return _contains_any(text, _NOTE_PHRASES)


def get_class_state() -> dict:
    duration = None
    if _class_active and _class_start_time:
        elapsed = datetime.now() - _class_start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        duration = f"{minutes:02d}:{seconds:02d}"

    return {
        "active": _class_active,
        "file_path": _class_file_path,
        "fragments": _class_fragments[-5:],   # últimos 5 para UI
        "fragments_total": len(_class_fragments),
        "duration": duration,
        "start_time": _class_start_time.strftime("%H:%M:%S") if _class_start_time else None,
    }
