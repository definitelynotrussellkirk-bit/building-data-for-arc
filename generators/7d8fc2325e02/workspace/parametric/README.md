# Episode-level Boolean-mode prototype

This isolated prototype keeps the original separated-panel structure and varies
one meaningful rule parameter once per episode:

| Parameter | Allowed value | Meaning |
|---|---|---|
| `boolean_mode` | `or` (canonical default) | Output green where either aligned panel cell is occupied. |
| `boolean_mode` | `xor` | Output green only where exactly one aligned panel cell is occupied. |

The canonical `or` setting returns the selected `program_solution` text exactly.
The `xor` setting changes only the aligned occupancy predicate. Input dimensions,
panel roles, separator, output color, and alignment reasoning remain invariant.
The production generator, canonical ledger, rule hash, and public generator API
are not changed by this proposal.

Every generated input already contains empty, top-only, bottom-only, and overlap
cells. Therefore each of the three demonstrations and the query distinguishes OR
from XOR: overlap cells are green under OR and black under XOR. The hidden mode is
selected once from a deterministic seed domain and is reused for the complete
episode. Public challenge JSON exposes demonstration labels and query inputs only;
private files retain the selected setting, exact Racket program, query answer,
alternative-setting predictions, source hashes, and replay seed.

From the outer packet directory:

```bash
python3 review.py run python3 generators/7d8fc2325e02/workspace/parametric/boolean_mode.py \
  --seed-start 31 --out ../checks/parametric/boolean-mode-v1
python3 review.py run python3 -m pytest -q \
  generators/7d8fc2325e02/tests/test_parametric_boolean_mode.py
```

Use a new output path for each evidence run; the tool refuses to overwrite. All
labels are produced by executing the exact materialized Racket program through
the public `RacketBridge`, then checked against an independent Python oracle. The
retained report also executes the canonical OR program on all five labeled
canonical pairs.

This is a proposed, bounded prototype. Two settings and two deterministic
episodes do not prove universal identifiability, solver benefit, or training
admission. The input sampler deliberately uses the selected generator's strict
truth-table grammar; episodes lacking overlap would not distinguish OR from XOR
and are rejected rather than exported.
