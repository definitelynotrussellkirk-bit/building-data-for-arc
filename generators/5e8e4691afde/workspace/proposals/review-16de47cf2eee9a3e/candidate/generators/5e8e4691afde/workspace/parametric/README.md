# Proposed `diagonal_mode` parameter

This task-local prototype preserves the canonical framed-center and path-vector
reasoning.  One rule choice is fixed for the complete episode:

- `both` — canonical/default: draw both complete diagonals through the relocated
  frame center;
- `falling` — draw only the `\` diagonal;
- `rising` — draw only the `/` diagonal.

The input generator, indicator-to-endpoint vector, relocated 3x3 frame, canvas
fill, and preserved colored center do not change.  The default Racket text is
byte-for-byte the canonical program.  The alternatives replace only the unique
diagonal predicate.  This is a bounded **prototype**, not a production axis,
canonical rule change, approval, or training-admission claim.

Each retained setting has two labeled demonstrations and **four distinct query
inputs**.  Every selected label and both declared-rival predictions are executed
through `RacketBridge`.  Demonstrations alone refute both rivals before any query
answer is considered, and every query changes under both rivals.

From the outer packet directory:

```bash
python3 review.py run python3 generators/5e8e4691afde/workspace/parametric/prototype.py \
  --seed 20261023 --demo-count 2 --query-count 4 \
  --out ../checks/parametric/5e8e4691afde-diagonal-mode-v1
```

Public files contain exactly the visible demonstration pairs and query inputs.
Their filenames are SHA-256 hashes of those exact bytes via
`reviewer_support.public_challenge_bytes`; hidden settings, seeds, programs,
rival predictions, and query answers are private.  Batch writes are sorted by
public ID and duplicate visible payloads are rejected.
