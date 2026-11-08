# Native parametric family: `d377a54f20c6`

The promotion contract is `promotion.json`; the native entry point is
`adapter.py`. The production generator is unchanged.

## Settings

- `finish=redraw_only` is the byte-exact canonical Racket program in
  `rules/canonical.rkt`.
- `finish=highlight_most_stroke_cells` first performs the canonical redraw,
  counts the marker-color stroke cells produced inside each original object
  box, selects the unique maximum, and recolors that complete produced stroke
  to color 9.

The source-bound wrong-intermediate program
`rules/highlight_most_input_markers.rkt` selects by the number of marker cells
in the input instead. Every constructed scene makes that select a different
object.

The adapter supports 2–6 demonstrations and 1–4 queries; production review
uses four distinct, sequentially revealed queries. Inputs are identical across
settings. Query profile order is seed-shuffled, and every episode contains a
30×30 query touching all four canvas boundaries.

## Reproducible checks

From `WORK/`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/d377a54f20c6/tests/test_parametric_native_adapter.py
python3 review.py run python3 \
  generators/d377a54f20c6/workspace/parametric/audit.py \
  --out generators/d377a54f20c6/workspace/parametric/evidence/current/self-audit.json
```

Then rebuild the source manifest and run native qualification. The checked-in
`episode.py` and the three older noncanonical rule variants are retained as
historical prototype material; they are not the current promotion contract.

All conclusions are bounded to generated scenes and declared rivals. This
prototype is not owner-accepted and is not admitted to training by this work.
