# Campus Assistant Telegram Bot - Complete Project

## 📋 Project Overview

Complete project implemented according to the requirements of **Word Document "Campus Assistant Telegram Bot - AWS EC2 Complete Deployment Guide"**.
This project integrates Telegram bot, LLM API, cloud database, Docker containerization, and CI/CD automated deployment.

---

## 🔍 Detailed Modification Comparison Table

### 📂 New Files

| File Path | According to Document Section | Function Description | Status |
|---------|-----------|--------|------|
| `main.py` | Section 1.2.3 | Complete version of bot core logic (new database, multi-commands, interest matching) | ✅ Added |
| `.env` | Section 1.2.2 | Environment variable configuration (for local testing) | ✅ Added |
| `.gitignore` | Section 1.2.4 | Git ignore sensitive files configuration | ✅ Added |
| `Dockerfile` | Section 2.1 | Docker container build file | ✅ Added |
| `docker-compose.yml` | Section 2.2 | Container orchestration configuration (optional optimization) | ✅ Added |
| `.github/workflows/deploy.yml` | Section 7.1 | GitHub Actions CI/CD workflow | ✅ Added |

### 📝 Modified Files

#### 1. **requirements.txt** (Section 1.2.1)
```diff
# ===== [Modified] Added database support dependencies =====
+ mysql-connector-python==8.4.0    # AWS RDS MySQL connection
+ python-dotenv==1.0.1             # Environment variable management
```
**Reason for modification**: Support database log storage and environment variable loading

---

#### 2. **chatbot.py** (Section 1.2.3)
Multiple modifications, mainly including:

**Location 1** - File header import modification:
```python
# ===== [Modified] Add database and environment variable support =====
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime
```

**Location 2** - Main function header new initialization:
```python
# ===== [New] Load environment variable support =====
load_dotenv()

# ===== [New] Database initialization - According to Word Document Section 1.2.3 =====
logging.info('INIT: Initializing database...')
init_db()

# ===== [New] Register command handlers =====
logging.info('INIT: Registering command handlers...')
app.add_handler(CommandHandler("start", handle_start))
app.add_handler(CommandHandler("course", handle_course))
app.add_handler(CommandHandler("interest", handle_interest))
```

**Location 3** - Added database related functions:
```python
# ===== [New] Database connection function =====
def get_db_connection():
    # ...AWS RDS connection configuration

# ===== [New] Initialize database table structure =====
def init_db():
    # ...Create chat_logs and user_interests tables

# ===== [New] Log recording function =====
def log_chat(user_id, username, user_msg, llm_msg):
    # ...Save conversation to database

# ===== [New] Command handler functions =====
async def handle_start(...)          # /start command
async def handle_course(...)         # /course command
async def handle_interest(...)       # /interest command
```

**Location 4** - Modified callback function:
```python
# ===== [Modified] Added database logging =====
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("UPDATE: " + str(update))
    loading_message = await update.message.reply_text('Thinking...')
    response = gpt.submit(update.message.text)
    
    # ===== [New] Store conversation records in database =====
    log_chat(...)
    
    await loading_message.edit_text(response)
```

**Modification Reason**: 
- Support database storage
- Added complete command processing system (/start, /course, /interest)
- Implemented user interest matching functionality
- Meets all document functional requirements

---

#### 3. **ChatGPT_HKBU.py** (Section 1.2.3)
```python
# ===== [Note] According to Word Document Section 1.2.3, this file fully meets LLM API integration requirements =====
# Integrated HKBU LLM API (Azure OpenAI compatible interface)
```
**Note**: This file fully complies with document requirements, no modification needed

---

#### 4. **config.ini** (User Provided)
```ini
# ===== [Note] Original configuration file =====
[TELEGRAM]
ACCESS_TOKEN = 111111
[CHATGPT]
API_KEY = 222222
BASE_URL = https://genai.hkbu.edu.hk/api/v0/rest
MODEL = gpt-5-mini
API_VER = 2024-12-01-preview
```
**Note**: Original configuration fully complies with HKBU LLM API requirements, no modification needed

---

## ✅ Document Requirements Cross-Reference Completion Status

### Mandatory Requirements (Full Coverage)
- ✅ **Telegram Bot** - Implemented with python-telegram-bot library, supports multiple commands
- ✅ **Cloud Database** - AWS RDS MySQL stores logs and user data
- ✅ **AWS Hosting** - Docker container supports EC2 deployment  
- ✅ **LLM API** - HKBU API integration (ChatGPT_HKBU.py)
- ✅ **Git Management** - .gitignore configuration, supports GitHub hosting
- ✅ **Containerization** - Complete Dockerfile and docker-compose.yml
- ✅ **Monitoring & Cost Control** - .github/workflows/deploy.yml supports CloudWatch integration

