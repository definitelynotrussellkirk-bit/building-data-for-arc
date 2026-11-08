# Working notes: 2f0f072d3d7e

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `221970f06f2831e2a8a0f7d3f06abbf4e57cf0a722fefbaf3ccb2e3bf8876c15`.

# DECISIONS

## D1 — Keep the Racket authority unchanged

**Choice.** Preserve the selected canonical program and pin `RULE_HASH = "5c71009c7048"`.

**Reason.** The program already executes all canonical pairs and correctly expresses first-match transform precedence plus winner-position preservation. The defects were in generation, validation, controls, and teaching support—not label authority.

**Rejected alternative.** Editing the Racket rule to match a simpler sampler would change the task instead of repairing it.

**Evidence.** `checks/after/checks/2f0f072d3d7e_after_rule_smoke.log`, `..._authority_sync.json`.

## D2 — Replace the leaky axis surface with six exact controls

**Choice.** Advertise only `panel_s`, `n_candidates`, `shape_size_a`, `shape_size_c`, `transform_code`, and `winner_rank`. Validate types/ranges before `gen_ctx`; reject unknown keys; declare only `n_candidates=2, winner_rank=2` incompatible.

**Reason.** These values are pixel-observable and constructively realizable. Baseline palette, texture, density, position-bias, and distinct-color axes were dead, aliases, or degenerate escape hatches.

**Rejected alternative.** Keeping broad metadata while silently clamping it. Baseline override evidence shows why this is not harmless: it accepted unknown keys and produced thousands of mismatches and invalid scenes.

## D3 — Enumerate a finite connected-shape domain

**Choice.** Build cached translation-normalized connected supports, then choose A only from shapes whose requested code survives the authority's first-match precedence.

**Reason.** This eliminates capped-retry luck, symmetric-A transform drift, clipping, and accidental blank labels. Every legal joint override is constructive; the focused test enumerates all 720 joint tuples.

**Rejected alternative.** Random walks with retries. They made exact size/transform controls contingent on shape luck and were hard to audit exhaustively.

## D4 — Preserve canonical scale while varying difficulty

**Choice.** Default to side 4 and three candidates, yielding the canonical 4×29/eight-color profile in every band. Difficulty changes scheduled support sizes and RNG namespaces, not the rule.

**Reason.** The profile floor requires canonical support in each band, while dead difficulty knobs must still change realized grids.

**Limitation.** “Difficulty” is geometric variety, not a calibrated human hardness score.

## D5 — Use a source-visible teaching schedule, not independent random draws

**Choice.** `EXAMPLES_NEEDED = 5`; six consecutive pairs form a rotatable lesson. Quarter-turn codes 1 and 3 each occur twice with conflicting winner ranks; branch slots rotate identity/reflection/half-turn over an 18-draw superperiod. Winner ranks shift independently over cycles.

**Reason.** Any one held-out query leaves five demonstrations containing (a) a direction counterexample, (b) a later winner, and (c) at least one same-transform/different-rank contradiction. This kills the canonical inverse/first-candidate shortcuts and the later-discovered transform→rank proxy.

**Rejected alternative.** The first six-profile repair tied each transform to one rank. It passed all 12 stock stages but failed the added self-review regression; that intermediate pass is retained rather than erased.

## D6 — Make translation a nuisance, not an answer cue

**Choice.** Independently translate A, B, and C. For candidates, choose one common placement mode per example: all candidates shifted when every option permits it, otherwise all candidates top-left. Preserve the winning candidate's raw offset in the output.

**Reason.** Baseline top-left anchoring taught normalization. The first repair overcorrected by preferentially shifting only the winner, which could identify it. Shared mode demonstrates offset preservation without leaking candidate identity.

**Rejected alternative.** Always shifting only the winner. `checks/tdd-red-self-review.log` contains the concrete failure.

## D7 — Keep decoys equal-count and semantically useful

**Choice.** Every generated candidate has C's cell count. Quarter-turn scenes include the inverse-direction shape as a mandatory decoy; other transform-derived and finite-pool decoys are randomized before insertion at the exact winner rank.

**Reason.** Cell count cannot select the winner, and the inverse rival receives a concrete wrong candidate rather than merely falling off-domain.

**Limitation.** Canonical distractors do not always share C's cell count, so the validator accepts broader canonical-lawful inputs even though generation uses the stronger invariant.

## D8 — Separate authority, mirror, and independent probe

**Choice.** Racket remains label authority. `_solve` is a local mirror for contracts; `workspace/review_probe.py` independently reparses matrices and reconstructs geometry for tests and audits.

**Reason.** Independent code catches shared implementation mistakes and leaves a reusable tool for future agents. The probe also evaluates every declared namespace dynamically instead of hard-coding only one rival list.

## D9 — Declare finite rivals and generic lesson checks

**Choice.** Declare always-first, inverse direction, normalized output, copy-C position, and the exact obsolete transform/rank lookup. `lesson_identifiable` additionally requires a same-transform/different-rank contradiction in every five-demo view.

**Reason.** Canonical fit alone cannot reveal all teaching shortcuts. Executable declarations make claims testable; the generic hook covers the broader family of transform→rank tables rather than one fixed table only.

**Limitation.** These declarations do not exhaust the program space. The reports say finite evidence, not proof of unique induction.
