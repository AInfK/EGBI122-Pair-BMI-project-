# BME Health Calculator Suite😁



**Course:** *EGBI122*.

**Student:** *1. Arnakorn Kajornsirisin*.
             *2. Watsananon Wongsurin*.
---

## 1) Executive Summary

This project is a three-tab, in-memory health calculator built with **Python**, **Gradio 5.49**, and **Matplotlib**. It helps track **BMI**, estimate **BMR/TDEE** (Harris–Benedict + activity factors), and log daily calories via a **Food Tracker** with a goal-based target line and a **7-day chart**. I designed it with strict input guardrails (one BMI per day, range checks, confirmation for outliers) to reduce data entry errors, which is important for biomedical data quality.

Use cases include personal health tracking, demonstrating basic biomedical calculations, and practicing UI/UX for health tools.

---

## 2) Learning Objectives

1. Implement biomedical formulas (BMI, BMR/TDEE) correctly in Python.
2. Enforce data integrity (single daily records, numeric checks, range validation).
3. Build a usable health UI with clear feedback and plots for trend analysis.
4. Reflect on ethical use and limitations of screening metrics (BMI, estimated TDEE).

---

## 3) System Overview

### Components

* **Tab 1 — BMI Calculator:**

  * Inputs: unit system (Metric/Imperial), height, weight, date (`YYYY-MM-DD`).
  * Guardrails: numeric checks, allowed ranges (Height 100–250 cm, Weight 30–200 kg, BMI 10–70), **one record per day**.
  * Output: BMI value + category (Underweight/Normal/Overweight/Obese) and a trend plot with category bands.

* **Tab 2 — Metabolic Rate (BMR/TDEE):**

  * Inputs: gender, age (10–80), activity level; height/weight auto-loaded from a BMI date.
  * Output: BMR (Harris–Benedict) and TDEE card; saved per date for linking to the Food Tracker.

* **Tab 3 — Food Tracker (Upgraded):**

  * Links to a selected **TDEE date**; **Goal** (Lose −20%, Maintenance 0%, Gain +15%) sets a daily **target kcal**.
  * Meals: Breakfast, Lunch, Dinner (each with Main/Dessert/Beverage dropdowns).
  * **Custom Food**: add (name, type, kcal); appears instantly in all dropdowns.
  * Outputs: daily summary + progress bar vs target and a **7-day bar chart** with a target line.

### Data Model (Ephemeral, per session)

```python
users = {
  "<username>": {
    "bmi_records": { "YYYY-MM-DD": {"h_cm": float, "w_kg": float, "bmi": float}, ... },
    "tdee_records": { "YYYY-MM-DD": {"bmr": float, "tdee": float, "gender": str, "age": int, ...}, ... },
    "food_log":     { "YYYY-MM-DD": total_kcal_float, ... },
    "foods":        { "MAIN": {...}, "DESSERT": {...}, "BEVERAGE": {...} }
  }
}
SESSION = {"current_user": "<username or None>"}
```

> **Note:** No database is used; all data disappears when the app stops (useful for prototyping).

---

## 4) Installation & Run

### Requirements

