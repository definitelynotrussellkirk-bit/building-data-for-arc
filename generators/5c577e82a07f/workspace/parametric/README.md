# Completed borders → largest enclosure

`enclosure_policy=borders_only` returns the exact selected canonical Racket
program. `largest_enclosure` first completes every rectangle border, recomputes
4-connected zero regions on that completed grid, discards regions touching the
grid boundary, and fills the unique largest remaining region with color 8.
Nested rectangles make the winning region an input-dependent annulus or inner
pocket rather than a direct original rectangle fill.

`audit.py` is reusable after edits. It sweeps supported demonstration/query
counts, checks setting-neutral inputs and count prefixes, attacks the finite
rival bank, replays selected labels through protected Racket, and writes strict
content-addressed public challenges separately from private audit metadata.

After packet setup, run the complete 50-seed audit directly so it is not
limited by the short generic launcher timeout:

```bash
cd WORK/repo
RACKET_PATH=../.review/racket-runtime/racket/bin/racket \
PYTHONPATH=shared/runtime:. \
python3 generators/5c577e82a07f/workspace/parametric/audit.py \
  --out ../checks/5c577e82a07f/authoring-audit --stress-seeds 50
```

For a faster launcher-bound smoke check from the packet root, use the same
script through `review.py run` with `--stress-seeds 30`.
