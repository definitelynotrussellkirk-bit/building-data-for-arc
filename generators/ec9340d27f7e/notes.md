# Working notes: ec9340d27f7e

## Review record — 2026-09-28

### Baseline

- Battery: 7 green, 2 advisory, 3 failed.
- Missing `RULE_HASH`.
- Strict defect lint: negative textures in ordinary domain and four dead helpful textures.
- Override gate: 20,845 findings, including range mismatches, inert axes, omitted draw provenance, fixed-shape degenerates, and an accepted unknown key.
- Profile floor: 6/60 exact, 10/60 envelope, hard band had zero support.
- Semantic gate: no contract.

### Root hypothesis

The central defect was not random sampling quality. The declared input grammar was wider than the implemented semantics, while the ordinary distribution repeatedly showed only the positive motif. That allowed both API-level false claims and strong rival rules.

### Implemented model

- Immutable canonical rule retained and pinned to `80ec61287499`.
- Public API reduced to exact dimensions and target count.
- Four empirical canonical anchors alternate with four complete contrast profiles.
- Contrast controls refute horizontal-without-equality, vertical, wide-gap, occupied-midpoint, first-only, one-color-only, and identity shortcuts.
- Grid-derived analysis powers self-checking, override observation, strict-profile recognition, witnesses, and lesson auditing.

### Verification

- Official after battery: 12/12 green.
- Focused tests: 14 passed.
- Semantic probe: 96 draws, 48 strict, 8/8 profiles, 9/9 witnesses, 7/7 rivals refuted, 0 lesson failures.
- Authority sync: active selected sources synchronized; execution parity PASS.

### Known limitations

- Contrast examples come from a controlled symbolic template family rather than every possible arrangement.
- Explicit override examples are valid positive scenes, not complete semantic lessons.
- Rolling three-example guarantees assume consecutive sample indices.
- Rival inventories are provisional; add any newly observed shortcut as executable code plus a minimal witness.
## Current reviewer considerations

Source SHA-256: `4843969353f14d101f0281ccf9e6e99b59f832392ac8b1f2181ac9cf05b72bc4`.

# Decisions for `ec9340d27f7e`

The canonical Racket program is the authority. “Original rationale” below refers to the imported generator when recoverable from its comments; where no measurement or provenance existed, it is marked unknown.

## Decision matrix

