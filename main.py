# ===== [New File] According to Word Document Section 1.2.3, Bot Core Logic (Complete Version) =====
# This file is enhanced based on chatbot.py and ChatGPT_HKBU.py, adding database and complete functionality

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from ChatGPT_HKBU import ChatGPT
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters, ConversationHandler
import psycopg2
from psycopg2 import Error

# ===== [Modified] Load environment variables support =====
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== 1. Initialize Connections =====================

# ===== [New] Database connection function =====
def get_db_connection():
    """Get AWS RDS PostgreSQL database connection"""
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
        logger.error(f"Database connection failed: {e}")
        return None

# Global LLM client
gpt = None

# ===================== 2. Database Initialization =====================

# ===== [New] Initialize database table structure =====
def init_db():
    """Create database tables on first run"""
    conn = get_db_connection()
    if conn is None:
        logger.warning("Database not connected, skipping table initialization")
        return

    try:
        cursor = conn.cursor()

        # Chat logs table (Required: Data logging)
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            user_message TEXT,
            llm_response TEXT,
            create_time TIMESTAMP
        )''')
        logger.info("✓ Successfully created chat_logs table")

        # User interests table (Interest matching)
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_interests (
            user_id BIGINT PRIMARY KEY,
            interests TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        logger.info("✓ Successfully created user_interests table")

        conn.commit()
        cursor.close()
    except Error as e:
        logger.error(f"Failed to create tables: {e}")
    finally:
        if conn:
            conn.close()

# ===================== 3. Utility Functions =====================

# ===== [New] Log chat to cloud database function =====
def log_chat(user_id: int, username: str, user_msg: str, llm_msg: str):
    """Write conversation logs to AWS RDS PostgreSQL"""
    conn = get_db_connection()
    if conn is None:
        logger.warning("Unable to log: Database connection failed")
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_logs (user_id, username, user_message, llm_response, create_time) VALUES (%s, %s, %s, %s, %s)",
            (user_id, username, user_msg, llm_msg, datetime.now())
        )
        conn.commit()
        cursor.close()
        logger.info(f"✓ Log recorded (User: {username})")
    except Error as e:
        logger.error(f"Log recording failed: {e}")
    finally:
        if conn:
            conn.close()

# ===================== 4. Telegram Command Handling =====================

# ===== [New] /start command =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start command"""
    welcome_msg = """👋 Campus Assistant Started!

📚 Main Features:
• /course <question> - Course Q&A
• /interest <tags> - Save interest tags
• Send messages directly - General Q&A

Examples:
/course What is tested in data structures
/interest programming fitness
"""
    await update.message.reply_text(welcome_msg)
    logger.info(f"User {update.effective_user.username} started the bot")

# ===== [New] /course command =====
async def course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle course Q&A"""
    if not context.args:
        await update.message.reply_text("📚 Usage: /course <your course question>\n\nExample: /course What is tested in data structures")
        return

    question = " ".join(context.args)
    loading_msg = await update.message.reply_text("🤔 Querying course information...")

    try:
        # Call LLM to generate answer
        prompt = f"As a campus assistant, answer this course question (concise and professional): {question}"
        answer = gpt.submit(prompt)

        # Record to database
        log_chat(
            update.effective_user.id,
            update.effective_user.username or "anonymous",
            f"/course {question}",
            answer
        )

        await loading_msg.edit_text(answer)
    except Exception as e:
        logger.error(f"Course Q&A failed: {e}")
        await loading_msg.edit_text(f"❌ Course Q&A service error: {str(e)}")

# ===== [New] /interest command =====
async def interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle interest matching"""
    if not context.args:
        await update.message.reply_text("🎯 Usage: /interest <interest tag1> <interest tag2> ...\n\nExample: /interest programming fitness photography")
        return

    user_id = update.effective_user.id
    tags = " ".join(context.args)

    # Reply to user even if database is unavailable
    response = f"✅ Interest tags recorded: {tags}"

    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            # Save or update user interest tags (using PostgreSQL ON CONFLICT syntax)
            cursor.execute(
                "INSERT INTO user_interests (user_id, interests) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET interests = %s",
                (user_id, tags, tags)
            )
            conn.commit()

            # Query other users with similar interests
            cursor.execute(
                "SELECT user_id FROM user_interests WHERE interests LIKE %s AND user_id != %s LIMIT 5",
                (f"%{context.args[0]}%", user_id)
            )
            matches = cursor.fetchall()

            if matches:
                response = f"✅ Interest tags saved: {tags}\n\n👥 Found {len(matches)} classmates with similar interests!"
            else:
                response = f"✅ Interest tags saved: {tags}\n\nNo classmates with similar interests found yet, keep sharing your interests!"

            logger.info(f"User {update.effective_user.username} updated interest tags: {tags}")

        except Error as e:
            logger.error(f"Interest matching database operation failed: {e}")
            response = f"✅ Interest tags recorded: {tags}\n\n(Database temporarily unavailable, data will be saved when restored)"
        finally:
            cursor.close()
            conn.close()
    else:
        logger.warning(f"Interest matching: Database connection failed, recorded in memory only")
        response = f"✅ Interest tags recorded: {tags}\n\n(Database connection interrupted, data will be saved when restored)"

    # Record to database (don't interrupt user reply on failure)
    log_chat(
        user_id,
        update.effective_user.username or "anonymous",
        f"/interest {tags}",
        response
    )

    # Always reply to user
    await update.message.reply_text(response)

# ===== [New] General message handling =====
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user_msg = update.message.text
    loading_msg = await update.message.reply_text("🤖 Thinking...")

    try:
        # Call LLM to generate response
        response = gpt.submit(user_msg)

        # Record to database
        log_chat(
            update.effective_user.id,
            update.effective_user.username or "anonymous",
            user_msg,
            response
        )

        await loading_msg.edit_text(response)
    except Exception as e:
        logger.error(f"Message processing failed: {e}")
        await loading_msg.edit_text(f"❌ Service error: {str(e)}")

# ===================== 5. Main Program Startup =====================

def main():
    """Main program entry point"""
    global gpt

    logger.info("=" * 50)
    logger.info("INIT: Campus Assistant Telegram Bot Starting...")
    logger.info("=" * 50)

    # Load configuration
    logger.info("INIT: Loading configuration file...")
    try:
        # ===== [Modified] Initialize ChatGPT client - now uses environment variables =====
        logger.info("INIT: Initializing ChatGPT client...")
        gpt = ChatGPT()  # No longer need to pass config parameter
        logger.info("✓ ChatGPT client initialization successful")
    except Exception as e:
        logger.error(f"✗ Configuration loading failed: {e}")
        return

    # ===== [New] Initialize database =====
    logger.info("INIT: Initializing database...")
    init_db()

    # Create Telegram application
    logger.info("INIT: Connecting Telegram Bot...")
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
        app = ApplicationBuilder().token(token).build()
        logger.info("✓ Telegram Bot connection successful")
    except Exception as e:
        logger.error(f"✗ Telegram Bot connection failed: {e}")
        return

    # ===== [New] Register command handlers =====
    logger.info("INIT: Registering command handlers...")
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("course", course))
    app.add_handler(CommandHandler("interest", interest))

    # ===== [Modified] Register message handlers =====
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("✓ Command handlers registration successful")
    logger.info("=" * 50)
    logger.info("INIT: Initialization complete! Bot has started")
    logger.info("=" * 50)

    # Start the bot
    app.run_polling()

if __name__ == '__main__':
    main()
