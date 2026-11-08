# da515329: clipped spiral fragments

`spiral_policy=all_paths` is byte-identical to `../../reference.rkt`, via the
adjacent `canonical.rkt`. `longest_fragment` retains every completed path and
recolors the unique largest four-connected visible fragment red (2).

The rule infers center and radius from four equal, monochrome radial spokes.
The minimum effective radius is two, as required by the one-cell original.
Starting at each extended tip, its clockwise direction advances `2+4k` cells,
notches inward `radius-2`, advances another `radius`, and turns clockwise.
Whole paths are constructed in the plane, not terminated at a canvas edge.
All four supplied original labels (including test gold) are reproduced.

Generated grammar: 12–30 rows/columns, equal radius 1–6, nonzero non-red seed
color, four complete spokes and empty center. Rectangles and non-cyan colors
are declared extensions of the square/cyan supplied examples. No arbitrary
extra objects or incomplete/unequal spokes are admitted. Output growth reaches
all parts of the canvas; the 30×30 query is a genuine filled spiral, not padding.
Unique post-clipping largest component is required by bounded construction.
Ties in the general Racket selector use row-major discovery, but are not sampled.

`generate(seed, settings, demos, queries)` supports 2–6 / 1–4 independently.
Six fixed demonstrations and a separate four-query bank make prefixes stable.
The complete four-query bank is shuffled privately before taking a prefix.
`public_turn` returns a deep-copied whitelist: demonstrations and exactly one
unanswered query, with no count, ordinal, settings, program, seed or future data.

First two demonstrations eliminate the alternate setting and the declared
smallest, first, last, bounding-box, north-spoke and whole-arm shortcuts.
This is a finite hypothesis check, not proof of universal identifiability.
The sampler search is bounded (160 candidates/slot); tests retain exact seeds.

Run from the packet root:

```
python3 review.py task-tests public_eval_da515329 --phase after --timeout 180 --out ../checks/spiral-tests-new
python3 review.py run python3 generators/public_eval_da515329/workspace/parametric/audit.py --out ../checks/spiral-audit-new --seeds 20
```

No sampler runtime dependencies outside this folder; Python standard library
only. Audit and tests additionally require the checkout's protected Racket bridge.
Authoring preflight is not registration, native qualification, owner acceptance
or training admission. Preserve the source-bound witness when reconciling sources.
