# app.py
import streamlit as st
import requests
import json
import os
from datetime import datetime
import sys
from together import Together
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle
import pathlib

# ====== 設定區 ======
TOGETHER_API_KEY = st.secrets.get("TOGETHER_API_KEY", "your_together_api_key")
N8N_WEBHOOK_URL = st.secrets.get("N8N_WEBHOOK_URL", "your_n8n_webhook_url")

# Google OAuth 設定
GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_PROJECT_ID = st.secrets.get("GOOGLE_PROJECT_ID", "")
GOOGLE_REDIRECT_URI = st.secrets.get("GOOGLE_REDIRECT_URI", "http://localhost:8502")

# 調試信息
print(f"[DEBUG] Google Client ID: {GOOGLE_CLIENT_ID[:10]}...")
print(f"[DEBUG] Google Client Secret: {GOOGLE_CLIENT_SECRET[:10]}...")
print(f"[DEBUG] Google Project ID: {GOOGLE_PROJECT_ID}")

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

def convert_datetime(obj):
    if isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']

# 初始化 session state
if 'google_credentials' not in st.session_state:
    st.session_state.google_credentials = None
if 'google_authenticated' not in st.session_state:
    st.session_state.google_authenticated = False

# Google OAuth 認證函數
def get_google_credentials():
    """處理 Google OAuth 認證流程"""
    if st.session_state.google_credentials:
        return st.session_state.google_credentials

    # 檢查配置是否完整
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_PROJECT_ID:
        st.error("未設定 Google OAuth 客戶端配置")
        st.error(f"Client ID: {'已設定' if GOOGLE_CLIENT_ID else '未設定'}")
        st.error(f"Client Secret: {'已設定' if GOOGLE_CLIENT_SECRET else '未設定'}")
        st.error(f"Project ID: {'已設定' if GOOGLE_PROJECT_ID else '未設定'}")
        return None

    try:
        # 創建 OAuth 流程
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )

        # 生成認證 URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        # 顯示登入按鈕
        if st.button("🔑 登入 Google 帳戶"):
            st.markdown(f'<a href="{auth_url}" target="_self">點擊這裡進行 Google 登入</a>', unsafe_allow_html=True)
            return None

        # 處理回調
        if 'code' in st.experimental_get_query_params():
            code = st.experimental_get_query_params()['code'][0]
            flow.fetch_token(code=code)
            credentials = flow.credentials
            st.session_state.google_credentials = credentials
            st.session_state.google_authenticated = True
            st.experimental_rerun()
            return credentials

    except Exception as e:
        st.error(f"Google 認證設定錯誤: {str(e)}")
        st.error("請確認 Google OAuth 客戶端配置是否正確")
        return None

    return None

# 檢查 Google 認證狀態
def check_google_auth():
    """檢查 Google 認證狀態"""
    if not st.session_state.google_authenticated:
        st.warning("請先登入 Google 帳戶以使用日曆功能")
        return False
    return True

# 全域 client 初始化
client = None
if TOGETHER_API_KEY and TOGETHER_API_KEY != "your_together_api_key":
    try:
        client = Together(api_key=TOGETHER_API_KEY)
    except Exception as e:
        st.error(f"Together client 初始化失敗: {e}")

