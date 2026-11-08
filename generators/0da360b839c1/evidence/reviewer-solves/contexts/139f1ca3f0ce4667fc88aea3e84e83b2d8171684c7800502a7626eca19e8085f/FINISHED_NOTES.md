# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, canonical record, reference
solutions, private labels, audit records, or any earlier solution explanation. I
used only `solve-blind/challenge.json` and local visible-example checks.

## Revision 1 — point reflection around color 9

**Observation.** Every example has one color-9 cell that stays fixed. All other
colored cells reappear at the coordinate directly opposite that pivot, preserving
their colors. In relative coordinates about the 9, the mapping is
`(dr, dc) -> (-dr, -dc)`, i.e. a 180-degree rotation / point reflection.

**Probe.** In training example 1, the color-1 cell at relative `(-1,-1)` moves
to `(1,1)`, and the color-3 cell at `(1,-1)` moves to `(-1,1)`. In example 2
I briefly considered a horizontal reflection because the object moves from above
to below the pivot, but the lone color-7 cell at relative `(-1,+2)` appears at
`(+1,-2)`, which requires both signs to flip and rejects horizontal reflection.
The other two demonstrations also match the same 180-degree rotation exactly.

**Program.** Find the unique 9, create a zero background of the same shape, keep
9 fixed, and place each other nonzero cell at `(2*pr-r, 2*pc-c)`. The visible
examples show lawful in-bounds rotations; the implementation ignores any
out-of-bounds destination defensively rather than wrapping it.

**Remaining uncertainty.** The examples consistently use 0 as background and a
single 9 pivot. There is no visible evidence for multiple pivots or clipped
objects, so I did not add a competing behavior for those cases.
