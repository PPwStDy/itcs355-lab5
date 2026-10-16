FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt requirements-cloud.txt requirements-serve.txt ./
RUN pip install -r requirements.txt -r requirements-cloud.txt -r requirements-serve.txt
RUN useradd --create-home --uid 10001 runner && chown runner:runner /app
COPY --chown=runner:runner src/ ./src/
COPY --chown=runner:runner service/ ./service/
COPY --chown=runner:runner monitoring/ ./monitoring/
COPY --chown=runner:runner cloudlayer/ ./cloudlayer/
COPY --chown=runner:runner scripts/ ./scripts/
USER runner
EXPOSE 8080
CMD ["uvicorn","service.app:app","--host","0.0.0.0","--port","8080","--workers","1"]
