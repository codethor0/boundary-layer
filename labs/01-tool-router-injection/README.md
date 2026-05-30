# Tool Router Injection Lab

Demonstrates how poisoned retrieved content can influence simulated tool routing.

## Modes

- **vulnerable**: Trusts retrieval content; poisoned instructions route to destructive tool.
- **hardened**: Detects instruction-like patterns and blocks tool execution.

## Validation

```bash
curl -X POST http://localhost:8000/labs/tool-router/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/tool-router/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

## Risk

Indirect prompt injection via RAG or retrieval poisoning.

## Control

Instruction-pattern detection and tool execution block.
