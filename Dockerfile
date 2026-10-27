FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 DATABASE_PATH=/data/tickets.db
WORKDIR /app
COPY app.py ./app.py
COPY static ./static
RUN mkdir -p /data && chown -R 10001:10001 /app /data
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["python", "app.py"]
