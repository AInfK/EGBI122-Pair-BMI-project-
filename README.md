# BME Health Calculator Suite — README

A 3-tab health toolkit for **biomedical engineering students**.
Runs locally with **Gradio 5.49** + **Matplotlib** and stores everything **in memory** per session.

> Tabs
>
> 1. **BMI Calculator** — one record/day, range checks, trend chart
> 2. **BMR/TDEE** — Harris-Benedict + activity factors, linked to a BMI date
> 3. **Food Tracker** — breakfast/lunch/dinner (Main/Dessert/Beverage), **custom foods**, **goal-based target**, 7-day chart

---

## ✨ Highlights

* **Login first** → data keyed by username (no external DB)
* **One BMI per day** with **out-of-range confirmation** (height/weight/BMI guardrails)
* **Metric/Imperial** unit support
* **Auto-link** BMI → **TDEE** on a chosen date
* **Goals**: Lose (−20%), Maintenance (0%), Gain (+15%) → target kcal from TDEE
* **➕ Custom Food** (name, type, kcal) appears instantly in all dropdowns
* **7-day calories chart** with **target line** and values on bars
* “**Clear this day**” & “**Clear week**” so wrong entries don’t persist
* **Game-vibe UI** + centered toast notifications

---

## 🧰 Requirements

* **Python** 3.10+
* **Gradio** 5.49
* **Matplotlib**

`requirements.txt` (optional):

```
gradio==5.49
matplotlib
```

---

## 🚀 Quickstart

1. Create & activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

2. Install

```bash
pip install -r requirements.txt
# or
pip install gradio==5.49 matplotlib
```

3. Run

```bash
python app.py   # or whatever filename you saved
```

4. Open the URL that Gradio prints (e.g., [http://127.0.0.1:7860](http://127.0.0.1:7860))

---

## 🧭 How to Use

### 0) Login

* Enter a **Username** → **Log in**. You’ll see a welcome message and the tabs.

### 1) Tab: BMI Calculator

* Choose **Unit System** (Metric or Imperial), enter **Height/Weight**, and **Date (YYYY-MM-DD)**.
* Click **Save BMI for this day**. If values look unrealistic, the app asks you to **confirm** first.
* **One record per day** (must clear before overwriting).
* View any date’s summary or **Clear this day**.
* The **BMI chart** shows category bands (Underweight/Normal/Overweight/Obese) with annotations.

### 2) Tab: Metabolic Rate (BMR/TDEE)

* Pick a **BMI date** (auto-loads that day’s height/weight).
* Fill **Gender**, **Age (10–80)**, and **Activity** level.
* Click **Compute & Save TDEE** to store a card with BMR & TDEE.
* The saved **TDEE date** becomes available to Tab 3.

### 3) Tab: Food Tracker (Upgraded)

* Select a **date with TDEE** and a **Goal**; the app computes a **Target kcal**.
* For **Breakfast/Lunch/Dinner**, pick **Main/Dessert/Beverage**.
* Use **➕ Add your own food** (name, type, kcal). It appears in all dropdowns immediately.
* Optionally add **Manual extra calories**.
* Click **➕ Log Day Total** → you’ll see a styled summary, **progress vs target**, and a **7-day chart**.
* **♻️ Reset This Day** sets that date to 0 kcal; **🧹 Clear Week** clears the whole log.

---

## 🧠 For BME Students

* **BMI** is a rough screening tool; it does **not** reflect body composition.
* **BMR/TDEE** uses **Harris–Benedict** with standard activity multipliers; useful for trend-tracking but still an **estimate**.
* Food kcal values are **approximate**; use **custom foods** for Thai dishes or lab-measured portions.
* This app is for **learning and personal tracking**, not clinical diagnosis or treatment.

---

## 🗃️ In-Memory Data Model

```python
users = {
  "<username>": {
    "bmi_records": { "YYYY-MM-DD": {"h_cm": float, "w_kg": float, "bmi": float}, ... },
    "tdee_records": { "YYYY-MM-DD": {"bmr": float, "tdee": float, "gender": str, "age": int, ...}, ... },
    "food_log": { "YYYY-MM-DD": total_kcal_float, ... },
    "foods": { "MAIN": {...}, "DESSERT": {...}, "BEVERAGE": {...} }
  }
}
SESSION = {"current_user": "<username or None>"}
```

> ⚠️ **Ephemeral**: data is **not saved** after you stop the app. For persistence, add a DB (e.g., SQLite) later.

---

## ✅ Guardrails

* **Height**: 100–250 cm, **Weight**: 30–200 kg, **BMI**: 10–70 → out-of-range asks for confirmation
* **Age**: 10–80 for TDEE → out-of-range asks for confirmation
* **One BMI per date** (must clear before re-saving)

---

## 🎨 UI/CSS

* Neon game vibe with custom CSS
* Centered toasts for better visibility
* Matplotlib charts saved to temp files and displayed in app

---

## 🧩 Project Layout (suggested)

```
bme-health-calculator/
├─ app.py            # this script
├─ README.md         # this file
├─ requirements.txt  # optional
└─ assets/           # screenshots (optional)
```

---

## 🛠️ Troubleshooting

* **Gradio not launching** → verify Python 3.10+, reinstall `gradio==5.49`
* **Charts not showing** → ensure Matplotlib can write to your temp directory (`/tmp` on Unix)
* **Data missing** → remember: per-session, in-memory only; log in with the same username during the same run

---

## 🗺️ Roadmap (nice next steps)

* SQLite persistence for users/logs
* Macro & micronutrient breakdowns
* CSV export/import
* Mobile-first layout tweaks
* Thai/English UI toggle

---

## 🔒 Ethics & Privacy

* Do **not** use for diagnosis/treatment.
* Keep runs local and avoid sharing usernames/data.

---

## 📄 License

This project is using MIT license 

Happy building & analyzing!😁
