import streamlit as st
import time
import matplotlib.pyplot as plt
import sqlite3
from fpdf import FPDF
import pandas as pd

# Set page config
st.set_page_config(page_title="Advanced BMI Calculator", page_icon="📏", layout="wide")
# Custom CSS for background and theme
st.markdown(
    """
   <style>
    body {
        background-color: #f0f2f6; /* Light grayish-blue background */
        color: #333; /* Dark gray foreground color for text */
    }
    .main {
        background-color: #f0f2f6;
        color: #222; /* Slightly darker text for better contrast */
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #45a049;
        color: white;
    }
</style>

    """,
    unsafe_allow_html=True
)


# Initialize session state
if "bmi" not in st.session_state:
    st.session_state.bmi = None
if "bmi_category" not in st.session_state:
    st.session_state.bmi_category = ""
if "bmi_tip" not in st.session_state:
    st.session_state.bmi_tip = ""
if "calorie_estimate" not in st.session_state:
    st.session_state.calorie_estimate = None  # Fix: Ensure calorie estimate is stored properly

# Database setup
conn = sqlite3.connect("bmi_history.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS bmi_records (
    id INTEGER PRIMARY KEY,
    weight REAL,
    height REAL,
    bmi REAL,
    category TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Sidebar
st.sidebar.title("⚙️ Settings")
unit = st.sidebar.radio("Select Unit", ["Metric (kg/m)", "Imperial (lbs/in)"])
st.sidebar.title("📌 BMI Categories")
st.sidebar.info("""
- **Underweight:** BMI < 18.5  
- **Normal weight:** 18.5 - 24.9  
- **Overweight:** 25 - 29.9  
- **Obese:** BMI ≥ 30  
""")

# Main Section
st.title("💪 Advanced BMI Calculator")

# Input fields
name = st.text_input("Enter Your **Name**")
age = st.number_input("Enter your **Age**", min_value=10, max_value=120, step=1)
gender = st.selectbox("Select Gender", ["Male", "Female", "Other"])

if unit == "Metric (kg/m)":
    weight = st.number_input("Enter your **Weight (kg)**", min_value=1.0, format="%.2f")
    height = st.number_input("Enter your **Height (m)**", min_value=0.5, format="%.2f")
else:
    weight_lbs = st.number_input("Enter your **Weight (lbs)**", min_value=1.0, format="%.2f")
    height_in = st.number_input("Enter your **Height (inches)**", min_value=10.0, format="%.2f")
    weight = weight_lbs * 0.453592  # Convert lbs to kg
    height = height_in * 0.0254  # Convert inches to meters

# BMI Calculation
if st.button("Calculate BMI"):
    if weight > 0 and height > 0:
        bmi = weight / (height ** 2)
        st.session_state.bmi = bmi

        # Determine Category & Tips
        if bmi < 18.5:
            category = "Underweight"
            tip = "Increase protein intake and exercise."
        elif 18.5 <= bmi < 24.9:
            category = "Normal weight"
            tip = "Maintain a balanced diet."
        elif 25 <= bmi < 29.9:
            category = "Overweight"
            tip = "Reduce sugar intake and increase cardio."
        else:
            category = "Obese"
            tip = "Consider a structured fitness program."

        st.session_state.bmi_category = category
        st.session_state.bmi_tip = tip

        # Save record to database
        c.execute("INSERT INTO bmi_records (weight, height, bmi, category) VALUES (?, ?, ?, ?)",
                  (weight, height, bmi, category))
        conn.commit()

        # Display results
        st.subheader(f"📊 Your BMI: **{bmi:.2f}**")
        st.subheader(f"📌 Category: **{category}**")
        st.info(f"🧠 **Health Tip:** {tip}")

        # Calorie Suggestion
        calorie_estimate = round((10 * weight) + (6.25 * height * 100) - (5 * age) + (5 if gender == "Male" else -161))
        st.session_state.calorie_estimate = calorie_estimate  # Fix: Store calorie estimate in session state
        st.success(f"🔥 Recommended Daily Calorie Intake: **{calorie_estimate} kcal**")
    else:
        st.error("⚠️ Please enter valid values!")

# BMI History and Visualization
st.sidebar.subheader("📈 BMI History")
history = pd.read_sql("SELECT * FROM bmi_records ORDER BY timestamp DESC LIMIT 10", conn)
st.sidebar.write(history)

if len(history) > 1:
    fig, ax = plt.subplots()
    ax.plot(history['timestamp'], history['bmi'], marker='o', linestyle='-', color='b')
    ax.set_xlabel("Date")
    ax.set_ylabel("BMI")
    ax.set_title("Your BMI Progress Over Time")
    st.sidebar.pyplot(fig)

# Generate PDF Report
if st.sidebar.button("📝 Generate PDF Report"):
    if st.session_state.bmi is None:
        st.sidebar.error("⚠️ Please calculate your BMI first!")
    else:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "BMI Report", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Name: {name}", ln=True, align="L")
        pdf.cell(200, 10, f"Age: {age} years", ln=True, align="L")
        pdf.cell(200, 10, f"Gender: {gender}", ln=True, align="L")
        pdf.cell(200, 10, f"Weight: {weight:.2f} kg", ln=True, align="L")
        pdf.cell(200, 10, f"Height: {height:.2f} m", ln=True, align="L")
        pdf.cell(200, 10, f"BMI: {st.session_state.bmi:.2f}", ln=True, align="L")
        pdf.cell(200, 10, f"Category: {st.session_state.bmi_category}", ln=True, align="L")
        pdf.cell(200, 10, f"Health Tip: {st.session_state.bmi_tip}", ln=True, align="L")

        # Fix: Use session state variable for calories
        calorie_value = st.session_state.calorie_estimate if st.session_state.calorie_estimate else "N/A"
        pdf.cell(200, 10, f"Recommended Daily Calories: {calorie_value} kcal", ln=True, align="L")

        pdf_output_path = "BMI_Report.pdf"
        pdf.output(pdf_output_path)

        with open(pdf_output_path, "rb") as file:
            st.sidebar.download_button(
                label="⬇️ Download BMI Report",
                data=file,
                file_name="BMI_Report.pdf",
                mime="application/pdf",
            )

# Close DB Connection
conn.close()
