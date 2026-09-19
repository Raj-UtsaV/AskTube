import os
from dataclasses import dataclass

import streamlit as st


def get_secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value

    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    huggingface_api_token: str = ""


def load_settings() -> Settings:
    return Settings(
        groq_api_key=get_secret("GROQ_API_KEY"),
        groq_model=get_secret("GROQ_MODEL", Settings.groq_model),
        embedding_model=get_secret("EMBEDDING_MODEL", Settings.embedding_model),
        huggingface_api_token=(
            get_secret("HUGGINGFACEHUB_API_TOKEN") or get_secret("HF_TOKEN")
        ),
    )
