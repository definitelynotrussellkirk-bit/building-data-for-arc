# Working notes: 4c17a205be08

## Baseline defects

The imported generator was not a faithful curriculum for the selected task. It varied dimensions away from 5×17, used dense random panel fills, collapsed canonical fragmentation to one non-background component, had weak separator-only validation, silently accepted unknown overrides, declared dead/overlapping textures, lacked `RULE_HASH`, and had no semantic or lesson contract. The before battery recorded four blocking failures and two advisories; see `checks/before/checks/4c17a205be08_before_battery_summary.json`.

## Repair

Version `3.0.0` fixes geometry at the canonical 5×17 layout and generates sparse 2×2 through 3×3 crops with explicit occupied-cell axes. A and C patterns are required to have six distinct outputs under the rule's six transforms. The draw alternates component profiles so complete inputs have six or seven non-background components, uses canonical palette sizes 5/6, and cycles all six transform branches. Overrides are limited to `transform`, `exemplar_cells`, and `query_cells`; `observe_overrides` round-trips them and unknown keys raise.

`self_check` now validates the entire grammar and unique A→B relation. `strict_canonical_like`, semantic witnesses/rivals, `CANONICAL_SHORTCUTS`, and `lesson_identifiable` make the teaching objective executable. The selected Racket rule and canonical row were not changed.

## Verification highlights

- Final task-local tests: 10 passed.
- Final independent battery: all 12 stages green.
- Canonical profile floor: 60/60 exact and 60/60 envelope hits.
- Semantic census: 600/600 strict-canonical draws; all six branches fired in every difficulty band.
- Rule smoke: 120/120 applied without crash; Python mirror parity 120/120.
- Override matrix: 6,120 draws, zero findings/warnings; unknown-key probe rejected.
- Workspace audit: 24 valid draws with four instances per transform, balanced palette/component profiles, and 18/18 identifiable lesson windows.

## Known limits

The ordinary domain intentionally excludes empty, symmetric, malformed, or separator-damaged panels because those do not identify the rule. The generator follows the canonical six-transform family rather than all eight square dihedral operations (diagonal reflections are not in the authority). The repository-wide suite has one unrelated environment-sensitive timeout test still failing; the selected task battery and tests are green.
## Current reviewer considerations

Source SHA-256: `bc804b9fdda08451fbd63dbfb2918d0f1e1e84074d71db7cf97973555722fe2b`.

# Design decisions — 4c17a205be08

## D1 — Preserve the selected authority; repair the curriculum

The Racket program already maps all five canonical pairs correctly and passed baseline rule smoke/authority checks. The defects were in input generation and validation, not the selected rule, so I left the canonical row and Racket source unchanged. Changing the authority would have introduced unnecessary semantic risk.

## D2 — Fix geometry at 5×17 instead of keeping arbitrary panel sizes

The old generator's dimension variability had no canonical support: the profile probe measured 0/60 exact and 0/60 envelope hits. Every canonical input is 5×17 with three 5×5 panels and full color-9 separators at columns 5 and 11. The new generator treats this as grammar, not a cosmetic choice.

Rejected alternative: continue varying panel dimensions and opt out of the profile floor. That would preserve more superficial diversity while training a distribution unsupported by the task.

Failure mode controlled: separator-only solvers and dimension-dependent shortcuts. `self_check` now rejects malformed geometry and separators before semantic inference.

## D3 — Generate sparse canonical crops, not dense random rectangles

Canonical A crops contain 4–6 occupied cells and C crops 3–5 (the generator permits 3–6 to keep the hard band useful); crop dimensions are 2–3 in both axes. I enumerate tiny sparse support/color patterns and keep only those with the requested occupied-cell/component profile and six distinct transform images.

Rejected alternative: mutate the old dense fill probabilities. Dense fills frequently create symmetric or near-full crops, collapse components, and make multiple transforms observationally equivalent.

Probe: task-local tests exercise all cell-count/transform override combinations; `strict_canonical_like` and the semantic census accepted 600/600 final draws.

## D4 — Explicitly schedule all six authoritative transforms

Canonical demonstrations cover only CW, 180, CCW, and LR. Identity and UD are absent, so the strongest plausible rival learns only the four observed commands and defaults elsewhere. `schedule_profile(seed, sample_index)` cycles all six branches, and every consecutive six samples covers the family exactly once.

With five demonstrations per episode, any cyclic five-window contains five distinct branches and necessarily contains identity or UD, refuting the four-command shortcut. The reusable audit checked all six start residues across three difficulty bands: 18/18 windows identifiable.

