const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
const API_URL = "https://healthmate-backend-ui9u.onrender.com"; // our Python backend
const $ = (id) => document.getElementById(id);

// Small helper that builds one HTML element
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

$("logoutBtn").addEventListener("click", async () => {
  await sb.auth.signOut();
  window.location.href = "login.html";
});

// Shows a problem message at the top, with an optional link
function showProblem(text, linkText, linkHref) {
  const box = $("summary");
  box.textContent = text + " ";
  if (linkHref) {
    const a = el("a", "", linkText);
    a.href = linkHref;
    a.style.color = "var(--accent)";
    a.style.textDecoration = "underline";
    box.append(a);
  }
}

function statCard(label, value, note) {
  const card = el("article", "stat-card");
  card.append(el("span", "label", label), el("strong", "", value), el("small", "", note));
  return card;
}

// Small label such as "Option 1"
function optionBadge(text) {
  const badge = el("span", "", text);
  badge.style.cssText =
    "background:#202715;color:var(--accent);border:1px solid #35421f;" +
    "border-radius:6px;padding:2px 8px;font-size:0.72rem;font-weight:700;" +
    "text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;";
  return badge;
}

function renderDiet(plan) {
  $("summary").textContent = plan.summary;

  // Warnings
  const warnings = $("warnings");
  warnings.replaceChildren();
  plan.warnings.forEach((w) => {
    const box = el("div", "warning " + w.level);
    box.append(el("strong", "", w.level === "high" ? "Important" : "Please note"), w.text);
    warnings.append(box);
  });

  // Daily numbers
  const numbers = $("numbers");
  numbers.replaceChildren();
  numbers.append(
    statCard("Calories", String(plan.calories), "kcal a day"),
    statCard("Protein", plan.protein_g + " g", "a day"),
    statCard("Carbs", plan.carbs_g + " g", "a day"),
    statCard("Fat", plan.fat_g + " g", "a day"),
    statCard("Water", plan.water_l + " L", "a day")
  );

  // Meals
  const meals = $("meals");
  meals.replaceChildren();
  plan.meals.forEach((m, i) => {
    const card = el("article", "meal");
    card.style.animationDelay = i * 0.08 + "s";

    const head = el("div", "meal-head");
    head.append(
      el("span", "meal-name", m.name),
      el("span", "meal-kcal", "About " + m.kcal + " kcal (" + m.share + "% of your day)")
    );
    card.append(head);

    if (m.options.length === 0) {
      card.append(el("p", "empty-meal", "No safe foods found. Please ask a dietitian."));
    } else {
      // Tell the user what to do with the options
      const hint = el("p", "", "Choose ONE option below for this meal.");
      hint.style.cssText = "font-size:0.85rem;color:var(--muted);margin-top:10px;";
      card.append(hint);

      const list = el("ul", "ex-list");
      m.options.forEach((o, index) => {
        const li = el("li");
        const portion = o.servings + (o.servings === 1 ? " serving" : " servings") + ", about " + o.kcal + " kcal";

        const top = el("div");
        top.style.cssText = "display:flex;align-items:center;gap:10px;flex-wrap:wrap;";
        top.append(optionBadge("Option " + (index + 1)), el("span", "ex-name", o.name));

        li.append(top, el("span", "ex-detail", portion));
        list.append(li);
      });
      card.append(list);
    }
    meals.append(card);
  });

  // Tips
  const notes = $("notes");
  notes.replaceChildren();
  notes.append(el("h2", "", "Good to know"));
  const ul = el("ul");
  plan.tips.forEach((t) => ul.append(el("li", "", t)));
  notes.append(ul);
}

// Grocery list: adds up the food from the plan
function setupGrocery(plan) {
  const DAYS = 7; // change this number to shop for more or fewer days

  $("groceryBtn").addEventListener("click", () => {
    // Add up the food, using Option 1 for each meal
    const totals = {};
    plan.meals.forEach((meal) => {
      if (meal.options.length === 0) return;
      const pick = meal.options[0];
      totals[pick.name] = (totals[pick.name] || 0) + pick.servings * DAYS;
    });

    // Show the list with a tick box for each item
    const box = $("groceryList");
    box.replaceChildren();
    box.append(el("h2", "", "Grocery list for " + DAYS + " days"));

    const ul = el("ul", "ex-list");
    Object.entries(totals).forEach(([name, servings]) => {
      const li = el("li");
      const label = el("label", "");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      label.append(checkbox, " " + name + " (" + servings + " servings)");
      li.append(label);
      ul.append(li);
    });
    box.append(ul);
  });
}

(async function init() {
  // 1. The user must be logged in
  const { data } = await sb.auth.getSession();
  if (!data.session) {
    window.location.href = "login.html";
    return;
  }

  // 2. Ask the Python backend for the plan, and send the login token
  let res;
  try {
    res = await fetch(API_URL + "/api/diet", {
      headers: { Authorization: "Bearer " + data.session.access_token }
    });
  } catch (e) {
    showProblem("Could not reach the Python backend. Open a terminal in the backend folder and run: python -m uvicorn main:app --reload --port 8000");
    return;
  }

  if (res.status === 401) {
    window.location.href = "login.html";
    return;
  }
  if (res.status === 404) {
    showProblem("We could not find your saved details.", "Fill in the details form", "onboarding.html");
    return;
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    showProblem(err.detail || "Something went wrong. Please try again.");
    return;
  }

  // 3. Show the plan, then turn on the grocery button
  const plan = await res.json();
  renderDiet(plan);
  setupGrocery(plan);
})();