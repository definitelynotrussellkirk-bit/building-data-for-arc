# Working notes: 9713c70409d0

## 2026-09-28 review

The public task is semantically ambiguous: raw bounding-box intersection reproduces all three canonical pairs. The main review objective was therefore not generic randomization, but construction of lessons that preserve canonical support while falsifying that shortcut and the neighboring row-only/raw-cell rules.

Replaced generator 3.0.1 with 4.0.0. The old implementation exposed eight misleading controls, silently accepted unknown keys, sometimes grew the canvas after drawing exact dimensions, accepted semantically empty degenerates, and had no rule hash or semantic contract. The before battery finished 7 green, 2 advisory, 3 failed.

The new schedule cycles four exact profiles. Two retain canonical dimensions; `closure_order` supplies ordered-closure counterexamples; `graph_5` broadens relation graphs. Objects are three/four endpoints on two rows. `self_check` enforces exact signatures, grammar, at least one edge, and at least one non-edge.

Added named rivals (`bbox_overlap`, `row_closure_only`, `raw_cells_only`), witnesses, witness bindings, a canonical-shortcut declaration, lesson-identifiability checks, a Python rule mirror, mutation fixtures, focused tests, and `workspace/analyze_closure_curriculum.py`.

Final evidence:

- full battery: 12/12 green;
- canonical profile floor: 30/60 exact and envelope;
- semantic census: 295/600 strict, 3/3 canonical accepted, 3/3 witnesses verified, 12/12 lessons identifiable;
- linter: 52 distinct outputs, 36% unique, no errors/warnings;
- task analyzer: 120/120 valid, 30 draws per profile, 119 unique inputs, 47 unique outputs, 50% strict fraction.

Known limitation: constructions come from finite graph families rather than uniform sampling over every realizable closure-intersection graph. Retain the full battery and analyzer when adding templates.
## Current reviewer considerations

Source SHA-256: `74002db308ca5a49255e4e077d7ea5871e095cb359f4f5d943af5dc6999ae093`.

# Decisions: 9713c70409d0

## D1 — Preserve the canonical rule and authority

**Choice.** Keep the selected Racket program and canonical examples unchanged; pin its normalized hash as `c6c3ba6e25a0` and build an independent Python mirror only for testing and semantic analysis.

**Original rationale.** The baseline docstring had already corrected an older mistaken “pair-difference” interpretation and identified the real completed-closure overlap rule. The canonical program passed Racket lint and authority-sync checks.

**Alternatives considered.** Editing the Racket rule; weakening the generator to match an easier bounding-box interpretation.

**Probe.** The mirror reproduces all three canonical outputs, and the final rule-smoke and authority-sync stages are green.

**Failure mode / limitation.** Any future authority edit requires updating the hash and revalidating the mirror; the mirror is not label authority.

## D2 — Replace eight pseudo-controls with one exact profile axis

**Choice.** Expose only `scene_profile`, with four recoverable signatures.

**Original rationale.** The baseline wanted to vary canvas size, color count, palette, motifs, density, position, and texture. In practice several names were aliases or constants, the implementation used undeclared `n_colors`, and post-placement canvas growth broke exact dimensions.

**Alternatives considered.** Repair every legacy axis; expose low-level graph/template/color/reflection axes; remove all overrides.

**Probe.** The override gate now passes across every difficulty band and rejects unknown keys. Focused tests verify all four exact profile overrides.

**Failure mode / limitation.** Callers cannot request arbitrary dimensions or color counts. This is intentional: only values with a stable, observable semantic contract are public.

## D3 — Use a deterministic four-slot lesson cycle

**Choice.** Cycle `canonical_3`, `canonical_4`, `closure_order`, and `graph_5`; set `EXAMPLES_NEEDED = 4`.

**Original rationale.** Unknown. The baseline randomized dimensions and color count by difficulty but had no lesson-level curriculum guarantee.

**Alternatives considered.** Pure random profile selection; weighted canonical sampling; three-example lessons.

**Probe.** Every four-example window across all three difficulty bands passes `lesson_identifiable`; the semantic gate reports 12/12 identifiable lessons.

**Failure mode / limitation.** A consumer that shuffles individual examples without retaining four-example groups loses the schedule guarantee.

## D4 — Preserve canonical-scale support at 50%

**Choice.** Two of four schedule slots use canonical dimensions and endpoint morphology.

**Original rationale.** The baseline attempted broad generalization but achieved only 2/60 exact-profile hits and no hard-band exact support.

