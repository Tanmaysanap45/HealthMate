"""Diet plan rules for HealthMate.

Simple "if this, then that" rules, so every choice can be explained.
The plan is built from the user's saved details.
The calorie numbers in the food list are rough, everyday estimates.
"""
import re

# (meal name, share of the daily calories)
MEALS = [("Breakfast", 0.25), ("Lunch", 0.35), ("Snack", 0.10), ("Dinner", 0.30)]

# type: "vegan" = suits everyone, "veg" = vegetarian and non-vegetarian, "nonveg" = non-vegetarian only
# tags: allergens (milk, egg, gluten, nuts, peanut, soy, fish) and flags (highsugar, highsalt, fried)
FOODS = {
    "Breakfast": [
        {"name": "Vegetable poha (1 plate)", "kcal": 280, "type": "vegan", "tags": []},
        {"name": "Idli (3) with sambar", "kcal": 260, "type": "vegan", "tags": []},
        {"name": "Moong dal chilla (2) with mint chutney", "kcal": 250, "type": "vegan", "tags": []},
        {"name": "Fruit bowl with a spoon of seeds", "kcal": 220, "type": "vegan", "tags": []},
        {"name": "Oats cooked with milk and fruit (1 bowl)", "kcal": 330, "type": "veg", "tags": ["milk", "gluten"]},
        {"name": "Vegetable upma (1 plate)", "kcal": 280, "type": "vegan", "tags": ["gluten"]},
        {"name": "Besan chilla (2) with curd", "kcal": 320, "type": "veg", "tags": ["milk"]},
        {"name": "Peanut poha (1 plate)", "kcal": 320, "type": "vegan", "tags": ["peanut"]},
        {"name": "Omelette (2 eggs) with 2 slices whole-wheat bread", "kcal": 330, "type": "nonveg", "tags": ["egg", "gluten"]},
        {"name": "Boiled eggs (2) with a fruit", "kcal": 230, "type": "nonveg", "tags": ["egg"]},
        {"name": "Banana milkshake with sugar (1 glass)", "kcal": 300, "type": "veg", "tags": ["milk", "highsugar"]},
    ],
    "Lunch": [
        {"name": "Brown rice, rajma and salad", "kcal": 520, "type": "vegan", "tags": []},
        {"name": "Chole (chickpeas) with brown rice and salad", "kcal": 540, "type": "vegan", "tags": []},
        {"name": "Vegetable khichdi with salad", "kcal": 450, "type": "vegan", "tags": []},
        {"name": "2 rotis, dal, vegetable sabzi and salad", "kcal": 520, "type": "vegan", "tags": ["gluten"]},
        {"name": "Paneer bhurji with 2 rotis and salad", "kcal": 560, "type": "veg", "tags": ["milk", "gluten"]},
        {"name": "Vegetable khichdi with curd", "kcal": 480, "type": "veg", "tags": ["milk"]},
        {"name": "Tofu stir-fry with rice", "kcal": 500, "type": "vegan", "tags": ["soy"]},
        {"name": "Chicken curry (100 g) with rice and salad", "kcal": 560, "type": "nonveg", "tags": []},
        {"name": "Fish curry with rice and vegetables", "kcal": 540, "type": "nonveg", "tags": ["fish"]},
        {"name": "Egg curry (2 eggs) with 2 rotis", "kcal": 520, "type": "nonveg", "tags": ["egg", "gluten"]},
    ],
    "Snack": [
        {"name": "Roasted chana (1 handful)", "kcal": 120, "type": "vegan", "tags": []},
        {"name": "Fruit (1 apple or orange)", "kcal": 90, "type": "vegan", "tags": []},
        {"name": "Sprouts salad (1 bowl)", "kcal": 130, "type": "vegan", "tags": []},
        {"name": "Apple with 10 almonds", "kcal": 160, "type": "vegan", "tags": ["nuts"]},
        {"name": "Buttermilk (1 glass) with roasted cumin", "kcal": 60, "type": "veg", "tags": ["milk"]},
        {"name": "Curd (1 cup) with seeds", "kcal": 130, "type": "veg", "tags": ["milk"]},
        {"name": "Boiled eggs (2)", "kcal": 140, "type": "nonveg", "tags": ["egg"]},
        {"name": "Roasted salted peanuts (small handful)", "kcal": 170, "type": "vegan", "tags": ["peanut", "highsalt"]},
        {"name": "Sweet lassi (1 glass)", "kcal": 220, "type": "veg", "tags": ["milk", "highsugar"]},
    ],
    "Dinner": [
        {"name": "Lentil soup with brown rice", "kcal": 400, "type": "vegan", "tags": []},
        {"name": "Moong dal with rice and salad", "kcal": 420, "type": "vegan", "tags": []},
        {"name": "Vegetable dalia (broken wheat) khichdi", "kcal": 400, "type": "vegan", "tags": ["gluten"]},
        {"name": "2 rotis, moong dal and salad", "kcal": 420, "type": "vegan", "tags": ["gluten"]},
        {"name": "Grilled paneer with sauteed vegetables and 1 roti", "kcal": 450, "type": "veg", "tags": ["milk", "gluten"]},
        {"name": "Tofu and vegetable stir-fry with 1 roti", "kcal": 420, "type": "vegan", "tags": ["soy", "gluten"]},
        {"name": "Grilled chicken (120 g) with sauteed vegetables and 1 roti", "kcal": 450, "type": "nonveg", "tags": ["gluten"]},
        {"name": "Baked fish with vegetables and a small portion of rice", "kcal": 430, "type": "nonveg", "tags": ["fish"]},
        {"name": "Egg bhurji (2 eggs) with 2 rotis and salad", "kcal": 430, "type": "nonveg", "tags": ["egg", "gluten"]},
    ],
}

