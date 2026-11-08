# Working notes: f7660051ec70

## Current design (version 4.0.0)

The canonical task is unchanged: color-1 closed rectangular frames are processed independently. If a frame interior contains at least one color-2 seed, every remaining interior color-0 cell becomes color 3; an unseeded frame is a decoy and remains unchanged. The selected Racket authority was not edited. `RULE_HASH = "3efd212303b7"` pins the normalized canonical rule, whose retained source SHA-256 is `f38ae25adfd79186f55cd3037ceb11e921f488b5c59eb1f14d5a994693cb394e`.

Ordinary generation now has five exact, observable axes only: `grid_h` 9..26, `grid_w` 11..26, `n_seeded_frames` 1..2, `n_decoy_frames` 1..2, and `seed_count` 1..2. Unknown, mistyped, non-integer, and out-of-range overrides fail closed. Every generated grid has one or two seeded frames, one or two unseeded decoys, separated color-1 rectangular components, and at least one visible fill target in each seeded frame. Input colors remain the canonical fixed roles 0/1/2.

The default canvas distribution uses an exact canonical profile on three of four draws and a band-dependent broader profile on one of four draws. Frames are placed in up to four separated slots so the minimum 9x11 canvas remains constructive at every advertised frame-count combination. This deliberately favors canonical sizes without reducing the task to a fixed-size shortcut.

## Reversed decisions and evidence

### Advertised generic axes → exact task-domain axes

Prior source version 3.1.0 advertised dimensions and palette/texture controls that `generate()` ignored; even an unknown misspelled key returned the same bytes. That was reproduced from audit return `review-ec130d3b60baa621:v0001` and again under `checks/baseline-repro/override-audit.txt`. The new choice removes nonsemantic palette aliases, implements every retained axis exactly, and rejects unknown keys. Evidence: the final compact override stage is green in `checks/after/checks/f7660051ec70_after_override.log`, and task-local boundary/unknown-key tests pass.

### Independent seed multiplicity → two-slot teaching schedule

Prior source version 3.1.0 could emit three easy demonstrations whose seeded frames all had exactly one seed, allowing an “activate only when there is exactly one seed” rival to fit every demonstration and fail on a lawful two-seed query. The retained lead was audit return `review-e4e5273a823f4fd2:v0001`; the exact seed-0 indices 51..54 replay is under `checks/baseline-repro/lesson-ambiguity-audit.txt`. The new default schedule alternates one-seed and two-seed profiles with `LESSON_SCHEDULE_PERIOD = 2`; therefore every three consecutive demonstration pairs expose both multiplicities. The declared rivals are `exactly_one_seed` and `fill_all_frames`.

### Output-only confidence → structural contract

The previous source had no source-bound `self_check`, no pinned rule hash, and no executable lesson competitors. Version 4.0.0 parses color-1 components as exact closed rectangular outlines, assigns each seed to exactly one frame interior, validates frame/seed counts and fill targets, exposes exact axis observations, rejects malformed impostors, mirrors the simple rule for tests, and declares witness-to-rival mappings. The Racket implementation remains the label authority.

## Final evidence

Final generator SHA-256: `ebf6a3812da68f57f361fa3058c190d4da0828a28b429c6d578dbe1976a20b5a`.

- Test-first receipt: before implementation, the new contract produced 51 failures and 2 passes (`checks/tdd-red/result.json`).
- Final task-local contract: 53/53 tests pass, covering canonical parity, exact axes, fail-closed overrides, schedule windows, semantic rivals, malformed grids, Racket authority, determinism, and hash-seed stability.
- Full after battery: 12 green, 0 advisory, 0 failed, 0 interrupted, 0 pending (`checks/after/checks/f7660051ec70_after_battery_summary.json`), with required query rotations enabled.
- Random production census: 300 lessons (100 per easy/medium/hard), 1,200 materialized pairs/query rotations, 1,197 unique inputs, zero ambiguity, materialization errors, hook warnings, or scoring errors (`checks/lesson-census.json.gz`; restoration metadata in `checks/COMPRESSED-EVIDENCE.json`).
- Declared schedule census: both period residues across all three bands at seed 0, six lessons and 24 query rotations, zero ambiguity or errors (`checks/lesson-schedule-period.json`).
- Exposed post-repair solve: three visible demonstrations passed on revision 1; earlier rule exposure was declared and no reference was consulted during the solve (`solve/summary.json`).

