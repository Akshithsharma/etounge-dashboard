import streamlit as st
import pandas as pd
import time
import json
import os
import random

# --------------------------
# App state defaults
# --------------------------
if "model" not in st.session_state:
    st.session_state.model = None
if "MODEL_AVAILABLE" not in st.session_state:
    st.session_state.MODEL_AVAILABLE = False
if "expected_features" not in st.session_state:
    st.session_state.expected_features = None
if "serial_available" not in st.session_state:
    st.session_state.serial_available = False
if "serial_ports" not in st.session_state:
    st.session_state.serial_ports = []
if "serial_obj" not in st.session_state:
    st.session_state.serial_obj = None
if "serial_connected" not in st.session_state:
    st.session_state.serial_connected = False

# --------------------------
# Load ML model
# --------------------------
def try_load_model(path="herb_classifier.joblib"):
    try:
        import joblib
    except Exception:
        st.error("❌ joblib not installed. Add it to requirements.txt.")
        return
    if not os.path.exists(path):
        st.warning(f"⚠️ Model file `{path}` not found.")
        return
    try:
        st.session_state.model = joblib.load(path)
        st.session_state.MODEL_AVAILABLE = True
        try:
            st.session_state.expected_features = int(st.session_state.model.n_features_in_)
        except:
            st.session_state.expected_features = 11
    except Exception as e:
        st.error(f"❌ Failed to load model: {e}")

try_load_model()

# --------------------------
# Serial handling
# --------------------------
try:
    import serial
    from serial.tools import list_ports
    st.session_state.serial_available = True
except Exception:
    st.session_state.serial_available = False

def refresh_serial_ports():
    ports = []
    if st.session_state.serial_available:
        try:
            ports_info = list_ports.comports()
            for p in ports_info:
                ports.append((p.device, p.description))
        except Exception:
            ports = []
    st.session_state.serial_ports = ports

def release_serial():
    if "serial_obj" in st.session_state and st.session_state.serial_obj:
        try:
            st.session_state.serial_obj.close()
            st.session_state.serial_connected = False
        except:
            pass

refresh_serial_ports()

# --------------------------
# UI setup
# --------------------------
st.set_page_config(page_title="E-Tongue Dashboard", layout="wide")
st.sidebar.title("🔎 Navigation")
page = st.sidebar.radio("Go to", ["Instructions", "Home", "Herb Classifier", "Dataset"])

HERB_INFO = {
    "Tulsi": {"Properties": "Rich in antioxidants, antimicrobial", "Uses": "Helps with cold, cough, respiratory issues"},
    "Neem": {"Properties": "Anti-bacterial, antifungal, blood purifier", "Uses": "Treats skin diseases, dental issues, boosts immunity"},
    "Ashwagandha": {"Properties": "Adaptogenic, stress reliever", "Uses": "Reduces stress, boosts energy, improves sleep"},
    "Unknown": {"Properties": "Not in dataset", "Uses": "Needs further research"}
}

# --------------------------
# Instructions Page
# --------------------------
if page == "Instructions":
    st.title("📖 How to Use This Project")
    st.markdown("""
    ### Steps to Use:
    1. **Connect Arduino** to your computer with the correct sensors attached.  
    2. Ensure Arduino is programmed to send sensor data in JSON format like:  
       ```json
       {"LDR_Analog": 320, "LDR_Digital": 1, "pH": 6.8}
       ```  
    3. Open the **Herb Classifier** page.  
    4. Select **Arduino Mode** if you have the device connected.  
    5. Select **Demo Mode** if you want to test without hardware.  
    6. Click **Start Herb Analysis** to identify the herb.  
    """)

# --------------------------
# Home Page
# --------------------------
elif page == "Home":
    st.markdown("<h1 style='text-align: center; color: green;'>🌿 E-Tongue Project</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Smart Herbal Identification System using IoT + ML</h3>", unsafe_allow_html=True)
    st.write("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔬 Sensor-Based")
        st.markdown("Captures **real-time data** using LDR and Soil pH sensors.")
    with col2:
        st.markdown("### 🤖 ML Powered")
        st.markdown("Machine learning model identifies medicinal herbs.")
    with col3:
        st.markdown("### 💊 Healthcare Impact")
        st.markdown("Helps in **classifying herbs** and highlighting uses.")
    st.write("---")
    if st.button("🚀 Start Herb Analysis"):
        st.session_state.page_redirect = "Herb Classifier"
        st.experimental_rerun()

