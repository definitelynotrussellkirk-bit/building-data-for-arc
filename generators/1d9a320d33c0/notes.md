# Working notes: 1d9a320d33c0

## 2026-10-02 review — assignment review-b4a044e31c5fa03e

### Baseline findings

- The generator had no `RULE_HASH` pin and declared nine axes although only dimensions and count materially controlled the output.
- Helpful palette/texture controls were silently ignored; three malformed negative fixtures were advertised in the ordinary texture domain.
- Difficulty-specific draw bounds contradicted the declared global ranges, so valid cross-band overrides could reject or be ignored.
- Placement could silently return fewer dominoes than requested.
- Ordinary scenes often contained only one orientation. A 500-draw census found single-orientation rates of 49.6% easy, 27.2% medium, and 6.6% hard.
- The old `self_check` only required one nonzero cell. It accepted singletons, solid 2×2 blocks, blocked growth, repeated colors, and one-orientation scenes.
- Canonical profile support was 3/60 exact and 4/60 envelope; easy and hard had zero exact-profile support in their 20-draw bands.
- No semantic contract existed, so the battery could not test whether lessons distinguished the full two-branch rule from one-branch shortcuts.

### Repair

- Bumped to version 3.0.0 and pinned `RULE_HASH = "528b7a20c766"`.
- Reduced the public surface to three exact axes: `grid_h`, `grid_w`, and `domino_count`; added strict request validation and observable provenance.
- Replaced greedy placement with deterministic backtracking over non-overlapping 2×2 footprints. The generator now realizes exactly the requested count and deliberately covers both diagonal-contact and fully separated layouts.
- Guaranteed mixed horizontal/vertical orientation in every ordinary draw.
- Added a 50% canonical-profile schedule plus bounded extrapolation; retained two-to-four objects and canonical-compatible dimensions.
- Rebuilt `self_check` around complete component, target, separation, color, and footprint semantics.
- Added `strict_canonical_like`, `rule_mirror`, horizontal-only and vertical-only rivals, paired witnesses, schedule metadata, and `lesson_identifiable`.
- Kept malformed examples as explicit negative fixtures only.
- Added task-local regression tests covering canonical parity, every axis-boundary cross in all bands, distribution support, negative impostors, provenance, rivals, determinism, and global-RNG isolation.

### Verification highlights

- Task-local tests: 27 passed.
- Strict lint: 0 errors, 0 warnings.
- Defect lint: 0 findings.
- Canonical profile gate: 38/60 exact, 39/60 envelope, 4/4 canonical inputs accepted.
- Semantic gate: 339/600 strict-canonical-like; 2/2 witnesses fired; both rival claims verified 60/60; 12/12 lessons identifiable.
- Override contract: 5,580/5,580 draws accepted over 62 cases and three bands.
- Rule smoke: 120/120 applied, Python mirror 120/120, no crashes.
- All twelve required stages passed when run individually. The monolithic wrapper exceeded the host foreground execution cap, so the individual source-bound receipts are retained instead of claiming a completed monolithic invocation.

### Failed attempts and retained friction

- The initial monolithic before and after battery invocations were externally timed out before the wrapper returned. Focused/per-stage invocations were used to preserve complete evidence.
- The first repaired static-lint run found one Python local named `objects`, which shadows a Racket primitive in the cross-language linter. Renaming it to `dominoes` cleared the warning with all 27 tests still green.
- A grouped check command exhausted its shared wall-clock budget while entering `racket_lint`; isolated reruns proved `racket_lint` and `authority_sync` pass.

### Remaining limitations

- Canonical evidence is only four pairs, so the exact curriculum breadth beyond those profiles is justified by the pinned Racket authority and generated counterexamples rather than additional public examples.
- Color-swap mutations are lawful for this color-agnostic task, so the generic mutation-sensitivity report correctly leaves those accepted.
- No Racket authority was changed.
## Current reviewer considerations

Source SHA-256: `f7d47b4d276e64425d1c267f43a0391c0253f3a19012dff1c0dd8364b9642acd`.

# Design decisions for 1d9a320d33c0

## 1. Public axis surface

**Baseline choice and rationale.** The baseline declared dimensions, palette controls, object count, palette size, position bias, distinct-color count, density, and texture. No retained note explains why all nine were public. Several were constants, aliases, or ignored.

