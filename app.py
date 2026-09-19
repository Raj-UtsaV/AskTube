import streamlit as st
from dotenv import load_dotenv

from src.ui import run


load_dotenv()
st.set_page_config(
    page_title="AskTube | YouTube Q&A",
    page_icon="assets/asktube-banner.png",
    layout="wide",
    initial_sidebar_state="expanded",
)
run()
