# Working notes: aea86d2776f1

## Baseline leads

No prior task-specific patch was integrated or reused. The current selected baseline, canonical examples, and the packet’s derived assignment metadata were the leads. The before battery was interrupted after five stages, but its completed evidence was decisive:

- lint failed for missing `RULE_HASH` and non-probeable/dead axes;
- defect lint found input-shape drift, dead texture claims, and comment-only archival authority divergence;
- self-check, rule smoke, and the coarse distribution gate were green.

The old generator claimed a fixed `5×11` grammar while padding the bottom/right, sampled commands and template palettes independently, and had no executable lesson rivals.

## Repair decisions

- Pin the unchanged canonical Racket rule as `RULE_HASH = "5d25ec4af105"`.
- Restore the exact `5×11` input contract rather than teaching irrelevant padding.
- Advertise only six controls recoverable from pixels: template occupancy, template color counts, source balance, and transform count.
- Construct connected 3×3 occupancy masks whose four command transforms are distinct.
- Repeat a four-profile schedule so any four consecutive pairs contain one exact canonical-profile anchor and three broad counterexamples.
- Make every generated source sequence nonalternating. Three of four profiles are multicolor and have at least one template whose nonzero bounding box is offset from the frame.
- Declare executable rivals and witnesses, plus `lesson_identifiable`, `rule_mirror`, `observe_overrides`, and `semantic_signature`.
- Salt difficulty through a bijection on transform residues. This changes pixels in easy/medium/hard without changing any declared axis or task semantics.
- Synchronize the selected task’s archival `racket_target.target_code` to its unchanged raw/canonical text; the removed divergence consisted only of two injected comments.

## Test-driven iterations retained

1. The first task-local suite failed 29 tests (plus one direct-runtime skip) on the baseline: no rule pin, no observable controls, ignored invalid overrides, padded shapes, no schedule/rivals, and weak outside-region validation.
2. The rewritten generator passed 39 direct tests and 40 tests under the protected Racket wrapper.
3. Official lint then detected a perfect default correlation between `right_colors` and `source_balance`. A regression test failed first; changing one scheduled source balance broke the correlation while preserving all lesson witnesses.
4. Defect lint then detected byte-identical difficulty bands. A regression test failed first; the transform-residue bijection fixed it without changing declared axes.
5. Final focused wrapper run: 42/42 tests passed. Final aggregate battery: 12/12 stages green.

## Measured final evidence

Generator SHA-256: `d4384636c01f65149ead14c557223008b830feb51dc28b7450584b7a163127a0`.

- canonical profile floor: 5/5 canonical inputs accepted; 24/60 exact-profile hits;
- semantic gate: 600/600 strict, 3/3 witnesses firing, 3/3 rival claims verified, 12/12 sampled lessons identifiable;
- rule smoke: 120/120 applied and mirrored, 0 crashes, 120 distinct outputs;
- override matrix: 23,490/23,490 draws accepted across 261 cases and three bands;
- production lesson census: 300 lessons, 1,200 pairs, 1,200 query rotations, 1,200 unique inputs, zero ambiguities or hook/scoring errors;
- task-local cyclic probe: the same 300/1,200 scale across all four schedule starts, zero failures; rival disagreements were 1,200 source, 900 monochrome, and 900 crop cases.

## Remaining limits

This is finite evidence against three explicit rivals, not a proof of unique induction. The input frame and two-template/4-command grammar are intentionally fixed because the Racket authority reads fixed coordinates. Template occupancies are restricted to connected asymmetric shapes with 3–8 cells, and color counts to 1–3; those are curriculum choices rather than logical requirements of the rule.
## Current reviewer considerations

Source SHA-256: `d4384636c01f65149ead14c557223008b830feb51dc28b7450584b7a163127a0`.

# Decisions for `aea86d2776f1`

Generator SHA-256 for the final measurements: `d4384636c01f65149ead14c557223008b830feb51dc28b7450584b7a163127a0`.

## D1 — Restore the exact `5×11` fixed-coordinate input

**Choice.** Emit exactly five rows and eleven columns, with commands at row 0 columns `1,3,7,9` and templates in rows `2..4`, columns `1..3` and `7..9`.

**Original rationale.** The baseline's reason for adding random bottom/right padding was not documented. It may have been intended as harmless shape diversity, but the Racket rule reads fixed coordinates and ignores the padding, so the extra area was not task substance.

