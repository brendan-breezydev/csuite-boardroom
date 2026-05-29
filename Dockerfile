# ── Stage 1: Python dependencies ──────────────────────────────────────────
FROM python:3.12-slim AS backend-deps
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: React build ───────────────────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 3: Final image ───────────────────────────────────────────────────
FROM python:3.12-slim AS final
WORKDIR /app

# Copy Python packages
COPY --from=backend-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-deps /usr/local/bin /usr/local/bin

# Copy backend source
COPY backend/ ./backend/

# Copy compiled frontend
COPY --from=frontend-build /frontend/dist ./frontend/dist/

EXPOSE 8000

# Railway injects $PORT; fall back to 8000 for local docker run
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