# Words people write for allergies -> the food tags we remove
ALLERGY_WORDS = {
    "milk": ["milk"], "dairy": ["milk"], "lactose": ["milk"], "curd": ["milk"], "paneer": ["milk"],
    "cheese": ["milk"], "yogurt": ["milk"], "yoghurt": ["milk"], "butter": ["milk"],
    "egg": ["egg"], "eggs": ["egg"],
    "gluten": ["gluten"], "wheat": ["gluten"], "maida": ["gluten"],
    "peanut": ["peanut"], "peanuts": ["peanut"], "groundnut": ["peanut"], "groundnuts": ["peanut"],
    "nut": ["nuts", "peanut"], "nuts": ["nuts", "peanut"], "almond": ["nuts"], "almonds": ["nuts"],
    "cashew": ["nuts"], "cashews": ["nuts"], "walnut": ["nuts"], "walnuts": ["nuts"],
    "soy": ["soy"], "soya": ["soy"], "tofu": ["soy"],
    "fish": ["fish"], "seafood": ["fish"], "shellfish": ["fish"], "prawn": ["fish"], "prawns": ["fish"],
}
FLAGS = {"highsugar", "highsalt", "fried"}
NO_ALLERGY = {"", "none", "no", "nil", "nothing", "na", "n/a", "not applicable"}

PROTEIN_PER_KG = {"lose weight": 1.6, "build muscle": 1.8, "stay fit": 1.2}


def parse_allergies(text):
    """Turn the allergy text into a set of tags to avoid, plus words we could not match."""
    text = (text or "").lower().strip()
    if text in NO_ALLERGY:
        return set(), []
    tags, unknown = set(), []
    for part in re.split(r"[,;/&\n]|\band\b", text):
        part = part.strip()
        if part in NO_ALLERGY:
            continue
        found = False
        for word in re.findall(r"[a-z]+", part):
            if word in ALLERGY_WORDS:
                tags.update(ALLERGY_WORDS[word])
                found = True
        if not found:
            unknown.append(part)
    return tags, unknown


def allowed(food, food_type, avoid):
    if food_type == "vegan" and food["type"] != "vegan":
        return False
    if food_type == "vegetarian" and food["type"] == "nonveg":
        return False
    return not (set(food["tags"]) & avoid)


def servings_for(target, base):
    return min(max(round(target / base * 2) / 2, 0.5), 2.5)