**Alternatives considered.** Keep padding and advertise it as a distractor; or modify the Racket rule to locate panels dynamically. The first teaches irrelevant zeros and contradicts the fixed-shape summary; the second changes the task rather than repairing its generator. Both were rejected.

**Probe/failure mode.** Baseline defect lint reported shape/summary drift. Final `strict_canonical_like`, self-checks, task tests, profile floor, and grammar checks enforce the exact frame. Limitation: the generator intentionally does not explore translated/scaled layouts because the authority does not support them.

## D2 — Use connected asymmetric `3×3` occupancies

**Choice.** Each template has 3–8 four-connected nonzero cells. Its occupancy must produce four distinct results under identity, clockwise rotation, horizontal reflection, and 180° rotation.

**Original rationale.** The old free-form/random panel sampling was not accompanied by a documented identifiability argument. Symmetric panels can make command residues observationally indistinguishable.

**Alternatives considered.** Permit all masks and reject only when a sampled lesson happens to be ambiguous; or use a small hard-coded template list. Precomputing the complete connected/asymmetric catalog gives broad seeded variation while preventing avoidable transform collisions before lesson assembly.

**Probe/failure mode.** The task tests enumerate shape invariants and transform distinguishability. Rule smoke produced 120 distinct outputs from 120 inputs. Limitation: disconnected templates and the all-nine-cells mask are excluded even though the Racket rule could technically transform them.

## D3 — Make occupancy and color counts the only panel controls

**Choice.** Public axes are `left_cells`, `right_cells` in `3..8` and `left_colors`, `right_colors` in `1..3`.

**Original rationale.** The baseline advertised texture-like controls, but the completed before evidence showed those claims were dead/non-observable. No defensible original reason for those names was found.

**Alternatives considered.** Preserve compatibility aliases for the dead axes, or expose low-level RNG/style knobs. Both would make provenance claim properties that cannot be reliably recovered from the generated pixels. The repair instead rejects unknown keys and records only exact observable values.

**Probe/failure mode.** `observe_overrides` round-trips the six controls, and the final override stage accepted all 23,490 expected draws. Color assignment guarantees every requested template color appears. Limitation: color count is capped at three to keep each small shape legible; the rule itself accepts more colors.

## D4 — Control source balance and transform count, not raw command codes

**Choice.** `source_balance` is the number (1–3) of the four commands selecting the left template. `transform_count` is the number (2–4) of distinct transform residues.

**Original rationale.** Independent random commands in the baseline could accidentally reproduce the canonical alternating-source shortcut or fail to expose multiple transforms. There was no documented lesson-level contract.

**Alternatives considered.** Expose each command code as an axis; use fully uniform codes; or force all four transforms and a 2/2 source split always. Per-command axes are cumbersome and encourage memorization, fully uniform draws have no witness guarantee, and an always-fixed pattern would narrow diversity. Aggregate controls preserve observability while allowing command ordering to vary.

**Probe/failure mode.** Every generated source pattern explicitly excludes `ABAB` and `BABA`, both sources occur, and at least two transform classes occur. Exact Racket-backed evidence is retained in `checks/shortcut-witness/`. Limitation: source balance 0 or 4 is excluded because it leaves one template unused.

## D5 — Use a four-profile repeating curriculum

**Choice.** Repeat `canonical_core`, `multicolor_left`, `multicolor_right`, `dense_counterexample`. The defaults are:

| Profile | L cells | R cells | L colors | R colors | L-source commands | transforms |
|---|---:|---:|---:|---:|---:|---:|
| `canonical_core` | 5 | 5 | 1 | 1 | 2 | 4 |
| `multicolor_left` | 4 | 6 | 2 | 1 | 3 | 3 |
| `multicolor_right` | 7 | 3 | 1 | 3 | 3 | 2 |
| `dense_counterexample` | 4 | 8 | 2 | 2 | 1 | 4 |

**Original rationale.** No source-bound baseline schedule existed. Random independent lessons could contain witnesses in aggregate without placing them in each learner-visible window.

**Alternatives considered.** Pure random sampling, a three-slot schedule matching `EXAMPLES_NEEDED`, and a single always-dense profile. Random sampling cannot guarantee lesson identifiability; three slots leave no spare pair for rotating the query; one dense profile loses a clean canonical anchor and creates stronger profile regularities. Four slots permit three demonstrations plus one query, with every held-out rotation checked.

