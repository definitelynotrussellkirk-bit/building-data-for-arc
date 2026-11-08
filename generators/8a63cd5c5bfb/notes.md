# Working notes: 8a63cd5c5bfb

## Current parametric design

Keep the approved canonical generator and exact cyan-outline Racket program unchanged.
The separate native adapter adds `color_source=largest_interior`: infer the rectangle
from its two green markers, mask to its strict interior, find same-color 4-connected
components, and paint only empty border cells using the unique largest component's
color. This is an input-derived spatial selection dependency, not iterative simulation.
The admitted sampler has a unique largest interior component; ties and empty interiors
are outside its grammar. Larger outside objects and repeated disconnected interior
colors are deliberate distractors. All original occupied cells remain intact.

Implementation plan (packet-local; no shared or owner-acceptance edits):

- [x] Add focused hand-checked semantic and request-boundary tests, then the native
  adapter, exact canonical resource, alternative Racket resource and promotion contract.
- [x] Construct matched inputs across settings, 2–6 demonstrations and 1–4 queries;
  use distinct input streams so the first query and demos do not depend on query count.
  Default four-query schedules reach 30×30 with scaled objects and long borders.
- [x] Check protected Racket parity, finite wrong-rule rivals using demos only,
  strict single-query public projection and minimum/maximum shapes; retain compact evidence.
- [x] Freeze the native source inventory, qualify both settings, and build a
  protected-Racket counterfactual witness. Owner acceptance remains pending.

Main review focus: selecting a globally largest outside object; adding disconnected
same-color areas; overwriting existing border cells; query-count-dependent first turns;
and ties, booleans, or impossible count/size requests silently accepted.


## Current bounded evidence and handoff

The native adapter and both rule settings are ready for owner acceptance. Native
qualification (`checks/8a63cd5c5bfb/qualification/qualification.json`, sibling
`execution.json`) passed both settings on seeds 0/17 with three demonstrations and
four queries. No canonical generator, canonical authority, approval, or training
allocation was changed; owner qualification/acceptance on integrated live bytes is
still required.

The focused suite has 18 passing tests. The retained reusable `verify.py` audit
passed 16 episodes: both settings, seeds 0/17, demonstration counts 2/3/6 and four
queries, plus exact 12×12, 12×30, 30×12 and 30×30 boundaries. It made 512 distinct
protected-Racket program/input evaluations. All 23 declared executable rivals were
checked on demonstrations; only equivalent programs survived, and none disagreed
on a query. This is finite evidence, not universal uniqueness or measured training
benefit. `checks/8a63cd5c5bfb/precheck-v1/` retains the private episodes, per-rival
witness indices and hash-named public projections. All 32 saved public files passed
count/type/identity checks (16 one-query turns, 16 four-query controller payloads).
The first turn is identical for one versus four queries and invariant to poisoned
private metadata, query answers and future query inputs.

Self-review found real holes in the first constructor: demonstrations excluded
cyan winners and shared an exterior-normalized winning corner. The retained
protected-Racket example `checks/8a63cd5c5bfb/teaching-gap-before.json` records the
original cyan-exclusion failure. Construction now teaches a cyan winner, varies
normalized position, changes the aggregate-color rank, uses diagonal contacts that
separate 4/8-connectivity, and includes a clipped boundary-crossing distractor.
Regression tests and the final finite rival audit cover these repairs without
increasing the two-demonstration minimum.

`checks/8a63cd5c5bfb/causal/witness.json` and `causal/replay.json` bind two actual
qualified pairs to protected-Racket counterfactual execution: selecting full
components before clipping and ignoring rectangle scope both change final output.
One witness is a substantive 30×30 query. The actual intermediate component is
recorded with its cells, size and color; the causal interpretation remains an
explicit reviewer argument. This is contextual selection, not iterative simulation.

Support limits: unique largest clipped interior component; 12–30 cells per side
in the separate parametric sampler; four principal slot-grown components plus a
clipped outside fragment; no arbitrary tied/empty interior lessons. The exact-size
keywords are authoring controls only. Canonical production has no new height/width
override; native alternate export, after acceptance, uses its documented schedule
including a 30×30 fourth query. Queries are revealed one at a time by the existing
consumer; all-four masked payloads are controller storage only.
