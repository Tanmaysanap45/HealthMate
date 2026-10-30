"""Workout plan rules for HealthMate.

Rule-based workout plan generation following the exact parameters
expected by main.py and the frontend dashboard.
"""

EXERCISES = {
    "home": {
        "Full Body": [
            {"name": "Bodyweight Squats", "sets": "3 sets of 12-15 reps", "type": "legs", "intensity": "low"},
            {"name": "Push-ups (or Knee Push-ups)", "sets": "3 sets of 8-12 reps", "type": "chest", "intensity": "medium"},
            {"name": "Glute Bridges", "sets": "3 sets of 12-15 reps", "type": "legs", "intensity": "low"},
            {"name": "Plank Hold", "sets": "3 sets of 30-45 sec", "type": "core", "intensity": "low"},
            {"name": "Jumping Jacks", "sets": "3 sets of 45 sec", "type": "cardio", "intensity": "medium"},
        ],
        "Upper Body": [
            {"name": "Standard Push-ups", "sets": "3 sets of 10-15 reps", "type": "chest", "intensity": "medium"},
            {"name": "Pike Push-ups", "sets": "3 sets of 8-10 reps", "type": "shoulders", "intensity": "high"},
            {"name": "Chair / Bench Dips", "sets": "3 sets of 10-12 reps", "type": "triceps", "intensity": "medium"},
            {"name": "Doorframe Rows / Inverted Rows", "sets": "3 sets of 10-12 reps", "type": "back", "intensity": "medium"},
            {"name": "Plank to Push-up", "sets": "3 sets of 8 reps", "type": "core", "intensity": "medium"},
        ],
        "Lower Body": [
            {"name": "Bodyweight Squats", "sets": "4 sets of 15 reps", "type": "quads", "intensity": "medium"},
            {"name": "Walking Lunges", "sets": "3 sets of 10 reps per leg", "type": "legs", "intensity": "medium"},
            {"name": "Single-Leg Glute Bridge", "sets": "3 sets of 10 reps per leg", "type": "glutes", "intensity": "medium"},
            {"name": "Standing Calf Raises", "sets": "3 sets of 20 reps", "type": "calves", "intensity": "low"},
            {"name": "Wall Sit", "sets": "3 sets of 30-45 sec hold", "type": "quads", "intensity": "high"},
        ],
        "Cardio & Core": [
            {"name": "High Knees", "sets": "3 sets of 40 sec", "type": "cardio", "intensity": "high"},
            {"name": "Mountain Climbers", "sets": "3 sets of 30 sec", "type": "core", "intensity": "high"},
            {"name": "Bicycle Crunches", "sets": "3 sets of 15 reps per side", "type": "core", "intensity": "medium"},
            {"name": "Russian Twists", "sets": "3 sets of 20 total reps", "type": "core", "intensity": "medium"},
            {"name": "Brisk Walk / Jog in Place", "sets": "10-15 minutes steady pace", "type": "cardio", "intensity": "low"},
        ],
    },
    "gym": {
        "Full Body": [
            {"name": "Barbell or Goblet Squat", "sets": "3 sets of 8-10 reps", "type": "legs", "intensity": "high"},
            {"name": "Dumbbell Bench Press", "sets": "3 sets of 10-12 reps", "type": "chest", "intensity": "medium"},
            {"name": "Lat Pulldown or Seated Cable Row", "sets": "3 sets of 10-12 reps", "type": "back", "intensity": "medium"},
            {"name": "Dumbbell Overhead Shoulder Press", "sets": "3 sets of 10 reps", "type": "shoulders", "intensity": "medium"},
            {"name": "Hanging Knee Raises", "sets": "3 sets of 12 reps", "type": "core", "intensity": "medium"},
        ],
        "Push": [
            {"name": "Flat Barbell Bench Press", "sets": "4 sets of 8-10 reps", "type": "chest", "intensity": "high"},
            {"name": "Incline Dumbbell Press", "sets": "3 sets of 10-12 reps", "type": "chest", "intensity": "medium"},
            {"name": "Seated Dumbbell Overhead Press", "sets": "3 sets of 10 reps", "type": "shoulders", "intensity": "medium"},
            {"name": "Cable Lateral Raises", "sets": "3 sets of 12-15 reps", "type": "shoulders", "intensity": "low"},
            {"name": "Triceps Rope Pushdowns", "sets": "3 sets of 12-15 reps", "type": "triceps", "intensity": "low"},
        ],
        "Pull": [
            {"name": "Conventional or Romanian Deadlift", "sets": "3 sets of 6-8 reps", "type": "back", "intensity": "high"},
            {"name": "Lat Pulldown (Wide Grip)", "sets": "3 sets of 10-12 reps", "type": "back", "intensity": "medium"},
            {"name": "Seated Cable Rows", "sets": "3 sets of 10-12 reps", "type": "back", "intensity": "medium"},
            {"name": "Face Pulls", "sets": "3 sets of 15 reps", "type": "rear delts", "intensity": "low"},
            {"name": "Barbell or Dumbbell Bicep Curls", "sets": "3 sets of 10-12 reps", "type": "biceps", "intensity": "low"},
        ],
        "Legs": [
            {"name": "Barbell Back Squats", "sets": "4 sets of 8-10 reps", "type": "quads", "intensity": "high"},
            {"name": "Leg Press Machine", "sets": "3 sets of 10-12 reps", "type": "legs", "intensity": "medium"},
            {"name": "Leg Curl (Hamstrings)", "sets": "3 sets of 12 reps", "type": "hamstrings", "intensity": "low"},
            {"name": "Dumbbell Walking Lunges", "sets": "3 sets of 10 steps per leg", "type": "glutes", "intensity": "medium"},
            {"name": "Standing Calf Raises", "sets": "4 sets of 15 reps", "type": "calves", "intensity": "low"},
        ],
    },
}


