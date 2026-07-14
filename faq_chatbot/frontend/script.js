// Change this if your backend runs on a different host/port
const API_BASE = "http://127.0.0.1:8000";

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const suggestionsBox = document.getElementById("suggestions");

function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  msg.textContent = text;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addConfidenceNote(confidence) {
  const note = document.createElement("div");
  note.classList.add("message", "confidence");
  note.textContent = `Match confidence: ${(confidence * 100).toFixed(0)}%`;
  chatWindow.appendChild(note);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendQuery(query) {
  addMessage(query, "user");
  userInput.value = "";

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    addMessage(data.answer, "bot");
    addConfidenceNote(data.confidence);
  } catch (err) {
    addMessage("Could not reach the server. Make sure the backend is running on " + API_BASE, "bot");
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = userInput.value.trim();
  if (query) sendQuery(query);
});

// Load a few suggested questions as clickable chips
async function loadSuggestions() {
  try {
    const res = await fetch(`${API_BASE}/faqs`);
    const data = await res.json();
    const sample = data.faqs.slice(0, 4); // show first 4 as quick suggestions
    sample.forEach((q) => {
      const chip = document.createElement("div");
      chip.classList.add("chip");
      chip.textContent = q;
      chip.addEventListener("click", () => sendQuery(q));
      suggestionsBox.appendChild(chip);
    });
  } catch (err) {
    // Backend not reachable yet - silently skip suggestions
  }
}

loadSuggestions();
