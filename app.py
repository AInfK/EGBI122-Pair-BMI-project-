
import gradio as gr
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta

# -----------------------------
# In-memory store (temporary)
# -----------------------------
users = {}
SESSION = {"current_user": None}

# -----------------------------
# Utilities
# -----------------------------
def ymd(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def today_str() -> str:
    return ymd(date.today())

def parse_date_str(s: str):
    if not s:
        return None
    s = s.strip()
    try:
        dt = datetime.strptime(s, "%Y-%m-%d").date()
        return ymd(dt)
    except Exception:
        return None

def to_float(x):
    try:
        return float(x)
    except Exception:
        return None

def unit_to_metric(unit, height_val, weight_val):
    h = to_float(height_val)
    w = to_float(weight_val)
    if h is None or w is None:
        return None, None
    if unit == "Metric (cm, kg)":
        return h, w
    return h * 2.54, w * 0.453592

def calc_bmi(h_cm, w_kg):
    if h_cm is None or w_kg is None or h_cm <= 0:
        return None
    h_m = h_cm / 100.0
    return w_kg / (h_m ** 2)

def bmi_category(bmi):
    if bmi is None:
        return "-"
    if bmi < 18.5: return "Underweight"
    if bmi < 25:   return "Normal"
    if bmi < 30:   return "Overweight"
    return "Obese"

def ensure_user(username):
    if username not in users:
        users[username] = {
            "bmi_records": {},
            "tdee_records": {},
            "food_log": {},
            # per-user food tables (start with defaults)
            "foods": {
                "MAIN": {
                    "-": 0,
                    "Pad Thai (1 plate)": 545,
                    "Khao Man Gai": 600,
                    "Fried Rice": 520,
                    "Chicken Breast (100g)": 165,
                    "Grilled Salmon (100g)": 208,
                    "Beef (lean, 100g)": 250,
                    "Rice (1 cup)": 206,
                    "Spaghetti (1 cup)": 220,
                    "Green Curry Chicken": 320,
                },
                "DESSERT": {
                    "-": 0,
                    "Sticky Rice with Mango": 380,
                    "Ice Cream (100g)": 207,
                    "Brownie": 250,
                    "Fruit (Apple 100g)": 52,
                    "Fruit (Banana 100g)": 89,
                },
                "BEVERAGE": {
                    "-": 0,
                    "Water": 0,
                    "Coffee (black)": 5,
                    "Milk (1 cup)": 150,
                    "Thai Iced Tea": 250,
                    "Bubble Tea": 340,
                    "Coke (1 can)": 140,
                }
            }
        }

# -----------------------------
# Charts
# -----------------------------
def plot_bmi_series(series):
    # BMI chart w/ category bands + labels
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7.6, 3.8))
    ax = plt.gca()
    ax.axhspan(0, 18.5, color="#6ec1ff22")
    ax.axhspan(18.5, 25, color="#39ff1433")
    ax.axhspan(25, 30, color="#ffdd0033")
    ax.axhspan(30, 80, color="#ff3b3b2a")
    ax.set_title("BMI Over Time (category bands)")
    ax.set_ylabel("BMI")
    ax.grid(True, linestyle="--", alpha=0.35)
    if series:
        items = sorted(series.items(), key=lambda kv: kv[0])
        xs = [k for k, _ in items]
        ys = [v for _, v in items]
        ax.plot(xs, ys, marker="o", linewidth=2)
        for x, y in zip(xs, ys):
            cat = bmi_category(y)
            ax.annotate(f"{y:.1f}\\n{cat}", (x, y), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=9)
        plt.xticks(rotation=25, ha="right")
    else:
        ax.text(0.5, 0.5, "No BMI data yet", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, alpha=0.7)
    plt.tight_layout()
    path = "/tmp/bmi_series.png"
    plt.savefig(path); plt.close()
    return path

def compute_target_from_goal(tdee: float, goal: str) -> float:
    if not tdee or tdee <= 0:
        return 0.0
    # simple, clear multipliers
    m = {"Lose (-20%)": 0.80, "Maintenance (0%)": 1.00, "Gain (+15%)": 1.15}.get(goal, 1.00)
    return tdee * m

