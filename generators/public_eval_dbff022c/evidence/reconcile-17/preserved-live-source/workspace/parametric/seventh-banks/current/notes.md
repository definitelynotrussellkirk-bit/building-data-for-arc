# Current authoring state

New public parent dbff022c; no owner registration or acceptance. The reference
reproduces all three demonstrations and the supplied test gold. The multicolor
solid legend is two cells thick and touches a canvas edge. Read it **inward**:
the outer row/column is the key, the inner row/column the value. Mapping is
directed and one-step: a color appearing only as a value is not a key. Discover
four-connected background pockets; only enclosed regions with a monochromatic
boundary and a known key are filled. Open background, unmapped holes, boundaries
and the legend remain unchanged. Background is modal, not necessarily zero.

Settings: `fill_scope=all` is the exact authored reference;
`largest_per_color` fills every maximum-area enclosed region for each boundary
color, retaining all ties across distinct objects. The intermediate consists of
exact region cells, enclosing color and occupied-cell count. A bounding-box-area
substitution selects different regions in the retained 30x30 causal case.

Two to six demos, exactly four novel queries, matched input streams. The native
adapter retains a private coverage schedule; the evidence helper independently
shuffles all four before revealing one at a time. Inputs include an object with
multiple unequal holes, multiple objects of one color, equal-area ties, irregular
holes, diagonal enclosures, open shapes, unmapped keys, self-maps, mapping chains,
all four legend edges, nonzero backgrounds and distributed 30x30 geometry.

Self-review found a genuine two-demo teaching gap: on self-colored small diamonds,
painting a hole's bounding box was indistinguishable from painting its exact cells,
but it changed the 30x30 answer. Six protected-Racket evaluations confirmed the
saved pre-repair case (both demos agree, query differs by four cells). The first
demo now maps its nonrectangular diamond to a different color; alternating scenes
retain self-maps. The regression test failed before repair and passes after it.
No query answers or future inputs select demonstration content.

The finite audit compares 22 named Python policies; bounded protected-Racket
checks establish parity for executable geometry/mapping rivals. This is not
universal uniqueness. Generated components are separated; each admitted scene
has one full legend with unique keys. A 2x2 legend touching a horizontal edge
uses that orientation; ambiguous corner arrangements are not sampled.

`generator.py` and native `model.py` are intentional identical standalone copies.
Native resources must remain inside the parametric folder; base modules must
work after relocation. Keep the copies synchronized on future edits.

Evidence: WORK/checks/public_eval_dbff022c/. Authoring preflight, task tests and
reviewer causal replay are not owner qualification, acceptance or training admission.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.