## Known limits and open findings

The semantic checks are finite: they refute the two declared plausible rivals but do not prove unique induction against every imaginable program. The period census exhausts start residues only for seed 0, while the random census samples 100 lessons per band. Geometry is intentionally restricted to disjoint axis-aligned frames, at most four total, with fixed canonical color roles; overlapping/nested frames and color permutations are outside this generator domain. No blocking finding remains for the selected task.

## Current audit resolution

Exact v4.0.0 repair rejects ignored/unknown legacy controls and implements five observable exact axes; period-two seed schedule supplies one- and two-seed demonstrations and decoys. Reviewer reports 53/53 focused tests, 12/12 strict battery, 300 lessons/1200 rotations and both period starts. Resolves these two concrete baseline findings only.

Closure is reviewer-reported on the exact repaired source. Detailed current assessment: `evidence/current-audit-assessment.json`.
## Current reviewer considerations

Source SHA-256: `ebf6a3812da68f57f361fa3058c190d4da0828a28b429c6d578dbe1976a20b5a`.

# Decisions for f7660051ec70

## D1 — Keep the canonical Racket rule unchanged

**Prior choice.** The selected baseline had no declared `RULE_HASH`; its Python generator nevertheless targeted the canonical seeded-frame transformation. The original rationale for omitting the hash is unknown.

**New choice.** Pin normalized rule hash `3efd212303b7` and leave the selected Racket source byte-for-byte unchanged.

**Reason and probes.** Canonical examples and the baseline rule smoke established the intended transformation. The defect was in input generation and lesson assembly, not the authority. Final `racket_lint`, `authority_sync`, `rule_smoke`, canonical tests, and task-local Racket comparisons all pass in the 12-stage battery.

**Rejected alternative.** Editing the rule to require exactly one seed would have made the ambiguous old lessons easier, but would contradict the canonical two-seed example and preserve the shortcut rather than repair the teaching data.

**Limit.** The Python mirror is test support only; it is not a second label authority.

## D2 — Replace generic/fictional axes with five observable task axes

**Prior choice.** Version 3.1.0 advertised dimensions through 26 and palette/texture controls, but the source ignored the entire override dictionary. The associated rationale is unknown. At seed 1729/sample 4, dimensions, warm/cool palette requests, and an unknown misspelling all returned the same 15x15 bytes.

**New choice.** Retain only `grid_h`, `grid_w`, `n_seeded_frames`, `n_decoy_frames`, and `seed_count`. Each has a structural observer and an exact override path. Reject unknown names, `None`-free invalid values, booleans/non-integers, and out-of-range values.

**Alternatives considered.** I considered implementing color/palette variation. I rejected it because the canonical rule assigns fixed semantic roles to colors 1, 2, and 3; a “warm/cool” axis would either be dead or would require a role-aware Racket change and color-permutation evidence. I also considered keeping a generic `texture` axis, but it had no task-domain meaning.

**Probes.** `checks/baseline-repro/override-audit.txt`; task tests for every low/high boundary in every band; compact override stage in `checks/after`; unknown/obsolete-key tests.

**Failure modes and limits.** Only exact integral controls are supported. Callers expecting the obsolete palette controls now receive a loud error rather than silent fallback.

## D3 — Use a constructive 9..26 × 11..26 canvas domain

**Prior choice.** The old metadata claimed broad ranges but did not honor them. It also provided no evidence that joint boundary combinations were constructible.