def plot_food_week(log, ref_date_str, target_kcal):
    # 7-day window ending at selected date; target line & value labels
    import matplotlib.pyplot as plt
    if ref_date_str:
        try:
            ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d").date()
        except Exception:
            ref_date = date.today()
    else:
        ref_date = date.today()
    days = [(ref_date - timedelta(days=i)) for i in range(6, -1, -1)]
    labels = [ymd(d) for d in days]
    vals = [log.get(lbl, 0) for lbl in labels]

    plt.figure(figsize=(7.6, 3.8))
    ax = plt.gca()
    bars = ax.bar(labels, vals, color='Orange')
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    plt.xticks(rotation=25, ha="right")
    ax.set_ylabel("Calories (kcal)")
    ax.set_title(f"Daily Calories — {labels[0]} to {labels[-1]}")

    # target line
    if target_kcal and target_kcal > 0:
        ax.axhline(target_kcal, linestyle="--", linewidth=2)
      
    # labels on bars
    for b in bars:
        v = b.get_height()
        ax.annotate(f"{v:.0f}", (b.get_x() + b.get_width()/2, v),
                    ha="center", va="bottom", fontsize=9, xytext=(0, 3),
                    textcoords="offset points")
    plt.tight_layout()
    path = "/tmp/food_week.png"
    plt.savefig(path); plt.close()
    return path

# -----------------------------
# Login helpers
# -----------------------------
def _choices_bmi(user): return sorted(users[user]["bmi_records"].keys())
def _choices_tdee(user): return sorted(users[user]["tdee_records"].keys())

def _food_choices(user):
    f = users[user]["foods"]
    return list(f["MAIN"].keys()), list(f["DESSERT"].keys()), list(f["BEVERAGE"].keys())

# -----------------------------
# Login / Logout (unchanged behavior)
# -----------------------------
def do_login(username):
    username = (username or "").strip()
    if not username:
        gr.Error("Please enter a username.")
        # keep output shape consistent with wiring below
        blank_foods = [gr.update(choices=[])] * 9
        return (
            gr.update(value=None),
            gr.update(visible=False),
            "Please enter a username.",
            None,
            gr.update(choices=[]),
            gr.update(choices=[]),
            gr.update(choices=[]),
            gr.update(value=""),
            *blank_foods
        )
    SESSION["current_user"] = username
    ensure_user(username)
    bmi_series = {k: v["bmi"] for k, v in users[username]["bmi_records"].items()}
    bmi_plot_path = plot_bmi_series(bmi_series)
    # food choices for 9 dropdowns (B/L/D × Main/Dessert/Beverage)
    main_c, des_c, bev_c = _food_choices(username)
    food_updates = [
        gr.update(choices=main_c), gr.update(choices=des_c), gr.update(choices=bev_c),  # Breakfast
        gr.update(choices=main_c), gr.update(choices=des_c), gr.update(choices=bev_c),  # Lunch
        gr.update(choices=main_c), gr.update(choices=des_c), gr.update(choices=bev_c),  # Dinner
    ]
    gr.Info(f"Welcome, {username}!")
    return (
        gr.update(value=username),
        gr.update(visible=True),
        f"Welcome, **{username}**!",
        bmi_plot_path,
        gr.update(choices=_choices_bmi(username)),   # Tab1 mirror list
        gr.update(choices=_choices_bmi(username)),   # Tab2 BMI-date dropdown
        gr.update(choices=_choices_tdee(username)),  # Tab3 TDEE-date dropdown
        gr.update(value=""),                         # Tab2 output clear
        *food_updates
    )

def do_logout():
    SESSION["current_user"] = None
    blank_foods = [gr.update(choices=[])] * 9
    gr.Info("Logged out.")
    return (
        gr.update(value=""),
        gr.update(visible=False),
        "Logged out.",
        None,
        gr.update(choices=[]),
        gr.update(choices=[]),
        gr.update(choices=[]),
        gr.update(value=""),
        *blank_foods
    )

# -----------------------------
# Tab 1 — BMI (same as your last version)
# -----------------------------
ALLOWED = {"h_cm_min": 100, "h_cm_max": 250, "w_kg_min": 30, "w_kg_max": 200, "bmi_min": 10, "bmi_max": 70}

