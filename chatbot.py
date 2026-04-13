'''
This program requires the following modules:
- python-telegram-bot==22.5
- urllib3==2.6.2
# ===== [Modified] Added the following dependencies according to Word document requirements =====
- mysql-connector-python==8.4.0  (Database support)
- python-dotenv==1.0.1           (Environment variable support)
'''
from ChatGPT_HKBU import ChatGPT
gpt = None
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
import configparser
import logging
# ===== [New] Database and environment variable support =====
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime

def main():

    # Configure logging so you can see initialization and error messages
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    # ===== [New] Load environment variable support =====
    load_dotenv()
    
    # Load the configuration data from environment variables
    logging.info('INIT: Loading configuration...')
    # No longer need config.ini - using environment variables
    
    global gpt
    gpt = ChatGPT()  # Now uses environment variables
    
    # ===== [New] Database initialization - Added according to Word Document Section 1.2.3 =====
    logging.info('INIT: Initializing database...')
    init_db()
    
    # Create an Application for your bot
    logging.info('INIT: Connecting the Telegram bot...')
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    app = ApplicationBuilder().token(token).build()

    # ===== [New] Register command handlers =====
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

# ===== [New] Database connection function =====
def get_db_connection():
    """Get database connection"""
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

# ===== [New] Initialize database table structure =====
def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        logging.warning("Database not available, skipping table initialization")
        return
    
    try:
        cursor = conn.cursor()
        # Chat logs table
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            username VARCHAR(255),
            user_message TEXT,
            llm_response TEXT,
            create_time DATETIME
        )''')
        # User interests table - According to Word document user interest matching function
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

# ===== [New] Log recording function =====
def log_chat(user_id: int, username: str, user_msg: str, llm_msg: str):
    """Store chat records in AWS RDS database - According to Word document mandatory requirements"""
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

# ===== [New] /start command handling =====
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_msg = """👋 Campus Assistant Started!

📚 Main Features:
• /course <question> - Course Q&A
• /interest <tag> - Save interest tags
• Send message directly - General Q&A
"""
    await update.message.reply_text(welcome_msg)

# ===== [New] /course course Q&A command - According to Word document functional requirements =====
async def handle_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /course course Q&A command"""
    if not context.args:
        await update.message.reply_text("Usage: /course <your course question>")
        return
    
    question = " ".join(context.args)
    loading_msg = await update.message.reply_text("Thinking...")
    
    try:
        prompt = f"As a campus assistant, answer this course question: {question}"
        answer = gpt.submit(prompt)
        
        # ===== [Modified] Record to database =====
        log_chat(update.effective_user.id, update.effective_user.username or "anonymous", f"/course {question}", answer)
        
        await loading_msg.edit_text(answer)
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)}")

# ===== [New] /interest interest matching command - According to Word document functional requirements =====
async def handle_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /interest interest tag command"""
    if not context.args:
        await update.message.reply_text("Usage: /interest <interest tag1> <interest tag2> ...")
        return
    
    user_id = update.effective_user.id
    tags = " ".join(context.args)
    
    conn = get_db_connection()
    if not conn:
        await update.message.reply_text("Database connection failed")
        return
    
    try:
        cursor = conn.cursor()
        # Save user interests
        cursor.execute(
            "REPLACE INTO user_interests (user_id, interests) VALUES (%s, %s)",
            (user_id, tags)
        )
        conn.commit()
        
        # Query users with similar interests - According to Word document interest matching function
        cursor.execute(
            "SELECT user_id FROM user_interests WHERE interests LIKE %s AND user_id != %s LIMIT 5",
            (f"%{context.args[0]}%", user_id)
        )
        matches = cursor.fetchall()
        
        response = f"✅ Interest tags saved: {tags}\nFound {len(matches)} similar users" if matches else f"✅ Interest tags saved: {tags}\nNo similar users found yet"
        
        # ===== [Modified] Record to database =====
        log_chat(user_id, update.effective_user.username or "anonymous", f"/interest {tags}", response)
        
        await update.message.reply_text(response)
    except mysql.connector.Error as e:
        await update.message.reply_text(f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# ===== [Modified] Message callback handler function - Added database logging =====
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ===== [Modified] Show specific processing prompt =====
    logging.info("UPDATE: " + str(update))
    loading_message = await update.message.reply_text('Thinking...')

    # send the user message to the ChatGPT client
    response = gpt.submit(update.message.text)
    
    # ===== [New] Store conversation records in database - According to Word document data logging mandatory requirements =====
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
