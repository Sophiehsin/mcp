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
import sqlite3
import uuid

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

GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']

# 初始化所有 session state 變數
if 'google_credentials' not in st.session_state:
    st.session_state.google_credentials = None
if 'google_authenticated' not in st.session_state:
    st.session_state.google_authenticated = False
if 'planning_mode' not in st.session_state:
    st.session_state.planning_mode = "行程規劃助手"  # 預設模式
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'schedule' not in st.session_state:
    st.session_state.schedule = None
if 'editable_schedule' not in st.session_state:
    st.session_state.editable_schedule = None
if 'sync_status' not in st.session_state:
    st.session_state.sync_status = None
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

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
def get_system_message(mode):
    """根據不同模式返回對應的 system message"""
    if mode == "AI 幫你規劃":
        return (
            "你是一個專業的行程規劃助手，擅長透過對話式問答來幫助使用者規劃行程。\n"
            "請遵循以下規則：\n"
            "1. 當使用者提出需求時，先提出 2-3 個關鍵問題來了解使用者的具體需求\n"
            "2. 根據使用者的回答，提供建議的行程安排\n"
            "3. 行程安排必須包含：\n"
            "   - 具體的時間點\n"
            "   - 地點或活動名稱\n"
            "   - 交通方式建議\n"
            "   - 預估所需時間\n"
            "4. 使用友善的對話方式，並提供實用的建議\n"
            "5. 如果使用者提到特定地點，可以補充該地點的特色或注意事項\n"
            "6. 依照用戶輸入的語言進行回應\n"
            "7. 最後將所有行程整理成以下格式：\n"
            "   **[開始時間] - [結束時間]** [活動名稱]\n"
            "   備註：[相關建議或注意事項]\n"
            "8. 重要：你只能回答與行程規劃相關的問題，其他問題一律回答：'這個內容我沒有辦法回應唷！'\n"
            "9. 在回答時，請參考之前的對話內容，確保回答的連貫性和一致性"
        )
    else:  # 行程規劃助手模式
        return (
            "你是一個行程規劃助手。請將輸入的行程資訊轉換成以下固定格式：\n"
            "1. **[開始時間] - [結束時間]** [活動名稱]\n\n"
            "規則：\n"
            "1. 每行都必須以數字編號開始\n"
            "2. 時間必須用粗體標記 (**)**\n"
            "3. 時間格式必須是 HH:MM\n"
            "4. 如果沒有明確說明開始時間與結束時間，但是有提到與時間相關關鍵字，請直接訂出最接近的『開始時間 - 結束時間』\n"
            "5. 如果完全沒有說明時間、也沒有提及關鍵字、只有活動名稱，使用早上九點當作開始時間，結束時間為開始時間加上一小時\n"
            "6. 依照用戶輸入的語言進行回應\n"
            "7. 範例輸入：我今天早上要跟欣欣銀行開會、中午要與同事聚餐、下午要先去聿聿人壽完成駐點、然後要回到公司開會、最後完成 merge request 審核、最後晚上要去練跑\n"
            "輸出：\n"
            "1. **09:00 - 10:00** 欣欣銀行開會\n"
            "2. **12:00 - 13:30** 與同事聚餐\n"
            "3. **14:00 - 15:30** 聿聿人壽駐點\n"
            "4. **16:00 - 17:00** 公司開會\n"
            "5. **17:30 - 18:30** Merge Request 審核\n"
            "6. **19:00 - 20:30** 練跑\n\n"
            "請直接輸出行程清單，不要加入任何其他說明文字。"
        )

