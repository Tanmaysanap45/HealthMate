const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
const $ = (id) => document.getElementById(id);

const API_BASE = window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "http://127.0.0.1:8000";

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

  const btn = $("btnRunOptimizer");
  const resultBox = $("optimizerResultBox");
  const tableBody = $("optimizedTableBody");
  const macroSummary = $("optimizedMacroSummary");

  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳ Solving Linear Programming Matrix...</span>`;

    try {
      const res = await fetch(`${API_BASE}/api/diet/optimized`, {
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Server returned error: ${res.status} - ${errorText}`);
      }

      const data = await res.json();
      tableBody.innerHTML = "";

      if (data.meals && data.meals.length > 0) {
        data.meals.forEach((m) => {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td style="font-weight: 600; color: #ffffff;">${m.food}</td>
            <td style="color: #d4f938; font-weight: 700;">${m.portion_grams}g</td>
            <td style="color: #e2e4dc;">${m.calories}</td>
            <td style="color: #d4f938; font-weight: 600;">${m.protein_g}g</td>
            <td style="color: #e2e4dc;">${m.carbs_g}g</td>
            <td style="color: #e2e4dc;">${m.fat_g}g</td>
          `;
          tableBody.appendChild(row);
        });

        macroSummary.innerHTML = `
          <span><strong>Total Calories:</strong> ${data.achieved_calories} kcal / ${data.target_calories} target</span>
          <span><strong>Total Protein:</strong> <span style="color: #d4f938; font-weight: bold;">${data.achieved_protein}g</span> (Min target: ${data.target_protein_min}g)</span>
          <span><strong>Total Carbs:</strong> ${data.achieved_carbs}g</span>
          <span><strong>Total Fats:</strong> ${data.achieved_fat}g</span>
          <span style="color: #8c8d84; font-size: 0.8rem; margin-left: auto;">Algorithm: ${data.algorithm}</span>
        `;

        resultBox.style.display = "block";
      } else {
        alert(data.message || "Could not optimize with current restrictions.");
      }
    } catch (err) {
      console.error("Optimizer error:", err);
      alert(`Backend Optimizer Error: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span>⚡ Run LP Optimizer</span>`;
    }
  });
})();