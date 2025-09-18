import streamlit as st
import pandas as pd
import time
import json
import os

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
# Try import joblib (model loader)
# --------------------------
def try_load_model(path="herb_classifier.joblib"):
    """Attempt to load a joblib model from the repo root (or uploaded file)."""
    try:
        import joblib
    except Exception as e:
        st.session_state.MODEL_AVAILABLE = False
        st.session_state.model = None
        st.error("❌ `joblib` is not installed in the environment. Add `joblib` to requirements.txt and redeploy.")
        return

    if not os.path.exists(path):
        st.session_state.MODEL_AVAILABLE = False
        st.session_state.model = None
        st.warning(f"⚠️ Model file not found at `{path}`. Please add `herb_classifier.joblib` to your repo (or upload below).")
        return

    try:
        st.session_state.model = joblib.load(path)
        st.session_state.MODEL_AVAILABLE = True
        # Get expected features from model if scikit-learn provides it
        try:
            st.session_state.expected_features = int(st.session_state.model.n_features_in_)
        except Exception:
            # fallback to 11 (previous assumption)
            st.session_state.expected_features = 11
    except Exception as e:
        st.session_state.MODEL_AVAILABLE = False
        st.session_state.model = None
        st.error(f"❌ Failed loading model: {e}")

# attempt to load model from default path at app start
try_load_model()

# --------------------------
# Try import pyserial (only used locally)
# Do NOT open ports automatically (avoid locking them)
# --------------------------
try:
    import serial
    from serial.tools import list_ports
    st.session_state.serial_available = True
except Exception:
    st.session_state.serial_available = False

def refresh_serial_ports():
    """Refresh list of available serial ports (local machine only)."""
    ports = []
    if st.session_state.serial_available:
        try:
            ports_info = list_ports.comports()
            for p in ports_info:
                # (device, description)
                ports.append((p.device, p.description))
        except Exception as e:
            ports = []
    st.session_state.serial_ports = ports

# initial refresh
refresh_serial_ports()

# --------------------------
# UI & Pages
# --------------------------
st.set_page_config(page_title="E-Tongue Dashboard", layout="wide")
st.sidebar.title("🔎 Navigation")
page = st.sidebar.radio("Go to", ["Instructions", "Home", "Herb Classifier", "Dataset"])

# Herb info dictionary (unchanged)
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
# Instructions Page
# --------------------------
if page == "Instructions":
    st.title("📖 Instructions")
    st.markdown("""
    1. Connect your Arduino to the computer running this Streamlit app.  
    2. Make sure the Arduino is sending JSON lines containing at least `LDR_Analog` and `pH`, e.g.:
       ```json
       {"LDR_Analog": 320, "LDR_Digital": 1, "pH": 6.8}
       ```
    3. Go to **Herb Classifier**, select the port and click **Connect**.  
    4. Click **Start Herb Analysis** after successful connection.
    """)
    st.write("---")
    st.info("Important: This app will **not** run in demo mode — real Arduino connection is required.")

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
        st.markdown("Trained **machine learning model** identifies medicinal herbs.")
    with col3:
        st.markdown("### 💊 Healthcare Impact")
        st.markdown("Helps in **classifying herbs** and highlighting medicinal uses.")
    st.write("---")
    st.markdown("""
    ### 📌 About the Project  
    This project integrates **IoT sensors** with **ML** to classify medicinal herbs.  
    """)
    st.write("---")
    if st.button("🚀 Start Herb Analysis"):
        st.session_state.page_redirect = "Herb Classifier"

