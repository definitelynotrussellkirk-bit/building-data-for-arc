# Edge cuts and corner placement — public_eval_4a21e3da

This proposed family follows official parent `4a21e3da`. The default program is
the exact root `reference.rkt`, copied byte-for-byte to `canonical.rkt`. The
root generator declares the relocated rule ID `ee_4a21e3da`. Neither an
authoring preflight nor this source inventory grants owner acceptance.

The adapter loads only sibling files in this folder. `sampler.py` is a declared
resource and an exact copy of the self-contained root `generator.py`; the
focused tests enforce byte identity to prevent drift between the two entry
points. Root generation remains independently relocatable.

## Rule and parameter

Read the background from the four equal corners. One or two same-color edge
markers define inward cut axes. Extend each marker ray only as far as the
farthest foreground cell on that same axis. Foreground on either cut axis stays
in its original position and takes precedence over the painted ray.

Partition the remaining foreground by the axes. A single marker yields two
half-planes; two orthogonal markers yield four quadrants. Each nonempty region
has one bounding box, including all its disconnected cells. Select its target
corner, then translate the entire region flush to that corner. Remove all
off-axis foreground from its original positions, including unselected regions.

| `selection` | Retained corners |
| --- | --- |
| `union` (canonical default) | Corners touching at least one marked edge |
| `intersection` | Corners touching every marked edge |

One-marker scenes agree under both settings. With two markers, `union` keeps
three regions and `intersection` keeps the jointly incident corner. Settings
are fixed for a complete episode; the same seed gives matched inputs and query
order under both settings.

Stage A determines the cuts and each selected region's cells and local bounds.
Stage B uses those bounds to calculate the corner translation. The retained
causal experiment replaces the local bounds with the whole foreground bounds
while keeping the cells and corner assignments: this changes the final grid.

## Exact supported boundary

Inputs are rectangular exact-list grids of exact integer colors 0–9, with both
dimensions 5–30. All corners contain the background. There are one or two
same-color noncorner edge markers, at most one top/bottom marker and at most
one left/right marker. A third color forms a nonempty foreground mask strictly
inside the border. Each marked axis intersects that mask. Empty off-axis
regions and scenes with all foreground on the cut axes are allowed.

Renamed colors, arbitrary disconnected masks, horizontal-only cuts, and dense
or extreme-aspect-ratio canvases are explicit generalizations. The original
examples alone do not establish all these cases. Background is determined by
the corners and can be less frequent than foreground; color zero has no special
role. The sampler explores a finite profile grammar within this larger lawful
input domain, and does not claim uniform or exhaustive coverage.

Seeds and root sample indices are exact integers in `0..2**63-1`. The native
adapter accepts exactly `{"selection": "union"}` or
`{"selection": "intersection"}`, 3–6 demos and 1–4 queries. Booleans, extra
settings, unsupported counts and unknown root overrides are rejected. The root
API returns an input grid; its `self_check` returns a findings list, empty on a
lawful input. `difficulty` is an accepted hint without changing this grammar.

## Teaching and sampling

The first three demos cover a rich two-axis cut, a single vertical cut and a
single horizontal cut, under a common rotation. They show disconnected region
placement, singleton regions, gaps between axis hits, and off-axis extrema that
must not extend the rays. Additional demos add scene diversity. The four-query
bank includes a 5×5 input, one of each single-axis orientation and a substantive
30×30 dense input. The entire bank is shuffled before applying the requested
query prefix. All inputs in an episode are distinct; increasing either count
preserves the corresponding prefix. Calls own their row storage and do not
change the process-global random state.

The independent audit checks plausible rival rules using only the visible
demonstrations before inspecting their query disagreements. These finite checks
support the declared lesson design; they do not prove uniqueness among all
possible programs. Original test gold, programs, parameter choices, source
indices, seeds and future query inputs stay in author/controller evidence.

The retained minimum-count diagnostic tests all two-demo subsets of the core
lesson at seeds 17 and 43 under both settings: all 24 subsets leave a plausible
query-changing rival. With all three demos, 44 independently audited episodes
refute all 17 frozen rivals. Thus the contract supports three demos, rather than
silently accepting an underidentified two-demo prefix.

## Run and review

From the outer packet directory, using this packet's prepared runtime:

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run --receipt checks/public_eval_4a21e3da/tests-command.json python3 -m pytest --import-mode=importlib generators/public_eval_4a21e3da/tests -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run --receipt checks/public_eval_4a21e3da/preflight-command.json python3 -m arcpuzzles.review_public_creation preflight public_eval_4a21e3da --root . --out ../checks/public_eval_4a21e3da/preflight
```

The promotion contract requests three demos and four queries for every setting
at both native preflight seeds. For an explicit private four-query episode,
the following payload can be run through `review.py run python3 -`:

```python
import importlib.util
import json
from pathlib import Path

path = Path("generators/public_eval_4a21e3da/workspace/parametric/adapter.py")
spec = importlib.util.spec_from_file_location("edge_cut_adapter", path)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
episode = adapter.generate(17, {"selection": "union"}, demos=3, queries=4)
print(json.dumps(episode))  # Private labels and program: controller use only.
```

`checks/public_creation_tools.py` builds a protected causal witness and exports
one-query public views directly from the unapproved native preflight. Its usage
and limitations are in `checks/PUBLIC_CREATION_TOOLS.md`. Choose fresh evidence
destinations after any source change. Owner registration, source review, native
qualification, acceptance and any training admission remain separate steps.