# --------------------------
# Herb Classifier Page
# --------------------------
elif page == "Herb Classifier" or st.session_state.get("page_redirect") == "Herb Classifier":
    st.title("🌿 Herb Classifier")

    if not st.session_state.MODEL_AVAILABLE:
        st.error("❌ Model not available. Place `herb_classifier.joblib` in folder.")
        st.stop()

    mode = st.radio("Choose Mode:", ["Arduino Mode", "Demo Mode"])

    # Arduino Mode
    if mode == "Arduino Mode":
        if not st.session_state.serial_available:
            st.error("❌ pyserial not available. Install it locally (`pip install pyserial`).")
            st.stop()

        st.subheader("Arduino Connection")
        if st.button("🔄 Refresh Ports"):
            refresh_serial_ports()

        if len(st.session_state.serial_ports) == 0:
            st.warning("No COM ports detected. Plug Arduino and refresh.")
            st.stop()

        port_options = [f"{dev} — {desc}" for dev, desc in st.session_state.serial_ports]
        selected = st.selectbox("Select port", port_options)
        selected_port = selected.split(" — ")[0]
        baud = st.number_input("Baudrate", value=9600, step=1)

        if not st.session_state.serial_connected:
            if st.button("🔗 Connect"):
                try:
                    release_serial()
                    ser = serial.Serial(selected_port, int(baud), timeout=2)
                    time.sleep(2)
                    st.session_state.serial_obj = ser
                    st.session_state.serial_connected = True
                    st.success(f"Connected to {selected_port}")
                except Exception as e:
                    st.error(f"Failed to connect: {e}")
        else:
            st.success(f"✅ Connected to {st.session_state.serial_obj.port}")
            if st.button("🔌 Disconnect"):
                release_serial()
                st.success("Disconnected.")

        if st.session_state.serial_connected:
            st.write("---")
            if st.button("Start Herb Analysis"):
                with st.spinner("Reading from Arduino..."):
                    try:
                        raw = st.session_state.serial_obj.readline().decode("utf-8", errors="ignore").strip()
                        if raw == "":
                            st.error("No data received. Check Arduino sketch.")
                            st.stop()
                        data = json.loads(raw)

                        # Progress bar
                        progress = st.progress(0)
                        for i in range(100):
                            time.sleep(0.02)
                            progress.progress(i + 1)

                        expected = st.session_state.expected_features or 11
                        X = [[float(data["LDR_Analog"]), float(data["pH"])] + [0.0] * max(0, expected - 2)]
                        pred = st.session_state.model.predict(X)[0]

                        st.success(f"🌱 Identified Herb: **{pred}**")
                        st.metric("LDR Analog", f"{data['LDR_Analog']}")
                        st.metric("LDR Digital", f"{data.get('LDR_Digital', 'N/A')}")
                        st.metric("Soil pH", f"{data['pH']}")

                        info = HERB_INFO.get(pred, HERB_INFO["Unknown"])
                        st.subheader("✨ Properties")
                        st.write(info["Properties"])
                        st.subheader("💊 Medicinal Uses")
                        st.write(info["Uses"])

                        if float(data["pH"]) < 5.5 or float(data["pH"]) > 8.5:
                            st.error("⚠️ Abnormal pH detected.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Demo Mode
    elif mode == "Demo Mode":
        st.info("ℹ️ Running in demo mode with random data (no Arduino required).")
        if st.button("Run Demo Analysis"):
            with st.spinner("Generating demo data..."):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress.progress(i + 1)

                data = {
                    "LDR_Analog": round(random.uniform(200, 800), 2),
                    "LDR_Digital": random.choice([0, 1]),
                    "pH": round(random.uniform(5.5, 8.5), 2)
                }

                expected = st.session_state.expected_features or 11
                X = [[data["LDR_Analog"], data["pH"]] + [0.0] * max(0, expected - 2)]
                pred = st.session_state.model.predict(X)[0]

                st.success(f"🌱 Identified Herb: **{pred}**")
                st.metric("LDR Analog", f"{data['LDR_Analog']}")
                st.metric("LDR Digital", f"{data['LDR_Digital']}")
                st.metric("Soil pH", f"{data['pH']}")

                info = HERB_INFO.get(pred, HERB_INFO["Unknown"])
                st.subheader("✨ Properties")
                st.write(info["Properties"])
                st.subheader("💊 Medicinal Uses")
                st.write(info["Uses"])

                if data["pH"] < 5.5 or data["pH"] > 8.5:
                    st.error("⚠️ Abnormal pH detected.")

    st.session_state.page_redirect = None

# --------------------------
# Dataset Page
# --------------------------
# --------------------------
# Dataset Page
# --------------------------
elif page == "Dataset":
    st.title("📊 Dataset Collected")

    dataset_path = "e_tongue_high_sep_dataset.csv"

    if os.path.exists(dataset_path):
        try:
            dataset = pd.read_csv(dataset_path)
            st.success(f"✅ Loaded dataset from `{dataset_path}`")
            st.dataframe(dataset)
        except Exception as e:
            st.error(f"⚠️ Failed to load dataset: {e}")
    else:
        st.error(f"❌ Dataset file `{dataset_path}` not found in the project folder.")
        st.info("Upload the file using the uploader below:")
        uploaded = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded is not None:
            dataset = pd.read_csv(uploaded)
            st.success("✅ Dataset uploaded successfully")
            st.dataframe(dataset)
