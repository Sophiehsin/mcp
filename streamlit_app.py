# app.py
import streamlit as st
import requests
import json
import os
from datetime import datetime

# ====== 設定區 ======
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "your_openrouter_api_key")
ZAPIER_WEBHOOK_URL = st.secrets.get("ZAPIER_WEBHOOK_URL", "your_zapier_webhook_url")

# ====== GPT 呼叫函式 ======
def get_schedule_suggestion(user_input):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "你是一個行程規劃助手，請根據輸入幫我用條列式排出今日行程，確保行程有明確的時間點"},
            {"role": "user", "content": user_input}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    return result['choices'][0]['message']['content']

# ====== Zapier 整合函式 ======
def send_to_zapier(user_input, schedule):
    payload = {
        "user_input": user_input,
        "suggested_schedule": schedule,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    response = requests.post(ZAPIER_WEBHOOK_URL, json=payload)
    return response.status_code == 200

# ====== Streamlit 介面 ======
st.set_page_config(page_title="AI 行程規劃助手", page_icon="📅", layout="wide")

# 標題與說明
st.title("📅 AI 行程規劃助手")
st.markdown("""
此應用程式可以幫助你規劃今日行程，並自動同步到 Google Calendar、Notion 和發送通知。

**使用流程：**
1. 輸入你今天的計劃或想法
2. AI 會生成建議行程表
3. 選擇將行程同步到其他平台
""")

# 側邊欄配置
with st.sidebar:
    st.header("設定")
    st.info("行程同步後將自動發送到以下平台：")
    st.markdown("- ✅ Google Calendar")
    st.markdown("- ✅ Notion 資料庫")
    st.markdown("- ✅ 通知 (Slack/Email/LINE)")
    
    if OPENROUTER_API_KEY == "your_openrouter_api_key":
        st.warning("尚未設定 OpenRouter API Key")
    
    if ZAPIER_WEBHOOK_URL == "your_zapier_webhook_url":
        st.warning("尚未設定 Zapier Webhook URL")

# 主要介面
user_input = st.text_area("請輸入你今天的想法和計劃，我會幫你排出行程表", height=150)

# 初始化 session state 變數
if 'schedule' not in st.session_state:
    st.session_state.schedule = None
if 'sync_status' not in st.session_state:
    st.session_state.sync_status = None

# 生成行程按鈕
if st.button("✨ 生成行程建議"):
    if not user_input:
        st.error("請先輸入今日計劃")
    else:
        with st.spinner("正在生成建議行程..."):
            try:
                schedule = get_schedule_suggestion(user_input)
                st.session_state.schedule = schedule
            except Exception as e:
                st.error(f"生成行程時發生錯誤: {str(e)}")

# 顯示生成的行程
if st.session_state.schedule:
    st.markdown("### 📋 建議行程：")
    st.markdown(st.session_state.schedule)
    
    # 同步到其他平台的按鈕
    if st.button("🔄 同步到 Google Calendar、Notion 和發送通知"):
        with st.spinner("正在同步資料..."):
            success = send_to_zapier(user_input, st.session_state.schedule)
            if success:
                st.session_state.sync_status = "success"
                st.success("✅ 成功傳送至 Zapier！資料正在自動整合到各平台")
            else:
                st.session_state.sync_status = "error"
                st.error("❌ 傳送失敗，請檢查 Zapier Webhook URL 設定")

# 頁尾
st.markdown("---")
st.markdown("使用 OpenRouter API 和 Zapier 自動化整合")
