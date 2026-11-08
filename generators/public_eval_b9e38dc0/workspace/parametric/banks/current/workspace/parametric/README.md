# Stepped nozzle continuation and parallel obstacle shadows

This is an unapproved native family for public parent `b9e38dc0`. Root
`reference.rkt` and adjacent `canonical.rkt` are byte-identical general rules.
The adapter reads the adjacent resource. The selected generator declares literal
`RULE_TASK_ID = 'ee_b9e38dc0'`; the task home remains `public_eval_b9e38dc0`.
Implementation does not read original examples or answer tables.

## Rule and admitted geometry

Infer the unique modal background and uniquely next-most-frequent wall color.
The wall is one eight-connected component with exactly two degree-one endpoints.
Sum their outward unit tangents; the uniquely dominant axis determines cardinal
flow. Rotate that flow downward for computation and restore the original frame
after rendering.

Each terminal side repeats a staircase: one lateral step per complete forward
run. Its final run and preceding inward run must have equal lengths, and both
sides share that stride. Extend each side past its own endpoint, preserving the
staircase phase. Unequal endpoint stations and a side clipped at the canvas are
supported. Partial final runs are explicitly outside this grammar.

The rear cap is a contiguous run of at least three wall cells. Each subsequent
pre-tip row has its left and right contiguous wall runs; after an endpoint, its
virtual continuation supplies that side. The intervals between these walls must
remain nonempty and four-connected. Bent and asymmetric reservoirs, horizontal
collars, boundary clipping and repeated forward run lengths are supported.

Among foreign colors inside this geometry, the earliest forward marker row must
contain exactly one color: the dye. This is an explicit source-selection grammar.
Other interior colored cells are obstacles. Foreign cells outside the band,
including behind the cap or before a widening band reaches their column, are
irrelevant to shadow casting. Preserve every original non-background cell.

## Parameter and sequential dependency

`obstacle_mode` is fixed for an episode:

- `opaque` is canonical: each reached obstacle blocks its parallel forward ray.
- `transparent` preserves obstacle pixels while filling background behind them.

First infer direction, staircase geometry, dye and eligible obstacle positions.
Then derive the nearest blocking row in each normalized column. The renderer
consumes these input-derived frontiers to decide which background cells receive
dye. A counterfactual can replace only the frontier vector while retaining the
input, opaque setting, band, dye and entire downstream renderer.

## Request contract and evidence

Grids are exact integer ARC rectangles with axes 1..30 and colors 0..9. Python
validates this grammar; Racket operates on lawful inputs. Palette roles may all
vary, including color zero. Required teaching demonstrations have different
background, wall and dye colors, preventing a constant role color from fitting
the smallest lesson. Their flow directions also differ by construction, preventing
a rule restricted to the first observed direction from fitting both. The second
rotation is drawn directly from the other three choices, without retries; the
independent query bank is unchanged by this coverage constraint.
Native generation supports 2..6 demonstrations and 1..4
queries, with ordinary defaults of three/four. Qualification/preflight uses two.
Seeds are exact integers in 0..2**63-1. Geometry, settings, demo augmentation and
query presentation are deterministic; the complete query bank is shuffled before
prefix selection. Construction and label code have no retry fallback.

The constructor has ten geometry profiles with seeded cap positions, lateral
shifts, reservoir bends, throat dwell and dye size/position. The six demos and
four queries include strides 1, 2 and 3. Both initial demos combine a pre-mouth
blocker larger than the dye patch, another blocker color beyond the mouth,
unblocked rays, a larger behind-cap distractor and a side distractor whose column
enters the widening band later. The second demo has clipped, unequal tip stations.
Distinct 30x30 demo/query profiles contain long walls and hundreds of interior
cells. This is a finite constructive profile family, not exhaustive arbitrary
nozzle geometry; the supported grammar is broader than its sampled bank.

Current sampler profiles and finite verification outcomes are recorded in root
`notes.md`, packet `RESULTS.json`, and task `checks/` evidence. Authoring preflight
is separate from owner registration, source review, native qualification and
acceptance. This build changes no shared runtime, approval, catalog or training
state.
