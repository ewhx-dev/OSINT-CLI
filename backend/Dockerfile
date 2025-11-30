FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY . /app

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8001"]