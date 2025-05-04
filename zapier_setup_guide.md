# Zapier 整合設定指南

## Webhook 設定

1. 登入 [Zapier](https://zapier.com/) 或註冊新帳號
2. 點擊 "Create Zap" 按鈕開始建立新的自動化工作流
3. 在觸發器 (Trigger) 部分搜尋並選擇 "Webhooks by Zapier"
4. 選擇 "Catch Hook" 作為觸發器事件
5. 點擊 "Continue"，Zapier 將生成一個唯一的 Webhook URL
6. 複製此 URL，這將作為你的 `ZAPIER_WEBHOOK_URL`（需要填入 Streamlit 應用程式的 secrets.toml 檔案）

## Google Calendar 成功設定流程

### 方法一：使用日期選擇器（最可靠方法）

1. 在 Zap 中添加 Google Calendar 動作

   - 點擊 "+" 按鈕添加動作
   - 搜尋並選擇 "Google Calendar"
   - 選擇 "Create Detailed Event" 動作

2. 連接你的 Google Calendar 帳號

   - 點擊 "Sign in to Google Calendar"
   - 完成 Google 帳號驗證流程

3. 設定日曆事件關鍵欄位：
   - **Calendar ID**: 從下拉選單選擇你要用的日曆
   - **Summary**: `AI 行程規劃: {{1. webhook.user_input|truncate:50}}`
   - **Description**: `{{2. webhook.suggested_schedule}}`
4. 設定日期時間（關鍵步驟）:
   - **Start Date & Time**: 點擊日曆圖示，手動選擇日期和時間
   - **End Date & Time**: 同樣點擊日曆圖示，選擇晚於開始時間的時間
   - **不要**嘗試在這些欄位使用動態值或公式
5. 其他可選欄位:

   - **Attendees**: 若需要邀請其他人，輸入電子郵件
   - **All Day Event**: 保持不勾選狀態
   - **Location**: 可選填入地點

6. 點擊 "Continue" 並測試

### 方法二：使用全天事件（最簡單方法）

1. 在 Google Calendar 動作設定中:

   - **Calendar ID**: 選擇你的日曆
   - **Summary**: `今日行程規劃: {{1. webhook.user_input|truncate:40}}`
   - **Description**: `{{2. webhook.suggested_schedule}}`
   - **All Day Event**: 勾選此選項
   - **Start Date**: 使用日期選擇器選擇日期（只需選擇日期，不需要時間）

2. 點擊 "Continue" 並測試

## 使用 Formatter 提取時間（進階方法）

如果你希望嘗試從 AI 生成的行程中提取時間：

1. 在 Google Calendar 動作前添加 Formatter 步驟

   - 點擊 "+" 按鈕添加步驟
   - 搜尋選擇 "Formatter by Zapier"

2. 設定 Formatter:

   - **Transform**: 選擇 "Text"
   - **Transform With**: 選擇 "Extract Pattern"
   - **Input**: 選擇 Webhook 中的 `suggested_schedule` 欄位
   - **Pattern**: 輸入 `(\d{1,2}[:.]\d{2})` (提取標準時間如 9:00, 14:30)
   - **Match All**: 選擇 "Yes"

3. 測試 Formatter 是否成功提取時間

4. 在 Formatter 後添加 Date/Time Formatter:

   - 再添加一個 Formatter 步驟
   - **Transform**: 選擇 "Date/Time"
   - **Transform With**: 選擇 "Format a Date"
   - **Input**: 選擇 "Today" 或固定日期
   - **To Format**: 選擇 "MM/DD/YYYY"

5. 在 Google Calendar 動作中正確設定日期時間欄位:

   ### 設定 Start Date & Time（開始時間）

   1. 點擊 **Start Date & Time** 欄位右側的輸入框
   2. 輸入以下格式的文字（組合日期和提取的時間）:
      ```
      05/15/2023 {{3.1. Text.0}}
      ```
      或者使用今天的日期:
      ```
      {{4. Date.formatted_date}} {{3.1. Text.0}}
      ```
   3. 實際設定範例:
      - 如果 Text Formatter 的步驟編號是 3
      - 如果 Date Formatter 的步驟編號是 4
      - 則設定為: `{{4. Date.formatted_date}} {{3.1. Text.0}}`
      - 或設定為今天日期: `05/15/2023 {{3.1. Text.0}}`

   ### 設定 End Date & Time（結束時間）

   1. 點擊 **End Date & Time** 欄位右側的輸入框
   2. 如果提取到了第二個時間，可以使用:
      ```
      {{4. Date.formatted_date}} {{3.2. Text.1}}
      ```
   3. 如果沒有第二個時間或想設定固定持續時間:
      ```
      {{4. Date.formatted_date}} {{3.1. Text.0
      ```
   4. 實際設定範例:
      - 使用第二個提取時間: `05/15/2023 {{3.2. Text.1}}`
      - 或使用第一個時間加 1 小時: `05/15/2023 {{3.1. Text.0 | add: 1 "hours"}}`

   ### 重要說明：

   - 欄位中的數字部分 (`3.1`, `3.2`, `4`) 代表步驟編號，可能需要根據你的實際 Zap 步驟編號調整
   - `Text.0` 表示第一個提取的時間，`Text.1` 表示第二個提取的時間
   - 日期格式必須是美式格式: MM/DD/YYYY
   - 時間格式應該與提取的時間格式匹配
   - 如果遇到錯誤，可能需要調整時間格式或使用前面提到的日期選擇器方法

   ### 實際 Zap 中的參考圖

   當你點擊 Start Date & Time 欄位右側的 "+" 按鈕時，應該會看到類似的選項:

   - Webhook
   - Text Formatter (可能會顯示提取的時間)
   - Date Formatter (可能會顯示格式化的日期)

   選擇適當的組合來構建完整的日期時間值。

## 疑難排解

### 常見錯誤: "Required field Start Date & Time is missing"

出現此錯誤的解決方法:

1. **使用日期選擇器**:
   - 放棄使用動態值，直接使用 Zapier 內建的日期選擇器
   - 手動選擇今天或明天，並輸入具體時間
2. **格式問題**:
   - 若手動輸入，請使用美式日期格式: `MM/DD/YYYY h:mm am`
   - 例如: `05/15/2023 9:00 am`
3. **改用全天事件**:
   - 如果以上方法仍然失敗，勾選 "All Day Event"
   - 只需設定日期，不需設定時間

### 時間格式參考

有效的時間格式範例:

- `05/15/2023 9:00 am`
- `05/15/2023 14:30`
- `05/15/2023 9:00 am GMT+8` (包含時區)

## Notion 與其他整合

設定完 Google Calendar 後，可依相同方式添加其他動作:

1. 點擊 "+" 添加 Notion 或其他服務
2. 完成對應服務的認證
3. 設定相應欄位映射
4. 測試並啟用整個 Zap
