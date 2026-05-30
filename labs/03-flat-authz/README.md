# Flat AuthN/AuthZ Lab

Demonstrates how a broadly authenticated token can access restricted tools.

## Modes

- **vulnerable**: Any authenticated token can invoke restricted tools.
- **hardened**: Requires explicit scope and tenant match.

## Validation

```bash
curl -X POST http://localhost:8000/labs/authz/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/authz/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

## Risk

Horizontal privilege escalation via flat authorization checks.

## Control

Explicit scope and tenant match enforcement.
