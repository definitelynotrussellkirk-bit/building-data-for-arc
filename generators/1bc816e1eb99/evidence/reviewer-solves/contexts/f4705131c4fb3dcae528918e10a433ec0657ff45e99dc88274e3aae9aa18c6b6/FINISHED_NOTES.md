# Solve work log

## Prior exposure

Before this visible-only solve I had not opened this task's generator, Racket rule,
reference solutions, private query labels, audit evidence, or earlier solution
notes. I had only read the public packet directions and the visible examples
printed by `python3 review.py blind prepare`.

## Revision 1 — classify objects by whether they enclose background

**Observation.** Every input consists of separated yellow (4) objects. The output
preserves all occupied cells and changes each whole object to either red (2) or
azure (8). Across all four demonstrations, rectangular solids and the irregular
3x3 object whose missing top-middle cell remains open to the exterior become red.
Closed outlines become azure.

**Hypothesis.** Recolor each four-connected nonzero object azure exactly when it
encloses at least one zero cell; otherwise recolor it red. This is a topological
hole test, not merely a density or rectangle test. The open notch in training
example 1 is the useful discriminator: its zero is connected to the bounding-box
boundary and therefore is not a hole.

**Program/probe.** I implemented four-connected component extraction. For each
component, I flood-fill empty cells from the boundary of its bounding box; any
empty cell not reached is enclosed. The implementation preserves grid shape and
background and recolors every component cell according to this test.

**Expected queries.** Query 0 has a hollow 3x3 object (azure) and a solid 4x4
object (red). Query 1 has two non-hollow objects (red), including the top-open
notched 3x3, and one hollow 4x4 outline (azure).

**Remaining uncertainty.** The examples use only background 0 and object color 4,
and objects are separated under four-connectivity. The implementation generalizes
to arbitrary nonzero component colors but assumes the intended connectivity is
four-neighbor, which is consistent with every demonstration.
