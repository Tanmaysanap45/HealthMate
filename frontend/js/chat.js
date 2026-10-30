const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
const API_URL = "http://127.0.0.1:8000";
const $ = (id) => document.getElementById(id);

let sessionToken = null;

$("logoutBtn").addEventListener("click", async () => {
  await sb.auth.signOut();
  window.location.href = "login.html";
});

function appendMessage(sender, text) {
  const box = $("chatBox");
  const row = document.createElement("div");
  row.className = `msg-row ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  box.appendChild(row);
  box.scrollTop = box.scrollHeight;
}

$("chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("userInput");
  const msg = input.value.trim();
  if (!msg) return;

  // Append user question to UI
  appendMessage("user", msg);
  input.value = "";

  // Temporary placeholder while awaiting response
  const box = $("chatBox");
  const loadingRow = document.createElement("div");
  loadingRow.className = "msg-row bot";
  loadingRow.id = "coachLoading";
  loadingRow.innerHTML = `<div class="msg-bubble" style="color: var(--muted);">Coach is typing...</div>`;
  box.appendChild(loadingRow);
  box.scrollTop = box.scrollHeight;

  try {
    const res = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionToken}`
      },
      body: JSON.stringify({ message: msg })
    });

    const loader = $("coachLoading");
    if (loader) loader.remove();

    if (!res.ok) {
      appendMessage("bot", "Sorry, I had trouble processing that request. Please try again.");
      return;
    }

    const data = await res.json();
    appendMessage("bot", data.reply);
  } catch (err) {
    const loader = $("coachLoading");
    if (loader) loader.remove();
    appendMessage("bot", "Could not reach the coach server. Please ensure the backend is running on port 8000.");
  }
});

(async function init() {
  const { data: sessionData } = await sb.auth.getSession();
  if (!sessionData.session) {
    window.location.href = "login.html";
    return;
  }
  sessionToken = sessionData.session.access_token;
})();