def adjust_for_health(exercises, body_condition, diagnosis, age, bmi):
    """Filters or replaces high-impact moves based on injuries, diagnosis, age, or BMI."""
    warnings = []
    filtered = []

    cond = (body_condition or "none").lower()
    diag = (diagnosis or "none").lower()

    if "knee" in cond or "back" in cond:
        warnings.append({"level": "high", "text": f"Modified for your {cond}: avoid heavy axial loading and deep squats without medical clearance."})
    if diag in ("high blood pressure", "heart problem"):
        warnings.append({"level": "high", "text": "Cardiac caution: avoid maximum 1-rep efforts and prolonged breath-holding (Valsalva maneuver). Rest well between sets."})
    if bmi >= 30:
        warnings.append({"level": "info", "text": "Low-impact exercises are emphasized to minimize joint stress."})
    if age >= 60:
        warnings.append({"level": "info", "text": "Focus on stability, controlled tempo, and joint mobility warm-ups."})

    for ex in exercises:
        name_lower = ex["name"].lower()
        if ("knee" in cond or bmi >= 32) and any(k in name_lower for k in ["jumping", "high knees", "lunges"]):
            filtered.append({"name": "Brisk Treadmill or Incline Walking", "sets": "15-20 mins steady low impact", "type": "cardio", "intensity": "low"})
        elif "back" in cond and any(b in name_lower for b in ["deadlift", "pike"]):
            filtered.append({"name": "Chest-Supported Row", "sets": "3 sets of 12 reps (neutral spine)", "type": "back", "intensity": "low"})
        else:
            filtered.append(ex)

    return filtered, warnings


def generate_plan(profile: dict) -> dict:
    place = profile.get("workout_place") or "home"
    if place not in EXERCISES:
        place = "home"

    goal = profile.get("goal") or "stay fit"
    days = int(profile.get("days_per_week") or 3)
    days = min(max(days, 2), 6)
    condition = profile.get("body_condition") or "none"
    diagnosis = profile.get("diagnosis") or "none"
    age = int(profile.get("age") or 25)
    bmi = float(profile.get("bmi") or 22.0)

    # Decide schedule split based on days per week
    if place == "gym" and days >= 5:
        split_routine = [
            ("Day 1: Push (Chest, Shoulders, Triceps)", "Push"),
            ("Day 2: Pull (Back, Biceps, Rear Delts)", "Pull"),
            ("Day 3: Legs & Abs", "Legs"),
            ("Day 4: Rest & Mobility", None),
            ("Day 5: Push / Upper Body", "Push"),
            ("Day 6: Pull / Lower Body", "Legs"),
        ][:days]
    elif days >= 4:
        split_routine = [
            ("Day 1: Upper Body Strength", "Upper Body" if place == "home" else "Push"),
            ("Day 2: Lower Body & Core", "Lower Body" if place == "home" else "Legs"),
            ("Day 3: Rest & Hydration", None),
            ("Day 4: Cardio & Core Conditioning", "Cardio & Core" if place == "home" else "Pull"),
            ("Day 5: Full Body Functional Circuit", "Full Body"),
            ("Day 6: Upper Body Endurance", "Upper Body" if place == "home" else "Push"),
        ][:days]
    else:
        split_routine = [
            ("Day 1: Full Body Foundations", "Full Body"),
            ("Day 2: Rest or Active Recovery", None),
            ("Day 3: Full Body Strength & Core", "Full Body"),
            ("Day 4: Rest or Mobility Walk", None),
            ("Day 5: Full Body Conditioning", "Cardio & Core" if place == "home" else "Legs"),
        ][:days]

    schedule = []
    all_warnings = []

    for day_title, workout_type in split_routine:
        if workout_type is None:
            schedule.append({
                "day": day_title,
                "focus": "Recovery",
                "exercises": [{"name": "Light Stretching & 20-min Walk", "sets": "1 session", "type": "mobility", "intensity": "low"}]
            })
        else:
            base_pool = EXERCISES[place].get(workout_type, EXERCISES[place]["Full Body"])
            clean_ex, warns = adjust_for_health(base_pool, condition, diagnosis, age, bmi)
            all_warnings.extend(warns)
            schedule.append({
                "day": day_title,
                "focus": workout_type,
                "exercises": clean_ex
            })

    # Deduplicate warning messages
    unique_warnings = []
    seen = set()
    for w in all_warnings:
        if w["text"] not in seen:
            unique_warnings.append(w)
            seen.add(w["text"])

    tips = [
        "Warm up for 5 to 10 minutes with dynamic stretches before starting.",
        "Stay hydrated and maintain strict form over heavy weight.",
        "Take 60-90 seconds rest between sets on multi-joint movements.",
    ]
    if goal == "lose weight":
        tips.append("Keep rest periods around 45-60 seconds to elevate calorie burn.")
    elif goal == "build muscle":
        tips.append("Aim for progressive overload: increase reps or weight gradually each week.")

    return {
        "summary": f"{days}-Day {place.capitalize()} Workout Plan for {goal.capitalize()}",
        "goal": goal,
        "place": place,
        "days_per_week": days,
        "schedule": schedule,
        "warnings": unique_warnings,
        "tips": tips,
    }