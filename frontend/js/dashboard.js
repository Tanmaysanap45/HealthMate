const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
const $ = (id) => document.getElementById(id);
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function bmiCategory(bmi) {
  if (bmi < 18.5) return "Underweight";
  if (bmi < 25) return "Healthy range";
  if (bmi < 30) return "Overweight";
  return "Obesity range";
}

function countUp(el, target, decimals = 0, suffix = "") {
  if (!el) return;
  const fmt = (v) =>
    v.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }) + suffix;

  if (reduce) {
    el.textContent = fmt(target);
    return;
  }
  const start = performance.now();
  const duration = 1200;
  function tick(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = fmt(target * eased);
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

$("logoutBtn").addEventListener("click", async () => {
  await sb.auth.signOut();
  window.location.href = "login.html";
});

// Render dynamic charts and habit cards using real Supabase logs
async function loadTrackedProgress(userId, targetWeight, dailyCaloriesTarget) {
  // Fetch up to the last 7 logged days in ascending order for charting
  const { data: logs, error } = await sb
    .from("daily_logs")
    .select("log_date, weight_kg, steps, calories_consumed, water_liters, sleep_hours")
    .eq("user_id", userId)
    .order("log_date", { ascending: true })
    .limit(7);

  if (error) {
    console.error("Failed to load tracking data:", error);
    return;
  }

  // 1. Prepare data for the graphs
  let labels = [];
  let weightData = [];
  let calorieData = [];

  if (logs && logs.length > 0) {
    labels = logs.map(l => (l.log_date ? l.log_date.slice(5) : "Day"));
    weightData = logs.map(l => (l.weight_kg != null ? Number(l.weight_kg) : null));
    calorieData = logs.map(l => (l.calories_consumed != null ? Number(l.calories_consumed) : 0));
  } else {
    labels = ["No Data"];
    weightData = [null];
    calorieData = [0];
  }

  // Render Line Chart: Weight Trajectory
  const ctxWeight = document.getElementById("weightProgressChart").getContext("2d");
  new Chart(ctxWeight, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Current Weight (kg)",
          data: weightData,
          borderColor: "#d4f938",
          backgroundColor: "rgba(212, 249, 56, 0.08)",
          borderWidth: 2.5,
          tension: 0.25,
          fill: true,
          pointBackgroundColor: "#d4f938",
          pointRadius: 4,
          pointHoverRadius: 6,
          spanGaps: true
        },
        {
          label: "Target Weight (kg)",
          data: Array(labels.length).fill(targetWeight || 60),
          borderColor: "#8c8d84",
          borderWidth: 1.5,
          borderDash: [6, 6],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#8c8d84", font: { family: "DM Sans", size: 11 } } }
      },
      scales: {
        x: { grid: { color: "#22231b" }, ticks: { color: "#8c8d84", font: { family: "DM Sans" } } },
        y: { grid: { color: "#22231b" }, ticks: { color: "#8c8d84", font: { family: "DM Sans" } } }
      }
    }
  });

  // Render Bar Chart: Calorie Adherence
  const ctxCal = document.getElementById("calorieProgressChart").getContext("2d");
  new Chart(ctxCal, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Consumed (kcal)",
          data: calorieData,
          backgroundColor: "#d4f938",
          borderRadius: 6,
          barPercentage: 0.45
        },
        {
          label: "Target Budget (kcal)",
          data: Array(labels.length).fill(dailyCaloriesTarget || 2961),
          type: "line",
          borderColor: "#ff8a7a",
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#8c8d84", font: { family: "DM Sans", size: 11 } } }
      },
      scales: {
        x: { grid: { color: "#22231b" }, ticks: { color: "#8c8d84", font: { family: "DM Sans" } } },
        y: { grid: { color: "#22231b" }, ticks: { color: "#8c8d84", font: { family: "DM Sans" } } }
      }
    }
  });

  // 2. Populate Daily Habits & Recovery Cards from the most recent log
  const latestLog = logs && logs.length > 0 ? logs[logs.length - 1] : null;

  // --- STEPS CARD ---
  const stepTarget = 10000;
  const loggedSteps = latestLog && latestLog.steps != null ? Number(latestLog.steps) : 0;
  const stepPct = Math.min(Math.round((loggedSteps / stepTarget) * 100), 100);

  if ($("stepDisplay")) $("stepDisplay").textContent = loggedSteps.toLocaleString();
  if ($("stepBar")) $("stepBar").style.width = `${stepPct}%`;
  if ($("stepStatus")) $("stepStatus").textContent = stepPct >= 100 ? "Goal Hit" : "Active";
  const stepDesc = $("stepDisplay")?.parentElement?.querySelector(".habit-target");
  if (stepDesc) stepDesc.textContent = `Target: 10,000 steps (${stepPct}% done)`;

  // --- SLEEP CARD ---
  const sleepTarget = 8.0;
  const loggedSleep = latestLog && latestLog.sleep_hours != null ? Number(latestLog.sleep_hours) : 0;
  const sleepPct = Math.min(Math.round((loggedSleep / sleepTarget) * 100), 100);

  const hours = Math.floor(loggedSleep);
  const minutes = Math.round((loggedSleep - hours) * 60);
  if ($("sleepDisplay")) $("sleepDisplay").textContent = loggedSleep > 0 ? `${hours}h ${minutes ? minutes + "m" : "00m"}` : "0h 00m";
  if ($("sleepBar")) $("sleepBar").style.width = `${sleepPct}%`;
  if ($("sleepStatus")) $("sleepStatus").textContent = loggedSleep >= 7.0 ? "Optimal" : (loggedSleep > 0 ? "Rest Needed" : "No Log");
  const sleepDesc = $("sleepDisplay")?.parentElement?.querySelector(".habit-target");
  if (sleepDesc) sleepDesc.textContent = `Target: 8h 00m (${sleepPct}% recovered)`;

  // --- WATER INTAKE CARD ---
  setupLiveWaterTracker(userId, latestLog);
}

