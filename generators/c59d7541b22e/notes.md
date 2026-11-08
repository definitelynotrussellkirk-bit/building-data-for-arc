# Current notes: `c59d7541b22e`

## Intended rule

Perform one simultaneous pass over the **original** input. For every 2×2 window containing exactly three cells of one nonzero color and one black cell, fill the black cell with that color. Newly filled cells do not trigger additional completions during the same application. The selected Racket authority is unchanged and pinned by `RULE_HASH = "014f3ef40cee"`.

## Current generator (`v3.0.2`)

- Final generator SHA-256: `3c01af7a3a8e8e8dab0d37ab19cf0aa3cb42b463790026feaf4f3859adbea16f`.
- Two separated components, distinct nonzero colors, black background.
- `canonical` profile: two D4-transformed L-triominoes.
- `witness` profile: one overlapping-two-window zigzag plus one one-pass cascade trap.
- Exact controls: `grid_h` 7–14, `grid_w` 7–16, and `profile` `canonical|witness`.
- Default schedule: `canonical`, `witness` alternating by `sample_index % 2`.
- Lesson policy: four demonstrations followed by one query; arbitrary one-of-five query holdouts are supported.

## Decision reversal

The baseline choice was isolated L-triominoes with broad advertised texture/count/palette controls. That distribution was replaced because its controls were often dead or unobservable, its validator accepted non-task impostors, and both “fill component bounding boxes” and “iterate completion to stability” fit every canonical and generated example. The new witness profile explicitly separates those rules and also refutes “one fill per component.”

An intermediate schedule based on `seed + sample_index` was also reversed: the shared defect probe uses equal seed/index values, canceling parity and hiding witness/difficulty coverage. The final schedule depends only on `sample_index`; the regression is retained in `tests/test_review_contract.py`.

## Evidence

- Final battery: 12/12 green at `checks/after-final/`.
- Focused task tests: 73 passed at `checks/task-tests-final/`.
- Required semantic rotations: 0/60 ambiguous at `checks/required-rotations-final/`.
- Random census: 300 lessons, 1,500 pairs/rotations, 1,500 unique inputs, zero declared-rival ambiguity at `checks/lesson-census-final.json`.
- Declared-period census: all 6 band/residue starts and 30 rotations, zero ambiguity at `checks/schedule-census-final.json`.
- Minimal/replayable shortcut case: `counterexamples/one-pass-vs-shortcuts.json`.

## Known limits and open findings

The curriculum grammar intentionally covers exactly two separated components and only three motif families; the reference rule itself applies more broadly. Census results are finite evidence against the three declared rivals, not universal uniqueness. No task-local blocker remains, and no reference-rule edit was made. The retained associated-notes file was empty, so no earlier return was used as a lead.
## Current reviewer considerations

Source SHA-256: `3c01af7a3a8e8e8dab0d37ab19cf0aa3cb42b463790026feaf4f3859adbea16f`.

# Decisions for `c59d7541b22e`

## D1 — Keep the selected authority unchanged

**Decision.** Preserve the canonical Racket/reference rule and pin its normalized hash as `RULE_HASH = "014f3ef40cee"`.

**Reason.** An independent Python oracle reproduced all three official input/output pairs: inspect each 2×2 window in the original input; when it contains exactly three cells of one nonzero color and one black cell, fill that black cell. All completions are simultaneous. The source defect was curriculum/contract quality, not a demonstrated authority error.

**Alternatives rejected.** I did not broaden or rewrite the Racket rule, because that would change task semantics without evidence. Authority synchronization and rule smoke remain green.

## D2 — Replace fictitious controls with three exact, observable axes

**Prior choice.** The baseline advertised many controls (`texture`, density/palette/count variants, position bias), several of which were ignored, degenerate, incompatible without declarations, or absent from default draw provenance.

**New choice.** Advertise only:

- `grid_h`: exact integer 7–14;
- `grid_w`: exact integer 7–16;
- `profile`: exact enum `canonical|witness`.

Every product is constructively satisfiable in every difficulty band, unknown keys and invalid types/ranges fail loudly, and `observe_overrides` reconstructs all three values from the grid.

**Evidence.** The baseline override stage failed with thousands of findings; the final override stage is green. Parametrized task tests cover boundary/cross-product values, malformed requests, and observation.

## D3 — Use a narrow structural grammar rather than random noise

**Decision.** Ordinary generated inputs contain two non-touching, differently colored monochrome components on a black background. Permitted component signatures are all D4 transforms of an L, an overlapping-window `multi` shape, and a one-pass `cascade` shape.

**Reason.** This keeps each example visually legible and makes the intended local operation—not texture or object-count noise—the source of difficulty. Exactly two components also mirrors every official input while allowing a compact witness scene.

**Rejected alternatives.** More components and arbitrary connected polyominoes would increase diversity but complicate conflict prevention, validation, and lesson interpretation without adding evidence needed for this repair. Keeping only isolated Ls was rejected because it leaves strong shortcuts answer-equivalent.

**Limitation.** The grammar is narrower than the full rule domain. It validates curriculum instances, not every grid on which the reference program could execute.

## D4 — Alternate canonical and shortcut-refuting profiles

**Canonical profile.** Two independent L-triominoes, preserving the official visual idiom and exact-profile support.

**Witness profile.** One four-cell zigzag has two overlapping eligible 2×2 windows, so both missing corners must fill simultaneously. A separate four-cell cascade has one eligible window whose fill would enable a second window only on a forbidden later pass.

**Reason.** Together these components refute three plausible rivals:

1. fill every connected component’s bounding box;
2. repeatedly apply completion until stable;
3. fill at most one missing corner per component.

The minimal cascade counterexample and an exact generated replay are retained in `generators/c59d7541b22e/counterexamples/one-pass-vs-shortcuts.json`.

