FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/mock_llm/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/mock_llm /app/apps/mock_llm

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uvicorn", "apps.mock_llm.main:app", "--host", "0.0.0.0", "--port", "8080"]
