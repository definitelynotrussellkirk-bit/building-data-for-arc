# Current notes: 603bd7fff5df

## Current state

- Version: `3.0.1`.
- Final reviewed generator SHA-256:
  `b9c242c596862cfef1335b8a22dea95749bac917dd7f5be0d7ffe0c0dbb8bfba`.
- Canonical rule hash: `539d28e25b24`.
- Active Racket authority changed in this review: **no**.
- Selected-task blockers after repair: **none**.
- Training/variant approval changed by this review: **no**.

## Intended rule

Find all gray (`5`) cells. Let their bounding box be rows `r0..r1` and columns
`c0..c1`. Return columns `c0..c1` and rows `(r0-1)..(r1+1)`. Lawful generated
inputs always provide the required vertical margin.

## Ordinary input distribution

Ordinary scenes stay on the original `{0,5,8}` family. Gray side markers define
one rectangular frame; blue cells provide retained content and outside
nuisance. The public axes are four canonical scene profiles, three placements,
and three side styles. All 36 joint combinations are legal in every band.
Difficulty changes schedule phase and nuisance density, not the rule or legal
axis domain.

Every draw deliberately exposes:

- blue content in the top and bottom retained halo rows;
- blue content inside the gray-defined crop;
- at least one blue distractor outside the crop;
- no paired blue endpoints that would validate `side_endpoint_eights`;
- sparse-side examples that refute `full_side_only`.

The deterministic default curriculum has twelve slots and now declares
`LESSON_SCHEDULE_PERIOD = 12` for exhaustive shared-tool enumeration.

## 3.0.1 repairs

### Strict public request scalars

Version `3.0.0` accepted coercible request values. Baseline defect lint found 48
warnings: booleans/floats/strings as seeds or sample indices, negative indices,
and invalid difficulty values. Version `3.0.1` validates these values before
schedule selection or keyed drawing. Focused regressions are in
`tests/test_review_repairs.py`.

### Lesson contract and rotations

A retained audit counterexample showed that the previous hook rejected 24/48
query rotations because a three-demo subset omitted one side-style label, even
though every declared competitor was already refuted. The old check conflated
axis-label coverage with semantic identifiability.

The current hook requires:

1. at least three lawful demonstrations;
2. correct demonstration and optional query labels;
3. three distinct canonical scene profiles;
4. a query scene profile not repeated in the demonstrations;
5. refutation of every declared task-domain competitor.

It no longer separately requires all side-style labels. This reversal is bound
to the retained counterexample under
`counterexamples/review-ae7bce401b5111fe-v0001/` and the new cyclic-rotation
regression.

## Final evidence

- Strict after battery: 12/12 stages green.
- Defect lint: zero warnings.
- Canonical profile floor: 60/60 exact and 60/60 envelope.
- Strict semantic gate: 600/600.
- Override gate: 3,960/3,960 accepted; unknown keys rejected.
- Racket smoke/mirror parity: 120/120.
- Portable selected-task tests: 20/20.
- Exhaustive declared schedule: 36 lessons (12 starts × 3 bands), 144 labelled
  pairs, and all 144 held-out query rotations clean.
- Random production census: 300 lessons, 1,200 pairs/unique inputs, and all
  1,200 held-out query rotations clean.

Evidence is under `WORK/checks/`; the final source-bound summaries are named in
`REVIEW.md`.

## Native halo-depth parametric family (2026-10-25)

The earlier authoring prototype is now a native reviewer-ready adapter under
`workspace/parametric/`. The episode-fixed parameter is
`halo_depth ∈ {0,1,2}`; depth `1` returns the exact canonical 405-byte Racket
program (SHA-256
`cd8b9b6730035269c89a10e32f91d3ace632cc5cf1a7adc283f68d9f993bb58e`),
depth `0` removes the halo, and depth `2` retains two rows above and below.
The production generator and canonical authority remain unchanged.

The native contract independently supports 2–6 demonstrations and 1–4 queries,
with stable prefixes, matched inputs across settings, four distinct queries, and
a substantive 30×30 fourth query. Constructive halo-ring evidence and five
executable shortcuts make every retained lesson distinguish the setting. A
256-seed audit covered 3,840 episodes and 30,720 labeled pairs over every
supported demonstration count with zero failures. Four public exports excluded
settings, programs, and query answers.

Native protected-Racket qualification passed at 2, 3, and 6 demonstrations:
270 evaluations across 18 setting/seed jobs. The required sequential dependency
is the input-derived gray bounding box consumed by the halo crop. On the exact
qualified 30×30 witness, replacing `[5,3,22,22]` with `[6,3,21,22]` changes the
final output from 22×20 to 20×20; construction and fresh replay both passed.
Current evidence is under `WORK/checks/603bd7fff5df/`. This is reviewer-reported
native-ready work, not owner acceptance or training admission.

## Assumptions and known limits

- The generator intentionally prioritizes high-signal canonical teaching over
  broad visual diversity. It does not cover arbitrary colors, arbitrary sizes,
  top/bottom gray borders, or unrelated textures.
