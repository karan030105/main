import gradio as gr
import requests
import pandas as pd
import time

FIREBASE_URL = "https://flood-alert--2-default-rtdb.asia-southeast1.firebasedatabase.app/WaterQuality/LiveData.json"

# Store history for graphs
history = {
    "time": [],
    "temperature": [],
    "ph": [],
    "turbidity": [],
    "tds": []
}

def get_data():
    try:
        res = requests.get(FIREBASE_URL, timeout=5)
        data = res.json()

        if data:
            return data
        else:
            return None
    except:
        return None


def update():
    data = get_data()

    if not data:
        return "Error", "-", "-", "-", None, "⚠ No Data"

    t = time.strftime("%H:%M:%S")

    temp = data.get("temperature", 0)
    ph = data.get("ph", 0)
    turb = data.get("turbidity", 0)
    tds = data.get("tds", 0)

    # Save history (limit size)
    history["time"].append(t)
    history["temperature"].append(temp)
    history["ph"].append(ph)
    history["turbidity"].append(turb)
    history["tds"].append(tds)

    if len(history["time"]) > 20:
        for k in history:
            history[k].pop(0)

    df = pd.DataFrame(history)

    # 🚨 ALERT LOGIC
    alert = "✅ Water Quality Normal"

    if ph < 6 or ph > 8.5:
        alert = "⚠ pH Unsafe"
    elif turb > 1000:
        alert = "⚠ High Turbidity"
    elif tds > 500:
        alert = "⚠ High TDS"

    return (
        f"{temp:.2f} °C",
        f"{ph:.2f}",
        f"{turb:.2f} NTU",
        f"{tds:.2f} ppm",
        df,
        alert
    )


with gr.Blocks(theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # 💧 Smart Water Quality Dashboard
    ### Real-Time IoT Monitoring System
    """)

    with gr.Row():
        temp = gr.Textbox(label="🌡 Temperature")
        ph = gr.Textbox(label="🧪 pH")

    with gr.Row():
        turb = gr.Textbox(label="💧 Turbidity")
        tds = gr.Textbox(label="⚡ TDS")

    alert = gr.Textbox(label="🚨 Alert Status")

    gr.Markdown("## 📈 Live Trends")

    graph = gr.LinePlot(
        x="time",
        y=["temperature", "ph", "turbidity", "tds"],
        title="Sensor Trends",
        height=300
    )

    # 🔥 FIXED AUTO REFRESH (NO BUILD ERROR)
    demo.load(update, None, [temp, ph, turb, tds, graph, alert])
    demo.load(update, None, [temp, ph, turb, tds, graph, alert], every=5)

demo.launch()