# f44596002946 — Connect Matching Endpoints

For each nonzero color appearing **exactly twice**, connect its two cells when
they share a row or column. Colors are painted in ascending numeric order, so
the larger color wins where completed horizontal and vertical segments cross.
Diagonal pairs and colors appearing three or more times remain unchanged.

## Generator design

Version `3.0.0` exposes one exact, grid-observable axis:

- `scene_profile=canonical_mixed`
- `scene_profile=cross_horizontal_high`
- `scene_profile=cross_vertical_high`
- `scene_profile=precondition_decoys`

Every four consecutive examples contain all four profiles. Together they teach
multiple simultaneous pairs, both possible crossing winners, the alignment
precondition, and the exactly-two precondition. Generated inputs use only the
canonical shape/palette signatures `(8,10,4)`, `(9,9,3)`, and `(7,11,4)`.
Endpoints never lie on another pair's segment.

The generator includes an independent Python rule mirror, exact override
observer, strict canonical predicate, named rival solvers, semantic witnesses,
and whole-lesson identifiability checks. Task-local regression tests and the
read-only `workspace/profile_audit.py` census preserve these guarantees.

Kind: `per_puzzle`. Imported version: `3.0.0`. Canonical Racket authority is
unchanged and pinned by `RULE_HASH=61e6c49f5645`.
