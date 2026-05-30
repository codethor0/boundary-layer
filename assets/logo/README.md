# BoundaryLayer Visual Identity

Hand-authored SVG assets for the BoundaryLayer open-source project. All files are plain SVG with simple shapes only. There are no embedded raster images, external font files, remote resources, scripts, or image-generator metadata.

## Asset list

| File | Purpose |
|------|---------|
| `boundarylayer-mark.svg` | Icon-only mark for favicons and compact UI |
| `boundarylayer-wordmark.svg` | Text-only wordmark for light backgrounds |
| `boundarylayer-logo.svg` | Mark plus wordmark for README and light backgrounds |
| `boundarylayer-logo-dark.svg` | Mark plus wordmark for dark backgrounds |
| `boundarylayer-social-preview.svg` | 1200x630 social card layout |

## Intended usage

- Use `boundarylayer-mark.svg` at 32x32 or larger for icons and badges.
- Use `boundarylayer-logo.svg` in README and documentation on light backgrounds.
- Use `boundarylayer-logo-dark.svg` on dark GitHub themes or dark slides.
- Use `boundarylayer-social-preview.svg` for social cards and repository preview graphics.

Do not rasterize for Git tracking unless a specific platform requires PNG. Prefer SVG in this repository.

## Color palette

| Name | Hex | Usage |
|------|-----|-------|
| Navy | `#0B1F3A` | Primary text and top boundary layer |
| Blue | `#2563EB` | Middle boundary layer and accents |
| Cyan | `#38BDF8` | Controlled crossing path |
| Teal | `#14B8A6` | Lower boundary layer |
| Green | `#22C55E` | Hardened path accent |
| Light background | `#F8FAFC` | Light logo background |
| Dark background | `#020617` | Dark logo and social card background |

## Accessibility

- SVGs include `role="img"` and `aria-label` attributes.
- Mark and logo rely on shape contrast, not color alone.
- Wordmark uses system UI fonts for readability without external dependencies.

## Design concept

The mark represents layered infrastructure boundaries with a deliberate controlled crossing path. It avoids generic lock or shield icons and communicates observability-ready infrastructure control rather than decorative AI imagery.

## Inspection

These files are safe to inspect and edit in any text editor or vector tool. They contain only `rect`, `path`, `circle`, `text`, and `g` elements.
