# main chatbot module that interacts with the ChatGPT REST API
import requests
import configparser

# A simple client for the ChatGPT REST API
class ChatGPT:
    def __init__(self, config):
        # Read API configuration values from the ini file
        api_key = config['CHATGPT']['API_KEY']
        base_url = config['CHATGPT']['BASE_URL']
        model = config['CHATGPT']['MODEL']
        api_ver = config['CHATGPT']['API_VER']

        # Construct the full REST endpoint URL for chat completions
        self.url = f'{base_url}/deployments/{model}/chat/completions?api-version={api_ver}'

        # Set HTTP headers required for authentication and JSON payload
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "api-key": api_key,
        }

        # Define the system prompt to guide the assistant’s behavior
        self.system_message = (
            'You are a helper! Your users are university students. '
            'Your replies should be conversational, informative, use simple words, and be straightforward.'
        )

    def submit(self, user_message: str):
        
        # Build the conversation history: system + user message
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_message},
        ]

        # Prepare the request payload with generation parameters
        payload = {
            "messages": messages,
            "temperature": 1,     # randomness of output (higher = more creative)
            "max_tokens": 150,    # maximum length of the reply
            "top_p": 1,           # nucleus sampling parameter
            "stream": False       # disable streaming, wait for full reply
        }    

        # Send the request to the ChatGPT REST API
        response = requests.post(self.url, json=payload, headers=self.headers)

        # If successful, return the assistant’s reply text
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            # Otherwise return error details
            return "Error: " + response.text
    

if __name__ == '__main__':
    # Load configuration from ini file
    config = configparser.ConfigParser()
    config.read('config.ini')    

    # Initialize ChatGPT client
    chatGPT = ChatGPT(config)

    # Simple REPL loop: read user input, send to ChatGPT, print reply
    while True:
        print('Input your query: ', end='')
        response = chatGPT.submit(input())

        print(response)





import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import mysql.connector
from openai import OpenAI

# 加载环境变量
load_dotenv()
logging.basicConfig(level=logging.INFO)

# ===================== 1. 初始化连接 =====================
# Telegram Bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
updater = Updater(TELEGRAM_TOKEN)

# LLM 客户端
llm_client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# AWS RDS 云数据库连接（日志+用户数据存储）
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )

# 初始化数据库表（首次运行创建）
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 请求日志表（必选：数据日志）
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT,
        username VARCHAR(255),
        user_message TEXT,
        llm_response TEXT,
        create_time DATETIME
    )''')
    # 用户兴趣表（兴趣匹配）
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_interests (
        user_id BIGINT PRIMARY KEY,
        interests TEXT,
        schedule TEXT
    )''')
    conn.commit()
    cursor.close()
    conn.close()

# ===================== 2. 工具函数 =====================
# 日志写入云数据库
def log_chat(user_id: int, username: str, user_msg: str, llm_msg: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (user_id, username, user_message, llm_response, create_time) VALUES (%s, %s, %s, %s, %s)",
        (user_id, username, user_msg, llm_msg, datetime.now())
    )
    conn.commit()
    cursor.close()
    conn.close()

# LLM 对话生成（课程问答+日程助手）
def llm_chat(prompt: str) -> str:
    try:
        # 提示词模板（最佳实践）
        system_prompt = """你是校园助手机器人，负责解答课程问题、管理日程、匹配兴趣相似的同学。
        规则：1. 回答简洁专业；2. 课程问题优先回答校园相关；3. 日程管理支持增删查；4. 兴趣匹配基于标签。"""
        response = llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM服务异常：{str(e)}"

# ===================== 3. Telegram 命令处理 =====================
# 启动命令
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 校园助手已启动！\n功能：/course 课程问答 /schedule 日程管理 /interest 兴趣匹配")

# 课程问答
def course(update: Update, context: CallbackContext):
    question = " ".join(context.args)
    if not question:
        update.message.reply_text("用法：/course 你的课程问题")
        return
    answer = llm_chat(f"课程问题：{question}")
    # 日志写入云数据库
    log_chat(update.effective_user.id, update.effective_user.username, question, answer)
    update.message.reply_text(answer)

# 兴趣匹配
def interest(update: Update, context: CallbackContext):
    tags = " ".join(context.args)
    user_id = update.effective_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO user_interests (user_id, interests) VALUES (%s, %s)", (user_id, tags))
    conn.commit()
    # 匹配相似兴趣用户
    cursor.execute("SELECT user_id FROM user_interests WHERE interests LIKE %s AND user_id != %s", (f"%{tags}%", user_id))
    matches = cursor.fetchall()
    res = f"✅ 兴趣标签保存成功！\n相似用户：{len(matches)}人" if matches else "✅ 兴趣标签保存成功！暂无相似用户"
    update.message.reply_text(res)
    cursor.close()
    conn.close()

# 消息处理（通用对话）
def echo(update: Update, context: CallbackContext):
    user_msg = update.message.text
    llm_res = llm_chat(user_msg)
    log_chat(update.effective_user.id, update.effective_user.username, user_msg, llm_res)
    update.message.reply_text(llm_res)

# ===================== 4. 启动机器人 =====================
if __name__ == "__main__":
    init_db()
    dp = updater.dispatcher
    # 注册命令
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("course", course))
    dp.add_handler(CommandHandler("interest", interest))
    # 注册消息
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    # 启动机器人
    updater.start_polling()
    updater.idle()