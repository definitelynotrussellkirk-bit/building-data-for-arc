# Working notes: e5525362bfb8

## Current rule and domain

Review `review-c0456ed9fa5e1369` advances version `3.1.0` to `4.1.0`.
The unchanged canonical rule (`RULE_HASH = 7aef5b5cd6e6`) detects color-3 cells with four cardinal color-3 neighbors, considers every diagonally aligned center pair, and paints only zero cells between them red (2). Existing green pixels remain intact. Python rival functions are deliberately incomplete alternatives and never generate labels.

The reviewed generator is intentionally bounded: rectangular integer 0/3 inputs, 8..24 rows and columns, two through five complete plus centers, every green cell in a complete plus footprint, and at least one aligned pair with a paintable zero cell. This includes all four canonical inputs (three have labels). The validator accepts some lawful four-center arrangements; the constructive sampler emits the five named two/three/five-center families. It is not a complete sampler of the broader Racket input domain.

## Decisions reversed and evidence

- **R1 — two centers and gap >=4 to all-pairs teaching support.** The baseline rejects all three labelled canonical inputs and the unlabelled canonical input. Both 8x8 training cases use gap 3; the 11x11 cases contain three centers. The original rationale for excluding these cases is unknown. Pair, chain, bend, skipped-pair, and network scenes now preserve those core sizes and exercise additional relations. Baseline failures are retained in the return's `checks/before/` and `checks/regressions-before/`.
- **R2 — advertised ignored controls to three exact observable controls.** Removed palette, anchor, direction, and texture claims which did not describe actual construction. Only dimensions and scene are advertised; unknown controls and invalid values fail explicitly. Default difficulty weighting does not narrow the exact override range. Every dimension/scene combination is constructible, so there is no incompatible-combination exception.
- **R3 — random witnesses to a materialized lesson policy.** Three demonstrations and one query use a 12-slot schedule: pair, network, network, chain, network, network, bend, network, network, skipped, network, network. Core slots keep 8x8 pairs or 11x11 multi-plus grids; other slots vary sizes, separations, translations, and all eight square symmetries. At least two network draws in every four raw draws protects a witness under a single query rotation. Duplicate filtering can change accepted indices, so actual lessons and all four query positions were measured rather than inferred solely from this schedule.
- **R4 — intermediate even square to an odd square network.** The first repair (`cb4a7de65d826b883337acf3253f637dd1580116d8d27b807a9ae0a1b673f472`) passed all 12 battery stages but had only two aligned pairs in its network. Independent review showed a solver stopping after the first two aligned pairs could fit that entire generated family. The final odd square has four aligned pairs; its fifth plus lies on one diagonal and has arms on the other. The added capped-pair regression failed on the intermediate source and passes on the final source. See the return's `checks/regressions-intermediate/` and the task-local `counterexamples/review-c0456ed9fa5e1369/network.json`.
- **R5 — duplicate authority synchronization.** Only `racket_target.target_code` in the assigned base solution record was replaced by the canonical `program_solution`. The canonical ledger is byte-identical; historical `raw_code` remains unchanged. Final authority synchronization reports selected synchronization with archival divergence and passing execution parity.

## Final evidence and limits

Final generator SHA-256: `8881324e04e919f61e7c329bc6c9df4afeca1863ce095ad4d7f834b1eddddad2`.
The 32 focused regressions and all 12 battery stages pass. Final profile-floor sampling has 16 exact size/palette hits out of 60 draws, with easy/medium/hard support 3/20, 6/20, and 7/20. The semantic gate with required query rotations passes. The larger census contains 300 materialized lessons (100 per band), 1,200 labelled pairs, 913 unique inputs, and 1,200 query rotations with no ambiguity against seven distinct rivals. Fixed-seed schedule enumeration covers starts 0..11 in each band at seed 0: 36 lessons, 144 query rotations, and 35 unique inputs, also with no ambiguity. Overlapping windows and repeated grids are not independent samples.

The five canonical shortcuts each fit all three usable canonical labels. The two additional lesson competitors (first two centers and positive slope only) are already refuted by canonical examples, so they are not called canonical shortcuts. The declarations are executable and are enumerated directly by `workspace/extract_census_witness.py`; that probe reuses a source-bound Racket-labelled network and verifies exact seed replay.

