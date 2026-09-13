import os
import streamlit as st
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(
    page_title="SPRZones - Institutional Intelligence Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Sidebar Setup
st.sidebar.title("🤖 SPRZones Terminal")
st.sidebar.caption("Multi-Agent Quantitative Strategy Desk")

view_option = st.sidebar.radio(
    "Navigation",
    ["🌐 Institutional Strategy Report", "⚡ Trading Signals Desk", "⚙️ System Configuration"]
)

# 3. HTML Report Renderer
def load_weekly_report():
    file_path = os.path.join("dashboard", "weekly_report.html")
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Render HTML component inside Streamlit Iframe
        components.html(html_content, height=1400, scrolling=True)
    else:
        st.error(f"⚠️ Report File missing at `{file_path}`. Please ensure 'weekly_report.html' is inside the 'dashboard/' folder.")

# 4. Routing Logic
if view_option == "🌐 Institutional Strategy Report":
    load_weekly_report()

elif view_option == "⚡ Trading Signals Desk":
    st.title("⚡ Quantitative Trading Signals Desk")
    st.info("System connected to live signal pipeline (`data/signals.json`).")

elif view_option == "⚙️ System Configuration":
    st.title("⚙️ Multi-Agent Settings")
    st.json({
        "status": "Active",
        "agents": ["Macro_Global_Agent", "Quant_Risk_Agent", "Moderator_Transformer"],
        "pipeline": "GitHub Actions Auto-Update"
    })
