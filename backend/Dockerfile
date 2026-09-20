# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for OpenCV, zbar barcode decoding, and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libzbar0 \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-deva \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . .

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV OCR_ENGINE=paddleocr
ENV ASYNC_OCR_ENABLED=False
ENV PORT=8000

EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
