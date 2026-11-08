# Working notes: 2a5919c40197

## Current parametric proposal (2026-10-24)

- Added `workspace/parametric/adapter.py`, exact `canonical.rkt`, alternative
  `longest.rkt`, and the native promotion contract. Production generator
  `d222d3cf44d694716979214022e8f461ee2995df4a635c868b291e9a3a82178a`
  and canonical rule `bb6a3cb8ba31` remain unchanged.
- Episode-fixed `mode` is `all_uniform` or `longest_uniform_run`. The latter
  discovers maximal consecutive fully uniform bands, ignores their row colors,
  and retains every global-maximum band. Run lengths are the input-dependent
  intermediate needed by selection; ties are intentionally retained.
- Two decisive demos teach relative run length: a tied maximum of two with a
  losing singleton, followed by a compact unique larger maximum with a shorter
  band. This removes both absolute threshold/fallback and fixed relative-height
  shortcuts. Independent review found a20%-of-height rival fitting the old
  seed0 demonstrations but changing180 cells of its30x30 query; a protected
  before witness is retained. The repaired second demo rejects a band occupying
  3/10 or4/12 of its height, while the first accepts bands of relativeheight2/7. The default third demo restores
  canonical 3x3 morphology; a distinct 3x3 query exists even at two demos.
- Counts are independent (2..6 demos,1..4 queries), ordinary use is3+4, and
  query profiles are3x3,17x12,24x23,30x30. Seed streams and collision decisions
  are independent of settings/counts. Only public challenge bytes determine
  public identifiers. `audit.py` regenerates bounded Racket-backed teaching,
  export, and boundary evidence for future reviewers.
- The prototype's3..30 semantic validator is separate from canonical
  self_check's3..18 grammar. Current scalar-validation proposals in the older
  notes remain unselected; this work does not alter canonical seeds/version.
- Retained native qualification and causal replay are reviewer evidence. The
  owner's next action is exact-source integration, qualification, and native
  acceptance. No training activation or universal uniqueness is claimed.

## Review repair (2026-10-05)

- Pinned canonical authority with `RULE_HASH = "bb6a3cb8ba31"`.
- Replaced the broad, internally conflicting override surface with one exact,
  observable axis: `scene_profile ∈ {canonical_anchor, width_extension}`.
- Alternated the two profiles by `sample_index`, so any four consecutive pairs
  contain two anchors and two width-extension witnesses. With three demos and
  one query, every query rotation leaves at least one of each in the demos.
- Declared and executable-tested the strongest canonical-fitting rival:
  “inspect only the first three cells of each row.” Wider examples always include
  a mixed row whose first three cells are equal and a later cell changes.
- Preserved broad variation on width-extension scenes (height `3..18`, width
  `4..18`, multiple row textures and difficulty-biased dimensions) without
  advertising probabilistic draws as exact public controls.
- Synchronized the selected base solution text to the exact canonical Racket
  program. This was a source-text repair only; canonical behavior did not change.

## Deliberate domain limits

