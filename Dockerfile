# Base Image compatible with Tesseract and Ghostscript
FROM python:3.11-slim

# Install system dependencies
# tesseract-ocr: for OCR
# tesseract-ocr-por: Portuguese language pack for OCR
# ghostscript: required by ocrmypdf
# gcc: sometimes needed for python libs compilation
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

# Copy application code
COPY . .

# Mark startup script executable
RUN chmod +x _start.sh

# Skip venv inside container
ENV CONTAINER=1

# Expose Streamlit port
EXPOSE 8501

# Command to run the application
CMD ["bash", "_start.sh"]
