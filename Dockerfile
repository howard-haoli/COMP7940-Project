# ===== [New File] According to Word Document Section 2.1, Application Container Build =====
# Docker mandatory requirement: Used to containerize application for AWS EC2 deployment

FROM python:3.10-slim

# Set working directory
WORKDIR /chatbot_project_comp7940

# Copy dependency file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code and configuration
COPY *.py ./
COPY .env ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /chatbot_project_comp7940
USER app

# Start command - run main.py as main program
CMD ["python", "main.py"]
