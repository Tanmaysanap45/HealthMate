import pytest
from trajectory_engine import compute_trajectory
from diet_optimizer import optimize_diet_plan
from workout_graph import find_safe_progression


# ==========================================
# 1. Tests for ML Trajectory Engine
# ==========================================
def test_trajectory_insufficient_data():
    """Verify that fewer than 3 logs return an insufficient data status."""
    logs = [
        {"log_date": "2026-03-01", "weight_kg": 75.0},
        {"log_date": "2026-03-02", "weight_kg": 74.8}
    ]
    result = compute_trajectory(logs, target_weight=70.0)
    assert result["status"] == "insufficient_data"
    assert result["data_points"] == 2


def test_trajectory_valid_weight_loss_prediction():
    """Verify OLS regression calculates a negative slope and projected date."""
    logs = [
        {"log_date": "2026-03-01", "weight_kg": 80.0},
        {"log_date": "2026-03-08", "weight_kg": 79.0},
        {"log_date": "2026-03-15", "weight_kg": 78.0},
        {"log_date": "2026-03-22", "weight_kg": 77.0}
    ]
    result = compute_trajectory(logs, target_weight=74.0)
    assert result["status"] == "success"
    assert result["weekly_rate_kg"] < 0
    assert result["days_to_target"] is not None
    assert result["predicted_target_date"] is not None
    assert result["model_r2_score"] > 0.90


def test_trajectory_plateau_detection():
    """Verify plateau flag triggers when weekly weight change is minimal."""
    logs = [
        {"log_date": "2026-03-01", "weight_kg": 75.0},
        {"log_date": "2026-03-08", "weight_kg": 75.0},
        {"log_date": "2026-03-15", "weight_kg": 75.02},
        {"log_date": "2026-03-22", "weight_kg": 74.98}
    ]
    result = compute_trajectory(logs, target_weight=70.0)
    assert result["status"] == "success"
    assert result["is_plateau"] is True


# ==========================================
# 2. Tests for Linear Programming Diet Optimizer
# ==========================================
def test_diet_optimizer_dairy_allergy_exclusion():
    """Verify that dairy items like Paneer and Greek Yogurt are strictly excluded."""
    result = optimize_diet_plan(
        daily_calories=2000,
        weight_kg=70.0,
        food_type="vegetarian",
        allergies="dairy"
    )
    assert result["status"] in ["optimized", "approximation"]
    meal_names = [m["food"].lower() for m in result["meals"]]
    assert not any("paneer" in name for name in meal_names)
    assert not any("yogurt" in name for name in meal_names)


def test_diet_optimizer_protein_constraint():
    """Verify that the optimizer achieves the minimum required protein target."""
    weight = 75.0
    result = optimize_diet_plan(
        daily_calories=2200,
        weight_kg=weight,
        food_type="non-vegetarian",
        allergies="none"
    )
    assert result["status"] == "optimized"
    assert result["achieved_protein"] >= (weight * 1.5)


# ==========================================
# 3. Tests for Biomechanical Graph Traversal
# ==========================================
def test_safe_progression_knee_pain():
    """Verify that BFS graph traversal prunes knee-stressing movements."""
    result = find_safe_progression(
        exercise_key="barbell_back_squat",
        user_conditions=["knee pain"]
    )
    assert result["status"] == "adapted"
    assert result["prescribed_exercise"] == "Bodyweight Box Squat"
    assert "Barbell Back Squat" in result["adaptation_path"]


def test_safe_progression_shoulder_injury():
    """Verify that overhead pressing adapts away from shoulder stress."""
    result = find_safe_progression(
        exercise_key="standing_overhead_press",
        user_conditions=["shoulder impingement"]
    )
    assert result["status"] == "adapted"
    assert result["prescribed_exercise"] == "Dumbbell / Cable Lateral Raises"