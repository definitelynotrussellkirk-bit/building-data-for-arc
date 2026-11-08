# Working notes: 270af96a99b0

## Current rule

Extract each nonzero same-color 4-connected component, retain its tight crop, compute true exposed-edge perimeter, sort ascending by `(perimeter, bbox top row, bbox left column)`, then top-align the crops left-to-right with one zero column between them. The selected Racket rule was not changed; `RULE_HASH = cf57cf408f13`.

## Decision reversal

The imported `2.0.1` generator described random motifs gathered into a **vertical** pack. That was inconsistent with the catalog authority, which horizontally packs crops after perimeter sorting. It also exposed fake/dead axes, accepted rule-hiding degenerates, omitted `RULE_HASH`, had no semantic contract, and had zero canonical profile support.

Version `3.0.0` replaces that sampler with a constructive four-component grammar:

- `p8_tie`, `p10_tie`, and `p12_tie` make the source-position tie-break observable at three perimeter levels.
- A concave component distinguishes true perimeter from bbox perimeter.
- Deliberate source/color/area order scrambling refutes plausible sort shortcuts.
- Unequal crop heights, one-column gaps, and internal crop background distinguish alignment and packing mechanics.
- All advertised axes are exact, observable, accepted across every difficulty band, and invalid/unknown overrides fail loudly.
- Every fourth sample is an 8-row canonical-size anchor; successive anchors use widths 9, 10, and 11.

The first repaired layout used four quadrants. The defect detector showed that 42/60 outputs widened the input (`reshape`), while every canonical pair has a `shrink` relation. The final source gallery is nine columns wide, so all outputs are at most the input width and strictly shorter in height. This reversal is covered by `test_generated_transformation_stays_in_canonical_shrink_relation`.

## Teaching evidence

The three canonical examples do not distinguish true perimeter from bbox perimeter (and some also admit area order). The retained witness `counterexamples/canonical-demos-admit-bbox-perimeter.json` contains a lawful query where the bbox-perimeter rival changes the answer. The generated three-profile schedule refutes all eight declared rivals within three demonstrations; `lesson_identifiable` rejects any surviving query-changing rival.

The independent probe in `workspace/reference_probe.py` is supplementary only. Racket remains the label authority. Its 128-sample-per-band audit found no invalid or nondeterministic draws, all three profiles in each band, and disagreement with every declared rival on every sampled input.

## Assumptions and limits

- The grammar intentionally fixes four distinct-color components because all canonical pairs contain four.
- Source scenes are horizontal galleries rather than arbitrary scatter; margins and moat widths vary. This keeps source ordering controlled and the output in the canonical shrink class.
- The `p12_tie` profile uses a five-cell vertical line and compact branched shapes; these are lawful but more synthetic than the tiny canonical objects.
- Passing finite declared-rival checks does not prove unique induction against every possible rule.
- Difficulty changes deterministic layout randomness but does not narrow exact axis support.

## Evidence and leads

No prior return was used as an implementation lead. I consulted the retained passing example `generators/b90d4c3d5553/` for check-contract conventions and `generators/78143e5d7ed1/` for a related crop/sort/pack semantic-contract pattern. Before evidence is under `WORK/checks/before`; the failed quadrant attempts are retained under `WORK/checks/after` and `WORK/checks/after-v2`; the clean full battery is under `WORK/checks/after-v3`.
## Current reviewer considerations

Source SHA-256: `50dd4badf1fd787f83fcc4266d490d575f8299e1dbfca5f0f8240c74b583b389`.

# Decisions: 270af96a99b0

## 1. Preserve the selected Racket authority

**Prior choice/rationale:** the baseline generator implicitly implemented a different vertical-gathering story; its original rationale is unknown. The selected catalog authority already agrees with all canonical pairs.

**Decision:** do not edit the Racket rule. Pin `RULE_HASH = cf57cf408f13` and make the generator, mirrors, tests, and documentation conform to it.

**Alternatives considered:** rewrite the rule to match the old sampler; change the canonical row; add compatibility behavior. All were rejected because they would replace a coherent authority merely to preserve an incorrect generator.

**Probe/evidence:** canonical pairs were checked with both the independent Python oracle and the Racket catalog runner. Final rule smoke, Racket lint, and authority sync are green.

**Failure modes/limits:** an archival raw-code copy remains textually divergent, although selected execution parity passes. The Python mirror is supplementary and never promoted to authority.

## 2. Use exactly four distinctly colored components

**Prior choice/rationale:** the old sampler varied motif count and could collapse motifs under degenerate textures. Its intended training rationale was not recorded.

**Decision:** construct exactly four isolated components in four distinct colors.

**Alternatives considered:** vary component count; reuse colors across disconnected components; allow touching objects. Those alternatives complicate object identity and depart from all three canonical examples, which each contain four objects.

