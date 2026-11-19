FROM node:22-bookworm-slim AS web-build
WORKDIR /web
ENV NEXT_TELEMETRY_DISABLED=1
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim-bookworm
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libstdc++6 libatomic1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=web-build /usr/local/bin/node /usr/local/bin/node
RUN node --version
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=10000 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /app
COPY requirements.txt requirements.docker.txt ./
RUN python -m pip install --no-cache-dir -r requirements.docker.txt
COPY api.py predict.py preprocessing.py scraper.py train.py ./
COPY data/ ./data/
COPY models/ ./models/
RUN python -c "from predict import load_model; print(load_model().training_report_['selected_model'])"
COPY --from=web-build /web/.next/standalone/ ./frontend/
COPY --from=web-build /web/.next/static/ ./frontend/.next/static/
COPY --from=web-build /web/public/ ./frontend/public/
COPY deploy/start.py ./deploy/start.py
RUN useradd --create-home app && chown -R app:app /app
USER app
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '10000') + '/api/health', timeout=3)"
CMD ["python", "deploy/start.py"]