**New choice.** Height is 9..26 and width is 11..26. A one-cell separator divides the canvas into four slots; even the 9x11 minimum yields four 4x4 slots. Up to four frames can therefore be placed without rejection for every legal frame-count combination.

**Alternatives considered.** A rejection sampler around random rectangles was simpler, but could make lawful exact overrides probabilistic or hang near boundaries. A larger minimum would simplify geometry but needlessly narrow the canonical envelope. Nested/overlapping frames were excluded because ownership semantics become ambiguous and are absent from the canonical task.

**Probes.** Exhaustive boundary matrices in task tests, override gate, `self_check`, and deterministic generation across difficulties.

**Failure modes and limits.** The slot grammar is intentionally narrower than all mathematically lawful arrangements: frames are disjoint and separated, not nested or touching.

## D4 — Anchor most defaults to exact canonical profiles

**Prior choice.** The baseline had no measurable canonical-profile policy.

**New choice.** Three of four default draws select one exact canonical size pair: 10x12, 11x13, or 12x14. One of four draws explores a wider band-dependent range. Canonical dimensions are correlated as pairs rather than independently sampled inside an envelope.

**Reason.** The profile-floor gate asks for exact profile support, not merely dimensions that surround the canonical range. The 75/25 mixture gives each band dependable canonical anchors without teaching a fixed-size rule.

**Alternatives considered.** Always canonical would maximize profile hits but create a size shortcut. Fully uniform dimensions would broaden diversity but make exact canonical hits sparse and unstable in 20-draw gates.

**Probes.** `profile_floor`, `dist_gate`, diversity, and 240 default-draw task probes.

**Failure modes and limits.** This is a curriculum weighting, not an estimate of the original ARC data distribution.

## D5 — Guarantee both seeded and unseeded frames

**Prior choice.** Baseline draws included seeded and decoy frames but lacked a structural validator and exact count controls.

**New choice.** Generate one or two seeded frames and one or two unseeded decoys. Frame roles are shuffled across slots. Every seeded frame has at least one remaining zero interior cell, and every seed lies strictly inside exactly one frame.

**Reason.** A seeded witness teaches activation; a decoy refutes “fill every frame.” Exact counts make distribution audits and joint overrides falsifiable.

**Alternatives considered.** Optional decoys were rejected because a lesson without a decoy supports the fill-all rival. More than four frames would require a different minimum-canvas construction and is unnecessary for this rule.

**Probes.** Structural mutation tests, `fill_all_frames` rival, self-check power, override contract, semantic gate.

**Failure modes and limits.** The domain does not include all-seeded or all-empty scenes, even though such individual grids could be reference-lawful; they are weak teaching examples and intentionally excluded.

## D6 — Alternate one-seed and two-seed profiles with period 2

**Prior choice.** Seed counts were independent random draws. Audit return `review-e4e5273a823f4fd2:v0001` found seed 0/easy indices 51–53 all used one seed, while query 54 used two; an exactly-one rival fit all three demonstrations and changed the query.

**New choice.** `schedule_profile()` alternates `one_seed` and `two_seed` by sample index, with `LESSON_SCHEDULE_PERIOD = 2`. All seeded frames within one generated grid share the scheduled count. Every three consecutive demonstration pairs therefore contain both profiles.

**Alternatives considered.** Rejection-sampling complete lessons until both counts appear would couple the single-grid generator to downstream assembly and obscure replay. Random per-grid balancing would reduce but not eliminate the counterexample. Putting one one-seed and one two-seed frame in every grid would be maximally explicit but would collapse the seed-count axis and reduce lesson variety.

**Probes.** Exact old counterexample replay; every consecutive three-sample window across multiple seeds/bands in task tests; strict semantic gate; 300-lesson random census; complete fixed-seed period census across both residues and all query rotations.

