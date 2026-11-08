# Global zero-group ranks: proposed parametric prototype

This task-local research prototype retains the original reasoning: find every
zero, collect globally shared groups, rank the distinct groups spatially,
replace each zero by its group's one-indexed rank, and preserve every nonzero
cell. It does not change `generate(...)`, the selected rule, or approval state.

| Parameter | Allowed values | Meaning |
|---|---|---|
| `grouping_axis` | `columns`, `rows` | Zeros share a group when their column or row coordinate agrees. |
| `direction` | `forward`, `reverse` | Rank groups from left to right / top to bottom, or in the opposite order. |

The original/default setting is **columns / forward**. Its emitted Racket is
byte-for-byte identical to the selected canonical program. Other settings alter
only the grouping coordinate and rank comparison. The derivation fails visibly
if the expected canonical source fragments change.

## Episode and input contract

`choose_parameters(seed)` chooses one of four settings exactly once, using a
stable seed namespace. One program supplies every demonstration and query label
in that episode. Four demonstrations and one query use distinct inputs.

The input sampler is independent of the hidden parameters. It draws the
selected generator's `canonical_sparse` and `scrambled_order` profiles with
explicit seed, sample index, medium difficulty and profile. Both the input and
its transpose must pass the selected canonical validator. This common subset
has 4–8 zero groups on either axis, so every parameter rival produces legal
ARC colors. The direction adds no input constraint. There is no resampling of
the hidden parameters inside the pair loop.

This prototype intentionally does not expose `wide_many` or `dense_mixed` as
episode profiles: their active rows can exceed nine, making a row-group rival
leave the ARC color alphabet. Separately, default-rule parity exercises every
selected canonical generator profile. There is no claim that the prototype
covers the canonical sampler's entire domain.

## Run from the outer extraction directory

Use new output paths to retain earlier attempts. The wrapper selects the
included offline Racket runtime and sets the payload working directory to
`WORK/repo/`.

```bash
python3 review.py run python3 generators/af840d59f24c/workspace/parametric/prototype.py build --seed 17 --out ../checks/parametric/example
python3 review.py run python3 generators/af840d59f24c/workspace/parametric/prototype.py verify --evidence ../checks/parametric/example --out ../checks/parametric/example-replay.json
python3 review.py run python3 -m pytest -q generators/af840d59f24c/tests/test_parametric.py
```

If the wrapper's Python lacks pytest, use a Python 3.12+ interpreter with pytest,
NumPy and Pillow for both the wrapper and its payload. The retained command
receipt records the actual interpreter used.

`build` deterministically searches at most 256 consecutive seeds, starting at
the requested seed, to find one episode for each setting. The chosen seed and
parameter values are private episode metadata. It compares every episode with
the other three exact Racket programs, retaining refuting demonstration indices
and all five query rotations. These are finite checks against the declared
parameter rivals, not a proof against arbitrary programs or all seeds.

All example outputs and rival predictions execute the materialized Racket
sources through the included `RacketBridge` and the shared `wrap_rule` pipeline
in a freshly prepared runtime. No Python output mirror supplies evidence.
`programs/` retains exact source text; `execution.json` retains both source and
wrapped callable hashes, input grids, outputs, runtime identity and worker
command. `default-parity.json` retains separate all-profile canonical controls.

`episodes.private.json` contains complete labeled episodes. Give solvers only
the opaque `public/challenge-NN.json` files: each contains demonstration input /
output pairs and query inputs, with no query answers, parameter metadata, seed
or reference code. Public files are numbered in chosen-seed order rather than
a fixed order of parameter settings. `contrast.json` retains a common lawful input whose four
outputs differ. `report.json` binds source hashes and counts, and `manifest.json`
binds all bundle files. `verify` checks those hashes, regenerates inputs and
parameters from seeds, checks public masking, and executes all saved programs
again. A source edit requires a new bundle, not a refreshed hash on old labels.

The focused tests in `tests/test_parametric.py` apply only to this prototype.
They separately check explicit small-grid rank expectations, canonical default
parity, complete seed-fixed episodes, rival discrimination, public masking,
determinism and replay rejection of changed files. Their success does not
approve the proposed rule variants or replace canonical repair verification.