- Four scene profiles are source-family signatures, not a claim that the rule
  cannot generalize beyond them.
- Finite declared-rival censuses do not prove unique induction against every
  possible alternative.
- The post-repair solve bundle used two auxiliary queries; one repeats a scene
  profile and is marked diagnostic-unsupported by the solve preparer. Production
  lesson evidence is three demonstrations plus one query and is clean.
- Native evidence is finite: three parameter settings, two qualification seeds,
  and a bounded rival list. It does not prove universal learnability. Owner-side
  exact-source acceptance and any training admission remain pending.

## Open findings

No open blocker remains for the selected canonical generator. General shared
harness suggestions are recorded in `FEEDBACK_TO_CODEX.md`; peer-audit defects
for other tasks are recorded in `AUDIT.md` and were not edited here.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-41eb0cc00606309b:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `b9c242c596862cfef1335b8a22dea95749bac917dd7f5be0d7ffe0c0dbb8bfba`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/603bd7fff5df/generator.py,unchanged SHA256 b9c242c596862cfef1335b8a22dea95749bac917dd7f5be0d7ffe0c0dbb8bfba. No issue found within bounded source audit:20 tests pass;combined command exits1 solely missing period12 evidence. Separate seed0 followup covers36 starts/144 rotations withzero ambiguity/errors. Two declared canonical rivals andhalo/outside-blue witnesses assessed. Failed aggregate preserved,not rewritten green;target unchanged. No owner audit rerun or new target approval. Target-local receipts: `checks/audit/603bd7fff5df-combined.console.log` `checks/audit/603bd7fff5df-combined.exit` `checks/audit/603bd7fff5df-combined/checks/603bd7fff5df_audit_battery_summary.json` `checks/audit/603bd7fff5df-combined/checks/603bd7fff5df_audit_commands.jsonl` `checks/audit/603bd7fff5df-combined/checks/603bd7fff5df_audit_semantic_gate.json` `checks/audit/603bd7fff5df-combined/checks/603bd7fff5df_audit_semantic_gate.log` `checks/audit/603bd7fff5df-combined/checks/603bd7fff5df_audit_semantic_gate.receipt` `checks/audit/603bd7fff5df-combined/checks/603bd7fff5df_audit_summary.json` `checks/audit/603bd7fff5df-combined/checks/task_tests.xml` `checks/audit/603bd7fff5df-combined/progress.log` `checks/audit/603bd7fff5df-combined/result.json` `checks/audit/603bd7fff5df-schedule-period.console.log` `checks/audit/603bd7fff5df-schedule-period.exit` `checks/audit/603bd7fff5df-schedule-period.json` `checks/audit/603bd7fff5df-schedule-period.summary.json`

### Assessment or prior finding

## 603bd7fff5df

**No issue found in the bounded audit.** I checked assigned source SHA-256
`b9c242c596862cfef1335b8a22dea95749bac917dd7f5be0d7ffe0c0dbb8bfba`.
The portable task-test snapshot passed 20/20 tests. Its combined audit command
then reported a strict-policy warning—not a semantic counterexample—because the
declared 12-slot schedule had not been enumerated by that command. I ran the
requested fixed-seed schedule census separately: all 36 declared starts across
three bands materialized, all 36 production lessons were identifiable, and all
144 held-out query rotations were identifiable, with zero materialization,
hook, or scoring errors. Evidence:
`checks/audit/603bd7fff5df-combined/checks/task_tests.xml`,
`checks/audit/603bd7fff5df-combined/checks/603bd7fff5df_audit_semantic_gate.json`,
and `checks/audit/603bd7fff5df-schedule-period.summary.json`.

I specifically checked the current side-style/scene-profile curriculum, the two
canonical-fitting shortcuts (`side_endpoint_eights` and `full_side_only`), the
halo/outside-blue witnesses, portable API validation, and every declared
schedule residue at seed 0. This finite check does not prove uniqueness against
undeclared rules or all seeds. The target was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `b9c242c596862cfef1335b8a22dea95749bac917dd7f5be0d7ffe0c0dbb8bfba`.

# Decisions for 603bd7fff5df

## D1 — Preserve the canonical crop rule and authority

**Input choice.** Keep the selected transformation unchanged: find the gray
bounding box, keep its columns, and include exactly one source row above and
below its row span.

**Original rationale.** The canonical examples, selected Racket authority, and
existing mirror all agree. The assignment requested a nearby parameterized
prototype, not a replacement canonical rule.

**Alternatives considered.** Infer the rows from blue endpoint pairs; crop only
the gray rows; use nonzero bounds; change the active Racket program to one of
the prototype settings.

**Probes.** Final rule-smoke and authority-sync stages, 120 Racket applications,
120 mirror-parity checks, and the source-bound shortcut witness.

**Decision.** No active Racket or canonical-data edit. `RULE_HASH` remains
`539d28e25b24`.

**Failure modes and limits.** Agreement on sampled lawful inputs does not prove
the mirror equivalent for every malformed grid. The production validator and
Racket authority remain the source of truth.

