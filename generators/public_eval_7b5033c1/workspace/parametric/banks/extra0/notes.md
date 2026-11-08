# 7b5033c1 — current source and handoff

Reviewer-ready public-parent creation, **not registered, owner-qualified or accepted**. `training_admitted=false`.

## Canonical rule
The uniquely modal background surrounds a single nonbranching induced four-neighbor path. Start at the row-major smaller endpoint, traverse its bends, and emit the visited colors as a one-column grid. Keep repeated colors in their separate path positions; a histogram is not the rule. The general Python and protected-Racket implementations reproduce both training examples and the provided test gold. Gold was inspected during development; these are reproductions, not an unseen-test score. No official grids or answers are embedded in the implementation.

## Parametric extension and causal dependence
`unroll` reads the byte-identical local `canonical.rkt` and preserves root `reference.rkt` exactly. `length_addressed_run` consumes that traced sequence: split it into maximal same-color runs; let k be the first run's length; recolor the kth subsequent run to color 9. Index 0 is the header, index k is selected. Recolor only this occurrence, not all cells of its color.

Stage A is path traversal; its ordered sequence/run boundaries are the intermediate; Stage B is input-derived addressing. A source-bound protected-Racket counterfactual substitutes spatial row-major scanning for traversal on the same 30x30 input, changing 17 final cells. Both programs are valid and the witness was independently replayed by the supplied protected replay helper; this is still reviewer execution, not owner acceptance.

## Constructive grammar and API
All implementation/resource files needed by the native adapter are within `workspace/parametric/`. The root generator delegates to the same implementation and declares literal `RULE_TASK_ID = 'ee_7b5033c1'`.

The bounded sampler makes induced self-avoiding paths, independently assigned run lengths/colors, repeated colors, variable turns, grid aspect ratios and boundary placements. It varies the header across consecutive demonstrations. Two demonstrations suffice for the two settings and tested shortcuts; supports independent 2–6 demo and 1–4 query requests. Generate all four queries before public projection; the complete bank is shuffled independently of requested prefix length. All ten full-bank inputs (six demos and four queries) are distinct. Inputs are matched across settings. Count and seed controls reject booleans/coercions.

Color 9 is reserved for alternate output. Sampled headers are lengths 2–4; source paths contain 18–30 cells. Every stress input is 30x30 with a maximum-length 30-cell winding path touching canvas boundaries. The canonical N-by-1 output caps N at 30: dense 30x30 foreground would violate the original rule's output-size limit. This is sparse, maximum-length boundary stress, not a dense-canvas claim. Walks use bounded construction/rejection; exhaustion or duplicates raise instead of returning fewer queries. The grammar does not claim every imaginable path drawing.

## Actual teaching repair
Before repair, seed 5 had two demonstrations with header/total-leading-color counts (4,4) and (2,2), while query 1 had (3,5). Counting all occurrences of the leading color fit both demos and failed that query. Six protected-Racket evaluations confirm the retained historical counterexample at `checks/public_eval_7b5033c1/header-shortcut-before.json`.

The sampler now constructs a later recurrence of the header color, with varying recurrence position, and separately repeats the selected color. This refutes both total-color addressing and global-color recoloring without increasing the two-demo budget. The seed-5 regression was observed RED then GREEN. A final 128-seed audit performed 2,304 minimum-demo teaching checks with no harmful declared-rival survivor.

## Export and verification
The public tool validates exact integer-color grids before any writes, strips metadata, hashes only visible challenge bytes, shuffles before truncating, refuses duplicate batches, and physically writes a complete batch in content-ID order. Its verifier detects tampering and missing expected files. A final independent packet checker exposed a missing-newline serialization mismatch in the inherited byte encoder; both families now match `reviewer_support.public_challenge_bytes` exactly and have regression tests against that external contract.

Final combined task suite: 85 passed (50 in this home, 35 in the other). This family's final audit: 256 episodes, 2,560 pairs, 1,024 public turns, 2,304 teaching checks, 240 protected-Racket evaluations. All four queries were executed for every declared rival at seeds 17 and 43; Python rival mirrors matched their Racket programs. Authoring preflight passed four jobs (two settings x two seeds), all three original labels and 24 selected generated labels. Current evidence is under `checks/public_eval_7b5033c1/{audit-final,preflight-final,causal-final}`. Packet public-file checker passed all 32 files across both targets. Relocation replay executed all four settings in a fresh subprocess with copied project source and no predecessor imports.

Owner must review the interpretation and exact source, register provenance, perform actual native qualification and acceptance, and separately decide any training use. Finite tests/rivals/seeds do not prove universal induction or training improvement. Final review is author self-review, not independent agent review.
