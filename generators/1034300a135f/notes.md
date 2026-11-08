# Working notes: 1034300a135f

## Native parametric candidate — current review

The native adapter now preserves the exact canonical DSL bytes for
`near_to_far` and changes only the stable distance sort key for `far_to_near`.
The separate constructive sampler supports 2–6 demos (default 3), 1–4 queries
(default 4), matched inputs across settings, independent count-invariant query
streams, and 5×5 through substantive 30×30 cases. The large mandatory demo uses
all 15 ranks; this deliberately spends one 29×30 demonstration to rule out
marker truncation at 8 or 14 before larger queries. Production and canonical
source remain unchanged. Earlier two-demo/one-query standalone evidence below
is historical; the native API is the current qualification candidate.

Self-review found and repaired a real two-demo teaching hole: both mandatory
distance ties originally had descending numeric color order, so a
color-descending tie-breaker fit both demos and failed a retained query at seed 17
under both settings. Keep the compact demo's descending tie and construct the
large demo's tie in ascending order. Both numeric tie-break alternatives are
now in the executable rival audit. The retained pre-repair witness is
`checks/1034300a135f/tie-shortcut-before.json`; final protected-Racket evidence
and qualification are linked in the return's RESULTS.json. Current verification:
57 focused tests pass; the minimum/maximum lesson probes reject 11 rivals under
both settings, and native qualification passes all four setting/seed jobs.
The source-bound four-case causal witness passes native schema validation.

The causal dependency is global spatial ranking → ordered marker identities →
rank-indexed output rings. A paired relocation leaves row-major color order
unchanged but changes several other markers' ring assignments; the executable
skip-sort ablation isolates this dependency. This is not claimed to be an
iterative simulation. Public bundles use exact visible-byte hashes, and the
single-query projection carries no future inputs or total-count metadata.
Answer-then-advance gating belongs to the caller, not this stateless projection.

Limits: finite rivals and bounded seeds, intentionally constructed lesson
profiles, a fixed menu of shapes, and no measured training benefit. Reviewer
qualification does not grant exact-source owner acceptance or training
admission. The inherited fixed-depth production test fixture is outside this
prototype-only change; no new whole-production-suite claim is made.

## Current intended rule

Choose the unique most frequent nonzero input color as background. Treat every
cell unequal to that background as an independent marker, including color zero.
Scan markers row-major, then stably sort by minimum distance to any edge. Paint
the sorted marker colors as output rings from the outside inward; when marker
colors run out, retain the background in deeper rings.

Generator version: `3.1.0`
Generator SHA-256: `0294ac0f781379c431b6e7d9319d78f7e6dcdc75856857c779544520a64d546b`
Canonical rule hash: `4e51401fbef6` (unchanged)

## Reversed decisions in this review

The prior `3.0.0` sampler selected from a weighted random profile list and had
no executable lesson contract. Retained return `review-cd846e20d1f37734:v0001`
showed a reverse-equal-distance-tie rival fitting all demonstrations in 69/900
sampled lessons; `review-b4a044e31c5fa03e:v0001` separately identified the
missing semantic hooks. The new choice is a deterministic 28-slot schedule:
`teaching_combined` occupies every even slot and all 14 earlier profiles cycle
through odd slots. This guarantees that every three-demo rotation of a
four-pair lesson retains a compact multi-witness counterexample.

The combined profile simultaneously exercises an equal-distance tie, a missing
raw distance, zero as a marker, one repeated marker color, nonnumeric color
order, and an unfinished center. Its nonzero marker placement also guarantees
a visible spatial change. This replaced an earlier construction whose ordering
could still admit a generic first-object-only mutation.

The prior public call contract also accepted boolean/float/string scalars and a
negative sample index. `generate` and `schedule_profile` now share strict
literal-integer, nonnegative-index, and difficulty validation.

## Semantic contract

