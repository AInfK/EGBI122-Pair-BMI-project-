# BME Health Calculator Suite 

A neon-styled, multi-tab health app built with **Gradio 5.49** and **Matplotlib**.
It runs **in-memory** (no database) and lets a user:

* Log in (per-user, temporary memory)
* Record **BMI** once per day and see trends with category bands
* Compute **BMR/TDEE** (Harris–Benedict) linked to a BMI date
* Track food for **3 meals** + manual calories, with:

  * **Custom foods** (name, type, kcal) saved per-user and added to all dropdowns instantly
  * **Goal/target** (Lose, Maintenance, Gain) – progress bar and 7-day chart compare to **target** (derived from TDEE)
* Enjoy a “video-game” dark neon UI with **centered** pop-up notifications

> ⚠️ Data is cleared when the process stops—it’s intentionally **temporary**.

---

## Table of Contents

* [Demo (Run Locally)](#demo-run-locally)
* [Requirements](#requirements)
* [Features](#features)
* [How It Works](#how-it-works)
* [User Flow](#user-flow)
* [Validations & Guardrails](#validations--guardrails)
* [UI/UX Details](#uiux-details)
* [Folder / File](#folder--file)
* [Customization](#customization)
* [Troubleshooting](#troubleshooting)
* [Roadmap Ideas](#roadmap-ideas)
* [License](#license)

---

## Demo (Run Locally)

1. **Create a virtual environment** (recommended):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

2. **Install dependencies**:

```bash
pip install gradio==5.49.0 matplotlib
```

3. **Run the app** (save the provided code to `app.py`):

```bash
python app.py
```

4. Open the **local URL** printed in the terminal (usually `http://127.0.0.1:7860`).

---

## Requirements

* Python **3.9+** (tested most with 3.10/3.11)
* Packages:

  * `gradio==5.49.0`
  * `matplotlib`

> Using a different Gradio major version may break component APIs or CSS behavior.

---

## Features

### Tab 1 — BMI Calculator

* Input **unit system** (Metric or Imperial), **height**, **weight**, and **date**.
* **One record per day**. If a date already exists, you must clear it first.
* **Range checks**:

  * Height: **100–250 cm**
  * Weight: **30–200 kg**
  * BMI: **10–70**
* If out of range, a **confirm** radio appears (hidden otherwise).
  If confirmed **True**, data saves and adds *“You gotta be kidding me”* to the message.
  If **False**, nothing is saved.
* Chart shows **category bands** (Underweight/Normal/Overweight/Obese) with **point labels**.

### Tab 2 — Metabolic Rate (BMR/TDEE)

* **Select a BMI date** (dropdown). Height/weight **auto-load** from Tab 1 and the TDEE date **locks** to that selection.
* Fill **gender**, **age**, and **activity level**; compute **BMR** and **TDEE**.
* **Age validation**: must be **10–80**. If outside, a confirm radio appears; only saves on **True**.
* Results are shown in a **stat card** (neon style).

### Tab 3 — Food Tracker

* **Pick a date with TDEE** (from Tab 2) and a **Goal/Target**:

  * *Lose (-20%)*, *Maintenance (0%)*, *Gain (+15%)*
    Target = TDEE × goal multiplier.
* **Custom foods**: add *(name, type, calories)* once; it appears **immediately** in **all meal dropdowns** (Breakfast/Lunch/Dinner × Main/Dessert/Beverage).
* **Daily summary**: totals by meal, **progress bar vs target**, and a **7-day chart** (window ends on the selected date) with:

  * **Target line & label**
  * **Bar value labels**
  * Light grid and clear title

---

## How It Works

* **Temporary storage**:

  ```python
  users = {
    "<username>": {
      "bmi_records": {"YYYY-MM-DD": {h_cm,w_kg,bmi}},
      "tdee_records": {"YYYY-MM-DD": {bmr,tdee,gender,age,activity,h_cm,w_kg}},
      "food_log": {"YYYY-MM-DD": total_kcal},
      "foods": {"MAIN": {...}, "DESSERT": {...}, "BEVERAGE": {...}}
    }
  }
  ```
* **Login** sets `SESSION["current_user"]`. All reads/writes are **per user**.
* **Linking**:

  * Tab 2’s BMI date comes from Tab 1’s saved dates.
  * Tab 3’s date must exist in **TDEE records** (Tab 2).
  * The weekly chart centers on **the chosen Tab 3 date**.

---

## User Flow

1. **Login** with a username (creates your in-memory profile).
2. **Tab 1**: Enter BMI for a date → see it plotted.
3. **Tab 2**: Pick that BMI date → auto load height/weight → compute & save TDEE.
4. **Tab 3**: Pick the TDEE date, set a **Goal** → add foods (optional) → select meals → **Log Day Total**.
   View the **progress bar vs target** and the **7-day chart**.

---

## Validations & Guardrails

* **BMI**:

  * Height 100–250 cm, Weight 30–200 kg, BMI 10–70
  * If out-of-range ⇒ ask *“Is it correct?”* (True/False). Saves only on **True**.
  * One record per day (duplication blocked).
* **TDEE**:

  * Age must be **10–80** or confirm **True** when outside.
  * Missing gender/activity/age/height/weight/date ⇒ **centered** warning popup.
* **Food Tracker**:

  * Custom foods must have **name**, **type**, **kcal ≥ 0**.
  * TDEE target = TDEE × goal (0.8/1.0/1.15).

---

## UI/UX Details

* **Neon “video-game” theme** via custom CSS.
* Built-in **toasts repositioned to the center** of the screen.
* Tab 2 and 3 dropdowns **auto-link** data on change (no “Load” button).
* Tab 3 shows a **progress bar** and target-aware **7-day chart**.

---

## Folder / File

Single file app (example):

```
app.py
```

Run with:

```bash
python app.py
```

---

## Customization

* **Goal multipliers**: edit `compute_target_from_goal()`:

  ```python
  m = {
      "Lose (-20%)": 0.80,
      "Maintenance (0%)": 1.00,
      "Gain (+15%)": 1.15
  }
  ```

* **Default foods**: modify `ensure_user(... "foods": {...})`.

* **Ranges**:

  * BMI tab: edit `ALLOWED` (height/weight/BMI).
  * TDEE age: change checks in `t2_compute_and_save()`.

* **Theme**: tweak the `CSS` string for colors, borders, or toast position.

---

## Troubleshooting

* **“module 'gradio' has no attribute 'Date'”**
  This code uses **Textbox** for dates (string `YYYY-MM-DD`) to be compatible with **Gradio 5.49**.

* **Popups not centered**
  Some Gradio builds change utility classes. Adjust the CSS selector that targets the toast container:

  ```css
  div[class*="absolute"][class*="top-4"][class*="right-4"] { ... }
  ```

* **Nothing appears in dropdowns**
  Make sure you’re **logged in**, then add/save data in the tabs in order (Tab 1 → Tab 2 → Tab 3).

* **Data disappears**
  That’s expected—storage is **in memory**. To persist, save to a file/DB in the handlers.

---

## Roadmap Ideas

* Persist users/records to a **SQLite/JSON** backend
* Real **date picker** once stable in your Gradio version
* Export reports (CSV/PDF)
* Multi-user auth, sessions, and roles
* More nutrition fields (protein, fat, carbs) + macro targets
* Mobile-responsive tweaks & PWA install

---

## License

MIT (or your preferred license). Add a `LICENSE` file if distributing.


