# Native bbox-threshold reconstruction

`min_bbox_area` is fixed for an entire episode and is one of **2, 4, 8**.
Discover nonzero same-color 4-connected components and retain components whose
bounding-box area is strictly greater than the cutoff. Retained bounding-box
edges define row/column intervals. Read the covering object's color in each
interval intersection, use zero for an uncovered slot, and reverse the columns.
The default uses the canonical Racket source byte for byte. The canonical
generator and all canonical/archival rules are unchanged.

## Supported requests and input grammar

`adapter.generate(seed, settings, demos=3, queries=4)` supports exact integer seeds
in `0..2**63-1`, 2–6 demos and 1–4 queries independently. No global RNG is used.
The same seed/split/index produces the same input across settings and counts;
requesting one query produces the exact first query of a four-query request.
The ordinary lesson has three demonstrations and four distinct private queries.

Scenes combine a dense connected noisy mosaic with independently colored sparse
objects and singleton/domino fragments. Every core tile spans its bounding box,
retains 4-connectivity after carving, and differs from cardinally adjacent tiles.
Two guaranteed demonstrations contain bbox-area/cell-count pairs 3/3, 4/3, 6/4,
8/5, 9/5 and 12/6. A mandatory zero row separates rotated top fragments from
the mosaic so shared colors cannot accidentally merge them. Global quarter turns
and reflections vary placement; all outputs are recomputed from the actual input.

The four query profiles are 14x17, 18x23, 30x30 and 29x30, with transposes when
rotated. The 30x30 query contains a 24x24 noisy core with 25 real tiles, sparse
objects and boundary contacts. This broadens the separate parametric grammar;
the calibrated production generator's four original profiles are unchanged.

## Teaching and causal dependency

The declared cutoff settings and six explicit rivals are tested with protected
Racket: pixel-count filtering, inclusive cutoff, keep-all, partition-before-filter,
no reflection, and sampling the slot's corner pixel. A rival surviving all demos
must agree on every query. Pixel-count and bbox filtering at strict cutoff 2 are
equivalent on 4-connected components and are recorded as such. The finite rival
checks do not establish uniqueness against arbitrary programs.

**A:** Discover components, retain the eligible boxes, and derive sorted boundary
sets. **Intermediate:** retained colored boxes and row/column boundary lists.
**B:** Allocate the output matrix and compute reflected slot destinations using
those lists. A wrong intermediate that includes discarded-component edges but
still paints only eligible boxes changes output dimensions and destinations.
The source-bound `checks/5c9fd75979d1/causal/witness.json` executes both programs.
This demonstrates a data dependency, not iterative simulation.

## Run in a review packet

From the outer folder containing `review.py`, use the selected ready interpreter:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/5c9fd75979d1/tests/test_parametric_threshold.py \
  generators/5c9fd75979d1/tests/test_parametric_projection.py -q

WORK/.venv/bin/python review.py run python3 \
  generators/5c9fd75979d1/workspace/parametric/audit.py \
  --out ../checks/5c9fd75979d1/new-audit

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  5c9fd75979d1 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/5c9fd75979d1/new-qualification --summary

WORK/.venv/bin/python review.py run python3 \
  generators/5c9fd75979d1/workspace/parametric/export_qualified.py \
  --qualification ../checks/5c9fd75979d1/new-qualification/qualification.json \
  --out ../checks/5c9fd75979d1/new-projected
```

Run the native manifest helper after source changes and before qualification;
see `docs/parametric-promotion.md`. Choose new evidence destinations. The retained
manifest includes the current source, task tests and bounded audit. The reusable
audit reports sampling failures explicitly; failed rival execution never counts
as a distinguishing demonstration.

## Projection and acceptance boundary

The exporter validates source-bound native qualification and its execution digest.
It writes `public/<visible-sha256>.json` with demos plus **one query input** per
file. Give only the selected file to the model. `private/manifest.json` retains
ordered public IDs, labels, rule settings, programs and the source binding for
the existing consumer. The first projection is identical to single-query use.
Changing private labels, seeds/settings or future inputs cannot change its bytes
or ID. Duplicate visible challenges and existing destinations are rejected.

The exporter performs static receipt checks; it does not replay Racket or grant
acceptance. Qualified examples are reviewer evidence. The owner must integrate
the exact source, freshly qualify it and perform native acceptance. No training
data admission or trainer allocation change is part of this return.
