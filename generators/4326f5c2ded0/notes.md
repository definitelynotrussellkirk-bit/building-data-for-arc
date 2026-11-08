# Current notes: 4326f5c2ded0

## Decision

Keep production generator v3.0.0 and canonical rule `884d94dde3d6` unchanged.
The concrete missing extension is now an opt-in prototype in
`workspace/parametric/shear.py`: episode-fixed direction (left/right) and
stride (1/2), with left/1 returning the exact canonical program text.
Both parameters preserve the bottom-anchored, row-dependent shear pattern.
No variant is approved or admitted to training by this change.

## Teaching and evidence

Use one diagnostic demonstration to expose direction, stride, clipping,
global anchoring, row gaps, and source clearing; vary additional objects and
query geometry. Every pair executes in Racket. Accept an episode only after
its demonstrations eliminate query-relevant ambiguity among the four
settings and eleven declared shortcuts. This finite set is not a universal
identifiability claim. Public names depend only on exact visible challenge
bytes; private seed, program, parameters, and query answers are separated.

Focused verification passed: 13 unittest tests; eight retained three-demo,
four-query episodes; 114 additional Racket pair applications including all
four settings at 8x9, 30x30, 8x30, and 30x9. Command receipts are in the
return's `checks/parametric/`. Counts are independently supported in 1..16;
exact generation dimensions are height 8..30 and width 9..30.

## Limits and next action

Maintain the opt-in boundary. The next owner decision is whether this small
family merits a formal variant schema and broader teaching/generalization
review before integration. Large profile schedules, arbitrary parameters,
blank-input semantics, and adversaries beyond the declared finite set are
outside this proposal. Existing production batteries and approvals were not
rerun or inferred. Imported associated notes retain their original evidence
and timestamps in `evidence/associated_notes.jsonl`.
