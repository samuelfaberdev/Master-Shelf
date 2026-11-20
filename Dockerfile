FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Librairies système nécessaires à OpenCV / Ultralytics
RUN apt-get update && apt-get install -y --no-install-recommends \
        libxcb1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyTorch en version CPU : évite ~2 Go de dépendances CUDA inutiles
RUN pip install --upgrade pip \
    && pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY mastershelf ./mastershelf
COPY static ./static

# Les poids YOLO (models/) sont montés en volume par docker-compose.
# Cloud Run fournit $PORT ; en local on retombe sur 8000.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn mastershelf.api.fast:app --host 0.0.0.0 --port ${PORT:-8000}"]