Rejected alternative: independent random transform draws. Random draws can omit branches or repeat one enough to leave fixed-transform rivals alive in short lessons.

## D5 — Match linked palette and fragmentation profiles

The canonical linked profiles are `(height=5, width=17, palette=5)` and `(5,17,6)`. I alternate one/two query colors to realize those palette sizes. Separators contribute two components; alternating `(A components=1, C=2)` and `(A=2, C=1)` yields complete-input component counts 6 and 7, matching the canonical median 6.5.

Rejected alternative: force a single canonical profile. It would pass a floor but erase useful linked variation and create an easy parity shortcut.

Probe: the 24-draw workspace audit measured 12 draws of each palette size and 12 draws of each component count.

## D6 — Make every semantic axis observable and reject typos

The old axis list included unprobeable dimensions, dead textures, and semantic axes with no `observe_overrides`; unknown keywords were silently ignored. I reduced the public contract to three causal axes: transform, A occupied-cell count, and C occupied-cell count. `observe_overrides` reports exactly those realized values, and unknown keys raise `ValueError`.

Rejected alternative: retain legacy axes as diagnostic aliases. That would keep a misleading API and allow the override matrix to report false confidence.

Probe: the final override matrix executed 6,120 draws with zero findings/warnings; the unknown-key probe was rejected.

## D7 — Validate the relation, not just the layout

`self_check` now checks rectangular literal grids, exact geometry, separators, reserved colors, nonempty crops, A/B palette preservation, C palette disjointness, and exactly one legal transform mapping A to B. `strict_canonical_like` adds palette, crop-scale, occupied-cell, and component-profile constraints. `_teaching_reasons` additionally requires all six transform images to be distinct for A and C.

Rejected alternative: allow symmetric lawful examples and rely on first-match semantics. Such examples are executable but poor teaching data because the demonstrated operation is not identifiable.

## D8 — Encode rivals and lesson success as executable contracts

The semantic contract includes six fixed-transform rivals, copy-panel-B, and `observed_transform_family_only`. Per-transform witnesses check branch coverage and disagreement. `lesson_identifiable` requires valid outputs, five distinct branches, at least one canonical-missing branch, and elimination of every declared competitor.

This is stronger than relying on distribution statistics: profile match cannot show that the rule is learnable or that a plausible shortcut is refuted.

## D9 — Build a reusable reviewer tool

`workspace/audit_curriculum.py` loads canonical pairs and the current generator, then emits canonical shortcut fit, exact first generated witnesses, branch/palette/component counts, invalid examples, and all scheduled lesson-window results. It is deliberately Python-mirror based for speed and labels that limitation; protected-Racket probes and battery reports remain authority-backed evidence.

TDD record: `checks/audit-tool-red.log` shows the test failing because the tool did not exist; `checks/audit-tool-green.log` shows it passing after implementation.

## D10 — Retain failed iterations and out-of-scope failures

The first complete after-battery launch was terminated by the outer execution harness after roughly 300 seconds. Its runtime journal proves lint, selfcheck, rule smoke, and defect lint had already passed; buffered console output made it appear stuck at defect lint. I preserved that attempt under `checks/interrupted-after-outer-timeout/` and reran detached; the final run completed 12/12 green.

The repository-wide suite's one streaming-timeout failure was reproduced five times and not patched because only selected-task files may change. A 0.2/0.3-second timeout captures no child output on this host; 0.5/1.0 seconds does. The remaining 143 tests pass when that case is deselected.


## D11 — Keep the source patch representable and rebind hash-sensitive evidence

The first return-package attempt failed before ZIP creation because the frozen baseline module docstring contained a source line beginning with `--`. In a deletion hunk, the unified-diff deletion marker produced a line beginning `--- `, and the static patch validator misclassified it as a file header. The exact traceback is retained in `checks/package-failure-triple-hyphen.log`.

I restored the frozen baseline module docstring verbatim. This changes no executable behavior, public contract, rule hash, or Racket authority, but it prevents the unchanged troublesome line from appearing as a deletion. A direct `_patch_paths` probe then accepted all seven changed task paths. Because source identity is byte-sensitive, I regenerated task tests, curriculum/shortcut evidence, the complete 12-stage battery, and the reviewer solve. The old solve remains under `checks/prior-solve/`; the final solve is bound to generator SHA-256 `bc804b9fdda08451fbd63dbfb2918d0f1e1e84074d71db7cf97973555722fe2b`.
