# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    ghostscript \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código base
COPY . .

# Copia os assets do frontend buildados no Stage 1 (a mágica acontece aqui)
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Mark startup script executable
RUN chmod +x _start.sh

# Skip venv inside container
ENV CONTAINER=1

# Expose backend port
EXPOSE 8000

# Command to run the application
CMD ["bash", "_start.sh"]
