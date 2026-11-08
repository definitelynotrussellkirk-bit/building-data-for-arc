# Working notes: 3ef5f8be2639

## Baseline findings

Baseline generator SHA-256 `9025e044484a07414d49634309982b6b9843d6b075544482bd21eab9888c5267` did not pin `RULE_HASH`, declared ignored/singleton axes, and exposed ordinary texture values that did not change generation. Its override stage found 6,105 findings across 52,830 draws; its semantic stage had no contract; its profile census reached only 11/60 canonical-envelope draws and had zero hard-band support. The claimed optional extra seeds were never generated, so the authority's first-in-scan-order behavior was not taught. See `checks/before/` and `checks/baseline-stages/` in the return.

## Repair

Version `4.0.0` is constructive rather than retry-based. It declares only five exact observable controls: two dimensions, one of 24 selected-pair offsets, and the two seed counts. Unknown or malformed overrides fail closed. The selected pair is interior and always lawful; optional later cells are placed so they cannot replace either selected center. Every even default draw contains an effective distractor for the all-pairs rival.

Canonical-size support is deterministic rather than probabilistic: sample-index phases include 7×7, 8×8, and 7×8/8×7 before broader difficulty-aware shapes. Distance 1 and distance 2 alternate. This avoids a pass that depends on lucky seeds.

`self_check`, `strict_canonical_like`, and `observe_overrides` validate the actual domain. The task now declares executable `all_pairs` and `distance_two_only` rivals, witness hooks, and a `lesson_identifiable` check. `workspace/qualify.py` exhausts joint exact controls and rotates every item in each four-pair lesson window through the query position.

## Final evidence

Final generator SHA-256: `c5e2f143ecdc72ef4195f54a18c009f4e4c2e75dd3a9ff041622b1d394bd84b5`.

- Full battery: 12/12 green (`checks/after-final-1/`).
- Portable selected-task tests: 130/130 passed (`checks/task-tests/`).
- Production lesson census: 300/300 lessons materialized, 0 ambiguous, 0 hook warnings, 0 scoring errors; every declared rival alias refuted in 100/100 lessons per band (`checks/lesson-census-final.json`).
- Qualification probe: 576 exact-axis cases, 300 default draws, and 1,200 cyclic query rotations, all without failures (`checks/qualification-final.json`).
- Reference authority: unchanged; declared hash `020757caefaf`.

## Limits

This finite rival set does not prove universal induction. The lawful generated domain keeps selected centers interior, uses at most two cells of each seed color, and does not teach clipped edge neighborhoods; those restrictions are deliberate because the canonical examples and written task concept use full 3×3 growths. Future domain expansion should add named rivals and rerun cyclic lesson rotations rather than broadening by untracked random noise.
## Current reviewer considerations

Source SHA-256: `c5e2f143ecdc72ef4195f54a18c009f4e4c2e75dd3a9ff041622b1d394bd84b5`.

# Decisions — `3ef5f8be2639`

All final-source measurements below use generator SHA-256 `c5e2f143ecdc72ef4195f54a18c009f4e4c2e75dd3a9ff041622b1d394bd84b5`.

## D1 — Keep the Racket authority unchanged

**Decision.** Preserve the canonical first-color-2/first-color-3 rule and pin `RULE_HASH = "020757caefaf"`.

**Why.** The canonical outputs, written solution, and Racket implementation agree. Baseline rule-smoke passed; the defects were in sampling and contracts, not the authority.

**Alternative rejected.** Reinterpret multiple seeds as “grow all 2/3 pairs.” That rival fits all three usable canonical pairs only because each has one seed of each color; changing the authority would silently invent semantics. Generated later-seed witnesses instead teach the already selected Racket behavior.

**Probe / failure mode.** `all_pairs` is retained as an executable canonical-fitting rival. It is refuted by 150/300 default qualification draws and 100/100 production lessons per band.

## D2 — Expose only exact observable axes

**Decision.** Replace nine partly fake axes with five exact controls: `grid_h`, `grid_w`, `offset_id`, `num_2_seeds`, and `num_3_seeds`.

**Original rationale.** Unknown. The v3 file labeled palette, density/position, and texture concepts but generation did not read most of them; singleton axes could not produce variation.

**Alternatives rejected.** Keeping compatibility aliases would preserve silent no-ops. Marking them diagnostic would still add no training value. Removing them makes typos and stale callers fail closed.

**Probe / failure mode.** Baseline: 6,105 findings across 52,830 draws. Final: 17,730/17,730 accepted with no mismatch, plus 576 task-local joint exact cases. Unknown, boolean, float, and out-of-range controls are regression-tested.

## D3 — Use a constructive selected-pair layout

**Decision.** Enumerate all 24 nonzero Chebyshev-distance-1/2 offsets and place an interior first pair directly.

**Why.** The full 3×3 neighborhoods then exist and always overlap. A constructive mapping makes every exact override legal on 7×7 and 8×8 grids and avoids seed-dependent retry exhaustion.

**Alternatives rejected.** Randomly sample two points until a legal offset appears; retain the old 60-attempt loop and fallback. Both obscure which override was realized and can bias offsets near boundaries.

**Probe / failure mode.** `workspace/qualify.py` covers 3 bands × 2 canonical-size shapes × 24 offsets × 4 count combinations = 576 cases, all accepted and exactly observed.

## D4 — Make scan-order semantics observable with later distractors

**Decision.** Schedule one or two seeds of each color and, on every even default draw, place at least one later same-color seed that makes `all_pairs` disagree with the first-pair rule.

**Why.** The baseline summary claimed extras, but the generator returned immediately after one pair. Without effective extras, a model cannot infer which of multiple seeds the authority selects.

