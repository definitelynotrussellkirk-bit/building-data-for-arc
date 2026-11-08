# Wall-keyed arrow motion — public_eval_88e364bc

This proposed family follows official parent `88e364bc`, including all three
training pairs and both provided test golds. Root `reference.rkt` is the
canonical default and exactly matches the declared sibling `canonical.rkt`.
The relocated rule ID is the literal `ee_88e364bc`. The native authoring
preflight grants no owner qualification or acceptance.

## Rule and parameter

A solid rectangular legend contains two parallel arrows, each with two
tail-colored cells and a red 2 head. Its uniform border color identifies the
wall color it controls. Decode each arrow geometrically, then discover the
four-connected regions of background 0 and yellow 4 tokens. Each token region
is enclosed by exactly one keyed wall color. The same legend can control
multiple disconnected containers; another wall's color can serve as an arrow
tail inside a legend.

| `motion` | Bound movement direction |
| --- | --- |
| `toward_head` (canonical default) | The unit vector from the two tail cells toward the head |
| `toward_tail` | The opposite unit vector |

Move each token along the bound direction until its next step is blocked.
Cardinal steps require a free destination. Diagonal steps also require both
forward orthogonal cells to be free, so a token cannot cut across a wall corner.
Remove the old tokens and paint their final positions simultaneously; preserve
all walls and legends. Existing contact with a side or rear wall does not by
itself prevent movement.

This corner rule matters in the supplied test: the gray token at `(3,11)` stops
at `(4,12)` even though the next diagonal cell `(5,13)` is empty, because
`(4,13)` is a wall. A destination-only diagonal rule gives a wrong original
answer. The independent review retains that failed hypothesis and its exact
counterexample.

Stage A decodes the wall-to-direction map and binds each discovered region's
cells and tokens to a direction. Stage B consumes those bindings to calculate
collision-limited endpoints. `first_stage` exposes only those bindings, before
any endpoint calculation. The causal experiment rotates the bound directions
while preserving the input, token starts, region cells and movement algorithm.

## Supported grammar and explicit limits

Inputs are exact-list rectangular grids with both dimensions 10–30 and exact
integer colors 0–9. Background 0, arrow head 2 and movable token 4 retain their
original semantic roles. There are one to three isolated eight-connected
nonzero legend components. Each is a completely filled rectangle with a
uniform wall-colored border, exactly two heads and four same-color tails, and
one unambiguous shared length-three direction. Wall colors are distinct across
legends and exclude 0, 2 and 4. Every nonlegend wall color has a legend, and
every legend controls at least one token-containing region.

Token-containing free components must not touch the grid edge, and each has
exactly one boundary wall color. Irregular contours, internal obstacles,
disconnected containers of the same wall color, narrow pockets and stationary
tokens are allowed. A token initially between wall cells is still part of the
free component. The declared domain excludes two tokens on the same motion
line within a component. The originals do not establish collision ordering,
and this exclusion makes simultaneous independent movement unambiguous under
both settings. Different components may use the same infinite motion line.

The sampler covers a finite subset of that grammar with one or two legends;
the three-legend bound is available to hand-authored lawful inputs. It generates
jagged outlines, internal wall protrusions, split containers, different wall
and tail colors, and all eight directions. The first core lesson exchanges
panel slots relative to containers; the second aligns them. Thus neither nearest
nor farthest legend position can replace the color key.
All transformations are geometric; original grids and gold labels are not
embedded in the implementation.

## Episodes and teaching

Settings are fixed across each complete episode. The supported request is
2–6 demos and 1–4 queries, with exact integer seeds in `0..2**63-1`. The first
two demos jointly cover horizontal, vertical and both diagonal axes, under a
common rotation. Their token placements distinguish local obstacles, corner
collisions, long movement, one-step movement and legal stationary cases.
Adjacent particles on distinct diagonal motion lines explicitly teach that
all original particle positions clear simultaneously. Each member of this
pair frees the other's side cell in one of the two settings, refuting the
otherwise plausible rule that original particles remain static obstacles.

Sampling is independent of the setting. The same seed produces matched inputs
and query order under both modes. Generate all four queries, shuffle that bank
privately, then take the requested prefix. Query and demo counts are independent
and prefix-stable; inputs are distinct within an episode. Calls own their row
storage and leave global random state unchanged. Booleans, extra setting keys,
unsupported counts and unknown root overrides are rejected. The root input-only
API accepts a difficulty hint without changing this grammar; `self_check`
returns a findings list, empty for a valid input.

Queries include a 14×14 single-controller scene and a substantive 30×30 scene
with multiple containers, many tokens and substantial walls. Finite named
rival checks support the selected minimum; they do not prove uniqueness among
all possible programs. The output of the Python mirror is checked against
protected Racket, not treated as an independent label authority.

After both teaching repairs, the independent audit finds no query-changing
demonstration-consistent survivor among 24 frozen rivals across 40 episodes.
All 240 independently interpreted labels and 80 count-prefix checks pass, with
53 protected original, hand, stress and generated label checks. The three-legend
and 10×10 limits are exercised by lawful explicit fixtures, while a 30×30
fixture checks 26 independent motion lines. The two earlier counterexamples
and their executed labels are retained alongside the final passing evidence.

## Resource closure and runnable commands

All adapter imports and declared resources stay in this directory.
`sampler.py` is byte-identical to the standalone root `generator.py`, enforced
by a focused regression. The copy preserves both the relocated input-only API
and native resource closure; update both copies together when changing code.

From the outer packet directory, using its prepared runtime:

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run --receipt checks/public_eval_88e364bc/tests-command.json python3 -m pytest --import-mode=importlib generators/public_eval_88e364bc/tests -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run --receipt checks/public_eval_88e364bc/preflight-command.json python3 -m arcpuzzles.review_public_creation preflight public_eval_88e364bc --root . --out ../checks/public_eval_88e364bc/preflight
```

The promotion contract requests two demos and four queries for each setting at
both native preflight seeds. To construct an explicit private four-query
episode, run this payload through `review.py run python3 -`:

```python
import importlib.util
import json
from pathlib import Path

path = Path("generators/public_eval_88e364bc/workspace/parametric/adapter.py")
spec = importlib.util.spec_from_file_location("wall_motion_adapter", path)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
episode = adapter.generate(17, {"motion": "toward_head"}, demos=2, queries=4)
print(json.dumps(episode))  # Private program and labels: controller use only.
```

Use `checks/public_creation_tools.py` after a successful native preflight for
the protected causal witness and one-query public exports. The complete bundle,
directory listing, mappings, programs, settings, seeds, gold labels and future
inputs stay private; a solver receives one chosen public file at a time.
Choose new evidence destinations after source changes. Owner source review,
registration, native qualification, acceptance and training admission remain
separate from this reviewer-ready proposal.
