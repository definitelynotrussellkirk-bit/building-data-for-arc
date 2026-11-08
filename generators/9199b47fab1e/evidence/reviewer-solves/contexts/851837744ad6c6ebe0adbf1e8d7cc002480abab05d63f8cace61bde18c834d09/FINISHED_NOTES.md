# Solve work log

## Exposure

Before this visible-only solve I had not opened the task's generator, canonical
rule, reference solution, private query labels, audit evidence, or any repair
source. I used only the grids printed by `python3 review.py blind prepare` and
`challenge.json`.

## Revision 1 — seeded Manhattan phase inside wall components

**Observation.** The nonzero color other than red forms closed rectangular walls.
Only wall-bounded zero regions containing a red `2` change. A red seed becomes
`3`; cells one orthogonal step away become `4`; cells two steps away become `5`;
and the `3,4,5` cycle repeats with Manhattan distance. In the split examples,
each seeded compartment has its own phase origin, while an unseeded compartment
stays zero.

**Hypothesis.** Treat `0` and `2` as traversable for connected-component
membership. For each component containing a red seed, replace every cell by
`(3,4,5)[d mod 3]`, where `d` is the minimum ordinary Manhattan distance to a
seed. Preserve all walls and all unseeded components.

**Probe.** I first wrote a visible-pair regression test over all three training
examples. It failed on the untouched `NotImplementedError`, as expected. I then
implemented the component mask and distance law and reran the same test.

**Remaining uncertainty.** Query 1 contains a nested wall, making the outer
seeded component nonconvex. I interpret the visible pattern as a coordinate
Manhattan-distance phase masked by walls, rather than a shortest-path wave that
bends around obstacles. The training examples do not distinguish those two
interpretations. Multiple seeds in one component are not shown; the program uses
the nearest seed deterministically.
