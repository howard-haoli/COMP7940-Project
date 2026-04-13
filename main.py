# ===== [新增文件] 根据Word文档第1.2.3节，机器人核心逻辑（完整版本） =====
# 此文件基于chatbot.py和ChatGPT_HKBU.py增强，添加了数据库和完整功能

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from ChatGPT_HKBU import ChatGPT
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters, ConversationHandler
import psycopg2
from psycopg2 import Error

# ===== [修改] 加载环境变量支持 =====
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== 1. 初始化连接 =====================

# ===== [新增] 数据库连接函数 =====
def get_db_connection():
    """获取AWS RDS PostgreSQL数据库连接"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database=os.getenv('DB_NAME', 'campus_bot'),
            port=int(os.getenv('DB_PORT', 5432))
        )
        return conn
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        return None

# 全局LLM客户端
gpt = None

# ===================== 2. 数据库初始化 =====================

# ===== [新增] 初始化数据库表结构 =====
def init_db():
    """首次运行时创建数据库表"""
    conn = get_db_connection()
    if conn is None:
        logger.warning("数据库未连接，跳过表初始化")
        return
    
    try:
        cursor = conn.cursor()
        
        # 请求日志表（必选：数据日志）
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            user_message TEXT,
            llm_response TEXT,
            create_time TIMESTAMP
        )''')
        logger.info("✓ 创建 chat_logs 表成功")
        
        # 用户兴趣表（兴趣匹配）
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_interests (
            user_id BIGINT PRIMARY KEY,
            interests TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        logger.info("✓ 创建 user_interests 表成功")
        
        conn.commit()
        cursor.close()
    except Error as e:
        logger.error(f"创建表失败: {e}")
    finally:
        if conn:
            conn.close()

# ===================== 3. 工具函数 =====================

# ===== [新增] 日志写入云数据库函数 =====
def log_chat(user_id: int, username: str, user_msg: str, llm_msg: str):
    """将对话日志写入AWS RDS MySQL"""
    conn = get_db_connection()
    if conn is None:
        logger.warning("无法记录日志：数据库连接失败")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_logs (user_id, username, user_message, llm_response, create_time) VALUES (%s, %s, %s, %s, %s)",
            (user_id, username, user_msg, llm_msg, datetime.now())
        )
        conn.commit()
        cursor.close()
        logger.info(f"✓ 日志已记录 (用户: {username})")
    except Error as e:
        logger.error(f"日志记录失败: {e}")
    finally:
        if conn:
            conn.close()

# ===================== 4. Telegram 命令处理 =====================

# ===== [新增] /start 启动命令 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动命令处理"""
    welcome_msg = """👋 校园助手已启动！

📚 主要功能：
• /course <问题> - 课程问答
• /interest <标签> - 保存兴趣标签
• 直接发送消息 - 通用问答

例如：
/course 数据结构考什么
/interest 编程 健身
"""
    await update.message.reply_text(welcome_msg)
    logger.info(f"用户 {update.effective_user.username} 启动了机器人")

# ===== [新增] /course 课程问答命令 =====
async def course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """课程问答处理"""
    if not context.args:
        await update.message.reply_text("📚 用法：/course <你的课程问题>\n\n例如：/course 数据结构考什么")
        return
    
    question = " ".join(context.args)
    loading_msg = await update.message.reply_text("🤔 正在查询课程信息...")
    
    try:
        # 调用LLM生成答案
        prompt = f"作为校园助手，回答这个课程问题（简洁专业）：{question}"
        answer = gpt.submit(prompt)
        
        # 记录到数据库
        log_chat(
            update.effective_user.id,
            update.effective_user.username or "anonymous",
            f"/course {question}",
            answer
        )
        
        await loading_msg.edit_text(answer)
    except Exception as e:
        logger.error(f"课程问答失败: {e}")
        await loading_msg.edit_text(f"❌ 课程问答服务异常：{str(e)}")

