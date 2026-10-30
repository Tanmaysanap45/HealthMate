import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DARK = colors.HexColor("#11120d")
GREEN = colors.HexColor("#4d6600")
GREY = colors.HexColor("#5f6155")
LINE = colors.HexColor("#d7dbc8")

_styles = getSampleStyleSheet()
TITLE = ParagraphStyle("ReportTitle", parent=_styles["Title"], textColor=DARK, fontSize=22, leading=26, alignment=0, spaceAfter=4)
H2 = ParagraphStyle("ReportH2", parent=_styles["Heading2"], textColor=GREEN, fontSize=14, spaceBefore=16, spaceAfter=6)
BODY = ParagraphStyle("ReportBody", parent=_styles["BodyText"], fontSize=10, leading=14, textColor=DARK)
BOLD = ParagraphStyle("ReportBold", parent=BODY, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=2)
HINT = ParagraphStyle("ReportHint", parent=BODY, fontSize=9, leading=12, textColor=GREY, spaceAfter=4)
INDENT = ParagraphStyle("ReportIndent", parent=BODY, leftIndent=12)
BULLET = ParagraphStyle("ReportBullet", parent=BODY, leftIndent=12)
SMALL = ParagraphStyle("ReportSmall", parent=BODY, fontSize=8.5, leading=11, textColor=GREY)
CELL = ParagraphStyle("ReportCell", parent=BODY, fontSize=9.5, leading=12)
CELL_HEAD = ParagraphStyle("ReportCellHead", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)


def p(text, style=BODY):
    return Paragraph(escape(str(text)), style)


def num(value, digits=0):
    """Returns the number rounded, or '-' if the value is missing."""
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return "-"


def bmi_label(bmi):
    b = num(bmi, 1)
    if b == "-":
        return "Not available"
    if b < 18.5:
        return "Underweight"
    if b < 25:
        return "Healthy range"
    if b < 30:
        return "Overweight"
    return "Obese range"


def table(rows, widths):
    """Builds a table. The first row is the header."""
    data = []
    for r, row in enumerate(rows):
        style = CELL_HEAD if r == 0 else CELL
        data.append([Paragraph(escape(str(cell)), style) for cell in row])

    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def build_advice(profile, workout, diet):
    """Simple rule-based advice. No AI is used."""
    tips = []
    bmi = num(profile.get("bmi"), 1)
    weight = num(profile.get("weight_kg"), 1)
    target = num(profile.get("target_weight_kg"), 1)
    goal = str(profile.get("goal") or "").lower()

    if bmi != "-":
        if bmi < 18.5:
            tips.append("Your BMI is below the healthy range. Make sure you eat enough, and talk to a doctor if you lose weight without trying.")
        elif bmi < 25:
            tips.append("Your BMI is in the healthy range. Keep your current habits steady.")
        elif bmi < 30:
            tips.append("Your BMI is slightly above the healthy range. Small, steady changes to food and daily movement work best.")
        else:
            tips.append("Your BMI is above the healthy range. A gradual plan, checked with a doctor or dietitian, is the safest way to reach your goal.")

    if weight != "-" and target != "-":
        diff = round(weight - target, 1)
        if diff > 0:
            tips.append(str(diff) + " kg to go to reach your target. A loss of about 0.25 to 0.5 kg per week is a safe pace.")
        elif diff < 0:
            tips.append("You are " + str(abs(diff)) + " kg below your target weight. Check that you are eating enough to meet your goal.")
        else:
            tips.append("You have reached your target weight. Focus on keeping it steady.")

    if "lose" in goal:
        tips.append("Keep a small daily calorie deficit, walk regularly, and avoid sugary drinks.")
    elif "build" in goal or "muscle" in goal:
        tips.append("Eat enough protein at every meal, and increase your training weights slowly each week.")
    else:
        tips.append("Keep your meal times regular and aim for a steady sleep schedule.")

    tips.append("Sleep 7 to 9 hours a night. Your body recovers and adapts to training during sleep.")
    tips.append("Drink water through the day, and stop an exercise if you feel dizzy or have sharp pain.")

    condition = str(profile.get("body_condition") or "none").lower()
    diagnosis = str(profile.get("diagnosis") or "none").lower()
    if condition != "none" or diagnosis != "none":
        tips.append("You listed a health condition or injury. Check your plan with a doctor or physiotherapist before you start a new routine.")

    if workout:
        tips.extend(workout.get("tips", []))
    if diet:
        tips.extend(diet.get("tips", []))

    return tips


