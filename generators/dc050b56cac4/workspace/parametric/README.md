# Diagonal-direction rule prototype

This task-local prototype proposes one episode-level rule parameter while
preserving the original family:

| Parameter | Allowed values | Original/default |
| --- | --- | --- |
| `direction` | `down_left`, `down_right`, `up_left`, `up_right` | `down_left` |

The gray-cell count remains the movement distance. The input still contains one
full-row/full-column colored cross plus one to three off-cross gray markers. The
only changed rule choice is the pair of signs applied to the old cross center.
For `down_left`, `instantiate()` returns the canonical Racket text byte for byte.
The production generator, selected rule hash, and approval state are untouched.

`parameters(seed)` chooses one direction once per episode. Four inputs then use
the same setting: three labeled demonstrations and one masked query. Controlled
cross centers leave the marker-count margin on all four sides, so every rival
direction is executable on every input. Each retained episode distinguishes all
three alternative directions in its demonstrations before the query.

## Run from the outer packet directory

```sh
python3 review.py run python3 generators/dc050b56cac4/workspace/parametric/prototype.py \
  --out ../checks/parametric/direction-prototype
python3 review.py run python3 -m pytest -q \
  generators/dc050b56cac4/tests/test_parametric_direction.py
```

The first command uses the included Racket bridge for every label and rival. It
writes four complete private episodes, four public challenges with query answers
and hidden settings removed, exact `.rkt` programs and SHA-256 hashes, a common
input on which all four settings differ, canonical-default parity evidence, and
a member manifest. Python constructs fixtures and compares results but does not
supply episode labels.

Scope is deliberately bounded: four settings, four retained seeds, controlled
fixtures, three demonstrations and one query per episode. This is proposed
authoring evidence, not a production parametric API, exhaustive identifiability
proof, or approval of the noncanonical rules.
