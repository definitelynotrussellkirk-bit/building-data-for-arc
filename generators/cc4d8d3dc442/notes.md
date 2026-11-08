# Working notes: cc4d8d3dc442

## 2026-09-28 review

Canonical inspection showed that all five official inputs are 11×11 grids with a 2×2 full-wall lattice plus one local straight separator, producing five flood-fill regions. Canonical region key counts are limited to 0/1/2; the official test has only 0/2 and therefore disproves the old self-check requirement for an odd region.

The selected Racket rule repaints every non-wall cell, including color-2 keys. No authority change was needed; normalized rule hash is `cdefe31a4be3`.

The generator was replaced with a strict, observable grammar:

- equal base-cell dimensions 3–6;
- 2–3 lattice rows and columns;
- 1–3 local straight separators;
- profiles `mixed`, `zero_even`, `zero_odd`, and `high_parity`;
- exact `observe_overrides` recovery and loud unknown-key rejection;
- canonical-scale prior for the 11×11/2×2/one-split profile;
- semantic rival `one_vs_many` plus `three_key_region` witness.

A greedy separator implementation failed for some `ch_h=3, split_count=3` combinations because earlier choices could create a later full divider. Bounded backtracking fixed the root cause. The exhaustive 2,304-combination census and 15,300-draw override gate are clean.

Final evidence: 9 regression tests pass and all 12 battery stages are green on generator SHA-256 `6f3208ca9f69aa2bd620870b5c288d1f4b6a9914cbf34bf30c2fab72133fd4e4`.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `6f3208ca9f69aa2bd620870b5c288d1f4b6a9914cbf34bf30c2fab72133fd4e4`.

# Design decisions: `cc4d8d3dc442`

## 1. Treat flood-fill regions—not nominal rectangles—as the semantic unit

**Original rationale:** Unknown. The baseline prose fixed a 2×2 rectangular chamber layout, and the implementation generalized that to full 2×2, 2×3, or 3×3 lattices, but it did not model the partial internal wall visible in every canonical input.

**Decision:** Generate a regular outer lattice, then add local straight separators inside selected base cells. Count keys over the resulting four-connected non-wall regions.

**Alternatives considered:** Keep only rectangles; generate arbitrary wall mazes; copy the five canonical masks exactly.

**Probe:** Flood-fill analysis of all five canonical inputs found five regions in each: four base cells plus one local split. The baseline always had exactly the base-lattice region count.

**Failure modes and limits:** A local separator must actually create two open sides. Offsets adjacent to an existing wall only thicken the wall, and multiple separators can accidentally form a complete global row/column. The implementation excludes boundary-adjacent offsets and uses bounded backtracking. It still does not generate arbitrary bends, holes, or maze-like walls.

## 2. Use base-cell dimensions `ch_h` and `ch_w` in the full 3–6 range

**Original rationale:** The baseline declared 3–6 but used narrower band-specific ranges, causing legal overrides to fail in some bands.

**Decision:** Keep 3–6 as the real domain and use difficulty-aware defaults only through `draw_int_diff`; explicit overrides remain valid in every band.

**Alternatives considered:** Narrow the declared domain to each band; remove dimension axes; allow 1–8.

**Probe:** The final Cartesian census exercised every dimension with every other axis across easy, medium, and hard: 2,304/2,304 valid and exactly observable.

**Failure modes and limits:** Three-cell interiors leave few legal separator offsets and exposed the greedy-placement bug. The regression `test_small_cells_with_three_splits_are_total_not_greedy_rejections` protects that boundary. Dimensions above six were not needed for canonical coverage and would inflate grids without adding a new rule distinction.

## 3. Vary lattice shape with `n_rows` and `n_cols` in 2–3

**Original rationale:** The baseline implementation already sometimes emitted 2×3 and 3×3 layouts, but these were undeclared or inconsistently drawn despite prose claiming a fixed 2×2 layout.

**Decision:** Make both dimensions explicit, real, and observable.

**Alternatives considered:** Canonical-only 2×2; a single `layout` enum; 1–4 cells per direction.

**Probe:** Full override and stress censuses confirm all four shapes generate valid grids, and `observe_overrides` recovers them exactly.

**Failure modes and limits:** More than 3×3 can approach ARC size limits when combined with large cell dimensions and adds repetition rather than semantic novelty. A 1×N layout would depart from every canonical example and reduce structural evidence for region decomposition.

## 4. Make `split_count` a real 1–3 axis

**Original rationale:** No equivalent baseline axis existed; the baseline never emitted a local split.

**Decision:** Require at least one local separator, because it is the task-defining canonical feature, and allow up to three in distinct base cells.

**Alternatives considered:** Permit zero; force exactly one; allow every cell to split.

**Probe:** Every default test draw has more flood-fill regions than base lattice cells. The final override matrix accepted every declared split count. Canonical-profile coverage retained the exact one-split form.

**Failure modes and limits:** Zero would reintroduce the rectangular shortcut. Very high counts can make layout selection brittle and overemphasize wall combinatorics. At most one separator per base cell is generated and validated.