**Alternatives considered.** Exact canonical dimensions only; a small 15% canonical anchor; fully unconstrained random scenes.

**Probe.** The canonical-profile gate reports 30/60 exact and envelope matches, all three canonical inputs accepted, and the semantic census reports 49.2% strict support.

**Failure mode / limitation.** Canonical support is dimension/morphology linked, not a claim that generated relation graphs reproduce the empirical canonical graph-frequency distribution.

## D5 — Add a dedicated closure-order counterexample profile

**Choice.** Include scenes where column closure creates an overlap and where two raw bounding boxes overlap although the completed closures do not.

**Original rationale.** None was present. Direct probing showed the bounding-box rival matches every public pair.

**Alternatives considered.** Depend on random layouts to eventually produce a counterexample; add only a row-only witness; annotate the rule in prose without changing data.

**Probe.** `CANONICAL_SHORTCUTS["bbox_overlap"]` matches 3/3 canonical pairs, while every `closure_order` draw refutes it. The semantic gate observed 142/600 bounding-box false-positive witnesses.

**Failure mode / limitation.** The named rival set is necessarily incomplete; future reviews can add plausible competitors without changing the rule.

## D6 — Use sparse endpoint objects with strict grammar

**Choice.** Each color has three or four endpoint cells over exactly two rows. The row intervals are completed first, then their columns.

**Original rationale.** The baseline used disconnected small motifs to create closures, but accepted empty and weakly specified scenes.

**Alternatives considered.** Arbitrary point clouds; filled rectangles; multiple disconnected motif occurrences with no exact count.

**Probe.** `self_check` accepts all canonical pairs and generated scenes, rejects seven targeted malformed/trivial fixtures, and the self-check/defect-lint stages are green.

**Failure mode / limitation.** This grammar does not cover every lawful sparse object that the canonical program could process. It prioritizes clean supervision and reliable counterexamples.

## D7 — Require both positive and negative relations

**Choice.** Reject scenes whose output has no 8 edge or no 0 non-edge.

**Original rationale.** Unknown. The baseline did not prevent all-disjoint or all-overlapping examples.

**Alternatives considered.** Allow relation-trivial examples as easy curriculum; enforce an exact edge count.

**Probe.** Focused tests check every sampled scene. The 120-draw analyzer observed edge counts from 1 through 6.

**Failure mode / limitation.** Complete or empty relation graphs are valid under the rule but excluded from ordinary training because they teach less about pairwise discrimination.

## D8 — Use finite graph families plus label randomization

**Choice.** Define explicit K=3, K=4, and K=5 construction families, then randomize object order, colors, and reflections.

**Original rationale.** The baseline sought output-shape and matrix diversity using random motif placement, but placement retries could mutate requested dimensions and did not guarantee semantic coverage.

**Alternatives considered.** Rejection-sample arbitrary endpoints until a target graph appears; solve rectangle-intersection graph realization online; keep the old free-placement loop.

**Probe.** The linter measured 52 distinct outputs (36% unique); focused sampling found at least 30; the analyzer found 47 unique outputs in 120 draws.

**Failure mode / limitation.** The finite graph alphabet is not exhaustive. Adding a new template requires checking endpoint collisions, mixed relations, and rival coverage.

## D9 — Make semantic assumptions executable

**Choice.** Declare rivals, canonical shortcuts, witnesses, witness-to-rival bindings, lesson competitors, and mutation fixtures in generator code.

**Original rationale.** Unknown; these contracts were absent in the baseline.

**Alternatives considered.** Keep the reasoning only in comments; rely solely on aggregate diversity; add tests without machine-readable hooks.

**Probe.** The semantic gate reports all three witness claims verified and all lessons identifiable. Tests first failed on the old generator, then passed after implementation.

**Failure mode / limitation.** The gate can only challenge declared or discoverable shortcuts. A separate model- or synthesis-based rival miner would expand coverage.

## D10 — Add a reusable curriculum analyzer

**Choice.** Ship `workspace/analyze_closure_curriculum.py` and test it.

**Original rationale.** The packet had general-purpose checks but no task-local report tying schedule balance to relation graphs and rivals.

**Alternatives considered.** One-off notebook; static report only; no extra tool.

**Probe.** A 120-draw run completed with zero invalid draws and a balanced 30/30/30/30 profile census.

**Failure mode / limitation.** It is a cheap structural/semantic monitor, not a replacement for Racket execution or the full battery.
