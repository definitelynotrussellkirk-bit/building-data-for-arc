# Current account: bdd177308a5b v3.1.0

## Intended rule

A color-5 L-frame encloses a small template object in its upper-left compartment. Among the external cardinally connected colored objects, exactly one has the same normalized cell coordinates in the same orientation. Recolor that translated exact match to 5; rotations/reflections and differently sized objects remain unchanged.

## Current generator decisions

- Public scalar arguments are validated before `gen_ctx`: `seed`, `sample_index`, and integer overrides require exact integers (booleans and floats are rejected); difficulty and string overrides require exact declared strings; unknown overrides are rejected.
- Default dimensions retain the advertised 10–14 override domain, but use a weighted 10×10 anchor so canonical-profile support appears in every difficulty band. The final 20-draw-per-band gate measured 19/60 exact-profile and 19/60 envelope hits.
- `strict_canonical_like` accepts canonical examples. `orientation_near_miss` witnesses a rotated/reflected decoy, and `dihedral_invariant_all` is an executable semantic rival and lesson competitor. It is deliberately **not** a canonical shortcut because it fits only 2/8 canonical pairs.
- The active selected `racket_target.target_code` fields were synchronized to canonical exact text. Archival `raw_code` remains byte-for-byte unchanged; rule semantics and declared rule hash `5b8904c8dace` did not change.

## Parametric extension

`workspace/parametric/` contains a proposed, unapproved episode prototype with one once-per-episode parameter: `match_relation ∈ {exact, quarter_turn_cw}`. The canonical default is byte-identical to the selected exact rule. Two retained seeds cover both settings; each has three demonstrations and one query, and the alternate setting is refuted by every demonstration. This prototype is authoring evidence only and does not alter production generation or approval.

## Final evidence and limits

- Final generator SHA-256: `3e207704a49b6f341c1cb9fc7604a16394eee391f83cf47331dd0a224d9b0650`.
- Final battery: 12/12 stages green (`checks/after-final/`).
- Focused tests: 20 repair tests and 5 parametric tests pass.
- Lesson census: 300 materialized lessons (100 per band), 1,200 unique inputs/pairs, 0 production ambiguities, and 0/1,200 rotated-query ambiguities against the declared orientation rival. This finite census is not a universal identifiability proof.
- Remaining inherited blocker: frozen root fixture `tests/test_generator_bdd177308a5b.py` uses a fixed `__file__.parents[...]` canonical path and fails portable preflight before task-test execution. It was not edited, per assignment policy. New focused tests pass separately.
## Current reviewer considerations

Source SHA-256: `3e207704a49b6f341c1cb9fc7604a16394eee391f83cf47331dd0a224d9b0650`.

# Decisions and probes

## Evidence policy

I treated the packet baseline and commands as authoritative measurements. No prior selected-task return was used as a substitute for rerunning the baseline. The retained prior audit for peer target `38eaf32b0d29` was used only as a lead, then independently reproduced against its current hash.

## D1 — validate public scalar types before context construction

**Prior choice:** rely on `gen_ctx` coercion/validation. **New choice:** `_validate_generate_args` rejects non-exact scalar types and unknown overrides before they reach `gen_ctx`.

Reason: baseline `defect_lint` produced 120 accepted-invalid warnings, including `distractor_count=4.75`. The focused red suite reproduced booleans/floats for seed, sample index, integer controls, and non-exact string values. Minimal exact-type validation fixed the source rather than special-casing one value. Evidence: `checks/repair-tests-red.log`, `checks/repair-tests-final.log`.

Rejected alternative: silently cast numerics. That preserves the baseline defect and obscures malformed authoring calls.

## D2 — weight, rather than shrink, the default dimension domain

**Prior choice:** roughly uniform dimensions 10–14, yielding exact-profile support only in easy (3/20) and none in medium/hard. **New choice:** retain all exact overrides 10–14 but sample from a weighted list with six copies of 10 and one each of 11–14.

Reason: canonical inputs are 10×10 or 10×11-like, and the gate requires support in every band. Weighting reaches 19/60 exact/envelope hits without deleting hard examples or making an advertised override unreachable. A focused test enumerates every size value in every band. Final evidence: `checks/after-final/checks/bdd177308a5b_after_profile_floor.log`.

Rejected alternative: clamp all defaults/overrides to 10. It would satisfy the profile floor by restricting the generator and would violate observable override semantics.

## D3 — encode orientation as an executable teaching distinction

Added `strict_canonical_like`, witness `orientation_near_miss`, and rival `dihedral_invariant_all`. The witness detects a non-exact-orientation decoy; the rival recolors every translated rotation/reflection match and therefore predicts extra changed cells.

