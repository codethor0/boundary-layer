FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 boundarylayer \
    && useradd --uid 1000 --gid boundarylayer --create-home boundarylayer

COPY apps/alert_webhook/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/alert_webhook /app/apps/alert_webhook

RUN chown -R boundarylayer:boundarylayer /app

ENV PYTHONPATH=/app

USER boundarylayer

EXPOSE 8080

CMD ["uvicorn", "apps.alert_webhook.main:app", "--host", "0.0.0.0", "--port", "8080"]