Six executable rivals cover reverse tie order, raw-distance indexing,
extending the final color, ignoring zero, deduplicating colors, and numeric
color sorting. Six witness predicates map directly to those rivals. Four rivals
that fit at least one canonical pair are declared as `CANONICAL_SHORTCUTS`.
`lesson_identifiable` rejects a rival that fits every demonstration but changes
the query.

Minimal retained reproducer:
`counterexamples/reverse-equal-distance-tie.json`.
Reusable final-source verifier:
`workspace/review_probe.py`.

## Parametric assessment

A separate prototype at `workspace/parametric/` varies only marker-distance
ordering: canonical `near_to_far` versus proposed `far_to_near`, selected once
per episode. It includes exact Racket programs and public examples. Production
remains fixed to canonical near-to-far; this prototype is not approval or
training admission.

## Final evidence

- Full strict battery: 12/12 green (`checks/after-final/`).
- Semantic strict support: 600/600; canonical support 8/8.
- Fixed-seed declared-period check: all 28 residues and every query rotation.
- Production census: 300 lessons, 3 demos + 1 query, 0 ambiguities; all 1,200
  query rotations also unambiguous; 1,018 unique inputs.
- Focused source-bound probe: 6/6 checks pass.
- Canonical authority and Racket execution parity remain synchronized.

## Known limits and open findings

The finite rival set does not prove universal identifiability, and the random
census does not cover every seed. The strong alternating teaching profile is
curriculum-oriented and makes schedule parity observable. The official
portable task-test aggregate is blocked before pytest by the inherited frozen
fixture's fixed parent-depth lookup; that fixture was restored unchanged and
must be migrated by the library maintainer to `reviewer_support.find_root` and
canonical helpers. The focused probe covers the final source but does not
replace that official aggregate.

## Current owner source and evidence limits

Accepted version3.1.0 strict literal-integer seed/index validation, nonnegative index and supported difficulty validation. Signed integer seeds remain legal. Retains four exact public and ten prior generalized profiles, adds teaching_combined on even slots with the other14 profiles cycling odd slots (period28). Every three-demo rotation retains a combined witness against six declared rivals: reversed equal-distance ties, raw-distance indexing, extended center, ignoring zero, deduplicating colors and numeric color sorting. Canonical Racket remains unchanged (4e51401fbef6). Reviewer reports12/12 final battery stages,600/600 strict and8/8 canonical support,300 lessons/1200 rotations with no declared-rival ambiguity (1018 unique inputs), and all28 residues across three bands (84 lessons/336 rotations). These are finite checks; schedule parity is observable. The official aggregate task tests exit2 before pytest because the unchanged frozen fixture uses a fixed-depth canonical path. The intermediate36-test run used a temporary migrated fixture and is not a final aggregate pass. Final source-bound probe passes6/6, also after fresh full-packet replay. The separate marker_order near_to_far/far_to_near prototype selects once per episode and provides two demonstrations plus one query per setting, live Racket labels and opposite-setting refutation. Default parity is against the canonical mirror; standalone prototype source is not claimed byte-identical to canonical. Owner replaced literal-setting public filenames with visible-content hashes, passed two focused tests and regenerated both Racket exports. Original reviewer source and evidence are preserved. No production parameter API, variant approval, training admission or owner repair battery rerun.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-cd846e20d1f37734:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `846c9c14236798015ee21bdaab735fcef1bf36b33e8ffaa9f22a7c9dd48052fa`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolved for selected3.1.0 source: combined teaching profile is present in every three-demo holdout; six executable rivals/witnesses and lesson hook cover the missing contract and reverse-tie ambiguity. Reviewer final300 lessons/1200 rotations plus all28 residues/336 rotations have no declared-rival ambiguity. Canonical unchanged; source-specific prior reproducer remains retained. Finite evidence, not universal uniqueness. No owner battery rerun.

### Assessment or prior finding

## 1034300a135f

