# Working notes: 2c1567aea733


## 2026-10-23 parametric prototype

The approved production generator and canonical authority remain unchanged. The
production generator SHA-256 is
`76f477202fa8cad504e70e865bb6154e1f7ef0a7aad5d2f41e7b5eb65dc0d4a9`.

A task-local prototype under `workspace/parametric/` adds exactly one episode
parameter, `anchor_color in {1,2,4}`. The canonical default is `1`, and its
Racket program is byte-for-byte the selected canonical program. Alternate
settings change only the color used to obtain the target top row; the invariant
reasoning is still “group by color, read one anchor top, vertically translate
each whole color without changing columns or shape.” The setting is chosen once
per episode as `ALLOWED_ANCHORS[episode_seed % 3]`.

Retained sampling uses copied-shape inputs with pairwise-disjoint horizontal
extents and three distinct initial top rows. This makes every setting total,
keeps clipping/collision semantics out of scope, and guarantees that the two
alternate anchor programs disagree on the demonstrations. Demonstration and
query counts are independent (`1..8` each, total at most 12); the retained
batch uses three demonstrations and four distinct queries.

Evidence is in `checks/parametric/2c1567aea733-anchor-color-v1/` and
`checks/parametric/2c1567aea733-anchor-color-adversarial-v1.json`. Three retained
episodes cover all settings and contain 9 demonstrations, 12 queries, 63
Racket episode labels, all 4 canonical labels under the default program, 0
Python/Racket disagreements, and 0 ambiguous queries against the two alternate
settings. A 64-seed adversarial pass checked 768 sampled inputs, 2,304 anchor
applications, 1,024 query-rival comparisons, count boundaries, retry uniqueness,
and public-ID privacy with no finding. The prototype source SHA-256 is
`0b4ac5d1f2e157a3a143a52198175acc99527381ea34a4e7f03124c2bab95eef`.

Focused parametric tests are 11/11 green and the existing production tests are
51/51 green. This is proposal evidence only: it does not modify production,
change approval, or claim uniqueness against hypotheses beyond the two declared
alternate anchor settings.

## Intended rule

Find the top row of color 1. For each nonzero color independently, translate all
of that color's cells vertically so its top row equals blue's original top row.
Columns, per-color shape, component structure, and cell count are preserved.

## 2026-10-13 repair decisions

The imported `1.3.0` generator sampled only solid copied rectangles, advertised
dead texture controls, accepted malformed/unknown overrides, missed canonical
size profiles, had no executable semantic contract, and did not pin the
canonical rule hash. It also kept a selected Racket `target_code` text separate
from the canonical active authority.

Version `2.1.0` makes the following choices:

- Pin `RULE_HASH = 837d7987242d` and reject non-literal seed/index/axis values and
  unknown axes.
- Fix the canonical palette `{0,1,2,4}` and retain pairwise-disjoint horizontal
  extents. This matches the task domain without teaching collisions or
  overwrite behavior that the rule does not define.
- Advertise only observable controls: `grid_h` 5–12, `grid_w` 10–15, and
  `scene_profile` in `copied_rectangles`, `copied_irregular`, `mixed_shapes`.
- Weight heights 5/10 and width 10 so every band has canonical profile support,
  while every advertised exact override remains constructive.
- Reproduce the canonical query's disconnected detached-tail morphology in the
  irregular profile. Mixed scenes combine a vertical bar, L, and detached tail
  to prevent rectangle-only, equal-height, bottom-alignment, and
  connected-component shortcuts.
- Schedule blue's vertical rank by `sample_index mod 4` as
  top/middle/bottom/top. Every four-pair lesson contains all three ranks, and
  every held-out-query rotation leaves at least one top-ranked blue example and
  at least two ranks among the demonstrations.

The strongest retained canonical shortcut is `canonical_size_rank`: ignore
color 1; on grids with at least 10 rows align to the lowest-starting color, and
on smaller grids align to the median-starting color. It fits all three canonical
training demonstrations but disagrees with the canonical query. The generator
now emits direct counterexamples; see
`counterexamples/canonical_size_rank.json`. Declared semantic competitors also
include identity and fixed highest/median/lowest alignment.

## Authority

