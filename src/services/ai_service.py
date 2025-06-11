from together import Together
from config.settings import TOGETHER_API_KEY

# 初始化 Together client
client = None
if TOGETHER_API_KEY and TOGETHER_API_KEY != "your_together_api_key":
    try:
        client = Together(api_key=TOGETHER_API_KEY)
    except Exception as e:
        print(f"Together client 初始化失敗: {e}")

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

def call_together_api(prompt, model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", mode="行程規劃助手", recent_messages=None):
    """使用 Together AI SDK 生成回應"""
    if not TOGETHER_API_KEY:
        return "API 錯誤: 未設定 API Key"
        
    try:
        if not client:
            return "API 錯誤: Together client 未初始化"
            
        system_message = get_system_message(mode)
        
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
        print(f"[DEBUG] API error details: {str(e)}")
        return error_msg 