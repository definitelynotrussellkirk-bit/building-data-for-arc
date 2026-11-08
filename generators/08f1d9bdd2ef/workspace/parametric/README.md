# Proposed `arm_rotation` extension for `08f1d9bdd2ef`

This task-local prototype is **proposed and unapproved**. It does not add a
production axis and does not replace the selected canonical Racket authority.
It keeps the same divider grammar and cross-zone reasoning while varying one
hidden episode-level rule parameter.

| Parameter | Values | Canonical/default |
|---|---|---|
| `arm_rotation` | `0`, `1`, `2`, `3` clockwise quarter-turns | `0` |

Read the four arm colors clockwise as top, right, bottom, left. Setting `0`
uses the canonical assignment `(2, 3, 1, 4)`. Each additional setting rotates
that assignment clockwise as a unit. Black corners, cyan dividers, and the
magenta center remain unchanged. One setting is selected once per episode and
is reused across all three demonstrations and the query. Any demonstration
refutes all three alternative settings because every arm zone has positive
area and the four arm colors are distinct.

From the outer packet extraction directory, run:

```bash
python3 review.py run python3 \
  generators/08f1d9bdd2ef/workspace/parametric/verify.py \
  --out ../checks/parametric/arm-rotation
```

From this directory, the equivalent local payload is:

```bash
python3 verify.py --out ../../../../checks/parametric/arm-rotation
```

The verifier materializes exact Racket for all four settings, executes the full
program-by-episode matrix in one reusable offline Racket session, compares every
result to the Python mirror, checks that demonstrations and query distinguish
all rivals, and writes both private evidence and public challenges with query
answers and hidden settings removed. Reusing one bridge avoids sixteen separate
Racket startups and makes the evidence command reliably bounded.

Limits: this is finite evidence for four color assignments, not proof for an
arbitrary color permutation. The input does not reveal the parameter directly;
identification comes only from labeled demonstrations. No production or
training approval is implied.

## Native promotion: area-ranked arm assignment

The production-facing finite adapter is `adapter.py` with settings
`arm_assignment=compass|area_ranked`. `compass` is the exact selected canonical
program. In `area_ranked`, step A finds the two divider rows/columns, computes
the top/right/bottom/left arm areas, and ranks the four directions. Step B
consumes that input-derived ranking and assigns colors `2,3,1,4` from largest
to smallest arm. Center/divider/corner behavior remains `6/8/0`.

The authored grammar guarantees four unique arm areas, never uses the canonical
compass order as the area order, supports 2–6 demonstrations and exactly four
private queries, and includes a substantive 30×30 query. The earlier
`arm_rotation.py` prototype is retained as prior evidence but is not the native
promotion contract.