**Decision.** Keep only `grid_h`, `grid_w`, and `domino_count`, because these are independently observable and materially change the input.

**Alternatives rejected.** I did not preserve no-op palette labels for compatibility, because accepting a control that cannot be observed is worse than a loud migration error. I did not expose orientation mix or spacing profile as public axes because the ordinary curriculum needs both branches and both spacing regimes automatically.

**Probe.** All boundary crosses in all three bands are covered by task-local tests and the repository override gate (5,580 draws, zero findings).

**Failure modes and limits.** This is a deliberate breaking change for callers using dead keys; they now receive a descriptive exception. The reduced surface does not expose exact colors, which remain nuisance variation rather than a semantic control.

## 2. Dimension and count envelope

**Baseline choice and rationale.** Defaults were approximately 7..10 by 8..12 and 2..4 objects, but difficulty code silently changed the actual hard envelope to 10..13 by 12..16 and 4..6 objects. The original rationale is unknown.

**Decision.** Use the declared/canonical-linked 7..10 by 8..12 envelope and two to four objects in every band. Difficulty changes count mass: easy 2/3, medium 2/3/4, hard 3/4.

**Alternatives rejected.** Keeping hard 5/6-object scenes would emphasize a scale not present in any canonical pair and was unnecessary to teach the local rule. Restricting every draw to exactly three objects would overfit the canonical count and remove useful compositional variation.

**Probe.** The profile gate improved from 3/60 exact and 4/60 envelope to 38/60 exact and 39/60 envelope. The 160-draw census records all intended count supports.

**Failure modes and limits.** The chosen envelope is conservative. It does not test very large canvases or dense packs; those could be added later only with evidence that they improve learning rather than dilute canonical mass.

## 3. Canonical schedule mass

**Baseline choice and rationale.** Canonical profiles appeared only accidentally; easy and hard had zero support in the pinned profile census.

**Decision.** Assign four of eight sample-index residues to the four exact canonical profiles, leaving the other four for bounded extrapolation.

**Alternatives rejected.** A 25% anchor schedule risked missing the repository's 25% envelope policy under deterministic census variation. A 100% exact-profile schedule would pass the floor but teach scale memorization.

**Probe.** The strict semantic census measured 56.5% strict-canonical-like draws (339/600), and every declared schedule profile appeared in every band.

**Failure modes and limits.** The schedule links only dimensions/count, not canonical placements or colors. This is intentional: exact scene copying would reduce diversity and invite memorization.

## 4. Mixed orientations in every ordinary scene

**Baseline choice and rationale.** Orientations were sampled independently. This produced many one-orientation scenes; no note indicates that this was intentional.

**Decision.** Every generated input includes at least one horizontal and one vertical domino. Count two uses one of each; count three uses a 2/1 split; count four uses two of each.

**Alternatives rejected.** Merely balancing orientation marginal frequencies across a large corpus was rejected because a model trains on finite lessons, and one-branch shortcuts can survive individual episodes even when the corpus average is balanced.

**Probe.** The frozen baseline had single-orientation rates of 49.6% easy, 27.2% medium, and 6.6% hard over 500 draws. The repaired generator had 0/500 in every band. A concrete baseline three-demo window at seed 0, sample indices 7–9, is horizontal-only.

**Failure modes and limits.** Requiring both branches in every scene may be stronger than necessary for some curricula, but it is cheap here and prevents a known shortcut without introducing unnatural objects.

## 5. Placement constraints

**Baseline choice and rationale.** `_clear_patch` imposed 8-connected clearance around input cells. The summary claimed one-cell padding, but a canonical example has diagonal contact between different dominoes.

**Decision.** Forbid only orthogonal contact between input objects and overlap between their complete growth footprints. Permit diagonal contact. Alternate deterministic diagonal-contact and fully separated scenes by sample-index parity.

**Alternatives rejected.** Retaining universal 8-connectivity clearance would exclude a canonical relation. Allowing arbitrary contact would create ambiguous connected structures or blocked targets.

**Probe.** The current 160-draw census has exactly 80 diagonal and 80 separated scenes per band. All four canonical inputs pass `self_check`.

**Failure modes and limits.** Footprints may touch at edges/corners after growth, which is canonical-compatible. They never overlap, so object outputs remain unambiguous.

## 6. Constructive search instead of greedy placement

