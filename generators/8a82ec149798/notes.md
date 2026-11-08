# Working notes: 8a82ec149798

## Review identity

- Assignment: `review-2ee863ac1f5e56cf`
- Baseline generator SHA-256: `1d7d319ef4ccc9f542b4a29b5da122d54f990bed07648de860ed459494ac3c92`
- Revised generator SHA-256: `1a9b416c4fc1b2023f478c91c760aa34cb4a51dbce7bbddc1571b6f6a8bd1484`
- Selected rule hash: `40243de2441c`
- Canonical ledger SHA-256: `1966140b2d15b3c90521b3334d55760b9143ea25b8673aa7e4c91630462c285b`

## Canonical reconstruction

The selected Racket program finds the first full color-5 column, creates a blank output, preserves all gray cells, preserves every non-{0,5} cell left of the axis, and paints its horizontal mirror. Right-side input marks are not sources. Unrelated right marks disappear; marks already occupying mirror targets are overwritten by the corresponding left source color.

All four canonical pairs match this interpretation. Canonical train example 0 contains unrelated right-side color-7 marks and proves that “right half must be empty” is not a valid checker invariant.

## Baseline findings

`checks/before/` records 6 green, 1 advisory, and 5 failed stages:

- missing `RULE_HASH` and unprobeable metadata;
- canonical input rejected by `self_check`;
- 0/59 destructive mutations rejected in the baseline self-check stage;
- dead helpful textures and contradictory degenerate textures;
- exact canonical profile only 3/60, envelope 21/60;
- no semantic contract;
- 9,513 override findings across 100,440 draws / 1,116 cases, including accepted unknown keys.

The Racket smoke, grammar, Racket lint, and selected authority checks were already sound, so no rule edit was justified.

## Implemented contract

Public axes are exactly `grid_h`, `grid_w`, `n_sources`, `n_source_colors`, `axis_profile`, and `distractor_mode`. Every accepted value is observable from the output grid. Unknown and invalid keys reject.

The legal grammar requires:

- dimensions 6..8 by 9..11;
- one full gray axis at center or center ±1 and no other gray cells;
- 2..7 mirrorable left sources in exactly one or two colors;
- no right marks, or exactly two same-color distractor cells in erase, overwrite, or mixed configuration;
- distractor color distinct from source colors;
- non-identity under the reconstruction.

Five consecutive sample indices cover `canonical_erase_noise`, `left_offset_clean`, `overwrite_targets`, `canonical_clean`, and `right_offset_multicolor_mixed`. Difficulty changes layout/palette realization while preserving that profile.

## Semantic contract

Named witnesses:

- off-center axis;
- multiple source colors;
- unrelated right noise;
- occupied mirror targets;
- multiple sources.

Named rivals:

- fixed geometric center;
- single source color;
- preserve unrelated right marks;
- do not overwrite right marks;
- first source only.

`lesson_identifiable` also checks leave-input-unchanged and erase-without-mirroring competitors and requires the five demonstrations to cover all axis/distractor controls and both source-color counts.

## TDD history

1. Seven initial contract tests failed against version 2.0.1.
2. The rewrite made six pass; the remaining failure exposed two accidental `copy.deepcopy` calls after importing `deepcopy` directly. The error was reproduced and fixed at the namespace source.
3. `defect_lint` then detected byte-identical difficulty bands. A failing test was added before difficulty-sensitive layout/palette logic.
4. A failing integration test required a source-bound probe. Its first run exposed that direct packet execution lacked the staged `scripts` namespace expected by `rule_wrap`; the probe now exposes `shared/tools` as an in-memory namespace package without copying source.
5. Final source review added a branch-specific regression for a rival that fits every demo but changes the query; it exposed one remaining unimported namespace reference. The regression failed first, the call now uses the imported `deepcopy`, and all hash-bound evidence was replayed.
6. Final focused tests: 10 passing.

## Final evidence

`checks/after/` records 12/12 green stages for the revised generator hash:

- 4/4 canonical inputs accepted;
- 120 Racket calls, zero crashes, 120/120 mirror parity;
- exact canonical profile 41/60, envelope 53/60;
- strict semantic profile 243/600 (40.5%);
- 5/5 witnesses and 5/5 rivals verified;
- 12/12 lessons identifiable;
- 18,270 override draws / 203 cases with zero findings;
- 100% unique inputs and outputs in the diversity stage.

`workspace/review_probe.py` produced `checks/review_probe_after.json`: 136 actual Racket calls, zero failures, zero difficulty collisions, exact invalid-override rejections, and first concrete counterexamples for every rival.

The final focused suite passed 10/10 tests. The repository-wide suite passed 131/131 tests with the packet Racket runtime enabled (zero skips).

## Limitations

The generator teaches a deliberately compact grammar rather than every input the Racket program can mechanically process. The rival set is strong but finite. The Python mirror is never label authority. Review completion does not itself grant approval; candidate integration and explicit assessment remain required.
## Current reviewer considerations

Source SHA-256: `1a9b416c4fc1b2023f478c91c760aa34cb4a51dbce7bbddc1571b6f6a8bd1484`.

# Design decisions for `8a82ec149798`

Each decision below records the original rationale when recoverable, the selected alternative, the probe that supports it, and the cost if the decision is wrong.

