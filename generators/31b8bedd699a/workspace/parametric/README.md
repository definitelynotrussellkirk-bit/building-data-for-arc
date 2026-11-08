# Native token-size / spatial-order family

Status: **reviewer-ready, owner-pending**. This task-local family does not modify
the selected production generator, canonical Racket authority, accepted-family
ledger, or training mix.

## Rule family

Every setting keeps the reviewed frame pipeline:

1. find four-connected monochrome components and retain the hollow frames;
2. derive an input-dependent axis from the ranges of frame top rows and left
   columns (`vertical` only when the row range is strictly larger; ties are
   horizontal);
3. sort frames on that derived axis in the episode-selected spatial order; and
4. redraw each frame as a same-colored hollow square of the episode-selected
   token size.

The private parameters are fixed for one complete episode:

- `token_size`: `3`, `4`, or `5`;
- `order`: `ascending` or `descending`.

`{"token_size":4,"order":"ascending"}` is the exact selected canonical
Racket source, byte-for-byte. The descending programs alter only the frame-order
site by reversing the canonical stable sort. The six settings share identical
inputs for the same seed and requested counts.

This is a genuine two-stage dependency. Stage A emits the horizontal/vertical
axis from the input. Stage B must consume that intermediate to choose both the
sort coordinate and output packing orientation. The retained witness forces the
wrong axis on a qualified vertical example and replays both programs through
protected Racket; the final grid changes.

## Episode construction

The adapter supports two to six demonstrations and one to four queries with
independent prefix stability. The minimum two-example lesson deliberately shows
one vertical and one horizontal input. Candidate pairs are retained only when:

- one input separates all six declared settings;
- the first two demonstrations uniquely identify every selected setting; and
- none of the eight named finite rivals fits both visible demonstrations.

The four query slots are fixed independently of demonstration count. They include
one dense 30×30 input with five frames, three solids, at least four colors, and
content translated to touch the top and left canvas boundaries.

The earlier token-size / tie-policy prototype remains as authoring history, but
it is not the promoted adapter. A reviewer audit found that its two-example
`vertical` lesson could be fit by an `always vertical` rule and then fail a
horizontal query. Replacing tie policy with spatial order removed that teaching
hole while preserving the canonical default exactly.

## Native files

- `adapter.py` — exact-path native adapter with `program(settings)` and
  `generate(seed, settings, demos, queries)`.
- `promotion.json` — six-setting contract and supported counts.
- `native_family.py` — matched-input sampler, Python oracle, Racket program
  construction, two-stage decomposition, and finite rival family.
- `audit_native_family.py` — reusable bounded audit that samples each seed once,
  evaluates all settings over the same bytes, checks every supported visible
  prefix, and refuses to overwrite prior evidence.
- `prototype.py` — retained generator-facing construction and canonical-source
  helper reused by the native family.

## Replay

From the packet root, run the finite audit:

```bash
python3 review.py run \
  env PYTHONPATH=shared/runtime python3 \
  generators/31b8bedd699a/workspace/parametric/audit_native_family.py \
  --out ../checks/31b8bedd699a/native-audit.json --seed-count 32
```

Run the complete task-local suite with protected Racket available:

```bash
python3 review.py run \
  env PYTHONPATH=shared/runtime python3 -m pytest -q \
  generators/31b8bedd699a/tests
```

Create current source/evidence inventory and native qualification with:

```bash
python3 review.py run env PYTHONPATH=src python3 -m arcpuzzles parametric manifest \
  31b8bedd699a \
  --evidence generators/31b8bedd699a/workspace/parametric/evidence/current \
  --include generators/31b8bedd699a/tests/test_parametric_native_adapter.py \
  --reported-checks 'See the scoped receipts in evidence/current.'

python3 review.py run env PYTHONPATH=src python3 -m arcpuzzles parametric qualify \
  31b8bedd699a --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/31b8bedd699a/qualification --summary
```

All evidence is finite. It covers the declared settings, named rivals, listed
seeds, and supported count prefixes; it is not a proof against arbitrary
programs or a claim of model-learning benefit. Owner acceptance and every
training-admission decision remain separate downstream actions.
