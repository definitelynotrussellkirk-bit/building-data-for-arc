# Proposed `scale_factor` rule parameter

**Status: proposed, unapproved task-local prototype.** The production generator,
canonical Racket authority, catalog approval, and training status are unchanged.

## Contract

`scale_factor` is chosen once per episode and remains fixed across every
labeled demonstration and query.

| Value | Rule | Role |
| ---: | --- | --- |
| `2` | replace each cell by a solid `2×2` block | canonical/default |
| `3` | replace each cell by a solid `3×3` block | proposed alternative |

The input grammar is independent of the hidden setting: distinct lawful
canonical-scale square grids (`2×2` through `5×5`) come from the selected
approved generator. The exact canonical source
`(rule! (lambda (g) (upscale g 2)))` is pinned by full SHA-256
`511f58f5d47190acd7307da0e87d1e6d84d787e18b14ce8c3c14de0471730050`.
The alternative changes only the guarded factor literal. Every retained output,
including rival predictions, is executed by the included Racket bridge; there
is no Python answer mirror.

Each default episode contains two demonstrations and four distinct queries.
The other factor is checked independently for every query and must already be
refuted by the demonstrations. Public files contain only demonstration
inputs/outputs and query inputs. Their `challenge-<sha256>.json` names hash the
exact visible bytes, so seeds, factors, Racket source, and query answers cannot
change a public identifier.

## Reproduce

From the outer extracted packet directory, use a new output directory:

```bash
python3 review.py setup
python3 review.py run python3 \
  generators/2dacb90452ce/workspace/parametric/prototype.py materialize \
  --seed 0 --demo-count 2 --query-count 4 \
  --out ../checks/parametric/2dacb90452ce-scale-factor-v1

python3 review.py run python3 \
  generators/2dacb90452ce/workspace/parametric/prototype.py verify \
  --out ../checks/parametric/2dacb90452ce-scale-factor-v1

python3 review.py run python3 -m pytest -q \
  generators/2dacb90452ce/tests/test_parametric_scale_factor.py
```

The materializer writes two complete episodes (one per factor), exact private
Racket programs, per-query rival analyses, a shared distinguishing witness,
canonical-pair receipts, public challenges, and a hash manifest. `verify`
replays file hashes, public projections and names, all private labels, all rival
analyses, the witness, and all four labeled canonical pairs.

## Limits

The retained evidence covers factors `{2, 3}` and two episode seeds. Rival
analysis is finite and addresses the declared alternative factor, not every
conceivable rule. Inputs remain bounded to side length five, so the largest
proposed output is `15×15`. This prototype is not a production parametric API,
does not refresh approval hashes, and does not admit any examples to training.