def build_report_pdf(profile, workout, diet):
    """Creates the PDF and returns it as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="HealthMate Personal Report",
        author="HealthMate",
    )
    story = []

    story.append(p("HealthMate Personal Report", TITLE))

    # 1. Personal information
    story.append(p("1. Your information", H2))
    story.append(table([
        ["Item", "Value"],
        ["Goal", profile.get("goal") or "-"],
        ["Age", profile.get("age") or "-"],
        ["Current weight", str(num(profile.get("weight_kg"), 1)) + " kg"],
        ["Target weight", str(num(profile.get("target_weight_kg"), 1)) + " kg"],
        ["BMI", str(num(profile.get("bmi"), 1)) + " (" + bmi_label(profile.get("bmi")) + ")"],
        ["Daily calorie target", str(num(profile.get("daily_calories"))) + " kcal"],
        ["Diet style", profile.get("food_type") or "-"],
        ["Food allergies", profile.get("food_allergies") or "None"],
        ["Workout place", profile.get("workout_place") or "-"],
        ["Injuries or conditions", profile.get("body_condition") or "None"],
    ], [60 * mm, 110 * mm]))

    # 2. Workout plan
    story.append(p("2. Workout plan", H2))
    if workout:
        story.append(p(workout.get("summary", ""), BODY))
        for day in workout.get("schedule", []):
            story.append(p(str(day.get("day", "")) + ": " + str(day.get("focus", "")), BOLD))
            rows = [["Exercise", "Sets and reps", "Target", "Intensity"]]
            for ex in day.get("exercises", []):
                rows.append([ex.get("name", ""), ex.get("sets", ""), ex.get("type", ""), ex.get("intensity", "")])
            story.append(table(rows, [62 * mm, 50 * mm, 36 * mm, 22 * mm]))
    else:
        story.append(p("No workout plan found yet.", BODY))

    # 3. Diet plan
    story.append(p("3. Diet plan", H2))
    if diet:
        story.append(p(diet.get("summary", ""), BODY))
        story.append(Spacer(1, 6))
        story.append(table([
            ["Calories", "Protein", "Carbs", "Fat", "Water"],
            [
                str(diet.get("calories", "-")) + " kcal",
                str(diet.get("protein_g", "-")) + " g",
                str(diet.get("carbs_g", "-")) + " g",
                str(diet.get("fat_g", "-")) + " g",
                str(diet.get("water_l", "-")) + " L",
            ],
        ], [34 * mm] * 5))
        for meal in diet.get("meals", []):
            story.append(p(str(meal.get("name", "")) + ": about " + str(meal.get("kcal", "")) + " kcal (" + str(meal.get("share", "")) + "% of your day)", BOLD))
            options = meal.get("options", [])
            if not options:
                story.append(p("No safe foods found. Please ask a dietitian.", INDENT))
                continue
            story.append(p("Choose ONE option for this meal.", HINT))
            for index, o in enumerate(options, start=1):
                story.append(p(
                    "Option " + str(index) + ": " + str(o.get("name", "")) + " - "
                    + str(o.get("servings", "")) + " serving(s), about " + str(o.get("kcal", "")) + " kcal",
                    INDENT,
                ))
    else:
        story.append(p("No diet plan found yet.", BODY))

    # 4. Advice
    story.append(p("4. Advice for you", H2))
    for tip in build_advice(profile, workout, diet):
        story.append(p("- " + tip, BULLET))

    # 5. Important notes from the plans
    warnings = []
    if workout:
        warnings += workout.get("warnings", [])
    if diet:
        warnings += diet.get("warnings", [])
    if warnings:
        story.append(p("5. Important notes", H2))
        for w in warnings:
            story.append(p("- " + str(w.get("text", "")), BULLET))

    story.append(Spacer(1, 14))
    story.append(p("HealthMate estimates are general guidelines, not medical advice. If you have medical concerns or allergies, review this report with a licensed doctor or dietitian.", SMALL))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()