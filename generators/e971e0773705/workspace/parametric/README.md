# Opposite-pair T counting family

This task-local proposal adds `count_mode` to task `e971e0773705`. The default
`raw` setting returns the exact Catalog canonical Racket source in
`canonical.rkt`. The alternative `cancel_opposites` setting performs an
input-dependent intermediate operation before the existing emblem is drawn.
Production `generator.py`, the Catalog rule, and its original calibrated scene
validator are unchanged.

## Rule and admitted scenes

Each input is a rectangular integer grid with black background (`0`) and red
(`2`) four-connected components. Every component must be exactly one of the
two vertical T tetrominoes: three cells across its top row plus a centered stem,
or a centered stem above three cells across its bottom row. Diagonal contact is
allowed; edge contact between distinct components is not. The proposal admits
dimensions from 1 through 30 on each axis, subject to fitting at least one
complete T, and 1 through 70 components. This separate grammar extends the
production validator's height 5..22, width 4..22, and 1..10-component limits.

Let `a` count top-bar Ts and `b` count bottom-bar Ts. Under `raw`, retain `(a,b)`.
Under `cancel_opposites`, derive `m=min(a,b)` and retain `(a-m,b-m)`. Then cap
each retained count at four. Render bottom-bar counts in green (`3`) at
`(0,0),(2,0),(0,2),(2,2)` and top-bar counts in blue (`1`) at
`(0,3),(2,3),(0,5),(2,5)`, in those orders, on a black 3×6 output.

The order is observable. Counts `(8,3)` become `(5,0)` and display four blue
cells. Capping first gives `(4,3)`, then `(1,0)`, displaying one blue cell.
Cancellation is derived from the current input, not from a seed or an episode
constant. The example is a count-dependent composition; it does not claim an
iterative physical simulation.

## Why five demonstrations

The supported demonstration range is **5..6**, with five as the adapter and
qualification default. Queries range from 1..4, with four as the default. The
first five inputs have these roles, with profiles and winner order varying by
seed:

1. One orientation wins by at least four.
2. The opposite orientation wins by at least four.
3. One orientation wins by one, two, or three.
4. The opposite orientation wins by one, two, or three.
5. Positive equal counts cancel to an empty emblem.

The minimum follows demonstrated teaching gaps. A prior lesson admitted a
green-only cap-three hypothesis. After adding both saturated winners, the
supported four-demo seed-17 lesson still admitted a blue-only hypothesis that
always displayed four cells whenever blue won. Its query with counts `(10,8)`
required two blue cells. Protected Racket replay and the complete four-demo
source snapshot are retained under `checks/e971e0773705/` in
`asymmetric-majority-before/` and `asymmetric-majority-before-source/`.
The two per-color regression tests now require evidence against both mistakes.
Unsupported shorter prefixes remain useful audit witnesses; they are not
declared training episodes.

## Sampling and teaching coverage

Every request builds the same complete six-demo/four-query input bank for its
seed before taking any prefix. Both settings use identical inputs and ordering.
Changing demonstration or query counts therefore preserves existing prefixes.
Queries are distinct from every demonstration and from each other.

The first five scenes include a pair of bottom-bar Ts whose origins differ by
`(2,2)`: they touch diagonally but remain separate four-connected components.
The cluster moves among corners. Bounded constructive selection checks that
the five inputs jointly distinguish four- from eight-connectivity, ignoring
boundary components, reading only the upper or left half, and counting at most
one component of each orientation per anchor row. This Python construction
screen is separate from the independent protected Racket rival audit.

Placement and teaching selection have explicit 128-attempt limits. Every
returned grid is validated against the exact-T grammar. The large query uses
54 Ts, or 216 red cells, on a 30×30 canvas. It samples 54 of 70 separated slots,
includes all corner slots, randomizes orientations and positions, and spreads
positive gaps across the canvas. Active cells reach all four boundaries.
Dense query profiles include both winners, multiple residual magnitudes, and a
tie. This exercises the enlarged scene grammar directly.

Seed zero pins a literal 2×3 single-T boundary query. Other seeds use varied
small count profiles and 6..9 by 8..11 shapes for the first query. The remaining
queries are 12×16, 20×24, and 30×30. The bounded sampler report records actual
unique grids, labeled pairs, count profiles, dimensions, and retry costs; it
labels these checks as Python-only.

## API and trust boundary

`adapter.py` exposes `program(settings)` and
`generate(seed, settings, demos=5, queries=4)`. Settings must be exactly
`{"count_mode": "raw"}` or `{"count_mode": "cancel_opposites"}`. Seeds must be
literal integers in `0..2**63-1`; booleans and unsupported counts are rejected.
Returned outputs are deterministic Python claims until independently executed
by the native protected Racket worker.

`prototype.py` also exposes `validate_grid`, `counts(grid, connectivity=4)`
returning `(top,bottom)`, `residual_counts`, `emblem`, and `solve`.
`rule_program(mode, cap=4, cap_before_cancel=False, connectivity=4)` constructs
complete executable counterfactual rules for replay. `program` alone owns the
exact canonical default. The emitted source is checked with the native rule
wrapper and protected Racket in focused boundary tests.

`audit_native.py` independently executes declared settings and a finite rival
set. `make_examples.py` executes native reference labels before calling
`export.py`. Public tasks and independent query turns contain only visible
demonstrations and the current query input. Settings, programs, source hashes,
certificates, and query answers remain in private artifacts. Successful local
tests and qualification do not grant owner acceptance or training admission.

## Reproduction

From the outer packet directory, run focused tests through the packet wrapper:

```sh
WORK/.venv/bin/python review.py run --receipt checks/e971e0773705/family-tests-command.json python3 -m pytest generators/e971e0773705/tests/test_parametric_e971e0773705.py -q
WORK/.venv/bin/python review.py run --receipt checks/e971e0773705/audit-final-command.json python3 generators/e971e0773705/workspace/parametric/audit_native.py --out ../checks/e971e0773705/audit-final
WORK/.venv/bin/python review.py run --receipt checks/e971e0773705/examples-command.json python3 generators/e971e0773705/workspace/parametric/make_examples.py --out ../checks/e971e0773705/examples --seed 0 --demos 5 --queries 4
```

The audit and exporter require fresh destination paths. After creating the
native source inventory with the retained checks, qualification must use the
declared minimum explicitly:

```sh
WORK/.venv/bin/python review.py run --receipt checks/e971e0773705/qualification-command.json python3 -m arcpuzzles parametric qualify e971e0773705 --seed 0 --seed 17 --seed 101 --demos 5 --queries 4 --out ../checks/e971e0773705/qualification --summary
```

Final source-bound reports provide the tested seeds, runtime identity, exact
source hashes, surviving hypotheses, and any limitations. The proposal remains
owner-pending unless the owner performs native acceptance.
