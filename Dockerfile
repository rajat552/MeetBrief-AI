# ------------------------------------------------------------------------------
# Stage 1: Build React 18 UI
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /build

COPY ui/package*.json ./
RUN npm install

COPY ui/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Python FastAPI Backend & Unified Server
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    ENVIRONMENT=production

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY app.py ./

# Copy compiled frontend from Stage 1 into ui/dist
COPY --from=frontend-builder /build/dist ./ui/dist/

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

EXPOSE 5000

# Run FastAPI app
CMD ["python", "app.py"]
