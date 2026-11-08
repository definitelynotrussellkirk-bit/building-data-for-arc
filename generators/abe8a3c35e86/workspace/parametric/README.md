# One or two pivot-reflection passes

This task-local native prototype keeps `passes=1` byte-for-byte equal to the
approved canonical program (`eb5d6fb489a0`). `passes=2` executes that exact body,
stores its resulting grid, and executes the same body with the stored grid as
its input. Production generation and its approval are unchanged. Qualification
is reviewer evidence; exact integrated-source acceptance is an owner action.

## Rule and grammar

The grammar is every rectangular built-in list of built-in lists with each
axis in1..30, exact integer colors0..9, and exactly one color9 pivot. It includes
all original examples, thin grids, a pivot alone, disconnected and multicolor
motifs, a neither-side identity branch, and copies that partly or wholly leave
the canvas. Each pass treats **all** non0/non9 cells jointly. If they are wholly
left or right of the pivot, copy them across its column; otherwise, if wholly
above or below, copy across its row. Preserve source pixels and ignore each
out-of-bounds copy. With no motif or neither side predicate, return unchanged.

In the two-pass setting, copied pixels can change which side predicate holds.
A successful quadrant column copy makes the actual intermediate straddle that
column; the next pass can then choose the row branch. If every column copy
clips, the intermediate does not change, so the next pass must select the column
again. The latter distinguishes actual state-dependent execution from applying
fourfold symmetry or forcing a second axis. This is a finite explicit dependency,
not a claim that every input needs two productive actions.

`program(settings)` requires exactly `{"passes":1}` or `{"passes":2}`.
`generate(seed, settings=None, demos=4, queries=4)` accepts exact integer
seeds0..2**63-1, demos4..6, and queries1..4. Omitted settings are seeded once
per episode, independently of input sampling. `reflect(grid)` is one pass;
`axis(grid)` reads the supplied state; `solve(grid, passes)` returns fresh lists.

## Constructive teaching and size support

The full bank is sampled before taking either count prefix. Four core
demonstrations cover a partially clipped quadrant, a fully column-clipped
quadrant with legal row copies, a multicolor row-only case, and an asymmetric
neither-side identity case. Horizontal/vertical flips and colors vary by seed.
The absent near-boundary cell in the first core exposes a clamp-to-edge rival.

Four is the supported minimum. The first three do not refute an unconditional
else-row fallback: on a column-only query, its second pass can add a wrong row
copy after the correct rule has reached neither-side geometry. The fourth
demonstration refutes that shortcut before any query output is used. The audit
retains the smaller-context counterexample and repaired context separately.
This is a measured finite-rival teaching limit, not a universal lower bound.

The optional fifth demo is the1x1 pivot-only boundary; the sixth is a dense
30x30 column-only scene. Four distinct, novel queries use7x9 quadrant,
14x19 row-only,23x27 column-only, and30x30 wholly column-clipped quadrant
scenes. The complete query bank is seed-shuffled before a shorter query prefix
is selected. Native public presentation applies its separate private shuffle.
Same seeds/counts have identical inputs across settings; query answers never
teach another query. Demo and query RNG streams are independent.

Large scenes use hundreds of colored cells, several colors, holes, disconnected
pieces, partial clipping, and an off-center pivot. Their empty mirror region is
required by the global side predicate. The30x30 demo has over400 occupied
input cells and over700 after one pass; the30x30 query has over300 occupied
input cells and deliberately remains unchanged because every column copy clips.
The generator does not claim to sample every grid admitted by its validator.

## Reproduce from the packet outer directory

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m pytest generators/abe8a3c35e86/tests/test_native_family.py generators/abe8a3c35e86/tests/test_native_audit.py -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 generators/abe8a3c35e86/workspace/parametric/audit_native.py --out ../checks/abe8a3c35e86/teaching-new
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify abe8a3c35e86 --demos 4 --queries 4 --out ../checks/abe8a3c35e86/qualification-new --summary
```

Use fresh output paths. The independent audit freezes candidate fits from only
the supported demonstration prefix before scoring all surviving hypotheses on
each private query. Every reported audit label is checked through protected
Racket. Finite seed/rival results do not establish universal identifiability or
training admission. Exact programs, settings, seeds, source identities, answers,
intermediate grids and future queries remain controller-side evidence.