`self_check` requires rectangular `3..18 × 3..18` inputs, at least three visible
input colors, and both a uniform and a non-uniform row. These constraints keep
training scenes informative but do not claim coverage of smaller, monochrome,
or single-output-color inputs on which the mathematical row rule is still
well-defined. The finite declared-rival census is evidence against named
shortcuts, not a proof of unique induction against every possible rival.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d222d3cf44d694716979214022e8f461ee2995df4a635c868b291e9a3a82178a`.

# Decisions: 2a5919c40197

## D1 — Preserve the selected semantic rule

**Choice.** Keep the canonical full-row uniformity rule unchanged and pin it with
`RULE_HASH = "bb6a3cb8ba31"`.

**Original rationale.** The baseline documentation stated the same rule, but the
reason for its unpinned source arrangement was not recorded. Canonical execution
already solved all five labeled pairs.

**Alternatives considered.** Rewriting the canonical Racket program, retaining
multiple textually divergent authorities, or changing the task domain. A rule
rewrite would add semantic risk without fixing the generator defects.

**Probe.** Rule smoke and authority sync execute every canonical pair. Final
source parity is recorded in
`checks/final-after-rerun/checks/2a5919c40197_after_authority_sync.json`.

**Limit.** Text synchronization establishes one selected source group; it does
not itself approve the generator for training.

## D2 — Replace the old public controls instead of patching each one

**Choice.** Expose exactly one axis:
`scene_profile ∈ {canonical_anchor, width_extension}`. Unknown and retired axes
raise `ValueError`.

**Original rationale.** Unknown. The baseline exposed height, width, palette,
ratio, and texture controls, but their advertised ranges, degeneracy labels, and
difficulty-local behavior conflicted with generation and validation.

**Alternatives considered.** Keep all old axes and enumerate incompatibilities;
turn approximate random draws into exact controls; or make every internal row
texture public. Those designs create a large Cartesian contract without helping
the teaching objective.

**Probe.** The override checker exercised three cases across all three bands,
30 seeds each (270 draws), with zero findings or explicit rejections. The
unknown-key probe was rejected. Evidence:
`checks/final-after-rerun/checks/2a5919c40197_after_override_results.json`.

**Failure mode / limit.** Internal dimensions, palettes, and row textures remain
stochastic and therefore cannot be requested exactly through the public API.
That is deliberate rather than an undocumented control promise.

## D3 — Alternate exact anchors with direct shortcut witnesses

**Choice.** Even sample indices emit `canonical_anchor`; odd indices emit
`width_extension`. `EXAMPLES_NEEDED = 3`, so a four-pair lesson has three demos
and one query. Every query rotation retains at least one anchor and one witness.

**Original rationale.** The baseline had no source-bound guarantee that a lesson
contained canonical support or a counterexample to a plausible rival.

**Alternatives considered.** Independent random profile draws, a four-block
schedule with only one witness, or wider examples only. Random draws permit
all-anchor lessons; one witness can be held out as the query; wider-only lessons
lose exact canonical morphology.

**Probe.** The task test exhausts 12 cyclic starts in every difficulty band and
all four held-out positions. The large census checks 300 lessons and 1,200
rotations. Evidence: `checks/lesson-census.json`.

**Failure mode / limit.** The alternating schedule is predictable. That is
acceptable because profile parity does not determine row labels, but future
lesson assemblers must continue using consecutive sample indices or explicitly
recheck identifiability.

## D4 — Use a first-three-only rival as the primary semantic target

**Choice.** Declare “inspect only the first three cells of each row” in
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, linked to the
`late_change_after_three` witness.

**Rationale.** Every canonical row has width three, so this rival is behaviorally
identical on every public pair yet has a simple exact counterexample at width
four. It is stronger and more task-specific than generic guesses such as “paint
all rows black.”

**Alternatives considered.** First/last-cell equality, majority color, or
memorizing the finite canonical grids. The row-texture distribution supplies
some evidence against those, but the first-three rival is the most direct
canonical underdetermination and is executable under the shared semantic gate.

**Probe.** The exact input/output disagreement is retained in
`checks/shortcut-counterexample/counterexample.json`, with the authoritative
Racket execution in `checks/shortcut-counterexample/racket.json`.

**Failure mode / limit.** Passing one declared rival family does not rule out all
programs consistent with the demonstrations.

## D5 — Preserve exact canonical morphology without copying canonical grids

**Choice.** Use six index templates at exactly `3×3`, each with at least one
uniform and one mixed row and with three or four palette entries drawn from ARC
colors excluding `0` and `5`.

**Original rationale.** The baseline profile-floor evidence had only 2/60 exact
hits and no medium/hard support. Exact canonical support was therefore required.

**Alternatives considered.** Sample arbitrary random `3×3` grids; copy canonical
inputs; or allow output colors in the input. Arbitrary sampling gives weak
profile control, copying risks memorization, and input `0`/`5` can make the
transformation visually identity-like.

**Probe.** All five canonical inputs pass `self_check` and
`strict_canonical_like`; final profile floor has exact support in every band.

**Failure mode / limit.** The finite anchor-template family is intentionally
small. Generalization pressure comes from the alternating broad profile rather
than from anchor diversity alone.

## D6 — Make wider scenes broad but guarantee one decisive row

**Choice.** Draw heights `3..18`, widths `4..18`, and three to six non-output
colors. Insert one row whose first three cells are equal and a later cell changes;
fill remaining mixed rows with alternating, split, same-ends, one-minority, or
random patterns, plus one or more uniform rows.

**Original rationale.** Unknown. The baseline advertised `3..18`/`2..18` but
sampled only a narrow range, and some degenerate textures contradicted its own
validator.

**Alternatives considered.** Only width four; only the mandatory witness row;
or fully random rows. The selected design keeps the counterexample guaranteed
while varying size, color, row count, and other local heuristics.

**Probe.** The focused distribution test draws 120 examples per band, exactly 60
anchors and 60 witnesses, requires every witness to refute the rival, and
requires at least 115 unique grids per 120 draws.

**Failure mode / limit.** `self_check` intentionally excludes scenes with fewer
than three colors or only one output class. Such grids are mathematically lawful
but poor teaching examples and remain outside the documented generator domain.

## D7 — Treat validation as the lawful training grammar

**Choice.** Require rectangular ARC-color grids, dimensions `3..18`, at least
three colors, at least one uniform row, and at least one mixed row.

**Original rationale.** The baseline validator accepted low-signal minimal
impostors and conflicted with advertised degenerates.

**Alternatives considered.** Validate only shape/range, or accept all inputs on
which the Racket rule runs. Both permit lessons with all-identical outputs or
visually trivial transformations.

**Probe.** Canonical inputs pass; malformed, one-class, and collapsed examples
fail in task-local regressions; defect lint is green.

**Failure mode / limit.** This is a curriculum grammar, not the maximal domain of
the mathematical transformation.

## D8 — Synchronize selected Racket text, not behavior

**Choice.** Replace the selected base solution’s `raw_code` and `target_code`
with the exact canonical program text.

**Original rationale.** The divergent text was described by the checker as an
unsynchronized beautification; no design rationale was retained.

**Alternatives considered.** Leave the divergence advisory/failure in place or
rewrite the canonical source to match the base solution. The former blocks the
required gate; the latter changes the higher-authority source unnecessarily.

**Probe.** All three authorities now share exact SHA
`72e69fa2d29a33575fd623dc610554eb99b989013d47e570ee0b59aee253b339`
and normalized rule hash `bb6a3cb8ba31`; execution parity is 5/5 canonical
pairs.

**Failure mode / limit.** None identified beyond ordinary maintainer review of a
source-text delta.

## D9 — Add portable tests and retain real failures

**Choice.** Add nine tests using `reviewer_support.find_root`, `canonical_path`,
and `canonical_pairs`, and keep the red TDD run plus failed checker probes.

**Rationale.** The selected task-test stage snapshots into a portable layout;
fixed parent-depth imports would pass locally and fail in that runtime. Retaining
red evidence shows which behavior the implementation added rather than merely
recording post-hoc green tests.

**Alternatives considered.** Root-only pytest tests or ad hoc scripts. They are
not automatically discovered by the selected task stage and provide weaker
handoff guarantees.

**Probe.** `checks/tdd-red-v2.log` records eight expected baseline failures;
`checks/final-task-tests-rerun/result.json` records 9/9 passing in the staged
runtime.

## Current compatibility proposal

Unselected compatibility-conflicting repair. Current approved source d222d3cf/version2.0.0 accepts literal integer seeds, including negative seeds supported by public runtime.generate. Proposed ab882fbc/version2.0.1 adds useful literal-call validation but rejects negative seeds and changes VERSION passed to GenCtx. stable_rng hashes VERSION, so the version bump changes the keyed random stream; the claimed preservation of lawful generated grids is not established. Rebase the validation to retain the existing seed domain and RNG version, or explicitly justify and verify a deliberate sampling migration. Current malformed-scalar weakness is not claimed fixed. Retain the row/column rule prototype, reported12/12 battery,15 portable/fresh tests,48 Racket labels and24 rotations solely with proposed bytes; no current prototype count, source/rule modification, approval upgrade or owner submitted-code execution. Retained at `workspace/proposals/review-803b0250fdb9ec1a/manifest.json`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-c6a4656fd390973b:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `51388816c44bdee20ae0191aa7ae70ede07e49a08c4ae853c313cdb62671dac3`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit static resolution on already installed reviewed source d222d3cf44d694716979214022e8f461ee2995df4a635c868b291e9a3a82178a, unchanged this intake. Current AXES advertises only scene_profile, and generate rejects every undeclared key before GenCtx. The old palette_size/grid_h/texture controls were explicitly retired in the current2026-10-05 design; their old difficulty-local bounds and all_uniform path are no longer advertised or reachable as accepted controls. This resolves the old-source exact-control/domain promises, not the newly proposed scalar repair, which remains unselected. No owner battery or new source approval.

### Assessment or prior finding

## 2a5919c40197

**Reproduced contract defects; target left unchanged.** Frozen generator SHA-256 `51388816c44bdee20ae0191aa7ae70ede07e49a08c4ae853c313cdb62671dac3`, rule hash `bb6a3cb8ba31`.

At seed `271828`, sample index `11`, the axis table advertises `grid_h=18`, but the easy sampler raises `draw_int('grid_h'): override 18 outside [3, 4]`. It also advertises `palette_size=10`, but medium raises outside `[3, 7]`. The declared valid `texture=all_uniform` does return a grid, yet `self_check` rejects it with `no non-uniform row (output would be all 5s)`. These are generator-domain defects, not claims about the Racket rule. Exact overrides, emitted grid, hashes, and diagnostics are in `checks/audit/2a5919c40197/probe.json`; replay with `python3 generators/fd277c567993/workspace/audit_contract_probe.py --out ../checks/audit` from `repo`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-c6a4656fd390973b-v0001/audit_assets.json), manifest SHA-256 `e8d3b14d162011b07a09e9e97dab2a541281b2076a8bb691506f102b95443605`.
<!-- arcpuzzles-current-audit-assessment:end -->