// 3. Water Tracker Sync (Reads from Supabase log and allows live quick-adds)
function setupLiveWaterTracker(userId, latestLog) {
  const goalMl = 3000;
  // Convert Supabase Liters to milliliters (e.g. 2.5 L -> 2500 ml)
  let currentWaterMl = latestLog && latestLog.water_liters != null
    ? Math.round(Number(latestLog.water_liters) * 1000)
    : 0;

  function updateWaterDisplay() {
    const pct = Math.min(Math.round((currentWaterMl / goalMl) * 100), 100);
    if ($("waterDisplay")) $("waterDisplay").textContent = `${currentWaterMl.toLocaleString()} ml`;
    if ($("waterBar")) $("waterBar").style.width = `${pct}%`;
    if ($("waterPercentage")) $("waterPercentage").textContent = `${pct}%`;
  }

  async function persistWaterToLog(amountLiters) {
    const today = new Date().toISOString().slice(0, 10);
    await sb.from("daily_logs").upsert(
      { user_id: userId, log_date: today, water_liters: amountLiters },
      { onConflict: "user_id,log_date" }
    );
  }

  $("btnAdd250")?.addEventListener("click", async () => {
    currentWaterMl = Math.min(currentWaterMl + 250, 6000);
    updateWaterDisplay();
    await persistWaterToLog(currentWaterMl / 1000);
  });

  $("btnAdd500")?.addEventListener("click", async () => {
    currentWaterMl = Math.min(currentWaterMl + 500, 6000);
    updateWaterDisplay();
    await persistWaterToLog(currentWaterMl / 1000);
  });

  $("btnResetWater")?.addEventListener("click", async () => {
    currentWaterMl = 0;
    updateWaterDisplay();
    await persistWaterToLog(0);
  });

  updateWaterDisplay();
}

// 4. Initializer
(async function init() {
  const { data: sessionData } = await sb.auth.getSession();
  if (!sessionData.session) {
    window.location.href = "login.html";
    return;
  }
  const session = sessionData.session;
  const user = session.user;

  const { data: p, error } = await sb
    .from("profiles")
    .select("*")
    .eq("id", user.id)
    .maybeSingle();

  if (error || !p) {
    window.location.href = "onboarding.html";
    return;
  }

  const fullName = p.full_name || (user.user_metadata && user.user_metadata.full_name) || "";
  const firstName = fullName.trim().split(" ")[0];
  $("greeting").textContent = firstName ? "Hello, " + firstName + "." : "Hello.";

  const goalLine = $("goalLine");
  goalLine.textContent = "Your goal: ";
  const strong = document.createElement("strong");
  strong.textContent = p.goal;
  goalLine.append(strong, ".");

  const bmi = Number(p.bmi);
  countUp($("bmi"), bmi, 1);
  $("bmiCat").textContent = bmiCategory(bmi);

  countUp($("bmr"), Number(p.bmr));
  countUp($("cal"), Number(p.daily_calories));

  countUp($("wt"), Number(p.weight_kg), 1, " kg");
  $("wtNote").textContent = "Target: " + Number(p.target_weight_kg) + " kg";

  // Load and bind user's actual progress logs
  await loadTrackedProgress(user.id, Number(p.target_weight_kg), Number(p.daily_calories));
})();