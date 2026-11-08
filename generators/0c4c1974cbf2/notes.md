# Working notes: 0c4c1974cbf2

## Current intended rule

A centered full-height color-8 bar divides an odd-width zero-background grid. For each nonzero left cell, inspect its exact reflection on the right. Start from a blank output and place color 2 at the reflected right position iff both input positions are nonzero. Input colors do not affect overlap membership; the bar and all non-overlap cells disappear.

Canonical authority is unchanged and pinned by `RULE_HASH = "ceb28731a942"`. The Python `rule_mirror` is audit-only; Racket remains authoritative.

## Decision reversal

**Prior choice (v2.2.1):** broad off-center-bar sampling with nine advertised controls and random lessons. It guaranteed a left-only decoy but no right-only decoy, exposed aliases/dead controls, and had no executable lesson contract.

**New choice (v3.0.0):** centered bar; five exact axes (`grid_h`, `half_w`, `left_cells`, `overlap_count`, `palette_size`); two transformed canonical-profile anchors plus three contrast-rich schedule slots; strict scalar/unknown-key handling; executable witnesses and rivals.

**Reason/evidence:** baseline battery had 3 failed and 2 advisory stages, including 16,246 override findings and zero canonical profile hits. A retained six-pair baseline probe shows the wrong `mark_every_right_cell` rule fits 6/6 authoritative labels because right-only objects were absent. The final source has a 12/12 green battery, 163/163 portable tests, 300/300 materialized census lessons with zero declared-rival ambiguity, and exhaustive five-start/query-rotation probe coverage.

## Distribution assumptions

- Positive grids are 5–14 rows with 2–7 columns per half and a centered bar.
- There are 5–8 left cells, 2–4 exact overlaps, and 2–4 non-bar colors.
- Every generic contrast scene includes left-only, right-only, same-color overlap, different-color overlap, non-red constant-output, and same-row wrong-position witnesses.
- The two anchor slots preserve the canonical 7×11 and 7×13/two-color envelopes after bounded transforms and recoloring.
- Degenerate textures are negative fixtures, not positive training controls.

## Known limits and open findings

- Identifiability evidence is finite and relative to the declared eight rivals plus shared generic candidates; it is not a proof against all hypotheses.
- The positive domain does not teach off-center fold bars.
- The schedule's true period is five, but the public period declaration is omitted because the current shared semantic gate warns without enumerating it. Task tests and `workspace/lesson_probe.py` exhaust the five starts; shared-tool feedback requests native support.
- The post-repair visible-only solve passed all demonstrations, but masked-query correctness is intentionally unknown to the reviewer.
## Current reviewer considerations

Source SHA-256: `973d449491497081dd3a005d16c1e1ae067b15ab725c61307fc04f025d1ca162`.

# Design and repair decisions for `0c4c1974cbf2`

## D1 — Keep the canonical authority unchanged

**Prior state.** The generator description and emitted structures had drifted from the canonical task, but the Racket rule itself executed consistently on canonical and generated inputs.

**Decision.** Do not edit the canonical Racket row. Pin `RULE_HASH="ceb28731a942"` in the generator and make the Python audit mirror match the selected canonical authority.

**Evidence.** The after rule-smoke stage applied 120 samples with 120 mirror matches and no execution defect. Authority sync reports selected-source parity while correctly retaining a divergent archival copy as archival history.

**Rejected alternative.** Changing the rule to preserve unrelated input cells or support the baseline generator's broader off-center narrative would redefine the puzzle and erase a sound authority to accommodate weak data.

## D2 — Center the bar and make width structural

**Prior choice.** Version 2.2.1 sampled an off-center bar inside a general width, despite all canonical inputs using a centered bar. That broadened geometry without teaching it and contributed to the generator/authority structural mismatch reported by defect lint.

**New choice.** Represent width as `half_w`; emit an odd grid of width `2*half_w+1` with the full-height color-8 bar at the center.

**Reason.** This is the canonical support, makes reflection exact and easy to validate, and removes an unnecessary nuisance variable from a task whose intended semantic difficulty is the two-sided occupancy conjunction.

**Rejected alternative.** Continue supporting arbitrary bar columns and add more axis metadata. That spends examples on bar-location generalization while leaving fewer examples to distinguish the actual overlap rule.

**Limitation.** The positive training domain no longer claims off-center generalization.

## D3 — Replace nine advertised controls with five observable axes

