## fdb8815ba528

**Domain question / coverage restriction — overlapping bounding-box precedence
is not taught.** The 58 portable task tests pass, and the advertised grammar and
named rivals are well covered. The canonical Racket program nevertheless paints
component boxes sequentially, so different-color box borders that overlap have
an order-dependent output. Production rejects all overlapping bbox footprints,
therefore this composition behavior is absent from its lessons.

`checks/audit/fdb8815ba528/overlapping-bbox-witness.json` contains an exact 7×7
input with two disjoint L-shaped components whose tight bounding boxes overlap.
The selected Racket authority matches row-major component processing and differs
from a reverse-order rival at `(2,4)` and `(4,2)` (authority color 3 versus rival
color 2). The generator's `self_check` rejects the input solely because the bbox
footprints overlap.

This is not a failure inside the declared nonoverlap grammar. It is a concrete
unrepresented part of the canonical rule's composition semantics. A future
repair can either retain and explicitly document the restricted domain or add a
nonambiguous overlap curriculum with an executable reverse-order rival. No
audited source was edited.
