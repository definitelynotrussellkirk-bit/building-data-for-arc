## 28b87bd4c441

**Source-bound corroboration — dimension-template shortcut remains on the pinned source.**
Supplementary ticket `ticket-e90ecd36fc166b47` ran one bounded probe against generator SHA-256
`29036f7470aca505bde6c0a0f047c9a131ab22a9a27abcd6b111d333ea6ebc2e` and canonical rule `0af5c7008ee7` (raw program SHA-256
`d488617f0f22d0115b860791a46ebdb0b32dd15c52cbbd12f0c2612c95addb7c`). This corroborates the retained unresolved finding
`review-c80cb054851bda44:v0001`; it is not a separate new label-error claim.

The pinned ticket seed was converted with `int(probe_seed[:16],16)` to
`12776969345045385379`. One fresh medium-difficulty lesson at sample indices 0–7
covers all eight profiles. A rival learns a shape template for each canvas size
from those demonstration outputs and stamps that template at the red marker,
without examining query gray geometry. It fits all eight demonstrations and the
three canonical training pairs. On the original 12×13 canonical query it differs
from protected Racket at `(2,2)` (rival 5, reference 0) and `(2,3)` (rival 0,
reference 5), using zero-based coordinates.

The canonical query passes `self_check` and `strict_canonical_like`; the complete
eight-demo lesson also returns `lesson_identifiable == []` for it. Conversely,
`observe_overrides` rejects that query because it is outside the eight exact
sampling profiles. This is a teaching and canonical-coverage limitation. All
12 executed reference outputs match the unchanged mirror and all four canonical
labels. No wrong reference label or failure on a sampled production query is
claimed. No peer source, approval record, or audit disposition was changed.

Evidence, relative to WORK: `checks/tickets/ticket-e90ecd36fc166b47/witness.json`, `checks/tickets/ticket-e90ecd36fc166b47/probe.py`,
`checks/tickets/ticket-e90ecd36fc166b47/reference-batch.rkt`, `checks/tickets/ticket-e90ecd36fc166b47/result.json`, and
`checks/tickets/ticket-e90ecd36fc166b47/command.json`. The result retains source/runtime hashes and scope.
Suggested follow-up remains to vary lawful shapes within each canvas size and
include a demo that defeats this rival before claiming canonical-query coverage.
