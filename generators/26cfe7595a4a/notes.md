# Working notes: 26cfe7595a4a

## 2026-10-25 base repair

- Replaced the inherited dead/aliased controls with strict observable axes: `grid_h`, `grid_w`, `motif_size`, `palette_kind`, `color_count`, `density`, and `position_bias`.
- Added `RULE_HASH = "a6ccad31118b"`, exact override validation, 6..30 dimensions, an exact square motif bbox, exact nonzero color count, and a fail-closed `self_check` for rectangular ARC grids with a strict background margin.
- Ordinary `None` and `medium` generation now pass the packet authoring preflight; the canonical crop rule and authority program were not changed.

## Native parametric family

- `border_rule=crop_only` is byte-exact canonical behavior.
- `border_rule=highlight_perimeter_mode` first performs the tight crop, then finds the unique most frequent nonzero color on the crop-created perimeter and recolors all of that color to 8.
- Constructive teaching scenes make the perimeter winner disagree with crop-wide mode, top-row mode, left-column mode, first/corner color, least-perimeter mode, and the alternate setting.
- The family supports independent `demos=2..6` and `queries=1..4`, uses matched inputs, and retains four distinct queries including a substantive 30x30 input.
- Bounded evidence: 3/3 repaired-base task tests, 9/9 combined focused tests, six audit jobs with 72 protected-Racket evaluations, four authoring-preflight jobs with 32 protected-Racket evaluations, a wrong-intermediate witness changing 26 cells, and 16 strict one-query public projections.
- Finite rival checks are not a universal uniqueness proof. Owner exact-source qualification, acceptance, and any training admission remain separate.
