# dc91f4798e24 — count components, not pixels

Version: **3.0.1**. Rule hash: `1493886adfda` (unchanged).

A zero-background grid contains monochromatic four-connected bodies of colors 1, 2 and 3, plus optional irrelevant colors 4–9. Count bodies separately by target color. The output is three left-aligned histogram rows, colors 1/2/3, with width `max(1,n1,n2,n3)`; labels are produced by the canonical Racket rule.

The generator varies component counts and areas, same-color diagonal contacts, different-color contacts, positions and boundary contact. Every ordinary input contains at least one multi-cell target body. All three target colors occur and at least two component counts differ. A 40% canonical-scale shape/palette mixture remains present at every difficulty; the rest uses difficulty-scaled grids. Explicit dimensions always take precedence.

Axes: `grid_h=7..18`, `grid_w=8..22`, and `texture=default|sparse|dense|varied|diagonal`. Unknown overrides are rejected. Explicit negative textures `equal_counts`, `missing_color`, and `no_components` remain diagnostic fixtures, not ordinary advertised valid draws.

Task-local tests and reference/audit/portability probes are in `tests/` and `workspace/`. Review evidence is source-bound; a green reviewer battery does not itself confer catalog approval or training admission.
