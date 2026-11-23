# ---- Stage 1: install dependencies ----
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: minimal runtime image ----
# One Dockerfile builds every release; pick the release file with APP_FILE:
#   docker build --build-arg APP_FILE=versions/ACEest_Fitness_v1.py \
#                --build-arg APP_VERSION=1.0.0 -t <user>/aceest-fitness:1.0.0 .
FROM python:3.12-slim
ARG APP_FILE=ACEest_Fitness.py
ARG APP_VERSION=3.0.0
LABEL org.opencontainers.image.title="aceest-fitness" \
      org.opencontainers.image.version="${APP_VERSION}"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/data/aceest_fitness.db
WORKDIR /app

COPY --from=builder /install /usr/local
COPY ${APP_FILE} ./ACEest_Fitness.py

# Run as a non-root user
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "ACEest_Fitness:app"]
