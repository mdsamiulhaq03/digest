FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

FROM builder AS builder-dev
RUN pip install --no-cache-dir --user -r requirements-dev.txt

FROM python:3.12-slim AS base
WORKDIR /app
RUN useradd --create-home --shell /bin/bash appuser
COPY . .
# The uploads volume takes this directory's owner on first mount, so it must
# exist and belong to appuser here, or every upload fails with EACCES.
RUN mkdir -p /data/uploads && chown appuser:appuser /data/uploads
RUN chmod +x entrypoint.sh && chown -R appuser:appuser /app
ENV PATH=/home/appuser/.local/bin:$PATH
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Adds pytest/ruff on top of the runtime deps. Used by Compose for local work.
FROM base AS dev
COPY --from=builder-dev --chown=appuser:appuser /root/.local /home/appuser/.local
USER appuser

# Last stage, so a plain `docker build .` produces the lean production image.
FROM base AS runtime
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
USER appuser
