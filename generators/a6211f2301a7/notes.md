# Working notes: a6211f2301a7

## Repair diagnosis

Baseline generator SHA-256: `99894ec130dc99e9d27e793f7b35d1d0e2b546d6f58807299919f148298454be`.

The before battery collected all twelve stages and ended 7 green, 2 advisory, 3 failed. Blocking defects were missing `RULE_HASH`, dead/overlapping texture controls, exact overrides that did not match returned dimensions, accepted unknown keys, and a permissive self-check. The hard band had 0/20 exact canonical-profile hits, and there was no executable semantic contract.

No earlier return was used as authority. Packet notes and check output were treated only as leads; every count in the final review comes from this packet’s retained before/after receipts.

## Final design

- Pin canonical rule hash `aad722fb766b`; do not alter Racket authority.
- Enumerate a finite lawful shape catalog instead of rejection-sampling masks.
- Expose only five pixel-observable exact controls.
- Reject unknown and malformed overrides.
- Enforce zero border padding, bounded boxes/cells/colors/components, and nonidentity rotation.
- Alternate five canonical profile anchors with broad tall examples.
- Declare the canonical-fitting `portrait_normalizer` rival and a `tall_bbox` counterexample witness.
- Guarantee every three consecutive unforced samples includes a tall witness.

Final generator SHA-256: `afa5d9d8c4040757a622d8d4d36ee6ce745a43dc76ca9f732abd03a5f9c0d23f`.

## Verification

- Focused selected-task tests: 46/46 passed.
- Final battery: 12/12 green, no advisory or failed stages.
- Profile floor: 30/60 exact hits overall; easy 11/20, medium 11/20, hard 8/20.
- Semantic census: 600/600 strict; tall witness 291/600; witness disagreed with rival in 60/60 checked cases.
- Source-bound lesson audit: 100/100 lessons per band refuted the rival, across starts 0 and 1.
- Exposed post-repair solve: first revision passed all 3/3 visible examples; earlier exposure declared yes.

## Failed and intermediate approaches retained

A first lesson check that relied only on random broad orientation found that some three-example windows could remain compatible with the portrait-normalizer. That failure motivated the deterministic odd-index tall schedule and its regression test.

An initial full lesson-probe route materialized complete public episodes and was too slow for a 300-lesson run. The retained reusable probe instead generates exact selected inputs and batches only the minimum source-bound witness labels through public `Catalog.apply`; it records the same generator/rule identity and completed the final audit.

## Limitations

The generator’s strict manifold is intentionally smaller than the complete Racket authority domain. The lesson evidence assumes three demonstrations sampled consecutively under the default parity schedule and tests only declared rivals. Broad default examples intentionally overrepresent tall boxes; explicit overrides still construct and test all three orientations.
## Current reviewer considerations

Source SHA-256: `afa5d9d8c4040757a622d8d4d36ee6ce745a43dc76ca9f732abd03a5f9c0d23f`.

# Decisions: a6211f2301a7

## D1 — Keep the canonical authority unchanged

The selected Racket rule already implements the coherent task: tightly crop all nonzero cells, then rotate the crop 90° clockwise. Baseline rule smoke, Racket lint, and authority sync were green, and the final authority-sync receipt reports execution parity. I therefore pinned `RULE_HASH = "aad722fb766b"` and changed no Racket or canonical-data file.

Rejected alternative: changing the authority to match the baseline sampler’s narrower behavior. That would hide generator defects by redefining the task, and no authority evidence justified it.

## D2 — Replace the advertised control surface instead of patching dead axes

The baseline advertised controls including texture variants, palette controls, density, position bias, and duplicate color-count concepts. Several were singleton, overlapping, unused, or not recoverable from returned pixels. The final exact controls are:

