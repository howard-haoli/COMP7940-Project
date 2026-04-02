FROM python:3.12-slim

WORKDIR /COMP7940-Project
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
CMD ["python", "chatbot.py"]

# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 启动命令
CMD ["python", "main.py"]