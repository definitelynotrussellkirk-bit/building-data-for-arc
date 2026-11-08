# Parametric quadrant-divider reference

Both settings detect the same three distinct colored 2×2 blocks inside a cyan
frame and summarize their positions as a 2×2 color grid. The byte-exact
canonical `block_midrange` rule divides rows and columns at the midpoint of the
extreme block centers. `frame_midpoint` divides at the cyan frame's midpoint.
The input-derived divider is then consumed to place every block color.

The adapter supports 2–6 demonstrations and 1–4 queries with setting-independent
inputs. Every scene is constructive: both dividers assign the three blocks to
three distinct summary cells, their outputs disagree, and fixed canvas-center
and numeric-color-layout shortcuts also disagree. The four-query
bank is privately shuffled and includes a substantive 30×30 frame.

```bash
python3 review.py task-tests 3fb5ef8ad60e --phase after --out ../checks/3fb5ef8ad60e-tests
python3 review.py run python3 generators/3fb5ef8ad60e/workspace/parametric/audit.py \
  --out ../checks/3fb5ef8ad60e/audit.json --seeds 16
```

This is authoring evidence only; owner source review, native qualification and
acceptance, and any training admission remain separate.