| ID | Input/design choice | Original rationale | Alternatives considered | Probe and result | Failure mode / limitation |
|---|---|---|---|---|---|
| D1 | Keep the selected Racket rule unchanged. | The imported generator summary assumed a simple mirror rule, but the actual canonical program was the stronger authority. | Rewrite Racket to match the old “empty right half” story; or change only the generator. | All four canonical outputs matched the selected Racket program; final rule smoke made 120 calls with zero crashes and 120/120 mirror parity. | If an unseen canonical authority intended different behavior, the generator would teach the selected source rather than that unseen intent. The repository’s authority-sync gate is therefore retained. |
| D2 | Admit right-side marks as lawful distractors. | Unknown; old code rejected them despite canonical train example 0 containing them. | Require an empty right half; allow arbitrary right noise; allow a small explicit distractor grammar. | Canonical example 0 proves erase-noise is lawful. Generated overwrite and mixed cases produce Racket-backed rival counterexamples. | Arbitrary right patterns are not generated; the contract deliberately uses exactly two control cells for noisy modes. |
| D3 | Bound grids to 6..8 rows and 9..11 columns. | Old implementation exposed broader dimensions that did not reflect the four canonical shapes and were frequently ignored. | Preserve old broad ranges; use only exact canonical dimensions; use a small envelope. | Canonical shapes are 6..8 by 9..11. Final profile floor accepts 4/4 canonical and reaches 53/60 envelope support. | This excludes larger grids that the Racket rule could mechanically process but that lack canonical evidence. |
| D4 | Use 2..7 left sources and one or two source colors. | Old source count/palette controls were inconsistently implemented. Canonical examples use one source color and 5..7 sources. | Canonical-only one-color data; arbitrary many colors; minimal two-source witnesses. | Canonical examples are retained; a two-color profile refutes the single-color shortcut; all 600 semantic samples contain multiple sources. | Two colors are enough to falsify the shortcut, but do not explore every palette cardinality. |
| D5 | Place the full gray axis at center or one column left/right of center. | Old generator effectively taught a fixed divider placement. Canonical examples are centered, so center-only data admits a geometric-center shortcut. | Center only; unrestricted axis; center ±1. | Off-center witnesses fire 229/600 times in the official semantic gate and refute the fixed-center rival in all 60 checked claims. | Larger offsets are excluded to keep every source mirrorable across all supported widths and preserve a compact teaching grammar. |
| D6 | Define four right-distractor modes: none, erase, overwrite, mixed. | Old “cells_on_right” negative fixture contradicted the canonical rule and checker. | No noise; arbitrary noise; explicit semantic controls. | Official semantic evidence includes 232/600 unrelated-noise cases and 247/600 occupied-target cases, with both rivals refuted. | Each noisy mode uses exactly two same-color distractor cells; more complex noise morphology is not represented. |
| D7 | Rotate five fixed semantic profiles over every five consecutive sample indices. | No reliable old lesson-level schedule existed. | Independent random draws; a long stochastic curriculum; a short deterministic covering schedule. | Every five-slot window covers all named profiles. The official gate reports 12/12 identifiable lessons over all three bands; the Racket probe reports 4/4 clean windows per band. | Correlated fixed profiles may be easier to classify by superficial shape if a consumer always preserves sample order; seed-dependent rotation reduces but does not eliminate that risk. |
| D8 | Let difficulty alter surface form, not the semantic curriculum. | The first rewrite accidentally made easy, medium, and hard byte-identical. | Let bands change semantic frequency; ignore difficulty; hold semantics fixed and vary palette/layout. | A test first reproduced equality across bands. The final probe finds zero collisions while `observe_overrides()` remains identical for the same profile. | Difficulty is a surface-complexity signal, not a measured solver difficulty score. |
| D9 | Reject unknown and invalid overrides. | Old `**overrides` behavior silently accepted typos and ignored many declared axes. | Ignore unknown keys; clamp values; strict rejection. | Baseline override gate found 9,513 findings and accepted unknown keys. Final gate passes 18,270 draws/203 cases with zero findings and rejects unknown keys. | Strictness may break callers relying on undocumented typo-tolerance; that break is intentional because silent fallback corrupts provenance. |
| D10 | Make `self_check` validate the complete lawful grammar. | Old checker checked a much narrower story and rejected canonical noise while accepting destructive impostors. | Minimal “does Racket run” validation; canonical-only validation; explicit structural grammar. | Final self-check accepts 4/4 canonical inputs, is clean on 60 defaults, and rejects 46/68 destructive mutations. | Some destructive mutations remain lawful instances of the same sparse task, so rejection is not expected to be total. |
| D11 | Declare strict signatures, witnesses, rivals, and lesson identifiability. | The baseline had no semantic contract. | Rely only on rule smoke; add distribution statistics; require semantic counterexamples. | Official semantic gate moves from advisory/no-contract to green: 5/5 witnesses, 5/5 rivals, 12/12 lessons. | Named rivals are a high-value finite set, not proof against every possible shortcut. |
| D12 | Keep a Python mirror only as a diagnostic. | A Python oracle is convenient but could silently become a second, drifting label authority. | Use Python as authority; omit a mirror; use it only for parity assertions. | Official rule smoke reports 120/120 parity; the independent probe always obtains labels from Racket first. | Mirror and Racket could share a conceptual mistake, so canonical-pair checks remain mandatory. |
| D13 | Add a reusable source-bound Racket probe in the task workspace. | The packet’s standard stages summarize outcomes but do not retain one compact, replayable counterexample census for future reviewers. | Prose-only notes; a Python-only probe; a Racket-backed JSON probe. | `checks/review_probe_after.json` records 136 Racket calls, source hashes, exact rejections, witness counts, and first rivals’ counterexamples with zero failures. | It samples deterministic windows rather than exhaustively enumerating all seeds and overrides. |
