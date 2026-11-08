# Current public-evaluation creation: 8b9c3697

The new reference infers comb geometry, never looks up supplied grids. Each
nonred comb is identified by its complete spine, two equally long guard teeth,
and a shorter middle tooth. The middle tooth's transverse interval and outward
tip define the matching lane. Solid red rectangles must match the lane's width
and position exactly. The nearest eligible rectangle docks immediately against
the middle tip; its swept footprint becomes black, except the docked red block.
Every other red component is erased to the inferred modal background. A comb
with no compatible object remains unchanged. All three supplied demonstrations
and the supplied test gold passed protected-Racket authoring execution.

`candidate_order=nearest` is reference.rkt byte-for-byte. `farthest` changes only
which compatible object is selected, not width matching, orientation, stopping
geometry, deletion or trail semantics. The original test distinguishes nearest
from farthest using two aligned rectangles of different axial depths.

Fresh scenes contain two to four combs, independently colored and oriented,
widths 1..3, short tooth lengths 1..2 and guard lengths 3..4. Each comb has two
compatible blocks, plus closer and farther wrong-width blocks and off-axis noise.
The first two demonstrations reverse near/far payload size order, defeating
largest/smallest-block proxies. Demo count 2..6 is independent from exactly four
novel private queries; count-stable streams and an independent presentation
shuffle preserve a one-query first turn. 30x30 scenes contain three/four complete
socket interactions, not an enlarged blank margin.

Self-review found that independent arbitrary panel orientations allowed a ray
to capture a different panel's object. A failing regression reproduced it.
The constructive sampler now orients each quadrant's rays outward and uses
explicit clearances; the reference itself does NOT assume panels, gutters or
quadrants. The analyzer rejects competing eligibility across sockets. The
sampler's bounded grammar excludes intersecting streams, equally eligible ties,
ambiguous combs, and zero/red backgrounds. Unsupported inputs are not promised.
All reference directions use signed axial/lateral coordinates, so up and left
receive the same geometric treatment as down and right.

The causal counterfactual substitutes the long guard's tip for the derived short
middle tip, leaving the selected compatible payload unchanged. This changes its
final position and black trail under protected Racket. Audit/export tooling is
copied locally rather than imported from the other task, keeping both artifacts
independently relocatable.

Evidence is under WORK/checks/public_eval_8b9c3697/preflight and audit. Finite rival,
Racket parity, negative export and privacy checks do not establish universal
uniqueness, native qualification, owner acceptance or training admission.