def generate_diet(profile):
    calories = int(round(float(profile.get("daily_calories") or 1800)))
    calories = min(max(calories, 1200), 4000)
    goal = profile.get("goal") or "stay fit"
    if goal not in PROTEIN_PER_KG:
        goal = "stay fit"
    food_type = profile.get("food_type") or "vegetarian"
    weight = float(profile.get("weight_kg") or 65)
    diagnosis = (profile.get("diagnosis") or "none").lower()

    avoid, warnings = set(), []

    # 1. Allergies: remove every food that contains the allergen
    allergy_tags, unknown = parse_allergies(profile.get("food_allergies"))
    if allergy_tags:
        avoid |= allergy_tags
        names = ", ".join(sorted(allergy_tags))
        warnings.append({"level": "info", "text": "We removed foods that contain: " + names + ". Always read food labels and ask about ingredients."})
    for word in unknown:
        warnings.append({"level": "high", "text": "We could not match your allergy \"" + word + "\" to our food list. Please check every food yourself before you eat it."})

    # 2. Diagnosis
    if diagnosis == "diabetes":
        avoid.add("highsugar")
        warnings.append({"level": "info", "text": "Diabetes: sugary foods are kept out of your plan. Eat at regular times, choose whole grains, and ask your doctor how much carbohydrate is right for you."})
    elif diagnosis == "high blood pressure":
        avoid.add("highsalt")
        warnings.append({"level": "high", "text": "High blood pressure: keep salt below 5 g (about 1 teaspoon) a day, and avoid pickle, papad and salted snacks. Salty foods are kept out of your plan. Check with your doctor."})
    elif diagnosis == "heart problem":
        avoid.update(["highsalt", "fried"])
        warnings.append({"level": "high", "text": "Heart problem: fried and salty foods are kept out of your plan. Please follow your doctor's diet advice first."})
    elif diagnosis == "thyroid problem":
        warnings.append({"level": "info", "text": "Thyroid problem: ask your doctor when to take your medicine in relation to meals."})
    elif diagnosis not in ("none", ""):
        warnings.append({"level": "info", "text": "You told us about a diagnosis. Please ask your doctor or a dietitian if this plan is right for you."})

    # 3. Protein, fat and carbohydrate (in grams)
    protein = min(weight * PROTEIN_PER_KG[goal], 0.30 * calories / 4)
    fat = 0.25 * calories / 9
    carbs = (calories - protein * 4 - fat * 9) / 4
    water = min(max(round(weight * 0.035 * 2) / 2, 2.0), 4.0)

    # 4. Meals
    meals = []
    for name, share in MEALS:
        target = round(calories * share)
        pool = [f for f in FOODS[name] if allowed(f, food_type, avoid)]
        # foods closest to this meal's calories come first, so portions stay sensible
        # sugary, salty and fried foods come last, so they only appear if there is nothing else
        pool.sort(key=lambda f: abs(f["kcal"] - target) + (1000 if set(f["tags"]) & FLAGS else 0))
        options = []
        for f in pool[:3]:
            s = servings_for(target, f["kcal"])
            options.append({
                "name": f["name"],
                "servings": s,
                "kcal": int(round(f["kcal"] * s / 5) * 5),
            })
        if len(options) < 2:
            warnings.append({"level": "high", "text": "Very few foods match your rules for " + name.lower() + ". Please ask a dietitian for more choices."})
        meals.append({"name": name, "kcal": target, "share": int(share * 100), "options": options})

    tips = ["Pick ONE option for each meal. You can choose a different option every day."]
    if goal == "lose weight":
        tips.append("Fill half your plate with vegetables, eat slowly, and avoid sugary drinks.")
    elif goal == "build muscle":
        tips.append("Add a protein food to every meal, such as dal, paneer, eggs, chicken, fish or tofu.")
    else:
        tips.append("Keep your meal times regular and your portions steady.")
    tips.append("Drink about " + str(water) + " litres of water a day.")
    tips.append("Servings are rough guides. If you stay hungry or very tired, talk to a doctor or dietitian.")

    return {
        "summary": goal.capitalize() + " diet: about " + str(calories) + " kcal a day, " + food_type + " food.",
        "goal": goal,
        "calories": calories,
        "protein_g": int(round(protein)),
        "carbs_g": int(round(carbs)),
        "fat_g": int(round(fat)),
        "water_l": water,
        "warnings": warnings,
        "meals": meals,
        "tips": tips,
    }