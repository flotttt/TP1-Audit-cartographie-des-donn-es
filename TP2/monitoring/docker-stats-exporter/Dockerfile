FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY docker_stats_exporter.py .
CMD ["python", "-u", "docker_stats_exporter.py"]
