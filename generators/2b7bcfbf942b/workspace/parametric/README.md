# Parametric local checker phase — `2b7bcfbf942b`

Status: reviewer build; native qualification and exact-source owner acceptance are separate.

The episode-fixed parameter is `checker_phase`:

- `colored_first` — byte-exact canonical rule. The strict-interior upper-left
  cell of every derived bounding box is colored.
- `zero_first` — flips only that local checker phase.

Inputs are matched across settings and have stable independent prefixes for 2–6
demonstrations and 1–4 private queries. The first two examples jointly contain
complete frames, open frames, crosses, multiple colors, odd global offsets, and
even box widths. They reject the alternate phase plus global-parity, top-right
anchor, frame-only, largest-only, fixed-color, incomplete-border, canonical-size,
border-only, and solid-fill shortcuts.

The four queries scale through 12×15, 18×20, 24×27, and 30×30. The largest has
five separated objects, at least 120 source cells, and contacts every boundary.

The causal chain is component extraction → input-dependent bounding boxes/local
origins → border completion and local checker rendering. `build_witness.py`
shifts the derived row origin by one and replays both final outputs in protected
Racket.