No claim is made about arbitrary unseen rivals, all random seeds, more than five centers, noisy or incomplete pluses, color-role permutations, or model training improvement. Collinear neighboring-pair and extreme-pair formulations can paint the same union as all-pairs and should not be rejected merely because their iteration differs.

## Retained audit lead and disposition

The unresolved entry `review-7b9f28e84a1d3199:v0001` in `evidence/review_index.json` was used as a lead: its exactly-two-centers rejection was reproduced on the selected baseline. R1 and the canonical-input regressions address that finding. This return proposes explicit resolution against the final source hash; it does not rewrite the retained audit index or infer approval from passing tests. No known in-scope repair blocker remains. Both independently assigned audit targets are findings-only and unchanged.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `8881324e04e919f61e7c329bc6c9df4afeca1863ce095ad4d7f834b1eddddad2`.

# Decisions — review-c0456ed9fa5e1369

## Authority and the original intent

The canonical program at task `e5525362bfb8` is the authority: detect complete green plus centers; connect every diagonal-aligned pair; change only intervening zero cells to red. The three labelled canonical pairs and fourth unlabelled input establish support for gap three, both slopes, and three centers. The original rationale for generating only two centers at larger gaps is unknown. Imported historical statements were treated as leads and checked on the selected source.

The baseline's active base `target_code` had diverged from canonical text. R5 synchronizes only that active field. Changing the canonical program to match the narrower generator was rejected because the supplied canonical examples already demonstrate broader behavior. Historical `raw_code` is preserved as evidence, and the final authority gate reports selected synchronization with archival divergence and passing execution parity.

## R1: construct the relations directly

The generator now uses five explicit geometries. A pair is the easiest case. A chain adds multiple collinear pairs. A bend requires both slopes. A skipped scene has a relevant pair separated in row-major center order by an irrelevant center. A network adds crossing bridges, additional centers, and green arms on a bridge. These choices test relations that a two-plus-only distribution cannot distinguish.

The validator accepts 2..5 complete centers, all green cells covered by plus footprints, and at least one paintable diagonal connection. It intentionally accepts some lawful arrangements the sampler does not emit, including four-center inputs. It rejects ragged grids, illegal or noninteger colors, incomplete/orphan green shapes, and grids without a paintable relation. The broader Racket program may handle additional inputs; this return does not claim their coverage.

Arbitrary green noise and incomplete pluses were rejected as distribution changes for this repair because their teaching value was not established by the canonical examples and would add another domain question. Recoloring was rejected because the Racket rule uses fixed semantic colors. A generic random-placement/rejection sampler was rejected in favor of constructive, bounded placement with exact dimensions and guaranteed meaningful relations.

## R2: exact controls and nuisance variation

Only `grid_h`, `grid_w`, and `scene` are exact public overrides. Height and width accept integers 8..24 in every band. The five scenes fit every Cartesian combination, including 8x8, so no incompatible-combination declaration is needed. Unknown keys, booleans/floats for dimensions, out-of-range sizes, and unknown scenes fail explicitly. `observe_overrides` recovers all three controls from the returned pixels.

Prior advertised palette, texture, anchor, and direction controls were removed because their outputs did not honor the advertised contract. Colors stay fixed; orientation and translation remain sampled nuisance variables without false claims of exact user control. Making all internal draws configurable would enlarge the compatibility surface without helping the identified defect.

All eight square symmetries vary orientation. Distances vary from two to the largest that fits; core draws give extra weight to distance three without excluding other feasible distances. Translation uses the full fitting range with a one-cell arm margin. Difficulty changes the distribution of default canvas sizes, not legal override bounds: easy 8..12, medium 10..18, hard 14..24 outside the core slots. Core slots use an 8x8 pair or 11x11 multi-plus canvas. This preserves canonical-profile support while still varying the generated grids.

## R3: choose a lesson, not only a grid distribution

`EXAMPLES_NEEDED = 3`. The intended census lesson has three accepted demonstrations and one accepted query. The 12-slot schedule is:

`pair, network, network, chain, network, network, bend, network, network, skipped, network, network`.

