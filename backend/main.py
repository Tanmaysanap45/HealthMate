import base64
import json
import logging
import os
import re
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from google import genai
from google.genai import types
from pydantic import BaseModel

from diet_optimizer import optimize_diet_plan
from diet_plan import generate_diet
from report_pdf import build_report_pdf
from trajectory_engine import compute_trajectory
from workout_graph import find_safe_progression
from workout_plan import generate_plan

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Parse comma-separated Gemini keys
raw_keys = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

# Model list to cycle through if a model faces temporary traffic spikes (e.g. 503)
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HealthMate")

app = FastAPI(title="HealthMate API")

# Updated CORS to support localhost, 127.0.0.1, and various dev ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_profile(authorization: Optional[str]) -> dict:
    """Read the logged-in user's saved details from Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(500, "The backend .env file is missing SUPABASE_URL or SUPABASE_KEY.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please log in first.")

    headers = {"apikey": SUPABASE_KEY, "Authorization": authorization}
    try:
        r = httpx.get(
            f"{SUPABASE_URL}/rest/v1/profiles",
            params={"select": "*"},
            headers=headers,
            timeout=15,
        )
    except httpx.HTTPError:
        raise HTTPException(502, "Could not reach Supabase.")

    if r.status_code in (401, 403):
        raise HTTPException(401, "Your login has expired. Please log in again.")
    if r.status_code != 200:
        raise HTTPException(502, "Supabase returned an error.")

    rows = r.json()
    if not rows:
        raise HTTPException(404, "No saved details found. Please fill in the details form first.")
    return rows[0]


def get_user_logs(authorization: str) -> list[dict]:
    """Retrieve all daily logs for the logged-in user from Supabase."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": authorization}
    try:
        r = httpx.get(
            f"{SUPABASE_URL}/rest/v1/daily_logs",
            params={"select": "log_date,weight_kg,steps,calories_consumed", "order": "log_date.asc"},
            headers=headers,
            timeout=15,
        )
    except httpx.HTTPError:
        raise HTTPException(502, "Could not reach Supabase logs.")

    if r.status_code != 200:
        raise HTTPException(502, "Failed to retrieve logs from Supabase.")
    return r.json()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "HealthMate API", "keys_loaded": len(GEMINI_API_KEYS)}


# ---------- Machine Learning Trajectory Endpoint ----------
@app.get("/api/analytics/trajectory")
def get_weight_trajectory(authorization: Optional[str] = Header(default=None)):
    """Runs OLS regression on user logs to project target date and evaluate plateau state."""
    if not authorization:
        raise HTTPException(401, "Please log in first.")

    profile = get_profile(authorization)
    target_weight = profile.get("target_weight_kg")

    if not target_weight:
        raise HTTPException(400, "Target weight is not configured in your profile.")

    logs = get_user_logs(authorization)
    return compute_trajectory(logs, float(target_weight))


# ---------- Workout plan (Rule-based) ----------
@app.get("/api/workout")
def workout(authorization: Optional[str] = Header(default=None)):
    return generate_plan(get_profile(authorization))


@app.get("/api/workout/demo")
def workout_demo(
    goal: str = "lose weight",
    place: str = "home",
    days: int = 3,
    condition: str = "none",
    diagnosis: str = "none",
    activity: str = "light",
    age: int = 25,
    bmi: float = 24,
):
    return generate_plan({
        "goal": goal, "workout_place": place, "days_per_week": days,
        "body_condition": condition, "diagnosis": diagnosis,
        "activity_level": activity, "age": age, "bmi": bmi,
    })


# ---------- Biomechanical Graph Traversal Endpoints ----------
@app.get("/api/workout/safe-substitution")
def get_safe_substitution(exercise: str, authorization: Optional[str] = Header(default=None)):
    """Traverses DAG movement graph to prune contraindicated joints for logged-in user."""
    profile = get_profile(authorization)
    user_conditions = []
    if profile.get("body_condition") and profile.get("body_condition") != "none":
        user_conditions.append(profile.get("body_condition"))
    if profile.get("diagnosis") and profile.get("diagnosis") != "none":
        user_conditions.append(profile.get("diagnosis"))

    return find_safe_progression(exercise_key=exercise.lower().strip(), user_conditions=user_conditions)


