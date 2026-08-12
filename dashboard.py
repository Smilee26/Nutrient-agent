import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import re

# Page setup
st.set_page_config(
    page_title="IBM AI Universal Nutrition Dashboard",
    page_icon="🥗",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🥗 Universal AI-Powered Nutrition Dashboard")
st.caption("Real-time dynamic tracking & coaching tailored for all body profiles & age groups")

# --- SIDEBAR: PERSONAL PROFILE & GOALS ---
st.sidebar.header("👤 Personal Profile & Goals")

gender = st.sidebar.selectbox("Gender", ["Female", "Male"])

# Universal Age Input (0 to 110 years)
age = st.sidebar.number_input("Age (years)", min_value=0, max_value=110, value=19)

# Universal Weight Input (2 kg to 300 kg)
weight = st.sidebar.number_input("Weight (kg)", min_value=2.0, max_value=300.0, value=53.0, step=0.5)

# Dynamic Height Selector with Clean State Handling
height_unit = st.sidebar.radio("Height Unit", ["Feet", "Centimeters (cm)"], horizontal=True)

if height_unit == "Feet":
    height_feet = st.sidebar.number_input("Height (Feet)", min_value=1.0, max_value=8.5, value=5.32, step=0.01)
    height_cm = height_feet * 30.48
else:
    height_cm = st.sidebar.number_input("Height (cm)", min_value=30.0, max_value=260.0, value=162.2, step=0.5)
    height_feet = height_cm / 30.48

st.sidebar.caption(f"📏 **Current Height:** {height_feet:.2f} ft ({height_cm:.1f} cm)")

# --- DYNAMIC IDEAL WEIGHT & BMI CALCULATOR ---
height_m = height_cm / 100.0
bmi = weight / (height_m ** 2) if height_m > 0 else 0

# Ideal Weight Calculation (Adjusted for Age Groups)
if age < 18:
    # Uses standard pediatric growth reference median (~BMI 18.0)
    min_ideal_weight = 16.5 * (height_m ** 2)
    max_ideal_weight = 22.0 * (height_m ** 2)
    target_ideal_weight = 19.0 * (height_m ** 2)
else:
    # Standard Adult BMI (18.5 - 24.9)
    min_ideal_weight = 18.5 * (height_m ** 2)
    max_ideal_weight = 24.9 * (height_m ** 2)
    target_ideal_weight = 22.0 * (height_m ** 2)

# Determine Weight Status & Visual Badge
if bmi < (16.5 if age < 18 else 18.5):
    bmi_category = "Underweight"
    badge_color = "#3b82f6"  # Blue
    diff_kg = min_ideal_weight - weight
    weight_msg = f"Below target range by {diff_kg:.1f} kg"
elif (16.5 if age < 18 else 18.5) <= bmi <= (22.0 if age < 18 else 24.9):
    bmi_category = "Normal Weight"
    badge_color = "#22c55e"  # Green
    weight_msg = "Your weight is in the ideal healthy range!"
elif (22.0 if age < 18 else 25.0) <= bmi <= (27.0 if age < 18 else 29.9):
    bmi_category = "Overweight"
    badge_color = "#f59e0b"  # Amber
    diff_kg = weight - max_ideal_weight
    weight_msg = f"{diff_kg:.1f} kg above ideal max weight"
else:
    bmi_category = "Obese"
    badge_color = "#ef4444"  # Red
    diff_kg = weight - max_ideal_weight
    weight_msg = f"{diff_kg:.1f} kg above ideal max weight"

# Sidebar Body Status Card
st.sidebar.markdown(f"""
<div style="background-color: #f1f5f9; padding: 12px; border-radius: 8px; border-left: 5px solid {badge_color}; margin-top: 10px; margin-bottom: 15px;">
    <div style="font-size: 12px; color: #64748b; font-weight: bold; text-transform: uppercase;">Body Status & Ideal Weight</div>
    <div style="font-size: 16px; font-weight: bold; color: {badge_color}; margin-top: 2px;">
        BMI: {bmi:.1f} ({bmi_category})
    </div>
    <div style="font-size: 13px; color: #1e293b; margin-top: 4px;">
        <b>Ideal Weight Range:</b> {min_ideal_weight:.1f} kg - {max_ideal_weight:.1f} kg
    </div>
    <div style="font-size: 12px; color: #475569; margin-top: 2px;">
        <i>Target: ~{target_ideal_weight:.1f} kg ({weight_msg})</i>
    </div>
</div>
""", unsafe_allow_html=True)

activity_level = st.sidebar.selectbox(
    "Activity Level",
    [
        "Sedentary (Little/no exercise)",
        "Lightly Active (1-3 days/week)",
        "Moderately Active (3-5 days/week)",
        "Very Active (6-7 days/week)"
    ]
)

# Default to maintenance if weight is already optimal
is_normal_weight = (16.5 if age < 18 else 18.5) <= bmi <= (22.0 if age < 18 else 24.9)
default_goal_idx = 1 if is_normal_weight else 0

goal = st.sidebar.selectbox(
    "Primary Goal",
    ["Weight Loss (-500 kcal)", "Maintain Weight", "Weight Gain (+500 kcal)"],
    index=default_goal_idx
)

# --- UNIVERSAL BMR & MACRO FORMULAS FOR ALL AGES ---
if age < 3:
    # Infants/Toddlers (Schofield / WHO equations)
    bmr = (60.9 * weight) - 54 if gender == "Male" else (61.0 * weight) - 51
    min_calorie_floor = 700
    p_ratio, c_ratio, f_ratio = 0.15, 0.50, 0.35
elif age < 10:
    # Children (3 - 9 yrs)
    bmr = (22.7 * weight) + 495 if gender == "Male" else (20.3 * weight) + 485
    min_calorie_floor = 1000
    p_ratio, c_ratio, f_ratio = 0.18, 0.52, 0.30
elif age < 18:
    # Teens (10 - 17 yrs)
    bmr = (17.5 * weight) + 651 if gender == "Male" else (12.2 * weight) + 746
    min_calorie_floor = 1400
    p_ratio, c_ratio, f_ratio = 0.20, 0.55, 0.25
elif age >= 65:
    # Seniors (Slightly increased protein for sarcopenia prevention)
    bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) + (5 if gender == "Male" else -161)
    min_calorie_floor = 1200
    p_ratio, c_ratio, f_ratio = 0.30, 0.45, 0.25