def get_recent_messages(session_id, limit=3):
    """獲取最近的對話記錄"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT role, content 
        FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (session_id, limit))
    messages = [{"role": role, "content": content} for role, content in c.fetchall()]
    conn.close()
    return list(reversed(messages))  # 反轉列表以保持時間順序

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
            
        system_message = get_system_message(st.session_state.planning_mode)
        
        # 獲取最近的對話記錄
        recent_messages = []
        if st.session_state.planning_mode == "AI 幫你規劃":
            recent_messages = get_recent_messages(st.session_state.current_session_id)
        
        # 構建完整的對話歷史
        messages = [{"role": "system", "content": system_message}]
        if recent_messages:
            messages.extend(recent_messages)
        messages.append({"role": "user", "content": prompt})

        # 使用 SDK 的 chat completion
        response = client.chat.completions.create(
            model=model,
            messages=messages,
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
def send_to_n8n(user_input, schedule, date=None, access_token=None):
    payload = {
        "user_input": user_input,
        "suggested_schedule": schedule,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": date,
        "access_token": access_token
    }
    if date:
        payload["date"] = str(date)
    
    try:
        # 調試信息
        print(f"[DEBUG] n8n payload size: {len(json.dumps(payload, ensure_ascii=False).encode('utf-8'))} bytes")
        
        # 設置請求頭 - 確保只使用 ASCII 字符
        headers = {
            "Content-Type": "application/json",
        }
        
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

# ====== 資料庫設定 ======
DB_PATH = "chat_history.db"

def init_db():
    """初始化資料庫"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_chat_message(session_id, role, content):
    """保存聊天消息到資料庫"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, ?, ?)
    ''', (session_id, role, content))
    c.execute('''
        UPDATE chat_sessions 
        SET last_updated = CURRENT_TIMESTAMP 
        WHERE session_id = ?
    ''', (session_id,))
    conn.commit()
    conn.close()

def load_chat_history(session_id):
    """從資料庫載入聊天歷史"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT role, content 
        FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY timestamp ASC
    ''', (session_id,))
    messages = [{"role": role, "content": content} for role, content in c.fetchall()]
    conn.close()
    return messages

def create_new_session():
    """創建新的聊天會話"""
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO chat_sessions (session_id) VALUES (?)', (session_id,))
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    """獲取所有聊天會話"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT session_id, created_at, last_updated 
        FROM chat_sessions 
        ORDER BY last_updated DESC
    ''')
    sessions = c.fetchall()
    conn.close()
    return sessions

def reset_session_state():
    """重置所有相關的 session state 變數"""
    st.session_state.schedule = None
    st.session_state.editable_schedule = None
    st.session_state.sync_status = None
    st.session_state.chat_history = []

# 初始化資料庫
init_db()

# ====== Streamlit 介面 ======
st.set_page_config(page_title="AI 行程規劃助手", page_icon="📅", layout="wide")

