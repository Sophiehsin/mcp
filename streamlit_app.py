# app.py
import streamlit as st
import requests
import json
import os
from datetime import datetime
import subprocess
import sys

# ====== 設定區 ======
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "your_openrouter_api_key")
ZAPIER_WEBHOOK_URL = st.secrets.get("ZAPIER_WEBHOOK_URL", "your_zapier_webhook_url")

# ====== 標準 API 呼叫 (使用官方格式) ======
def call_openrouter_api(api_key, prompt, model="openai/gpt-3.5-turbo"):
    """使用完全符合 OpenRouter 官方文檔的格式呼叫 API"""
    # 調試信息：輸入提示及其字節長度
    print(f"[DEBUG] Input prompt: {prompt}")
    print(f"[DEBUG] Encoded length: {len(prompt.encode('utf-8'))} bytes")
    
    # 確保所有標頭值僅包含 ASCII 字符
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",  # 移除 charset=utf-8，避免中文字符
        "HTTP-Referer": "https://streamlit.app", 
        "X-Title": "AI Schedule Helper",  # 改為純英文標題
    }
    
    system_message = (
        "你是一個行程規劃助手，請根據輸入幫我用條列式排出今日行程，"
        "每一行請用以下格式：\n"
        "1. **開始時間 - 結束時間** 活動名稱\n"
        "如果沒有明確結束時間，請直接訂出最接近的『開始時間 - 結束時間』，"
        "例如：1. **12:00 - 14:00** 聯絡客戶\n"
        "請只輸出行程條列，不要有多餘的說明文字或結尾語。"
    )
    
    # 構建 JSON 數據
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    st.info("正在使用 requests 標準 API 方法...")
    
    try:
        # 不要使用 data 參數，改用 json 參數讓 requests 自行處理 JSON 序列化
        # 這樣 requests 會自動設置正確的 Content-Type 和編碼
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,  # 使用 json 參數而非自行處理的 data
        )
        
        # 強制設定響應編碼為 UTF-8
        response.encoding = 'utf-8'
        
        # 調試響應狀態碼和頭信息
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response encoding: {response.encoding}")
        
        if response.status_code != 200:
            st.error(f"API 錯誤: {response.status_code}")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    return f"API 錯誤: {error_data.get('error', {}).get('message', '未知錯誤')}"
                return f"API 返回非 200 狀態碼: {response.status_code}, 回應: {response.text[:200]}"
            except:
                return f"API 返回非 200 狀態碼: {response.status_code}, 回應無法解析: {response.text[:200]}"
        
        # 解析回應
        result = response.json()
        
        if 'choices' in result and result['choices'] and 'message' in result['choices'][0]:
            content = result['choices'][0]['message']['content']
            print(f"[DEBUG] Response content (first 50 chars): {content[:50]}...")
            return content
        else:
            st.warning("回應格式不符合預期")
            st.json(result)
            return "API 回應格式不符合預期，請檢查調試信息"
                
    except Exception as e:
        st.error(f"API 呼叫失敗: {e}")
        st.exception(e)  # 顯示完整 traceback
        return f"API 呼叫失敗: {str(e)}"

# ====== GPT 呼叫函式 ======
def get_schedule_suggestion(user_input, model="meta-llama/llama-4-maverick:free"):
    """呼叫 API 生成行程建議"""
    try:
        # 嘗試呼叫 API
        result = call_openrouter_api(OPENROUTER_API_KEY, user_input, model)
        
        # 檢查結果是否包含錯誤信息
        if "API 錯誤" in result or "API 呼叫失敗" in result or "HTTP 錯誤" in result:
            st.error("生成行程失敗")
        
        return result
    except Exception as e:
        error_msg = f"處理請求時發生錯誤: {str(e)}"
        st.error(error_msg)
        return error_msg