## D5 — Four demonstrations, one query, arbitrary holdout position

**Decision.** Set `EXAMPLES_NEEDED = 4`; use a deterministic period-2 profile schedule indexed only by `sample_index`; allow any of five materialized pairs to be held out as the query.

**Reason.** A five-pair alternating window contains either two or three witness examples. Removing any one still leaves at least one witness, so every declared rival is refuted by the remaining four demonstrations. This supports both ordered production and arbitrary query rotations.

**Intermediate failure and correction.** The first draft used `(seed + sample_index) % 2`. The defect detector probes `seed == sample_index`, causing parity cancellation and all-canonical samples; declared dimension spans and difficulty effects looked dead. I changed scheduling to `sample_index % 2` and added `test_default_probe_path_exercises_declared_span_and_noninert_difficulty` before the source change.

**Evidence.** Required semantic rotations: 0/60 ambiguous. Random census: 300 lessons, 1,500 holdouts, 0 ambiguities. Period census: all 6 band/residue starts, 30 holdouts, 0 ambiguities.

## D6 — Preserve canonical anchors while making difficulty meaningful

**Decision.** Canonical defaults choose 7×7 or 8×8. Witness defaults use easy 7–9 × 7–10, medium 9–12 × 9–13, and hard 11–14 × 13–16. Explicit dimensions override those defaults exactly and remain band-independent.

**Reason.** Canonical anchors satisfy the profile-floor requirement. Difficulty changes canvas scale rather than rule semantics, while explicit axes retain a simple exact contract.

**Alternatives rejected.** Difficulty-dependent object counts or additional motifs would confound semantic teaching. Restricting explicit dimensions by band was rejected because it would create unnecessary incompatibility declarations.

## D7 — Make validation semantic and immutable

**Decision.** `strict_canonical_like` and `self_check` validate rectangular ARC grids, dimensions, two components, shape signatures, separation, distinct colors, eligible windows, non-conflicting targets, and requested override observation. `rule_mirror` reads only the original input and writes to a copy.

**Reason.** The baseline self-check mostly counted nonzero cells and accepted full grids, lines, and solid blocks. Structural analysis makes failures diagnostic and prevents accidental identity examples, cross-color trigger conflicts, mutation, row aliasing, and iterative semantics.

**Evidence.** Focused tests include official-pair oracle checks, malformed grids, random-state purity, non-aliased rows, and exact output comparisons; final self-check, grammar, rule-smoke, and authority stages are green.

## D8 — Declare executable rivals and witnesses

**Decision.** Expose `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`; `lesson_identifiable` requires at least four correctly labelled lawful demonstrations and rejects any surviving declared competitor.

**Reason.** The two strongest rivals fit every official pair, so canonical correctness alone cannot establish a teachable generated lesson. Executable contracts let the shared semantic gate and lesson census verify actual disagreements rather than prose claims.

**Intermediate failure and correction.** The first `WITNESS_RIVALS` draft stored function objects. The semantic gate correctly required non-empty lists of names. I fixed the schema and added an exact regression test.

## D9 — Verification scope and limits

The final generator hash for every reported final check is `3c01af7a3a8e8e8dab0d37ab19cf0aa3cb42b463790026feaf4f3859adbea16f`. The full battery, 73 task tests, required-rotation gate, 300-lesson random census, and full declared-period census all pass. These measurements cover the declared grammar and rivals; they do not prove identifiability against unknown rivals, exhaust all seeds, or broaden the grammar to the full reference-law domain.

No earlier return was used as a design lead; the retained associated-notes file was empty. All decisions above were derived from the pinned baseline, official demonstrations, fresh test failures, and current source-bound reports.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-35fbdf7e5ce95e29:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3c01af7a3a8e8e8dab0d37ab19cf0aa3cb42b463790026feaf4f3859adbea16f`. At disposition, audited bytes match the current source.

### Current decision

No issue found in finite reviewer-reported evidence on source 3c01af7a3a8e8e8dab0d37ab19cf0aa3cb42b463790026feaf4f3859adbea16f: 73/73 task tests, 600/600 strict draws, 3/3 canonical inputs, 12/12 identifiable lessons, 0/60 ambiguous smoke rotations. Initial audit exit 1 reflected missing period enumeration; checks/audit/c59d7541b22e-period.json and checks/audit/c59d7541b22e-period.summary.json enumerate all six band/residue lessons at seed 0 and 30 rotations, with no ambiguity, hook warnings or scoring errors. This closes only that bounded missing-evidence warning, not all seeds or undeclared rivals. No maintainer rerun.

### Assessment or prior finding

## c59d7541b22e

**Conclusion: No issue found.** Audited generator SHA-256: `3c01af7a3a8e8e8dab0d37ab19cf0aa3cb42b463790026feaf4f3859adbea16f`.

I ran the combined portable task-test and semantic preset. All 73 task tests passed. The semantic smoke accepted 600/600 strict draws and 3/3 canonical inputs, fired 3/3 witnesses, verified 3/3 rival claims, found all 12/12 production lessons identifiable, and found 0/60 ambiguous query rotations. The combined command exited 1 only because the declared two-step lesson schedule had not been enumerated, not because a semantic counterexample was found (`checks/audit/c59d7541b22e-combined/result.json`).

I then enumerated every declared start residue at fixed seed `0` across easy, medium, and hard, with every query position. The source-bound census materialized 6/6 lessons and 30 rotations, with 0 production ambiguities, 0 rotation ambiguities, 0 hook warnings, 0 scoring errors, and 12 unique inputs (`checks/audit/c59d7541b22e-period.json`; compact `checks/audit/c59d7541b22e-period.summary.json`). This exhausts the declared period at one seed, not all seeds or undeclared rivals. I left the target unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