@app.get("/api/workout/safe-substitution/demo")
def get_safe_substitution_demo(exercise: str = "barbell_back_squat", condition: str = "knee pain"):
    """Direct demonstration endpoint for examiners testing graph traversal algorithms."""
    conditions = [c.strip() for c in condition.split(",") if c.strip()]
    return find_safe_progression(exercise_key=exercise.lower().strip(), user_conditions=conditions)


# ---------- Standard Diet plan ----------
@app.get("/api/diet")
def diet(authorization: Optional[str] = Header(default=None)):
    return generate_diet(get_profile(authorization))


@app.get("/api/diet/demo")
def diet_demo(
    goal: str = "lose weight",
    food: str = "vegetarian",
    calories: int = 1800,
    weight: float = 70,
    diagnosis: str = "none",
    allergies: str = "none",
):
    return generate_diet({
        "goal": goal, "food_type": food, "daily_calories": calories,
        "weight_kg": weight, "diagnosis": diagnosis, "food_allergies": allergies,
    })


# ---------- Linear Programming Diet Optimizer Endpoints ----------
@app.get("/api/diet/optimized")
def diet_optimized(authorization: Optional[str] = Header(default=None)):
    """Solves Linear Programming problem for the logged-in user's profile."""
    profile = get_profile(authorization)
    daily_calories = int(profile.get("daily_calories") or 2000)
    weight_kg = float(profile.get("weight_kg") or 70.0)
    food_type = profile.get("food_type") or "vegetarian"
    allergies = profile.get("food_allergies") or "none"

    return optimize_diet_plan(
        daily_calories=daily_calories,
        weight_kg=weight_kg,
        food_type=food_type,
        allergies=allergies,
    )


@app.get("/api/diet/optimized/demo")
def diet_optimized_demo(
    calories: int = 2000,
    weight: float = 72.0,
    food_type: str = "vegetarian",
    allergies: str = "none",
):
    """Test optimization without logging in."""
    return optimize_diet_plan(
        daily_calories=calories,
        weight_kg=weight,
        food_type=food_type,
        allergies=allergies,
    )


# ---------- AI Chat Coach with Model & Key Failover ----------
class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def chat_with_coach(req: ChatRequest, authorization: Optional[str] = Header(default=None)):
    """Personalized AI fitness coaching endpoint with automatic multi-model and multi-key fallback."""
    profile = get_profile(authorization)
    query = req.message.strip()

    if not query:
        raise HTTPException(400, "Message cannot be empty.")

    if not GEMINI_API_KEYS:
        return {"reply": "No Gemini API keys found in backend/.env. Please configure GEMINI_API_KEYS."}

    system_instruction = (
        "You are 'HealthMate Coach', an encouraging, empathetic, and knowledgeable fitness and nutrition mentor. "
        "Provide direct, actionable, practical, and safe fitness or nutrition advice. "
        "Keep answers concise (under 3-4 sentences or clear bullet points) suitable for a web chat bubble. "
        "Always respect the user's injuries and dietary preferences. "
        "Do not offer clinical medical diagnoses; recommend consulting a doctor for acute medical pains.\n\n"
        f"User Background:\n"
        f"- Target Goal: {profile.get('goal')}\n"
        f"- Daily Caloric Target: {profile.get('daily_calories')} kcal\n"
        f"- Dietary Style: {profile.get('food_type')}\n"
        f"- Allergies / Restrictions: {profile.get('food_allergies') or 'None'}\n"
        f"- Physical Conditions / Injuries: {profile.get('body_condition') or 'None'}\n"
        f"- Medical Diagnosis: {profile.get('diagnosis') or 'None'}\n"
        f"- Workout Location: {profile.get('workout_place') or 'Home'}"
    )

    last_error = ""

    # Iterate through models and keys sequentially until one succeeds
    for model_name in FALLBACK_MODELS:
        for index, key in enumerate(GEMINI_API_KEYS):
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=query,
                    config={
                        "system_instruction": system_instruction,
                        "temperature": 0.7,
                    }
                )
                if response.text:
                    return {"reply": response.text}
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Model {model_name} with Key #{index + 1} failed: {e}. Switching to next key/model..."
                )
                continue

    return {
        "reply": "The AI coach is currently experiencing heavy server traffic. Please ask your question again in a moment."
    }


