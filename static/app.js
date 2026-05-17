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

// ──────────────────────────────────────────────
// Estado de grabación
// ──────────────────────────────────────────────
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

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
}

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
      li.innerHTML = `
        <span class="ts">${task.timestamp}</span>
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