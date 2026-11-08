# Working notes: 155cf6b30713

## Current opt-in native relation-transfer family

The prior decision not to parameterize is superseded **only for a separate native
family**, not for production/canonical behavior. `workspace/parametric/adapter.py`
adds forward versus inverse transfer. The forward program is byte-exact canonical.
The inverse uses the inferred D4 inverse and inverse color permutation; the new
input grammar requires a bijective demonstrated palette permutation, while query
colors not in that permutation remain unchanged.

A infers exact support geometry and aligns the source example; the aligned color
correspondences are the intermediate; B transfers the learned operator (or its
inverse) to the query. The protected wrong-order program infers the map before
alignment and changes six cells on the retained seed-17 example. Both settings
use identical input draws, 2–6 demos and four novel prefix-stable queries. The
30x30 stress input contains three substantial 30x9 panels plus dividers; its
output is 30x9. This extends the native grammar, not the production sampler.

Self-review: 32 seeds, 320 episodes, all five demo counts, 2,560 pair observations,
320 distinct inputs, all eight transforms, 3/4-color permutations, 21 finite
policies, zero surviving query-disagreeing rivals. The Racket-backed intentional
weak-lesson control demonstrates that the real second demo refutes fixed query
geometry. It is a diagnostic negative, not an alleged production defect.
35 protected audit executions, exact-source qualification and source-bound causal
replay accompany the return. Current README records limits and replay commands.
Reviewer-ready remains owner-pending and does not admit training. Final review
was by the author; no independent reviewer agent was available.


## Current rule and authority

The selected canonical authority is unchanged: infer the first exact-position non-identity D4 transform taking panel 1's support to panel 2, infer the demonstrated nonzero color map, then apply both to panel 3; query colors absent from the demonstrated map pass through unchanged. `RULE_HASH = c4019681eb48`. Generator version `2.0.0`; final reviewed generator SHA-256 is `8eadbf6dd0d5fd933526ff4edcc2b019baa7f6d82ad4482230218b322c4849c3`.

## Reversed baseline decisions

The selected `1.5.0` baseline compared translation-normalized support signatures, generated dense random three-color panels, constrained query colors to the mapped source palette, advertised several inert axes, and had no executable semantic contract. The normalized validator rejected all three canonical examples even though the authority compares full panel coordinates. Dense generated inputs also drifted from the canonical sparse 4×14, 5/8-color support and never taught unmapped-color pass-through.

The repair now:

- compares exact-position binary support and accepts all canonical examples;
- pins the authority hash and provides a Python mirror used only for authoring/tests;
- generates sparse connected 4- or 5-cell panels at sizes 4..6;
- alternates 5-color and 8-color canonical palette profiles in every difficulty band;
- places both mapped and unmapped colors in every query;
- exposes only the observable `transform` and `panel_size` axes and rejects invalid/unknown overrides;
- declares executable witnesses/rivals for identity, transform-only, recolor-only, dropping unmapped colors, and the canonical-fitting unmixed-query shortcut;
- uses two demonstrations plus one query; every generated pair independently refutes all declared rivals, so all three query rotations are supported.

## Evidence

- Final 12-stage strict battery: all green, `checks/after-final/checks/155cf6b30713_after_battery_summary.json`.
- Focused portable regressions: 151 passed; final receipt is produced under `checks/task-tests-final/`.
- Profile floor: 19 exact canonical-profile hits of 60, with easy/medium/hard support `4/7/8`; no crashes.
- Wider lesson census: 300 lessons, 900 pairs, 900 query rotations, 900 unique inputs, zero declared-rival ambiguities or scoring errors; `checks/lesson-census-final.summary.json`.
- Replayable single-lesson diagnostic: `workspace/inspect_lesson.py`; retained example `checks/tool/lesson-991-7.json`.

## Distribution rationale and limits

The 5-color profile includes divider color 5 inside panel 1 to reproduce canonical color/object structure, while rejecting placements that would merge it with the right divider. The 8-color profile uses three demonstrated source/target colors and a mixed mapped/pass-through query, matching the canonical palette-role signature. Panels are short connected paths rather than scattered dense markers.

The finite rival set and 300-lesson census do not prove uniqueness against every possible hypothesis or every seed. The sampler covers panel sizes 4..6, while exact canonical shape support necessarily occurs only at size 4. Training approval remains a maintainer decision.

## Parametric-rule assessment

No separate hidden rule parameter was retained. The transform and color map are already inferred per instance; changing first-match order or unmapped-color behavior would alter canonical semantics and create a different task, not a small safe family variant. Input-side transform, size, palette profile, and layout already provide substantial lawful diversity.
## Current reviewer considerations

Source SHA-256: `8eadbf6dd0d5fd933526ff4edcc2b019baa7f6d82ad4482230218b322c4849c3`.

# Decisions — 155cf6b30713

## D1 — Preserve the canonical Racket authority

**Decision.** Keep rule hash `c4019681eb48` unchanged.

**Reason.** Canonical outputs and the selected Racket program consistently implement an exact-position panel transform, a demonstrated color map, and pass-through of unmapped query colors. The defects were in generation, validation, metadata, and curriculum support—not the authority. `checks/after-final/checks/155cf6b30713_after_authority_sync.json` and rule-smoke evidence bind the final source to the unchanged authority.

**Rejected alternative.** Changing the Racket rule to agree with the old translation-normalized validator would alter the task and invalidate canonical outputs.

## D2 — Replace translation-normalized matching with exact-position D4 matching

**Prior choice.** Baseline `1.5.0` used `_shape_sig`, which normalized foreground coordinates before comparing transforms. It then demanded D4 uniqueness under that normalized signature.

