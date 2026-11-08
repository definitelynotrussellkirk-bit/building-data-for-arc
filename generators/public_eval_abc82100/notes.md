# Current authoring state: public abc82100

The general rule recovers cyan stencils and their two-cell handles. The outside
handle color is the source-marker color; the inside color is the paint color.
The handle continuation on the stencil bounding-box boundary is the anchor,
which may itself be a zero cell (for a chevron, for example). Erase stencils and
handles, then replace all remaining source markers simultaneously with clipped
stencils. Keep unmapped dots. Reciprocal color mappings must not be sequentially
re-applied. Adjacent thin cyan stencils can share one connected component: their
different handles partition it into maximal straight cyan runs. No original
grid or answer is stored in or loaded by the solver or generator.

Python and protected Racket reproduce all four training examples and both supplied
test golds. Those golds were used during development, not held out for a score.
The single-handle or exact straight-ray-partition grammar rejects ambiguous or
unkeyed cyan regions in the Python analyzer. Arbitrary ambiguous templates or
conflicting different-color stamp overlays are not claimed as solved.

## Native family
`finish=stamp` equals reference.rkt and canonical.rkt byte-for-byte.
`finish=mark_overlap` expands the exact clipped stencil footprints, then marks
coordinates covered by two or more stamp instances with 9. This is not source-dot
overlap: the dots are distinct. Stencil holes, anchor offsets and clipping determine
the expanded intersections. Replacing exact stencils with their bounding boxes
changes the intermediate footprint multiset and final protected-Racket output.

The sampler varies palette, two/three templates, all handle directions and
whole-scene dihedral transforms, simultaneous reciprocal mappings, sparse
unmapped dots, intersecting stamps, clipped stamps, and touching long stencils.
Two examples teach a regular multi-template scene and a touching-line scene.
Four private queries include both regular and long-line 30x30 scenes. Demo/query
counts are independent; full-bank shuffling precedes prefix selection. The public
projection allowlists only demo input/output and one current query input. Public
file IDs depend solely on their own bytes; directory contents and presentation
mapping are controller-private.

The finite rival set tests swapped keys, bbox rather than exact masks, center
rather than handle anchors, dropped clipped stamps, first-template-only behavior,
other setting, and marking every stamped cell. Both code paths are executed in
Racket and compared with the Python rival, so runtime errors are never counted
as a teaching success. Finite-rival rejection does not prove unique induction.

Reusable tools: audit.py (structural/Racket/rival/causal checks) and publication.py
(pre-write validation, public content addressing and tamper detection). Every
runtime dependency is in this exact checkout; native resources are adjacent.

Authoring preflight is not owner qualification or acceptance. Registration,
exact-source review, fresh native qualification and acceptance remain pending;
training_admitted=false.

## Current repeated-parent reconciliation

Preserve exact stamp/mark_overlap programs; add exact largest-component and quarter-turn programs and both incoming constructors. Three-demo curriculum retains incumbent touching/overlap lessons and selects a demonstration rejecting known quarter-turn shortcuts. No Cartesian composition is claimed. Current evidence resides in evidence/repeat-sixth-union. Private native acceptance and root publication are separate.
