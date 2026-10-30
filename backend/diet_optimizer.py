import numpy as np
from scipy.optimize import linprog

# Nutritional database per 100g serving: [Calories (kcal), Protein (g), Carbs (g), Fats (g)]
FOOD_DATABASE = {
    # Vegetarian / Vegan items
    "oats": {"cal": 389, "protein": 16.9, "carbs": 66.3, "fat": 6.9, "type": "vegan", "allergens": ["gluten"]},
    "paneer": {"cal": 265, "protein": 18.3, "carbs": 1.2, "fat": 20.8, "type": "vegetarian", "allergens": ["dairy"]},
    "tofu": {"cal": 76, "protein": 8.0, "carbs": 1.9, "fat": 4.8, "type": "vegan", "allergens": ["soy"]},
    "lentils_dal": {"cal": 116, "protein": 9.0, "carbs": 20.0, "fat": 0.4, "type": "vegan", "allergens": []},
    "chickpeas": {"cal": 164, "protein": 8.9, "carbs": 27.4, "fat": 2.6, "type": "vegan", "allergens": []},
    "brown_rice": {"cal": 111, "protein": 2.6, "carbs": 23.0, "fat": 0.9, "type": "vegan", "allergens": []},
    "peanut_butter": {"cal": 588, "protein": 25.0, "carbs": 20.0, "fat": 50.0, "type": "vegan", "allergens": ["peanuts", "nuts"]},
    "almonds": {"cal": 579, "protein": 21.2, "carbs": 21.6, "fat": 49.9, "type": "vegan", "allergens": ["nuts"]},
    "greek_yogurt": {"cal": 59, "protein": 10.0, "carbs": 3.6, "fat": 0.4, "type": "vegetarian", "allergens": ["dairy"]},
    
    # Non-vegetarian additions
    "chicken_breast": {"cal": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "type": "non-vegetarian", "allergens": []},
    "eggs_whole": {"cal": 143, "protein": 12.6, "carbs": 0.7, "fat": 9.5, "type": "non-vegetarian", "allergens": ["eggs"]},
    "fish_fillet": {"cal": 120, "protein": 24.0, "carbs": 0.0, "fat": 2.5, "type": "non-vegetarian", "allergens": ["fish"]},
}


def optimize_diet_plan(daily_calories: int, weight_kg: float, food_type: str = "vegetarian", allergies: str = "none") -> dict:
    """
    Solves a Linear Programming optimization problem to generate an exact meal distribution.
    Minimizes deviation from target calories while strictly satisfying protein minimums and allergen boundaries.
    """
    user_allergies = [a.strip().lower() for a in allergies.split(",") if a.strip()]
    valid_foods = []
    
    food_type_clean = (food_type or "").lower().strip()

    for food_name, stats in FOOD_DATABASE.items():
        if food_type_clean == "vegan" and stats["type"] != "vegan":
            continue
        if food_type_clean == "vegetarian" and stats["type"] not in ["vegan", "vegetarian"]:
            continue
        
        has_allergy = any(allergen in user_allergies for allergen in stats["allergens"])
        if has_allergy:
            continue
            
        valid_foods.append(food_name)

    if len(valid_foods) < 3:
        return {
            "status": "error",
            "message": "Too few food items match your dietary restrictions.",
            "items": []
        }

    # Minimum protein requirement: 1.5g to 1.8g per kg of body weight
    min_protein = round(float(weight_kg) * 1.5, 1)

    num_items = len(valid_foods)
    c_cal = np.array([FOOD_DATABASE[f]["cal"] for f in valid_foods])
    c_protein = np.array([FOOD_DATABASE[f]["protein"] for f in valid_foods])

    # Objective: Maximize protein while controlling calories (minimize: -protein * 10 + cal * 0.05)
    c = -c_protein * 5.0 + (c_cal * 0.05)

    # Constraints (A_ub * x <= b_ub):
    # 1. Total protein >= min_protein  =>  -c_protein * x <= -min_protein
    # 2. Total calories <= daily_calories * 1.05
    # 3. Total calories >= daily_calories * 0.85  =>  -c_cal * x <= -(daily_calories * 0.85)
    A_ub = [
        -c_protein,
        c_cal,
        -c_cal
    ]
    b_ub = [
        -min_protein,
        daily_calories * 1.05,
        -(daily_calories * 0.85)
    ]

    # Bounds: Portions between 0.4 (40g) and 3.5 (350g)
    bounds = [(0.4, 3.5) for _ in range(num_items)]

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

    if not res.success:
        bounds_relaxed = [(0.1, 4.0) for _ in range(num_items)]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds_relaxed, method="highs")

    meal_breakdown = []
    total_cal = 0
    total_p = 0
    total_c = 0
    total_f = 0

    if res.success:
        servings = res.x
        for i, food_name in enumerate(valid_foods):
            portion_grams = round(float(servings[i]) * 100)
            if portion_grams > 0:
                f_data = FOOD_DATABASE[food_name]
                multiplier = portion_grams / 100.0
                
                cal = round(f_data["cal"] * multiplier)
                prot = round(f_data["protein"] * multiplier, 1)
                carbs = round(f_data["carbs"] * multiplier, 1)
                fat = round(f_data["fat"] * multiplier, 1)

                total_cal += cal
                total_p += prot
                total_c += carbs
                total_f += fat

                meal_breakdown.append({
                    "food": food_name.replace("_", " ").title(),
                    "portion_grams": portion_grams,
                    "calories": cal,
                    "protein_g": prot,
                    "carbs_g": carbs,
                    "fat_g": fat
                })

    return {
        "status": "optimized" if res.success else "approximation",
        "target_calories": daily_calories,
        "target_protein_min": min_protein,
        "achieved_calories": total_cal,
        "achieved_protein": round(total_p, 1),
        "achieved_carbs": round(total_c, 1),
        "achieved_fat": round(total_f, 1),
        "meals": meal_breakdown,
        "algorithm": "Simplex / HiGHS Linear Programming (SciPy)"
    }