# 添加自定義 CSS
st.markdown("""
<style>
    .mode-selector {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .mode-selector.planning {
        background-color: #f0f7ff;
        border: 1px solid #b3d4ff;
    }
    .mode-selector.ai {
        background-color: #fff0f7;
        border: 1px solid #ffb3d4;
    }
    .mode-button {
        width: 100%;
        padding: 0.5rem;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .mode-button.active {
        background-color: #4CAF50;
        color: white;
    }
    .mode-button.inactive {
        background-color: #f0f0f0;
        color: #666;
    }
    .mode-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# 標題與說明
st.title("📅 AI 行程規劃助手")
st.markdown("""
Smart Plan 是一個 AI 行程規劃助手，可以協助安排單天的日程。用戶只需輸入當天的計劃或想法，系統即會自動生成結構化行程表，並一鍵將所有活動同步到 Google Calendar
此應用程式可以幫助你規劃今日行程，並自動同步到 Google Calendar，並串聯 slack 發送通知。
""")

# 模式選擇器（移到主頁面頂部）
mode_selector_class = "mode-selector planning" if st.session_state.planning_mode == "行程規劃助手" else "mode-selector ai"
st.markdown(f'<div class="{mode_selector_class}">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.button("📝 行程規劃助手", 
                use_container_width=True,
                type="primary" if st.session_state.planning_mode == "行程規劃助手" else "secondary"):
        if st.session_state.planning_mode != "行程規劃助手":
            st.session_state.planning_mode = "行程規劃助手"
            reset_session_state()
            st.experimental_rerun()
with col2:
    if st.button("🤖 AI 幫你規劃", 
                use_container_width=True,
                type="primary" if st.session_state.planning_mode == "AI 幫你規劃" else "secondary"):
        if st.session_state.planning_mode != "AI 幫你規劃":
            st.session_state.planning_mode = "AI 幫你規劃"
            reset_session_state()
            st.experimental_rerun()
st.markdown('</div>', unsafe_allow_html=True)

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
            reset_session_state()
            st.experimental_rerun()
    else:
        get_google_credentials()

    # 在 AI 幫你規劃模式下顯示會話管理
    if st.session_state.planning_mode == "AI 幫你規劃":
        st.markdown("---")
        st.markdown("### 💬 會話管理")
        
        # 初始化當前會話
        if 'current_session_id' not in st.session_state or not st.session_state.current_session_id:
            st.session_state.current_session_id = create_new_session()
            st.session_state.chat_history = []
        
        # 顯示所有會話
        sessions = get_all_sessions()
        if sessions:
            selected_session = st.selectbox(
                "選擇會話",
                options=[s[0] for s in sessions],
                format_func=lambda x: f"會話 {datetime.fromisoformat(next(s[2] for s in sessions if s[0] == x)).strftime('%Y-%m-%d %H:%M')}",
                index=0
            )
            
            if selected_session != st.session_state.current_session_id:
                st.session_state.current_session_id = selected_session
                st.session_state.chat_history = load_chat_history(selected_session)
                st.experimental_rerun()
            
            if st.button("新建會話", use_container_width=True):
                st.session_state.current_session_id = create_new_session()
                reset_session_state()
                st.experimental_rerun()

    st.markdown("---")
    st.markdown("""
    ### ⚙️ 模型設定
    """)
    # Together 模型選擇
    model_options = [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        "meta-llama/Llama-Vision-Free"
    ]
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = model_options[0]
    st.session_state.selected_model = st.selectbox("選擇模型", model_options, index=model_options.index(st.session_state.selected_model))
    
    st.markdown("---")
    st.markdown("### 🔍 系統狀態")

    # 調試區塊移到側邊欄最下方
    with st.expander("系統資訊", expanded=False):
        st.write("API Key 狀態:", "✅ 已設定" if TOGETHER_API_KEY != "your_together_api_key" else "❌ 未設定")
        st.write("Webhook URL 狀態:", "✅ 已設定" if N8N_WEBHOOK_URL != "your_n8n_webhook_url" else "❌ 未設定")
        st.write("Google 認證狀態:", "✅ 已登入" if st.session_state.google_authenticated else "❌ 未登入")
        st.write("所選模型:", st.session_state.selected_model)
        st.write("Python 版本:", sys.version)
        st.write("操作系統:", os.name)

# 主頁日期選擇器（輸入框上方）
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()
st.session_state.selected_date = st.date_input("選擇要安排的日期", value=st.session_state.selected_date)

# 主要介面
if st.session_state.planning_mode == "AI 幫你規劃":
    st.markdown("""
    ### 🤖 AI 幫你規劃
    請告訴我你想要做什麼，我會透過對話來幫你規劃最適合的行程！
    """)
    
    # 顯示聊天歷史
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 聊天輸入框
    if prompt := st.chat_input("請輸入你的想法..."):
        # 添加用戶消息到歷史
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        save_chat_message(st.session_state.current_session_id, "user", prompt)
        
        # 顯示用戶消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成 AI 回應
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = get_schedule_suggestion(prompt, st.session_state.selected_model)
                st.markdown(response)
                # 添加 AI 回應到歷史
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                save_chat_message(st.session_state.current_session_id, "assistant", response)
                
                # 如果回應包含完整的行程安排，更新可編輯的行程
                if "**" in response and "-" in response:
                    st.session_state.schedule = response
                    st.session_state.editable_schedule = response
else:
    st.markdown("""
    ### 📝 行程規劃助手
    請輸入你的行程安排，我會幫你整理成清晰的時間表。
    
    例如：
    > 我今天早上要跟欣欣銀行開會、中午要與同事聚餐、下午要先去聿聿人壽完成駐點、然後要回到公司開會、最後完成 merge request 審核、最後晚上要去練跑
    """)

    user_input = st.text_area("請輸入你的想法和計劃", height=150)

    # 生成行程按鈕
    generate_button = st.button("✨ 生成行程建議")
    if generate_button:
        if not user_input:
            st.error("請先輸入今日計劃")
        else:
            with st.spinner("正在生成建議行程..."):
                try:
                    schedule = get_schedule_suggestion(user_input, st.session_state.selected_model)
                    st.session_state.schedule = schedule
                except Exception as e:
                    st.error(f"生成行程時發生錯誤: {str(e)}")
                    st.session_state.schedule = None

# 顯示生成的行程（兩種模式都適用）
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
                    access_token=access_token
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

