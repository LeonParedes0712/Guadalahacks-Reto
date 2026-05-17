// ──────────────────────────────────────────────
// Referencias DOM
// ──────────────────────────────────────────────
const recordBtn       = document.getElementById("recordBtn");
const statusText      = document.getElementById("status");
const transcriptText  = document.getElementById("transcriptText");
const intentText      = document.getElementById("intentText");
const responseText    = document.getElementById("responseText");
const confidenceBar   = document.getElementById("confidenceBar");
const confidenceText  = document.getElementById("confidenceText");
const emergencyText   = document.getElementById("emergencyText");
const emergencyCard   = document.getElementById("emergencyCard");
const historyList     = document.getElementById("historyList");
const notesList       = document.getElementById("notesList");
const tasksList       = document.getElementById("tasksList");
const wakeWordBadge   = document.getElementById("wakeWordBadge");
const ttsToggle       = document.getElementById("ttsToggle");

// Modo clase
const classCard         = document.getElementById("classCard");
const classStatusBadge  = document.getElementById("classStatusBadge");
const classMeta         = document.getElementById("classMeta");
const classDuration     = document.getElementById("classDuration");
const classFragCount    = document.getElementById("classFragCount");
const classSummaryBox   = document.getElementById("classSummaryBox");
const classSummaryText  = document.getElementById("classSummaryText");
const classFragments    = document.getElementById("classFragments");
const classFragList     = document.getElementById("classFragList");
const classFilePath     = document.getElementById("classFilePath");
const classDotNav       = document.getElementById("classDotNav");

// Modos nivel 2
const focusCard               = document.getElementById("focusCard");
const focusStatusBadge        = document.getElementById("focusStatusBadge");
const focusTimerText          = document.getElementById("focusTimerText");
const focusStateText          = document.getElementById("focusStateText");
const focusDotNav             = document.getElementById("focusDotNav");
const presentationCard        = document.getElementById("presentationCard");
const presentationStatusBadge = document.getElementById("presentationStatusBadge");
const presentationChecklist   = document.getElementById("presentationChecklist");
const presentationDotNav      = document.getElementById("presentationDotNav");
const filesCard               = document.getElementById("filesCard");
const savedFilePath           = document.getElementById("savedFilePath");
const mediaCard               = document.getElementById("mediaCard");
const mediaStatusText         = document.getElementById("mediaStatusText");

// ──────────────────────────────────────────────
// Estado de grabación
// ──────────────────────────────────────────────
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let classDurationInterval = null;

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────
function setStatus(s) {
  statusText.textContent = s;
}

const INTENT_COLORS = {
  emergency:    "#ef4444",
  music:        "#a855f7",
  productivity: "#3b82f6",
  emotional:    "#ec4899",
  system:       "#64748b",
  time:         "#0ea5e9",
  fun:          "#f59e0b",
  notes:        "#10b981",
  general:      "#6b7280",
  class_mode:   "#8b5cf6",
  focus_mode:   "#2563eb",
  presentation_mode: "#0f766e",
  media:        "#f97316",
  files:        "#0891b2",
  routine:      "#7c3aed",
};

function speak(text) {
  if (!ttsToggle.checked) return;
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "es-MX";
  utter.rate = 1.05;
  utter.pitch = 1;
  window.speechSynthesis.speak(utter);
}

// ──────────────────────────────────────────────
// Wake word
// ──────────────────────────────────────────────
const WAKE_WORD = "sentinel";

function checkWakeWord(transcript) {
  const lower = transcript.toLowerCase().trim();
  const detected = lower.startsWith(WAKE_WORD);

  if (detected) {
    wakeWordBadge.textContent  = "WAKE WORD: DETECTED ✓";
    wakeWordBadge.className    = "wake-badge wake-active";
  } else {
    wakeWordBadge.textContent  = "WAKE WORD: NOT DETECTED";
    wakeWordBadge.className    = "wake-badge wake-inactive";
  }
  return detected;
}

// ──────────────────────────────────────────────
// Grabación
// ──────────────────────────────────────────────
recordBtn.addEventListener("click", async () => {
  if (!isRecording) {
    await startRecording();
  } else {
    stopRecording();
  }
});

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder  = new MediaRecorder(stream);
  audioChunks    = [];

  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.onstop = async () => {
    const blob = new Blob(audioChunks, { type: "audio/wav" });
    await sendAudio(blob);
  };

  mediaRecorder.start();
  isRecording = true;
  recordBtn.textContent = "⏹ Detener grabación";
  setStatus("🔴 LISTENING");
}

