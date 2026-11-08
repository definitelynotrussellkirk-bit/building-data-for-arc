# Native payload-axis translation family

This workspace now contains the native promotion candidate for task
`1a8932958b14`.

## Declared parameter

`translation_policy` has two episode-fixed settings:

- `marker_vector` — the exact selected canonical program, byte-for-byte. Move
  the payload by `green - red`.
- `payload_axis_gate` — first classify the payload bounding box as **wide** or
  **tall**, then use that input-dependent intermediate to select the marker
  vector multiplier: wide → `+2`, tall → `-1`.

The alternative therefore has a real sequential dependency. Step B cannot
select its translation until Step A has classified the current payload. The
protected-Racket causal witness forces the wrong `tall` intermediate on a wide
payload and records the changed final grid.

## Episode contract

- 2–6 demonstrations and 1–4 queries are supported independently.
- Inputs are identical across settings for the same seed and counts.
- The first two demonstrations are a controlled wide/tall pair with the same
  grid size, marker vector, palette cardinality, and density.
- Four queries have sizes `18×22`, `22×18`, `26×30`, and `30×30`.
- Every input keeps multiplier `-1`, `+1`, and `+2` translations in bounds.
- Public projections expose demo labels and masked query inputs only; settings,
  programs, and query answers remain private.

`adapter.py` and `family.py` are the current native source. `canonical.rkt` is
an exact byte copy of the selected reference program. `promotion.json` is the
promotion contract. The earlier `prototype.py`, `build_evidence.py`, and their
old evidence are retained only as historical vector-multiplier draft material;
they are not the declared current family design.

## Focused checks

From the outer packet directory:

```bash
python3 review.py task-tests 1a8932958b14 --phase after \
  --out ../checks/1a8932958b14-tests

python3 review.py run python3 -m arcpuzzles parametric qualify \
  1a8932958b14 --out ../checks/1a8932958b14/qualification --summary

python3 review.py run python3 \
  generators/1a8932958b14/workspace/parametric/build_native_evidence.py \
  --qualification ../checks/1a8932958b14/qualification/qualification.json \
  --out ../checks/1a8932958b14/native-evidence

python3 review.py run python3 -m arcpuzzles.review_witness check \
  --qualification ../checks/1a8932958b14/qualification/qualification.json \
  --witness ../checks/1a8932958b14/native-evidence/causal/witness.json \
  --out ../checks/1a8932958b14/native-evidence/causal-check.json

python3 WORK/check_public_exports.py \
  WORK/checks/1a8932958b14/native-evidence/public --demos 2 --queries 4
```

The retained native qualification is reviewer evidence only. Owner acceptance
on the exact integrated bytes is still required, and no training admission is
claimed.