**Prior choice.** The baseline advertised `grid_h`, `grid_w`, `palette_kind`, `overlap_count`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`. Several were aliases, constants, ignored, or inconsistent with generation; the baseline override stage retained 16,246 findings.

**New choice.** Expose only `grid_h`, `half_w`, `left_cells`, `overlap_count`, and `palette_size`. Every value is drawn through a strict keyed control and reconstructed by `observe_overrides`.

**Reason.** A public control is useful only when callers can predict and verify its observable effect. The reduced surface supports the full legal endpoint cross-product without silent clamping or aliases.

**Rejected alternative.** Keep compatibility aliases such as `grid_w`, `palette_kind`, and `n_distinct_colors`. Silent or partial compatibility would preserve precisely the ambiguity that the override gate found.

## D4 — Use a five-slot schedule with two anchors and three contrast scenes

**Prior choice.** Ordinary examples were random independent draws. They guaranteed a left-only negative but did not guarantee right-only, color equality, constant-red, or row-decoy evidence in a complete three-demonstration lesson.

**New choice.** Slots 0–1 are transformed/recolored canonical-profile anchors; slots 2–4 are complete contrast scenes. `EXAMPLES_NEEDED=3` remains the lesson size.

**Reason.** The two anchors preserve canonical shape/palette support. With only two consecutive anchors, every cyclic window of three demonstrations includes at least one complete contrast scene, so lesson adequacy does not depend on a lucky random draw.

**Rejected alternatives.** All-random lessons were cheaper but could repeat the old shortcut. All-anchor lessons preserved source appearance but the canonical pairs admit `same_color_only`. Four or more demonstrations were unnecessary once one contrast scene refuted the finite rival set.

## D5 — Put all key semantic contrasts in each generic scene

Each contrast scene contains:

- one left-only source;
- one right-only object;
- one same-color exact overlap;
- one different-color exact overlap;
- at least one non-red overlap whose output must be red;
- a left-only and right-only cell sharing a row but not a reflected position.

This single-scene bundle refutes one-sided occupancy, color-equality, color-copy, row-local, and copy-input rules without requiring cross-example bookkeeping. The layout constructor treats these as hard witnesses and fills remaining cells only after reserving them.

A weaker alternative—distribute one witness across each schedule slot—was rejected because query rotation or duplicate rejection could remove the one decisive example.

## D6 — Preserve canonical anchors as support masks, not literal replay

The 7×11 and 7×13 canonical input masks are transformed by a bounded vertical shift, optional within-half reflection, and deterministic recoloring. The color-8 bar and support relationships remain intact.

This gives exact canonical profile hits without duplicating canonical examples byte-for-byte. Literal replay would improve profile metrics while adding little distribution value; unconstrained synthetic anchors could miss the characteristic supports again.

## D7 — Bound counts to constructive, teachable ranges

The final domain uses height 5–14, half-width 2–7, 5–8 left cells, 2–4 overlaps, and 2–4 object colors. The constructor supports every legal boundary combination tested by the task suite.

These limits keep enough cells for all required witnesses while avoiding large sparse canvases whose extra area adds little semantic information. Counts above these ranges were not needed to teach the rule and would increase rejection/packing complexity.

## D8 — Fail invalid calls and retired controls loudly

Seeds and sample indices must be true integers, sample indices must be nonnegative, difficulty must be recognized, axis values must be strictly typed/in range, and unknown keys are rejected. Negative textures are explicit fixture calls and are never reported as positive-domain override successes.

The baseline accepted unknown or misleading controls; preserving permissive coercion would make source-bound replay and curriculum provenance unreliable.

## D9 — Declare executable witnesses and rivals

Seven witnesses map to eight pure deterministic rivals. The task's `lesson_identifiable` hook requires every declared rival to fail on the demonstrations, not merely to agree on the current query. `same_color_only` is separately declared as a canonical shortcut because it fits all canonical pairs.

A textual-only semantic description was rejected: the baseline had a plausible prose rule but no machine-checkable way to detect a lesson that taught the wrong shortcut.

## D10 — Retain negative fixtures, but remove them from the positive control surface

`no_bar`, `no_overlap`, and `all_overlap` remain deterministic mutation fixtures for validator tests. They are not helpful textures and are rejected by the positive-domain self-check where appropriate.

The old overlap between helpful and degenerate texture contracts caused lint ambiguity and joint override failures. Keeping the fixtures separately preserves diagnostic value without misrepresenting them as lawful training samples.

## D11 — Do not publicly declare a schedule period until the shared gate can consume it cleanly

An intermediate source declared the true five-slot period. The semantic gate then emitted a nonblocking warning because that shared stage does not enumerate the declaration itself. The failed/advisory iteration is retained under `checks/intermediate/semantic_gate2/`.

The declaration was removed, while exhaustive five-start coverage was kept in `tests/test_generator_0c4c1974cbf2.py` and `workspace/lesson_probe.py`. This avoids a misleading public contract while preserving stronger evidence. `FEEDBACK_TO_CODEX.md` requests shared period enumeration so a future version can restore the declaration honestly.

## Known limits

- Identifiability is measured only against the declared finite rival set plus the generic candidates used by shared tooling.
- Positive examples use a centered bar.
- The count and palette bounds are intentionally narrower than all logically valid inputs.
- The census samples 300 production lessons; the task probe exhausts schedule starts for one deterministic seed structure, not every seed.
- Masked-query solve correctness is not available to the reviewer.

## Native parametric family — 2026-10-25

The production generator and canonical authority remain unchanged. The new native
adapter at `workspace/parametric/` keeps exact canonical `pair_mode=overlap` as
the default and adds the nearby `pair_mode=exclusive` rule, which selects
reflected pairs with exactly one occupied side. Both rules share the same
input-dependent first stage (classify every pair across the centered bar); the
second stage consumes that selected-pair list and paints its right coordinates.

The adapter supports 2–6 demonstrations and 1–4 query projection while retaining
four distinct private queries. Query four is a dense 30x29 boundary stress case.
Across 128 seeds, 22,016 contract assertions passed. The complete task suite is
187/187 green; native qualification executed 32 protected-Racket labels, and a
two-direction causal witness replayed both overlap→exclusive and
exclusive→overlap counterfactuals. A finite audit of overlap/exclusive/union,
one-sided, color-equality and wrong-side shortcuts found no rule that fit both
minimum demonstrations while changing a qualified query. Sixteen saved
single-query public views passed identity/privacy structure checks.

Evidence: `checks/0c4c1974cbf2/qualification/`,
`checks/0c4c1974cbf2/causal/`,
`checks/0c4c1974cbf2/adversarial-teaching.json`, and
`checks/0c4c1974cbf2/public-export-check.json`. These are finite reviewer checks,
not universal identifiability, measured training gain, owner acceptance, or
training admission.
