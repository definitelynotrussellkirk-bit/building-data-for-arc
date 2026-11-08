# Native parametric family: anchored motif normalization

This family keeps the accepted canonical rule as the exact default and adds one
meaningful episode-fixed variant.

## Contract

- Parameter: `tile_anchor`
- Values: `bottom_right`, `top_left`
- Default: `bottom_right`
- Demonstrations: 2–6
- Queries: 1–4; production qualification uses four distinct queries
- Seed domain: exact integers in `0..2**63-1`

Both settings count color-4 cells, normalize the color-8 motif into a 3×3 tile,
and repeat that tile horizontally once per counter cell. The parameter chooses
whether a motif smaller than 3×3 is aligned to the tile's bottom-right or
top-left. `bottom_right` is byte-for-byte the canonical program.

## API

```python
from adapter import generate, program, public_turn

episode = generate(17, {"tile_anchor": "top_left"}, demos=2, queries=4)
racket = program({"tile_anchor": "top_left"})
visible = public_turn(episode, query_index=0)
```

Inputs are identical across settings for the same seed/counts. Query profiles
include a populated 30×30 input with ten counters and a 3×30 output.

## Evidence and checks

- `evidence/manifest.json`: current exact-source inventory
- `evidence/current/report.json`: 16-seed bounded authoring audit
- `audit.py`: regenerates private/public audit evidence
- `tests/test_parameters.py`: contract, canonical preservation, rivals, stress,
  public projection, and count/placement regressions
- Packet-level native qualification and causal witness live under
  `WORK/checks/87aae821984d/` in a review workspace.

The causal dependency is motif extraction → anchor-normalized 3×3 tile →
count-based repetition. The protected-Racket counterfactual substitutes the
qualified bottom-right program for a qualified top-left case, changing the
intermediate tile and final output.

## Reproduce inside a review packet

Run these from the packet root (the directory containing `review.py`):

```bash
python3 review.py task-tests 87aae821984d --phase after --out ../checks/87aae821984d-tests
python3 review.py run python3 generators/87aae821984d/workspace/parametric/audit.py \
  --out generators/87aae821984d/workspace/parametric/evidence/current --seeds 16
python3 review.py run python3 -m arcpuzzles parametric manifest --help
python3 review.py run python3 -m arcpuzzles parametric qualify 87aae821984d \
  --out ../checks/87aae821984d/qualification --summary
```

The manifest command deliberately requires the exact evidence directory and an
author-written `--reported-checks` string. When replacing an existing manifest,
it also requires `--replace` with that file's current SHA-256; use `--help` rather
than silently carrying stale check claims forward.

Finite audits establish the declared settings/rivals and tested seeds only; they
do not prove universal identifiability or training gain. Reviewer readiness is
not owner acceptance and does not admit training data.