# ---------- Meal Nutrition (Gemini) ----------
# Food name: starts with a letter, then letters, spaces, dots, apostrophes, brackets or dashes.
FOOD_PATTERN = re.compile(r"[^\W\d_][A-Za-z\u00C0-\u024F .'()\-]{1,59}")
# Amount: a number first, then an optional unit, like "100g", "1 plate", "300ml"
AMOUNT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*([A-Za-z ]{0,20})")
MAX_AMOUNT = 1000        # largest allowed amount number
MAX_MEAL_KCAL = 10000    # largest believable calories for one entry

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


class MealRequest(BaseModel):
    food_name: str
    amount: str = "1 serving"


class ScanRequest(BaseModel):
    image_base64: str
    mime_type: str


def check_meal_input(food: str, amount: str) -> None:
    """Raises a 400 error if the food name or amount is not allowed."""
    if not FOOD_PATTERN.fullmatch(food):
        raise HTTPException(400, "Food name must be 2 to 60 letters (no numbers or symbols).")

    match = AMOUNT_PATTERN.fullmatch(amount)
    if not match:
        raise HTTPException(400, "Amount must start with a number, like 100g, 1 plate or 300ml.")

    value = float(match.group(1))
    if value <= 0:
        raise HTTPException(400, "Amount must be more than zero.")
    if value > MAX_AMOUNT:
        raise HTTPException(400, f"Amount must be {MAX_AMOUNT} or less.")


def clean_json_text(text: Optional[str]) -> str:
    """Removes markdown code fences that the AI sometimes adds around JSON."""
    return (text or "").strip().replace("```json", "").replace("```", "").strip()


def clean_food_name(text: str) -> str:
    """Keeps only letters, spaces and simple punctuation from an AI food name."""
    cleaned = re.sub(r"[^A-Za-z\u00C0-\u024F .'()\-]", "", str(text)).strip()
    return cleaned[:60]


def clean_amount(text: str) -> str:
    """Uses the AI amount if it looks valid, otherwise uses one serving."""
    text = str(text).strip()[:25]
    match = AMOUNT_PATTERN.fullmatch(text)
    if match and 0 < float(match.group(1)) <= MAX_AMOUNT:
        return text
    return "1 serving"


@app.post("/api/meal/estimate")
def estimate_meal(req: MealRequest, authorization: Optional[str] = Header(default=None)):
    """Ask Gemini to estimate calories and macros for one meal item."""
    get_profile(authorization)  # makes sure the user is logged in

    food = req.food_name.strip()
    amount = req.amount.strip() or "1 serving"
    check_meal_input(food, amount)

    if not GEMINI_API_KEYS:
        raise HTTPException(500, "No Gemini API keys found in backend/.env.")

    prompt = (
        "Estimate the nutrition for this meal item. "
        f"Food: {food}. Amount: {amount}. "
        "Reply ONLY with a JSON object, with no extra text and no markdown, in this exact form: "
        '{"calories": number, "protein_g": number, "carbs_g": number, "fat_g": number}. '
        "Use whole numbers. Give your best realistic estimate for the amount given."
    )

    for model_name in FALLBACK_MODELS:
        for index, key in enumerate(GEMINI_API_KEYS):
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"temperature": 0.2},
                )
                data = json.loads(clean_json_text(response.text))

                values = {
                    "calories": float(data.get("calories", 0)),
                    "protein_g": float(data.get("protein_g", 0)),
                    "carbs_g": float(data.get("carbs_g", 0)),
                    "fat_g": float(data.get("fat_g", 0)),
                }
                # Reject nonsense from the AI (negative or unrealistic values)
                if any(v < 0 for v in values.values()) or values["calories"] > MAX_MEAL_KCAL:
                    raise ValueError("Unrealistic estimate")

                return {
                    "food_name": food,
                    "amount": amount,
                    "calories": round(values["calories"]),
                    "protein_g": round(values["protein_g"], 1),
                    "carbs_g": round(values["carbs_g"], 1),
                    "fat_g": round(values["fat_g"], 1),
                }
            except Exception as e:
                logger.warning(
                    f"Meal estimate with {model_name} / Key #{index + 1} failed: {e}. Trying next..."
                )
                continue

    raise HTTPException(503, "Could not work out the nutrition right now. Please try again.")


