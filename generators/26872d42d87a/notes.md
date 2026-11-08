# Working notes: 26872d42d87a

## Current authority and contract

- Canonical rule hash: `bc262329ef0d`; the Racket authority was **not changed** in this review.
- Intended transformation: change an original `0` to `6` iff its immediate left and right input neighbours are both `6`. Evaluate from the input, not incrementally.
- Current selected source: `generator.py` version `3.0.0`, SHA-256 `50a1cff760fcb53d4ae76279ca83fe5a54f270903cd2f467bd9eed2195b879c6`.
- Exact profiles are the five canonical `(height,width)` pairs. Inputs use exactly colors `{0,5,6}`, with one or two color-5 border decorations and at least three true horizontal gaps in at least two rows.

## 2026-10-11 repair

The pinned baseline (`0860d736008b069fa7b7656ee9f659a303f4f73451c5b40c92c124fc1f06bf63`, version `2.1.0`) generated only alternating one-cell gaps. Therefore two plausible rules fit all five labeled canonical pairs and all sampled baseline inputs:

1. fill every zero between a row's outermost color-6 cells;
2. apply the local `6,0,6` rule both horizontally and vertically.

The inherited review leads were the retained findings under `counterexamples/review-3f5238ad09cbf112-v0001/` and `counterexamples/review-56319963af7c7673-v0001/`; both were treated as hypotheses and rechecked against the pinned source. The baseline also lacked `RULE_HASH`, rejected four canonical inputs because it treated particular corner-5 placements as mandatory, advertised dead/overlapping texture axes, silently swallowed unknown overrides, and conflicted with its own difficulty bands. The before battery records 6 green, 1 advisory, and 5 failed stages in `checks/before/checks/26872d42d87a_before_battery_summary.json`.

The repair:

- pins `RULE_HASH` and adds a pure Python authority mirror;
- replaces nine misleading controls with one observable `scene_profile` axis;
- cycles all five canonical profiles in every band;
- includes a wider horizontal near-miss and a vertical near-miss in every ordinary input;
- declares both canonical-fitting shortcuts as executable semantic rivals;
- makes `self_check` robust on malformed values and broad enough to accept every labeled canonical input without requiring generated-only witnesses;
- rejects unknown difficulty values, unknown controls, wrong types, and out-of-domain exact values;
- adds focused tests plus `workspace/qualify.py` for canonical, override, shortcut, and query-rotation replay.

## Decisions and reversals

- **Reversed:** fixed corner-5 positions were previously part of validation. Canonical evidence shows one or two border decorations in several positions, so validation now checks role and count rather than coordinates.
- **Reversed:** broad numeric size and texture controls were previously advertised despite being dead, overlapping, or incompatible with band ranges. The public contract now exposes only the exact, pixel-observable profile choice.
- **Rejected:** adding a wider gap only occasionally. A rare witness could still leave complete lessons shortcut-compatible; both near-misses are present in every input instead.
- **Rejected:** requiring the negative witnesses in `self_check`. They are teaching-support requirements for generated samples, not properties of every lawful canonical input.
- **Kept:** the palette and five exact canonical shape profiles. This is intentionally conservative and avoids unsupported color-role or geometry extrapolation.

## Evidence and limits

- Final 12-stage battery: all green at the selected source hash; `checks/after/checks/26872d42d87a_after_battery_summary.json`.
- Focused tests: `23 passed`; final receipt under `checks/task-tests-final/`.
- Required-rotation semantic smoke: pass; `checks/required-rotations/`.
- Shared Racket-labelled census: 300 lessons, 1,200 pairs/rotations, 1,200 unique inputs, zero production or rotation ambiguities; `checks/lesson-census.json`.
- Task-local source-only census: 300 unique inputs; both witnesses and both shortcut counterexamples in 300/300; zero ambiguous rotations across 1,200; `checks/qualification.json`.
- Retained dual-shortcut witness: `counterexamples/local-rule-shortcuts-v3.json`, with Racket receipt `checks/final-counterexample-racket.json`.

These finite checks establish coverage only against the declared rivals and sampled seeds. They do not prove universal rule identifiability against every possible hypothesis. The generator deliberately stays inside canonical sizes/palette rather than claiming broader task-domain support.

## Current audit resolution

Whole-span shortcut repaired: v3 places wider horizontal and vertical near-miss objects in every input and checks the named rival. Retained witnesses and reported 300-lesson/1200-rotation evidence address both prior findings; this is a specific closure, not automatic clearing on source change. Full prior findings and retained evidence pointers: `evidence/current-audit-assessment.json`.
## Current reviewer considerations

Source SHA-256: `50a1cff760fcb53d4ae76279ca83fe5a54f270903cd2f467bd9eed2195b879c6`.

# Distribution and implementation decisions for 26872d42d87a

## D1 — Keep the selected authority unchanged

