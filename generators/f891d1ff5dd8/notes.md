# Working notes: f891d1ff5dd8


## 2026-10-21 review-f4cb9d0b248a69e5

The pinned source SHA-256
`30e3efd77530e56104c4a4079e7f4ae0cdc7ed2a9a4dc705a6329a98e995bd7e`
was already approved and passed the retained lint, self-check, and Racket rule
smoke stages. Two prior audits (`review-db2283e10f17bf0f:v0001` and
`review-b854147a5b93c111:v0001`) independently reported the same unresolved
teaching ambiguity. The canonical-fitting rival “paint exactly `2 × width` body
rows, then stop” fits all four canonical pairs. On the pinned baseline, seed 20
with samples 0–2 as demonstrations and sample 3 as query reproduced it: the
three demonstrations matched the rival, while the 18×5 query differed.
Evidence: `checks/before/two-cycles-reproduction.json`.

Version 2.1.0 keeps the canonical Racket authority and public input grammar
unchanged. It declares `two_cycles_only`, adds the `beyond_two_cycles` witness,
and makes schedule roles 1 and 3 extend strictly beyond two complete header
cycles. Since two of four roles carry that witness, every three-demonstration
query rotation retains a refutation; the existing body-overwrite and positional-
repetition guarantees remain. It also rejects malformed request controls
strictly: booleans, floats, strings, negative sample indices, and undeclared
difficulty values no longer flow into deterministic sampling.

Final source SHA-256:
`633291826a9a5fe45eacbd918bef677a5864e4722525ced0e56cf65176cead27`.
The complete strict battery passed all 12 stages in `checks/after/`; portable
task tests passed 20/20 in `checks/task-tests/`. A Racket-labelled census
materialized 300 lessons (100 per band), 1,200 pairs, and all 1,200 single-pair
query rotations with zero ambiguities, hook warnings, scoring errors, or
materialization failures; 1,197 normalized inputs were unique. Evidence:
`checks/lesson-census.json` and its companion summary. The task-local exhaustive
mirror probe checked 4,096 rotations over seeds 0, 17, 20, and 91 and found no
surviving declared rival or hook failure in `checks/curriculum-probe-final.json`.

The requested nearby rule variant is implemented separately under
`workspace/parametric/`. Proposed `cycle_direction` is selected once per episode:
`forward` is the exact canonical source and `reverse` starts at `row0[0]` then
traverses the header right-to-left. Inputs are parameter-independent. Both exact
Racket programs were exercised, two retained episodes distinguish both settings,
and the canonical default replays all canonical pairs. Evidence:
`checks/parametric/cycle-direction-final/`. This is an unapproved prototype; it
does not alter production generation, rule authority, or training admission.

Known limits remain: the rival set is finite; the 300-lesson census samples the
production sampler rather than every seed; the 4,096-rotation probe uses the
Python mirror for speed; and bounded prototype evidence does not prove universal
identifiability.

## 2026-10-06 review-a1041c31d45ae959

The pinned v1.1.0 baseline had six failed battery stages. It lacked `RULE_HASH`,
accepted 0/67 destructive mutations, generated sparse noise with object-count
drift, exposed many incompatible or inert pseudo-axes, supplied no semantic
lesson contract, and used selected Racket text that was behaviorally equivalent
but not exact-text synchronized with the canonical authority.

The prior `kimi_generator_assignment.jsonl` row was used only as a lead. Its
`missing_rule_hash`, `rule_source_divergence`, and distribution-drift claims were
remeasured against the pinned source before repair.

Version 2.0.0 replaces random sparse noise with a compact reviewed grammar:
row 0 is a nonzero positional cycle, row 1 is a distinct solid decoy, and the
body is blank or one rectangle in the decoy color. A four-slot schedule provides
exact canonical anchors and deterministic counterexamples to two shortcuts:

- preserve nonzero body decoys instead of overwriting the whole body;
- deduplicate repeated header colors before cycling.

No Racket behavior changed. The selected base authority was synchronized
exactly to the canonical source (`at` rather than the legacy `cell-at` spelling).
The task-local tests and `workspace/probe_curriculum.py` are retained for replay.

Known limit: finite named-rival checks do not prove unique induction against all
possible programs. The generator intentionally stays near the public grammar
rather than sampling every mathematically lawful grid.
## Current reviewer considerations

Source SHA-256: `633291826a9a5fe45eacbd918bef677a5864e4722525ced0e56cf65176cead27`.

# Decisions for `f891d1ff5dd8`

## D1 — Preserve the canonical rule

**Finding:** F891-1 is a teaching-schedule defect, not an authority defect.
The selected rule already matches canonical hash `9a77eb6a5412` and all four
canonical pairs.

**Choice:** leave canonical and selected Racket source unchanged.

**Rejected:** changing the rule to stop at two cycles would encode the shortcut;
changing syntax without behavior would create needless authority churn.

**Evidence:** final rule smoke, Racket lint, and authority sync in
`checks/after/`; canonical source SHA-256
`0f0bd2e42171cc41e580b5adbbde6c7dcd73b9efdc12ca822b6b99a6b7594363`.

