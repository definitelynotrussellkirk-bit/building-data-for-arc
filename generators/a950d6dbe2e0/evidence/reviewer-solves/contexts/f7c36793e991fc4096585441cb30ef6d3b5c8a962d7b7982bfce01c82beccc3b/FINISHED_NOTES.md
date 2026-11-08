# Solve work log

## Exposure before solving

Before `blind prepare`, I read packet-level operating documents and the drawn duties. I did **not** open this task's generator, canonical rule, notes, prior solutions, audit evidence, or private query labels. The packet-level documents did not describe this task's transformation.

## Revision 1 — bilateral completion

**Observation.** In every visible training pair, all initially populated cells lie in the top-left half-grid. The output preserves that half-grid and reflects it across the vertical centerline, then reflects the completed top half across the horizontal centerline. Each original nonzero therefore appears in four symmetry-related positions (with zeros reflected too).

**Hypothesis.** For output coordinate `(r, c)`, use input coordinate `(min(r, H-1-r), min(c, W-1-c))`. This folds every output coordinate into the top-left quadrant and supports rectangular grids.

**Probe.** I wrote a local visible-example test that imports `solution.py` and compares `solve(input)` against all three public training outputs. The unimplemented template first failed with `NotImplementedError`, confirming the test exercised the solver. After implementing the fold, all visible examples passed.

**Alternatives considered.** Copy only nonzero cells into reflected positions, or detect a bounding box and tile it. These are needlessly special: the observed transformation mirrors the complete quadrant, including zeros, and the fold formula directly explains all rows and columns.

**Remaining uncertainty.** The visible examples and both query shapes are even-sized, so no center row/column behavior is demonstrated. The formula naturally leaves a center row or column self-mapped on odd dimensions.
