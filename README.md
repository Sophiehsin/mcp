# AI 行程規劃助手

一個簡單的 AI 驅動行程規劃應用程式，可以根據用戶輸入生成行程表，並自動同步到 Google Calendar、Notion 和發送通知。

## 功能

- 🤖 使用 GPT 生成行程建議
- 📝 格式化的行程表顯示
- 🔄 整合 Zapier 自動化工作流
- 📅 自動同步到 Google Calendar
- 📊 自動同步到 Notion 資料庫
- 📲 自動發送通知 (Slack/Email/LINE Notify)

## 部署指南

### 1. 設定 OpenRouter API

1. 前往 [OpenRouter](https://openrouter.ai/) 註冊並獲取 API 金鑰
2. 記下你的 API 金鑰，稍後會用到

### 2. 設定 Zapier 整合

#### Zapier Webhook 設定

1. 登入 [Zapier](https://zapier.com/) 或註冊新帳號
2. 點擊 "Create Zap" 按鈕開始建立新的自動化工作流
3. 在觸發器 (Trigger) 部分搜尋並選擇 "Webhooks by Zapier"
4. 選擇 "Catch Hook" 作為觸發器事件
5. 如需要，設定自訂查詢字串參數（可選）
6. 點擊 "Continue"，Zapier 將生成一個唯一的 Webhook URL
7. 複製此 URL，這將作為你的 `ZAPIER_WEBHOOK_URL`
8. 點擊 "Test trigger"，此時可以先不執行實際的測試（稍後我們會從應用程式發送資料）

#### Google Calendar 整合

1. 繼續設定 Zap 的動作 (Action)，點擊 "+" 添加動作
2. 搜尋並選擇 "Google Calendar"
3. 選擇 "Create Detailed Event" 作為動作事件
4. 連接你的 Google Calendar 帳號（如果尚未連接）
5. 設定事件詳情，可以使用來自 Webhook 的資料：

   - **Calendar ID**:

     - 說明：選擇要添加事件的日曆
     - 設定：從下拉選單中選擇你的主要日曆或其他可用的日曆
     - 範例：選擇 "Primary Calendar" 或 "Work Schedule"

   - **Summary (Title)**:

     - 說明：這是 Google Calendar 中事件的標題
     - 設定：點擊欄位右側的 "+" 按鈕，從 Webhook 接收到的資料中選擇
     - 範例設定：`AI 行程規劃: {{1. webhook.user_input|truncate:30}}`
     - 實際呈現：`AI 行程規劃: 明天要準備簡報和開會`

   - **Description**:

     - 說明：事件的詳細描述
     - 設定：選擇完整的行程資訊並加上自訂文字
     - 範例設定：

       ```
       {{2. webhook.suggested_schedule}}

       ---
       此行程由 AI 助手自動生成於 {{3. webhook.timestamp}}
       原始需求: {{1. webhook.user_input}}
       ```

     - 實際呈現：

       ```
       09:00-10:30 準備產品簡報
       11:00-12:00 與行銷團隊開會
       13:30-15:00 與客戶電話會議

       ---
       此行程由 AI 助手自動生成於 2023-05-15 14:30:22
       原始需求: 明天要準備簡報，上午與行銷團隊開會，下午有客戶來電
       ```

   - **Start Date & Time**:

     - 說明：事件的開始時間
     - 設定方法 1 (使用 Formatter 提取):

       1. 新增一個 "Formatter by Zapier" 步驟
       2. Action Type 選擇 "Text"
       3. 轉換選擇 "Extract Pattern"
       4. 輸入值設為 `{{2. webhook.suggested_schedule}}`
       5. Pattern 設為 `(\d{1,2}[:：時]\d{0,2})`
       6. 返回 Calendar 步驟，在開始時間欄位選擇 Formatter 輸出，再設定日期

     - 設定方法 2 (直接設定):
       1. 選擇 "Use a Custom Value (advanced)"
       2. 根據當前日期設定，例如 "Today" 或 "Tomorrow"
       3. 時間部分可設定為固定值，如 "9:00 AM"
     - 範例設定：`Today at {{4. Formatter.outputFirstTime}}`
     - 實際呈現：`Today at 09:00`

   - **End Date & Time**:

     - 說明：事件的結束時間
     - 設定方法 1 (固定持續時間):
       1. 設定與開始時間相同的日期
       2. 時間設為開始時間加上固定小時數
     - 設定方法 2 (使用 Formatter 提取多個時間):
       1. 在 Formatter 步驟中設定提取多個時間
       2. 使用第二個提取的時間作為結束時間
     - 範例設定：`Today at {{4. Formatter.outputFirstTime|add:1 "hours"}}`
     - 實際呈現：`Today at 10:00` (假設開始時間是 09:00)

   - **Location**:

     - 說明：事件的地點
     - 設定：可直接輸入固定地點或從行程中提取
     - 範例設定：`辦公室` 或從行程中提取如 `{{5. Formatter.extractedLocation}}`
     - 實際呈現：`台北市信義區松仁路100號10樓會議室`

   - **Attendees**:

     - 說明：會議參與者
     - 設定：輸入固定的電子郵件清單
     - 範例設定：`team@company.com, boss@company.com`
     - 實際呈現：邀請函會發送給這些電子郵件地址

   - **Reminders**:

     - 說明：設定事件提醒
     - 設定：選擇提醒時間和方式
     - 範例設定 1：`10 minutes, notification`
     - 範例設定 2：`30 minutes, email`
     - 實際呈現：事件前 10 分鐘收到通知提醒，30 分鐘前收到電子郵件提醒

   - **其他選項**:
     - Visibility: 選擇 `default`（使用日曆預設值）
     - Status: 選擇 `confirmed`（已確認的事件）
     - Guest Permissions: 可選擇是否允許賓客修改和邀請其他人

6. 點擊 "Continue" 並測試動作
   - 點擊 "Test & Review" 測試設定
   - 檢查範例資料是否填入各欄位
   - 成功後，點擊 "Publish" 或繼續添加其他動作

#### 使用 Formatter 提取時間的詳細步驟

當 AI 助手生成的行程包含時間資訊時，我們需要提取這些時間來設定 Calendar 事件。以下是詳細步驟：

1. 在 Google Calendar 動作前添加一個新步驟，搜尋並選擇 "Formatter by Zapier"
2. 選擇 "Text" 類型的轉換
3. 轉換方法選擇 "Extract Pattern"
4. 設定如下：
   - 輸入：`{{2. webhook.suggested_schedule}}`
   - Pattern：`(\d{1,2}[:：時]\d{0,2})` (這個正則表達式會提取類似 "9:00", "14:30", "10 時 30" 的時間格式)
   - 選擇 "Return All Matches"
5. 測試並確認正確提取時間
6. 回到 Google Calendar 動作中：
   - Start Date & Time: 使用 `{{4.1. Formatter.firstTimeFound}}` (第一個找到的時間)
   - End Date & Time: 可以使用 `{{4.2. Formatter.secondTimeFound}}` (第二個找到的時間) 或 `{{4.1. Formatter.firstTimeFound|add:1 "hours"}}` (第一個時間加一小時)

### 詳細的 Formatter 和 Start Date & Time 設定圖解

#### 步驟 1: 添加 Formatter 步驟

1. 在設定 Google Calendar 動作前，點擊 "+" 按鈕添加新步驟
2. 搜尋框中輸入 "Formatter"
3. 選擇 "Formatter by Zapier"
4. 這個步驟會出現在你的 Zap 流程中，位於 Webhook 觸發器之後，Google Calendar 動作之前

#### 步驟 2: 設定 Formatter

1. 在 Formatter 配置頁面：

   - "Transform" 下拉選單中選擇 "Text"
   - "Transform With" 下拉選單中選擇 "Extract Pattern"

2. 輸入設定：
   - "Input" 欄位點擊右側的 "+" 按鈕
   - 從下拉選單中找到 Webhook 步驟的輸出
   - 選擇 `suggested_schedule` 欄位 (通常顯示為 `2. Webhook.suggested_schedule`)
3. Pattern 設定：

   - 在 "Pattern" 欄位中輸入 `(\d{1,2}[:：時]\d{0,2})`
   - 這個正則表達式會匹配如 "9:00", "14:30", "10 時 30" 等時間格式
   - 括號 `()` 是必要的，它們標記要提取的內容

4. 輸出選項設定：

   - 勾選 "Return All Matches"，這樣可以提取多個時間點
   - 如果只想提取第一個時間，可以不勾選此選項

5. 測試設定：
   - 點擊 "Test & Continue" 按鈕
   - 檢查測試結果是否成功提取到行程中的時間
   - 例如，如果行程中有 "09:00-10:30 會議"，它應該提取出 "09:00" 和 "10:30"
   - 如果測試失敗，調整正則表達式或檢查輸入資料格式

#### 步驟 3: 在 Google Calendar 中使用提取的時間

1. 繼續設定或返回 Google Calendar 動作
2. 找到 "Start Date & Time" 欄位：

   - 點擊欄位右側的 "+" 按鈕
   - 在下拉選單中找到 Formatter 步驟的輸出
   - 如果返回所有匹配，會有多個選項如 `4.1`、`4.2` 等（代表第一個匹配、第二個匹配）
   - 選擇 `4.1` 作為第一個時間點（開始時間）

3. 日期部分設定：

   - 日期通常需要手動指定或從另一個欄位提取
   - 常見選項包括 "Today"、"Tomorrow" 或特定日期
   - 完整格式可以是 `Today at {{4.1. Formatter.firstTimeFound}}`

4. 最終確認：
   - 完成設定後，測試整個動作
   - 檢查 Google Calendar 預覽中顯示的開始時間是否符合預期
   - 如果時間格式有問題，可能需要使用 Formatter 的其他功能來轉換格式

#### 常見問題與解決方案

1. **時間格式不一致問題**：

   - 如果 AI 生成的時間格式不一致（例如混用 "9:00" 和 "9 時"）
   - 解決方案：使用更複雜的正則表達式，或添加多個 Formatter 步驟處理不同格式

2. **無法提取時間**：

   - 檢查原始文本中的時間格式
   - 測試不同的正則表達式
   - 考慮使用 Zapier 內建的 Date/Time 解析功能

3. **時區問題**：
   - Google Calendar 事件會使用你的日曆默認時區
   - 如需指定不同時區，在時間後添加時區信息，例如 `09:00 GMT+8`

### 實用替代方案：不使用 Formatter 的簡易設定

如果 Formatter 設定太複雜或無法正確提取時間，以下是三種簡單實用的替代方法：

#### 方法一：使用固定時間的單一事件

這個方法最簡單，適合只需要一個提醒事項的場景：

1. 在 Zapier 中直接設定 Google Calendar 動作，跳過 Formatter 步驟
2. **Start Date & Time** 設定：
   - 選擇 "Use a Custom Value (advanced)"
   - 輸入固定時間如 `Today at 9:00 AM` 或 `Tomorrow at 9:00 AM`
3. **End Date & Time** 設定：
   - 同樣選擇 "Use a Custom Value"
   - 設為 `Today at 6:00 PM` 或開始時間後的固定時段
4. **Summary (Title)** 設定：
   - 使用原始需求作為標題：`{{1. webhook.user_input}}`
   - 或加前綴：`AI 行程規劃: {{1. webhook.user_input|truncate:50}}`
5. **Description** 設定：
   - 直接使用完整的 AI 生成行程：`{{2. webhook.suggested_schedule}}`

優點：設定簡單，不需要複雜的正則表達式。
缺點：只能創建單一事件，不會根據 AI 生成的時間自動調整。

#### 方法二：使用全天事件 + 詳細描述

適合需要一整天查看多個任務的情況：

1. 在 Google Calendar 動作中，勾選 "All Day Event"（全天事件）
2. **Start Date** 選擇 `Today` 或 `Tomorrow`
3. **Summary (Title)** 設定：`今日行程規劃`
4. **Description** 欄位放入完整行程：

   ```
   {{2. webhook.suggested_schedule}}

   ---
   由 AI 助手自動生成於 {{3. webhook.timestamp}}
   ```

優點：設定極簡單，適合快速提醒。
缺點：只會在日曆上顯示為全天事件，不會有具體時間區塊。

#### 方法三：手動拆分多個事件 (多個 Zap 動作)

如果你經常有類似的行程模式，可以設定多個 Calendar 動作：

1. 第一個 Google Calendar 動作：

   - **Start Date & Time**: `Today at 9:00 AM`
   - **Summary**: `上午行程: {{1. webhook.user_input|truncate:40}}`
   - **Description**: `{{2. webhook.suggested_schedule}}`

2. 第二個 Google Calendar 動作 (點擊 + 添加):

   - **Start Date & Time**: `Today at 1:00 PM`
   - **Summary**: `下午行程: {{1. webhook.user_input|truncate:40}}`
   - **Description**: `{{2. webhook.suggested_schedule}}`

3. 可選的第三個動作：
   - **Start Date & Time**: `Today at 6:00 PM`
   - **Summary**: `晚間行程: {{1. webhook.user_input|truncate:40}}`
   - **Description**: `{{2. webhook.suggested_schedule}}`

優點：可以在日曆中清楚區分不同時段的行程。
缺點：時間是固定的，不會根據 AI 生成的具體時間調整。

### 其他實用技巧

1. **使用 Zapier 內建的日期選擇器**

   - 在設定時間時，可以使用日期選擇器而非手動輸入
   - 點擊欄位右側的日曆圖示，可選擇日期和時間

2. **使用簡單分類**

   - 可以根據 AI 行程中的關鍵字設定不同類型的事件
   - 例如，檢測是否包含「會議」「約會」等關鍵字，並據此設定不同標題或顏色

3. **設定重複提醒**
   - 對於 Google Calendar 事件，可以設定多個提醒時間
   - 例如：事件前 10 分鐘、30 分鐘和 1 小時各發送一次提醒

#### Notion 資料庫整合

1. 點擊 "+" 添加另一個動作
2. 搜尋並選擇 "Notion"
3. 選擇 "Create Database Item" 作為動作事件
4. 連接你的 Notion 帳號（如果尚未連接）
5. 設定 Notion 資料庫詳情：
   - Database: 選擇你預先在 Notion 中設置好的資料庫
   - 設定相應的欄位映射：
     - 名稱/標題欄位: 可使用行程的標題或摘要
     - 日期欄位: 映射到行程的日期
     - 描述/備註欄位: 可使用完整的 `suggested_schedule`
     - 狀態欄位（如果有）: 可設為 "計畫中"、"待辦" 等
     - 其他自訂欄位: 根據你的資料庫結構設定
6. 點擊 "Continue" 並測試動作

#### 通知整合（以 Slack 為例）

1. 點擊 "+" 添加另一個動作
2. 搜尋並選擇你想使用的通知服務，例如 "Slack"
3. 選擇 "Send Channel Message" 作為動作事件
4. 連接相應的服務帳號
5. 設定通知詳情：
   - 對於 Slack:
     - Channel: 選擇要發送訊息的頻道
     - Message Text: 使用 `suggested_schedule` 或自訂格式
     - Bot Name: 可選（例如 "行程助手"）
     - Bot Icon: 可選（可設定為日曆 emoji）
   - 對於 Email:
     - To: 設定收件人
     - Subject: 例如 "今日行程規劃"
     - Body: 使用 `suggested_schedule`
   - 對於 LINE Notify:
     - Message: 使用 `suggested_schedule`
6. 點擊 "Continue" 並測試動作

#### 完成與啟用

1. 檢查所有步驟是否正確設定
2. 為你的 Zap 命名（例如 "AI 行程助手自動化"）
3. 啟用 Zap（切換開關至 "ON" 狀態）
4. 現在，每當從 Streamlit 應用程式點擊 "同步" 按鈕時，Zapier 就會收到資料並執行所有設定的動作

### 3. 部署 Streamlit 應用程式

#### 本地部署

1. 克隆本儲存庫
2. 安裝依賴項：
   ```
   pip install streamlit requests
   ```
3. 創建 `.streamlit/secrets.toml` 文件並添加你的密鑰：
   ```
   OPENROUTER_API_KEY = "your_openrouter_api_key"
   ZAPIER_WEBHOOK_URL = "your_zapier_webhook_url"
   ```
4. 啟動應用程式：
   ```
   streamlit run streamlit_app.py
   ```

#### 部署到 Streamlit Cloud

1. 在 [Streamlit Cloud](https://streamlit.io/cloud) 註冊並連接你的 GitHub 儲存庫
2. 在設定中，添加相同的密鑰
3. 部署應用程式

## 使用方式

1. 在文本框中輸入你今天的計劃或想法
2. 點擊「生成行程建議」按鈕
3. 查看 AI 生成的行程表
4. 點擊「同步到 Google Calendar、Notion 和發送通知」按鈕將行程同步到所有平台

## 技術架構

```
[Streamlit Web UI]
     |  使用者輸入行程需求
     v
[Python 呼叫 GPT (via OpenRouter)]
     |
     v
[顯示格式化行程建議] → [傳送資料到 Zapier Webhook]
                                        |
                                        v
        [Zapier 處理流程]
           |- 寫入 Google Calendar
           |- 寫入 Notion DB
           |- 發 Slack / Email / LINE Notify
```

### 根據你的實際設定的完整設定範例

根據你提供的配置資訊，這裡是一個完整的設定範例，你可以直接參考填入：

#### Google Calendar 設定具體範例

| 欄位                        | 設定值                                                | 說明                             |
| --------------------------- | ----------------------------------------------------- | -------------------------------- |
| **conferencing**            | no                                                    | 無需設定視訊會議                 |
| **all_day**                 | no                                                    | 非全天事件                       |
| **visibility**              | default                                               | 使用預設可見性                   |
| **reminders\_\_useDefault** | yes                                                   | 使用預設提醒                     |
| **eventType**               | default                                               | 預設事件類型                     |
| **calendarid**              | ce23f1a34a0e...b3d92b@group.calendar.google.com       | 你的日曆 ID                      |
| **Summary**                 | `AI 行程規劃: {{1. webhook.user_input\|truncate:50}}` | 事件標題，使用原始需求並限制長度 |
| **Description**             | `{{2. webhook.suggested_schedule}}`                   | 完整的 AI 生成行程               |
| **start\_\_dateTime**       | `Today at 9:00 AM`                                    | 今天早上 9 點開始                |
| **end\_\_dateTime**         | `Today at 6:00 PM`                                    | 今天下午 6 點結束                |
| **Attendees**               | runrunsophie@gmail.com                                | 參與者郵箱                       |

#### 設定步驟說明

1. **Summary (標題)** 欄位：

   - 保留 `AI 行程規劃: ` 前綴
   - 點擊欄位右側的 "+" 按鈕
   - 選擇 Webhook 輸出中的 `user_input` (通常是 `1. Webhook.user_input`)
   - 添加過濾器 `|truncate:50` 以限制長度

2. **Description (描述)** 欄位：

   - 點擊欄位右側的 "+" 按鈕
   - 選擇 Webhook 輸出中的 `suggested_schedule` (通常是 `2. Webhook.suggested_schedule`)
   - 可選：添加額外信息如 `\n\n---\n生成時間: {{3. webhook.timestamp}}`

3. **start\_\_dateTime (開始時間)** 欄位：

   - 保留 `Today at ` 前綴
   - 添加固定時間 `9:00 AM`
   - 完整設定為: `Today at 9:00 AM`

4. **end\_\_dateTime (結束時間)** 欄位：

   - 保留 `Today at ` 前綴
   - 添加固定時間 `6:00 PM`
   - 完整設定為: `Today at 6:00 PM`

5. **Attendees (參與者)** 欄位：
   - 已填入 `runrunsophie@gmail.com`
   - 可根據需要添加更多郵箱，用逗號分隔

#### 多個事件時間設定選項

如果希望一天內有多個不同時段的事件，可以使用以下時間組合：

1. **上午行程**:

   - start\_\_dateTime: `Today at 9:00 AM`
   - end\_\_dateTime: `Today at 12:00 PM`
   - Summary: `上午行程: {{1. webhook.user_input|truncate:40}}`

2. **下午行程**:

   - start\_\_dateTime: `Today at 1:00 PM`
   - end\_\_dateTime: `Today at 5:00 PM`
   - Summary: `下午行程: {{1. webhook.user_input|truncate:40}}`

3. **晚間行程**:
   - start\_\_dateTime: `Today at 6:00 PM`
   - end\_\_dateTime: `Today at 9:00 PM`
   - Summary: `晚間行程: {{1. webhook.user_input|truncate:40}}`

#### 使用明天的日期

如果需要設定明天的行程，只需將 `Today` 改為 `Tomorrow`:

- start\_\_dateTime: `Tomorrow at 9:00 AM`
- end\_\_dateTime: `Tomorrow at 6:00 PM`

### Formatter 設定的簡化版本

根據你的截圖，我注意到你正在設定 Formatter 的 Pattern 欄位。這裡有幾個簡單可用的正則表達式模式，可以直接複製貼上：

#### 最簡單的時間提取模式

```
(\d{1,2}[:.]\d{2})
```

這個模式會匹配類似 `9:00`、`14:30` 這樣的時間格式。

#### 同時支援中文時間格式

```
(\d{1,2}[:：點時]\d{0,2})
```

這個模式可以匹配 `9:00`、`14:30`、`10時30` 等多種格式。

#### 如何在 Zapier 設定 Formatter

1. 在 **Input** 欄位:

   - 點擊 "+" 按鈕
   - 選擇 `2. Webhook` 下的 `suggested_schedule`

2. 在 **Pattern** 欄位:

   - 貼上上面的正則表達式 (建議使用最簡單版本)
   - 不要更改正則表達式中的任何字符

3. **Match All** 選項:

   - 選擇 "Yes" 可以提取多個時間
   - 選擇 "No" 只提取第一個時間

4. 點擊 "**Continue**" 按鈕完成設定

#### 無法使用 Formatter 的替代方案

如果 Formatter 設定仍有困難，我建議你採用前面提到的「方法二：使用全天事件 + 詳細描述」。這是最簡單的方法：

1. 直接在 Google Calendar 中設定全天事件
2. 把整個 AI 生成的行程放在 Description 欄位中
3. 這樣用戶可以在日曆中一目了然看到所有時間點

或者你也可以選擇「方法一：使用固定時間的單一事件」，如我們先前討論的，設定固定的開始和結束時間。

### 解決 Google Calendar 欄位錯誤問題

如果你遇到 "Required field 'Start Date & Time' is missing" 或 "Required field 'End Date & Time' is missing" 的錯誤，這通常是因為日期時間格式不正確或欄位映射有問題。以下是直接解決方案：

#### 直接使用固定日期時間（最可靠的方法）

1. 打開 Google Calendar 動作設定

2. **Start Date & Time** 欄位:
   - 選擇右側日曆圖示開啟日期選擇器
   - 手動選擇日期和時間（例如：今天 9:00 AM）
   - 不要使用 Formatter 輸出或動態值
   - 確認選擇器顯示完整的日期時間值
3. **End Date & Time** 欄位:
   - 同樣使用日期選擇器
   - 選擇比開始時間晚的時間（例如：今天 5:00 PM）
4. 點擊 "Continue" 並測試

#### 使用 Zapier 的日期轉換功能

如果你想要更靈活的設定，可以嘗試以下方法：

1. 添加一個新的 Formatter 步驟（在 Google Calendar 動作之前）
2. 選擇 "Date/Time" 轉換類型
3. 設定如下:
   - Operation: Format a date
   - Input: 選擇 "Today" 或明確的日期
   - To Format: 選擇 "MM/DD/YYYY hh:mm A" (例如 "05/15/2023 09:00 AM")
4. 在 Google Calendar 動作中:
   - Start Date & Time: 使用此 Formatter 的輸出
   - End Date & Time: 同樣設定另一個 Formatter 或使用固定時間

#### 使用全天事件解決方案

如果上述方法仍然有問題，最簡單的解決方案是使用全天事件：

1. 在 Google Calendar 動作中勾選 "All Day Event"
2. Start Date: 使用日期選擇器選擇今天或明天的日期
3. Description: 放入完整的 AI 生成行程 `{{2. webhook.suggested_schedule}}`

#### 常見錯誤修正

1. **字段名稱不匹配問題**:

   - 確認欄位使用正確的名稱：`start__dateTime` 和 `end__dateTime`（注意是雙下劃線）
   - 某些版本的 Zapier 介面可能顯示為 "Start Date & Time" 但實際欄位名是 `start__dateTime`

2. **時區問題**:

   - Google Calendar 預期接收包含時區的日期時間
   - 使用 Zapier 的日期選擇器會自動包含時區信息

3. **格式問題**:
   - Google Calendar API 需要特定的日期時間格式
   - 最安全的方法是使用 Zapier 內建的日期選擇器或 Date Formatter

### 實際可用的日期時間設定範例

以下是幾個確保可以正常工作的範例：

#### 使用日期選擇器（最推薦）

1. 在日期時間欄位點擊日曆圖示
2. 手動選擇日期並輸入時間
3. 對開始和結束時間都執行相同操作

#### 使用固定文本格式

如果必須手動輸入，使用以下確切格式：

```
05/15/2023 9:00 am
```

或包含時區的格式：

```
05/15/2023 9:00 am GMT+8
```

請注意月份在前，日期在中間，這是美式日期格式。
