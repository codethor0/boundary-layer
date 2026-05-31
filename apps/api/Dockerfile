FROM python:3.12-slim

WORKDIR /app

# hadolint ignore=DL3008: curl version pinning is unstable across python:3.12-slim rebuilds.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 boundarylayer \
    && useradd --uid 1000 --gid boundarylayer --create-home boundarylayer

COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api /app/apps/api
COPY labs /app/labs
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations

RUN chown -R boundarylayer:boundarylayer /app

ENV PYTHONPATH=/app

USER boundarylayer

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"]
