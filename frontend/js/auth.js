const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

const form = document.getElementById("authForm");
const title = document.getElementById("title");
const subtitle = document.getElementById("subtitle");
const nameRow = document.getElementById("nameRow");
const nameInput = document.getElementById("name");
const emailInput = document.getElementById("email");
const passInput = document.getElementById("password");
const message = document.getElementById("message");
const submitBtn = document.getElementById("submitBtn");
const switchText = document.getElementById("switchText");
const switchBtn = document.getElementById("switchBtn");

let isSignup = false;

function showMessage(text, ok = false) {
  message.textContent = text;
  message.className = ok ? "ok" : "";
}

function setMode(signup) {
  isSignup = signup;
  nameRow.hidden = !signup;
  title.textContent = signup ? "Create your account." : "Welcome back.";
  subtitle.textContent = signup ? "It takes less than a minute." : "Log in to see your plan.";
  submitBtn.textContent = signup ? "Create account" : "Log in";
  switchText.textContent = signup ? "Already have an account?" : "New to HealthMate?";
  switchBtn.textContent = signup ? "Log in" : "Create account";
  passInput.autocomplete = signup ? "new-password" : "current-password";
  showMessage("");
}

// If the user already saved their details, go to the dashboard.
// If not, go to the onboarding page.
async function goToNextPage(user) {
  const { data } = await sb
    .from("profiles")
    .select("id")
    .eq("id", user.id)
    .maybeSingle();
  window.location.href = data ? "dashboard.html" : "onboarding.html";
}

switchBtn.addEventListener("click", () => setMode(!isSignup));

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = nameInput.value.trim();
  const email = emailInput.value.trim();
  const password = passInput.value;

  if (isSignup && !name) return showMessage("Please enter your full name.");
  if (!email) return showMessage("Please enter your email.");
  if (password.length < 6) return showMessage("Password must be at least 6 characters.");

  submitBtn.disabled = true;
  showMessage("Please wait...", true);

  let result;
  if (isSignup) {
    result = await sb.auth.signUp({
      email,
      password,
      options: { data: { full_name: name } }
    });
  } else {
    result = await sb.auth.signInWithPassword({ email, password });
  }

  submitBtn.disabled = false;

  if (result.error) return showMessage(result.error.message);

  if (isSignup && !result.data.session) {
    showMessage("Account created. Check your email to confirm, then log in.", true);
  } else {
    showMessage("Success! Taking you to your page...", true);
    await goToNextPage(result.data.user);
  }
});

// Opens the sign-up form if the link has ?mode=signup
if (new URLSearchParams(location.search).get("mode") === "signup") setMode(true);

// If the user is already logged in, skip the login page
sb.auth.getSession().then(({ data }) => {
  if (data.session) goToNextPage(data.session.user);
});