def bmi_add_record(unit, height_in, weight_in, date_text, confirm_out_of_range):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first.")
        return ("Please login first.", None, gr.update(choices=[]), gr.update(choices=[]),
                gr.update(choices=[]), plot_bmi_series({}), gr.update(visible=False, value=None))
    d_str = parse_date_str(date_text)
    if d_str is None:
        gr.Warning("Enter a valid date in YYYY-MM-DD format.")
        return ("Invalid date format.", None, gr.update(choices=_choices_bmi(user)),
                gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_tdee(user)),
                plot_bmi_series({k:v["bmi"] for k,v in users[user]["bmi_records"].items()}),
                gr.update(visible=False, value=None))
    h_cm, w_kg = unit_to_metric(unit, height_in, weight_in)
    if h_cm is None or w_kg is None:
        gr.Warning("Height/Weight must be numbers.")
        return ("Height/Weight must be numbers.", None, gr.update(choices=_choices_bmi(user)),
                gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_tdee(user)),
                plot_bmi_series({k:v["bmi"] for k,v in users[user]["bmi_records"].items()}),
                gr.update(visible=False, value=None))
    if d_str in users[user]["bmi_records"]:
        gr.Warning(f"Data already exists on {d_str}. Clear it first to enter again.")
        return (f"You already have data on {d_str}. Clear it first to enter again.", None,
                gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_bmi(user)),
                gr.update(choices=_choices_tdee(user)),
                plot_bmi_series({k:v["bmi"] for k,v in users[user]["bmi_records"].items()}),
                gr.update(visible=False, value=None))
    bmi_val = calc_bmi(h_cm, w_kg)
    if bmi_val is None:
        gr.Error("Unable to compute BMI. Check your inputs.")
        return ("Unable to compute BMI.", None, gr.update(choices=_choices_bmi(user)),
                gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_tdee(user)),
                plot_bmi_series({k:v["bmi"] for k,v in users[user]["bmi_records"].items()}),
                gr.update(visible=False, value=None))
    out_of_range = not (ALLOWED["h_cm_min"] <= h_cm <= ALLOWED["h_cm_max"]) or \
                   not (ALLOWED["w_kg_min"] <= w_kg <= ALLOWED["w_kg_max"]) or \
                   not (ALLOWED["bmi_min"] <= bmi_val <= ALLOWED["bmi_max"])
    if out_of_range and confirm_out_of_range is None:
        gr.Warning("Value looks out of the allowed range. Confirm True/False, then click Save again.")
        return ("Please confirm out-of-range entry.", None, gr.update(choices=_choices_bmi(user)),
                gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_tdee(user)),
                plot_bmi_series({k:v["bmi"] for k,v in users[user]["bmi_records"].items()}),
                gr.update(visible=True, value=None))
    if out_of_range and confirm_out_of_range is False:
        gr.Info("Data NOT saved. Re-enter within allowed ranges.")
        return ("Data NOT saved. Use: Height 100–250 cm, Weight 30–200 kg, BMI 10–70.", None,
                gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_bmi(user)),
                gr.update(choices=_choices_tdee(user)),
                plot_bmi_series({k:v["bmi"] for k,v in users[user]["bmi_records"].items()}),
                gr.update(visible=False, value=None))

    users[user]["bmi_records"][d_str] = {"h_cm": round(h_cm,2), "w_kg": round(w_kg,2), "bmi": round(bmi_val,2)}
    cat = bmi_category(bmi_val)
    msg = f"Saved for {d_str}: Height {h_cm:.1f} cm, Weight {w_kg:.1f} kg ⇒ BMI **{bmi_val:.1f}** ({cat})."
    if out_of_range and confirm_out_of_range is True:
        msg += " **You gotta be kidding me.**"
    gr.Info("BMI saved.")
    series = {k:v["bmi"] for k,v in users[user]["bmi_records"].items()}
    return (msg, round(bmi_val,2), gr.update(choices=_choices_bmi(user), value=d_str),
            gr.update(choices=_choices_bmi(user), value=d_str), gr.update(choices=_choices_tdee(user)),
            plot_bmi_series(series), gr.update(visible=False, value=None))

def bmi_view_on_date(date_text):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first."); return "Please login first."
    d_str = parse_date_str(date_text)
    if d_str is None:
        gr.Warning("Enter a valid date (YYYY-MM-DD)."); return "Invalid date."
    rec = users[user]["bmi_records"].get(d_str)
    if not rec:
        gr.Info("No data on this date — please record your BMI first.")
        return "No data on this date — please record your BMI first."
    return f"{d_str}: Height {rec['h_cm']} cm, Weight {rec['w_kg']} kg, BMI **{rec['bmi']}** ({bmi_category(rec['bmi'])})."

def bmi_clear_day(date_text):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first."); return ("Please login first.", plot_bmi_series({}),
                                                 gr.update(choices=[]), gr.update(choices=[]), gr.update(choices=[]))
    d_str = parse_date_str(date_text)
    if d_str is None:
        gr.Warning("Enter a valid date (YYYY-MM-DD).")
        return ("Invalid date.", plot_bmi_series({k:v['bmi'] for k,v in users[user]['bmi_records'].items()}),
                gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_bmi(user)),
                gr.update(choices=_choices_tdee(user)))
    if d_str in users[user]["bmi_records"]:
        users[user]["bmi_records"].pop(d_str, None)
        users[user]["tdee_records"].pop(d_str, None)
        gr.Info(f"Cleared BMI (and linked TDEE) on {d_str}."); msg = f"Cleared BMI (and linked TDEE) on {d_str}."
    else:
        gr.Info("Nothing to clear for that date."); msg = "Nothing to clear for that date."
    series = {k:v["bmi"] for k,v in users[user]["bmi_records"].items()}
    return (msg, plot_bmi_series(series), gr.update(choices=_choices_bmi(user)),
            gr.update(choices=_choices_bmi(user)), gr.update(choices=_choices_tdee(user)))

