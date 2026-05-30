# Logo Concept Review

Three hand-authored SVG concepts for BoundaryLayer v1.0.10 visual refresh. Plain SVG only: no raster images, scripts, external resources, or base64.

## Concept A: Strata Conduit

File: `concepts/boundarylayer-concept-a.svg`

Horizontal infrastructure strata with a vertical inspection conduit and checkpoint nodes at each boundary crossing. Reads as layered blast-radius segmentation with controlled vertical flow.

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Memorability | 5 | Distinct stacked-band silhouette unlike common security icons |
| Originality | 5 | Strata plus conduit is unique in this repo and uncommon in OSS marks |
| GitHub avatar readability | 5 | Bold bands and central conduit survive 32x32 |
| Technical meaning | 5 | Strong layer, boundary, and inspection metaphor |
| Small-size legibility | 5 | Simple geometry, no fragile arcs |
| README fit | 5 | Aligns with infrastructure and blast-radius narrative |
| Open-source feel | 5 | Engineering diagram aesthetic, not corporate clip-art |
| Avoidance of clichés | 5 | No shield, lock, hexagon stack, or robot imagery |

## Concept B: Contour Ingress

File: `concepts/boundarylayer-concept-b.svg`

Nested rounded-square contours with corner gate cuts and a diagonal crossing path through successive trust zones.

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Memorability | 4 | Readable but diagonal path can blur at very small sizes |
| Originality | 4 | Corner-gate motif is strong but busier than Concept A |
| GitHub avatar readability | 3 | Diagonal line and corner cuts merge at 32x32 |
| Technical meaning | 4 | Suggests perimeter topology and staged ingress |
| Small-size legibility | 3 | Multiple corner cuts reduce clarity when scaled down |
| README fit | 4 | Fits boundary story but less immediately legible |
| Open-source feel | 4 | Technical, slightly abstract |
| Avoidance of clichés | 5 | Avoids shield and lock patterns |

## Concept C: Chevron Perimeter

File: `concepts/boundarylayer-concept-c.svg`

Nested chevron perimeters narrowing toward a central vertical conduit.

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Memorability | 4 | Chevron stack is recognizable |
| Originality | 3 | Triangular perimeter motifs appear in infra tooling |
| GitHub avatar readability | 4 | Central conduit remains visible |
| Technical meaning | 4 | Suggests funneling traffic through nested perimeters |
| Small-size legibility | 4 | Fewer elements than Concept B |
| README fit | 3 | Less aligned with horizontal infrastructure layers |
| Open-source feel | 3 | Slightly badge-like |
| Avoidance of clichés | 4 | Avoids lock/shield but feels like a funnel icon |

## Selected concept

**Concept A: Strata Conduit**

Rationale: Best balance of memorability, originality, and small-size legibility. Horizontal strata communicate infrastructure layers and blast-radius segmentation. The vertical conduit with checkpoint nodes expresses inspected, constrained flow through each boundary without resorting to security clichés. It is more distinctive than the prior hexagonal stack and scales better than the diagonal contour design.

Final production assets in `assets/logo/` are derived from Concept A.