## 5. Replace fake palette/texture axes with four key-count profiles

**Original rationale:** The baseline declared palette, palette-size, color-count, density, position-bias, and texture choices, but most did not affect generation. Negative fixtures were mixed into the lawful texture domain.

**Decision:** Remove non-semantic axes and expose one semantic axis, `count_profile`, with four exact profile families:

- `mixed`: 0/1/2
- `zero_even`: 0/2/4
- `zero_odd`: 0/1/3
- `high_parity`: 0/3/4

Every draw includes a zero-key region and a positive-key region, but no longer requires both parity classes.

**Alternatives considered:** Independent per-region 0–4 sampling; one canonical-only 0/1/2 profile; retain diagnostic degenerate textures.

**Probe:** The canonical test input proved that requiring an odd region was wrong. Semantic-gate sampling found the three-key witness in 305/600 draws, and the stress census found all four profiles in every band.

**Failure modes and limits:** Profiles are intentionally discrete and reveal only counts up to four. They do not independently control every region's exact count. That keeps overrides falsifiable and avoids a high-dimensional list-valued axis.

## 6. Keep a strong 11×11 canonical prior without making it the whole distribution

**Original rationale:** The baseline only occasionally matched the canonical linked profile and passed just 6/60 profile-floor draws.

**Decision:** On fully unoverridden draws, use a 45% prior for `ch_h=4`, `ch_w=4`, `n_rows=2`, `n_cols=2`, and `split_count=1`, which is exactly the canonical 11×11 geometry. Key profiles and separator positions still vary.

**Alternatives considered:** Always canonical scale; no prior; separate priors per difficulty.

**Probe:** Canonical-profile floor rose to 28/60 while broader layouts remained common. In the 1,500-draw stress census, exact 11×11 instances appeared in every band along with larger/smaller legal scales.

**Failure modes and limits:** A strong prior can reduce geometric breadth. The remaining 55% plus explicit overrides cover all declared layouts, and diversity stayed high (100% unique inputs, 89% unique outputs in the final battery).

## 7. Repaint every non-wall cell, including keys

**Original rationale:** The baseline summary said “walls and keys stay,” but this contradicted the selected Racket authority and canonical outputs.

**Decision:** `rule_mirror` and documentation implement the actual rule: the entire non-wall region becomes 0, 8, or 7 based on count.

**Alternatives considered:** Preserve keys; paint only original zeros; change the Racket authority.

**Probe:** The Python mirror matched all five official outputs and 120/120 generated Racket smoke outputs.

**Failure modes and limits:** Preserving keys is an especially plausible documentation-induced shortcut, so tests compare exact full grids rather than only background cells.

## 8. Validate the complete morphology in `self_check`

**Original rationale:** The baseline self-check accepted minimal impostors and encoded the false odd-plus-even requirement.

**Decision:** Validate palette, dimensions, complete outer/full divider structure, equal base-cell sizes, exact local separators, connected walls, expected region count, 0–4 keys per region, and zero-plus-positive coverage.

**Alternatives considered:** Minimal palette/size checks; compare against generator metadata; validate only with the reference rule.

**Probe:** All five canonical inputs pass. Sixty destructive mutations and explicit blank/no-split/bad-color tests fail. The strict semantic gate accepted 600/600 generated inputs.

**Failure modes and limits:** The validator defines the intended generated/canonical subgrammar, not every conceivable input on which the Racket program can execute. It therefore deliberately rejects arbitrary wall mazes.

## 9. Declare and teach the strongest canonical-compatible rival

**Original rationale:** The baseline had no semantic contract, so a generator could pass syntactic checks while never distinguishing parity from a simpler threshold rule.

**Decision:** Declare `one_vs_many`: zero→0, exactly one→8, two-or-more→7. Add a `three_key_region` witness and generation profiles containing 3 and 4.

**Alternatives considered:** Only document the rival; use a four-key witness; use “any positive count” as the rival.

**Probe:** The rival fits every canonical region count (only 0/1/2) but disagrees on the deterministic 3-key witness. The semantic gate independently verified 60/60 sampled witness disagreements against canonical Racket execution.

**Failure modes and limits:** Other rivals remain possible, but this is the strongest simple rule induced by the observed count support. The explicit profile also distinguishes odd/even at counts beyond the demonstrations.

## 10. Leave the selected Racket rule unchanged

**Original rationale:** The selected canonical program already implements the intended flood-fill/count/parity behavior and passed execution parity.

**Decision:** Change only the generator, tests, notes, and workspace tool.

**Alternatives considered:** Refactor the Racket style warnings; modify the archival base solution; rewrite the rule for speed.

**Probe:** Authority sync and Racket smoke both pass; the final rule hash remains `cdefe31a4be3`.

**Failure modes and limits:** The Racket linter still reports non-blocking style findings (`dummy-let-binding`, `generated-helper-name`, `style-eq-zero`) in the immutable selected program. Altering authority text would create unnecessary review and provenance risk without changing behavior.
