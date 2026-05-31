# TLS Runbook

BoundaryLayer uses TLS at two layers in production:

1. **Ingress TLS** — Nginx terminates HTTPS on `127.0.0.1:8443`
2. **Data-plane TLS** — Postgres and Redis require TLS inside the Docker network

## Ingress certificates

### Local / staging (self-signed)

```bash
bash deploy/nginx/generate-certs.sh
```

Generates an ECDSA certificate in `deploy/nginx/certs/`.

### CA-backed production certificates

Install a certificate from your CA (Let's Encrypt, internal PKI, cloud load balancer):

```bash
bash deploy/nginx/install-external-certs.sh /path/to/fullchain.pem /path/to/privkey.pem
```

### Rotation

```bash
# Self-signed rotation
bash deploy/nginx/rotate-certs.sh

# CA-backed rotation
bash deploy/nginx/rotate-certs.sh /path/to/new-fullchain.pem /path/to/new-privkey.pem
```

Previous certificates are archived under `deploy/nginx/certs/archive/`. Production nginx reloads automatically when the stack is running.

### Let's Encrypt (example)

Use certbot on the host or a sidecar, then install the resulting `fullchain.pem` and `privkey.pem` with `install-external-certs.sh`. Schedule renewal with cron or your orchestrator and re-run `rotate-certs.sh` before expiry.

## Internal Postgres / Redis TLS

Generate an internal CA and service certificates:

```bash
bash deploy/tls/generate-internal-ca.sh
```

Material is written to `deploy/tls/internal/` (gitignored). Production compose mounts this directory into Postgres, Redis, and the API container.

Environment variables set automatically in `docker-compose.prod.yml`:

- `POSTGRES_SSLMODE=require`
- `POSTGRES_SSL_ROOT_CERT=/app/tls/ca.crt`
- `REDIS_TLS_ENABLED=true`
- `REDIS_SSL_CA_CERT=/app/tls/ca.crt`

Regenerate internal material before CA expiry (825 days by default) and restart the production stack.

## Verification

```bash
make validate-prod
curl -k https://localhost:8443/health
```

See also [PRODUCTION.md](PRODUCTION.md) and [BACKUP_RESTORE.md](BACKUP_RESTORE.md).
