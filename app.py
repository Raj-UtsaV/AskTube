import streamlit as st
from dotenv import load_dotenv

from youtube_rag.ui import run


load_dotenv()
st.set_page_config(page_title="AskTube", page_icon="🎥")
run()
