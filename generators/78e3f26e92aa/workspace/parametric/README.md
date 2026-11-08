# Parametric prototype for `78e3f26e92aa`

This directory is a **task-local proposed extension**. It does not modify or
approve the canonical generator or Racket authority.

## Rule settings

Each episode fixes one setting for every demonstration and query:

- `step_multiplier`: `1` is canonical; `2` makes each horizontal ray step
  outward every two bar-heights instead of every bar-height.
- `overlap_color`: `6` is canonical; `2` is the proposed alternative color
  where the green and cyan ray systems meet.

The four supported settings are named `canonical`, `slow`, `recolor`, and
`slow-recolor`. The original object roles, outward-ray construction, vertical
bar-height measurement, and overlap test stay invariant. Input constraints do
not depend on the parameters.

The default authoring shape is exactly three demonstrations and four distinct
queries. Counts are separate CLI options. Demonstrations are selected to refute
all three rival settings before query answers are considered. The hard limits
are 1–8 demonstrations and 1–4 queries.

## Build with protected Racket

Run from the packet's `WORK` directory after `python3 setup_racket.py`:

```bash
python3 run_with_racket.py python3 generators/78e3f26e92aa/workspace/parametric/prototype.py build --seed 1704 --setting all --demo-count 3 --query-count 4 --out ../checks/parametric/run-1704
```

`--seed` is a batch seed. Internally, setting index `i` receives episode seed
`4 * seed + i`, so the existing deterministic `seed % 4` selector chooses the
requested setting exactly once for that episode.

The output contains:

- `public/<sha256>.json`: exactly
  `reviewer_support.public_challenge_bytes(...)`; demonstrations include labels,
  queries include inputs only, and the filename is the SHA-256 of those bytes.
- `private/<sha256>.private.json`: complete labeled episode, fixed setting,
  exact Racket text/hash, and protected-runtime execution receipt.
- `manifest.json`: source hashes and paths binding public and private records.

The writer rejects duplicate visible payloads before creating output folders.
Python mirrors are used only for selection and parity checks; retained labels
come from execution of the matching exact Racket program.

## Verify an existing export without Racket

The verifier rehashes source and public files, recomputes the public projection,
checks all inputs and Python parity, confirms demonstration-only
identifiability, and binds every output hash to a protected-Racket receipt:

Run from the packet root (the directory containing `review.py`):

```bash
python3 review.py run python3 generators/78e3f26e92aa/workspace/parametric/prototype.py verify --input ../checks/parametric/run-1704 --report ../checks/parametric/run-1704/verification.json
```
