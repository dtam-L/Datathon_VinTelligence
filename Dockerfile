
FROM python:3.11-slim

# Metadata
LABEL maintainer="VinTelligence Team"
LABEL description="Revenue & COGS Forecasting API powered by XGBoost"

# Không tạo .pyc, không buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# --- Cài dependencies hệ thống nhỏ gọn ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# --- Cài Python packages ---
COPY main/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy source code ---
COPY main/       /app/main/
COPY webapp/     /app/webapp/
COPY models/     /app/models/

# --- Port ---
EXPOSE 5000

# --- Chạy từ thư mục main/ ---
WORKDIR /app/main
CMD ["python", "app.py"]