| Axis | Domain | Observable meaning |
| --- | --- | --- |
| `grid_h` | integer 7–13 | returned row count |
| `grid_w` | integer 7–13 | returned column count |
| `n_colors` | integer 1–3 | number of distinct nonzero colors |
| `bbox_orientation` | `wide`, `tall`, `square` | orientation of the tight nonzero box |
| `component_count` | integer 1–3 | number of four-connected nonzero components |

Every domain value is constructively reachable. Unknown keys, booleans masquerading as integers, out-of-range integers, and invalid enum values reject before generation. The final override battery reports no findings or warnings and rejects its unknown-key probe.

Rejected alternatives:

- Retain `palette_kind`, `palette_size`, and `n_distinct_colors` as separate controls. They encode overlapping pixel facts and invite contradictory combinations.
- Retain texture names such as symmetric or border-touching motifs. Those names mixed lawful teaching cases with deliberate degeneracies and made exact override semantics difficult to falsify.
- Silently ignore unknown controls for compatibility. This turns typos into false passes and was an explicit baseline failure.

## D3 — Use a finite constructive shape catalog

The motif box is restricted to 2–4 rows by 2–4 columns, with 3–8 occupied cells and 1–3 four-connected components. All masks must touch every side of their tight box; square masks invariant under a clockwise rotation are excluded. A cached finite catalog is keyed by `(orientation, components, height, width, cell_count)`, so generation chooses from a known lawful set rather than repeatedly drawing and rejecting candidates.

Rationale:

- The ranges cover the canonical scales while giving enough shape and topology variation to defeat fixed-template shortcuts.
- Constructive availability makes exact overrides testable without probabilistic failure.
- Excluding rotation identities ensures each lesson demonstrates a visible transformation.
- One-cell zero padding makes the crop boundary unambiguous and preserves the canonical presentation style.

Rejected alternatives:

- Pure rejection sampling over arbitrary small masks. It complicated override guarantees and could make rare combinations fail nondeterministically.
- Fixed motif templates or canonical replay. They would raise profile counts while preserving shape-memorization shortcuts.
- Larger boxes and much denser objects immediately. They add breadth but are not needed to repair the measured contract, and they would weaken the claim that the sampler remains canonical-like.

Limitation: this finite shape manifold does not represent every lawful input to the Racket rule. It is a bounded teaching distribution, not a formal characterization of the authority domain.

## D4 — Preserve canonical profile support with five anchors

The five canonical inputs have exact `(grid_h, grid_w, total palette size including zero)` profiles:

- `(8, 9, 4)`
- `(9, 8, 4)`
- `(7, 10, 2)`
- `(8, 8, 3)`
- `(9, 9, 4)`

Even sample indices cycle through corresponding anchors. Each anchor fixes the canvas size, number of nonzero colors, orientation, component count, and a preferred motif scale/cell count, but still samples shape, colors, placement, and assignments. This reproduces profile support and two-component morphology without copying canonical grids.

Measured effect: exact profile support rose from 8/60 baseline draws to 30/60 final draws, and hard-band support rose from 0/20 to 8/20. The final 100-lesson-per-band probe saw canonical-profile occurrences in 220/400 easy, 214/400 medium, and 200/400 hard inputs.

Rejected alternative: leave profiles wholly random. The baseline hard band produced zero exact or envelope hits in its 20-draw check, so pooled diversity was masking a band-specific distribution gap.

## D5 — Make the strongest canonical-fitting rival executable

All five canonical tight boxes are wide or square. Therefore this rival fits every canonical pair:

> Crop to nonzero content; rotate clockwise only when the crop is wide or square; leave a tall crop unchanged.