**Alternatives rejected.** Add arbitrary far-away noise cells. Noise that never changes a plausible rival is visual diversity, not semantic evidence. Put distractors before the selected pair. That would change the selected centers and violate the requested exact offset.

**Probe / failure mode.** The default audit found 150 effective distractors in 300 draws. The `all_pairs` rival fits 3/3 canonical pairs but is refuted in every one of 300 production lessons.

## D5 — Schedule canonical profiles before broad variation

**Decision.** Use a four-phase shape schedule: 7×7, 8×8, alternating 7×8/8×7, then difficulty-aware 7..14 variation.

**Why.** Baseline canonical-envelope support was 11/60 and hard-band support was 0/20. Deterministic anchors ensure each band contains canonical-scale examples while preserving broader shapes.

**Alternatives rejected.** Increase only the probability of 7×7/8×8. A probabilistic floor can still fail for particular seeds and makes review results unstable. Restrict every example to canonical sizes. That discards useful shape generalization.

**Probe / failure mode.** Final profile floor reached exact 29/60 and envelope 48/60, with support in all bands. The 300-draw audit included 77 7×7 and 78 8×8 examples plus broader profiles.

## D6 — Alternate distance 1 and distance 2

**Decision.** Even sample indices use a distance-1 selected pair; odd indices use distance 2, with orientation keyed independently.

**Why.** All canonical pairs happen to use distance 2. A distance-2-only shortcut therefore fits canonical data but is not the general 3×3-intersection rule.

**Alternative rejected.** Rely on random distance choice. It does not guarantee each short lesson contains a distance-1 witness.

**Probe / failure mode.** `distance_two_only` fits all 3 canonical pairs. The default audit measured exactly 150 distance-1 and 150 distance-2 draws, and every production lesson refuted the rival.

## D7 — Treat validation as the generated-domain contract

**Decision.** `self_check` validates shape, ARC cell types/colors, dimensions, counts, interior selected centers, and selected-pair offset; `strict_canonical_like` delegates to it and `MIN_STRICT_FRAC = 1.0`.

**Why.** The old validator only checked whether both colors existed and explicitly bypassed degenerates. It accepted `no_overlap`, which produces no intended teaching signal.

**Alternatives rejected.** Keep negative fixtures inside the ordinary texture domain. Negative tests belong in tests, not in the production sampler. Permit border-selected centers. Although the Racket rule clips, edge cases teach a second concept and conflict with the canonical “full 3×3” wording.

**Probe / failure mode.** Task tests mutate away a seed, add a bad color, move the pair too far, exceed counts, and pass malformed grids; all are rejected without validator crashes.

## D8 — Declare plausible rivals and test complete lessons

**Decision.** Declare `all_pairs` and `distance_two_only` in all three supported rival registries, map each to a named witness, and implement `lesson_identifiable` over full demos plus query validation.

**Why.** Individual witness frequency does not show that each assembled lesson contains the witness among its demonstrations.

**Alternative rejected.** Count witness occurrences only. A lesson can place its only witness in the query, making the visible demos ambiguous. `checks/query-rotation-negative.json` reproduces exactly this failure.

**Probe / failure mode.** Production census: 300/300 fixed-policy lessons unambiguous. Task-local extension: every item in 100 contiguous four-item windows per band is rotated into query, 1,200/1,200 rotations passing.

## D9 — Build a reusable qualification tool

**Decision.** Add `workspace/qualify.py` and a portable test that executes it.

**Why.** The public battery is broad, while this task needs exhaustive offset/count support and cyclic lesson rotation. A source-bound report gives future agents the same checks without reconstructing ad hoc notebooks.

**Alternative rejected.** Put the logic only in tests. Tests would say pass/fail but would not retain a compact profile, uniqueness, witness, and rotation report for review.

**Limits.** This tool uses an independent Python oracle and canonical-data helper. Racket `rule_smoke` and `authority_sync`, not the probe, bind outputs to authority. Declared rivals are finite and task-specific.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-cf9c41ca8d4a7c2c:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c5e2f143ecdc72ef4195f54a18c009f4e4c2e75dd3a9ff041622b1d394bd84b5`. At disposition, audited bytes match the current source.

### Current decision

Bounded reviewer-reported no-issue audit of SHA c5e2f143ecdc72ef4195f54a18c009f4e4c2e75dd3a9ff041622b1d394bd84b5: 130 task tests and strict semantic probes reported passing. No source repair or new approval implied; no maintainer rerun.

### Assessment or prior finding

## 3ef5f8be2639

**No issue found.** I checked the generator source bound to SHA-256 `c5e2f143ecdc72ef4195f54a18c009f4e4c2e75dd3a9ff041622b1d394bd84b5`, its task-local tests, validator, semantic declarations, rival implementations, and generated witnesses. The portable test suite passed **130/130** tests. The strict semantic gate also passed: **600/600** sampled inputs met `strict_canonical_like`, all **3/3** canonical inputs were accepted, both declared witnesses fired, both canonical-fitting rival claims were verified and refuted by generated witnesses, **12/12** lessons were identifiable, and the diagnostic rotation probe found **0/48** ambiguous rotations. The checked rivals cover the two most plausible shortcuts visible in this task: using all color-2/color-3 pairs instead of the first row-major pair, and handling only Chebyshev-distance-2 seed pairs.

Evidence: `checks/audit/3ef5f8be2639-combined/result.json`, `checks/audit/3ef5f8be2639-combined/checks/task_tests.xml`, `checks/audit/3ef5f8be2639-combined/checks/3ef5f8be2639_audit_semantic_gate.log`, and `checks/audit/3ef5f8be2639-combined.command.log`. Scope limitation: this was a source-bound task-test and strict-semantic review, not an exhaustive proof over every integer seed or every possible malformed grid. No source changes were made and this audit does not approve the generator.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
