const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
const $ = (id) => document.getElementById(id);

const API_BASE = "https://healthmate-backend-ui9u.onrender.com";

$("logoutBtn").addEventListener("click", async () => {
  await sb.auth.signOut();
  window.location.href = "login.html";
});

(async function init() {
  const { data: sessionData } = await sb.auth.getSession();
  if (!sessionData.session) {
    window.location.href = "login.html";
    return;
  }
  const token = sessionData.session.access_token;

  try {
    const res = await fetch(`${API_BASE}/api/analytics/trajectory`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!res.ok) {
      $("plateauBadge").textContent = "Need More Logs";
      return;
    }

    const data = await res.json();

    if (data.status === "insufficient_data") {
      $("mlR2").textContent = "Need >= 3 logs";
      $("plateauBadge").textContent = "Need 3+ logs";
      $("mlWeeklyRate").textContent = "Pending";
      $("mlGoalDate").textContent = "Log 3+ days";
      $("mlDaysRemaining").textContent = "Awaiting data";
      return;
    }

    if (data.status === "success") {
      $("mlR2").textContent = data.model_r2_score;
      $("mlWeeklyRate").textContent = `${data.weekly_rate_kg > 0 ? "+" : ""}${data.weekly_rate_kg} kg/wk`;
      $("mlGoalDate").textContent = data.predicted_target_date || "Stabilizing";
      $("mlDaysRemaining").textContent = data.days_to_target ? `${data.days_to_target} days` : "On Target";

      const badge = $("plateauBadge");
      if (data.is_plateau) {
        badge.textContent = "⚠️ Plateau Detected";
        badge.style.background = "#2b2110";
        badge.style.color = "#fde047";
        badge.style.border = "1px solid #4a3816";
      } else {
        badge.textContent = "✓ Progress Active";
        badge.style.background = "#202715";
        badge.style.color = "#d4f938";
        badge.style.border = "1px solid #35421f";
      }
    }
  } catch (err) {
    console.error("Trajectory error:", err);
    $("plateauBadge").textContent = "Error connecting";
  }
})();
