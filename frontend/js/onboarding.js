const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
const $ = (id) => document.getElementById(id);
const steps = document.querySelectorAll(".step");

const titles = [
  { t: "Your body.", s: "We use these numbers to calculate your BMI, BMR and daily calories. HealthMate is made for adults (18 and above)." },
  { t: "Your health.", s: "This helps us keep your workout and diet plans safe." },
  { t: "Your goal.", s: "Tell us what you want, and we will build your plan." }
];

const fieldsByStep = {
  1: ["age", "gender", "height", "weight", "activity"],
  2: ["condition", "diagnosis", "allergies"],
  3: ["goal", "targetWeight", "foodType", "place", "days"]
};

const numberRules = {
  age: { name: "age", min: 18, max: 90, whole: true, unit: "years" },
  height: { name: "height", min: 120, max: 230, unit: "cm" },
  weight: { name: "weight", min: 30, max: 250, unit: "kg" },
  targetWeight: { name: "target weight", min: 30, max: 250, unit: "kg" }
};

const chooseMsg = {
  gender: "Please choose your gender.",
  activity: "Please choose your activity level.",
  condition: "Please choose your body condition, or None.",
  diagnosis: "Please choose your diagnosis, or None.",
  goal: "Please choose your goal.",
  foodType: "Please choose your food type.",
  place: "Please choose where you will work out.",
  days: "Please choose how many days you can exercise."
};

let current = 1;
let user = null;

function showMessage(text, ok = false) {
  $("message").textContent = text;
  $("message").className = ok ? "ok" : "";
}

function showStep(n) {
  current = n;
  steps.forEach((s) => (s.hidden = Number(s.dataset.step) !== n));
  $("stepLabel").textContent = "Step " + n + " of 3";
  $("barFill").style.width = (n / 3) * 100 + "%";
  $("stepTitle").textContent = titles[n - 1].t;
  $("stepSub").textContent = titles[n - 1].s;
  $("backBtn").hidden = n === 1;
  $("nextBtn").hidden = n === 3;
  $("saveBtn").hidden = n !== 3;
  showMessage("");
}

// Returns an error text, or "" if the field is fine
function checkField(id) {
  const value = $(id).value.trim();
  const rule = numberRules[id];

  if (value === "") {
    if (id === "allergies") return "Please write your food allergies, or write None.";
    if (rule) return "Please enter your " + rule.name + ".";
    return chooseMsg[id];
  }
  if (rule) {
    const n = Number(value);
    if (Number.isNaN(n) || n < rule.min || n > rule.max || (rule.whole && !Number.isInteger(n))) {
      return "Please enter a valid " + rule.name + " between " + rule.min + " and " + rule.max + " " + rule.unit + ".";
    }
  }
  return "";
}

// Shows (or clears) the red text under a box
function setError(id, text) {
  const el = $(id);
  const label = el.closest("label");
  let box = label.querySelector(".field-error");
  if (!box) {
    box = document.createElement("small");
    box.className = "field-error";
    label.appendChild(box);
  }
  box.textContent = text;
  el.classList.toggle("invalid", Boolean(text));
}

function validateStep(n) {
  let firstBad = null;
  fieldsByStep[n].forEach((id) => {
    const text = checkField(id);
    setError(id, text);
    if (text && !firstBad) firstBad = id;
  });
  if (firstBad) {
    $(firstBad).focus();
    showMessage("Please fix the red boxes. All fields are required.");
    return false;
  }
  showMessage("");
  return true;
}

function calculate(d) {
  const bmi = d.weight / Math.pow(d.height / 100, 2);
  const bmr = 10 * d.weight + 6.25 * d.height - 5 * d.age + (d.gender === "male" ? 5 : -161);
  const factors = { sedentary: 1.2, light: 1.375, moderate: 1.55, active: 1.725 };
  const tdee = bmr * factors[d.activity];

  let goal = d.goal;
  if (goal === "suggest") {
    goal = bmi < 18.5 ? "build muscle" : bmi < 25 ? "stay fit" : "lose weight";
  }

  let calories = tdee;
  if (goal === "lose weight") calories = tdee - 500;
  if (goal === "build muscle") calories = tdee + 300;

  const floor = d.gender === "male" ? 1500 : 1200; // safety minimum
  calories = Math.max(calories, floor);

  return { bmi, bmr, calories, goal };
}

$("nextBtn").addEventListener("click", () => {
  if (!validateStep(current)) return;
  showStep(current + 1);
});

$("backBtn").addEventListener("click", () => showStep(current - 1));

$("onboardForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  // Check all 3 steps again before saving
  for (let n = 1; n <= 3; n++) {
    if (!validateStep(n)) {
      showStep(n);
      validateStep(n);
      return;
    }
  }

  const d = {
    age: Number($("age").value),
    gender: $("gender").value,
    height: Number($("height").value),
    weight: Number($("weight").value),
    activity: $("activity").value,
    goal: $("goal").value
  };
  const r = calculate(d);

  $("saveBtn").disabled = true;
  showMessage("Saving...", true);

  const { error } = await sb.from("profiles").upsert({
    id: user.id,
    full_name: (user.user_metadata && user.user_metadata.full_name) || null,
    age: d.age,
    gender: d.gender,
    height_cm: d.height,
    weight_kg: d.weight,
    activity_level: d.activity,
    body_condition: $("condition").value,
    diagnosis: $("diagnosis").value,
    food_allergies: $("allergies").value.trim(),
    goal: r.goal,
    target_weight_kg: Number($("targetWeight").value),
    food_type: $("foodType").value,
    workout_place: $("place").value,
    days_per_week: Number($("days").value),
    bmi: Math.round(r.bmi * 10) / 10,
    bmr: Math.round(r.bmr),
    daily_calories: Math.round(r.calories)
  });

  $("saveBtn").disabled = false;
  if (error) return showMessage(error.message);

  showMessage(
    "Saved! BMI " + r.bmi.toFixed(1) +
    ", BMR " + Math.round(r.bmr) + " kcal, daily target " +
    Math.round(r.calories) + " kcal. Your goal: " + r.goal + ".",
    true
  );
  setTimeout(() => (window.location.href = "dashboard.html"), 2500);});

// Live checking: check a box when the user leaves it, and clear the red when fixed
Object.values(fieldsByStep).flat().forEach((id) => {
  const el = $(id);
  el.addEventListener("blur", () => {
    if (el.value.trim() !== "") setError(id, checkField(id));
  });
  const recheck = () => {
    if (el.classList.contains("invalid")) setError(id, checkField(id));
  };
  el.addEventListener("input", recheck);
  el.addEventListener("change", recheck);
});

$("logoutBtn").addEventListener("click", async () => {
  await sb.auth.signOut();
  window.location.href = "login.html";
});

// Stops the mouse wheel from changing number boxes by mistake
document.querySelectorAll('input[type="number"]').forEach((i) =>
  i.addEventListener("wheel", () => i.blur())
);

// Start: the user must be logged in
(async function init() {
  const { data } = await sb.auth.getSession();
  if (!data.session) {
    window.location.href = "login.html";
    return;
  }
  user = data.session.user;
  showStep(1);
})();