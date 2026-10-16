# Brand files

Unmodified copies of the DiamaneOS brand files (30 September 2026).

| File | SHA-256 |
| --- | --- |
| `assets/brand/diamaneos-lockup-light.svg` | `f3c22c271fc543c7037bfdf5eabb70f47a61c715ada608cc198b34dbb1f36713` |
| `assets/brand/diamaneos-mark-dark.svg` | `a1ed596ff580e50e531860a793342393579cd99dfac45fbc98816657edd82d20` |
| `static/favicon.svg` | `38ffbbd7923fcce0b3d782594646afb93d27dc9737567a006edcf150b1d751f8` |

The font's provenance is in `docs/fonts.md`.

The two SVGs under `assets/brand/` are inlined into the pages by `layouts/_partials/brand-svg.html`, which drops the
title, size and fixed fills and adds classes so the stylesheet colours them per theme. The shapes are not changed.
The stylesheet follows the brand guide: below 48 px on light grounds the lockup is one colour (ink). On dark grounds it
uses the dark variant's colours. The app-icon tile uses the icon ground `#3B3936` with the dark mark.

Check the copies:

```sh
shasum -a 256 assets/brand/*.svg static/favicon.svg
```
