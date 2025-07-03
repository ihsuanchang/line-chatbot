import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

# 文件處理相關套件
from docx import Document
import PyPDF2
import pandas as pd

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化 LINE Bot
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 初始化 OpenAI
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 全域變數儲存文件內容和系統提示
docs_content = {}
system_prompt = ""

def load_documents(data_dir="./data"):
    """
    讀取指定資料夾中所有檔案的內容，支援 txt/md、docx、pdf、xlsx 檔案。
    回傳一個字典，key 為檔名，value 為擷取的純文字內容。
    """
    docs = {}
    if not os.path.isdir(data_dir):
        logger.warning(f"資料夾 {data_dir} 不存在，將跳過文件載入。")
        return docs

    for filename in os.listdir(data_dir):
        path = os.path.join(data_dir, filename)
        if not os.path.isfile(path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext in [".txt", ".md"]:
                try:
                    with open(path, mode="r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(path, mode="r", encoding="latin-1") as f:
                        content = f.read()
            elif ext == ".docx":
                doc = Document(path)
                content = "\n".join([p.text for p in doc.paragraphs])
            elif ext == ".pdf":
                reader = PyPDF2.PdfReader(path)
                pages = [page.extract_text() or "" for page in reader.pages]
                content = "\n".join(pages)
            elif ext in [".xlsx", ".xls"]:
                sheets = pd.read_excel(path, sheet_name=None)
                parts = []
                for sheet_name, df in sheets.items():
                    parts.append(f"=== Sheet: {sheet_name} ===")
                    parts.append(df.to_csv(index=False))
                content = "\n".join(parts)
            else:
                continue

            docs[filename] = content
            logger.info(f"成功載入文件: {filename}")
        except Exception as e:
            logger.error(f"處理檔案 {filename} 時發生錯誤：{e}")
    
    return docs

def create_system_prompt(docs: dict) -> str:
    """
    將所有文件內容整合成系統訊息
    """
    if not docs:
        return "你是一個友善的AI助理，請用繁體中文回答使用者的問題。如果使用者詢問關於特定文件或資料的問題，請告訴他們目前沒有載入任何文件資料。"
    
    prompt = "你是一個文件回覆機器人，請根據以下文件內容回答使用者問題：\n\n"
    for name, content in docs.items():
        prompt += f"=== {name} ===\n{content}\n\n"
    prompt += "請根據上述文件回答使用者的提問。如果問題與文件內容無關，請禮貌地說明並提供一般性的協助。請用繁體中文回答。"
    return prompt

def get_openai_response(user_message: str) -> str:
    """
    呼叫 OpenAI API 獲取回應
    """
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # 使用較經濟的模型
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"呼叫 OpenAI API 時發生錯誤: {e}")
        return "抱歉，我現在無法處理您的請求，請稍後再試。"

@app.route("/callback", methods=['POST'])
def callback():
    """LINE webhook端點"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    logger.info("收到 LINE 請求")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理文字訊息"""
    user_message = event.message.text
    logger.info(f"收到訊息: {user_message}")
    
    # 獲取 AI 回應
    ai_response = get_openai_response(user_message)
    
    # 回覆訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ai_response)
    )

@app.route("/health", methods=['GET'])
def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy", 
        "docs_loaded": len(docs_content),
        "documents": list(docs_content.keys()) if docs_content else [],
        "system_prompt_length": len(system_prompt)
    }

@app.route("/", methods=['GET'])
def home():
    """首頁"""
    doc_list = "<br>".join([f"• {doc}" for doc in docs_content.keys()]) if docs_content else "沒有載入文件"
    
    return f"""
    <h1>🤖 LINE 文件聊天機器人</h1>
    <p>✅ <strong>機器人狀態：</strong>運行中</p>
    <p>📚 <strong>已載入文件數量：</strong>{len(docs_content)}</p>
    <p>📋 <strong>載入的文件：</strong></p>
    <div style="margin-left: 20px;">{doc_list}</div>
    <p>💬 <strong>系統提示長度：</strong>{len(system_prompt)} 字元</p>
    <hr>
    <p><small>使用 LINE 掃描 QR code 與機器人對話</small></p>
    """

@app.route("/reload", methods=['POST'])
def reload_documents():
    """重新載入文件（可選功能）"""
    global docs_content, system_prompt
    
    docs_content = load_documents()
    system_prompt = create_system_prompt(docs_content)
    
    return {
        "status": "reloaded",
        "docs_count": len(docs_content),
        "documents": list(docs_content.keys())
    }

# 應用啟動時載入文件
def initialize_app():
    """初始化應用，載入文件"""
    global docs_content, system_prompt
    
    logger.info("正在初始化應用...")
    
    # 載入文件
    docs_content = load_documents()
    system_prompt = create_system_prompt(docs_content)
    
    if docs_content:
        logger.info(f"應用初始化完成，載入了 {len(docs_content)} 個文件：{list(docs_content.keys())}")
    else:
        logger.warning("應用初始化完成，但沒有載入任何文件")

if __name__ == "__main__":
    initialize_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # 在 Render 等平台上，這個也會被執行
    initialize_app()