# Current design — public parent 8f215267

New public-evaluation creation. The immutable `workspace/public-parent.json`
provides exact parent linkage. There is no owner registration or acceptance yet.

## General reference rule

Find wide hollow monochrome rectangular frames. Exclude them from object
segmentation, count the remaining connected objects by each frame's color, and
encode each count as separated same-color dots along its middle row, right
aligned with a blank cell before the right wall. Retain the frames and erase
all external objects, including colors not represented by any frame.

This geometric rule reproduces the three provided demonstrations and the
provided test gold through protected Racket. The source contains no original
input/output lookup and no fixed palette or frame position.

The official examples do not distinguish four-neighbor from eight-neighbor
connectivity. This new canonical extension uses four; the alternative explicitly
teaches eight. No claim is made that the official examples uniquely imply four.
The generated minimum lessons contain diagonal contacts that distinguish them.

## Family and grammar

`connectivity=4|8`. The default program is exactly `reference.rkt`.
Two to six demos and one to four queries are supported independently, with a
full fixed bank of four queries built before private presentation shuffling.
Inputs are matched across settings. Returned arrays are copy-isolated.

Scenes use 3 or 4 large hollow frames, arbitrary background/key/distractor colors
(including zero), right-side and below-frame placement, zero and nonzero counts,
singletons, bars, L shapes, crosses, squares, rings, and deliberately diagonal
clusters. Query four is 30x30 with four frames, a large external counting field,
and content touching the right and bottom borders. The first stress frame
exercises all six tally positions under four-connectivity, versus three under
eight-connectivity. Counts fit each frame's
available tally capacity. Frames have distinct colors; external pieces are not
attached to their frames; legitimate objects are not frame-shaped. Top-left is
background. These are explicit generation-domain restrictions.

The first two demonstrations show a missing color, multiple same-size objects,
singletons and nonsquare shapes, as well as diagonal adjacency. Bounded minimum
lesson selection checks both connectivity settings against eleven executable
rivals, including area counting, distinct-size counting, color presence, global
count, counting the frame, sorted-color assignment, ignored singletons, only
rectangles, left alignment, retained inputs, and opposite connectivity.

## Sequential dependency

A identifies/removes frames and segments the exterior color graph; its
intermediate is the per-frame component-count vector. B uses those counts to
choose how many distinct tally positions to paint. The source-bound protected
counterfactual increases only the first frame's intermediate count by one,
keeping the actual input, colors, frames, rendering geometry and all other
counts unchanged. Topological object counting is not a fixed recoloring.

## Self-review and handoff

The common loader initially cached only by file path. A same-size, same-mtime
mutation regression exposed stale reuse. The adapter now compiles exact bytes
under a path-plus-content identity; both families retain the regression.
Finite checks do not prove uniqueness against all possible rules or any measured
training benefit. Direct focused pytest is the available test path for these
unregistered public IDs: the ordinary task-test wrapper requires an owner catalog
entry and cannot yet resolve them. Authoring preflight is intentionally separate
from owner source review, native qualification, fresh acceptance, and training.

`adapter.present` and audit bundles are controller-only. Give a model one public
view at a time without directory listings, source indices, programs, seeds,
future queries, or answers. Owner integration must preserve the public parent
link and run native admission against the exact integrated bytes.

## Native source closure
The adapter reads an exact canonical copy inside `workspace/parametric/canonical.rkt`, explicitly declared as a resource. This keeps program bytes inside the native promotion source inventory rather than relying on the task-root `reference.rkt`. Regression tests relocate only generator.py and the prototype directory, then produce a complete lesson; a separate default equality test requires the copied rule to remain byte-exact with the root reference.
