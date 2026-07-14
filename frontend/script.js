// Change this if your backend runs on a different host/port
const API_BASE = "http://127.0.0.1:8000";

// --- State Variables ---
let queriesCount = 0;
const activityLog = [];

// --- DOM Elements ---
const navItems = document.querySelectorAll(".nav-item");
const viewSections = document.querySelectorAll(".view-section");
const pageTitle = document.getElementById("page-title");

const dashboardSection = document.getElementById("dashboard-section");
const chatSection = document.getElementById("chat-section");
const placeholderSection = document.getElementById("placeholder-section");
const placeholderTitle = document.getElementById("placeholder-title");
const placeholderDescription = document.getElementById("placeholder-description");

const startChatBtn = document.getElementById("start-chat-btn");
const queriesCountSpan = document.getElementById("queries-count");
const activityLogContainer = document.getElementById("activity-log");

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const suggestionsBox = document.getElementById("suggestions");

// --- View Switching / Routing Logic ---
function switchView(target) {
  // Update sidebar active class
  navItems.forEach(item => {
    if (item.getAttribute("data-target") === target) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Hide all sections
  viewSections.forEach(sec => sec.classList.remove("active"));

  // Show target section and update header title
  if (target === "dashboard") {
    dashboardSection.classList.add("active");
    pageTitle.textContent = "Dashboard";
  } else if (target === "chat") {
    chatSection.classList.add("active");
    pageTitle.textContent = "AI Chat";
  } else {
    // Show placeholder for other sections
    placeholderSection.classList.add("active");
    pageTitle.textContent = getSectionTitle(target);
    placeholderTitle.textContent = `${getSectionTitle(target)} Workspace`;
    placeholderDescription.textContent = `The ${getSectionTitle(target).toLowerCase()} catalog search and management console is currently read-only in this simplified model.`;
  }
}

function getSectionTitle(target) {
  switch (target) {
    case "documents": return "Documents";
    case "search": return "Advanced Search";
    case "projects": return "Projects Catalog";
    case "departments": return "Departments Directory";
    case "admin": return "Administration Console";
    default: return "Workspace";
  }
}

// Bind Navigation Clicks
navItems.forEach(item => {
  item.addEventListener("click", (e) => {
    e.preventDefault();
    const target = item.getAttribute("data-target");
    switchView(target);
  });
});

// Bind Start Chat Button on Dashboard
if (startChatBtn) {
  startChatBtn.addEventListener("click", () => {
    switchView("chat");
  });
}

// Bind Quick Links Buttons
document.getElementById("link-search").addEventListener("click", () => switchView("search"));
document.getElementById("link-docs").addEventListener("click", () => switchView("documents"));


// --- Activity Log & Stats Tracker ---
function logActivity(queryText) {
  // Update Query Count Stat
  queriesCount++;
  if (queriesCountSpan) {
    queriesCountSpan.textContent = queriesCount;
  }

  // Add Item to Activity Log
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  activityLog.unshift({ text: `Asked: "${queryText}"`, time: timestamp });

  renderActivityLog();
}

function renderActivityLog() {
  if (!activityLogContainer) return;

  if (activityLog.length === 0) {
    activityLogContainer.innerHTML = '<span class="no-activity">No activity logged yet.</span>';
    return;
  }

  activityLogContainer.innerHTML = activityLog
    .map(act => `
      <div class="activity-item">
        <span class="activity-text">${escapeHtml(act.text)}</span>
        <span class="activity-time">${act.time}</span>
      </div>
    `)
    .join('');
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}


// --- AI Chatbot Client logic ---
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
  
  // Track this activity
  logActivity(query);

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

// Load suggested questions as chips
async function loadSuggestions() {
  try {
    const res = await fetch(`${API_BASE}/faqs`);
    const data = await res.json();
    const sample = data.faqs.slice(0, 4); // Show first 4 as quick suggestions
    
    if (suggestionsBox) {
      suggestionsBox.innerHTML = '';
      sample.forEach((q) => {
        const chip = document.createElement("div");
        chip.classList.add("chip");
        chip.textContent = q;
        chip.addEventListener("click", () => sendQuery(q));
        suggestionsBox.appendChild(chip);
      });
    }
  } catch (err) {
    // Backend not reachable yet - silently retry or skip suggestions
  }
}

// Initial Loading
loadSuggestions();
renderActivityLog();