function stopRecording() {
  mediaRecorder.stop();
  isRecording = false;
  recordBtn.textContent = "🎙 Grabar audio";
  setStatus("⏳ PROCESSING");
}

// ──────────────────────────────────────────────
// Envío y procesamiento
// ──────────────────────────────────────────────
async function sendAudio(blob) {
  const formData = new FormData();
  formData.append("audio", blob, "audio.wav");

  try {
    const res  = await fetch("/transcribe", { method: "POST", body: formData });
    const data = await res.json();
    const transcript = data.text || "No se detectó texto.";

    transcriptText.textContent = transcript;

    // Wake word check (visual only — siempre procesamos el intent)
    checkWakeWord(transcript);

    await sendIntent(transcript);
  } catch (err) {
    console.error(err);
    setStatus("ERROR");
    responseText.textContent = "Error al transcribir el audio.";
  }
}

async function sendIntent(transcript) {
  setStatus("🤖 RESPONDING");

  try {
    const res  = await fetch("/intent", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text: transcript }),
    });
    const data = await res.json();

    updateDashboard(data);
    speak(data.response || "");

    // Actualizar paneles de modos si hay info relevante
    if (data.class_state) {
      updateClassPanel(data.class_state, data.class_summary, data.class_file_path);
    }
    updateLevel2Panels(data);

    await Promise.all([loadHistory(), loadNotes(), loadTasks()]);
    setStatus("STANDBY");
  } catch (err) {
    console.error(err);
    setStatus("ERROR");
    responseText.textContent = "Error al detectar la intención.";
  }
}

// ──────────────────────────────────────────────
// UI update
// ──────────────────────────────────────────────
function updateDashboard(data) {
  const intent     = data.intent     || "general";
  const confidence = data.confidence || 0;
  const response   = data.response   || "Sin respuesta.";

  // Intent pill
  intentText.textContent = intent.toUpperCase();
  intentText.style.background = INTENT_COLORS[intent] || "#6b7280";

  // Response
  responseText.textContent = response;

  // Confidence bar
  const pct = Math.round(confidence * 100);
  confidenceBar.style.width = `${pct}%`;
  confidenceBar.style.background = INTENT_COLORS[intent] || "#22c55e";
  confidenceText.textContent = `Confidence: ${pct}%`;

  // Emergencia
  if (intent === "emergency") {
    emergencyText.textContent = "🚨 Emergencia detectada. Activando protocolo visual.";
    emergencyCard.classList.add("emergency-active");
  } else {
    emergencyText.textContent = "Sin emergencia detectada.";
    emergencyCard.classList.remove("emergency-active");
  }

  // Mostrar cards principales después de una interacción
  document.body.classList.remove("mode-idle");
  recorderPanel?.classList.remove("hidden");

  showCard("response");
  showCard("transcript");
  showCard("intent");
  showCard("history");

  if (intent === "emergency") {
    showCard("emergency");
  }

  if (intent === "notes") {
    showCard("notes");
  }

  if (intent === "productivity") {
    showCard("tasks");
  }

  // Modo clase: mostrar card si se activó o está activo
  if (intent === "class_mode" || data.class_mode_active) {
    showCard("class");
  }

  // Modos nivel 2
  if (intent === "focus_mode" || data.focus_mode_active) {
    showCard("focus");
  }

  if (intent === "presentation_mode" || data.presentation_mode_active) {
    showCard("presentation");
  }

  if (intent === "media" || data.media_status) {
    showCard("media");
  }

  if (intent === "files" || data.saved_file_path) {
    showCard("files");
  }

  updateLevel2Panels(data);
}

