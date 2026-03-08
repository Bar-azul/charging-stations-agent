import streamlit as st
from pathlib import Path
import os

st.set_page_config(page_title="Smoke Test", page_icon="⚡", layout="wide")

st.title("Charging Stations Agent - Smoke Test")
st.success("האפליקציה עלתה בהצלחה ב-Streamlit Cloud")

app_dir = Path(__file__).parent

st.write("Current working dir:", os.getcwd())
st.write("APP_DIR:", str(app_dir))
st.write("Files in APP_DIR:", os.listdir(app_dir))

st.info("אם אתה רואה את המסך הזה, הבעיה אינה ב-Streamlit עצמו אלא בקוד/תלויות/DB.")