The selected `racket_target.target_code` was copied exactly from canonical
`program_solution` after the retained before report showed that canonical,
legacy selected, and archival raw sources all solved all four canonical pairs.
Only `target_code` changed. Archival `raw_code` remains byte-for-byte preserved.
This is an active-source synchronization, not an intended rule change.

## Measured final evidence

Final generator SHA-256:
`76f477202fa8cad504e70e865bb6154e1f7ef0a7aad5d2f41e7b5eb65dc0d4a9`.
The strict after battery is 12/12 green. Profile floor: 48/60 exact and 52/60
envelope hits, with support in all bands. Override contract: 9,720/9,720 calls
accepted with zero findings/warnings and unknown keys rejected. Semantic gate:
600/600 strict inputs, 12/12 smoke lessons identifiable, 0/48 ambiguous query
rotations. The larger census materialized 300 lessons / 1,200 pairs (1,140
unique inputs) and found 0 production or rotation ambiguities across 1,200
rotations.

## Known limits

The generator deliberately covers exactly three foreground colors, disjoint
column extents, and pure vertical translations. It does not claim support for
colliding color extents, clipping, missing blue, extra colors, or per-component
rather than per-color motion. The finite declared-rival census is strong evidence
for these competitors, not a proof of unique induction against every imaginable
program.
## Current reviewer considerations

Source SHA-256: `76f477202fa8cad504e70e865bb6154e1f7ef0a7aad5d2f41e7b5eb65dc0d4a9`.

# Decisions: 2c1567aea733

## D1: Treat color 1 as the semantic anchor, not vertical rank

**Prior choice.** The imported generator drew copied rectangles without an executable semantic contract. Its original rationale is unknown.

**Decision.** The rule mirror groups all cells by color and aligns every color's top to color 1's original top. Shape, columns, disconnected components, and cell count are preserved.

**Alternatives rejected.** Aligning to the highest, lowest, or median starting object; identity; and the canonical size-conditioned rank rule. These are executable `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`.

**Probe/failure mode.** `counterexamples/canonical_size_rank.json` has blue at row 2, color 2 at row 3, and color 4 at row 7 in a 10-row grid. The intended output aligns to row 2; the strongest canonical shortcut aligns to row 7.

## D2: Keep the canonical palette and horizontal separation

**Prior choice.** The baseline sampled generic blob colors and dimensions. Its rationale for departing from the canonical palette is unknown.

**Decision.** Inputs use exactly `{0,1,2,4}` and pairwise-disjoint color column extents.

**Why.** The canonical task establishes blue as the anchor and never specifies collision priority. Horizontal separation makes vertical translation total and preserves every cell without inventing overwrite semantics.

**Alternative rejected.** Overlapping color extents. That would require a new collision rule not licensed by the selected Racket authority.

**Limit.** The generator deliberately does not train missing-blue, extra-color, clipping, or collision behavior.

## D3: Support canonical dimensions without collapsing to them

**Prior choice.** Baseline bands produced 0/60 exact and 0/60 canonical-envelope hits.

**Decision.** Advertise `grid_h` 5–12 and `grid_w` 10–15 in every band; weight canonical heights 5/10 and width 10 while keeping every exact advertised value constructive.

**Alternative rejected.** Hard-coding only 5×10 and 10×10. That would pass profile checks but make dimensions a stronger lookup cue and reduce distribution breadth.

**Probe.** Final profile floor is 48/60 exact and 52/60 envelope, with exact hits easy=16, medium=14, hard=18.

## D4: Replace dead texture knobs with three observable shape profiles

**Prior choice.** Baseline advertised `scattered`, `row_aligned`, `col_aligned`, and `diagonal`, but defect lint found all four byte-identical to untextured draws.

**Decision.** Expose only `copied_rectangles`, `copied_irregular`, and `mixed_shapes`.

- `copied_rectangles`: vertical bar, 2×2 block, or 2×3 block copied across colors.
- `copied_irregular`: exact canonical detached-tail morphology, optionally reflected.
- `mixed_shapes`: vertical bar, L, and detached-tail assigned across colors.

**Why.** The profiles are observable, exact, canonical-relevant, and distinguish per-color translation from rectangle-only or per-component shortcuts.