**Problem.** The canonical rule compares the whole binary panel in place. The baseline validator falsely rejected all three canonical examples. The retained witness is `repo/generators/155cf6b30713/counterexamples/review-45912c0c7cb6659e.json` and the original source is `workspace/generator.before-review.py`.

**Decision.** Compare exact binary support matrices for all seven non-identity D4 transforms and follow canonical transform order. Accept canonical queries even when unused transformations happen to share their support; require only that the demonstrated transform is uniquely inferred and visibly changes the query.

**Failure mode considered.** Allowing multiple matching transforms would make the color map or query action ambiguous. `self_check` still requires exactly one non-identity match for panel 1→2.

## D3 — Make the generated distribution sparse and canonical-shaped

**Prior choice.** Baseline generation filled from three cells up to nearly every panel cell, producing dense, scattered three-color textures.

**Decision.** Generate a short self-avoiding path and partition it into connected per-color pieces, with exactly 4 or 5 foreground cells per panel. Alternate two profiles:

- **5-color profile:** two source colors (including color 5), two target colors, and a two-color query; 4 cells per panel. Reject source placements where color 5 touches the right divider, preventing an accidental extra full separator. This reproduces the canonical 8-object/no-marker signature.
- **8-color profile:** three source colors, three target colors, and a two-color mixed-role query; 5 cells per panel. This reproduces the canonical `preserved=2, introduced=0, removed=5` palette-role signature.

Panel sizes remain 4..6 for lawful geometric diversity. Exact canonical profiles occur only at size 4; the final profile floor observed 19/60 exact hits, with easy/medium/hard support `4/7/8`.

**Rejected alternatives.** Merely reducing Bernoulli density still left singleton-marker and palette-role drift. Copying canonical grids would overfit positions and collapse diversity.

## D4 — Teach mapped and pass-through query roles together

**Prior choice.** Every baseline query color came from panel 1's source palette, so every query color was mapped.

**Problem.** Canonical examples include colors absent from the demonstrated map; those colors must pass through. A model trained only on mapped colors could learn “recolor every nonzero query cell.”

**Decision.** Put at least one mapped and one unmapped color in every generated query. Add executable rivals `drop_unmapped` and `unmixed_query_only`, plus witnesses and lesson checks. The counterexample file retains a baseline mapped-only input.

**Evidence.** The source-bound census materialized 300 lessons (two demonstrations plus one query each), 900 labelled pairs, and all 900 query rotations; every declared rival was refuted, with zero ambiguity or scoring errors (`checks/lesson-census-final.summary.json`).

## D5 — Reduce the public override surface to observable controls

**Prior choice.** The baseline advertised palette, texture, density, and position controls that were constant, aliases, or bypassed normal validation. Difficulty bands also made some valid transform/size overrides impossible.

**Decision.** Advertise only `transform` (all seven non-identity D4 codes) and `panel_size` (4..6), honor every joint combination in every band, reject unknown keys, booleans, malformed scalar types, and out-of-range values, and expose `observe_overrides`.

**Evidence.** The compact override matrix ran 2,880 accepted draws across 32 cases with zero findings or warnings (`checks/after-final/checks/155cf6b30713_after_override_results.json`).

## D6 — Use two demonstrations and support arbitrary query rotation

**Decision.** Set `EXAMPLES_NEEDED = 2`; production lessons contain two demonstrations and one query. Do not rely on which pair is held out. Every generated pair individually refutes all five declared rivals, and `lesson_identifiable` checks surviving hypotheses.

**Rejected intermediate.** A `fixed_4x4_only` canonical shortcut was initially considered, but it survived whenever a non-4×4 pair became the query. It was replaced with the genuine canonical-fitting `unmixed_query_only` shortcut, which every generated pair refutes. Failed iteration evidence is retained under `checks/after-semantic/`; final strict rotation evidence is under `checks/after-final/` and the wider census.

## D7 — Keep a Python mirror, but do not treat it as authority

**Decision.** Add `rule_mirror`, exact inference helpers, semantic rivals, and structural probes for tests and authoring. Racket remains authoritative; rule-smoke and authority-sync verify agreement.

**Reason.** A model-free Python mirror makes branch coverage and rivals cheap to test while source-bound Racket checks prevent mirror drift.

## D8 — Add reusable inspection tooling

**Decision.** Add `workspace/inspect_lesson.py` and document it in `workspace/README.md`.

**Output.** For one exact seed/index/band/override request it records generator SHA, rule hash, observed overrides, inferred transform/map, mapped and unmapped query roles, structural signature, and cell-level disagreement for every declared rival. It is covered by the portable tests; `checks/tool/lesson-991-7.json` is a retained example.

## D9 — Parametric-rule assessment: not suitable

I assessed two candidate hidden parameters:

1. **Transform search order.** Changing the first-match order changes which transform is authoritative on symmetric supports and is therefore a different rule, not a safe parameter.
2. **Unmapped-color policy (`preserve` vs `drop`).** This changes a central canonical branch and would require a separate task family; mixing it into this generator would weaken the exact behavior repaired here.

The transform and color map are already per-instance inferred quantities. Input-side panel size, transform, palette profile, and layout provide sufficient diversity without adding a hidden rule variant. No `workspace/parametric/` prototype was retained.

## D10 — Final self-review for newly introduced shortcuts

The repair was checked against identity, transform-only, recolor-only, drop-unmapped, and canonical-fitting unmixed-query hypotheses. A small witness is `checks/tool/lesson-991-7.json`: it has one mapped and one unmapped query color, and all five rivals differ from the authority by at least one cell.

Remaining limitation: this finite rival set is not a proof against every describable shortcut. The 300-lesson random census covers declared rivals and all pair rotations, not every seed or undeclared hypothesis.
