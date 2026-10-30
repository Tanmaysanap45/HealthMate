const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
const $ = (id) => document.getElementById(id);

let currentUser = null;
let profile = null;

// Realistic health boundaries for validation
const BOUNDS = {
  weight: { min: 30, max: 250, label: "Weight", unit: "kg" },
  steps: { min: 100, max: 100000, label: "Daily Steps", unit: "steps", whole: true },
  calories: { min: 500, max: 8000, label: "Calories", unit: "kcal", whole: true },
  water: { min: 0.2, max: 10.0, label: "Water", unit: "L" },
  sleep: { min: 1.0, max: 24.0, label: "Sleep", unit: "hours" }
};

$("logoutBtn").addEventListener("click", async () => {
  await sb.auth.signOut();
  window.location.href = "login.html";
});

function showMsg(text, ok = false) {
  const el = $("logMsg");
  el.textContent = text;
  el.style.color = ok ? "var(--accent)" : "#ff8a7a";
  el.className = ok ? "ok" : "";
}

async function loadLogs() {
  const { data: logs, error } = await sb
    .from("daily_logs")
    .select("*")
    .eq("user_id", currentUser.id)
    .order("log_date", { ascending: false });

  if (error) {
    $("historyList").innerHTML = `<li style="color: #ff8a7a;">Error: ${error.message}</li>`;
    return;
  }

  $("totalLogs").textContent = logs.length;

  const list = $("historyList");
  list.innerHTML = "";
  if (logs.length === 0) {
    list.innerHTML = `<li style="color: var(--muted);">No logs yet. Record today's metrics!</li>`;
    $("latestWt").textContent = profile ? `${Number(profile.weight_kg)} kg` : "-";
    $("wtDiff").textContent = "No entries yet";
  } else {
    logs.slice(0, 10).forEach((l) => {
      const li = document.createElement("li");
      li.className = "history-item";

      const left = document.createElement("div");
      left.innerHTML = `
        <div class="history-date">${l.log_date}</div>
        <div class="history-details">
          ${l.weight_kg != null ? `<span>${l.weight_kg} kg</span>` : ""}
          ${l.steps != null ? `<span>${Number(l.steps).toLocaleString()} steps</span>` : ""}
          ${l.calories_consumed != null ? `<span>${l.calories_consumed} kcal</span>` : ""}
          ${l.water_liters != null ? `<span>${l.water_liters} L</span>` : ""}
          ${l.sleep_hours != null ? `<span>🌙 ${l.sleep_hours}h sleep</span>` : ""}
        </div>
      `;

      const right = document.createElement("div");
      if (l.workout_completed) {
        right.innerHTML = `<span class="badge">Workout Done</span>`;
      }

      li.append(left, right);
      list.append(li);
    });

    const loggedWeights = logs.filter((l) => l.weight_kg != null);
    if (loggedWeights.length > 0) {
      const latest = Number(loggedWeights[0].weight_kg);
      $("latestWt").textContent = latest + " kg";
      if (profile && profile.weight_kg) {
        const diff = Math.round((latest - Number(profile.weight_kg)) * 10) / 10;
        const sign = diff > 0 ? "+" : "";
        $("wtDiff").textContent = `${sign}${diff} kg from start`;
      }
    }
  }
}

// Clear all logs handler
$("clearLogsBtn").addEventListener("click", async () => {
  const confirmed = confirm("Are you sure you want to delete all saved logs? This cannot be undone.");
  if (!confirmed) return;

  $("clearLogsBtn").disabled = true;
  $("clearLogsBtn").textContent = "Clearing...";

  const { error } = await sb
    .from("daily_logs")
    .delete()
    .eq("user_id", currentUser.id);

  $("clearLogsBtn").disabled = false;
  $("clearLogsBtn").textContent = "Clear All";

  if (error) {
    showMsg(`Failed to clear logs: ${error.message}`);
    return;
  }

  showMsg("All logs cleared successfully!", true);
  await loadLogs();
});

