# Demo Preview

BoundaryLayer does not ship a GIF in the default repository. The honest demo artifact is a sanitized terminal transcript captured from real `make smoke` and `make demo` runs.

## Transcript

Full output: [demo-transcript.txt](demo-transcript.txt)

Regenerate after stack changes:

```bash
make up
make capture-demo
```

## What the demo shows

1. **Smoke** — API health, lab list, metrics scrape, Redis vulnerable/hardened pair.
2. **Demo** — Redis tamper contrast, prompt cache isolation, circuit breaker hardened run with alert webhook poll.

## Optional GIF

If `asciinema` and `agg` are installed locally, you can record a cast and convert to GIF. The repository does not commit generated GIFs unless captured in a future release pass with tooling present.
