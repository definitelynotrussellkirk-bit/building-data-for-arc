# Guide-and-crop alignment: native parametric candidate

Task `4512012999bb`, canonical generator version `3.0.0`. This is a separate
opt-in family. The production generator and its Racket authority are unchanged.
Native source qualification is a reviewer deliverable; exact-source acceptance
after integration belongs to the owner. These artifacts do not activate training.

## Rule and parameter

Recover the unique pair of vertical guide walls whose dimensions accommodate the
separate nonzero crop. Read each wall's **first interior color**. Count matching
crop colors in the left and right halves, once in direct orientation and once
reflected horizontally. An odd middle column contributes to neither score.

| Episode-fixed `alignment` | Orientation decision |
|---|---|
| `match` (default) | Reflect only when the reflected side-color score is greater. |
| `contrast` | Reflect only when the reflected side-color score is smaller. |

Both keep direct orientation on ties, preserve every crop cell, and copy both
walls row by row. `program({"alignment":"match"})` is the exact canonical Racket
text; the alternative changes only the guarded final comparison.

The dependency is substantive: recovered guide colors and crop contents produce
an input-dependent score pair; that pair determines which crop orientation is
inserted. A fixed orientation can disagree even when frame geometry is unchanged.
This is derived-cue reasoning, not a claim of iterative simulation.

## Supported requests and teaching

`generate(seed, settings, demos, queries)` accepts an exact integer seed in
`0..2**63-1`, **3–6 demonstrations** and **1–4 queries**, independently. Ordinary
use is three demonstrations and four queries. Two demos are deliberately not
offered: the three constructive witnesses teach strict direct, strict reflected,
and asymmetric tied decisions without dropping the tie branch.

Inputs use independent deterministic RNG streams. The same seed and counts give
identical inputs under both settings; colors, placement, lower crop rows, query
support and distractor colors vary without revealing the setting. Increasing the
query count preserves the demonstrations and query prefix. Every input in an
episode is distinct. Invalid requests fail instead of coercing counts or returning
a short episode. Each random input has at most 32 construction attempts.

The Python teaching guard rejects ten declared shortcuts using demonstrations
alone: fixed direct/reflected orientation, reflected ties, first-row/edge-only
scores, one-sided scores, majority/last-wall colors, and uniform wall copying.
`audit.py` independently executes their Racket programs. This finite set does not
establish uniqueness against arbitrary programs or measured learning benefit.

The separate grammar requires one candidate, spatially disjoint crop/frame,
different first-interior side colors and common endpoint markers. It extends the
unchanged canonical generator's pedagogical output-height bound to lawful tall
frames. No `height`/`width` production override is being advertised.

| Query index (private) | Input size | Output size | Content |
|---|---:|---:|---|
| 0 | 7×10 | 5×5 | Small odd-width crop |
| 1 | 16×21 | 8×11 | Wider odd-width crop |
| 2 | 24×26 | 24×13 | Tall guides and 22×11 crop |
| 3 | 30×30 | 30×16 | Boundary-contacting guides and dense 28×14 crop |

The largest case contains pattern cells across the large canvas, not a padded
small task. The reference performs a finite candidate search; evidence reports
the measured execution time rather than promising a throughput bound.

## Run from the outer packet directory

Use the packet's Python environment and bundled Racket:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/4512012999bb/workspace/parametric/export.py \
  --seed 0 --demos 3 --queries 4 --alignment both \
  --out ../checks/4512012999bb/new-public-export

WORK/.venv/bin/python review.py run python3 \
  generators/4512012999bb/workspace/parametric/audit.py \
  --out ../checks/4512012999bb/new-self-review

WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/4512012999bb/tests/test_parametric.py \
  generators/4512012999bb/tests/test_parametric_export.py
```

The exporter executes every label in protected Racket before publishing. It
writes sorted, hash-named `public/*.json`, `public.jsonl`, separate `private.jsonl`
and a file-hash manifest. Existing destinations and duplicate visible episodes
are refused. `verify_export(path)` checks serialized hashes, strict types and
public/private projection; it does not replay Racket or authenticate a bundle
against a party able to rewrite every file.

Four-query public files are **controller data**, not complete model prompts.
`one_query_bytes(episode, index)` returns only the original demonstrations and
one query input, using the shared exact-public-byte helper. No query ordinal,
total-count hint, future input, settings, code or query answer enters that view.
The first turn is byte-identical to single-query use. Reveal subsequent inputs
through the existing consumer after each answer; this package adds no controller.

## Native qualification and owner handoff

After final source and task-local evidence are settled, the native manifest
inventories them; qualification executes each setting on multiple seeds:

```bash
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric manifest 4512012999bb \
  --evidence generators/4512012999bb/workspace/parametric/evidence/current \
  --include generators/4512012999bb/tests/test_parametric.py \
  --include generators/4512012999bb/tests/test_parametric_export.py \
  --reported-checks 'Use the actual retained focused tests and Racket self-review results.'

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 4512012999bb \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/4512012999bb/qualification
```

An existing manifest requires its native guarded replacement option. Source or
inventoried-evidence edits require a new inventory and qualification. The return
also contains a final-source-bound causal witness and protected replay. After
integration the owner must qualify and accept the exact live bytes. Reviewer
`ready`, canonical approval and accepted parameter variants are distinct states.
