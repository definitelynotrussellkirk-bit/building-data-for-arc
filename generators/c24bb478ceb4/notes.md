# Working notes: c24bb478ceb4

## Current design (3.1.0)

Each foreground color independently marks three corners of one axis-aligned
rectangle. The output adds only that color's missing fourth corner. Ordinary
sampling stays on canonical grid/count profiles while cycling palette bands and
an eight-position missing-pattern schedule.

The schedule alternates fixed-orientation and within-grid mixed-orientation
cases:
`top_left, mixed, bottom_right, mixed, top_right, mixed, bottom_left, mixed`.
This ordering is deliberate. With three demonstrations and one query, holding
out any one of four consecutive pairs still leaves a mixed-orientation demo.

## Reversed decision

Version 3.0.0 grouped four homogeneous-orientation samples before two mixed
samples. A plausible wrong rule—read the lowest-color rectangle's missing
orientation and apply that orientation to every color—fit all demonstrations in
18/54 checked three-demo windows and disagreed on the query in 9/54. The first
repair interleaved one mixed sample often enough for normal production, but a
300-lesson rotation census still found 201/1,200 held-out positions where the
mixed witness became the query. The final alternating schedule removes that
hole, and the rival is now declared in `SEMANTIC_RIVALS` /
`LESSON_COMPETITORS` with a `mixed_orientations` witness.

## Evidence and limits

Final source SHA-256:
`18096bd474f9f6825d4f9257c8949c19741d94d4ecfce01fc0f1770ec002d244`.
The final battery is 12/12 green; task tests are 10/10; the final 300-lesson
census reports 0 production ambiguities and 0/1,200 rotation ambiguities.
`workspace/probe_first_orientation_rival.py` also checks 54 deterministic cyclic
windows and reports no survivor. These are finite checks against declared and
one specifically reproduced rival, not a proof of unique induction against all
possible image features or every seed.

The canonical Racket rule and `RULE_HASH = 237d8e244b45` are unchanged.
## Current reviewer considerations

Source SHA-256: `18096bd474f9f6825d4f9257c8949c19741d94d4ecfce01fc0f1770ec002d244`.

# Decisions

## D1 — Treat the first-object broadcast rule as a teaching defect

**Observed failure.** Version 3.0.0's missing-pattern schedule grouped four
homogeneous-orientation puzzles before two mixed puzzles. The task is labelled
correctly, but a plausible learner can infer the lowest-color rectangle's
missing orientation and broadcast it to every rectangle. That rival survived
18/54 tested three-demo windows and disagreed on 9 queries.

**Decision.** Repair the lesson distribution. Correct individual labels are not
enough when ordinary demonstrations make a materially simpler wrong program
indistinguishable from the intended per-color law.

**Rejected alternative.** Documenting the ambiguity without changing the
schedule would preserve avoidable low-value training examples. Adding more than
three demonstrations was also rejected because the defect can be removed while
keeping the declared demonstration budget.

## D2 — Declare the adaptive rival and its witness

The rival was added as `_first_orientation_for_all` in the existing semantic
contract. It is linked to a `mixed_orientations` witness: at least one legal grid
must contain rectangles with different missing corners. This lets the shared
semantic machinery diagnose manually assembled lessons rather than relying only
on the default sampler.

A task-local declaration was chosen over a broad image heuristic because the
generator already exposes exact rectangle observables. The generalizable gate
is proposed separately in `QUESTION_ANSWER.md` and `F1`.

## D3 — Alternate fixed and mixed samples deterministically

**Final choice.** Use
`top_left, mixed, bottom_right, mixed, top_right, mixed, bottom_left, mixed`.
Every four consecutive pairs contain two mixed cases, so three demos retain a
mixed witness under every one-of-four query rotation.

**Why deterministic.** Exact cyclic guarantees are cheap to test and replay.
Randomly drawing `mixed` with a high probability was rejected because short
lessons could still cluster homogeneous cases, requiring probabilistic
resampling and making failures seed-sensitive.

**Why retain fixed cases.** An all-mixed schedule would refute the broadcast
shortcut but reduce explicit coverage of each missing-corner orientation and
unnecessarily narrow the distribution. Alternation preserves both kinds of
support.

## D4 — Reject the first interleaving after rotation evidence

The first repair used enough mixed cases for normal ordered lessons and reduced
the deterministic shortcut probe to 0/54 survivors. However, a 300-lesson
census found 201/1,200 ambiguous rotations: when the sole mixed case was held
out, all three remaining demos were homogeneous. That is a genuine failed
iteration, retained in `checks/lesson-census-summary.json` and
`checks/lesson-census.json.gz`.

The schedule was strengthened rather than weakening the claim to ordered-only
support, because the downstream four-pair bundles can cheaply support arbitrary
query placement.

## D5 — Keep the authoritative rule unchanged

The Racket transformation and canonical outputs already implement the intended
per-color rectangle completion. The problem was curriculum identifiability, not
label correctness. `RULE_HASH = 237d8e244b45` remains pinned; no canonical data
or authority file was edited.

## D6 — Preserve focused failures and use portable tests

The two initial failures and the later rotation failure are kept as separate TDD
runs. The final task tests run in the isolated runtime through `arcpuzzles check
--stage task_tests`; the new test module imports only the staged generator API.
The frozen legacy fixture was not edited.

## D7 — Keep audits adversarial and read-only

Audit target `4797203a6428` has a reproduced exact-control defect; target
`0be9d8005490` has a reproduced D4 lesson shortcut. Their generator sources were
not changed because the assignment requests evidence, not repairs. Racket
receipts and source hashes bind both findings.

## Limits

The final evidence establishes absence of the named shortcuts on the tested
support, not mathematical uniqueness of the intended rule. Other adaptive
features could still correlate with outputs. The final schedule was reviewed
for a new residue cue and query-position dependency; none survived the complete
one-of-four rotation census, but untested hypotheses remain explicitly unknown.