**Probe/evidence:** `self_check` rejects wrong counts, repeated component colors, and Chebyshev touching. Canonical support and focused mutation tests pass.

**Failure modes/limits:** this does not train transfer to five or more objects. The restriction is explicit rather than masquerading as a live axis.

## 3. Teach true perimeter with three tie profiles

**Prior choice/rationale:** the baseline motifs did not expose the authority's sort key, and canonical examples admit bounding-box-perimeter and sometimes area-order shortcuts.

**Decision:** schedule `p8_tie`, `p10_tie`, and `p12_tie`, with sorted true-perimeter signatures `(8,8,10,12)`, `(4,10,10,12)`, and `(6,12,12,14)`.

**Alternatives considered:** one fixed tie; random unconstrained polyominoes; no ties. One tie is easier to overfit, unconstrained search is harder to validate and may miss evidence, and no ties fail to teach the source-position tie-break.

**Probe/evidence:** the independent probe recovers all profiles in every band; focused tests check every profile against every declared rival. The lesson census reports no ambiguity among declared competitors.

**Failure modes/limits:** profile identity is synthetic and the `p12_tie` shapes are more elaborate than canonical objects. Finite profiles cannot cover every perimeter geometry.

## 4. Make source-position tie-breaking observable

**Prior choice/rationale:** the old generator did not reliably separate primary sort key from tie-break behavior.

**Decision:** every profile contains equal-perimeter components placed in a source order that matters, while their areas are deliberately ordered to defeat area-based sorting.

**Alternatives considered:** random placement and post-hoc rejection; deterministic canonical source order. Rejection is less auditable and can become expensive; canonical source order makes sorting a no-op.

**Probe/evidence:** `self_check` requires a perimeter tie and rejects scenes already in canonical order. `SEMANTIC_WITNESSES` verifies that source order and area order change the answer.

**Failure modes/limits:** tie cases are guaranteed rather than naturally distributed. This is intentional curriculum shaping.

## 5. Use a nine-column horizontal source gallery

**Prior choice/rationale:** the first repaired version used four spatial quadrants to create more apparent scatter.

**Decision reversal:** replace quadrants with a controlled gallery whose occupied construction width is nine columns, embedded in `grid_w=9..16` with varied margins.

**Alternatives considered:** keep quadrants; arbitrary rejection-sampled scatter; force wider inputs only. Quadrants caused 42/60 `reshape` outputs, a size relation absent from canonical examples. Arbitrary scatter increases collision/rejection complexity. Forcing only wide grids would lose canonical width support.

**Probe/evidence:** `checks/after-v2/` retains the transformation-drift failure. The final regression checks all bands/profiles and requires output dimensions to be no larger than input dimensions with at least one strict decrease. `checks/after-v3/` passes defect lint.

**Failure modes/limits:** the gallery can be visually easier to segment than arbitrary scatter. The source order is nonetheless scrambled relative to canonical order, and the eight rival checks guard the main shortcut family.

## 6. Exact grid-size axes and canonical anchors

**Prior choice/rationale:** baseline metadata claimed grid controls that the sampler did not honor.

**Decision:** support exact `grid_h=8..14` and `grid_w=9..16`; every fourth default sample is an 8-row anchor, cycling widths 9, 10, and 11.

**Alternatives considered:** remove dimension axes; retain approximate controls; use only canonical dimensions. Removing useful controls reduces composition, approximate controls violate the contract, and canonical-only dimensions reduce diversity.

**Probe/evidence:** exact overrides are tested in every difficulty band. The profile-floor stage and focused tests confirm all three canonical dimension profiles per band.

**Failure modes/limits:** legal height/width combinations are broad, but the internal gallery imposes minimum geometry. Invalid combinations are rejected before generation rather than silently adjusted.

## 7. Three explicit palette kinds

**Prior choice/rationale:** the baseline texture/palette controls included degenerate modes that could merge semantic objects or hide the rule.

**Decision:** expose only `low`, `high`, and `mixed` four-color palettes, all exactly observable from the output grid.

**Alternatives considered:** arbitrary palette size; all-same-color texture; color reuse. These either create fake axes or make distinct component identity ambiguous.

**Probe/evidence:** override tests recover the requested kind from generated colors in every band. The independent audit includes palette variation while color-order always disagrees with the authority.

**Failure modes/limits:** the palette axis controls ranges, not every possible four-color subset uniformly. Output semantics preserve source colors as required.

## 8. Declare eight executable competitors

**Prior choice/rationale:** no semantic contract existed.

**Decision:** implement source order, area order, bbox-perimeter order, color order, descending perimeter, bottom alignment, no-gap packing, and filled-bbox rivals, with corresponding witnesses and a lesson-identifiability hook.