### Core Features (All Implemented)
- ✅ **/start** - Start command, display function menu
- ✅ **/course** - Course Q&A script
- ✅ **/interest** - User interest tag saving and matching
- ✅ **General Messages** - Direct message processing and LLM conversation
- ✅ **Data Logging** - All conversations automatically saved to AWS RDS
- ✅ **Interest Matching** - Query users with similar interests

### Optional Optimizations (Included)
- ✅ **Docker Compose** - Resource limits and container orchestration
- ✅ **Redis Cache** - Supported in docker-compose.yml
- ✅ **Health Checks** - Container health check configuration
- ⭕ **Container Orchestration** - AWS ECS configuration (can be extended in deploy.yml)
- ⭕ **Application Load Balancing** - ALB configuration (can be extended in deploy.yml)

---

## 🚀 Quick Start

### Local Testing
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment variables
cp .env .env.local  # Edit local database configuration
# If using AWS RDS, configure DB_HOST, DB_PASSWORD, etc. in .env

# 3. Choose running method
# Method A: Original version (simplified)
python chatbot.py

# Method B: Complete version (includes all features)
python main.py
```

### Docker Local Testing
```bash
# Build and run container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

### AWS EC2 Deployment
```bash
# 1. SSH connect to EC2 instance
ssh -i "key-pair.pem" ec2-user@EC2_IP

# 2. Clone project
git clone https://github.com/your-username/campus-assistant-bot.git
cd campus-assistant-bot

# 3. Configure GitHub Secrets (in GitHub repository settings)
# EC2_HOST, EC2_SSH_KEY, TELEGRAM_BOT_TOKEN, LLM_API_KEY, DB_HOST, DB_PASSWORD

# 4. Start container
docker-compose up -d

# 5. Check logs
docker-compose logs -f
```

---

## 📊 Database Table Structure

### chat_logs (Conversation Logs Table)
```sql
CREATE TABLE chat_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,           -- Log ID
    user_id BIGINT,                              -- Telegram User ID
    username VARCHAR(255),                       -- Telegram Username
    user_message TEXT,                           -- User Message
    llm_response TEXT,                           -- LLM Response
    create_time DATETIME                         -- Creation Time
);
```

### user_interests (User Interests Table)
```sql
CREATE TABLE user_interests (
    user_id BIGINT PRIMARY KEY,                  -- Telegram User ID
    interests TEXT,                              -- Interest Tags
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Creation Time
);
```

---

## 📝 Function Command Examples

```
User: /start
Bot: 👋 Campus Assistant Started!
      📚 Main Features:...

User: /course What is tested in data structures
Bot: [Get answer from LLM and store in database]

User: /interest programming fitness
Bot: ✅ Interest tags saved
      👥 Found 5 classmates with similar interests!

User: Hello, I want to learn Python
Bot: [General message processing, LLM response and logging]
```

---

## 🔐 Security Configuration Key Points

1. **Sensitive Information Management**
   - `.env` file is in .gitignore, won't be committed to Git
   - Production environment uses AWS Secrets Manager for key management

2. **Database Security**
   - Use dedicated business account (non-admin) to connect to database
   - AWS RDS security group configuration: Only allow EC2 to access port 3306
   
3. **CI/CD Security**
   - Securely store EC2 keys and API keys through GitHub Secrets
   - deploy.yml uses appleboy/ssh-action for secure deployment

---

## 📖 Document Chapter Correspondence Quick Reference Table

| Function Module | Corresponding Chapter | Main Files |
|---------|---------|--------|
| Project Architecture Design | Chapter 1 | All files |
| Code Development | **Chapter 3** | main.py, chatbot.py, requirements.txt |
| Containerization | **Chapter 4** | Dockerfile, docker-compose.yml |
| Git Management | **Chapter 5** | .gitignore, config.ini |
| AWS Resources | Chapter 6 | (AWS Console Operations) |
| CI/CD Deployment | **Chapter 7** | .github/workflows/deploy.yml |
| Monitoring Cost Control | Chapter 8 | (AWS CloudWatch Configuration) |

---

## ⚠️ Important Notes

1. **Database Connection**
   - Local testing requires MySQL service running
   - AWS deployment needs RDS security group and EC2 security group configuration

2. **Environment Variable Priority**
   - 代码优先读取`.env`文件
   - AWS服务器通过GitHub Secrets注入环境变量
   - 生产环境建议使用AWS Secrets Manager

3. **容器镜像构建**
   - 首次部署会构建Docker镜像（较慢）
   - 后续更新使用`docker-compose up -d --build`重建

---

## 📞 支持与调试

查看容器日志：
```bash
docker-compose logs -f campus-bot
```

检查数据库连接：
```bash
mysql -h <DB_HOST> -u <DB_USER> -p<DB_PASSWORD> campus_bot
SELECT * FROM chat_logs LIMIT 10;
```

查看GitHub Actions部署日志：
```
GitHub仓库 → Actions → 选择最新的Deploy工作流
```

---

**最后更新**: 2026-04-11  
**项目状态**: ✅ 完全符合Word文档所有要求
