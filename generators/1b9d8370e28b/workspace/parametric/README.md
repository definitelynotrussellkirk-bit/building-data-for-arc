# Proposed cyan-anchor prototype

This task-local prototype keeps the production generator and canonical Racket
authority separate. It varies one hidden transformation parameter once per
complete episode:

| Parameter | Values | Canonical/default |
|---|---|---|
| `cyan_anchor` | `left`, `right` | `left` |

Both settings preserve the original reasoning structure: infer the straight
cyan/blue split, count red cells independently in each row and region, erase
the original placements, and compact the same row counts to color-directed
edges. The alternative changes only the color-to-edge mapping: cyan moves right
and blue moves left. Input constraints do not depend on the setting. Every
selected-family input contains red cells in both regions and leaves background
visible in each affected row, so the two settings disagree and demonstrations
identify the hidden setting before the query.

From the extracted packet root, build fresh evidence with the included protected
Racket runtime:

```bash
python3 review.py run python3 \
  generators/1b9d8370e28b/workspace/parametric/verify.py \
  --out ../checks/parametric/cyan-anchor-v1 \
  --seeds 0 1
```

The output includes byte-exact Racket programs for both settings, canonical
replay for the default, complete private episodes, public challenge projections
with hidden settings and query answers removed, a same-input disagreement
witness, runtime identity, hashes, a report, and a manifest. Python mirrors are
used only as assertions; all retained labels are executed by Racket.

This is a **proposed, unapproved prototype**. It is not a production parametric
API, a new canonical rule, or a claim that these are the only plausible nearby
variants.

Public filenames are hashes of visible puzzle content, excluding private settings, seeds and query answers. Deliver only the public subtree; original reviewer sources and galleries are retained under `evidence/reviewer-original/`.

## Native promotion handoff

`adapter.py` and `promotion.json` now expose this retained prototype to the
repository's native qualification path without changing the production generator
or canonical authority. The adapter loads the adjacent `prototype.py` by exact
path, keeps `cyan_anchor` fixed for the complete episode, and supports independent
counts of **1–32 demonstrations** and **1–32 queries**. Inputs depend only on the
seed and requested counts, so the two settings receive matched inputs. Duplicate
input draws are skipped deterministically with a bounded 4,096-candidate limit.

The adapter's labels are Python claims only until the native worker re-executes
them. This packet's scoped qualification used both settings on seeds 0 and 17,
with three demonstrations and four queries per job; protected Racket performed
40 evaluations and retained only the selected setting after demonstrations in
all four jobs:

```bash
python3 review.py run python3 -m arcpuzzles.cli parametric qualify \
  1b9d8370e28b \
  --seed 0 --seed 17 \
  --demos 3 --queries 4 \
  --out generators/1b9d8370e28b/workspace/parametric/evidence/promotion-review/qualification
```

Focused adapter tests also exercise the 32+32 boundary, strict scalar rejection,
matched inputs, deterministic duplicate retry, exact default-program identity,
and cached-module isolation. Owner acceptance remains a separate action; this
handoff does **not** approve the variant or admit generated data to training.