**Alternatives considered:** prose-only notes; a single competitor; learned-model evaluation. Prose is not enforceable, one competitor misses independent mechanics, and model evaluation is costly and nondeterministic.

**Probe/evidence:** all rivals are independently reimplemented in `workspace/reference_probe.py`; every rival differs on every one of 512 audited inputs. The 300-lesson/1200-rotation census reports zero surviving query-changing competitors.

**Failure modes/limits:** the list is not exhaustive. A novel rule outside these hypotheses can still fit finite demonstrations.

## 9. Require three demonstrations

**Prior choice/rationale:** canonical data provide three demonstrations, but those examples alone admit a bbox-perimeter shortcut.

**Decision:** set `EXAMPLES_NEEDED = 3` and design the three scheduled profiles so a production lesson includes evidence for multiple perimeter ties and packing mechanics.

**Alternatives considered:** two demonstrations; four or more; rely on canonical demonstrations. Two provide less profile coverage, four increase token cost, and canonical-only lessons are demonstrably ambiguous.

**Probe/evidence:** `counterexamples/canonical-demos-admit-bbox-perimeter.json` stores the ambiguity. The actual three-demo/one-query assembly passes 300 production lessons and 1200 held-out-role rotations.

**Failure modes/limits:** the shared census samples production starts; it does not enumerate every conceivable cyclic schedule or undeclared rival.

## 10. Strict validation and loud override failure

**Prior choice/rationale:** baseline overrides could be ignored, clipped, or produce invalid scenes.

**Decision:** validate all keys/types/ranges before sampling, reject unknown keys, and make `self_check` enforce the teaching invariants rather than merely grid syntax.

**Alternatives considered:** silently ignore unknown keys; clamp values; generate-and-retry indefinitely. These hide authoring errors and weaken reproducibility.

**Probe/evidence:** focused tests cover invalid keys, booleans-as-integers, floats, ranges, enum values, structural damage, color merging, lost ties, purity, and hash-seed independence. The final override stage has no findings and reports unknown keys rejected.

**Failure modes/limits:** strictness intentionally excludes lawful-but-unteachable grids outside this curriculum. `strict_canonical_like` is a generator-domain validator, not a claim that all possible authority-lawful inputs share this grammar.

## 11. Build and retain an independent probe

**Prior choice/rationale:** the old generator depended on self-description without a separate geometry implementation.

**Decision:** add `workspace/reference_probe.py`, written independently of the generator helpers, for extraction, true perimeter, packing, rival outputs, override observation, and batch audits.

**Alternatives considered:** reuse generator internals; rely only on the battery. Reuse makes correlated bugs more likely; the battery does not expose all distribution statistics in one reusable task-local tool.

**Probe/evidence:** its 512-sample audit found no invalid/nondeterministic draws and full rival disagreement. Selected canonical and generated cases are still checked with Racket, preventing the probe from becoming a second authority.

**Failure modes/limits:** independent Python can still share conceptual mistakes. The discarded `1120fd69b838` audit mirror is retained as an example of why Racket verification remains mandatory.

## Native parametric tie-break family — review-20ab221416598671

**Decision.** Keep the exact canonical `source_position` program as the default and add one episode-fixed `smaller_area` setting. Both settings sort by true exposed-edge perimeter first. The alternative resolves equal-perimeter objects by occupied area before source position, then uses the same crop-and-pack stage.

**Why this variant.** It preserves the task's demanding geometry rather than replacing perimeter reasoning with a scalar shortcut. It also creates a genuine sequential dependency: object extraction and perimeter/area measurement produce an input-dependent ordered component sequence; the later packing stage cannot choose output slots before that sequence is known.

**Teaching repair.** The first draft allowed a `global_area` rival to fit both demonstrations for seed 4 under `smaller_area` and disagree on every query. The sampler now rotates a constructive profile bank so every two-demonstration prefix includes evidence separating global-area order from perimeter-first/area-tie order. The retained finite audit tests eleven plausible rules over 768 episodes and reports no query-changing survivor in that scope.

**Coverage.** The native family supports 2–6 demonstrations and stable 1–4 query prefixes, always stores four distinct queries, and includes a substantive 30×30 boundary-spanning query. Matched inputs are used across settings. Public projections contain only demonstrations and one masked query at a time; settings, programs, later queries, and answers remain private.

**Native evidence.** Protected-Racket qualifications cover both settings at demonstration counts 2, 3, and 6 (32, 40, and 64 evaluations). The source-bound causal witness uses the 30×30 alternative query: the measured order `[3,9,6,7]` produces the qualified output, while substituting the canonical source-position order `[9,3,7,6]` changes the final packed result. Witness construction and independent replay both pass.

**Limit.** This is reviewer-ready, not owner-accepted. The finite rival set does not prove universal uniqueness. Owner integration must replay native qualification and acceptance on the exact integrated bytes before any training admission.