## D2 — Reject coercible request scalars before deterministic drawing

**Input choice.** Require `type(seed) is int`, `type(sample_index) is int`, a
nonnegative sample index, and `difficulty` in `{None, easy, medium, hard}`.

**Original rationale.** Version `3.0.0` relied on downstream coercions. The
baseline defect linter reported 48 accepted-invalid-scalar warnings across
three bands.

**Alternatives considered.** Silently coerce integral floats and numeric
strings; accept booleans as integers; validate only inside `gen_ctx`; suppress
the lint warnings.

**Probe.** A failing test was written first for booleans, floats, strings,
negative indices, and invalid difficulties. After the implementation, the
focused tests and defect-lint stage passed.

**Decision.** Validate at the public entry boundary, before schedule selection
or any keyed draw. Version advanced to `3.0.1`.

**Failure modes and limits.** This validates request scalars, not arbitrary
objects nested inside future override types. Current override axes are strings
and already use exact-choice validation.

## D3 — Make rival refutation authoritative for lesson validity

**Prior choice.** The lesson hook required all three `side_style` values in
every three-demo subset, in addition to refuting every declared competitor.

**New choice.** Keep the requirements for three lawful demonstrations, three
distinct scene profiles, a held-out scene profile, correct labels, and explicit
rival refutation. Remove the redundant requirement that every demo subset
cover all three side-style labels.

**Reason.** The retained current-source counterexample showed 24/48 cyclic
rotations rejected solely because one side style was absent, while every
declared rival was already refuted. That was a contract/schedule mismatch,
not ambiguous teaching.

**Alternatives considered.** Restrict downstream assembly to fixed query
positions; redesign the 12-slot schedule so every three-of-four subset contains
all side styles; keep the false-negative hook and ignore rotation support.

**Probe.** `test_every_cyclic_four_pair_rotation_is_identifiable`, exhaustive
12-start × 3-band schedule census with every query rotation, and a 300-lesson
random census.

**Decision.** Refutation of the declared task-domain competitors is the
teaching criterion. Axis labels are curriculum coverage, not independent proof
obligations once the shortcuts they represent are falsified.

**Failure modes and limits.** An undeclared plausible rival could still survive.
The finite rival list is therefore reported as bounded evidence, not proof of
unique induction.

## D4 — Declare the finite default schedule period

**Input choice.** Add `LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES) = 12`.

**Original rationale.** The deterministic schedule already had twelve slots,
but shared tooling could not discover that period and therefore could not
exhaustively enumerate every start.

**Alternatives considered.** Leave the period implicit; hard-code `12` only in
a review script; infer it from internal implementation details.

**Probe.** Focused declaration test and shared `lesson-census
--enumerate-schedule-period --schedule-seed 1234` across all three bands.

**Decision.** Publish the existing finite period as a machine-readable contract.

**Failure modes and limits.** The shared census currently reports its generic
pair-residue period separately; maintainers should use the declared period and
source-bound receipt when evaluating complete schedule coverage.

## D5 — Keep `halo_depth` as a separate parametric prototype

**Input choice.** Parameterize the number of rows retained above and below the
gray bounding box with allowed values `0`, `1`, and `2`; choose one value once
per complete episode. The canonical/default value is `1`.

**Original rationale.** This changes executed semantics while preserving the
family’s object roles and reasoning structure. It is more meaningful than a
color reskin or sampling-only parameter.

**Alternatives considered.** Vary retained columns, use arbitrary large depths,
parameterize colors, or alter production generation directly.

**Probe.** Exact Racket materialization for each setting, protected-Racket
execution of 12 episode pairs under all three settings, Python/Racket parity,
and tests that every retained demonstration distinguishes all values.

**Decision.** Retain the runnable code and artifacts under
`workspace/parametric/`, but do not connect them to the selected production
path or approval metadata.

**Failure modes and limits.** Output height makes these bounded settings easy to
distinguish, and the evidence covers one seed. The prototype is proposed, not
approved.

## D6 — Preserve the frozen fixture and make prototype loading portable

**Prior choice / failed iteration.** Reviewer regressions were initially added
to the frozen root test file, and the prototype called `load_selected_generator`
again from within the portable task-test snapshot. The portable harness had
already loaded runtime modules from its copied tree, so the second loader
correctly detected mixed roots. The first portable run passed 18/20.

**New choice.** Restore the frozen fixture byte-for-byte, put all new tests in
separate files, and import the exact task-local or `GENERATOR_UNDER_TEST` source
while reusing the process’s already-selected runtime package.

**Alternatives considered.** Disable the anti-mixing guard; modify the frozen
fixture; skip portable tests; import private repository aliases.

**Probe.** Seven focused local tests, source-hash check of the fixture, the
protected parametric verifier, and a new portable selected-task snapshot.

**Decision.** Keep the guard intact and fix the task-local loader. Final portable
result is 20/20.

**Failure modes and limits.** This pattern is task-local. A shared helper for
“the generator already selected by this portable harness” would be less easy
to misuse; see F1 in `FEEDBACK_TO_CODEX.md`.