**Reproduced lesson-level tie-order shortcut.** The audited source SHA-256 was
`846c9c14236798015ee21bdaab735fcef1bf36b33e8ffaa9f22a7c9dd48052fa`.
A rival that orders markers by edge distance but reverses row-major order within
an equal-distance tie fit all three demonstrations and predicted a different
query output in 23 of 300 lessons in each difficulty band (69/900 total). The
reproducible policy was `seed=700000+lesson`,
`start_sample_index=lesson*11`, then three consecutive demonstrations and one
query. Evidence and the first counterexample per band are in
`checks/audit/1034300a135f/probe.json`.

The first ambiguous lesson in every band used the profile sequence
`partial_center_background`, `zero_outer_ring`, `public_4`, then
`tied_distance_row_major`; the tie-breaking evidence appeared only in the query.
The canonical Racket output (rule hash `4e51401fbef6`) and the rival output are
retained in `checks/audit/1034300a135f/racket.json` and
`checks/audit/1034300a135f/rival.json`. The generator declares none of
`LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `lesson_identifiable`, or
`strict_canonical_like`, so no executable lesson contract catches this case.
No source was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-cd846e20d1f37734-v0001/audit_assets.json), manifest SHA-256 `3ba1faf91fe43f7b28a0df8610fd6a21c6995899632ed6d790e8be425eacd0ec`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `0294ac0f781379c431b6e7d9319d78f7e6dcdc75856857c779544520a64d546b`.

# Decisions: 1034300a135f

## D1 — Preserve the canonical authority

**Choice.** Keep `RULE_HASH = "4e51401fbef6"` and make no canonical/base Racket
change.

**Rationale.** Rule smoke and exact canonical labels were already correct. The
reproduced defects were request validation and lesson sufficiency, not rule
semantics.

**Alternatives rejected.** Changing the Racket implementation or reinterpreting
zero as background would alter the original task and invalidate canonical
behavior.

**Probe.** Final battery authority sync and execution parity are green; the
counterexample query was labelled by the selected Racket rule.

**Failure mode/limit.** Authority parity proves the selected source matches the
catalogue authority, not that every conceivable generated input is useful.

## D2 — Fail closed on public scalar requests

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`, a
nonnegative sample index, and a known difficulty in one shared validator.

**Original choice.** The baseline relied on downstream arithmetic/random APIs,
which silently accepted booleans, floats, strings, and negative indices. The
reason for that permissiveness is unknown.

**Alternatives rejected.** Coercing via `int(...)` would preserve aliases and
make replay identities ambiguous. Validating only `generate` would leave
`schedule_profile` inconsistent.

**Probe.** The focused probe makes 38 invalid calls; all are rejected. Final
defect lint is green.

**Failure mode/limit.** This deliberately rejects integer-like third-party
scalar classes. The public contract is literal Python integers.

## D3 — Use a 28-slot alternating schedule

**Choice.** Put `teaching_combined` at every even index and cycle the 14 previous
profiles through odd indices, declaring period 28.

**Original choice.** Version 3.0.0 drew from public profiles plus a fourfold
weighted generalized list. It offered broad marginal diversity but no guarantee
that a complete lesson retained a tie-order witness.

**Alternatives considered.** Rejection-sampling whole lessons would require a
second assembly layer and complicate exact replay. A shorter schedule containing
only teaching profiles would shrink the grammar. Independent random profile
draws leave a nonzero ambiguity probability.

**Probe.** Exhaustive fixed-seed schedule evidence covers 28 residues × three
bands × four query positions = 336 rotations, all identifiable. The 300-lesson
random census also passes.

**Failure mode/limit.** Sample parity is observable and may become a nuisance
shortcut if consumers preserve global indices. The schedule guarantee applies
to four-pair lessons with three demonstrations, not arbitrary lesson sizes.

## D4 — Combine six teaching distinctions in one lawful scene