- **Prior choice:** the baseline omitted `RULE_HASH`; its Python distribution nevertheless targeted the selected canonical rule.
- **Decision:** pin `RULE_HASH = "bc262329ef0d"`, add an independent Python mirror for tests and semantic rivals, and leave the Racket source untouched.
- **Why:** all five canonical labels and the existing rule smoke supported the immediate-horizontal-neighbour law. The defect was distributional and contractual, not an authority mismatch.
- **Probe:** before/after `rule_smoke`, `racket_lint`, and `authority_sync`; retained Racket witness in `checks/final-counterexample-racket.json`.
- **Failure mode avoided:** “repairing” the rule to match a shortcut would corrupt canonical authority rather than teach it.
- **Limit:** the Python mirror is supplementary; Racket remains label authority.

## D2 — Use five exact canonical scene profiles

- **Prior choice:** independent `grid_h`/`grid_w` ranges varied by difficulty and did not reproduce all canonical dimensions reliably; validation imposed extra coordinate assumptions.
- **Alternatives considered:** retain broad ranges; expose separate exact height and width; or use one profile token.
- **Decision:** expose one `scene_profile` axis for `8×10`, `9×11`, `10×12`, `9×10`, and `10×11`; cycle all five in each band.
- **Why:** a profile token is exactly observable from returned pixels, preserves canonical support, and avoids advertising unsupported cross-products.
- **Probe:** 15 exact override cases (five profiles × three bands) in `checks/qualification.json`; override and profile-floor stages are green.
- **Limit:** this deliberately does not test geometry outside canonical sizes.

## D3 — Put both negative branches in every ordinary input

- **Prior choice:** all rows with multiple 6s used alternating one-cell gaps. Original rationale is not recorded; likely it mirrored the most visually salient canonical rows.
- **Alternatives considered:** sample wider gaps or vertical patterns occasionally; reserve a special texture; rely on a four-example schedule.
- **Decision:** each input gets one wider horizontal `6...6` span and one vertical `6,0,6` span, both unchanged by the authority.
- **Why:** occasional negatives can still leave a complete lesson compatible with a shortcut. Per-input support makes production order and arbitrary query rotation robust to the two known canonical-fitting rivals.
- **Probe:** both witnesses and both shortcut counterexamples occur in 300/300 task-local samples; shared Racket-labelled census reports zero ambiguities in 300 production lessons and 1,200 query rotations.
- **Failure mode avoided:** correct labels whose demonstrations still teach a simpler wrong rule.
- **Limit:** only the declared whole-span and orientation rivals were exhaustively replayed.

## D4 — Validate lawful canonical grammar, not generated-only teaching structure

- **Prior choice:** validation treated two particular corner-5 placements as mandatory and rejected four of five canonical inputs.
- **Alternatives considered:** require the new wider/vertical witnesses in `self_check`; accept any palette/size; or mirror the generator exactly.
- **Decision:** require one of the five canonical dimensions, exactly colors `{0,5,6}`, one or two border 5s, and at least three horizontal triggers in at least two rows. Do not require generated-only negative witnesses.
- **Why:** validators should accept lawful canonical inputs; semantic gates and focused tests should enforce teaching support for generated samples.
- **Probe:** all five labeled pairs pass `self_check` and the Python mirror; malformed/out-of-domain grids return diagnostics.
- **Limit:** the strict grammar is conservative and may exclude lawful but unseen generalizations.

## D5 — Collapse the old control surface

- **Prior choice:** nine axes included aliases, fixed single-value controls, dead helpful textures, and degenerate textures; unknown keys could be swallowed by `**overrides`.
- **Decision:** keep only `scene_profile`; reject unknown axes, bad types/values, and unknown difficulty names.
- **Why:** exact controls must be recoverable and honored. Unobservable controls create false reproducibility and confound dataset audits.
- **Probe:** final override stage has no findings; focused negative tests cover invalid profile values, legacy keys, typos, and type errors.
- **Rejected alternative:** retain legacy names as aliases. Aliases would preserve ambiguity and add no useful sampling degree of freedom.

## D6 — Deterministic profile cycle plus independent keyed layout draws

- **Decision:** `schedule_profile` uses `sample_index % 5`; layout randomness remains keyed by seed/sample/version.
- **Why:** every consecutive five samples cover all exact profiles without relying on hash order, while positions, trigger lengths, and decorations remain diverse.
- **Probe:** 100 samples per band cover all five profiles and produce at least 90 unique grids in focused tests; the full census produced 300/300 unique inputs.
- **Limit:** profile frequency is uniform by construction rather than matching any empirical canonical frequency estimate.

## D7 — Add a portable, source-only qualification tool

- **Decision:** add `workspace/qualify.py`, tested both in the staged runtime and direct repository context.
- **Why:** future agents need a fast replay of canonical ownership, exact controls, semantic witnesses, declared rivals, and all query rotations without rerunning the full Racket battery.
- **Failed attempt:** the first CLI version imported the staged task package and failed in repository context. The red receipt under `checks/qualification-loader-red/` reproduces that boundary; the final loader imports `generator.py` directly and its passing follow-up is under `checks/qualification-loader-green/`.
- **Limit:** the tool trusts the Python mirror for bulk labels. The shared battery and lesson census provide independent Racket binding.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/26872d42d87a/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