# ====== Zapier 整合函式 ======
def send_to_zapier(user_input, schedule):
    # 準備資料
    payload = {
        "user_input": user_input,
        "suggested_schedule": schedule,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # 調試信息
        print(f"[DEBUG] Zapier payload size: {len(json.dumps(payload, ensure_ascii=False).encode('utf-8'))} bytes")
        
        # 設置請求頭 - 確保只使用 ASCII 字符
        headers = {
            "Content-Type": "application/json",
        }
        
        # 發送請求到 Zapier
        response = requests.post(
            ZAPIER_WEBHOOK_URL,
            headers=headers,
            json=payload,  # 使用 json 參數而非 data
        )
        
        # 強制設定響應編碼為 UTF-8
        response.encoding = 'utf-8'
        
        # 檢查回應
        if response.status_code == 200:
            print(f"[DEBUG] Zapier 成功響應: {response.text[:50]}...")
            return True
        else:
            st.error(f"Zapier 回應錯誤: {response.status_code}")
            print(f"[DEBUG] Zapier 錯誤響應: {response.text[:100]}...")
            return False
            
    except Exception as e:
        st.error(f"傳送到 Zapier 時發生錯誤: {e}")
        st.exception(e)  # 顯示完整 traceback
        return False

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
        st.warning("⚠️ 尚未設定 OpenRouter API Key。請在 .streamlit/secrets.toml 文件中設定。")
    
    if ZAPIER_WEBHOOK_URL == "your_zapier_webhook_url":
        st.warning("⚠️ 尚未設定 Zapier Webhook URL。請在 .streamlit/secrets.toml 文件中設定。")
    
    # 添加 API Key 輸入（僅用於臨時測試，不會保存）
    with st.expander("臨時設定 API 金鑰（不會保存）"):
        temp_api_key = st.text_input("OpenRouter API Key", type="password")
        if temp_api_key:
            OPENROUTER_API_KEY = temp_api_key
            st.success("已臨時設定 API Key")
        
        temp_webhook = st.text_input("Zapier Webhook URL", type="password")
        if temp_webhook:
            ZAPIER_WEBHOOK_URL = temp_webhook
            st.success("已臨時設定 Webhook URL")
        
        # 更新模型選擇項，使用更準確的 OpenRouter 模型 ID
        model_options = [
            "meta-llama/llama-4-maverick:free",
            "google/gemini-2.0-flash-exp:free",
            "deepseek/deepseek-chat:free",
            "google/gemma-3-4b-it:free"
        ]
        selected_model = st.selectbox("選擇模型", model_options, index=0)
        
        st.info("推薦使用 openai/gpt-3.5-turbo 獲得最佳兼容性。如果嘗試其他模型出錯，請回到這個選項。")

# 確保選擇的模型可用
if 'selected_model' not in locals():
    selected_model = "openai/gpt-3.5-turbo"

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
                # 使用選擇的模型
                schedule = get_schedule_suggestion(user_input, selected_model)
                st.session_state.schedule = schedule
            except Exception as e:
                st.error(f"生成行程時發生錯誤: {str(e)}")
                st.session_state.schedule = None

# 顯示生成的行程
if st.session_state.schedule and "API 呼叫失敗" not in st.session_state.schedule and "無法" not in st.session_state.schedule and "API 錯誤" not in st.session_state.schedule:
    st.markdown("### 📋 建議行程：")
    st.markdown(st.session_state.schedule)
    
    # 同步到其他平台的按鈕
    sync_button = st.button("🔄 同步到 Google Calendar、Notion 和發送通知")
    if sync_button:
        if OPENROUTER_API_KEY == "your_openrouter_api_key" or ZAPIER_WEBHOOK_URL == "your_zapier_webhook_url":
            st.error("請先在設定中配置 API Key 和 Webhook URL")
        else:
            with st.spinner("正在同步資料..."):
                success = send_to_zapier(user_input, st.session_state.schedule)
                if success:
                    st.session_state.sync_status = "success"
                    st.success("✅ 成功傳送至 Zapier！資料正在自動整合到各平台")
                else:
                    st.session_state.sync_status = "error"
                    st.error("❌ 傳送失敗，請檢查 Zapier Webhook URL 設定")
elif st.session_state.schedule:
    # 顯示錯誤訊息
    st.error("無法生成行程")
    st.markdown(st.session_state.schedule)

# 頁尾
st.markdown("---")
st.markdown("使用 OpenRouter API 和 Zapier 自動化整合")

# 用於調試的可展開區域
with st.expander("調試信息"):
    st.write("API Key 狀態:", "已設定" if OPENROUTER_API_KEY != "your_openrouter_api_key" else "未設定")
    st.write("Webhook URL 狀態:", "已設定" if ZAPIER_WEBHOOK_URL != "your_zapier_webhook_url" else "未設定")
    st.write("所選模型:", selected_model)
    
    # 測試系統環境
    st.write("Python 版本:", sys.version)
    st.write("操作系統:", os.name)
    
    # 添加 API 測試按鈕
    if st.button("測試 API 連接"):
        with st.spinner("測試中..."):
            try:
                test_result = call_openrouter_api(
                    OPENROUTER_API_KEY, 
                    "測試連接，請回覆 'API 運作正常'",
                    "openai/gpt-3.5-turbo"  # 使用最穩定的模型進行測試
                )
                if "API 運作正常" in test_result or "運作正常" in test_result:
                    st.success("✅ API 連接成功！回應: " + test_result)
                else:
                    st.warning("⚠️ API 連接可能有問題，回應: " + test_result)
            except Exception as e:
                st.error(f"API 測試錯誤: {str(e)}")