// ──────────────────────────────────────────────
// Modo Clase — actualizar panel
// ──────────────────────────────────────────────
function updateClassPanel(state, summary, filePath) {
  if (!state) return;

  const active = state.active;

  // Badge de estado
  classStatusBadge.textContent = active ? "ACTIVO" : "INACTIVO";
  classStatusBadge.className = "class-status-badge " + (active ? "class-badge-active" : "class-badge-inactive");

  // Punto de actividad en sidebar nav
  if (active) {
    classDotNav.classList.remove("hidden");
  } else {
    classDotNav.classList.add("hidden");
  }

  // Resaltar nav item de clase si está activo
  const classNavItem = document.querySelector('[data-view="class"]');
  if (classNavItem) {
    classNavItem.classList.toggle("class-nav-active", active);
  }

  // Metadatos
  if (active) {
    classMeta.style.display = "flex";
    classDuration.textContent = state.duration || "00:00";
    classFragCount.textContent = state.fragments_total || 0;
  } else {
    classMeta.style.display = "none";
  }

  // Fragmentos recientes
  const frags = state.fragments || [];
  if (frags.length > 0) {
    classFragments.classList.remove("hidden");
    classFragList.innerHTML = "";
    frags.slice().reverse().forEach(f => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="ts">${f.timestamp}</span> <span class="item-text">${f.text}</span>`;
      classFragList.appendChild(li);
    });
  } else {
    classFragments.classList.add("hidden");
  }

  // Resumen
  if (summary) {
    classSummaryBox.classList.remove("hidden");
    classSummaryText.textContent = summary;
  } else {
    classSummaryBox.classList.add("hidden");
  }

  // Ruta del archivo
  if (filePath) {
    classFilePath.classList.remove("hidden");
    classFilePath.textContent = "📁 " + filePath;
  } else if (state.file_path) {
    classFilePath.classList.remove("hidden");
    classFilePath.textContent = "📁 " + state.file_path;
  } else {
    classFilePath.classList.add("hidden");
  }
}

// ──────────────────────────────────────────────
// Modos Nivel 2 — actualizar paneles
// ──────────────────────────────────────────────
function updateLevel2Panels(data = {}) {
  // Focus / Pomodoro
  const focusState = data.focus_timer || data.modes_state?.focus || null;
  const focusActive = data.focus_mode_active || focusState?.active || false;

  if (focusStatusBadge) {
    focusStatusBadge.textContent = focusActive ? "ACTIVO" : "INACTIVO";
    focusStatusBadge.className = "class-status-badge " + (focusActive ? "class-badge-active" : "class-badge-inactive");
  }

  if (focusDotNav) focusDotNav.classList.toggle("hidden", !focusActive);

  if (focusState) {
    if (focusTimerText) {
      if (focusState.timer_type) {
        const label = focusState.timer_type === "break" ? "Descanso" : "Pomodoro";
        focusTimerText.textContent = `${label}: ${focusState.timer_remaining || "00:00"}`;
      } else {
        focusTimerText.textContent = focusActive ? "Sin temporizador activo" : "Inactivo";
      }
    }
    if (focusStateText) {
      focusStateText.textContent = focusActive ? "Enfoque activo" : "Listo";
    }
  }

  // Presentación / demo
  const presentationActive = data.presentation_mode_active || data.modes_state?.presentation?.active || false;
  if (presentationStatusBadge) {
    presentationStatusBadge.textContent = presentationActive ? "ACTIVO" : "INACTIVO";
    presentationStatusBadge.className = "class-status-badge " + (presentationActive ? "class-badge-active" : "class-badge-inactive");
  }
  if (presentationDotNav) presentationDotNav.classList.toggle("hidden", !presentationActive);

  const checklist = data.presentation_checklist || data.modes_state?.presentation?.checklist || [];
  if (presentationChecklist && checklist.length > 0) {
    presentationChecklist.innerHTML = "";
    checklist.forEach(item => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="done-label">✓</span><span class="item-text">${item}</span>`;
      presentationChecklist.appendChild(li);
    });
  }

  // Multimedia
  if (data.media_status && mediaStatusText) {
    mediaStatusText.textContent = data.media_status;
  }

  // Archivos
  if (data.saved_file_path && savedFilePath) {
    savedFilePath.classList.remove("hidden");
    savedFilePath.textContent = "📁 " + data.saved_file_path;
  }
}

async function pollModesState() {
  try {
    const res = await fetch("/modes/state");
    const state = await res.json();
    updateLevel2Panels({ modes_state: state });
  } catch (_) {}
}

setInterval(pollModesState, 10000);

// Polling del estado de clase (cada 10 seg si está activo)
async function pollClassState() {
  try {
    const res = await fetch("/class/state");
    const state = await res.json();
    if (state.active) {
      updateClassPanel(state, null, null);
    }
  } catch (_) {}
}

setInterval(pollClassState, 10000);

// ──────────────────────────────────────────────
// Historial
// ──────────────────────────────────────────────
async function loadHistory() {
  try {
    const res  = await fetch("/history");
    const data = await res.json();
    historyList.innerHTML = "";

    (data.history || []).forEach(item => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span class="ts">${item.timestamp}</span>
        <span class="pill" style="background:${INTENT_COLORS[item.intent] || '#6b7280'}">${item.intent}</span>
        <span class="item-text">${item.text}</span>`;
      historyList.appendChild(li);
    });
  } catch (err) { console.error(err); }
}

// ──────────────────────────────────────────────
// Notas
// ──────────────────────────────────────────────
async function loadNotes() {
  try {
    const res  = await fetch("/notes");
    const data = await res.json();
    notesList.innerHTML = "";

    if (!data.notes || data.notes.length === 0) {
      notesList.innerHTML = "<li class='empty'>Sin notas todavía.</li>";
      return;
    }

    data.notes.forEach(note => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="ts">${note.timestamp}</span> <span class="item-text">${note.text}</span>`;
      notesList.appendChild(li);
    });
  } catch (err) { console.error(err); }
}