# ====== 標準 API 呼叫 (使用官方格式) ======
def call_together_api(api_key, prompt, model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"):
    """使用 Together AI SDK 生成回應"""
    print(f"[DEBUG] Input prompt: {prompt}")
    print(f"[DEBUG] Encoded length: {len(prompt.encode('utf-8'))} bytes")

    if not api_key:
        return "API 錯誤: 未設定 API Key"
        
    try:
        # 使用全域 client
        if not client:
            return "API 錯誤: Together client 未初始化"
            
        system_message = (
            "你是一個行程規劃助手。請將輸入的行程資訊轉換成以下固定格式：\n"
            "1. **[開始時間] - [結束時間]** [活動名稱]\n\n"
            "規則：\n"
            "1. 每行都必須以數字編號開始\n"
            "2. 時間必須用粗體標記 (**)**\n"
            "3. 時間格式必須是 HH:MM\n"
            "4. 如果沒有明確說明開始時間與結束時間，但是有提到與時間相關關鍵字，請直接訂出最接近的『開始時間 - 結束時間』\n"
            "5. 如果完全沒有說明時間、也沒有提及關鍵字、只有活動名稱，使用早上九點當作開始時間，結束時間為開始時間加上\n"
            "6. 範例輸入：早上晨會，10:30到中午客戶拜訪\n"
            "輸出：\n"
            "1. **09:00 - 10:00** 晨會\n"
            "2. **10:30 - 12:00** 客戶拜訪\n\n"
            "請直接輸出行程清單，不要加入任何其他說明文字。"
        )

        # 使用 SDK 的 chat completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = f"API 呼叫失敗: {str(e)}"
        st.error(error_msg)
        print(f"[DEBUG] API error details: {str(e)}")
        return error_msg


# ====== GPT 呼叫函式 ======
def get_schedule_suggestion(user_input, model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"):
    """呼叫 Together API 生成行程建議"""
    try:
        # 嘗試呼叫 API
        result = call_together_api(TOGETHER_API_KEY, user_input, model)
        
        # 檢查結果是否包含錯誤信息
        if "API 錯誤" in result or "API 呼叫失敗" in result or "HTTP 錯誤" in result:
            st.error("生成行程失敗")
        
        return result
    except Exception as e:
        error_msg = f"處理請求時發生錯誤: {str(e)}"
        st.error(error_msg)
        return error_msg

# ====== N8N 整合函式 ======
def send_to_n8n(user_input, schedule, date=None, access_token=None, refresh_token=None, token_expiry=None, user_email=None):
    payload = {
    "user_input": user_input,
    "suggested_schedule": schedule,
    "timestamp": datetime.now().isoformat(),
    "date": date.today().isoformat(),
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_expiry": token_expiry,
    "email": user_email
    }
    if date:
        payload["date"] = str(date)
    
    try:
        # 調試信息
        print(f"[DEBUG] n8n payload size: {len(json.dumps(payload, ensure_ascii=False, default=str).encode('utf-8'))} bytes")
        
        # 設置請求頭 - 確保只使用 ASCII 字符
        headers = {
            "Content-Type": "application/json",
        }

        payload = convert_datetime(payload)
        # 發送請求到 n8n
        response = requests.post(
            N8N_WEBHOOK_URL,
            headers=headers,
            json=payload,  # 使用 json 參數而非 data
        )
        
        # 強制設定響應編碼為 UTF-8
        response.encoding = 'utf-8'
        
        # 檢查回應
        if response.status_code == 200:
            print(f"[DEBUG] n8n 成功響應: {response.text[:50]}...")
            return True
        else:
            st.error(f"n8n 回應錯誤: {response.status_code}")
            print(f"[DEBUG] n8n 錯誤響應: {response.text[:100]}...")
            return False
            
    except Exception as e:
        st.error(f"傳送到 n8n 時發生錯誤: {e}")
        st.exception(e)  # 顯示完整 traceback
        return False

# ====== Streamlit 介面 ======
st.set_page_config(page_title="AI 行程規劃助手", page_icon="📅", layout="wide")

# 標題與說明
st.title("📅 AI 行程規劃助手")
st.markdown("""
此應用程式可以幫助你規劃今日行程，並自動同步多個活動至 Google Calendar。

**使用流程：**
1. 輸入你今天的計劃或想法
ex: 我今天早上要跟欣欣銀行開會、中午要與同事聚餐、下午要先去聿聿人壽完成駐點、然後要回到公司開會、最後完成 merge request 審核、最後晚上要去練跑

2. AI 會生成建議行程表
3. 編輯並確認你的行程
4. 將行程同步到其他平台
""")

# 側邊欄配置
with st.sidebar:
    st.markdown("""
    ### 帳戶設定
    """)
    
    # Google 認證狀態
    if st.session_state.google_authenticated:
        st.success("✅ 已登入 Google 帳戶")
        if st.button("登出"):
            st.session_state.google_credentials = None
            st.session_state.google_authenticated = False
            st.experimental_rerun()
    else:
        get_google_credentials()

    st.markdown("""
    ### 模型設定
    """)
    # Together 模型選擇
    model_options = [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        #"deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        "meta-llama/Llama-Vision-Free"
    ]
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = model_options[0]
    st.session_state.selected_model = st.selectbox("選擇模型", model_options, index=model_options.index(st.session_state.selected_model))
    
    st.markdown("---")
    st.markdown("Together AI API ＆ n8n 連線狀態")

    # 調試區塊移到側邊欄最下方
    with st.expander("調試信息"):
        st.write("API Key 狀態:", "已設定" if TOGETHER_API_KEY != "your_together_api_key" else "未設定")
        st.write("Webhook URL 狀態:", "已設定" if N8N_WEBHOOK_URL != "your_n8n_webhook_url" else "未設定")
        st.write("Google 認證狀態:", "已登入" if st.session_state.google_authenticated else "未登入")
        st.write("所選模型:", st.session_state.selected_model)
        st.write("Python 版本:", sys.version)
        st.write("操作系統:", os.name)
        

# 主頁日期選擇器（輸入框上方）
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()
st.session_state.selected_date = st.date_input("選擇要安排的日期", value=st.session_state.selected_date)

# 主要介面
user_input = st.text_area("請輸入你今天的想法和計劃，我會幫你排出行程表", height=150)

# 初始化 session state 變數
if 'schedule' not in st.session_state:
    st.session_state.schedule = None
if 'sync_status' not in st.session_state:
    st.session_state.sync_status = None

# 生成行程按鈕
generate_button = st.button("✨ 生成行程建議")
if generate_button:
    if not user_input:
        st.error("請先輸入今日計劃")
    else:
        with st.spinner("正在生成建議行程..."):
            try:
                # 使用側邊欄選擇的模型
                schedule = get_schedule_suggestion(user_input, st.session_state.selected_model)
                st.session_state.schedule = schedule
            except Exception as e:
                st.error(f"生成行程時發生錯誤: {str(e)}")
                st.session_state.schedule = None

# 顯示生成的行程
if st.session_state.schedule and "API 錯誤" not in st.session_state.schedule:
    st.markdown("### 📋 建議行程（可編輯）：")
    if st.session_state.get("editable_schedule") != st.session_state.schedule:
        st.session_state.editable_schedule = st.session_state.schedule
    st.session_state.editable_schedule = st.text_area(
        "你可以在這裡修改行程內容再同步到其他平台",
        value=st.session_state.editable_schedule,
        height=200
    )

    # 同步到其他平台的按鈕
    sync_button = st.button("🔄 同步到 Google Calendar")
    if sync_button:
        if not check_google_auth():
            st.error("請先登入 Google 帳戶")
        elif TOGETHER_API_KEY == "your_together_api_key" or N8N_WEBHOOK_URL == "your_n8n_webhook_url":
            st.error("請先在設定中配置 API Key 和 Webhook URL")
        else:
            with st.spinner("正在同步資料..."):
                # 傳送認證資訊到 n8n
                access_token = st.session_state.google_credentials.token
                success = send_to_n8n(
                user_input,
                st.session_state.editable_schedule,
                date=st.session_state.selected_date,
                access_token=access_token,
                refresh_token=st.session_state.google_credentials.refresh_token if st.session_state.google_credentials else None,
                token_expiry=st.session_state.google_credentials.expiry if st.session_state.google_credentials else None,
                user_email=st.session_state.google_credentials.id_token.get("email") if st.session_state.google_credentials and st.session_state.google_credentials.id_token else None
)
                if success:
                    st.session_state.sync_status = "success"
                    st.success("✅ 成功傳送至 n8n！資料正在自動整合到各平台")
                else:
                    st.session_state.sync_status = "error"
                    st.error("❌ 傳送失敗，請檢查 n8n Webhook URL 設定")
elif st.session_state.schedule:
    # 顯示錯誤訊息
    st.error("無法生成行程")
    st.markdown(st.session_state.schedule)

