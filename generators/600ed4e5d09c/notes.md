# Working notes: 600ed4e5d09c

## Current decision

Repair the base generator before admitting a parametric family. The inherited
v2.1.0 generator placed a supposed frame-color control at the bottom-left corner,
but the canonical program reads only the top-left selected-color control and the
top-right transform key. Worse, the colored singleton was itself accepted as a
rectangular outline, so generated examples could select the wrong frame.

Version 2.2.0 removes that false control, makes `grid_h`, `grid_w`, and
`palette_kind` truthful, rejects unknown or incorrectly typed overrides, and
checks the actual two-anchor semantics against an exact Python mirror of the
canonical program. The canonical Racket program and `RULE_HASH=f96ec5618f89`
remain unchanged.

The native family has two matched-input settings:

- `transform_codebook=canonical`: byte-exact canonical key mapping.
- `transform_codebook=inverse`: key 1 uses counter-clockwise rotation, key 2
  remains 180 degrees, and keys 3/4 swap vertical and horizontal reflection.

Step A selects, tightly crops, and transforms the asymmetric target object. Step
B centers that transformed intermediate inside the detected hollow frame. The
first two demonstrations use keys that distinguish the codebooks. The adapter
supports 2–6 demonstrations and 1–4 queries independently and retains four
queries, including a 30x30 boundary-stress case.

## Verification and limits

Fourteen base-regression tests and ten focused family tests pass; the complete
source-bound staged suite passes 24/24 tests. The bounded audit passes all 12 jobs
with 177 protected-Racket evaluations and no surviving named rivals. Authoring
preflight passes four qualification jobs with 32 protected-Racket label
evaluations. The skip-transform witness changes two final cells, and public
release checks pass 16/16 one-query views, four first turns, 24 private-field
invariance mutations, and four positive controls.

This is reviewer-reported `ready`, not owner acceptance. Exact-source owner
review, native qualification, fresh acceptance, and training admission remain
mandatory. The finite rival audit is not a universal uniqueness or training-value
proof.
