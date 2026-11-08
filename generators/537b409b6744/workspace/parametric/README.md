# Candidate-rank parametric prototype

This task-local prototype leaves the selected production generator and canonical
rule unchanged. It varies one rule parameter once per episode:

- `candidate_rank = nearest` — canonical/default: move the qualifying object
  with the smallest gap through its wall.
- `candidate_rank = farthest` — proposed: move the qualifying object with the
  largest gap; equal gaps retain the canonical larger-wall tie-break.

The production sampler already emits a nearer mover and a farther qualifying
distractor against the same wall. Therefore each retained input distinguishes
the settings without changing input geometry, colors, component extraction, or
the move/cut/grow transformation after selection. Each episode contains three
demonstrations and four distinct queries under one fixed setting.

## Files

- `prototype.py` builds episodes, labels through the pinned Racket runtime,
  checks an independent Python geometry mirror, tests every retained pair as a
  possible query, and writes source-bound evidence.
- `rules/nearest.rkt` is byte-identical to the selected canonical program.
- `rules/farthest.rkt` is accepted only when it is the exact declared comparator
  reversal; both settings prefer the larger wall on equal gaps.
- `examples/` contains answer-masked public challenges. Filenames are SHA-256
  IDs of the exact visible bytes from `reviewer_support.public_challenge_bytes`;
  hidden parameters, seeds, programs, and query answers cannot affect them.

## Exact replay

From the outer extraction directory, use fresh output directories because the
writer validates before creating new output trees and intentionally refuses to overwrite evidence:

```bash
python3 review.py setup
python3 review.py run python3 \
  generators/537b409b6744/workspace/parametric/prototype.py \
  --out-dir ../checks/parametric/candidate-rank-replay \
  --public-dir ../checks/parametric/candidate-rank-replay-public \
  --seeds 0 1 --difficulty easy --start-index 0 --n-train 3 --n-test 4
python3 review.py run python3 -m pytest -q \
  generators/537b409b6744/tests
```

Retained evidence from the authored run is under
`checks/parametric/candidate-rank-final/`; the bounded tie/export adversarial
probe is under `checks/parametric/candidate-rank-adversarial/`.

This is evidence for a proposed task-local extension, not a production API,
canonical-rule change, generator approval, or training admission.