* Python **3.10+**
* Packages: **gradio==5.49**, **matplotlib**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install gradio==5.49 matplotlib
python app.py   # or your filename
# Open the URL Gradio prints (e.g., http://127.0.0.1:7860)
```

---

## 5) How to Use (Step-by-Step)

### 0) Login
![Register Example](https://github.com/AInfK/EGBI122-Pair-BMI-project-/blob/main/Picture/Tab0.png)


1. Enter a **Username** → click **Log in**. (All data is stored under this username during the session.)


### 1) BMI Calculator
![UI example](https://github.com/AInfK/EGBI122-Pair-BMI-project-/blob/main/Picture/tab1.png)

1. Select **Metric** or **Imperial**.
2. Enter **Height**, **Weight**, and **Date** (`YYYY-MM-DD`; default is today).
3. Click **Save BMI for this day**.

   * If values look unrealistic, the app asks for **confirmation** before saving.
4. View or **Clear** a specific date.
5. Inspect the **BMI trend chart** with category bands and annotations.

### 2) Metabolic Rate (BMR/TDEE)
![UI example](https://github.com/AInfK/EGBI122-Pair-BMI-project-/blob/main/Picture/Tab2.png)

1. Choose a **BMI date** (loads height/weight from Tab 1).
2. Set **Gender**, **Age (10–80)**, **Activity**.
3. Click **Compute & Save TDEE** → a summary card is saved for that date (used in Tab 3).

### 3) Food Tracker
![UI example](https://github.com/AInfK/EGBI122-Pair-BMI-project-/blob/bc4ac9958e7a5a35e336219037813ee6808e081f/Picture/Tab%203.png)
![graph example](https://github.com/AInfK/EGBI122-Pair-BMI-project-/blob/main/Picture/graph%20epic)

1. Select a **date that has TDEE** from Tab 2.
2. Choose a **Goal** (Lose/Maintenance/Gain) → the **target kcal** updates automatically.
3. Pick foods for Breakfast/Lunch/Dinner (Main/Dessert/Beverage).
4. (Optional) Add **Manual extra calories**.
5. Click **➕ Log Day Total** to save and view progress vs target + **7-day chart**.
6. Use **♻️ Reset This Day** to set that day’s total to 0 or **🧹 Clear Week** to clear all logged days.

---

## 6) Algorithms & Equations

### **1. Body Mass Index (BMI)**  
**Formula:**  
BMI = weight (kg) / height (m)<sup>2</sup>

**Categories:**  
| Category | BMI Range |  
|:--|:--:|  
| Underweight | &lt; 18.5 |  
| Normal | 18.5 – 24.9 |  
| Overweight | 25 – 29.9 |  
| Obese | ≥ 30 |  

*Used to classify body weight relative to height.*

---

### **2. Basal Metabolic Rate (BMR)** — _Harris–Benedict Equation_  

**Male:**  
BMR = 88.362 + (13.397 × W) + (4.799 × H) − (5.677 × A)  

**Female:**  
BMR = 447.593 + (9.247 × W) + (3.098 × H) − (4.330 × A)  

Where:  
- W = weight (kg)  
- H = height (cm)  
- A = age (years)  

*Represents the energy your body burns at rest.*

---

### **3. Total Daily Energy Expenditure (TDEE)**  
**Formula:**  
TDEE = BMR × Activity Factor  

**Activity Factors:**  
| Level | Description | Factor |  
|:--|:--|:--:|  
| Sedentary | Little/no exercise | 1.2 |  
| Light | Light exercise 1–3 days/week | 1.375 |  
| Moderate | Moderate exercise 3–5 days/week | 1.55 |  
| Active | Hard exercise 6–7 days/week | 1.725 |  
| Very Active | Physical job or intense training | 1.9 |  

*TDEE reflects total calories burned per day including activity.*

---

### **4. Goal Calorie Targets**  
| Goal | Formula | Description |  
|:--|:--|:--|  
| Lose Weight | 0.80 × TDEE | ~20 % calorie deficit |  
| Maintain Weight | 1.00 × TDEE | Maintain current body weight |  
| Gain Weight | 1.15 × TDEE | ~15 % calorie surplus |  

---

## 7) Data Validation & Guardrails

* **One BMI entry per date** (must clear before overwriting).
* **Numeric checks** for height/weight/age/calories.
* **Range checks** (with confirmation prompt for outliers):

  * Height: 100–250 cm
  * Weight: 30–200 kg
  * BMI: 10–70
  * Age: 10–80
* **Error/Info toasts** are centered to improve visibility.
  ![Error info](https://github.com/AInfK/EGBI122-Pair-BMI-project-/blob/main/Picture/Popup.png)
* **Food tables** are per-user and include a “-” sentinel choice.

---

## 8) UI/UX Notes
* **Neon “game vibe” theme** for engagement.
* **BMI plot** includes colored bands for category context.
* **Food 7-day bar chart** displays numeric labels + target line (from TDEE × goal).
* **Custom food** entries update all dropdowns immediately to reduce friction.

---

## 9) Testing Performed

* **Functional**:

  * Added/cleared BMI on multiple dates; ensured one entry/day rule works.
  * Verified height/weight conversion between Metric/Imperial.
  * Checked age out-of-range prompts in TDEE tab.
  * Logged food totals with default and custom items; confirmed chart and target updates.

* **Edge cases**:

  * Invalid date strings → warning and no save.
  * Negative/NaN calories on custom food → rejected.
  * TDEE not available for a date → tracker shows target = 0 with guidance.

---

## 10) Limitations

* **Ephemeral storage** (no database): data is lost when the app stops.
* **BMI** is a crude screening tool and does not reflect body composition.
* **TDEE** is an estimate; true energy expenditure varies by individual physiology.
* **Food kcal tables** are approximate; user must confirm values for accuracy.

---

## 11) Ethics & Safety Statement

This tool is for **education and personal tracking only**. It does **not** diagnose, treat, or prevent disease. Users should consult healthcare professionals for medical decisions. Data privacy is preserved by running locally and avoiding external storage; users should avoid entering personally identifying information in usernames.

---

## 12) How to Reproduce

1. Clone or copy the Python script provided.
2. Create a virtual environment; install `gradio==5.49` and `matplotlib`.
3. Run `python app.py`, open the local URL, log in with any username, and follow the steps in Section 5.

---

## 13) Future Work

* Add **SQLite** persistence per user (BMI/TDEE/food logs).
* **Macro/micronutrient** breakdown and weekly summaries.
* **CSV import/export** for logs.
* **Thai/English UI toggle** for bilingual use.
* Mobile-first responsive layout.

---

## 14) License
### Copyright (c) 2025 Arnakorn Kajornsirisin & Watsananon Wongsurin
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions.
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
