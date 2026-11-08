# Native branch-direction family

This task-local proposal retains the exact canonical `toward_trunk` Racket
program and the reviewed `away_to_edge` alternative from `prototype.py`.
`branch_direction` is fixed for the whole episode. First identify the unique
aligned red pair and derive its orientation, line and span. That intermediate
determines the trunk and each branch's connector direction. Substituting a
canvas-centered line changes the later painting. This is an input-derived
geometry dependency, not iterative state simulation.

`adapter.py` forwards to `native_family.py`; `promotion.json` declares the two
settings. Native `generate(seed, settings=None, demos=3, queries=4)` accepts exact
integer seeds in `0..2**63-1`, independently accepts 2–6 demos and 1–4 queries,
and returns claim labels for native protected-Racket checking. It does not run
a nested reference audit. Omitting settings selects the canonical default.

## Input and teaching contract

The opt-in grammar extends dimensions to 10..30 and branch count to 1..27 where
geometry permits. There is exactly one aligned pair, every branch lies inside
its span and at least two cells off its line, branch coordinates are distinct
on both axes, and multiple branches occupy both sides. Unrelated distractors
are not part of this grammar. The selected production generator remains
unchanged at 10..24 and 1..5 branches.

The sampler constructs six demo inputs and four query inputs directly, using
separate per-slot input RNG streams, before slicing either count. The setting
does not affect those inputs. The first two demos cover both orientations, both
sides, off-center trunks, internal endpoints, unequal ray lengths, six or more
branches and a branch between the trunk and the canvas midpoint. These contrasts
separate direction, one-sided, fixed-center, nearest-edge and branch-count
shortcuts without adding demonstrations. Independent finite-rival auditing lives
in `audit_native.py`.

Queries cover 10×10, medium rectangles, 30×17 or 17×30, and 30×30. The last query
has 14–18 branches and nonzero output in all four quadrants under either setting;
the largest optional demo has 20–22 branches. Boundary branches may have a
zero-length outward ray. Trunk endpoints and branch reds remain red. These are
full-canvas layouts rather than a small scene padded with empty rows.

## Executed examples and safe projections

From the outer packet folder, using its prepared interpreter:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/d8111f3f714d/workspace/parametric/make_examples.py \
  --seed 0 --demos 3 --queries 4 \
  --out ../checks/d8111f3f714d/examples-new \
  --report ../checks/d8111f3f714d/examples-new-report.json
```

Only `turns/<sha>.json` is actor-visible: demonstrations plus exactly one masked
query. `private/controllers/` retains all query inputs for the consuming
controller, and `private/metadata.jsonl` plus `private/context.json` retain
settings, labels, exact programs, native execution and reconstructed adapter
metadata. Public IDs hash only the exact visible bytes. Future inputs, total
query count, settings, seeds and answers cannot change the first turn. Turn
sequencing remains the consuming controller's responsibility; this writer does
not implement or test a turn controller. Existing output paths and duplicate
visible payloads are refused; the completion manifest is written last.

`make_examples.py` executes the native worker and verifies reconstructed labels
and programs before publishing. Its report is example execution, not owner
acceptance. It preserves the native wrapper's historical reference marker while
explicitly recording `owner_pending` and `training_admitted: false`.

## Qualification and retained legacy path

After the source/evidence inventory is current, qualify every setting with:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  d8111f3f714d --seed 0 --seed 17 --demos 6 --queries 4 \
  --out ../checks/d8111f3f714d/qualification --summary
```

Six demos deliberately exercise the complete bank; the ordinary API and example
builder default to three. The independent teaching audit checks the two-demo
minimum. Reviewer qualification and causal replay remain separate from fresh
owner qualification/acceptance after integration; neither admits training data.
Finite seeds and declared rivals do not establish universal identifiability or
measured training benefit.

The original `prototype.py` remains available unchanged with its original
sampling/count limits. Its historical `public/` files contain multiple query
inputs and must be treated as controller payloads. New model-facing exports use
the single-query `turns/` projection above.
