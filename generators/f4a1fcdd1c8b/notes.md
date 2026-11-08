# Working notes: f4a1fcdd1c8b

## 2026-09-28 full review

- Canonical rule retained; pinned `RULE_HASH=9a57908e9c92`.
- Replaced decorative/dead axes with four exact observable axes.
- Added strict validation, semantic observables, Python rule mirror, schedule metadata, rivals, and witnesses.
- Added repeated-color opposite-fate profiles to refute the canonical-compatible global-color shortcut.
- Replaced silent sequential placement truncation with exact all-component placement.
- Added bounded exact-override layout after the first correct search-based implementation made the 25,920-draw override gate too slow.
- Added `tests/test_generator_contract.py`; red-first baseline produced 8 failures, final suite passes 9/9.
- Final inherited battery: 12/12 green; 60/60 exact canonical profiles; 600/600 strict semantic draws; 25,920/25,920 override draws.

Known distribution limits are recorded in the packet-level `REVIEW.md` and `DECISIONS.md`.
## Current reviewer considerations

Source SHA-256: `026551bf9ea3c5259b3e9350514d9c8c7c9e7d218cb3a3b431d65adb51ea6a70`.

# Design decisions: f4a1fcdd1c8b

## 1. Preserve the canonical Racket rule

**Original rationale:** The retained rule and written solution both express border-touching component filtering. Baseline rule smoke already passed 120/120 applications.

**Decision:** Do not alter canonical data or Racket source. Pin the selected source with `RULE_HASH = "9a57908e9c92"` and add an independent Python mirror for parity checks.

**Alternatives considered:** Rewrite/simplify the Racket source; change object semantics. Both would create authority risk without addressing the generator defects.

**Probe:** Final rule smoke reports 120/120 applications and 120/120 mirror agreement.

**Failure modes / limits:** The mirror is a review aid, not authority. Authority synchronization still reports one archival-divergent source, but the selected active authorities are synchronized and execution parity passes.

## 2. Define objects as same-color 4-connected components

**Original rationale:** The canonical output separately treats differently colored components even when adjacent. The written solution says “component,” and the Racket object extraction is color-sensitive.

**Decision:** Flood-fill only cardinally adjacent cells of the same nonzero color. Disconnected regions of the same color remain separate objects.

**Alternatives considered:** Treat all touching nonzero cells as one object; treat each color globally as one object. Both contradict canonical behavior.

**Probe:** Canonical train pairs pass `self_check`, and `rule_mirror` reproduces their outputs. The repeated-color witness proves disconnected same-color components can have opposite fates.

**Failure modes / limits:** Default generated components are spatially separated, so differently colored touching components are accepted but not intentionally scheduled.

## 3. Replace decorative axes with four exact axes

**Original rationale:** Unknown. The imported generator declared eight axes, but most did not affect generation; `border_side` was unprobeable, helpful textures were dead, and `n_distinct_colors`, density, position bias, and palette controls were not consumed.

**Decision:** Declare only `grid_h`, `grid_w`, `n_border`, and `n_interior`. Every one is consumed through `GenCtx`, recoverable from the grid, and exhaustively checked by the override gate.

**Alternatives considered:** Implement every old decorative axis. This would add surface area without a demonstrated task need and would preserve redundant aliases.

**Probe:** Final override contract: 288 cases × 30 seeds × 3 bands = 25,920 accepted exact realizations. Unknown-key and out-of-range tests fail loudly.

**Failure modes / limits:** Palette and morphology remain internally scheduled rather than caller-selectable.

## 4. Anchor ordinary dimensions and palette sizes to canonical profiles

**Original rationale:** The old difficulty schedule expanded easy/hard outside canonical scale; baseline profile support was 3/60 exact and 7/60 envelope with zero support in two bands.

**Decision:** Use four stable profiles at 10x14, 11x15, and 11x16 with palette sizes matching canonical profiles. Difficulty affects deterministic layout/palette streams rather than moving the canvas away from the canonical manifold.

**Alternatives considered:** Preserve large hard grids; use a continuous random range. Both lower canonical support and teach scale changes unrelated to the rule.

**Probe:** Final profile floor is 60/60 exact and 60/60 envelope in all bands.

**Failure modes / limits:** The default canvas distribution is deliberately narrow. Exact overrides still allow the full 8..16 by 9..18 declared range.