The generator declares it in both `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, links it to a `tall_bbox` witness through `WITNESS_RIVALS`, and supplies the executable rival implementation used by the semantic gate and task-local probe. The exact counterexample and public Racket output appear in `QUESTION_ANSWER.md` and `checks/lesson-probe-final.json`.

Rejected alternative: declare a rival only in prose. That would not permit automatic canonical-fit or counterexample checks and would allow documentation to drift from behavior.

## D6 — Guarantee lesson-level identifiability, not just witness frequency

The first broad implementation sampled orientations freely. A focused curriculum test showed that some three-demonstration windows could contain only wide/square boxes and therefore remain compatible with the portrait-normalizer. The final schedule alternates anchors and broad draws, and every unforced broad draw is tall. Consequently every three consecutive default samples, for either parity start, contain a tall counterexample.

The source-bound audit tests both cyclic starts 0 and 1, 50 independent lessons per start, and all three difficulty bands. It measured 300/300 lessons refuting the rival. This is stronger than reporting an aggregate tall frequency because it checks complete lesson windows.

Rejected alternatives:

- Merely increase the random probability of tall boxes. A nonzero witness rate still permits unlucky all-wide lessons.
- Put tall cases only in a special difficulty band. That leaves other bands ambiguous.
- Force all examples tall. That would eliminate canonical wide/square support and create an equally narrow orientation shortcut.

Trade-off: broad default orientation is intentionally skewed to tall. Explicit orientation overrides remain available and tested, but the unforced schedule is optimized for identifiability rather than balance.

## D7 — Make `self_check` describe the actual training manifold

The final self-check validates:

- nonempty rectangular ARC-valued grid;
- canvas 7–13 by 7–13;
- zero border padding;
- nonempty motif;
- tight box 2–4 by 2–4;
- 3–8 occupied cells;
- 1–3 nonzero colors;
- 1–3 four-connected components;
- nonidentity under a clockwise turn.

`strict_canonical_like` delegates to the same contract. This prevents the baseline pattern in which degenerate samples passed an overly permissive validator.

Rejected alternative: accept every grid on which the Racket rule can execute. The generator’s training manifold is deliberately narrower than the authority domain; the validator should state that narrower promise exactly rather than pretending to prove universal lawfulness.

## D8 — Test first at the behavior boundary

The selected task now has focused tests for source identity, all exact controls, malformed overrides, profile anchors, lawful generation, strict rejection cases, nonidentity, semantic declarations, witness disagreement, and the “every three consecutive defaults” curriculum guarantee. The initial contract suite failed against the baseline; after the implementation and curriculum correction, the final suite passes 46/46.

The general battery does not discover this directory automatically, so the exact task test command is retained separately in `RESULTS.json` and `checks/focused-tests-final.log`.

## D9 — Build a reusable source-bound lesson probe

`workspace/probe_distribution.py` imports the exact selected generator, iterates the actual semantic registries, measures every generated input, and labels only the minimum witness subset needed to support each lesson/rival claim through public canonical `Catalog.apply`. It records generator, rule, canonical-ledger, and probe hashes; all source-bound Racket receipts; uniqueness and distribution counts; domain limits; and first disagreements.

The first implementation attempted to materialize every complete episode through the heavier public generation path. A 300-lesson audit exceeded the available command window and provided poor progress visibility. The final implementation uses direct exact generator inputs plus batched public `Catalog.apply` labels; the full 300-lesson report completed with five label batches and preserved the same source-binding requirement.

Rejected alternative: copy a Python implementation of the correct rule into the probe. That would let generator and probe share the same mistake and would not establish agreement with the selected Racket authority.

## D10 — Preserve honest solve and audit scope

The blind solve was completed before opening the assigned generator. The post-repair solve was performed after rule exposure and is explicitly marked exposed; no attempt was made to relabel it blind or claim hidden-query success. The two adversarial audit targets were not modified, even though concrete shortcut findings were reproduced, because the assignment requested findings only.

## Evidence map

- Baseline battery: `checks/before/checks/a6211f2301a7_before_battery_summary.json`
- Final battery: `checks/after/checks/a6211f2301a7_after_battery_summary.json`
- Final focused tests: `checks/focused-tests-final.log`
- Final lesson probe: `checks/lesson-probe-final.json`
- Audit findings: `checks/audit/*/comparison.json`
- Blind solve: `solve-blind/summary.json`
- Exposed final solve: `solve/summary.json`