Thus every four raw draws contain at least two compound networks; holding out one draw cannot remove all such witnesses. This is a statement about raw draws. Actual materialization may skip duplicates or rejected pairs, so the final-source evidence checks assembled lessons and records accepted indices. Independent witness probability alone was rejected as sufficient evidence for a lesson claim.

The ordered production verdict and rotation verdict are reported separately. Rotation holds out each labelled pair once and preserves remaining order. The explicit semantic gate requires rotations. The larger census checks 100 lessons per band, indices 0..99 with the recorded hash-derived seed recipe: 300 materialized lessons and 1,200 rotations, no ambiguity against the declared alternatives, 913 unique inputs. A separate seed-0 enumeration covers all starts 0..11 in all three bands: 36 lessons and 144 rotations, 35 unique inputs. The overlapping fixed-seed windows are not independent random trials, and arbitrary unseen seeds remain unproven.

## R4: revise the first repair after a real counterexample

The first repair used an even-sided square of four corner centers and an off-diagonal fifth plus. Its central arms made green preservation meaningful, and the declared semantic gate passed. Independent review then supplied a new hypothesis: stop after the first two qualifying aligned pairs. That intermediate network had only two such pairs, and the chain's first two pairs already painted its whole diagonal. The new hypothesis therefore fit the distribution despite a green battery.

The revised odd-sided square has side `2*d + 1`, with four corner centers and a fifth at `(d,d)` before symmetry and translation. It creates four aligned pairs. The fifth center lies on one diagonal, and its arms touch the other. This refutes the capped-pair hypothesis and the already declared green-overwrite alternative without expanding the envelope or inventing new symbols. The real regression was written against the intermediate source, failed, and then passed after the revision; evidence is retained under `checks/regressions-intermediate/`.

The final declarations contain seven distinct alternatives: first two centers, first three centers, row-major consecutive centers, first two aligned pairs, gap-three-only, positive-slope-only, and overwriting green arms. Only the five which fit all usable canonical labels are declared `CANONICAL_SHORTCUTS`. The other two remain useful lesson competitors. The task-local witness extractor iterates the actual declarations instead of keeping a second manually copied name list.

Neighboring pairs along a single diagonal and extreme endpoints can produce the same union of painted cells as all pairs. These were rejected as mandatory negative rivals because they can be output-equivalent. Merely writing a different loop does not create a semantic counterexample. The final finite rival set is not proof against every truncated, memorized, or otherwise undeclared program; automatic generation of useful truncation rivals is the top proposed shared-tool improvement in F1.

## Tests, execution, and handoff

The 32 focused tests use the public `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` interfaces so they run in portable layouts. The independent expected-output formulation is checked against all three labelled canonical pairs. Tests check canonical input admission, constructor/override geometry and observation, invalid controls, schedule windows and rotations, actual capped-pair behavior, preserved green arms, and malformed inputs. Root frozen fixtures and shared check code remain untouched.

The first portable task-test invocation failed because pytest was installed only in the disabled user site. A per-review environment made those installed distributions available while preserving the isolated worker policy. That is an environment remedy, not a generator fix; the failed run remains in the return. The final 32-test stage and 12-stage battery are bound to generator `8881324e04e919f61e7c329bc6c9df4afeca1863ce095ad4d7f834b1eddddad2`.

A fresh-copy patch replay is the final handoff gate. The reusable replay tool is intentionally limited to extraction, applying the exact delta, and source receipts; focused tests are an explicit subsequent command. Tool review found receipt overwrite and an old-path boundary bypass, both now fixed with retained red/green evidence. The full helper suite passes 21/21, independent review passes its nine focused cases, and the exact builder patch applies to a fresh original extraction whose 32 regressions also pass. The patched source matches the final battery/censuses/solve hash. No shared runtime changes are proposed in the allowed source delta.

## Scope and open findings

The unresolved prior main-task audit is addressed by R1; resolution must be recorded explicitly against the repaired hash. The two new audit findings A1 and A2-1 are separate, source-bound findings whose target generators were not edited. The blind solve and exposed post-repair solve each have one successful visible-example revision and unknown masked correctness. Their work logs are useful observations, not model-performance measurements.

These choices improve demonstrated input coverage, distinguishability against named shortcuts, and reproducibility of the handoff. No Qwen3.5-9B training experiment was run, no training admission was changed, and no claim of a measured downstream accuracy gain is made.