**Baseline choice and rationale.** The old generator greedily walked a shuffled candidate list and returned whatever number fit, even when fewer than requested. The rationale is unknown.

**Decision.** Use deterministic depth-first search over candidate 2×2 footprints, with early pruning for required diagonal scenes.

**Alternatives rejected.** Rejection sampling was simpler but made exact-count guarantees probabilistic. Hard-coded templates were rejected because they would reduce positional diversity and invite memorization.

**Probe.** Every axis-boundary cross (4 heights × 5 widths × 3 counts × 3 bands) realizes the exact requested count and passes the independent component checker.

**Failure modes and limits.** Search is specialized to at most four objects, where it is fast. Raising the count substantially should trigger a new performance/packing design rather than silently widening the axis.

## 7. Distinct colors

**Baseline choice and rationale.** Colors were sampled without replacement, which matches canonical examples and keeps components easy to separate.

**Decision.** Retain distinct nonzero colors 1..9 and remove redundant palette-size/distinct-color controls.

**Alternatives rejected.** Repeated colors could create disconnected same-color objects that the canonical scan still handles but would complicate component-based explanation and introduce a new ambiguity not present in the public evidence.

**Probe.** Self-check and tests require one unique color per component; canonical inputs and all generated draws pass.

**Failure modes and limits.** The curriculum does not teach repeated-color disconnected dominoes. That is a conscious scope boundary, not a claim that the authority could never handle them.

## 8. Strong self-check

**Baseline choice and rationale.** The prior checker only tested whether any cell was nonzero, likely as a minimal smoke assertion.

**Decision.** Validate the full task input grammar and every precondition needed for a clean application of the rule.

**Alternatives rejected.** Output-based self-checking alone was rejected because a malformed input can still produce some output and pollute training. A checker tied only to metadata was rejected because the grid itself is the training artifact.

**Probe.** Strict defect lint went from one issue/eight warnings to zero findings. Mutation sensitivity improved from 15/58 to 44/56, with all absent-color and blank-grid mutations rejected.

**Failure modes and limits.** Generic color swaps remain accepted because color identity is semantically irrelevant. Treating those as failures would be a false positive.

## 9. Semantic rivals and lesson identifiability

**Baseline choice and rationale.** No semantic hooks existed, so morphology/diversity checks could pass without asking whether the whole rule was learnable.

**Decision.** Declare horizontal-only and vertical-only rival solvers, witnesses for each branch, authority-backed witness/rival mappings, and a lesson-level identifiability check.

**Alternatives rejected.** A prose-only statement was insufficient because it cannot gate future changes. A single aggregate branch histogram was also insufficient because it does not reveal whether an individual lesson permits a shortcut.

**Probe.** Both witnesses fire 600/600; both claims hold 60/60 against the Racket authority; 12/12 materialized lessons refute every named competitor.

**Failure modes and limits.** The rival set is intentionally small and task-specific. It catches the most plausible branch-dropping errors but is not a proof against every imaginable program.

## 10. Negative fixtures

**Baseline choice and rationale.** `no_dominoes`, `single_cell`, and `growth_blocked` were exposed as valid textures, apparently to support diagnostics, but ordinary generation and override validation then treated malformed inputs as lawful.

**Decision.** Keep them only in `_draw_from_degenerate` for explicit self-check power tests; reject them from `generate` because they are not axes.

**Alternatives rejected.** Declaring them as lawful degenerates would mislabel rule-inapplicable examples as training data.

**Probe.** Each fixture is now rejected by `self_check`; defect lint reports no texture-domain overlap.

**Failure modes and limits.** External callers that previously requested these strings now fail loudly. This is desirable for training safety.

## 11. Racket authority

**Baseline choice and rationale.** The selected canonical Racket source already matched all four public pairs and passed rule smoke.

**Decision.** Do not edit it. Pin it with `RULE_HASH`, mirror it independently in Python, and verify synchronization/execution parity.

**Alternatives rejected.** Style-only Racket cleanup was rejected because it would create authority churn without changing semantics. The inherited linter style findings are documented rather than "fixed" in an unrelated generator-distribution review.

**Probe.** Rule smoke applies 120/120 with Python mirror parity 120/120. Authority sync reports exact selected synchronization and execution parity across two retained source texts.

**Failure modes and limits.** The archival authority remains textually divergent but execution-equivalent; intake should preserve that distinction.
