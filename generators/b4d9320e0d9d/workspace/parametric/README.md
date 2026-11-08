# Native parametric family: cascading diagonal completion

This family keeps the accepted canonical rule as the exact default and adds one
meaningful episode-fixed variant.

## Contract

- Parameter: `completion_rounds`
- Values: `one_pass`, `two_pass`
- Default: `one_pass`
- Demonstrations: 2–6
- Queries: 1–4; production qualification uses four distinct queries
- Seed domain: exact integers in `0..2**63-1`

`one_pass` is byte-for-byte the canonical program. It completes a 2×2 square
when one diagonal contains the same nonzero color and both opposite corners are
zero, reading only the original input. `two_pass` applies that transformation a
second time to the first pass's output, so newly written cells may trigger a
second completion.

## API

```python
from adapter import generate, program, public_turn

episode = generate(17, {"completion_rounds": "two_pass"}, demos=2, queries=4)
racket = program({"completion_rounds": "two_pass"})
visible = public_turn(episode, query_index=0)
```

Inputs are identical across settings for the same seed/counts. Query profiles
include 13×16, 19×21, 25×27, and a populated 30×30 stress case.

## Evidence and checks

- `evidence/manifest.json`: current exact-source inventory
- `evidence/current/report.json`: 16-seed bounded authoring audit
- `audit.py`: regenerates private/public audit evidence
- `tests/test_parameters.py`: contract, canonical preservation, rivals, stress,
  public projection, and seed-sweep regressions
- Packet-level native qualification and causal witness live under
  `WORK/checks/b4d9320e0d9d/` in a review workspace.

The causal dependency is first pass → intermediate grid → second pass. The
protected-Racket counterfactual replaces the two-pass program with the qualified
one-pass program on a cascade-sensitive qualified pair.

## Reproduce inside a review packet

Run these from the packet root (the directory containing `review.py`):

```bash
python3 review.py task-tests b4d9320e0d9d --phase after --out ../checks/b4d9320e0d9d-tests
python3 review.py run python3 generators/b4d9320e0d9d/workspace/parametric/audit.py \
  --out generators/b4d9320e0d9d/workspace/parametric/evidence/current --seeds 16
python3 review.py run python3 -m arcpuzzles parametric manifest --help
python3 review.py run python3 -m arcpuzzles parametric qualify b4d9320e0d9d \
  --out ../checks/b4d9320e0d9d/qualification --summary
```

The manifest command deliberately requires the exact evidence directory and an
author-written `--reported-checks` string. When replacing an existing manifest,
it also requires `--replace` with that file's current SHA-256; use `--help` rather
than silently carrying stale check claims forward.

Finite audits establish the declared settings/rivals and tested seeds only; they
do not prove universal identifiability or training gain. Reviewer readiness is
not owner acceptance and does not admit training data.
