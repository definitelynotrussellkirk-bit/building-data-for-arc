# Semantic review: 0a7f0faace31

## Authority and canonical population

The selected canonical rule uses same-color **4-connected components**, discovered
by the row-major position of their first occupied cell. It excludes colors 5 and
7; touching different colors remain distinct objects. The guide is the inclusive
bbox of **all** seven cells, irrespective of connectedness or frame style. Each
component's center is independently `floor((minimum+maximum)/2)` in each axis,
not its mass centroid or its real-valued bbox midpoint. The first eligible
component is selected. `crop-object` returns its raw bbox subgrid, retaining any
background, other-color, or seven cells inside that rectangle.

All usable canonical pairs (one variant) were read through reviewer_support:

| Split/index | Input | Palette | Guide bbox | Selected color/output |
|---|---|---|---|---|
| train/0 | 17x18 | 1,2,3,4,5,7,8 | (7,1)-(16,7) | 4; 3x3 ring |
| train/1 | 17x16 | 1,2,3,5,6,7,8 | (8,8)-(16,15) | 1; 3x3 ring |
| test/0 | 13x14 | 1,2,5,6,7,8 | (0,8)-(4,13) | 2; 3x3 ring |

The train boards have five glyph components each; the test board has four. Every
glyph is an eight-cell hollow 3x3 ring. Only one eligible component exists on
each canonical board. Therefore canonical records do not distinguish all the
general component/selection/cropping semantics described above.

## Baseline defects and risks

* The baseline's five-cell `diagonal` pattern consists of five singleton
  components under the actual 4-connected rule. Selecting this pattern can
  produce a 1x1 scalar, despite `_selected_glyph` requiring that the *whole
  pattern* not fill its bbox. `self_check` intentionally accepts tiny solids,
  so this is not rejected. This is a mismatch between generator intent and
  actual selected component, rather than a demonstrated Python/Racket mismatch.
* Distinct colors per board and separation of every glyph forbid repeated
  disconnected color components, foreign cells within a crop, and diagonal
  contacts. Those restrictions permit canonical-fitting shortcuts to survive.
* Random independent textures do not guarantee that a complete lesson refutes
  the containment, overlap, scan-order, or rounding alternatives.
* The frame-style override is ignored on `sticks_out` and `center_out`: those
  branches choose only corners/two-corners without consulting the override.
* Exact canonical input dimensions include 13x14,17x16,17x18; restricting bands
  to default 13..15 or 17..19 ranges prevents all-band canonical-profile support.

## Measured rival fits and supported witnesses

`semantic_probe.py` found that every one of thirteen plausible alternatives
matches **3/3** usable canonical pairs: `fully_contained`, `any_overlap`,
`real_center`, `ceil_center`, `strict_center`, `eight_connected`,
`one_object_per_color`, `object_mask`, `last_eligible`, `largest_eligible`,
`smallest_eligible`, `nearest_guide_center`, and `always_hollow_ring`.

Ten small individual witnesses are retained in `checks/semantic/input.json`.
The first supported apply call matched the independent authority mirror on
**10/10** outputs. Eleven witnesses, including the compound below, are retained
in `checks/semantic/compound_input.json`; its supported apply call matched
**11/11** outputs. These are 11 unique inputs, because the second set contains
all ten from the first; they must not be reported as 21 unique inputs.
Racket records retain executed rule hash `b5a68207c8ed`, full rule text hash
`a4d1963101f3b83ab360fcce7e64bf54005fb62030bccf855a2939a509ef64ea`, and baseline
generator hash `05815ee53c53583c200395ac04b8886f970434b40ca49aff883aaa5c6dc96206`.

The compact compound refutes **13/13** of these alternatives in a single board:

* 12x14 background5, guide corner marks at (3,3),(3,10),(10,3),(10,10).
* Color1 exterior 3x3 ring at (0,0), and isolated color1 singleton at (3,13).
* Earlier overlapping color3 3x3 ring at (1,5), whose center (2,6) is outside.
* Selected color1 3x4 hollow rectangle at (4,9). Its floored center is (5,10),
  on the guide edge; its real center column10.5 and ceil center column11 lie
  outside. It protrudes right. Singleton (3,13) is only diagonally connected to
  it, so eight-connectivity merges them and changes the eligible bbox.
* Foreign color4 singleton at (5,10), in the selected rectangle's hole.
* Later eligible color2 4x4 ring at (7,5), with twelve cells versus selected10.

Actual Racket output is `[[1,1,1,1],[1,4,5,1],[1,1,1,1]]`. The exterior duplicate
color refutes color union; the foreign singleton refutes object masking and
smallest eligible; later larger/nearer ring refutes largest/last/nearest;
boundary placement refutes strict/real/ceil/fully contained; early overlapping
outside ring refutes overlap; output dimensions refute fixed ring synthesis.

All eleven inputs passed the baseline `self_check` (**11/11**, exact source hash
above; recorded as `validator_check` in `compound_probe.json`), but several fall
outside its *documented generated distribution*.
They are authored semantic-domain probes, not claimed generated samples. A
repair that adds these cases should document the domain expansion explicitly.

## Proposed distribution and lesson schedule

Use a deterministic three-phase schedule `[compound, compound, ordinary]`
with arbitrary non-5/7 palette permutations and safe translations. Every
three-pair cyclic window includes two compounds; every four-pair cyclic window
includes at least two. Holding out any one pair leaves at least one compound
among demonstrations. Ordinary slots preserve canonical ring configurations,
diverse connected non-solid shapes, full/dashed/corner/two-corner marks, and
canonical profiles in each difficulty band. Verify accepted indices as well as
requested starts, since rejection sampling can otherwise destroy the schedule.

Blind geometric transforms are unsafe: reflection changes floor-center
rounding at even extents, and rotation/transpose changes row-major object
priority. Treat them as candidate constructions requiring semantic validation.
Do not narrow the rule to only 3x3 hollow rings: that would keep canonical
outputs but leave crop shape and component semantics unteachable.

## Replay commands

From packet root:

```
PYTHONPATH=repo/shared/runtime python3 repo/generators/0a7f0faace31/workspace/semantic_probe.py compound_
python3 run_with_racket.py python3 -m arcpuzzles apply 0a7f0faace31 --input ../checks/semantic/compound_input.json --out ../checks/semantic/compound_racket.json
PYTHONPATH=repo/shared/runtime python3 repo/generators/0a7f0faace31/workspace/semantic_probe.py compound_
```

The supported apply output refuses to overwrite an existing path. For a fresh
replay use a different prefix throughout or copy the saved input to a fresh
evidence location. The script does not execute Racket or import private runner
functions; it scores and records supported-CLI outputs if present.
