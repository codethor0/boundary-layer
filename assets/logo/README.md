# BoundaryLayer Visual Identity

Hand-authored SVG assets for BoundaryLayer. All files are plain SVG with simple shapes only. There are no embedded raster images, external font files, remote resources, scripts, or image-generator metadata.

## Selected concept

**Concept A: Strata Conduit** (see [CONCEPT_REVIEW.md](CONCEPT_REVIEW.md))

Horizontal infrastructure strata represent layered trust zones and blast-radius segmentation. A vertical inspection conduit with checkpoint nodes at each boundary expresses controlled, inspected flow without shield, lock, hexagon, or robot clichés.

## Asset list

| File | Purpose |
|------|---------|
| `concepts/boundarylayer-concept-a.svg` | Strata conduit concept (selected) |
| `concepts/boundarylayer-concept-b.svg` | Contour ingress concept (archive) |
| `concepts/boundarylayer-concept-c.svg` | Chevron perimeter concept (archive) |
| `boundarylayer-mark.svg` | Icon-only mark for favicons and compact UI |
| `boundarylayer-wordmark.svg` | Text-only wordmark for light backgrounds |
| `boundarylayer-logo.svg` | Mark plus wordmark for README and light backgrounds |
| `boundarylayer-logo-dark.svg` | Mark plus wordmark for dark backgrounds |
| `boundarylayer-social-preview.svg` | 1200x630 social card layout |

## Color palette

| Name | Hex | Usage |
|------|-----|-------|
| Navy | `#0B1F3A` | Outer stratum stroke on light backgrounds |
| Deep Blue | `#1D4ED8` | Middle stratum stroke |
| Blue | `#2563EB` | Inspection node accent |
| Sky | `#0EA5E9` | Mid-conduit segment |
| Cyan | `#38BDF8` | Ingress conduit segment |
| Teal | `#14B8A6` | Inner stratum stroke |
| Green | `#22C55E` | Egress conduit segment |
| Light | `#F8FAFC` | Conduit cutout on light backgrounds |
| Slate | `#64748B` | Secondary text on social preview |
| Dark | `#020617` | Dark logo and social card background |

## Usage guidance

- Use `boundarylayer-mark.svg` at 32x32 or larger for icons and avatars.
- Use `boundarylayer-logo.svg` in README and documentation on light backgrounds.
- Use `boundarylayer-logo-dark.svg` on dark GitHub themes or dark slides.
- Use `boundarylayer-social-preview.svg` for social cards; export to PNG locally if a platform requires raster output.

Do not commit raster exports to the repository unless explicitly required.

## Small-size guidance

The mark uses bold stratum bands and a central conduit so it remains readable at 32x32. Avoid scaling below 24px without testing.

## Accessibility

- SVGs include `role="img"` and `aria-label` attributes.
- Shape contrast carries meaning; color reinforces but does not stand alone.
- Wordmark uses system UI fonts for readability without external dependencies.

## Inspection and editing

These files are safe to inspect and edit in any text editor or vector tool. They contain only `rect`, `line`, `circle`, `path`, `polygon`, `text`, and `g` elements. No trademark is claimed.

Logo SVG validation runs as part of `make validate`.