The first registry decision placed the rival in `CANONICAL_SHORTCUTS`. The semantic gate proved that declaration false: it mismatched 6/8 canonical pairs. I changed the classification, not the callable: it remains in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS` but `CANONICAL_SHORTCUTS` is empty. A red test first asserted the corrected registry. The final semantic gate and 300-lesson census pass.

Limit: finite declared-rival checks do not prove no other plausible rule survives.

## D4 — synchronize active authority while preserving history

Used the prescribed dry-run/apply workflow to copy canonical `program_solution` text into only the two selected active `racket_target.target_code` fields. Only those JSON pointers changed. Archival `raw_code` remains unchanged, and execution parity passed before and after.

Reason: the baseline authority gate required exact active-source identity, not merely whitespace-normalized equivalence. Evidence: `checks/authority-sync-proposal.json`, `checks/authority-sync-apply.log`, and final authority report.

Rejected alternative: rewrite `raw_code` too. The return guide explicitly identifies it as archival and requires preservation.

## D5 — parameterize the matching relation, not cosmetic axes

The proposed extension samples `match_relation ∈ {exact, quarter_turn_cw}` once per episode. The exact setting is byte-identical to canonical source; the alternative changes one guarded comparison. Four lawful fixtures each contain distinct exact and clockwise-quarter-turn candidates, so every demonstration distinguishes the chosen relation.

Reason: this changes the reasoning relation while preserving the L-frame, template, decoys, output color, and canonical default. Color, grid size, or distractor-count parameters would merely change surface statistics already handled by the production generator.

Evidence: `workspace/parametric/`, `checks/parametric/match-relation-v1/report.json`, and 5 passing prototype tests. Status remains `proposed_unapproved`.

## D6 — preserve the inherited frozen-fixture failure

The required portable `task_tests` stage fails before collection because the frozen root test guesses a canonical path from `__file__.parents`. Assignment policy forbids editing that fixture, so I retained the failure and marked the return blocked. New tests use portable helpers and pass separately.

Rejected alternative: patch the frozen test or suppress its preflight. Either would violate the explicit handoff contract and hide a maintainer-owned migration.

## Remaining limits

- The census covers 300 generated lessons and one declared orientation rival, not all conceivable hypotheses or every cyclic schedule.
- The prototype uses four authored fixtures and two retained seeds; it is not a production distribution.
- The post-repair solve has masked query labels, so only 3/3 visible-example execution is reported.
- Training approval/admission is unchanged.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-db4731ef9a7fbbba:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3e207704a49b6f341c1cb9fc7604a16394eee391f83cf47331dd0a224d9b0650`. At disposition, audited bytes match the current source.

### Current decision

Audited source repo/generators/bdd177308a5b/generator.py SHA256 3e207704a49b6f341c1cb9fc7604a16394eee391f83cf47331dd0a224d9b0650. I sampled 300 generated inputs, 100 per difficulty band, spanning 286 unique
grids. Every draw passed `self_check` and observable-axis recovery, contained a
required orientation near miss, and caused the declared dihedral-invariant rival
to disagree with the exact-orientation target output. All canonical inputs also
passed the current grammar. I additionally inspected strict scalar validation,
placement/backtracking, exact normalized-shape matching, zone coverage, and the
mandatory same-size/different-size decoys. I did not find a concrete execution,
grammar, or declared-rival teaching defect.

This is a finite adversarial sample, not a proof against every imaginable
shortcut. No source was edited as part of this audit.

Evidence: `checks/audit/bdd177308a5b/sampling.json` and
`checks/audit/summary.json`.
 Scoped reviewer report;no owner audit rerun,source edit,approval or training admission. Exact receipts: `checks/audit/bdd177308a5b/sampling.json` `checks/audit/probe.py`

### Assessment or prior finding

## bdd177308a5b

**No issue found.** Current generator SHA-256:
`3e207704a49b6f341c1cb9fc7604a16394eee391f83cf47331dd0a224d9b0650`.

I sampled 300 generated inputs, 100 per difficulty band, spanning 286 unique
grids. Every draw passed `self_check` and observable-axis recovery, contained a
required orientation near miss, and caused the declared dihedral-invariant rival
to disagree with the exact-orientation target output. All canonical inputs also
passed the current grammar. I additionally inspected strict scalar validation,
placement/backtracking, exact normalized-shape matching, zone coverage, and the
mandatory same-size/different-size decoys. I did not find a concrete execution,
grammar, or declared-rival teaching defect.

This is a finite adversarial sample, not a proof against every imaginable
shortcut. No source was edited as part of this audit.

Evidence: `checks/audit/bdd177308a5b/sampling.json` and
`checks/audit/summary.json`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
