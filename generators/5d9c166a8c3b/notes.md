# Current generator decision

The former v2 sampler advertised eight axes but always emitted four two-cell
objects in two fixed clusters and rejected every canonical input.  Version 3.0.0
now pins canonical rule hash `020d87daf483`, accepts all canonical profiles, and
implements the exact fixed-point bbox merge as `rule_mirror`.

The public axes are deliberately reduced to four observable controls: dimensions,
final cluster count, and foreground color.  Each generated grid contains one scheduled semantic cluster plus zero to three
diagonal singleton groups.  The witness scales from the original 3x3 point case
to connected rectangular objects as space grows; this covers canonical-scale
object sizes and keeps the red fill visually substantial.  The singletons lie
outside both row and column spans of the witness, so they change the requested
final cluster count without changing the rule demonstration.  This compact
grammar still realizes every declared count 1–4 on the minimum 7x7 grid.  A
three-slot schedule rotates row-only links, column-only links, and a
row-then-column chain that requires transitive fixed-point merging.

Task-local regressions cover canonical pairs, exact overrides including the
full minimum-size cluster matrix, strict seed/sample-index validation, malformed
inputs, all three semantic branches, canonical-scale connected objects, visible
fill density, rival elimination, determinism, and hand-derived
row/column/transitive outputs.

## Separate parametric family: all / largest final bbox

The task-local `workspace/parametric/` adds `fill_scope=all|largest_bbox`. The
`all` setting returns the exact canonical Racket text; canonical generator and
authority bytes are untouched. The alternative selects every group tied for
maximal final bounding-box area after full dynamic closure, then fills zeros.
The two productive groups must both be taught: the old sampler's singleton
distractors cannot distinguish these settings.

The constructive sampler supports 7–30 cells per side, 2–6 demonstrations and
1–4 queries. Inputs are matched across settings, and query count does not change
the demonstrations or first query. The first demo needs an outer fixed-point
pass; the second teaches ties and the transposed new-overlap direction. A third
demo, when present, makes the connected group larger. At 7x7 that latter profile
cannot fit and is explicitly recorded as a tie. Larger examples occupy both
ends of the canvas with substantial connected foreground and filled regions.

Self-review found a one-pass merge shortcut fitting the old two-demo lesson
(seed 0, all) but changing query 2. `checks/5d9c166a8c3b/teaching-hole-before.json`
retains both programs and actual protected-Racket labels. The new first-demo
orientation forces a previously retained component to be reconsidered; the
regression and declared-rival check cover that repair without adding demos.
Diagnostic tie selection uses topmost geometry, avoiding different internal
Python/Racket merge list orders. Finite rival checks are not universal uniqueness.

The assigned evaluation inspiration is 195c6913: visible examples motivate
geometry-dependent continuation. Here newly merged geometry controls target
selection. No equivalence to that task is asserted (`relationship_verified=false`),
and its full hidden rule was not established. Native owner acceptance and any
training admission remain separate from this proposed source and its checks.