**Failure modes and limits.** The schedule guarantees the named distinction but cannot rule out undeclared hypotheses. Fixed-seed period enumeration does not prove behavior for every seed, though seed does not affect the profile function.

## D7 — Declare executable rivals and witnesses

**Prior choice.** No source-bound semantic contract existed.

**New choice.** Declare `exactly_one_seed` and `fill_all_frames` competitors, with `two_seed_frame` and `unseeded_decoy` witnesses and explicit witness-to-rival bindings. `lesson_identifiable` scores complete demos and the held-out query.

**Reason.** Correct labels per grid do not guarantee that a complete training lesson teaches the intended conditional rule. Executable rivals make that defect reproducible.

**Alternatives considered.** A prose-only warning was rejected because it cannot gate or replay. An unbounded program search was rejected as expensive and difficult to interpret; the finite rival set targets the observed high-risk shortcuts.

**Probes.** Strict semantic battery with required rotations, random census, period census, and direct task tests.

**Failure modes and limits.** Passing two rivals is not a uniqueness proof. Other spatial or color-based shortcuts may exist.

## D8 — Add an independent structural probe and test-first contract

**Prior choice.** There were no selected task tests and no independent observer.

**New choice.** Add `workspace/reference_probe.py` with a portable canonical-data locator, independent frame parser, intended oracle, and rivals. Add 53 task tests before implementation; the red receipt was 51 failures/2 passes.

**Reason.** Reusing production parsing in every test would allow the same bug to agree with itself. The probe gives future agents a compact, reusable way to inspect frames and compare rivals without importing private runners.

**Alternatives considered.** Embedding all helpers in the test file would work but make reuse and audit scripts harder. Modifying shared tools was outside the allowed task delta.

**Probes.** Official portable `task_tests` stage, real Racket authority comparisons, hash-seed subprocesses, and fresh-copy replay.

**Failure modes and limits.** The independent parser still encodes the same documented rectangular-frame domain; it is not an independent human annotation set.

## D9 — Retain failed and interrupted evidence honestly

The first full before battery was stopped by the foreground execution cap while entering `dist_gate`; the saved result remains `running` and is not called a pass. The first full after invocation was similarly interrupted after three green stages, then completed with the battery's native source/settings-checked `--resume` path. Focused baseline reproductions and the TDD-red receipt preserve the actual pre-fix failures. Large receipts are compressed with SHA/size/restoration metadata instead of discarded.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-992496e58d2560ee:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ebf6a3812da68f57f361fa3058c190d4da0828a28b429c6d578dbe1976a20b5a`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported bounded clean assessment on the unchanged audited source. 53 reported tests plus fixed-seed period2 census:6 lessons/24 query positions; shared coverage warning discharged by supplemental reviewer receipt, not a new owner semantic run. Original report and evidence retained. Training admission unchanged.

### Assessment or prior finding

## f7660051ec70

**No issue found in the audited generator bytes.** The audited source SHA-256
was `ebf6a3812da68f57f361fa3058c190d4da0828a28b429c6d578dbe1976a20b5a`.
I checked its current portable task suite (53/53 passed), 600 strict semantic
draws, all three canonical inputs, both declared witness/rival claims, 12/12
lessons, and 0/48 smoke-test rotation ambiguities.

The combined audit command exited nonzero only because the shared semantic gate
warns whenever a declared fixed period is not enumerated inside that command.
I then ran the prescribed period-two census at fixed seed 0 across easy,
medium, and hard. It exhaustively covered all 6 band/start-residue lessons and
all 24 query positions, with 0 production or rotation ambiguities and no hook or
scoring errors. I therefore classify the warning as shared-tool workflow noise,
not a reproduced task defect.

Evidence:

- `checks/audit/f7660051ec70-combined/result.json`
- `checks/audit/f7660051ec70-combined/checks/f7660051ec70_audit_semantic_gate.log`
- `checks/audit/f7660051ec70-schedule-period.json`

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