| Input choice | Original rationale | Alternatives considered | Probe/evidence used | Failure modes and limitations |
|---|---|---|---|---|
| Keep the canonical rule unchanged | The packet identifies the canonical row as authority; the imported generator was intended to model the same local horizontal completion rule. | Edit the Racket rule; reinterpret motifs as chain-level objects. | All canonical pairs were run through an independent Python oracle and `rule_mirror`; rule smoke and authority sync both pass. | A generator cannot prove the canonical rule is philosophically unique. It can only teach and test the pinned executable semantics. |
| Pin `RULE_HASH = 80ec61287499` | No original pin existed. | Continue relying on prose; pin a base-bank raw source instead. | Normalized canonical program hash and lint gate. | Hash changes require an explicit review even for semantically equivalent source edits; that is desirable fail-closed behavior. |
| Expose only `grid_h`, `grid_w`, and `n_gaps` | Imported code exposed dimensions, palette controls, chain length, density, position bias, texture, and color count. No measured rationale was recorded, and several were inert or contradictory. | Repair every old axis; mark inert axes diagnostic; expose motif topology and control counts. | Baseline override gate found 20,845 findings and omitted provenance for several exact axes. New boundary matrix covers all 2×2×2 boundary combinations across four difficulty labels. | The smaller API gives callers less direct artistic control. New axes should be added only with observable semantics and full Cartesian tests. |
| Dimensions 5..8 by 7..10 | Imported defaults were broader and difficulty-dependent; exact rationale unknown. Canonical dimensions occupy 5..7 by 7..10. | Use canonical dimensions only; preserve the prior 5..14 ranges; allow arbitrary ARC dimensions. | Canonical-profile census plus packing proof for five targets in the smallest 5×7 grid. | Very large canvases are not represented. The chosen envelope favors canonical morphology and dense semantic evidence over scale diversity. |
| Exactly 3..5 lawful gaps | The canonical examples contain 3, 4, or 5 changed cells. The imported generator had a broader, partly indirect motif API. | Allow 1..8 targets; expose chains and pairs separately; infer count from difficulty. | Canonical pair analysis, profile gate, override boundary tests, and `observe_overrides`. | It does not test single-target or extremely dense cases. Multiple targets are retained because they refute identity and first-target-only rivals. |
| Exactly three nonzero colors | Imported generator exposed palette size/kind, but helpful palette textures were inert. Original reason for those controls is unknown. | One color only; two colors; arbitrary 1..9 palette. | Canonical palettes contain zero plus three nonzero colors; distribution and diversity gates pass. | Fixing the palette cardinality does not test palette-size generalization. Colors themselves vary, and at least two must serve as target colors. |
| Four empirical canonical anchors | Imported generation only occasionally matched canonical profiles and had zero hard-band support. | Fully random scenes; literal replay of canonical inputs; one pooled anchor. | Extracted exact dimension, target-count, row-count, and nonzero-count signatures from all four canonical inputs. Profile floor improved from 6/60 exact to 32/60. | Anchors intentionally preserve some canonical ambiguity; contrast profiles must remain paired with them. |
| Four complete contrast profiles | No original semantic contrast design existed. | One counterexample per rival; random distractors; caller-only degenerates. | Rival search against canonical pairs identified orientation, equality, adjacency, occupied-center, first-target, and one-color shortcuts. Official semantic gate verifies all declared claims. | A fixed family of controls can itself become recognizable. Random transforms/colors and multiple profile shapes reduce but do not eliminate template learning. |
| Put the full control bundle in each contrast draw | Original negative textures were caller-only and leaked into a valid texture domain. | Spread controls over many draws; make each control a separate texture; sample controls independently. | `EXAMPLES_NEEDED = 3`; every three-consecutive-example window was tested at all difficulties. | Bundled controls are information-dense and less “natural” than sparse independent controls. They were chosen to guarantee identifiability under a small lesson budget. |
| Alternate anchors/contrasts through an eight-profile deterministic schedule | Original schedule was RNG/difficulty driven; rationale unknown. | Pure random mixture; four-profile cycle; hard-code anchor then contrast pairs. | Exhaustive rolling-window tests and semantic-gate schedule census. No cycle contains three consecutive anchors. | The local guarantee depends on consecutive sample indices. A consumer that reseeds or shuffles independently should inspect the profile metadata/census. |
| Offset schedules by difficulty without changing semantics | Imported difficulty changed ranges and caused declared override ranges to be rejected. | Give each difficulty different dimensions/counts; ignore difficulty; use difficulty to alter control strength. | Same full semantic and override tests were run over `None`, easy, medium, and hard. | Difficulty is currently curriculum ordering, not objective ARC complexity. This avoids semantic drift but gives only a mild difficulty distinction. |
| Use a positive-only generic builder for explicit overrides | The old override paths clamped/fell back, rejected declared values, or returned fixed degenerate shapes. | Force the contrast template into every dimension/count combination; declare incompatibility sets; reject small combinations. | All 4,860 official override draws pass and every requested value is observable. | Override-generated grids are valid but do not necessarily contain all shortcut controls. Ordinary scheduled generation is the teaching path. |
| Remove public helpful/degenerate textures | Imported `default/warm/cool/varied` were dead and negative textures were mixed into the valid domain. | Repair palette textures; retain negative textures under a diagnostic axis; declare lawful degenerates. | Strict defect lint now reports zero flags; no texture axis remains to be silently ignored. | Future diagnostic fixtures must live outside the ordinary exact-axis contract or be given explicit incompatibility/semantic declarations. |
| Require multiple target colors and same-color opposite fates in contrasts | Original generator could be explained by color-specific or “change every occurrence” rules. | Rely on random color variation; test only multiple colors globally. | `multiple_target_colors` fires 600/600; `same_color_opposite_fate` fires on every contrast draw in the official census. | Canonical anchors need not individually contain opposite fates; lesson-level mixing supplies the disambiguation. |
| Keep all scene analysis independent of generated metadata | The imported self-check mostly checked motif counts. | Return hidden metadata; trust construction; inspect only shape/palette. | `self_check`, witnesses, and `observe_overrides` recompute facts from grid cells. Mutation tests delete support and require rejection. | Some properties, such as construction provenance, are intentionally not inferable and therefore not claimed. |
| Add executable rivals rather than prose-only warnings | No original rival-rule inventory existed. | Describe shortcuts only in notes; test only the strongest rival. | Seven rivals are run against generated outputs, with explicit witness-to-rival mappings and lesson-level eliminations. | Rival sets are never exhaustive. Future failures should add the newly observed shortcut as executable code and a minimal witness. |
| Build a standalone semantic census tool | Original workspace contained no reusable audit tool. | Rely solely on the official gate; add ad hoc notebooks. | `workspace/semantic_probe.py` is exercised by pytest and emits deterministic JSON suitable for future agents. | It mirrors task-local contracts and is not a replacement for Racket execution or the official battery. |

## Stopping decision

I stopped after the complete official battery was 12/12 green, the focused regression suite was 14/14 green, the semantic probe had full witness/rival coverage with zero lesson failures, and the immutable authority checks passed. No unresolved blocking failure remains.
