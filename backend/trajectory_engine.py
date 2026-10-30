from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression


def compute_trajectory(logs: list[dict], target_weight: float) -> dict:
    """
    Fits an Ordinary Least Squares (OLS) regression line on daily weight logs.
    Calculates rate of weight change, predicted goal date, and plateau detection.
    """
    # Extract only valid weight entries sorted chronologically
    valid_entries = []
    for log in logs:
        wt = log.get("weight_kg")
        dt_str = log.get("log_date")
        if wt is not None and dt_str:
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
                valid_entries.append((dt, float(wt)))
            except ValueError:
                continue

    valid_entries.sort(key=lambda x: x[0])

    # Insufficient data points for statistical regression
    if len(valid_entries) < 3:
        return {
            "status": "insufficient_data",
            "message": "At least 3 weight entries are required to calculate regression trajectory.",
            "data_points": len(valid_entries),
        }

    # Convert dates to days relative to first recorded day (X-axis)
    start_date = valid_entries[0][0]
    X_days = np.array([(entry[0] - start_date).days for entry in valid_entries]).reshape(-1, 1)
    y_weights = np.array([entry[1] for entry in valid_entries])

    # Fit Linear Regression Model
    model = LinearRegression()
    model.fit(X_days, y_weights)

    # Slope represents kg change per day
    daily_slope = float(model.coef_[0])
    weekly_rate = round(daily_slope * 7, 2)
    current_weight = y_weights[-1]

    # Calculate model goodness of fit (R-squared)
    r2_score = round(float(model.score(X_days, y_weights)), 3)

    # Plateau Detection: rolling slope close to 0 over recent days
    is_plateau = abs(weekly_rate) < 0.10

    # Project days to reach target weight: (Target - Current) / Daily_Slope
    weight_delta = target_weight - current_weight
    target_date_str = None
    days_to_goal = None

    # Check if user is actually moving toward their target
    moving_towards_target = (weight_delta < 0 and daily_slope < 0) or (weight_delta > 0 and daily_slope > 0)

    if moving_towards_target and abs(daily_slope) > 0.001:
        days_to_goal = int(abs(weight_delta / daily_slope))
        # Cap projected future date realistically (max 2 years)
        if days_to_goal <= 730:
            target_date = valid_entries[-1][0] + timedelta(days=days_to_goal)
            target_date_str = target_date.strftime("%Y-%m-%d")

    return {
        "status": "success",
        "current_weight_kg": current_weight,
        "target_weight_kg": target_weight,
        "weekly_rate_kg": weekly_rate,
        "days_to_target": days_to_goal,
        "predicted_target_date": target_date_str,
        "is_plateau": is_plateau,
        "model_r2_score": r2_score,
        "total_data_points": len(valid_entries),
    }