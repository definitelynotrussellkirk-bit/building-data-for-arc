# 5c126cb64bf7 — rotation-equivalence matrix

Version: `3.1.0`. Kind: `per_puzzle`. Selected Racket rule: `338c27e34ee3`, unchanged.

Split the input into three five-column panels, starting at columns 0, 6 and 12.
Crop each entire panel's nonzero bounding box and binarize it. Compare patterns
under all four rotations. The output is a symmetric 3×3 matrix: diagonal 8,
off-diagonal 2 for rotation-equivalent panels, otherwise 0. Reflections alone do
not establish equivalence; disconnected cells remain part of the pattern.

Inputs have a zero background, zero separator columns 5 and 11, width 17 and
height 5–9 (height 5 favored). Each panel has 3–7 cells in one nonzero color.
Colors may repeat across panels. Connected, disconnected and mixed-connectivity
grids are supported; shapes move within their panels. The finite shape family
contains normalized 3×3 masks and small cores with separated satellites in a
5×5 footprint, including all canonical shape orbits.

Default lessons use nine demonstrations and one query from a ten-slot schedule.
Repeated chiral quarter-turn and half-turn witnesses distinguish reflections,
counting, component-only matching and incomplete rotation rules. Required core
witnesses have no nontrivial rotational symmetry; free samples retain symmetric
shapes. Exact controls expose dimensions, class count, partition, palette size
and connectivity. See `notes.md` for compatibility and lesson limitations.

Checks and review evidence do not change catalog approval or training admission.

## Native parametric extension

The unchanged approved base now has a task-local `pattern_scope` family:
`whole` is the exact selected canonical source, while `largest_component`
extracts each panel's unique largest four-connected component and compares those
three normalized intermediates under rotation. The two-demo teaching prefix
separates the two settings as well as reflection-permitting, cell-count,
fixed-output and first-match-only rivals. Four distinct private queries include
a boundary-spanning 30×17 case with 27 foreground cells. Protected authoring
preflight and causal replay remain owner-pending evidence only.
