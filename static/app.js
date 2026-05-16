let mediaRecorder;
let audioChunks = [];
let isRecording = false;

const recordBtn = document.getElementById("recordBtn");
const statusText = document.getElementById("status");
const transcriptText = document.getElementById("transcriptText");
const intentText = document.getElementById("intentText");
const responseText = document.getElementById("responseText");
const confidenceBar = document.getElementById("confidenceBar");
const confidenceText = document.getElementById("confidenceText");
const emergencyText = document.getElementById("emergencyText");
const historyList = document.getElementById("historyList");

function setStatus(status) {
  statusText.textContent = status;
}

recordBtn.addEventListener("click", async () => {
  if (!isRecording) {
    await startRecording();
  } else {
    stopRecording();
  }
});

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = event => {
    audioChunks.push(event.data);
  };

  mediaRecorder.onstop = async () => {
    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    await sendAudio(audioBlob);
  };

  mediaRecorder.start();
  isRecording = true;
  recordBtn.textContent = "Detener grabación";
  setStatus("LISTENING");
}

function stopRecording() {
  mediaRecorder.stop();
  isRecording = false;
  recordBtn.textContent = "Grabar audio";
  setStatus("PROCESSING");
}

async function sendAudio(audioBlob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "audio.wav");

  try {
    const res = await fetch("/transcribe", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    const transcript = data.text || "No se detectó texto.";

    transcriptText.textContent = transcript;

    await sendIntent(transcript);
  } catch (error) {
    console.error(error);
    setStatus("ERROR");
    responseText.textContent = "Error al transcribir el audio.";
  }
}

async function sendIntent(transcript) {
  setStatus("RESPONDING");

  try {
    const res = await fetch("/intent", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text: transcript })
    });

    const data = await res.json();

    updateDashboard(data);
    await loadHistory();

    setStatus("STANDBY");
  } catch (error) {
    console.error(error);
    setStatus("ERROR");
    responseText.textContent = "Error al detectar la intención.";
  }
}

function updateDashboard(data) {
  const intent = data.intent || "UNKNOWN";
  const confidence = data.confidence || 0;
  const response = data.response || "Sin respuesta.";

  intentText.textContent = intent;
  responseText.textContent = response;

  const percentage = Math.round(confidence * 100);
  confidenceBar.style.width = `${percentage}%`;
  confidenceText.textContent = `Confidence: ${percentage}%`;

  if (intent === "EMERGENCY") {
    emergencyText.textContent = "Emergencia detectada. Activando protocolo visual.";
    document.querySelector(".emergency-card").classList.add("emergency-active");
  } else {
    emergencyText.textContent = "Sin emergencia detectada.";
    document.querySelector(".emergency-card").classList.remove("emergency-active");
  }
}

async function loadHistory() {
  try {
    const res = await fetch("/history");
    const data = await res.json();

    historyList.innerHTML = "";

    const items = data.history || [];

    items.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item.intent || "UNKNOWN"}: ${item.text || "Sin texto"}`;
      historyList.appendChild(li);
    });
  } catch (error) {
    console.error(error);
  }
}
