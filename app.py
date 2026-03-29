import streamlit as st
import requests
import pandas as pd
import time

FIREBASE_URL = "https://flood-alert--2-default-rtdb.asia-southeast1.firebasedatabase.app/WaterQuality/LiveData.json"

st.set_page_config(page_title="Water Quality Dashboard", layout="wide")

st.title("💧 Smart Water Quality Monitoring System")

placeholder = st.empty()
history = []

while True:
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        data = res.json()

        if data:
            temp = data.get("temperature", 0)
            ph = data.get("ph", 0)
            turb = data.get("turbidity", 0)
            tds = data.get("tds", 0)

            history.append({
                "Temp": temp,
                "pH": ph,
                "Turbidity": turb,
                "TDS": tds
            })

            df = pd.DataFrame(history[-20:])

            with placeholder.container():

                st.subheader("📊 Live Sensor Data")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("🌡 Temperature", f"{temp:.2f} °C")
                col2.metric("🧪 pH", f"{ph:.2f}")
                col3.metric("💧 Turbidity", f"{turb:.2f}")
                col4.metric("⚡ TDS", f"{tds:.2f}")

                st.subheader("📈 Trends")
                st.line_chart(df)

                # 🚨 Alerts
                st.subheader("🚨 System Status")

                if ph < 6 or ph > 8.5:
                    st.error("⚠ Unsafe pH Level")
                elif turb > 1000:
                    st.warning("⚠ High Turbidity")
                elif tds > 500:
                    st.warning("⚠ High TDS")
                else:
                    st.success("✅ Water Quality Normal")

        time.sleep(5)

    except:
        st.error("⚠ Error fetching data from Firebase")
        time.sleep(5)