**Probe/failure mode.** The shared census checked 300 production lessons/1,200 rotations; the task-local probe additionally enumerated all cyclic starts. Both found zero declared-rival ambiguity. An intermediate default table accidentally made `right_colors` perfectly correlate with `source_balance`; official lint found it, a regression test reproduced it, and the `multicolor_left` balance was changed from 2 to 3. The schedule remains finite and could admit undeclared rivals.

## D6 — Preserve literal colors and full-frame transforms

**Choice.** Three profiles use multicolor templates; three expose at least one nonzero bounding box offset inside its `3×3` frame. The whole frame is transformed, including zeros.

**Original rationale.** Canonical demonstrations can be explained by monochrome occupancy-only copying and by cropping each nonzero bounding box before transforming. The baseline did not deliberately refute either interpretation.

**Alternatives considered.** Add arbitrary colored noise outside panels, or make every example maximally multicolor/full-offset. Noise would be semantically irrelevant; maximal complexity would obscure the clean command codebook. Scheduled minimal counterexamples target only the rival assumptions.

**Probe/failure mode.** Declared witnesses are `multicolor_template` and `offset_template_bbox`; executable rivals are `monochrome_templates` and `cropped_templates`. They disagree in 900 of 1,200 exhaustive rotations each, and every complete demonstration set contains a disagreement. Limitation: not every individual pair refutes both rivals.

## D7 — Differentiate difficulty without adding a hidden axis

**Choice.** Apply a band-specific bijection to transform residues: easy/medium/hard use offsets 0/1/2 modulo four.

**Original rationale.** Initially the same seed/index generated byte-identical puzzles in all bands because the framework does not automatically salt RNG streams by difficulty. Defect lint flagged the dead band.

**Alternatives considered.** Declare difficulty as an axis; change shape density by band; or ignore the warning because semantic difficulty is similar. Declaring an internal framework argument as a user override is misleading, and changing profile defaults by band would complicate lesson guarantees. A residue bijection changes visible commands/outputs while preserving all declared controls and the rule.

**Probe/failure mode.** A test first demonstrated equality across bands, then passed after the mapping. Final defect lint is clean. Limitation: the bands differ in instances rather than in a claimed monotonic reasoning difficulty.

## D8 — Pin but do not rewrite the Racket rule

**Choice.** Add `RULE_HASH = "5d25ec4af105"`; leave the canonical Racket row unchanged. Synchronize the selected archival bank's `racket_target.target_code` to its already-identical raw/canonical behavior by removing two injected comments.

**Original rationale.** The archival duplicate had drifted textually even though its behavior was the same. The generator itself had no rule pin.

**Alternatives considered.** Patch the canonical rule to validate dynamic layouts, or leave comment-only divergence. A semantic rule change was unnecessary and riskier; leaving divergence kept authority-sync evidence noisy.

**Probe/failure mode.** Authority sync reports synchronized exact/normalized groups and execution parity PASS. Rule smoke and the independent apply witness execute rule hash `5d25ec4af105`. Limitation: the archival file is changed textually, but no executable semantics or canonical authority changed.

## D9 — Make rival elimination executable and reusable

**Choice.** Implement `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, semantic witnesses/signatures, `lesson_identifiable`, and independent tools under `workspace/`.

**Original rationale.** The baseline had prose claims but no executable competitor contract. Frequency counts alone cannot show that each three-demo lesson eliminates a rival.

**Alternatives considered.** Keep one-off analysis in notes, or rely solely on the shared semantic gate. Reusable code is less error-prone, and the task-local cyclic probe covers the shared census's documented omission of all cyclic schedule windows.

**Probe/failure mode.** `reference_probe.py` does not import production rule helpers. `cyclic_lesson_probe.py` reads the actual rival registries, verifies each claimed shortcut fits all usable canonical pairs, rotates every query, and records source hashes/replay data. Its final report is `checks/cyclic-lesson-probe-final.json`.

## D10 — Retain failed iterations and stop after source-bound replay

**Choice.** Preserve the incomplete before run, the correlation failure (`checks/lint-v1/`), the dead-band failure (`checks/defect_lint-v1/`), and the stale/interrupted launcher artifact (`checks/defect_lint-v2/`). Do not relabel them as successful checks.

**Original rationale.** Required by the review contract and useful for distinguishing actual regressions from final claims.

**Alternatives considered.** Delete intermediate evidence to simplify intake. Rejected: the return guide explicitly asks for genuine failures/counterexamples. The final acceptance claim relies only on `checks/after-final/`, `checks/task-tests-final/`, the two final census reports, and fresh-packet replay evidence.
