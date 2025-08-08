# ---------- Builder (deps derlenir) ----------
    FROM python:3.11-slim AS builder
    ENV PIP_NO_CACHE_DIR=1
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc g++ libpq-dev pkg-config \
      && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    COPY requirements.txt .
    # İzole bir venv'e kuruyoruz, sonra sadece bunu kopyalayacağız
    RUN python -m venv /opt/venv \
      && . /opt/venv/bin/activate \
      && pip install --upgrade pip \
      && pip install --no-cache-dir -r requirements.txt
    
    # ---------- Final (hafif runtime) ----------
    FROM python:3.11-slim AS runtime
    ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        VIRTUAL_ENV=/opt/venv \
        PATH="/opt/venv/bin:$PATH"
    
    # İsteğe bağlı: healthcheck için curl istiyorsan ekle.
    # Eğer eklemezsen, healthcheck'i yorum satırı yap.
    RUN apt-get update && apt-get install -y --no-install-recommends curl \
      && rm -rf /var/lib/apt/lists/*
    
    # Non-root user
    RUN groupadd -r appuser && useradd -r -g appuser appuser
    WORKDIR /app
    
    # Sadece gerekli bağımlılıkları kopyala (builder'dan venv)
    COPY --from=builder /opt/venv /opt/venv
    
    # Uygulama kodu
    COPY . .
    
    # Klasör izinleri
    RUN mkdir -p /app/uploads /app/logs && chown -R appuser:appuser /app
    USER appuser
    
    # PaaS PORT’u atar -> ${PORT}; lokalde 8000'e düşer
    EXPOSE 8000
    
    # Healthcheck: /health endpoint'in varsa açık bırak; yoksa yoruma al.
    HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
      CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/health" || exit 1
    
    # Uygulama başlat
    CMD ["bash","-lc","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
    