// Strict validation & submit handler
$("logForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const logDate = $("logDate").value;
  if (!logDate) {
    showMsg("Please select a date.");
    $("logDate").focus();
    return;
  }

  const inputs = [
    { el: $("logWeight"), rule: BOUNDS.weight },
    { el: $("logSteps"), rule: BOUNDS.steps },
    { el: $("logCalories"), rule: BOUNDS.calories },
    { el: $("logWater"), rule: BOUNDS.water },
    { el: $("logSleep"), rule: BOUNDS.sleep }
  ];

  // Reset border colors
  inputs.forEach((i) => (i.el.style.borderColor = "var(--line)"));

  let firstError = null;
  let errorMsg = "";

  // Check every field: must not be empty AND must be within valid bounds
  for (const item of inputs) {
    const raw = item.el.value.trim();
    const rule = item.rule;

    // 1. Mandatory check
    if (raw === "") {
      item.el.style.borderColor = "#ff8a7a";
      if (!firstError) {
        firstError = item.el;
        errorMsg = `Please enter ${rule.label}. All fields are required.`;
      }
      continue;
    }

    // 2. Numerical & boundary check
    const n = Number(raw);
    if (Number.isNaN(n) || n < rule.min || n > rule.max || (rule.whole && !Number.isInteger(n))) {
      item.el.style.borderColor = "#ff8a7a";
      if (!firstError) {
        firstError = item.el;
        if (rule.whole && !Number.isInteger(n)) {
          errorMsg = `${rule.label} must be a whole integer number.`;
        } else {
          errorMsg = `${rule.label} must be between ${rule.min} and ${rule.max} ${rule.unit}.`;
        }
      }
    }
  }

  // If any field is missing or invalid, stop submission
  if (firstError) {
    showMsg(errorMsg);
    firstError.focus();
    return;
  }

  // Build complete payload
  const payload = {
    user_id: currentUser.id,
    log_date: logDate,
    weight_kg: Number($("logWeight").value),
    steps: parseInt($("logSteps").value, 10),
    calories_consumed: Number($("logCalories").value),
    water_liters: Number($("logWater").value),
    sleep_hours: Number($("logSleep").value),
    workout_completed: $("logWorkout").checked,
    notes: $("logNotes").value.trim() || null
  };

  $("saveLogBtn").disabled = true;
  showMsg("Saving...", true);

  const { error } = await sb.from("daily_logs").upsert(payload, { onConflict: "user_id,log_date" });

  $("saveLogBtn").disabled = false;
  if (error) {
    showMsg(`Database error: ${error.message}`);
    return;
  }

  showMsg("All daily numbers logged successfully!", true);

  // Clear inputs after successful save
  $("logWeight").value = "";
  $("logSteps").value = "";
  $("logCalories").value = "";
  $("logWater").value = "";
  $("logSleep").value = "";
  $("logWorkout").checked = false;
  $("logNotes").value = "";

  await loadLogs();
});

// Clear red border when user types
["logWeight", "logSteps", "logCalories", "logWater", "logSleep"].forEach((id) => {
  $(id).addEventListener("input", () => {
    $(id).style.borderColor = "var(--line)";
    $("logMsg").textContent = "";
  });
});

(async function init() {
  const { data: sessionData } = await sb.auth.getSession();
  if (!sessionData.session) {
    window.location.href = "login.html";
    return;
  }
  currentUser = sessionData.session.user;

  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  $("logDate").value = `${year}-${month}-${day}`;

  const { data: p } = await sb
    .from("profiles")
    .select("weight_kg, target_weight_kg")
    .eq("id", currentUser.id)
    .maybeSingle();

  profile = p;
  if (p) {
    $("startWt").textContent = Number(p.weight_kg) + " kg";
    $("targetWt").textContent = Number(p.target_weight_kg) + " kg";
  }

  await loadLogs();
})();