@app.post("/api/meal/scan")
def scan_meal(req: ScanRequest, authorization: Optional[str] = Header(default=None)):
    """Ask Gemini to look at a meal photo and estimate the food, amount and nutrition."""
    get_profile(authorization)  # makes sure the user is logged in

    if req.mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Please upload a JPG, PNG or WEBP photo.")

    try:
        image_bytes = base64.b64decode(req.image_base64, validate=True)
    except Exception:
        raise HTTPException(400, "The photo could not be read. Please try another photo.")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "That photo is bigger than 5 MB. Please choose a smaller one.")

    if not GEMINI_API_KEYS:
        raise HTTPException(500, "No Gemini API keys found in backend/.env.")

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=req.mime_type)
    prompt = (
        "Look at this photo of a meal. Identify the main food and estimate the portion you can see. "
        "Reply ONLY with a JSON object, with no extra text and no markdown, in this exact form: "
        '{"food_name": text, "amount": text, "calories": number, "protein_g": number, '
        '"carbs_g": number, "fat_g": number}. '
        "food_name must be a short name using letters only, for example Peanut poha. "
        "amount must look like 1 plate, 150g or 1 cup. "
        'If there is no food in the photo, reply {"food_name": ""}.'
    )

    result = None
    for model_name in FALLBACK_MODELS:
        for index, key in enumerate(GEMINI_API_KEYS):
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=[image_part, prompt],
                    config={"temperature": 0.2},
                )
                result = json.loads(clean_json_text(response.text))
                break
            except Exception as e:
                logger.warning(
                    f"Meal scan with {model_name} / Key #{index + 1} failed: {e}. Trying next..."
                )
                continue
        if result is not None:
            break

    if result is None:
        raise HTTPException(503, "Could not scan the photo right now. Please try again.")

    if not isinstance(result, dict):
        result = {}

    food = clean_food_name(result.get("food_name", ""))
    if not FOOD_PATTERN.fullmatch(food):
        raise HTTPException(400, "No clear food was found in this photo. Please type it manually.")

    try:
        values = {
            "calories": float(result.get("calories", 0)),
            "protein_g": float(result.get("protein_g", 0)),
            "carbs_g": float(result.get("carbs_g", 0)),
            "fat_g": float(result.get("fat_g", 0)),
        }
    except (TypeError, ValueError):
        raise HTTPException(400, "Could not read the nutrition from this photo. Please type the meal manually.")

    if any(v < 0 for v in values.values()) or values["calories"] > MAX_MEAL_KCAL:
        raise HTTPException(400, "The estimate looked unrealistic. Please type the meal manually.")

    return {
        "food_name": food,
        "amount": clean_amount(result.get("amount", "")),
        "calories": round(values["calories"]),
        "protein_g": round(values["protein_g"], 1),
        "carbs_g": round(values["carbs_g"], 1),
        "fat_g": round(values["fat_g"], 1),
    }


# ---------- Downloadable PDF Report (no AI) ----------
@app.get("/api/report/pdf")
def download_report(authorization: Optional[str] = Header(default=None)):
    """Builds the user's PDF report: info, workout plan, diet plan and advice."""
    profile = get_profile(authorization)
    workout_plan = generate_plan(profile)
    diet_plan = generate_diet(profile)
    pdf_bytes = build_report_pdf(profile, workout_plan, diet_plan)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="HealthMate-Report.pdf"'},
    )