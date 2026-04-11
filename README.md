# 校园助手 Telegram Bot - 完整项目

## 📋 项目概述

根据 **Word文档《校园助手 Telegram Bot - AWS EC2 完整部署指南》** 的要求完成的完整项目。
本项目集成了Telegram机器人、LLM API、云数据库、Docker容器化和CI/CD自动部署。

---

## 🔍 修改位置详细对照表

### 📂 新增文件

| 文件路径 | 根据文档章节 | 功能说明 | 状态 |
|---------|-----------|--------|------|
| `main.py` | 第1.2.3节 | 机器人核心逻辑完整版本（新增数据库、多命令、兴趣匹配） | ✅ 新增 |
| `.env` | 第1.2.2节 | 环境变量配置（本地测试用） | ✅ 新增 |
| `.gitignore` | 第1.2.4节 | Git忽略敏感文件配置 | ✅ 新增 |
| `Dockerfile` | 第2.1节 | Docker容器构建文件 | ✅ 新增 |
| `docker-compose.yml` | 第2.2节 | 容器编排配置（可选优化） | ✅ 新增 |
| `.github/workflows/deploy.yml` | 第7.1节 | GitHub Actions CI/CD工作流 | ✅ 新增 |

### 📝 修改的文件

#### 1. **requirements.txt** (第1.2.1节)
```diff
# ===== [修改] 新增数据库支持依赖 =====
+ mysql-connector-python==8.4.0    # AWS RDS MySQL连接
+ python-dotenv==1.0.1             # 环境变量管理
```
**修改原因**: 支持数据库日志存储和环境变量加载

---

#### 2. **chatbot.py** (第1.2.3节)
多处修改，主要包括：

**第1处** - 文件头部导入修改：
```python
# ===== [修改] 添加数据库和环境变量支持 =====
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime
```

**第2处** - 主函数头部新增初始化：
```python
# ===== [新增] 加载环境变量支持 =====
load_dotenv()

# ===== [新增] 数据库初始化 - 根据Word文档第1.2.3节添加 =====
logging.info('INIT: Initializing database...')
init_db()

# ===== [新增] 注册命令处理程序 =====
logging.info('INIT: Registering command handlers...')
app.add_handler(CommandHandler("start", handle_start))
app.add_handler(CommandHandler("course", handle_course))
app.add_handler(CommandHandler("interest", handle_interest))
```

**第3处** - 新增数据库相关函数：
```python
# ===== [新增] 数据库连接函数 =====
def get_db_connection():
    # ...AWS RDS连接配置

# ===== [新增] 初始化数据库表结构 =====
def init_db():
    # ...创建chat_logs和user_interests表

# ===== [新增] 日志记录函数 =====
def log_chat(user_id, username, user_msg, llm_msg):
    # ...保存对话到数据库

# ===== [新增] 命令处理函数 =====
async def handle_start(...)          # /start命令
async def handle_course(...)         # /course命令
async def handle_interest(...)       # /interest命令
```

**第4处** - 修改callback函数：
```python
# ===== [修改] 添加数据库日志记录 =====
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("UPDATE: " + str(update))
    loading_message = await update.message.reply_text('Thinking...')
    response = gpt.submit(update.message.text)
    
    # ===== [新增] 将对话记录存储到数据库 =====
    log_chat(...)
    
    await loading_message.edit_text(response)
```

**修改原因**: 
- 支持数据库存储
- 添加完整的命令处理体系（/start, /course, /interest）
- 实现用户兴趣匹配功能
- 满足文档所有功能需求

---

#### 3. **ChatGPT_HKBU.py** (第1.2.3节)
```python
# ===== [说明] 根据Word文档第1.2.3节，此文件完全满足LLM API集成要求 =====
# 已集成HKBU LLM API (Azure OpenAI兼容接口)
```
**说明**: 此文件已完全符合文档要求，无需修改

---

#### 4. **config.ini** (用户提供)
```ini
# ===== [说明] 原有配置文件 =====
[TELEGRAM]
ACCESS_TOKEN = 111111
[CHATGPT]
API_KEY = 222222
BASE_URL = https://genai.hkbu.edu.hk/api/v0/rest
MODEL = gpt-5-mini
API_VER = 2024-12-01-preview
```
**说明**: 原配置已完全符合HKBU LLM API要求，无需修改

---

## ✅ 文档要求对照完成情况

