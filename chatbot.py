'''
This program requires the following modules:
- python-telegram-bot==22.5
- urllib3==2.6.2
# ===== [修改] 根据Word文档要求添加以下依赖 =====
- mysql-connector-python==8.4.0  （数据库支持）
- python-dotenv==1.0.1           （环境变量支持）
'''
from ChatGPT_HKBU import ChatGPT
gpt = None
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
import configparser
import logging
# ===== [新增] 数据库和环境变量支持 =====
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime

def main():

    # Configure logging so you can see initialization and error messages
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    # ===== [新增] 加载环境变量支持 =====
    load_dotenv()
    
    # Load the configuration data from environment variables
    logging.info('INIT: Loading configuration...')
    # No longer need config.ini - using environment variables
    
    global gpt
    gpt = ChatGPT()  # Now uses environment variables
    
    # ===== [新增] 数据库初始化 - 根据Word文档第1.2.3节添加 =====
    logging.info('INIT: Initializing database...')
    init_db()
    
    # Create an Application for your bot
    logging.info('INIT: Connecting the Telegram bot...')
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    app = ApplicationBuilder().token(token).build()

    # ===== [新增] 注册命令处理程序 =====
    logging.info('INIT: Registering command handlers...')
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("course", handle_course))
    app.add_handler(CommandHandler("interest", handle_interest))
    
    # Register a message handler
    logging.info('INIT: Registering the message handler...')
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, callback))

    # Start the bot
    logging.info('INIT: Initialization done!')
    app.run_polling()

# ===== [新增] 数据库连接函数 =====
def get_db_connection():
    """获取数据库连接"""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database=os.getenv('DB_NAME', 'campus_bot'),
            port=int(os.getenv('DB_PORT', 3306))
        )
    except mysql.connector.Error as e:
        logging.error(f"Database connection failed: {e}")
        return None

# ===== [新增] 初始化数据库表结构 =====
def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    if not conn:
        logging.warning("Database not available, skipping table initialization")
        return
    
    try:
        cursor = conn.cursor()
        # 聊天日志表
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            user_message TEXT,
            llm_response TEXT,
            create_time DATETIME
        )''')
        # 用户兴趣表 - 根据Word文档用户兴趣匹配功能
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_interests (
            user_id BIGINT PRIMARY KEY,
            interests TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        logging.info("Database tables initialized successfully")
    except mysql.connector.Error as e:
        logging.error(f"Database initialization failed: {e}")
    finally:
        cursor.close()
        conn.close()

# ===== [新增] 日志记录函数 =====
def log_chat(user_id: int, username: str, user_msg: str, llm_msg: str):
    """将聊天记录存储到AWS RDS数据库 - 根据Word文档必选要求"""
    conn = get_db_connection()
    if not conn:
        logging.warning("Cannot log chat: database not available")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_logs (user_id, username, user_message, llm_response, create_time) VALUES (%s, %s, %s, %s, %s)",
            (user_id, username, user_msg, llm_msg, datetime.now())
        )
        conn.commit()
        logging.info(f"Chat logged for user {username}")
    except mysql.connector.Error as e:
        logging.error(f"Failed to log chat: {e}")
    finally:
        cursor.close()
        conn.close()

# ===== [新增] /start 命令处理 =====
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/start命令"""
    welcome_msg = """👋 校园助手已启动！

📚 主要功能：
• /course <问题> - 课程问答
• /interest <标签> - 保存兴趣标签
• 直接发送消息 - 通用问答
"""
    await update.message.reply_text(welcome_msg)

# ===== [新增] /course 课程问答命令 - 根据Word文档功能需求 =====
async def handle_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/course课程问答命令"""
    if not context.args:
        await update.message.reply_text("用法：/course <你的课程问题>")
        return
    
    question = " ".join(context.args)
    loading_msg = await update.message.reply_text("思考中...")
    
    try:
        prompt = f"作为校园助手，回答这个课程问题：{question}"
        answer = gpt.submit(prompt)
        
        # ===== [修改] 记录到数据库 =====
        log_chat(update.effective_user.id, update.effective_user.username or "anonymous", f"/course {question}", answer)
        
        await loading_msg.edit_text(answer)
    except Exception as e:
        await loading_msg.edit_text(f"错误：{str(e)}")

# ===== [新增] /interest 兴趣匹配命令 - 根据Word文档功能需求 =====
async def handle_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/interest兴趣标签命令"""
    if not context.args:
        await update.message.reply_text("用法：/interest <兴趣标签1> <兴趣标签2> ...")
        return
    
    user_id = update.effective_user.id
    tags = " ".join(context.args)
    
    conn = get_db_connection()
    if not conn:
        await update.message.reply_text("数据库连接失败")
        return
    
    try:
        cursor = conn.cursor()
        # 保存用户兴趣
        cursor.execute(
            "REPLACE INTO user_interests (user_id, interests) VALUES (%s, %s)",
            (user_id, tags)
        )
        conn.commit()
        
        # 查询兴趣相似的用户 - 根据Word文档兴趣匹配功能
        cursor.execute(
            "SELECT user_id FROM user_interests WHERE interests LIKE %s AND user_id != %s LIMIT 5",
            (f"%{context.args[0]}%", user_id)
        )
        matches = cursor.fetchall()
        
        response = f"✅ 兴趣标签已保存：{tags}\n找到 {len(matches)} 位相似用户" if matches else f"✅ 兴趣标签已保存：{tags}\n暂无相似用户"
        
        # ===== [修改] 记录到数据库 =====
        log_chat(user_id, update.effective_user.username or "anonymous", f"/interest {tags}", response)
        
        await update.message.reply_text(response)
    except mysql.connector.Error as e:
        await update.message.reply_text(f"数据库错误：{str(e)}")
    finally:
        cursor.close()
        conn.close()

# ===== [修改] 消息回调处理函数 - 添加数据库日志记录 =====
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ===== [修改] 显示具体处理中提示 =====
    logging.info("UPDATE: " + str(update))
    loading_message = await update.message.reply_text('Thinking...')

    # send the user message to the ChatGPT client
    response = gpt.submit(update.message.text)
    
    # ===== [新增] 将对话记录存储到数据库 - 根据Word文档数据日志必选要求 =====
    log_chat(
        update.effective_user.id,
        update.effective_user.username or "anonymous",
        update.message.text,
        response
    )

    # send the response to the Telegram box client
    await loading_message.edit_text(response)

if __name__ == '__main__':
    main()
