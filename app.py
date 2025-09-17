import streamlit as st
import pandas as pd
import serial
import joblib
import time
import json
import random

# --------------------------
# Load trained ML model
# --------------------------
model = joblib.load("herb_classifier.joblib")
FEATURES = ["LDR_Analog", "pH"]

# Herb info dictionary
HERB_INFO = {
    "Tulsi": {
        "Properties": "Rich in antioxidants, antimicrobial",
        "Uses": "Helps with cold, cough, respiratory issues"
    },
    "Neem": {
        "Properties": "Anti-bacterial, antifungal, blood purifier",
        "Uses": "Treats skin diseases, dental issues, boosts immunity"
    },
    "Ashwagandha": {
        "Properties": "Adaptogenic, stress reliever",
        "Uses": "Reduces stress, boosts energy, improves sleep"
    },
    "Unknown": {
        "Properties": "Not in dataset",
        "Uses": "Needs further research"
    }
}

# --------------------------
# Setup Arduino Serial
# --------------------------
try:
    arduino = serial.Serial("COM3", 9600, timeout=1)  # Change COM port if needed
    time.sleep(2)
    connected = True
except:
    arduino = None
    connected = False

# --------------------------
# Navigation
# --------------------------
st.set_page_config(page_title="E-Tongue Dashboard", layout="wide")
st.sidebar.title("🔎 Navigation")
page = st.sidebar.radio("Go to", ["Instructions", "Home", "Herb Classifier", "Dataset"])

# --------------------------
# Instructions Page
# --------------------------
if page == "Instructions":
    st.title("📖 Instructions")
    st.markdown("""
    1. Place the herb sample inside the sensing chamber on the electrode base.  
    2. Ensure proper contact between the herb extract and the sensors.  
    3. Close the chamber lid to avoid external interference.  
    4. Click on **Herb Classifier** to start the analysis.  

    🔬 The sensors (LDR + pH) capture the response, which is then processed by the Arduino.  
    📡 The data is sent to the ML model, which classifies the herb and displays its medicinal properties.
    """)

# --------------------------
# Home Page
# --------------------------
elif page == "Home":
    # Title with styling
    st.markdown("<h1 style='text-align: center; color: green;'>🌿 E-Tongue Project</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Smart Herbal Identification System using IoT + ML</h3>", unsafe_allow_html=True)

    st.write("---")

    # Project Highlights in 3 columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔬 Sensor-Based")
        st.markdown("Captures **real-time data** using LDR and Soil pH sensors.")

    with col2:
        st.markdown("### 🤖 ML Powered")
        st.markdown("Trained **machine learning model** identifies medicinal herbs.")

    with col3:
        st.markdown("### 💊 Healthcare Impact")
        st.markdown("Helps in **classifying herbs** and highlighting their medicinal uses.")

    st.write("---")

    # About Section
    st.markdown("""
    ### 📌 About the Project  
    This project integrates **IoT sensors** with **Machine Learning** to classify medicinal herbs.  
    Using an **E-Tongue approach**, sensor responses are captured, processed, and displayed in an interactive dashboard.  
    """, unsafe_allow_html=True)

    st.write("---")

    # Shortcut Button to Classifier
    if st.button("🚀 Start Herb Analysis"):
        st.session_state.page_redirect = "Herb Classifier"

# --------------------------
# Herb Classifier Page
# --------------------------
elif page == "Herb Classifier" or st.session_state.get("page_redirect") == "Herb Classifier":
    st.title("🌿 Herb Classifier")
    st.subheader("Real-time Herb Identification")

    if connected:
        if st.button("Start Herb Analysis"):
            with st.spinner("Collecting sensor data..."):
                time.sleep(2)  # Simulate reading delay

                # Read from Arduino (JSON expected)
                try:
                    raw = arduino.readline().decode("utf-8").strip()
                    data = json.loads(raw)
                except:
                    # For demo, use fake data if Arduino not sending
                    data = {
                        "LDR_Analog": round(random.uniform(0, 1023), 2),
                        "LDR_Digital": random.choice([0, 1]),
                        "pH": round(random.uniform(5.5, 8.5), 2)
                    }

                # Predict herb
                X = [[data[f] for f in FEATURES]]
                herb_prediction = model.predict(X)[0]

                # Show progress bar for interactivity
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress.progress(i + 1)

                # Display results
                st.success(f"🌱 Identified Herb: **{herb_prediction}**")
                st.metric("LDR Analog", f"{data['LDR_Analog']}")
                st.metric("LDR Digital", f"{data['LDR_Digital']}")
                st.metric("Soil pH", f"{data['pH']}")

                # Herb info
                info = HERB_INFO.get(herb_prediction, HERB_INFO["Unknown"])
                st.subheader("✨ Herb Properties")
                st.write(info["Properties"])
                st.subheader("💊 Medicinal Uses")
                st.write(info["Uses"])

                # Alerts
                if data["pH"] < 5.5 or data["pH"] > 8.5:
                    st.error("⚠️ Abnormal pH detected – sample may be invalid!")
    else:
        st.warning("⚠️ Arduino not connected. Please connect and restart.")

    # Clear redirect state
    st.session_state.page_redirect = None

# --------------------------
# Dataset Page
# --------------------------
elif page == "Dataset":
    st.title("📊 Dataset Collected")
    st.info("This table displays the dataset samples used for training and real-time analysis.")
    
    # For demo – later replace with your real dataset
    dataset = pd.DataFrame([
        {"LDR_Analog": 320, "pH": 6.8, "Herb": "Tulsi"},
        {"LDR_Analog": 550, "pH": 7.2, "Herb": "Neem"},
        {"LDR_Analog": 430, "pH": 6.5, "Herb": "Ashwagandha"}
    ])
    st.dataframe(dataset)