## D2 — Treat “two cycles only” as a canonical-fitting data obligation

**Finding:** the rival fits every canonical pair and a complete baseline
three-demo lesson, yet changes its query.

**Choice:** declare `two_cycles_only` in all three rival registries and bind it
to a concrete `beyond_two_cycles` witness.

**Rejected:** merely documenting the shortcut would leave the exporter free to
produce ambiguous lessons; relying on canonical parity cannot refute a rival
that fits all canonical examples.

**Evidence:** `checks/before/two-cycles-reproduction.json`, focused TDD logs,
and final census.

## D3 — Put two long-body witnesses in the four-role cycle

**Choice:** roles 1 and 3 satisfy `height - 2 > 2 × width`. With three
demonstrations from a four-pair window, every query rotation retains at least
one long-body witness.

**Rejected alternatives:**

- one long-body role: holding it out would recreate the ambiguity;
- random long bodies: finite frequency would not guarantee every lesson;
- four demonstrations: safe but unnecessary after every 3-of-4 rotation passed;
- shrinking the body cap: would change the rule rather than teach it.

**Trade-off:** compatible widths are narrower in long-body roles, but the full
strict profile floor still passes and the other roles retain broader support.

## D4 — Keep the three-demo, four-role curriculum

The retained schedule jointly teaches three independent distinctions:
body overwrite, positional repetition, and continuation beyond two cycles.
Every production bundle has three demonstrations and one query. Required
query-rotation support is explicit, not inferred from witness frequency.

**Evidence:** 300 Racket-labelled lessons and 1,200 rotations with zero
ambiguities; 4,096 additional cyclic rotations in the local probe.

## D5 — Reject malformed request controls at the boundary

**Finding:** strict defect-lint probing found booleans, floats, strings, negative
indices, and invalid difficulty values flowing into generation.

**Choice:** require exact integer types for seed/index, a nonnegative index, and
a closed difficulty enum before `gen_ctx` construction.

**Rejected:** coercion would make malformed calls silently alias valid samples;
letting downstream helpers reject a subset produced inconsistent behavior.

**Evidence:** red test `checks/tdd-scalar-red/focused.log`; green task test
`test_generate_rejects_malformed_call_control_scalars`; final defect lint.

## D6 — Build, but do not select, `cycle_direction`

The original-family priority supports a small parameter that preserves the
reasoning pattern. `forward` remains the canonical default; `reverse` changes
only the header index order. The setting is chosen once per episode and is not
encoded in input constraints.

**Rejected parameters:** changing which rows are preserved or whether the body
is overwritten would alter object roles and reasoning structure; resampling the
setting per pair would make an episode internally inconsistent.

**Status:** runnable proposed/unapproved prototype only. Production generation,
catalog selection, and training admission remain unchanged.

## D7 — Use independent and complementary evidence

The Python mirror is appropriate for exhaustive cheap schedule enumeration, but
not as the sole oracle. Racket supplies canonical labels for the strict battery,
lesson census, parametric episodes, and canonical replay. Portable task tests
verify both task-local code and staged-layout compatibility.

The interrupted before battery is retained as incomplete baseline evidence; it
is not promoted to a pass. The completed final-source battery is the aggregate
verification claim.

## D8 — Leave audit targets unchanged

The randomly assigned targets `d5a059b0f3a6` and `2f0b1cb87615` were inspected
and source-bound findings were retained in `AUDIT.md` and `checks/audit/`.
No source under either audit target was edited.

## D9 — Supersede `cycle_direction` with marker-derived `cycle_start`

The retained `forward|reverse` prototype was runnable but did not meet the new
causal A→intermediate→B requirement: reversing a fixed cycle is an episode-level
choice, not a value derived from the particular input. It is superseded for this
handoff by `cycle_start=first_header|row1_marker`.

`first_header` is the exact selected canonical Racket program. `row1_marker`
reads the unique row-1 cell whose color occurs in row 0, locates that color's
unique header index, and uses the derived index as the body-cycle phase. Inputs
are matched across settings. Demonstrations 1–2 constructively distinguish both
settings and seven executable phase shortcuts. Counts are independent over 2–6
demonstrations and 1–4 prefix-stable queries; qualification retains four queries,
including a distributed 30×30 case.

Finite self-audit covered both settings, seeds 0/17/31 and demonstration counts
2/3/6: 18 lessons, 1,104 protected-Racket evaluations and no harmful survivor
among the seven declared rivals. Native qualification passed four jobs and 40
protected-Racket evaluations. The protected causal witness uses a qualified
30×30 `row1_marker` query: the correct intermediate is header index 17; replacing
it with physical marker column 4 changes all 840 body cells.

Production `generator.py` and canonical authority remain unchanged. This is a
reviewer-ready native prototype, not owner acceptance. The owner must integrate
these exact bytes, rerun native qualification and fresh acceptance, and make any
training-admission decision separately. Optional peers were not run after
prioritizing the complete MAIN build and its adversarial/causal checks.
