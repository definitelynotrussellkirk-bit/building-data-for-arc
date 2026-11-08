# Working notes: 0491e1a49389

## 2026-09-28 review

The canonical Racket rule was retained unchanged. Its guide is the unique full-width row of color 9; every nonzero, non-guide cell is reflected across that row into a fresh canvas, with per-cell clipping at the grid boundary.

The imported generator had three blocking contract defects: no `RULE_HASH`, degenerate textures in the ordinary texture domain, and override declarations that were not globally realizable. It also had almost no canonical-profile support and no executable semantic contract. Most ordinary scenes placed objects only above a central guide, allowing a model to learn a fixed-middle-axis or above-only shortcut.

Version 3.0.0 uses a deterministic three-profile lesson cycle:

1. `canonical_both_sides`: canonical grid dimensions and palette size, with objects on both sides;
2. `off_center_both_sides`: the guide is not the geometric middle row;
3. `clip_both_sides`: at least one object has a partially visible reflection, proving clipping is per cell rather than all-or-nothing.

Ordinary textures are `both_sides`, `off_center`, `clip`, and lawful `touching_guide`. `no_objects` remains only as a negative fixture. Exact overrides are globally valid for heights 8-19, widths 8-18, 2-4 objects, and every ordinary texture. `observe_overrides` makes their realized values auditable, and unknown keys raise `ValueError`.

The module now exposes an independent Python mirror, strict canonical-profile predicate, named rivals, named witnesses, and lesson-identifiability hook. Task-local tests pin the rule hash, canonical pair parity, the three-example curriculum, boundary override products, determinism, RNG isolation, and the fixed-middle counterexample. A Racket-verified replayable shortcut witness is stored in `workspace/shortcut_witness.json`.

Retained limitations are deliberate: scenes use one horizontal color-9 guide, a zero background, distinct object colors, no reflected-object collisions, and 3-5-cell connected motifs. Same-color disconnected components, output collisions/occlusion, alternate guide colors/orientations, and source objects crossing the guide are outside this generator's current curriculum.
## Current reviewer considerations

Source SHA-256: `8e46b096c0424af787d6475a5f40b2501eaa4fae0eb2924253bdc495939162c7`.

# Decisions: 0491e1a49389

## D1 — Keep the canonical Racket rule unchanged

**Original rationale:** The packet did not record a design rationale, but the canonical pairs and synchronized rule authorities agree on guide-row reflection with fresh-canvas output and per-cell clipping.

**Alternatives considered:** Rewrite the rule to use a Python-style component transform; change clipping to drop whole objects; preserve original source cells.

**Probe:** Baseline and after rule smoke, grammar, Racket lint, and authority synchronization; an independent Python mirror was compared on canonical pairs and 120 generated inputs.

**Decision:** Keep rule hash `d6db986b56c9`. The observed faults were distribution and contract faults, not rule faults.

**Failure modes/limitations:** The canonical rule identifies the first full row of 9s and assumes one meaningful guide. Multiple full-width 9 rows remain outside the ordinary generator contract.

## D2 — Pin the rule hash and provide an independent mirror

**Original rationale:** Unknown; the imported generator omitted `RULE_HASH`.

**Alternatives considered:** Add only the hash; rely entirely on Racket smoke without a local mirror.

**Probe:** The missing hash caused the baseline lint failure. The after rule smoke checked 120 mirror comparisons with zero mismatches.

**Decision:** Add `RULE_HASH`, `rule_mirror`, and tests against all canonical pairs.

**Failure modes/limitations:** The mirror is a test oracle and semantic hook, not the rule authority. The Racket program remains authoritative.

## D3 — Use a three-profile deterministic schedule

**Original rationale:** The imported generator sampled textures independently and did not guarantee that a lesson-sized set covered the necessary counterexamples.

**Alternatives considered:** Pure random mixtures; larger `EXAMPLES_NEEDED`; one overloaded example containing every edge case.

**Probe:** Sliding windows over generated examples and the semantic lesson gate.

**Decision:** Cycle `canonical_both_sides`, `off_center_both_sides`, and `clip_both_sides` by `sample_index % 3`. Every three consecutive examples therefore contain all three profiles, regardless of the starting index.

**Failure modes/limitations:** Adjacent lessons can share the same profile order. The schedule optimizes identifiability rather than IID sampling.

## D4 — Include canonical-scale profiles in every cycle

**Original rationale:** Unknown. Baseline dimensions were broader and produced 0/60 exact canonical-profile matches.

**Alternatives considered:** Preserve only broad dimensions; use canonical sizes exclusively; add a probabilistic canonical-size bias.

**Probe:** Canonical profile floor across all difficulty bands.

**Decision:** One scheduled profile uses canonical dimensions `(8,9)`, `(9,10)`, or `(9,11)` and two objects, yielding the canonical palette size of four including 0 and 9. Other profiles retain broader dimensions.

**Failure modes/limitations:** Exact profile support is intentionally about one third, not 100%; broad generalization remains in the other two profiles.

## D5 — Require source objects on both sides of the guide

**Original rationale:** The old notes allowed either side, but ordinary sampling often taught only above-to-below reflection.

**Alternatives considered:** Randomly choose one side; require both sides only in one profile; allow empty sides and rely on large sample counts.