else:
    # Adults (Mifflin-St Jeor)
    bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) + (5 if gender == "Male" else -161)
    min_calorie_floor = 1200
    p_ratio, c_ratio, f_ratio = 0.25, 0.50, 0.25

multipliers = {
    "Sedentary (Little/no exercise)": 1.2,
    "Lightly Active (1-3 days/week)": 1.375,
    "Moderately Active (3-5 days/week)": 1.55,
    "Very Active (6-7 days/week)": 1.725
}

tdee = bmr * multipliers[activity_level]

# SMART CALORIE TARGET ADJUSTMENT
if is_normal_weight:
    target_calories = int(tdee)
    if "Weight Loss" in goal:
        st.sidebar.info(f"💡 **Optimal Weight Detected:** Target set to maintenance (~{target_calories} kcal) to preserve healthy mass.")
elif "Weight Loss" in goal:
    deficit = 250 if age < 18 else 500
    target_calories = int(tdee - deficit)
elif "Weight Gain" in goal:
    surplus = 250 if age < 18 else 500
    target_calories = int(tdee + surplus)
else:
    target_calories = int(tdee)

target_calories = max(min_calorie_floor, target_calories)

TARGETS = {
    "calories": target_calories,
    "protein": int((target_calories * p_ratio) / 4),
    "carbs": int((target_calories * c_ratio) / 4),
    "fats": int((target_calories * f_ratio) / 9)
}

st.sidebar.markdown("---")
st.sidebar.metric("Calculated Daily Target", f"{TARGETS['calories']} kcal")


# --- SESSION STATE INITIALIZATION ---
if "logged_meals" not in st.session_state:
    st.session_state.logged_meals = []

if "totals" not in st.session_state:
    st.session_state.totals = {"calories": 0, "protein": 0, "carbs": 0, "fats": 0}


# --- HELPER FUNCTIONS ---
def recalculate_totals():
    new_totals = {"calories": 0, "protein": 0, "carbs": 0, "fats": 0}
    for item in st.session_state.logged_meals:
        for key in new_totals:
            new_totals[key] += item.get(key, 0)
    st.session_state.totals = new_totals

def extract_quantity_multiplier(text_query):
    match = re.search(r'^(\d+)', text_query.strip())
    return int(match.group(1)) if match else 1


# --- SECTION 1: MEAL LOGGING & PROACTIVE AI DIETITIAN ---
st.subheader("💬 Log Today's Meal & AI Dietitian Plan")

col_form, col_suggest = st.columns([1.8, 1.2])

tot = st.session_state.totals
remaining_kcal = TARGETS['calories'] - tot['calories']

with col_form:
    with st.form("meal_form", clear_on_submit=True):
        meal_time = st.selectbox(
            "Select Meal Time",
            ["🌅 Breakfast", "☀️ Lunch", "☕ Evening Snack", "🌙 Dinner"]
        )
        user_query = st.text_input(
            "What did you eat?",
            placeholder="e.g., 2 chapati, 1 bowl daal, 1 bowl salad"
        )
        submitted = st.form_submit_button("➕ Log Meal", use_container_width=True)

# PROACTIVE AI DIETITIAN
with col_suggest:
    st.markdown("### 🤖 Proactive AI Dietitian")
    
    if is_normal_weight:
        st.success(
            f"🎯 **Great job! Your body profile is optimal ({weight} kg at {height_feet:.2f} ft).**\n\n"
            f"Your daily target is set to **{TARGETS['calories']} kcal** to maintain energy levels and balanced health."
        )
    elif remaining_kcal <= 0:
        st.error(
            f"🛑 **Calorie Limit Reached!** You are **+{abs(remaining_kcal)} kcal over** your daily target."
        )
    elif remaining_kcal < 400:
        st.info(
            f"💡 **Remaining Target:** You have **{remaining_kcal} kcal left** for today."
        )
    else:
        st.info(
            f"✅ **On Track!** You have **{remaining_kcal} kcal remaining** for today."
        )

