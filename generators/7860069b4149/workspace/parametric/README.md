# Proposed trail-mode family for `7860069b4149`

Status: **proposed and unapproved**. This does not change the selected canonical
Racket authority, approve a parametric family, or admit any records to training.

The hidden episode parameter is fixed across all demonstrations and queries:

- `continuous` (default/canonical): paint every valid translated component copy.
- `terminal_only`: preserve the input and paint only the farthest valid copy.

Both settings retain the original reasoning chain: isolate the non-9 connected
component, infer direction from the 9-anchor relative to its bounding box,
translate the complete shape without collapsing holes, and stop at the wall.
Inputs are sampled independently of the setting. Every label is executed through
the protected Racket bridge and checked against an independent Python mirror.
Demonstrations are restricted to 2–6; queries are independently 1–8, with four
by default. The fourth default query is a substantive 30×30 case.

`public_query_turns()` projects a stored episode into one public query per turn.
It exposes no future inputs, no query answers, and no total-count hint; turn one
contains the same visible challenge bytes as single-query use. Public IDs hash
only the exact visible bytes, so private settings, seeds, programs, and answers
cannot affect filenames.

From the packet root:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/7860069b4149/workspace/parametric/prototype.py \
  episode --seed 11 --mode terminal_only --demos 3 --queries 4

WORK/.venv/bin/python review.py run python3 \
  generators/7860069b4149/workspace/parametric/prototype.py \
  evidence --seed 53 \
  --out generators/7860069b4149/workspace/parametric/evidence/current \
  --demos 3 --queries 4

WORK/.venv/bin/python review.py run python3 \
  generators/7860069b4149/workspace/parametric/prototype.py \
  verify generators/7860069b4149/workspace/parametric/evidence/current
```

`public/` contains only demonstration inputs/outputs and query inputs. Private
settings, exact programs, and query labels remain under `private/`. Verification
is fail-closed: it binds the current generator and exact program hashes,
reconstructs each public projection, requires both settings and declared counts,
checks the complete file inventory, rejects paths outside the evidence root, and
rejects rehashed answer tampering. Focused mutation tests exercise each of those
trust boundaries. Owner-side protected qualification and explicit acceptance
remain required before use.
