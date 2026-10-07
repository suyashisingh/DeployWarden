FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY deploywarden ./deploywarden
RUN pip install --no-cache-dir .

ENV DEPLOYWARDEN_DATA_DIR=/var/lib/deploywarden
RUN useradd --create-home appuser && mkdir -p /var/lib/deploywarden && chown -R appuser:appuser /app /var/lib/deploywarden
USER appuser
VOLUME ["/var/lib/deploywarden"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "deploywarden.api:app", "--host", "0.0.0.0", "--port", "8000"]