# -----------------------------
# Tab 2 — BMR/TDEE (unchanged behavior from your last build)
# -----------------------------
ACTIVITY_FACTORS = {
    "Sedentary (little/no exercise)": 1.2,
    "Light (1–3 days/wk)": 1.375,
    "Moderate (3–5 days/wk)": 1.55,
    "Active (6–7 days/wk)": 1.725,
    "Very active (hard exercise)": 1.9
}

def hb_bmr(gender, age, h_cm, w_kg):
    if gender == "Male":
        return 88.362 + 13.397*w_kg + 4.799*h_cm - 5.677*age
    else:
        return 447.593 + 9.247*w_kg + 3.098*h_cm - 4.330*age

def t2_on_date_change(bmi_date_choice):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first.")
        return ("Please login first.", gr.update(value=None), gr.update(value=None), gr.update(value=""))
    if not bmi_date_choice:
        gr.Warning("Pick a BMI date from Tab 1.")
        return ("Pick a BMI date from Tab 1.", gr.update(value=None), gr.update(value=None), gr.update(value=""))
    rec = users[user]["bmi_records"].get(bmi_date_choice)
    if not rec:
        gr.Warning("No BMI data on that date — record in Tab 1 first.")
        return ("No BMI data on that date — record in Tab 1 first.", gr.update(value=None), gr.update(value=None), gr.update(value=bmi_date_choice))
    gr.Info(f"Loaded height/weight from {bmi_date_choice}.")
    return (f"Loaded from Tab 1 ({bmi_date_choice}).", gr.update(value=rec["h_cm"]), gr.update(value=rec["w_kg"]), gr.update(value=bmi_date_choice))

def t2_compute_and_save(t2_date_locked, gender, age, activity, height_cm, weight_kg, confirm_age_ok):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first.")
        return ("Please login first.", gr.update(value=""), gr.update(choices=_choices_tdee("n/a")), gr.update(visible=False, value=None))
    missing = []
    if gender not in ("Male", "Female"): missing.append("gender")
    if activity not in ACTIVITY_FACTORS: missing.append("activity level")
    try:
        age_val = int(age)
    except Exception:
        age_val = None; missing.append("age")
    if height_cm in (None, "") or weight_kg in (None, ""): missing.append("height/weight")
    d_str = parse_date_str(t2_date_locked)
    if d_str is None: missing.append("BMI date (select in dropdown)")
    if missing:
        gr.Warning("Please fill required fields: " + ", ".join(missing))
        return (f"Please fill the following first: {', '.join(missing)}.", gr.update(value=""), gr.update(choices=_choices_tdee(user)), gr.update(visible=False, value=None))
    # Age check (10–80)
    out_age = (age_val is None) or (age_val < 10 or age_val > 80)
    if out_age and confirm_age_ok is None:
        gr.Warning("Age seems out of the allowed range (10–80). Is this correct? Confirm True/False, then click again.")
        return ("Please confirm your age.", gr.update(value=""), gr.update(choices=_choices_tdee(user)), gr.update(visible=True, value=None))
    if out_age and confirm_age_ok is False:
        gr.Info("Data NOT saved. Please correct your age to be between 10 and 80.")
        return ("Age out of range — not saved.", gr.update(value=""), gr.update(choices=_choices_tdee(user)), gr.update(visible=False, value=None))

    bmr = hb_bmr(gender, age_val, float(height_cm), float(weight_kg))
    tdee = bmr * ACTIVITY_FACTORS[activity]
    users[user]["tdee_records"][d_str] = {
        "bmr": round(bmr, 2), "tdee": round(tdee, 2), "gender": gender, "age": age_val,
        "activity": activity, "h_cm": float(height_cm), "w_kg": float(weight_kg),
    }
    html = f"""
<div class="card">
  <div class="card-title">TDEE Summary — {d_str}</div>
  <div class="grid">
    <div class="item"><div class="label">Gender</div><div class="value">{gender}</div></div>
    <div class="item"><div class="label">Age</div><div class="value">{age_val}</div></div>
    <div class="item"><div class="label">Height</div><div class="value">{float(height_cm):.1f} cm</div></div>
    <div class="item"><div class="label">Weight</div><div class="value">{float(weight_kg):.1f} kg</div></div>
    <div class="item"><div class="label">Activity</div><div class="value">{activity}</div></div>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat-label">BMR</div><div class="stat-value">{bmr:.0f} kcal/day</div></div>
    <div class="stat"><div class="stat-label">TDEE</div><div class="stat-value">{tdee:.0f} kcal/day</div></div>
  </div>
</div>
"""
    gr.Info("TDEE saved.")
    return ("Calculated & saved.", gr.update(value=html), gr.update(choices=_choices_tdee(user)), gr.update(visible=False, value=None))

