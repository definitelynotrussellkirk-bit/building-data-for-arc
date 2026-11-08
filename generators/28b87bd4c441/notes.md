# Working notes: 28b87bd4c441

## Current rule and repair

Version **2.1.0** retains canonical Racket rule `0af5c7008ee7`: translate the
sole gray component so its bounding-box origin lands on the red marker, erase
the source and marker, and preserve the shape on the same-size black canvas.
Current generator SHA-256:
`d634827b23745c7c0ef57e134b3e68682c35143fc7326c237fae881176b71c46`.

The previous eight-profile curriculum assigned one shape to each canvas size.
A size-to-shape template could therefore fit the generated demonstrations while
failing the original canonical query. The actual canonical five-cell U is
`((0,0),(0,2),(1,0),(1,1),(1,2))`; it is distinct from both the old P shape and
the existing `hollow_u5` shape.

Two profiles now use that U on a 12x13 canvas:

- `canonical_up_right_u5` shares its size AND movement direction with
  `canonical_up_right_p5`. Their different outputs refute fixed templates
  conditioned on either dimensions alone or dimensions plus direction.
- `canonical_up_left_u5` includes the original canonical test's exact observable
  profile. All four canonical inputs now have a declared sampling profile.

Existing profile names and override meanings remain supported. The deterministic
cycle has ten profiles and requires **ten ordered demonstrations**, up from eight.
Every consecutive full cycle contains both conflicting templates and all eight
movement directions. Six of ten profiles satisfy the strict canonical predicate;
the sampled native semantic check observed 345/600 strict inputs (57.5%), above
the existing 45% minimum.

The lesson hook derives each template from a validated demonstration output,
relative to its input marker, and requires a conflicting template key. It does
not fit or validate against the query's private answer. It also rejects malformed
output grids, including Boolean and floating-point aliases for integer colors.
The portable suite in `tests/test_shape_teaching.py` uses public
`reviewer_support` imports and runs directly and in the isolated task-test
snapshot. The issued task-root tests remain byte-for-byte unchanged.

## Verification and audit disposition

In review `review-726007af613a01be`, the new regressions failed on the original
source (7 failures; 6 original cases passed), then all 13 portable tests passed
on the repair. After retaining that suite under the allowed `tests/` directory
and restoring the immutable task-root suite, the final isolated run passed all
19 collected tests (13 portable plus 6 issued tests). The earlier native
two-stage audit passed both isolated task tests and the strict semantic
gate: 12/12 ordered lessons identified; no materialization or competitor errors.
The independent bounded adversarial probe passed 81 cases, including missing
template/directional witnesses, malformed labels, all canonical pairs, and large
schedule indices. Exact commands, source bindings and outputs are in the return's
`RESULTS.json`, `checks/baseline/`, `checks/selected-audit/`,
`checks/final-task-tests/`, and `checks/adversarial/`. Racket-backed teaching evidence and a reusable verifier
are described in `workspace/README.md`.

**Dimension-template finding:** recommend resolving
`review-c80cb054851bda44:v0001` for these repaired bytes after intake assessment.
Its original source-bound evidence remains unchanged; source edits alone have
not changed the stored audit disposition or approval.

**Rotation finding remains open:** `review-1f4b2a09912ae523:v0001` is not resolved.
The supported contract is an ordered complete demonstration cycle. Arbitrary
holdouts can remove the only directional or template witness. The native
diagnostic recorded 108 hook warnings in 132 rotations, with zero errors and
zero ambiguities among its seven statically declared rivals. That does not
establish rotation safety or eliminate the stronger historical omission rival.

These checks establish a bounded repair to the named shortcuts. Sampling still
uses a finite set of shapes and profiles; arbitrary-shape generalization is not
proved. A next change should justify any added teaching cost and supply fresh
evidence before claiming broader shape support or arbitrary holdout support.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-837a747d9ae8ed16:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `29036f7470aca505bde6c0a0f047c9a131ab22a9a27abcd6b111d333ea6ebc2e`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

This peer audit binds old source 29036...; accepted repair review-726007af613a01be generator SHA d634827b23745c7c0ef57e134b3e68682c35143fc7326c237fae881176b71c46 adds distinguishing U profiles. Its reported staged and Racket checks address this dimension-template alias. Separate existing rotation limitation remains unresolved.

### Assessment or prior finding

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

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/28b87bd4c441/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