# Handle Meal Submission
if submitted and user_query:
    try:
        res = requests.post("http://127.0.0.1:8000/query", json={"query": user_query}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            nutrition = data.get("nutrition", {"calories": 200, "protein": 8, "carbs": 25, "fats": 6})
            
            qty = extract_quantity_multiplier(user_query)
            if qty > 1 and nutrition.get("calories", 0) <= 250:
                nutrition = {k: v * qty for k, v in nutrition.items()}
            
            st.session_state.logged_meals.append({
                "time": meal_time,
                "meal": user_query,
                **nutrition
            })
            recalculate_totals()
            st.toast(f"Logged [{meal_time}] '{user_query}' (+{nutrition['calories']} kcal)!", icon="✅")
            st.rerun()
        else:
            st.error("Failed to connect to backend API.")
    except Exception:
        st.error("Backend server is offline (Check http://127.0.0.1:8000)")


# --- LOGGED ITEMS TIMELINE WITH DELETE FUNCTIONALITY ---
if st.session_state.logged_meals:
    with st.expander("📋 Today's Full Timeline (Click ❌ to remove individual meals)", expanded=True):
        for idx, item in enumerate(st.session_state.logged_meals):
            c_text, c_del = st.columns([5, 1])
            with c_text:
                st.markdown(
                    f"**{idx+1}. [{item['time']}] {item['meal']}** — `{item['calories']} kcal` | "
                    f"**P:** {item['protein']}g | **C:** {item['carbs']}g | **F:** {item['fats']}g"
                )
            with c_del:
                if st.button("❌ Remove", key=f"del_{idx}"):
                    st.session_state.logged_meals.pop(idx)
                    recalculate_totals()
                    st.toast("Item removed!", icon="🗑️")
                    st.rerun()
                    
        st.write("")
        if st.button("🗑️ Reset Entire Daily Tracker"):
            st.session_state.logged_meals = []
            st.session_state.totals = {"calories": 0, "protein": 0, "carbs": 0, "fats": 0}
            st.rerun()

st.divider()

# --- SECTION 2: REAL-TIME INTAKE & MACRO DISPLAY ---
st.subheader("📈 Today's Real-time Intake")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Daily Calories", f"{tot['calories']} / {TARGETS['calories']} kcal")
col2.metric("Protein", f"{tot['protein']} / {TARGETS['protein']} g")
col3.metric("Carbs", f"{tot['carbs']} / {TARGETS['carbs']} g")
col4.metric("Fats", f"{tot['fats']} / {TARGETS['fats']} g")

col1.progress(min(1.0, tot['calories'] / TARGETS['calories']))
col2.progress(min(1.0, tot['protein'] / TARGETS['protein']))
col3.progress(min(1.0, tot['carbs'] / TARGETS['carbs']))
col4.progress(min(1.0, tot['fats'] / TARGETS['fats']))

st.divider()

# --- SECTION 3: VISUAL ANALYTICS ---
left_chart, right_chart = st.columns([2, 1])

with left_chart:
    st.subheader("📊 Weekly Intake vs Target")
    chart_data = pd.DataFrame({
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Today"],
        "Calories": [1500, 1550, 1450, 1500, 1520, 1480, tot['calories']],
        "Target": [TARGETS['calories']] * 7
    })
    fig_bar = px.bar(
        chart_data, 
        x="Day", 
        y=["Calories", "Target"], 
        barmode="group", 
        color_discrete_sequence=["#2563eb", "#e2e8f0"]
    )
    fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
    st.plotly_chart(fig_bar, use_container_width=True)

with right_chart:
    st.subheader("🎯 Calorie Budget Ring")
    consumed = tot['calories']
    target = TARGETS['calories']
    rem = max(0, target - consumed)
    pct = int((consumed / target) * 100) if target > 0 else 0
    
    ring_color = "#ef4444" if consumed > target else "#2563eb"
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=['Consumed', 'Remaining'],
        values=[consumed, rem],
        hole=0.7,
        marker_colors=[ring_color, '#e2e8f0'],
        textinfo='none',
        hoverinfo='label+value',
        sort=False
    )])
    
    center_text = (
        f"<b>{pct}%</b><br><span style='font-size:12px;color:red;'>+{consumed - target} kcal OVER</span>"
        if consumed > target
        else f"<b>{pct}%</b><br><span style='font-size:12px;color:gray;'>{rem} kcal left</span>"
    )
    
    fig_donut.update_layout(
        annotations=[
            dict(
                text=center_text,
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )
        ],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320
    )
    st.plotly_chart(fig_donut, use_container_width=True)