# -----------------------------
# Tab 3 — Food Tracker (UPGRADED)
# -----------------------------
GOALS = ["Lose (-20%)", "Maintenance (0%)", "Gain (+15%)"]

def _meal_total_for_user(user, m, d, b):
    foods = users[user]["foods"]
    return foods["MAIN"].get(m, 0) + foods["DESSERT"].get(d, 0) + foods["BEVERAGE"].get(b, 0)

def ft_on_date_or_goal_change(date_choice, goal_choice):
    """Auto-link TDEE and recompute target when the date/goal changes. Also refresh chart."""
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first.")
        return ("Please login first.", gr.update(value=0), "Target: 0 kcal", plot_food_week({}, None, 0))
    if not date_choice:
        return ("Pick a date that has TDEE (Tab 2).", gr.update(value=0), "Target: 0 kcal", plot_food_week(users[user]["food_log"], None, 0))
    rec = users[user]["tdee_records"].get(date_choice)
    if not rec:
        gr.Warning("No TDEE on this date — compute in Tab 2 first.")
        return ("No TDEE on this date — compute in Tab 2 first.", gr.update(value=0), "Target: 0 kcal", plot_food_week(users[user]["food_log"], date_choice, 0))
    tdee = rec["tdee"]
    target = compute_target_from_goal(tdee, goal_choice)
    gr.Info(f"Linked TDEE for {date_choice}. Target: {target:.0f} kcal.")
    chart = plot_food_week(users[user]["food_log"], date_choice, target)
    return (f"Linked TDEE from Tab 2 ({date_choice}).", gr.update(value=tdee), f"Target: {target:.0f} kcal", chart)

def ft_add_custom_food(name, ftype, kcal,
                       bm, bd, bb, lm, ld, lb, dm, dd, db):
    """Add new food to per-user tables and refresh ALL meal dropdowns."""
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first.")
        updates = [gr.update()] * 9
        return "Please login first.", *updates
    name = (name or "").strip()
    if not name:
        gr.Warning("Please enter a food name."); updates = [gr.update()] * 9
        return "Enter a food name.", *updates
    if ftype not in ("Main", "Dessert", "Beverage"):
        gr.Warning("Choose a valid type."); updates = [gr.update()] * 9
        return "Choose a valid type.", *updates
    try:
        kcal = float(kcal)
        if kcal < 0: raise ValueError
    except Exception:
        gr.Warning("Calories must be a positive number."); updates = [gr.update()] * 9
        return "Calories must be a positive number.", *updates

    table_key = {"Main": "MAIN", "Dessert": "DESSERT", "Beverage": "BEVERAGE"}[ftype]
    # put newest near top by recreating dict with new item after '-'
    tbl = users[user]["foods"][table_key]
    if name in tbl:
        gr.Info("Updated existing food calories.")
    new_tbl = {"-": 0, name: kcal}
    for k, v in tbl.items():
        if k == "-": continue
        if k != name:
            new_tbl[k] = v
    users[user]["foods"][table_key] = new_tbl

    main_c, des_c, bev_c = _food_choices(user)
    gr.Info(f"Added '{name}' to {ftype}.")
    # refresh all 9 dropdowns, keep current selections if still valid
    def pick(value, choices):
        return value if value in choices else "-"
    return (
        f"Added: {name} ({ftype}) = {kcal:.0f} kcal",
        gr.update(choices=main_c, value=pick(bm, main_c)),
        gr.update(choices=des_c, value=pick(bd, des_c)),
        gr.update(choices=bev_c, value=pick(bb, bev_c)),
        gr.update(choices=main_c, value=pick(lm, main_c)),
        gr.update(choices=des_c, value=pick(ld, des_c)),
        gr.update(choices=bev_c, value=pick(lb, bev_c)),
        gr.update(choices=main_c, value=pick(dm, main_c)),
        gr.update(choices=des_c, value=pick(dd, des_c)),
        gr.update(choices=bev_c, value=pick(db, bev_c)),
    )

