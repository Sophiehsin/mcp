import streamlit as st

# API 設定
TOGETHER_API_KEY = st.secrets.get("TOGETHER_API_KEY", "your_together_api_key")
N8N_WEBHOOK_URL = st.secrets.get("N8N_WEBHOOK_URL", "your_n8n_webhook_url")

# Google OAuth 設定
GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_PROJECT_ID = st.secrets.get("GOOGLE_PROJECT_ID", "")
GOOGLE_REDIRECT_URI = st.secrets.get("GOOGLE_REDIRECT_URI", "http://localhost:8502")

GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI]
    }
}

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']

# 資料庫設定
DB_PATH = "chat_history.db"

# 模型設定
MODEL_OPTIONS = [
    "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
    "meta-llama/Llama-Vision-Free"
] 