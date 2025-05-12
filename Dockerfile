FROM python:3.10-slim

# 安裝必要套件與 Chrome + ChromeDriver
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg2 fonts-liberation libnss3 libxss1 libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 xdg-utils libgbm1 chromium chromium-driver \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Flask 自動 reload 預防
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip && pip install -r requirements.txt

# Render 預設會傳入 PORT 環境變數，這樣可配合 Flask 運行
EXPOSE 10000

CMD ["python", "app.py"]