def ft_log_day(date_choice, tdee_val, goal_choice,
               bm, bd, bb, lm, ld, lb, dm, dd, db, manual):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first.")
        return (0, "Please login first.", plot_food_week({}, None, 0))
    if not date_choice:
        gr.Warning("Pick a date from the dropdown.")
        return (0, "Pick a date.", plot_food_week(users[user]["food_log"], None, 0))

    b = _meal_total_for_user(user, bm, bd, bb)
    l = _meal_total_for_user(user, lm, ld, lb)
    d = _meal_total_for_user(user, dm, dd, db)
    manual = manual if (manual and manual > 0) else 0
    total = b + l + d + manual

    users[user]["food_log"][date_choice] = total

    target = compute_target_from_goal(tdee_val, goal_choice)
    if target > 0:
        delta = total - target
        diff = f" Over target by <b>+{delta:.0f} kcal</b>" if delta > 0 else f" Under target by <b>{abs(delta):.0f} kcal</b>"
        pct = max(0, min(100, (total / target) * 100))
    else:
        diff = "ℹ️ Target is 0; select a date with TDEE and goal."
        pct = 0

    info_html = f"""
<div class="card">
  <div class="card-title">Daily Summary — {date_choice}</div>
  <div class="grid" style="grid-template-columns: repeat(4,1fr);">
    <div class="item"><div class="label">Breakfast</div><div class="value">{b} kcal</div></div>
    <div class="item"><div class="label">Lunch</div><div class="value">{l} kcal</div></div>
    <div class="item"><div class="label">Dinner</div><div class="value">{d} kcal</div></div>
    <div class="item"><div class="label">Manual</div><div class="value">{manual} kcal</div></div>
  </div>
  <div class="stat" style="margin-top:10px;">
    <div class="stat-label">Total</div>
    <div class="stat-value">{total} kcal</div>
  </div>
  <div style="margin-top:10px">
    <div class="label">Progress vs Target</div>
    <div style="height:14px; background:#222; border:1px solid var(--neon); border-radius:10px; overflow:hidden;">
      <div style="height:100%; width:{pct:.0f}%; background:linear-gradient(90deg, #39ff14, #ff9f1c);"></div>
    </div>
    <div style="margin-top:6px">Target: <b>{target:.0f} kcal</b> — {diff}</div>
  </div>
</div>
"""
    chart = plot_food_week(users[user]["food_log"], date_choice, target)
    gr.Info("Logged today’s calories.")
    return (total, info_html, chart)

def ft_reset_day(date_choice, goal_choice):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first."); return (0, "Please login first.", plot_food_week({}, None, 0))
    if not date_choice:
        gr.Warning("Pick a date from the dropdown.")
        return (0, "Pick a date.", plot_food_week(users[user]["food_log"], None, 0))
    users[user]["food_log"][date_choice] = 0
    target = compute_target_from_goal(users[user]["tdee_records"].get(date_choice, {}).get("tdee", 0), goal_choice)
    gr.Info(f"Cleared totals for {date_choice}.")
    return (0, f"Cleared totals for {date_choice}.", plot_food_week(users[user]["food_log"], date_choice, target))

def ft_clear_all(goal_choice):
    user = SESSION["current_user"]
    if not user:
        gr.Error("Please login first."); return (0, "Please login first.", plot_food_week({}, None, 0))
    users[user]["food_log"].clear()
    gr.Info("Cleared log.")
    target = 0
    return (0, "Cleared log.", plot_food_week(users[user]["food_log"], None, target))

# -----------------------------
# Custom CSS (game vibe + centered toasts)
# -----------------------------
CSS = """
:root { --neon: #39ff14; --neon2: #ff9f1c; --bg: #0b1020; --panel: #121735; --text: #d9e7ff; }
.gradio-container, body { background: var(--bg) !important; color: var(--text); }
.block.svelte-vjg2a4, .gr-panel, .wrap.svelte-1clh5d2, .form { background: var(--panel) !important; border-radius: 16px; }
button { border-radius: 14px !important; }
button.primary { box-shadow: 0 0 10px var(--neon); }
h1, h2, h3 { color: var(--neon); text-shadow: 0 0 6px rgba(57,255,20,.6); }

.card {
  border: 2px solid var(--neon2);
  border-radius: 16px;
  padding: 14px;
  background: linear-gradient(180deg, rgba(255,159,28,0.08), rgba(0,0,0,0));
}
.card-title { font-weight: 800; color: var(--neon2); margin-bottom: 10px; }
.grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.item { background: rgba(255,255,255,0.04); border-radius: 10px; padding: 8px; }
.label { font-size: 12px; opacity: 0.85; }
.value { font-size: 16px; font-weight: 700; }
.stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px; }
.stat { background: rgba(57,255,20,0.08); border: 1px solid var(--neon); border-radius: 12px; padding: 12px; text-align: center; }
.stat-label { font-size: 12px; opacity: .85; }
.stat-value { font-size: 22px; font-weight: 900; color: var(--neon); text-shadow: 0 0 8px rgba(57,255,20,.6); }

/* Center built-in toast notifications */
div[class*="absolute"][class*="top-4"][class*="right-4"] {
  position: fixed !important;
  left: 50% !important;
  top: 50% !important;
  right: auto !important;
  transform: translate(-50%, -50%) !important;
  z-index: 9999 !important;
}
"""