// ──────────────────────────────────────────────
// Tareas
// ──────────────────────────────────────────────
async function loadTasks() {
  try {
    const res  = await fetch("/tasks");
    const data = await res.json();
    tasksList.innerHTML = "";

    if (!data.tasks || data.tasks.length === 0) {
      tasksList.innerHTML = "<li class='empty'>Sin tareas todavía.</li>";
      return;
    }

    data.tasks.forEach((task, i) => {
      const li = document.createElement("li");
      li.className = task.done ? "task-done" : "";
      const sourceTag = task.source === "class_mode"
        ? `<span class="class-task-tag">🎓 clase</span>`
        : "";
      li.innerHTML = `
        <span class="ts">${task.timestamp}</span>
        ${sourceTag}
        <span class="item-text">${task.text}</span>
        ${!task.done
          ? `<button class="done-btn" onclick="markDone(${i})">✓</button>`
          : `<span class="done-label">Hecho</span>`}`;
      tasksList.appendChild(li);
    });
  } catch (err) { console.error(err); }
}

async function markDone(index) {
  await fetch(`/tasks/${index}/done`, { method: "POST" });
  await loadTasks();
}

// ──────────────────────────────────────────────
// Carga inicial
// ──────────────────────────────────────────────
loadHistory();
loadNotes();
loadTasks();

// Cargar estado inicial de clase
fetch("/class/state").then(r => r.json()).then(state => {
  if (state.active) {
    updateClassPanel(state, null, null);
    showCard("class");
  }
}).catch(() => {});

fetch("/modes/state").then(r => r.json()).then(state => {
  updateLevel2Panels({ modes_state: state });
  if (state.focus?.active) showCard("focus");
  if (state.presentation?.active) showCard("presentation");
}).catch(() => {});

// ──────────────────────────────────────────────
// Sidebar / vistas dinámicas
// ──────────────────────────────────────────────
const navItems = document.querySelectorAll(".nav-item");
const recorderPanel = document.querySelector(".recorder-panel");
const cardsArea = document.querySelector(".cards-area");
const allCards = document.querySelectorAll("[data-card]");
const sidebarToggle = document.getElementById("sidebarToggle");
const sidebar = document.getElementById("sidebar");

function hideAllCards() {
  allCards.forEach(card => {
    card.classList.add("hidden");
    card.classList.remove("view-active");
  });
}

function showCard(cardName) {
  const card = document.querySelector(`[data-card="${cardName}"]`);
  if (card) {
    card.classList.remove("hidden");
    card.classList.add("view-active");
  }
}

function setActiveNav(view) {
  navItems.forEach(item => {
    item.classList.toggle("nav-active", item.dataset.view === view);
  });
}

function showView(view) {
  setActiveNav(view);

  // Inicio / nuevo comando
  if (view === "home") {
    document.body.classList.add("mode-idle");
    recorderPanel?.classList.remove("hidden");
    hideAllCards();
    return;
  }

  document.body.classList.remove("mode-idle");
  recorderPanel?.classList.add("hidden");
  hideAllCards();

  if (view === "history") {
    showCard("history");
    loadHistory();
  }

  if (view === "notes") {
    showCard("notes");
    loadNotes();
  }

  if (view === "tasks") {
    showCard("tasks");
    loadTasks();
  }

  if (view === "emergency") {
    showCard("emergency");
  }

  if (view === "class") {
    showCard("class");
    // Actualizar estado al navegar
    fetch("/class/state").then(r => r.json()).then(state => {
      updateClassPanel(state, null, null);
    }).catch(() => {});
  }

  if (view === "focus") {
    showCard("focus");
    pollModesState();
  }

  if (view === "presentation") {
    showCard("presentation");
    pollModesState();
  }

  if (view === "files") {
    showCard("files");
  }

  if (view === "media") {
    showCard("media");
  }
}

navItems.forEach(item => {
  item.addEventListener("click", () => {
    const view = item.dataset.view;
    showView(view);

    if (sidebar) {
      sidebar.classList.remove("sidebar-open");
    }
  });
});

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("sidebar-open");
  });
}

// Estado inicial
hideAllCards();
showView("home");