**Probe:** The `below_to_above` witness fired on 600/600 semantic census draws, and the above-only rival was contradicted on every checked witness.

**Decision:** Every ordinary input contains at least one object above and one below.

**Failure modes/limitations:** This is stronger than the minimum canonical condition and reduces one-sided scene coverage. It is justified as curriculum design because one-sided examples do not establish bidirectionality.

## D6 — Deliberately generate off-center guides

**Original rationale:** The imported generator mentioned off-center guides but did not supply an executable guarantee or rival contract. Canonical guides are all middle/upper-middle.

**Alternatives considered:** Always center the guide; rare random offsets; shift the guide but keep objects only above it.

**Probe:** The fixed-middle rival fits all canonical demonstrations. The after semantic census observed 410/600 off-center cases and verified 60/60 rival disagreements. The exact replay witness uses guide row 7 in a 14-row grid, while the rival uses row 6.

**Decision:** One profile per cycle is guaranteed off-center, with two-sided objects.

**Failure modes/limitations:** Offsets are modest to preserve placement feasibility and visual clarity; extreme near-edge guides are exercised through explicit texture/size combinations rather than made the default.

## D7 — Teach partial clipping explicitly

**Original rationale:** Canonical code clips each reflected cell independently, but ordinary imported examples did not guarantee a partially clipped object.

**Alternatives considered:** Avoid all clipping; allow only fully invisible objects; include clipping randomly without a schedule.

**Probe:** The partial-clipping witness fired 188/600 times; all 60 checked witnesses disagreed with the all-or-nothing rival.

**Decision:** One profile per cycle has an object whose reflection is partly in bounds and partly out of bounds, while every object retains at least one visible reflected cell.

**Failure modes/limitations:** Fully invisible reflections are excluded because they add no visible teaching signal. The generator also avoids collisions, so overwrite precedence is not taught.

## D8 — Connected 3-5-cell motifs with distinct colors

**Original rationale:** The imported generator used grown polyominoes, but exact object-count recovery and collision-free reflection were not robustly enforced.

**Alternatives considered:** Single pixels; arbitrary scattered same-color cells; large random walks; repeated object colors.

**Probe:** Boundary-product tests, self-check, and exact `observe_overrides` recovery.

**Decision:** Place normalized connected motifs of 3-5 cells, give each object a distinct color, and reject candidate placements whose visible reflections collide.

**Failure modes/limitations:** Distinct colors make object counting unambiguous but do not teach connected-component separation for repeated colors. Motif size is intentionally small for dense 8×8/four-object overrides.

## D9 — Global exact override ranges

**Original rationale:** The original AXES declared global ranges while implementation used difficulty-specific bounds, so valid declared values failed in other bands.

**Alternatives considered:** Narrow AXES to the intersection of all bands; declare incompatibilities; silently clamp; remove difficulty.

**Probe:** The inherited override checker over all single-axis and combined cases, plus an explicit boundary product over heights/widths, 2/4 objects, and all helpful textures.

**Decision:** Overrides use global bounds in every band. Difficulty influences defaults only. `grid_h=8..19`, `grid_w=8..18`, and `n_objects=2..4` are exact everywhere.

**Failure modes/limitations:** Difficulty separation is softer because hard/easy cannot forbid an explicit value. This is preferable to a false public contract.

## D10 — Reject unknown keys and expose realized overrides

**Original rationale:** Unknown. The imported `**overrides` silently accepted typos, and semantic axes lacked provenance.

**Alternatives considered:** Ignore unknown keys for forward compatibility; return metadata separately from the grid.

**Probe:** Baseline unknown-key check failed. After override battery accepted 30,420/30,420 declared cases and rejected the sentinel unknown key.

**Decision:** Validate keys before generation and implement `observe_overrides(grid)` for all exact axes.

**Failure modes/limitations:** A new axis must be added to both AXES and validation intentionally; this is desired schema discipline.

## D11 — Reclassify textures

**Original rationale:** `touching_guide` was labeled degenerate even though it consistently passed `self_check`; `no_objects` was declared ordinary despite violating the object requirement.

**Alternatives considered:** Make touching illegal; weaken self-check to accept no objects; declare both lawful degenerates.

**Probe:** Baseline defect lint and texture-specific task tests.

**Decision:** `touching_guide` is an ordinary lawful texture. `no_objects` is a negative fixture and is excluded from `AXES['texture'].valid`.

**Failure modes/limitations:** The negative fixture intentionally fails ordinary self-check and should be used only by explicit tests, not dataset generation.

## D12 — Add named rivals, witnesses, and lesson identification

**Original rationale:** The imported generator only described rivals in comments, so the semantic gate reported `NO_CONTRACT`.

**Alternatives considered:** Keep prose only; declare witnesses without rival functions; rely on marginal distribution checks.

**Probe:** Racket-backed semantic gate over 600 draws and 12 materialized lessons.

**Decision:** Make three rivals executable and bind each to a witness. A lesson is identifiable only if all rivals are falsified by its demonstrations when they disagree on the query.

**Failure modes/limitations:** The competitor set is not exhaustive. It targets the three strongest distribution-induced shortcuts found in this review; future audits can add others without changing the canonical rule.
