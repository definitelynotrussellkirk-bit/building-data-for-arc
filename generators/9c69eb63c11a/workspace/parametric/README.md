# Native parametric candidate: area-rank object selection

This directory contains a reviewer-built native promotion candidate for
`9c69eb63c11a`. It is **ready for owner qualification/acceptance**, not accepted
or training-admitted by this return.

## Contract

- Private episode parameter: `selection_mode` in
  `{median, second_largest}`.
- Default: `selection_mode=median` returns `canonical.rkt` byte-for-byte;
  canonical SHA-256 is
  `e0d91c9e70a70e962e245e26ca6954646200dc6a6aa46738475302920931e3aa`.
- Semantics: extract nonzero four-connected objects, rank them by area using the
  canonical stable tie rule, select either the median-ranked or second-largest
  object, and paint only that object's original cells/color onto a zero grid.
- Counts: 2–6 demonstrations and exactly four distinct queries.
- Inputs are deterministic and independent of the setting. Every retained
  demonstration contains five distinct-area blobs and distinguishes the two
  settings by its protected-Racket label.
- The query bank includes 8×8 lower-bound cases and a substantive 30×30 case
  with five objects of areas `[17, 31, 47, 63, 79]` and 237 nonzero cells.

The causal dependency is genuine: Step A produces the ranked object list and
selected rank index; Step B consumes that choice to decide which cells survive.
The retained `wrong_intermediate` witness substitutes the median index for a
`second_largest` episode and changes the protected-Racket output.

## Source files

- `adapter.py` — native `program(settings)` and
  `generate(seed, settings, demos, queries)` contract.
- `canonical.rkt` — exact selected canonical default.
- `promotion.json` — parameter grammar, default, count limits and resource list.
- `evidence/manifest.json` — current source/evidence inventory.

## Reproduce the reviewer checks

Run from the outer extracted packet directory:

```sh
python3 review.py task-tests 9c69eb63c11a --phase after \
  --out ../checks/9c69eb63c11a/task-tests

python3 review.py run python3 -m arcpuzzles parametric qualify 9c69eb63c11a \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/9c69eb63c11a/qualification --summary

python3 review.py run python3 -m arcpuzzles parametric qualify 9c69eb63c11a \
  --seed 0 --seed 17 --demos 6 --queries 4 \
  --out ../checks/9c69eb63c11a/qualification-max6 --summary

python3 review.py preview-public \
  --receipt checks/9c69eb63c11a/preview-export-command.json export \
  --qualification ../checks/9c69eb63c11a/qualification/qualification.json \
  --out ../checks/9c69eb63c11a/preview

python3 review.py preview-public \
  --receipt checks/9c69eb63c11a/preview-verify-command.json verify \
  --bundle ../checks/9c69eb63c11a/preview

python3 WORK/check_public_exports.py \
  WORK/checks/9c69eb63c11a/preview/public --queries 1 --summary

python3 review.py run python3 ../check_first_turn.py \
  --bundle ../checks/9c69eb63c11a/preview \
  --out ../checks/9c69eb63c11a/first-turn.json
```

The qualification receipts re-execute every claimed label through protected
Racket. The projection checks do not rerun Racket; they verify current source
binding, one-query public files, masked answers, and first-turn invariance under
private/future-query mutations.

## Reviewer evidence and limits

- Minimum-count qualification: 2 settings × 2 seeds, 2 demos + 4 queries,
  32 protected-Racket evaluations.
- Maximum-count qualification: 2 settings × 2 seeds, 6 demos + 4 queries,
  64 protected-Racket evaluations.
- Portable changed-target tests: 62/62 passed.
- Public projection: 4 private episodes → 16 one-query views; 24 first-turn
  invariance checks and 4 visible-change controls passed.
- Counterfactual witness: `checks/9c69eb63c11a/causal/witness.json`.

These are finite checks of the declared grammar and seeds. They do not prove
uniqueness against arbitrary algorithms, owner acceptance, learning benefit, or
training admission. The owner must run fresh qualification and acceptance on the
exact integrated sources.
