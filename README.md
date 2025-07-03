# LINE 文件聊天機器人 - Render 部署指南

這個專案將你的文件聊天機器人部署到 Render 平台，並整合 LINE Messaging API。

## 前置準備

### 1. LINE Developers 設定

1. 前往 [LINE Developers](https://developers.line.biz/)
2. 登入並創建新的 Provider 或使用現有的
3. 創建新的 Messaging API Channel
4. 在 Channel 設定中記下以下資訊：
   - **Channel Access Token** (Long-lived)
   - **Channel Secret**

### 2. OpenAI API 設定

1. 前往 [OpenAI Platform](https://platform.openai.com/)
2. 創建 API Key
3. 記下你的 **OpenAI API Key**

## 部署到 Render

### 步驟 1: 準備檔案結構

確保你的專案有以下檔案：
```
your-project/
├── app.py
├── requirements.txt
├── render.yaml
├── data/
│   ├── your-document1.txt
│   ├── your-document2.pdf
│   └── your-document3.docx
└── README.md
```

### 步驟 2: 上傳到 GitHub

1. 創建新的 GitHub repository
2. 將所有檔案推送到 repository
3. 確保 `data/` 資料夾包含你想要機器人學習的文件

### 步驟 3: 在 Render 創建服務

1. 前往 [Render](https://render.com/)
2. 註冊/登入帳號
3. 點擊 "New +" → "Web Service"
4. 連接你的 GitHub repository
5. 選擇包含機器人程式碼的 repository

### 步驟 4: 配置環境變數

在 Render 的 Environment 設定中添加以下環境變數：

| 變數名稱 | 值 |
|---------|---|
| `OPENAI_API_KEY` | 你的 OpenAI API Key |
| `LINE_CHANNEL_ACCESS_TOKEN` | 你的 LINE Channel Access Token |
| `LINE_CHANNEL_SECRET` | 你的 LINE Channel Secret |

### 步驟 5: 部署

1. 確認所有設定正確
2. 點擊 "Create Web Service"
3. 等待部署完成（通常需要 5-10 分鐘）
4. 記下你的 Render 應用 URL（例如：`https://your-app-name.onrender.com`）

## 設定 LINE Webhook

### 步驟 1: 設定 Webhook URL

1. 回到 LINE Developers Console
2. 選擇你的 Messaging API Channel
3. 在 "Messaging API" 頁籤中：
   - 找到 "Webhook settings"
   - 將 Webhook URL 設定為：`https://your-app-name.onrender.com/callback`
   - 啟用 "Use webhook"

### 步驟 2: 設定回覆模式

在 LINE Developers Console 中：
1. 關閉 "Auto-reply messages"
2. 關閉 "Greeting messages"（可選）
3. 確保 "Webhooks" 已啟用

### 步驟 3: 測試機器人

1. 使用 LINE app 掃描你的 QR code 或搜尋 Bot ID
2. 加入機器人為好友
3. 發送訊息測試功能

## 文件管理

### 支援的檔案格式

- `.txt` - 純文字檔案
- `.md` - Markdown 檔案
- `.docx` - Word 文件
- `.pdf` - PDF 檔案
- `.xlsx`, `.xls` - Excel 檔案

### 更新文件內容

1. 在 GitHub repository 的 `data/` 資料夾中更新檔案
2. 推送變更到 GitHub
3. Render 會自動重新部署

## 監控和除錯

### 查看日誌

1. 在 Render Dashboard 中選擇你的服務
2. 點擊 "Logs" 查看運行日誌
3. 檢查錯誤訊息和除錯資訊

### 健康檢查

訪問 `https://your-app-name.onrender.com/health` 查看服務狀態

### 常見問題

**Q: 機器人沒有回應**
- 檢查 Webhook URL 是否正確設定
- 確認環境變數是否正確配置
- 查看 Render 日誌是否有錯誤

**Q: OpenAI API 錯誤**
- 確認 API Key 是否有效
- 檢查 OpenAI 帳戶餘額
- 確認 API 使用限制

**Q: 文件沒有載入**
- 確認 `data/` 資料夾存在且包含檔案
- 檢查檔案格式是否支援
- 查看日誌中的文件載入訊息

## 成本考量

- **Render**: 免費方案有限制，付費方案從 $7/月開始
- **OpenAI API**: 按使用量計費
- **LINE Messaging API**: 免費（有訊息數量限制）

## 安全注意事項

1. 不要在程式碼中寫入 API Keys
2. 使用環境變數管理敏感資訊
3. 定期檢查 API 使用量
4. 考慮設定 OpenAI API 使用限制

## 進階功能

### 添加更多功能

你可以在 `app.py` 中添加：
- 圖片訊息處理
- 檔案上傳功能
- 多使用者對話管理
- 資料庫整合

### 擴展部署

考慮升級到付費方案以獲得：
- 更好的效能
- 自訂網域
- 更多運算資源