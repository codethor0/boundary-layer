# BoundaryLayer Visual Identity

Hand-authored SVG assets for BoundaryLayer. All files are plain SVG with simple shapes only. There are no embedded raster images, external font files, remote resources, scripts, or image-generator metadata.

## Selected concept

**Concept B: Angular Boundary Stack** (see [CONCEPT_REVIEW.md](CONCEPT_REVIEW.md))

Nested angular hexagonal layers represent infrastructure trust zones. A central gate and crossing path express inspected, shaped traffic and blast-radius control without shield, lock, or robot clichés.

## Asset list

| File | Purpose |
|------|---------|
| `concepts/boundarylayer-concept-a.svg` | Contour stack concept (archive) |
| `concepts/boundarylayer-concept-b.svg` | Angular boundary stack concept (selected) |
| `concepts/boundarylayer-concept-c.svg` | Perimeter gate concept (archive) |
| `boundarylayer-mark.svg` | Icon-only mark for favicons and compact UI |
| `boundarylayer-wordmark.svg` | Text-only wordmark for light backgrounds |
| `boundarylayer-logo.svg` | Mark plus wordmark for README and light backgrounds |
| `boundarylayer-logo-dark.svg` | Mark plus wordmark for dark backgrounds |
| `boundarylayer-social-preview.svg` | 1200x630 social card layout |

## Color palette

| Name | Hex | Usage |
|------|-----|-------|
| Navy | `#0B1F3A` | Outer boundary stroke on light backgrounds |
| Deep Blue | `#1D4ED8` | Middle boundary layer |
| Blue | `#2563EB` | Accents and dark-background outer layer |
| Cyan | `#38BDF8` | Ingress crossing path |
| Teal | `#14B8A6` | Inner boundary layer |
| Green | `#22C55E` | Egress crossing path accent |
| Light | `#F8FAFC` | Gate cutout on light backgrounds |
| Slate | `#64748B` | Secondary text on social preview |
| Dark | `#020617` | Dark logo and social card background |

## Usage guidance

- Use `boundarylayer-mark.svg` at 32x32 or larger for icons and avatars.
- Use `boundarylayer-logo.svg` in README and documentation on light backgrounds.
- Use `boundarylayer-logo-dark.svg` on dark GitHub themes or dark slides.
- Use `boundarylayer-social-preview.svg` for social cards; export to PNG locally if a platform requires raster output.

Do not commit raster exports to the repository unless explicitly required.

## Small-size guidance

The mark uses bold strokes and a simple gate silhouette so it remains readable at 32x32. Avoid scaling below 24px without testing.

## Accessibility

- SVGs include `role="img"` and `aria-label` attributes.
- Shape contrast carries meaning; color reinforces but does not stand alone.
- Wordmark uses system UI fonts for readability without external dependencies.

## Inspection and editing

These files are safe to inspect and edit in any text editor or vector tool. They contain only `polygon`, `rect`, `line`, `circle`, `path`, `text`, and `g` elements. No trademark is claimed.

Logo SVG validation runs as part of `make validate`.
