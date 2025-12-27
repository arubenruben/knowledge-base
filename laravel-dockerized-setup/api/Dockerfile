FROM python:3.13-slim

WORKDIR /api

RUN apt-get update && apt-get install -y \
    libmagic-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "fastapi", "run", "/api/main.py", "--host", "0.0.0.0", "--port", "8000", "--workers=4" ]