### 必选要求（全覆盖）
- ✅ **Telegram机器人** - python-telegram-bot库实现，支持多命令
- ✅ **云数据库** - AWS RDS MySQL存储日志和用户数据
- ✅ **AWS托管** - Docker容器支持EC2部署  
- ✅ **LLM API** - HKBU API集成（ChatGPT_HKBU.py）
- ✅ **Git管理** - .gitignore配置，支持GitHub托管
- ✅ **容器化** - Dockerfile和docker-compose.yml完整
- ✅ **监控&成本控制** - .github/workflows/deploy.yml支持CloudWatch集成

### 核心功能（全实现）
- ✅ **/start** - 启动命令，显示功能菜单
- ✅ **/course** - 课程问答脚本
- ✅ **/interest** - 用户兴趣标签保存与匹配
- ✅ **通用消息** - 直接消息处理和LLM对话
- ✅ **数据日志** - 所有对话自动保存到AWS RDS
- ✅ **兴趣匹配** - 查询相似兴趣用户

### 可选优化（已包含）
- ✅ **Docker Compose** - 资源限制和容器编排
- ✅ **Redis缓存** - docker-compose.yml支持
- ✅ **健康检查** - 容器健康检查配置
- ⭕ **容器编排** - AWS ECS配置（可在deploy.yml中扩展）
- ⭕ **应用负载均衡** - ALB配置（可在deploy.yml中扩展）

---

## 🚀 快速开始

### 本地测试
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env .env.local  # 编辑本地数据库配置
# 如果使用AWS RDS，请在.env中配置DB_HOST、DB_PASSWORD等

# 3. 选择运行方式
# 方式A: 原始版本（简化版）
python chatbot.py

# 方式B: 完整版本（包含所有功能）
python main.py
```

### Docker本地测试
```bash
# 构建并运行容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止容器
docker-compose down
```

### AWS EC2部署
```bash
# 1. SSH连接EC2实例
ssh -i "密钥对.pem" ec2-user@EC2_IP

# 2. 克隆项目
git clone https://github.com/你的用户名/campus-assistant-bot.git
cd campus-assistant-bot

# 3. 配置GitHub Secrets（在GitHub仓库设置）
# EC2_HOST, EC2_SSH_KEY, TELEGRAM_BOT_TOKEN, LLM_API_KEY, DB_HOST, DB_PASSWORD

# 4. 启动容器
docker-compose up -d

# 5. 检查日志
docker-compose logs -f
```

---

## 📊 数据库表结构

### chat_logs（对话日志表）
```sql
CREATE TABLE chat_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,           -- 日志ID
    user_id BIGINT,                              -- Telegram用户ID
    username VARCHAR(255),                       -- Telegram用户名
    user_message TEXT,                           -- 用户消息
    llm_response TEXT,                           -- LLM反应
    create_time DATETIME                         -- 创建时间
);
```

### user_interests（用户兴趣表）
```sql
CREATE TABLE user_interests (
    user_id BIGINT PRIMARY KEY,                  -- Telegram用户ID
    interests TEXT,                              -- 兴趣标签
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 创建时间
);
```

---

## 📝 功能命令示例

```
用户: /start
机器人: 👋 校园助手已启动！
      📚 主要功能：...

用户: /course 数据结构考什么
机器人: [从LLM获取答案并存储到数据库]

用户: /interest 编程 健身 
机器人: ✅ 兴趣标签已保存
      👥 找到5位兴趣相似的同学！

用户: 你好，我想学习Python
机器人: [通用消息处理，LLM回复并记录]
```

---

## 🔐 安全配置要点

1. **敏感信息管理**
   - `.env`文件已列入.gitignore，不会提交到Git
   - 生产环境使用AWS Secrets Manager管理密钥
   
2. **数据库安全**
   - 使用专用业务账号（非admin）连接数据库
   - AWS RDS安全组配置：仅允许EC2访问3306端口
   
3. **CI/CD安全**
   - 通过GitHub Secrets安全存储EC2密钥和API密钥
   - deploy.yml中使用了appleboy/ssh-action用于安全部署

---

## 📖 文档对应章节速查表

| 功能模块 | 对应章节 | 主要文件 |
|---------|---------|--------|
| 项目架构设计 | 第一章 | 所有文件 |
| 代码开发 | **第三章** | main.py, chatbot.py, requirements.txt |
| 容器化 | **第四章** | Dockerfile, docker-compose.yml |
| Git管理 | **第五章** | .gitignore, config.ini |
| AWS资源 | 第六章 | (AWS控制台操作) |
| CI/CD部署 | **第七章** | .github/workflows/deploy.yml |
| 监控成本控制 | 第八章 | (AWS CloudWatch配置) |

---

## ⚠️ 注意事项

1. **数据库连接**
   - 本地测试需要MySQL服务运行
   - AWS部署需要配置RDS安全组和EC2安全组

2. **环境变量优先级**
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
