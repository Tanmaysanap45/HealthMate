const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

const API_URL = "https://healthmate-backend-ui9u.onrender.com";

const $ = (id) => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// Makes a YouTube search link for an exercise name
function videoLink(exerciseName) {
  const query = encodeURIComponent("How To Do " + exerciseName);
  return "https://www.youtube.com/results?search_query=" + query;
}

$("logoutBtn").addEventListener("click", async () => {
  await sb.auth.signOut();
  window.location.href = "login.html";
});

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

function renderWorkout(plan) {
  $("summary").textContent = plan.summary;

  // Warnings
  const warnings = $("warnings");
  warnings.replaceChildren();
  (plan.warnings || []).forEach((w) => {
    const box = el("div", "warning " + (w.level || "info"));
    box.append(el("strong", "", w.level === "high" ? "Health Precaution" : "Guideline"), w.text);
    warnings.append(box);
  });

  // Schedule cards
  const container = $("schedule");
  container.replaceChildren();

  plan.schedule.forEach((day, i) => {
    const card = el("article", "meal");
    card.style.animationDelay = i * 0.08 + "s";

    const head = el("div", "meal-head");
    head.append(
      el("span", "meal-name", day.day),
      el("span", "meal-kcal", "Focus: " + day.focus)
    );
    card.append(head);

    const list = el("ul", "ex-list");
    day.exercises.forEach((ex) => {
      const li = el("li");

      // Exercise name opens a YouTube search in a new tab
      const nameLink = el("a", "ex-name", "▶ " + ex.name);
      nameLink.href = videoLink(ex.name);
      nameLink.target = "_blank";
      nameLink.rel = "noopener";

      li.append(
        nameLink,
        el("span", "ex-detail", ex.sets + " • Target: " + ex.type + " (" + ex.intensity + " intensity)")
      );
      list.append(li);
    });

    card.append(list);
    container.append(card);
  });

  // Coaching tips
  const notes = $("notes");
  notes.replaceChildren();
  notes.append(el("h2", "", "Workout Guidelines"));
  const ul = el("ul");
  plan.tips.forEach((t) => ul.append(el("li", "", t)));
  notes.append(ul);
}

(async function init() {
  const { data } = await sb.auth.getSession();
  if (!data.session) {
    window.location.href = "login.html";
    return;
  }

  let res;
  try {
    res = await fetch(API_URL + "/api/workout", {
      headers: { Authorization: "Bearer " + data.session.access_token }
    });
  } catch (e) {
    showProblem("Could not reach the Python backend. Please try again in a minute, as the free server may be waking up.");
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
    showProblem(err.detail || "Something went wrong loading your workout.");
    return;
  }

  renderWorkout(await res.json());
})();