**Probe.** `observe_overrides()` recovers each declared profile; the override matrix accepted all 9,720 calls with no findings.

## D5: Rotate blue's starting rank across a four-pair lesson

**Rejected intermediate choice.** The first repair design kept blue between the other two objects, which made the anchor correlate with median vertical rank.

**Final decision.** Use `(top, middle, bottom, top)` for `sample_index mod 4`, with three demonstrations plus one query.

**Why this schedule.** Every complete lesson contains all three ranks. Duplicating top means every possible query holdout leaves at least one blue-topmost demonstration, which refutes the 10+-row-lowest/smaller-median shortcut while preserving at least two observed ranks.

**Probe.** Focused tests exhaust all four starts; the semantic smoke check found 0/48 ambiguous rotations; the larger census found 0/1,200.

**Alternative rejected.** Random rank with rejection. A deterministic four-cycle is easier to inspect, test, and replay and avoids rare ambiguous windows.

## D6: Make the public call and override contract strict

**Prior choice.** Bool/float/string scalars and unknown keys were often accepted; advertised axis ranges disagreed with band-specific generation.

**Decision.** Require literal integer seed and nonnegative integer sample index, restrict difficulty to `None/easy/medium/hard`, reject unknown keys, validate exact axis types, and advertise only three axes whose full domains work in every band.

**Why.** A control should either be exact and observable or not exist. Silent coercion and band-dependent rejection make authoring probes untrustworthy.

**Probe.** The final override report records 9,720 accepted calls, zero explicit rejections/findings/warnings, and rejection of `__override_contract_unknown_axis__`.

## D7: Use finite executable teaching checks, with explicit limits

**Decision.** Declare four witnesses (`visible_motion`, `blue_between_extremes`, `blue_not_median`, `blue_topmost`) and five rivals (`identity`, highest, lowest, median, canonical-size-rank). `lesson_identifiable` validates labels and rejects any rival that survives demonstrations but changes the query.

**Why.** Correct individual labels do not prove a three-demo lesson identifies the rule.

**Probe.** Final semantic gate: 600/600 strict inputs and 12/12 lessons identifiable. Larger census: 300 lessons, 1,200 pairs, 1,140 unique inputs, and no production or query-rotation ambiguity.

**Limit.** These checks cover named and shared generic rivals, not all computable hypotheses.

## D8: Synchronize only the selected active Racket text

**Prior state.** Canonical `program_solution`, selected `target_code`, and archival `raw_code` used different primitive spellings. Before-rule execution parity showed all solved all four canonical pairs, but authority sync correctly failed exact active-text divergence.

**Decision.** Copy canonical `program_solution` exactly into selected `racket_target.target_code`; preserve `raw_code` byte-for-byte.

**Why.** This removes duplicate active source without rewriting history or changing intended semantics. The automated proposal refused because the difference was more than formatting, so I retained a manual primitive-level review in `checks/authority-sync/manual-review.json`.

**Probe.** Final status is `SELECTED_SYNC_ARCHIVAL_DIVERGENT`, with selected exact synchronization and execution parity `PASS`.

## D9: Preserve failed/interrupted evidence and source binding

The before battery and the interrupted first final-battery attempt remain under `checks/before/` and `checks/after-final/attempts/0001/`. Final claims use generator SHA `76f477202fa8cad504e70e865bb6154e1f7ef0a7aad5d2f41e7b5eb65dc0d4a9`; the fresh solve and every final report are bound to those bytes.

## 2026-10-25 native parametric completion

Promoted the retained `anchor_color` idea through the native adapter contract.
The default `anchor_color=1` is the exact selected canonical Racket source;
settings 2 and 4 change only the anchor lookup. The native sampler now provides
separate deterministic pools for 2–6 demonstrations and 1–4 queries, with
matched inputs across settings, prefix stability, and a boundary-spanning 30×30
fourth query. The first two demonstrations rotate every anchor color through a
different vertical rank, closing the fixed-rank teaching hole.

Sequential dependency: stage A obtains the selected anchor's top row; that row
is the intermediate consumed by stage B to translate every color. The retained
counterfactual increments the true anchor top by one before stage B, changing the
final Racket output on a qualified query. Production `generator.py` and the
canonical authority remain unchanged.