**Choice.** Build one odd-square profile with distances `[0,2,2,3,...]`, sequence
`[anchor,anchor,0,...]`, nonmonotone remaining colors, and unused inner capacity.

**Rationale.** A single combined scene survives every query rotation without
requiring six teaching examples. It simultaneously refutes the six concrete
rivals while remaining inside the original rule family.

**Rejected alternatives.** Six separate witness profiles could all be held out
under some three-demo rotation. An early combined sequence still admitted a
generic first-object-only mutation; remaining colors were changed to a
nonmonotone order, and a test now requires a nonzero marker cell to change.

**Probe.** The profile is recognized by `_is_teaching_signature`; 96 generated
instances in the focused probe refute all six rivals. The spatial regression was
first observed failing and then made green.

**Failure mode/limit.** The profile is intentionally dense with cues and may be
easier than naturally distributed examples. Other undeclared shortcuts may
exist.

## D5 — Make semantic claims executable

**Choice.** Add six `SEMANTIC_RIVALS`, matching witnesses, a strict-domain hook,
`CANONICAL_SHORTCUTS`, and `lesson_identifiable`.

**Rationale.** Profile names alone are not evidence that assembled lessons teach
the rule. Executable rivals turn concrete shortcut claims into regression
checks.

**Alternatives rejected.** A prose-only note would not protect future schedule
changes. Declaring every rival a canonical shortcut would be false because two
do not fit canonical support.

**Probe.** Final semantic gate, focused probe, fixed-period enumeration, and
300-lesson census all execute the declarations.

**Failure mode/limit.** Passing six rivals is bounded evidence, not proof of
program uniqueness.

## D6 — Keep marker-order variation as a separate prototype

**Choice.** Add an episode-level `marker_order` parameter with canonical
`near_to_far` and proposed `far_to_near`, each backed by an exact Racket file.
Choose once from the episode seed and use the same setting for both demos and
query.

**Rationale.** It is the smallest rule parameter that preserves background,
markers, distances, tie stability, and concentric construction while producing
a genuinely distinct transformation.

**Alternatives rejected.** Per-example selection would make a lesson internally
inconsistent. Varying tie order alone is too close to the known erroneous rival
and can be invisible without ties. Moving the variant into production would mix
rules without approval.

**Probe.** Seed 19 evidence checks two demos plus one query for each setting;
all Python outputs equal exact Racket outputs and every demo refutes the opposite
setting.

**Failure mode/limit.** Only two settings and one episode seed were exercised;
no variant admission is claimed.

## D7 — Restore the frozen fixture and verify around it

**Choice.** Keep `tests/test_generator_1034300a135f.py` byte-identical to the
packet baseline and add portable focused tests/probes elsewhere.

**Rationale.** The assignment explicitly forbids rewriting the frozen fixture.
Its hard-coded parent depth is a library-maintainer migration issue, not a
selected-source defect.

**Alternative rejected.** Leaving the temporary path correction would make the
suite green by violating packet policy and would hide the portability defect.

**Probe.** Restored SHA-256 is
`f130bc77802cb30f1591b113f6b90246e32fb22eab05b95e449f3e6f9738b502`.
The official final task-test preflight reproduces the blocker; the independent
source-bound probe passes 6/6.

**Failure mode/limit.** Completion remains `blocked` until the maintainer migrates
the fixture, even though production gates are green.

## D8 — Retain the exact tie-order counterexample

**Choice.** Keep the smallest final-source JSON reproducer with three public
demos and one combined-profile query.

**Rationale.** It captures the original lesson defect in executable form and
will fail if a future schedule/contract again permits reverse tie order.

**Probe.** Racket receipt at `checks/counterexample-reverse-tie/racket.json` is
bound to the unchanged rule and final generator hash.

**Failure mode/limit.** It demonstrates one rival and one query, not the full
lesson distribution; the census supplies broader evidence.
