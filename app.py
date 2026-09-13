import os
import streamlit as st
import streamlit.components.v1 as components

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="SPRZones - Institutional Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Sidebar Navigation
st.sidebar.title("🤖 SPRZones Terminal")
view_option = st.sidebar.radio(
    "Select View",
    ["Institutional Report", "Live Trading Signals", "Agent Settings"]
)

# 3. Render HTML Report Function
def load_weekly_report():
    file_path = os.path.join("dashboard", "weekly_report.html")
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Render HTML with scrolling and proper height
        components.html(html_content, height=1400, scrolling=True)
    else:
        st.error(f"⚠️ Report File Not Found at `{file_path}`! Please check your file directory.")

# 4. Routing Logic
if view_option == "Institutional Report":
    st.markdown("### 🏛️ Institutional Weekly Market Strategy")
    load_weekly_report()

elif view_option == "Live Trading Signals":
    st.markdown("### ⚡ Live Trading & Signals Desk")
    st.info("Signals data updating via GitHub Actions...")

elif view_option == "Agent Settings":
    st.markdown("### ⚙️ Multi-Agent Configuration")
    st.json({"status": "Active", "agents": ["Transformer_Moderator", "Quant_Risk_Agent"]})
