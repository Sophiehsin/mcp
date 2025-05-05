# MCP AI 行程規劃助手

MCP AI 行程規劃助手是一個結合 AI 智能與自動化的行程管理平台，專為現代多工生活設計。用戶只需輸入一天的計劃或想法，系統即會自動生成結構化行程表，並一鍵同步到 Google Calendar、Notion、LINE、Slack 等多個平台，實現真正的跨平台行程整合。

---

## 主要功能

- 🤖 **AI 智能行程規劃**  
  只需輸入自然語言描述，AI 會自動解析並生成條列式、標準化的行程表（含明確時間區段）。

- 🔄 **多平台自動同步**  
  行程可自動同步到 Google Calendar、Notion 資料庫，並發送 LINE、Slack、Email 等通知，無需手動重複輸入。

- 📝 **格式化行程輸出**  
  行程表以統一格式輸出，方便後續自動化處理與第三方服務串接。

- ⚡ **一鍵自動化**  
  透過 Zapier Webhook，實現行程自動分拆、時間解析、事件建立等全自動流程。

---

## MCP 專屬獨特性

- **專為多平台協作設計**：MCP 讓你在一個介面上同時管理個人與團隊行程，並自動同步到多個常用工具。
- **AI 輔助標準化**：所有行程皆經 AI 標準化格式處理，確保跨平台資料一致性，減少人工整理負擔。
- **彈性自訂自動化**：可根據個人或團隊需求，透過 Zapier 設定自訂自動化流程（如自動分類、標籤、通知等）。
- **支援多語言與在地化**：行程描述可用中文或英文，AI 會自動辨識並正確解析。

---

## 使用方法

### 1. 本地執行

1. 下載或 clone 此專案
2. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
3. 設定 `.streamlit/secrets.toml`，填入你的 OpenRouter API Key 與 Zapier Webhook URL：
   ```toml
   OPENROUTER_API_KEY = "你的_openrouter_api_key"
   ZAPIER_WEBHOOK_URL = "你的_zapier_webhook_url"
   ```
4. 啟動應用程式：
   ```bash
   streamlit run streamlit_app.py
   ```

### 2. 雲端部署（Streamlit Cloud）

1. 將專案推送到 GitHub
2. 在 [Streamlit Cloud](https://streamlit.io/cloud) 連接你的 repo
3. 在 Secrets 設定中填入 API Key 與 Webhook URL
4. 點擊 Deploy 即可

---

## 如何使用

1. 在主頁輸入你今天的計劃或想法（可用自然語言）
2. 點擊「生成行程建議」
3. 查看 AI 產生的條列式行程表
4. 點擊「同步到 Google Calendar、Notion 和發送通知」即可一鍵同步

---

## 連動功能與自動化流程

- **Google Calendar**：自動建立多個分時段活動，並正確對應開始/結束時間
- **Notion**：自動建立行程資料庫項目，方便後續追蹤與管理
- **LINE/Slack/Email**：自動推播行程摘要或提醒，確保不漏接重要行程
- **Zapier**：負責行程拆解、時間解析、格式轉換等自動化處理

---

## 特色亮點

- **一站式行程管理**：從 AI 生成到多平台同步，全部自動化
- **格式統一，易於擴充**：所有行程皆以標準格式輸出，方便後續串接更多自動化服務
- **彈性自訂**：可根據個人/團隊需求，調整自動化流程與通知方式
- **MCP 專屬優化**：針對 MCP 團隊協作與多平台需求特別優化

---

## 聯絡與貢獻

歡迎 issue、pull request 或聯絡 MCP 團隊共同優化！
