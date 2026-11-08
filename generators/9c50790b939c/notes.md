# Working notes: 9c50790b939c

## Canonical read

All four canonical inputs are 16×16 color-7 fields containing 10–15 maximal vertical 8/9 runs. Every example includes the complete 2/4/6/8/10 length ladder. The single mixed rail is the source; the unique all-8 rail two cells longer is the target.

The demonstrations leave one important ambiguity: in every canonical pair, the source 9-block occupies half of the source, so the intended output size (`input_nines + 1`) also equals half the target length. A solver can therefore fit all demonstrations by painting half the target. Version 3.1.0 makes non-half block lengths common and declares this rival/witness explicitly.

## Review changes

- Added `RULE_HASH`, strict-manifold metadata, a Python mirror, semantic rival hooks, and an observable override contract.
- Replaced inert/dead metadata and malformed “degenerate textures” with five truthful axes.
- Replaced isolated singleton noise with 10–15 vertical rails containing the canonical 2/4/6/8/10 ladder.
- Added strict source/target uniqueness, end alignment, palette, dimension, rail-count, and ladder checks.
- Synchronized the selected Racket `target_code` with the canonical authority; retained archival `raw_code` unchanged.
- Added six task-local regression tests, including canonical ownership and a concrete half-target counterexample.

The final 12-stage battery is all green. Iteration evidence is retained under `checks/iterations/`; the first rail-field repair still under-covered canonical object counts, and the next packing implementation was replaced with the current bounded O(height×width) scaffold before final verification.
## Current reviewer considerations

Source SHA-256: `08b52963e0ef45f418fa275bb846122d0e9340a791c1431ca6daa69b40edf9d1`.

# Review decisions — 9c50790b939c

## D13 / R1 — validate call scalars before deterministic sampling

**Observed failure.** The pinned source accepted 33 invalid calls across the three difficulty bands. Python booleans, floats, strings, and negative sample indices could reach scheduling/RNG code.

**Alternatives.** Rely on downstream RNG conversion; coerce integral-looking values; or enforce a literal API contract.

**Decision.** Enforce `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0`. Coercion was rejected because values such as `True` and `1.0` would silently alias valid deterministic episodes and weaken reproducibility.

**Probe and evidence.** Eleven focused parameter cases failed before implementation and pass afterward. Baseline and final defect-lint evidence are under `checks/before/` and `checks/after-green/`.

**Limit.** This validates public generation calls, not every private helper parameter.

## D14 / R2 — coordinate witness placement across the whole lesson

**Observed failure.** The prior 80% independent non-half policy had adequate per-grid witness frequency yet produced 10/300 ambiguous ordered lessons and 49/1,200 ambiguous held-out-query rotations. The only rival-breaking grid could be selected as the query.

**Alternatives.** Increase non-half probability; always generate non-half blocks; downstream resample lessons after scoring; add more demonstrations; or coordinate a small deterministic schedule.

**Decision.** Alternate `shortcut_counterexample` and `canonical_half` with period two. Four-pair lessons retain canonical-looking cases, contain exactly two counterexamples, and keep at least one counterexample among any three demonstrations after arbitrary query holdout.

**Why not the alternatives.** A probability below one cannot guarantee lesson identifiability; always-non-half would erase canonical support; resampling duplicates semantic logic downstream; and longer lessons raise training cost unnecessarily.

**Evidence.** Retained counterexample `generators/9c50790b939c/counterexamples/half_target_query_rotation.json`; failed census `checks/lesson-census.summary.json`; final census `checks/lesson-census-final.summary.json`.

**Limit.** The guarantee is against declared rivals and the declared period. It does not prove uniqueness against undeclared hypotheses.

## D15 / R3 — exact two-cell overrides take precedence over profile intent

**Observed failure.** The first schedule implementation requested a non-half proper block for `source_length=2`, which is impossible.

**Alternatives.** Declare source length two incompatible with counterexample slots; reject the override; change source length silently; or preserve the exact override and allow the sole lawful half block.

**Decision.** Preserve the override. Default counterexample sampling excludes length two, while explicit length-two calls use the one-cell block in every band and schedule residue.

**Reason.** Public exact controls are stronger contracts than an internal curriculum profile. The complete lesson, rather than every individual grid, bears the rival-refutation obligation.

## D16 / R4 — parametrize output growth only

**Parameter.** `growth_delta ∈ {0,1,2}`, chosen once per episode, with target block length `source_block_length + growth_delta`.

**Alternatives.** Vary target offset, transfer end, source/target identity, or colors. These were rejected because they alter the core reasoning structure or collide with the fixed-color executable authority.

**Decision.** Keep target selection, matching-end transfer, geometry, and palette unchanged; vary only the output growth constant. Canonical default delta 1 remains byte-for-byte identical to the selected rule.

**Evidence.** Exact-Racket hashes `8ce88af79577`, `846ddca6645d`, and `2d8ecbdcca01`; 4/4 canonical replay at default; a common lawful distinguishing input; and three episodes with all alternative settings refuted by demonstrations (`checks/parametric-final/growth-delta-evidence.json`).

**Approval boundary.** Status is `proposed_unapproved`. The prototype is not imported by canonical generation and does not imply source, variant, or training approval.

## D17 — keep frozen and new tests separate

The packet names `tests/test_generator_9c50790b939c.py` as a frozen fixture. It was restored byte-for-byte to SHA-256 `d3817489ef0bc7d0500e045ee235bee26a2938f9b98c9ecd4207bcf1b3debd1c`. New scalar, schedule, edge-case, and parametric regressions live in separate modules and use portable root discovery.

## D18 — evidence retention

The baseline scalar failure, the v3.1.1 lesson ambiguity, and the intermediate schedule edge case are retained. Final claims point only to source-bound final evidence. Large census reports may be gzip-compressed for the return budget; their summary files retain original size/SHA mappings and are sufficient for routine intake.

## D19 / R5 — derive public identity only from visible bytes

**Observed failure.** The retained writer named files `episode-a.json`,
`episode-b.json`, and `episode-c.json` by iterating hidden `growth_delta` values
`0`, `1`, and `2` in order. The public bytes omitted the parameter, but the
ordinal filename preserved a direct hidden-setting channel.

**Decision.** Project private episodes through
`reviewer_support.public_challenge_bytes`, name each file by
`public_challenge_id`, sort by that ID, and reject duplicate visible payloads.
The private evidence report alone maps public IDs to seeds and parameters.
Superseded ordinal JSON files are removed only after all replacement files are
written.

**Evidence.** Focused regressions mutate private seed/parameter/Racket/query-label
fields without changing the public ID, mutate a visible query input and require a
new ID, reject duplicate visible payloads, verify exact public bytes, and exercise
relative-root relocation.

## D20 / R6 — retain four distinct queries per parameter setting

**Observed limitation.** The prototype had three demonstrations but only one
query, below the packet's requested four-query supervision when the domain
supports it.

**Decision.** Keep demonstration indices `0,1,2` and use query indices
`3,4,5,6`. Evidence exposes counts and indices separately and fails unless every
episode has four query inputs distinct from one another and from every demonstration. The chosen parameter remains fixed
for all seven pairs, and all alternative growth settings remain refuted by the
three demonstrations.

## D21 / R7 — bind reproducibility evidence to the explicit root

`build_evidence(root=...)` now resolves the prototype, generator, rule files and
canonical ledger beneath that root rather than import-time paths. A copied-tree
regression hashes every reported source from the relocated root, preventing a
passing report that silently borrows predecessor files.
