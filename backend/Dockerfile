# =============================================================================
# Maruti Suzuki Knowledge Assistant — Backend Dockerfile
# =============================================================================
FROM python:3.12-slim

WORKDIR /app

# System dependencies for psycopg2 and document parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application code (mounted as volume in dev, copied in prod)
COPY . .

# Create storage directories
RUN mkdir -p /app/storage/documents /app/storage/vectors

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