# -----------------------------
# Build UI
# -----------------------------
with gr.Blocks(title="BME Health Calculator", css=CSS) as demo:
    gr.Markdown("# 🎮 BME Health Calculator")
    with gr.Row():
        username = gr.Textbox(label="Username", placeholder="Enter a username to start", scale=3)
        login_btn = gr.Button("Log in", variant="primary")
        logout_btn = gr.Button("Log out")
    login_info = gr.Markdown("")
    app_panel = gr.Group(visible=False)

    with app_panel:
        # --- Tab 1 (unchanged UI) ---
        with gr.Tab("BMI Calculator"):
            gr.Markdown("### Record and visualize BMI (one record per day)")
            with gr.Row():
                unit = gr.Dropdown(["Metric (cm, kg)", "Imperial (inch, lb)"], value="Metric (cm, kg)", label="Unit System")
                height_in = gr.Number(label="Height", precision=2)
                weight_in = gr.Number(label="Weight", precision=2)
                bmi_date = gr.Textbox(label="Date (YYYY-MM-DD)", value=today_str(), info="Format: YYYY-MM-DD")
            confirm_out = gr.Radio([True, False], label="If your data is out of range, is it CORRECT?",
                                   info="Only appears if the app detects out-of-range data.", value=None, visible=False)
            with gr.Row():
                add_bmi_btn = gr.Button("Save BMI for this day", variant="primary")
                clear_bmi_btn = gr.Button("Clear this day")
            bmi_msg = gr.Markdown()
            bmi_value = gr.Number(label="BMI", interactive=False)
            bmi_plot = gr.Image(value=plot_bmi_series({}), label="BMI Over Time", height=300)
            bmi_dates_for_tab1 = gr.Dropdown(label="Existing BMI dates (from Tab 1)", choices=[])
            view_bmi_btn = gr.Button("View selected date summary")
            view_bmi_out = gr.Markdown()

        # --- Tab 2 (unchanged UI, locked date) ---
        with gr.Tab("Metabolic Rate (BMR/TDEE)"):
            gr.Markdown("### Select a BMI date (auto loads H/W), then compute BMR/TDEE")
            with gr.Row():
                link_date = gr.Dropdown(label="Pick a BMI date (from Tab 1)", choices=[])
            link_status = gr.Markdown("")
            with gr.Row():
                gender = gr.Radio(["Male", "Female"], label="Gender")
                age = gr.Number(label="Age (years, 10–80)", precision=0)
            with gr.Row():
                height_cm_t2 = gr.Number(label="Height (cm)", precision=2)
                weight_kg_t2 = gr.Number(label="Weight (kg)", precision=2)
                activity = gr.Dropdown(list(ACTIVITY_FACTORS.keys()), label="Activity Level")
            t2_date_locked = gr.Textbox(label="Date for this TDEE record (locked)", interactive=False)
            confirm_age_ok = gr.Radio([True, False], label="Age is outside 10–80. Is it CORRECT?",
                                      info="Only appears if age is out of the allowed range.", value=None, visible=False)
            compute_btn = gr.Button("Compute & Save TDEE", variant="primary")
            t2_big_output = gr.HTML(label="Results")

        # --- Tab 3 (UPGRADED) ---
        with gr.Tab("Food Tracker"):
            gr.Markdown("### Pick a TDEE date (auto links) — 3 meals × (Main, Dessert, Beverage)")

            with gr.Row():
                ft_date_dd = gr.Dropdown(label="Pick a date (with TDEE saved in Tab 2)", choices=[])
                goal_choice = gr.Dropdown(GOALS, value="Maintenance (0%)", label="Goal / Target")
                tdee_val = gr.Number(label="TDEE (linked)", value=0, interactive=False)
            tdee_link_status = gr.Markdown()
            target_label = gr.Markdown("Target: 0 kcal")

            # Add Custom Food
            gr.Markdown("#### ➕ Add your own food")
            with gr.Row():
                add_name = gr.Textbox(label="Food name")
                add_type = gr.Dropdown(["Main", "Dessert", "Beverage"], label="Type")
                add_kcal = gr.Number(label="Calories (kcal)", precision=0)
                add_food_btn = gr.Button("Add Food", variant="primary")
            add_food_msg = gr.Markdown()

            # Meals
            gr.Markdown("#### Breakfast")
            with gr.Row():
                bm = gr.Dropdown(choices=["-"], value="-", label="Main")
                bd = gr.Dropdown(choices=["-"], value="-", label="Dessert")
                bb = gr.Dropdown(choices=["-"], value="-", label="Beverage")

            gr.Markdown("#### Lunch")
            with gr.Row():
                lm = gr.Dropdown(choices=["-"], value="-", label="Main")
                ld = gr.Dropdown(choices=["-"], value="-", label="Dessert")
                lb = gr.Dropdown(choices=["-"], value="-", label="Beverage")

            gr.Markdown("#### Dinner")
            with gr.Row():
                dm = gr.Dropdown(choices=["-"], value="-", label="Main")
                dd = gr.Dropdown(choices=["-"], value="-", label="Dessert")
                db = gr.Dropdown(choices=["-"], value="-", label="Beverage")

            manual = gr.Number(label="Manual extra calories (optional)", value=0)

            with gr.Row():
                add_day_btn = gr.Button("➕ Log Day Total", variant="primary")
                reset_day_btn = gr.Button("♻️ Reset This Day")
                clear_week_btn = gr.Button("🧹 Clear Week")

            total_out = gr.Number(label="Total Calories Today", value=0)
            info_out = gr.HTML()
            chart_out = gr.Image(value=plot_food_week({}, None, 0), label="Recent Week Chart", height=300)

    # -----------------------------
    # Wiring
    # -----------------------------
    # Login/Logout: also refresh 9 meal dropdowns
    login_btn.click(
        do_login, inputs=[username],
        outputs=[username, app_panel, login_info, bmi_plot, bmi_dates_for_tab1, link_date, ft_date_dd, t2_big_output,
                 bm, bd, bb, lm, ld, lb, dm, dd, db],
    )
    logout_btn.click(
        do_logout,
        outputs=[username, app_panel, login_info, bmi_plot, bmi_dates_for_tab1, link_date, ft_date_dd, t2_big_output,
                 bm, bd, bb, lm, ld, lb, dm, dd, db],
    )

    # Tab 1
    add_bmi_btn.click(
        bmi_add_record,
        inputs=[unit, height_in, weight_in, bmi_date, confirm_out],
        outputs=[bmi_msg, bmi_value, bmi_dates_for_tab1, link_date, ft_date_dd, bmi_plot, confirm_out],
    )
    clear_bmi_btn.click(
        bmi_clear_day,
        inputs=[bmi_date],
        outputs=[bmi_msg, bmi_plot, bmi_dates_for_tab1, link_date, ft_date_dd],
    )
    view_bmi_btn.click(bmi_view_on_date, inputs=[bmi_date], outputs=[view_bmi_out])

    # Tab 2
    link_date.change(
        t2_on_date_change,
        inputs=[link_date],
        outputs=[link_status, height_cm_t2, weight_kg_t2, t2_date_locked],
    )
    compute_btn.click(
        t2_compute_and_save,
        inputs=[t2_date_locked, gender, age, activity, height_cm_t2, weight_kg_t2, confirm_age_ok],
        outputs=[login_info, t2_big_output, ft_date_dd, confirm_age_ok],
    )

    # Tab 3 — auto-link on date/goal change
    ft_date_dd.change(ft_on_date_or_goal_change, inputs=[ft_date_dd, goal_choice], outputs=[tdee_link_status, tdee_val, target_label, chart_out])
    goal_choice.change(ft_on_date_or_goal_change, inputs=[ft_date_dd, goal_choice], outputs=[tdee_link_status, tdee_val, target_label, chart_out])

    # Tab 3 — add custom food then refresh all meal dropdowns
    add_food_btn.click(
        ft_add_custom_food,
        inputs=[add_name, add_type, add_kcal, bm, bd, bb, lm, ld, lb, dm, dd, db],
        outputs=[add_food_msg, bm, bd, bb, lm, ld, lb, dm, dd, db],
    )

    # Tab 3 — log/reset/clear with target-aware chart
    add_day_btn.click(
        ft_log_day,
        inputs=[ft_date_dd, tdee_val, goal_choice, bm, bd, bb, lm, ld, lb, dm, dd, db, manual],
        outputs=[total_out, info_out, chart_out],
    )
    reset_day_btn.click(
        ft_reset_day,
        inputs=[ft_date_dd, goal_choice],
        outputs=[total_out, info_out, chart_out],
    )
    clear_week_btn.click(
        lambda goal: ft_clear_all(goal),
        inputs=[goal_choice],
        outputs=[total_out, info_out, chart_out],
    )

# Launch
if __name__ == "__main__":
    demo.launch()