## 5. Schedule repeated-color opposite-fate scenes

**Original rationale:** The old generator always assigned a distinct color to each object. All canonical examples do the same, so the wrong rule “keep every cell whose color appears on the border” matched every available example.

**Decision:** Profiles 1 and 3 reuse one border-component color on a disconnected interior component. With a four-slot cycle, every contiguous three-example window contains at least one such counterexample.

**Alternatives considered:** Rely on random color collisions; merely document the shortcut; use a rare edge-case texture. Random/rare evidence does not guarantee lesson identifiability.

**Probe:** The semantic gate confirms the shortcut matches canonical examples, then verifies 60/60 declared rival claims on generated witnesses. The witness fires 299/600 times and in every band.

**Failure modes / limits:** Noncontiguous or independently sampled demonstrations can still omit the witness. The exporter should validate each actual lesson window.

## 6. Cover all border directions

**Original rationale:** The rule is symmetric over top, bottom, left, and right. A top-only distribution would permit a directional shortcut.

**Decision:** Each profile schedules side-specific border components, always including at least one survivor that does not touch the top edge.

**Alternatives considered:** Random side choice only. Random sampling can produce weak windows and gives no deterministic witness guarantee.

**Probe:** `non_top_border_survivor` fires 600/600 times, and `top_border_only` disagrees with the intended rule in every checked rival claim.

**Failure modes / limits:** Corner-touching frequency is incidental rather than a separately declared axis.

## 7. Use deterministic transformed shapes with exact placement

**Original rationale:** The old random-growth approach could fail placement and `break`, silently returning fewer components than requested.

**Decision:** Use a connected shape library of 1..12 cells, generate rotations/reflections, enumerate legal placements, and solve all component placements as one deterministic search. If rich shapes cannot fit, retry all requested components as separated singletons; if that also fails, raise.

**Alternatives considered:** Keep sequential retry loops; reduce requested counts after failure. Both make metadata dishonest.

**Probe:** Self-check and override tests assert exact counts; no generation crashes appear in the official census.

**Failure modes / limits:** The finite shape library does not cover every polyomino. Ordinary scenes avoid object overlap and touching.

## 8. Add a bounded exact-override path

**Original rationale:** The first correct implementation used combinatorial placement for every override-matrix case. The official override gate performs 25,920 draws, and that path exceeded the execution transport budget.

**Decision:** When any exact axis is supplied, realize the requested counts in eight prevalidated singleton slots that work at the minimum 8x9 canvas. Ordinary generation retains rich morphology.

**Alternatives considered:** Cache search results; lower the gate seed count; accept long runtime. The bounded layout is simpler, exact, and independent of process-level caching.

**Probe:** A regression test monkeypatches the search routine to fail and verifies exact overrides still succeed. Official override runtime dropped enough to complete, with 25,920/25,920 accepted.

**Failure modes / limits:** Override-probe morphology is intentionally simple; overrides test semantic axes, not default visual richness.

## 9. Separate ordinary generation from mutation fixtures

**Original rationale:** Degenerate texture names were mixed into `AXES['texture']`, while helpful textures were no-ops.

**Decision:** Keep `all_border`, `all_interior`, and `empty` only as explicit negative fixtures. Declare no helpful textures. Reject texture-plus-exact-axis combinations.

**Alternatives considered:** Make the old warm/cool/varied aliases real. Palette themes are irrelevant to the task and would add distractor controls.

**Probe:** Strict defect lint reports zero findings; no texture-domain overlap or dead helpful texture remains.

**Failure modes / limits:** Negative fixtures intentionally fail ordinary `self_check` invariants.

## 10. Make the semantic contract executable

**Original rationale:** The baseline had comments but no machine-checkable task contract.

**Decision:** Add `self_check`, `strict_canonical_like`, observables, mirror, named rivals, named witnesses, and witness/rival bindings.

**Alternatives considered:** Rely only on static comments or coarse morphology gates. Neither can detect shortcut-teaching data.

**Probe:** Semantic gate: 600/600 strict acceptance, 3/3 witnesses firing, 3/3 rival claims verified, and the canonical-ambiguous shortcut refuted.

**Failure modes / limits:** `self_check` enforces structural legality, not every desired distribution frequency; those frequencies remain the job of census gates.