# --------------------------
# Herb Classifier Page (REQUIRES Arduino)
# --------------------------
elif page == "Herb Classifier" or st.session_state.get("page_redirect") == "Herb Classifier":
    st.title("🌿 Herb Classifier — Arduino required")
    st.write("This page runs **only** when an Arduino is connected and a model is available.")

    # Model status block
    st.subheader("Model status")
    if st.session_state.MODEL_AVAILABLE:
        st.success(f"✅ Model loaded. Expected features: {st.session_state.expected_features}")
    else:
        st.error("❌ Model not available. Place `herb_classifier.joblib` in repo root or upload it below.")
        uploaded = st.file_uploader("Upload herb_classifier.joblib (optional)", type=["joblib", "pkl"])
        if uploaded is not None:
            # save to working dir and try load
            with open("herb_classifier.joblib", "wb") as f:
                f.write(uploaded.getbuffer())
            try_load_model("herb_classifier.joblib")
            st.experimental_rerun()
        # do not proceed if model missing
        st.stop()

    # Serial (Arduino) status block
    st.subheader("Arduino connection")
    if not st.session_state.serial_available:
        st.error("❌ `pyserial` / `serial` not available in this environment. Arduino connectivity will not work here.")
        st.info("If you're running locally, install pyserial (`pip install pyserial`) and run Streamlit locally.")
        st.stop()

    # Show available ports & controls
    cols = st.columns([2, 1, 1])
    with cols[0]:
        if st.button("🔄 Refresh ports"):
            refresh_serial_ports()
    with cols[1]:
        if st.button("❌ Disconnect") and st.session_state.serial_connected:
            try:
                st.session_state.serial_obj.close()
            except Exception:
                pass
            st.session_state.serial_obj = None
            st.session_state.serial_connected = False
            st.success("Disconnected.")
    with cols[2]:
        st.write("")  # spacer

    # Show port selection
    if len(st.session_state.serial_ports) == 0:
        st.warning("No serial ports detected. Plug in the Arduino and click 'Refresh ports'.")
        st.stop()

    port_options = [f"{dev} — {desc}" for dev, desc in st.session_state.serial_ports]
    selected = st.selectbox("Select serial port", port_options)
    selected_port = selected.split(" — ")[0]  # device like COM3 or /dev/ttyUSB0

    # Connect button
    if not st.session_state.serial_connected:
        if st.button("Connect to selected port"):
            baud = st.number_input("Baudrate", value=9600, step=1)
            try:
                ser = serial.Serial(selected_port, int(baud), timeout=2)
                time.sleep(2)  # allow Arduino to reset
                st.session_state.serial_obj = ser
                st.session_state.serial_connected = True
                st.success(f"Connected to {selected_port} at {baud}.")
            except Exception as e:
                st.session_state.serial_obj = None
                st.session_state.serial_connected = False
                st.error(f"Failed to open port: {e}")
                st.stop()
    else:
        st.success(f"✅ Connected to {st.session_state.serial_obj.port}")
        if st.button("Reconnect (close & reopen)"):
            try:
                st.session_state.serial_obj.close()
            except Exception:
                pass
            st.session_state.serial_connected = False
            st.experimental_rerun()

    # Now the Arduino is connected and model loaded -> proceed with analysis
    if st.session_state.serial_connected and st.session_state.MODEL_AVAILABLE:
        st.write("---")
        st.subheader("Run analysis")
        if st.button("Start Herb Analysis"):
            with st.spinner("Reading from Arduino (waiting for a JSON line)..."):
                try:
                    ser = st.session_state.serial_obj
                    raw_bytes = ser.readline()
                    raw = raw_bytes.decode("utf-8", errors="ignore").strip()
                    if raw == "":
                        st.error("No data received from Arduino. Ensure the Arduino is sending JSON and try again.")
                        st.stop()
                    # Parse JSON
                    try:
                        data = json.loads(raw)
                    except Exception as e:
                        st.error(f"Failed to parse JSON from Arduino: {e}\nRaw: {raw}")
                        st.stop()

                    # Validate required keys
                    if "LDR_Analog" not in data or "pH" not in data:
                        st.error("Incoming data must contain at least 'LDR_Analog' and 'pH' fields.")
                        st.write("Received keys:", list(data.keys()))
                        st.stop()

                    # Build feature vector and pad to expected length
                    expected = st.session_state.expected_features or 11
                    # Put your actual two values first, then pad zeros for the rest
                    X = [[float(data["LDR_Analog"]), float(data["pH"])] + [0.0] * max(0, expected - 2)]

                    # Predict
                    try:
                        pred = st.session_state.model.predict(X)[0]
                    except Exception as e:
                        st.error(f"Model prediction failed: {e}")
                        st.stop()

                    # Show results
                    st.success(f"🌱 Identified Herb: **{pred}**")
                    st.metric("LDR Analog", f"{data['LDR_Analog']}")
                    st.metric("LDR Digital", f"{data.get('LDR_Digital', 'N/A')}")
                    st.metric("Soil pH", f"{data['pH']}")

                    info = HERB_INFO.get(pred, HERB_INFO["Unknown"])
                    st.subheader("✨ Herb Properties")
                    st.write(info["Properties"])
                    st.subheader("💊 Medicinal Uses")
                    st.write(info["Uses"])

                    if float(data["pH"]) < 5.5 or float(data["pH"]) > 8.5:
                        st.error("⚠️ Abnormal pH detected – sample may be invalid!")

                except Exception as e:
                    st.error(f"Unexpected error while reading from serial: {e}")

    st.session_state.page_redirect = None

# --------------------------
# Dataset Page
# --------------------------
elif page == "Dataset":
    st.title("📊 Dataset Collected")
    st.info("This table shows example dataset.")
    dataset = pd.DataFrame([
        {"LDR_Analog": 320, "pH": 6.8, "Herb": "Tulsi"},
        {"LDR_Analog": 550, "pH": 7.2, "Herb": "Neem"},
        {"LDR_Analog": 430, "pH": 6.5, "Herb": "Ashwagandha"}
    ])
    st.dataframe(dataset)