# ===== [新增] /interest 兴趣匹配命令 =====
async def interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """兴趣匹配处理"""
    if not context.args:
        await update.message.reply_text("🎯 用法：/interest <兴趣标签1> <兴趣标签2> ...\n\n例如：/interest 编程 健身 摄影")
        return
    
    user_id = update.effective_user.id
    tags = " ".join(context.args)
    
    # 即使数据库不可用，也先回复用户
    response = f"✅ 兴趣标签已记录：{tags}"
    
    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # 保存或更新用户兴趣标签（使用PostgreSQL的ON CONFLICT语法）
            cursor.execute(
                "INSERT INTO user_interests (user_id, interests) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET interests = %s",
                (user_id, tags, tags)
            )
            conn.commit()
            
            # 查询相似兴趣的其他用户
            cursor.execute(
                "SELECT user_id FROM user_interests WHERE interests LIKE %s AND user_id != %s LIMIT 5",
                (f"%{context.args[0]}%", user_id)
            )
            matches = cursor.fetchall()
            
            if matches:
                response = f"✅ 兴趣标签已保存：{tags}\n\n👥 找到 {len(matches)} 位兴趣相似的同学！"
            else:
                response = f"✅ 兴趣标签已保存：{tags}\n\n暂时没有找到兴趣相似的同学，继续分享你的兴趣吧！"
            
            logger.info(f"用户 {update.effective_user.username} 更新了兴趣标签: {tags}")
            
        except Error as e:
            logger.error(f"兴趣匹配数据库操作失败: {e}")
            response = f"✅ 兴趣标签已记录：{tags}\n\n（数据库暂时不可用，数据将在恢复后保存）"
        finally:
            cursor.close()
            conn.close()
    else:
        logger.warning(f"兴趣匹配：数据库连接失败，仅在内存中记录")
        response = f"✅ 兴趣标签已记录：{tags}\n\n（数据库连接中断，数据恢复后将保存）"
    
    # 记录到数据库（失败时不中断用户回复）
    log_chat(
        user_id,
        update.effective_user.username or "anonymous",
        f"/interest {tags}",
        response
    )
    
    # 始终回复用户
    await update.message.reply_text(response)

# ===== [新增] 通用消息处理 =====
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通文本消息"""
    user_msg = update.message.text
    loading_msg = await update.message.reply_text("🤖 思考中...")
    
    try:
        # 调用LLM生成回复
        response = gpt.submit(user_msg)
        
        # 记录到数据库
        log_chat(
            update.effective_user.id,
            update.effective_user.username or "anonymous",
            user_msg,
            response
        )
        
        await loading_msg.edit_text(response)
    except Exception as e:
        logger.error(f"消息处理失败: {e}")
        await loading_msg.edit_text(f"❌ 服务异常：{str(e)}")

# ===================== 5. 主程序启动 =====================

def main():
    """主程序入口"""
    global gpt
    
    logger.info("=" * 50)
    logger.info("INIT: 校园助手Telegram机器人启动中...")
    logger.info("=" * 50)
    
    # 加载配置
    logger.info("INIT: 加载配置文件...")
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # ===== [新增] 初始化ChatGPT客户端 =====
        logger.info("INIT: 初始化ChatGPT客户端...")
        gpt = ChatGPT(config)
        logger.info("✓ ChatGPT客户端初始化成功")
    except Exception as e:
        logger.error(f"✗ 配置加载失败: {e}")
        return
    
    # ===== [新增] 初始化数据库 =====
    logger.info("INIT: 初始化数据库...")
    init_db()
    
    # 创建Telegram应用
    logger.info("INIT: 连接Telegram Bot...")
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN') or config['TELEGRAM']['TELEGRAM_BOT_TOKEN']
        app = ApplicationBuilder().token(token).build()
        logger.info("✓ Telegram Bot连接成功")
    except Exception as e:
        logger.error(f"✗ Telegram Bot连接失败: {e}")
        return
    
    # ===== [新增] 注册命令处理程序 =====
    logger.info("INIT: 注册命令处理程序...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("course", course))
    app.add_handler(CommandHandler("interest", interest))
    
    # ===== [修改] 注册消息处理程序 =====
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("✓ 命令处理程序注册成功")
    logger.info("=" * 50)
    logger.info("INIT: 初始化完成！机器人已启动")
    logger.info("=" * 50)
    
    # 启动机器人
    app.run_polling()

if __name__ == '__main__':
    main()
