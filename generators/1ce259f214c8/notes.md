# Working notes: 1ce259f214c8

## 2026-10-02 first repair

The five canonical pairs all have empty output borders. Therefore the rival rule “compute the panel-occupancy XOR, then force the complete output border to zero” fits every canonical pair. Under the original independent 45% canonical prior, it survived both demonstrations in 51/300 easy, 74/300 medium, and 64/300 hard sampled two-demo lessons; it then disagreed with the query in 23, 31, and 35 of those lessons respectively.

Version 2.1.0 replaced independent sampling with a seed-rotated 20-slot schedule containing nine canonical and eleven generalized slots, with no adjacent canonical slots. Generalized samples exposed at least one output-border XOR cell. That removed the whole-border-zero rival from two-demo lessons.

## 2026-10-02 second repair

A broader independent search then tested 70 rules that use ordinary XOR everywhere except one canonical-empty region—the full border, one edge, all corners, or one fixed corner—where they substitute zero, OR, AND, a panel copy, or a directional difference. All 70 fit all five canonical pairs. Version 2.1.0 still allowed 68/70 such rivals to produce dangerous two-demo lessons in every band. Merely increasing the old curriculum to five demonstrations did not solve the defect: 66 easy, 66 medium, and 67 hard competitors still survived all five demonstrations and disagreed with a query; the worst competitor failed 83/1000 lessons per band.

The root cause is a finite-observation lower bound. At one fixed corner, left-only, right-only, and overlap are all required to distinguish XOR from the seven simpler Boolean alternatives. Two demonstrations can show at most two of those states. Random generalized examples do not guarantee all three even with five demonstrations.

Version 2.2.0 therefore uses a linked 18-slot schedule with six exact canonical scenes and twelve generalized scenes. The generalized subsequence cycles through three declared corner-relation phases. Every circular five-slot window contains all three phases, and each corner takes each of the three nonempty relation states across those phases. Generalized objects are constructed as connected required-cell masks rather than accepted by chance. `EXAMPLES_NEEDED` is now five.

The independent regional probe measured zero survivals and zero dangerous query disagreements for all 70 competitors across 1000 five-demo lessons in each band. The official battery is 12/12 green; the semantic gate materialized 12/12 identifiable five-demo lessons, the rule mirror matched Racket 120/120 times, the override contract passed 29,070 draws, and the diversity probe measured 100% unique inputs and 95% unique outputs.

The override contract continues to exclude divider color 5 from both object-color axes and explicitly declares same-color pairs incompatible. The Racket authority and `RULE_HASH` remain unchanged.

Reusable measurements:

- `workspace/shortcut_probe.py` — whole-border-zero shortcut.
- `workspace/regional_shortcut_probe.py` — 70 edge/corner-local Boolean competitors and lesson-level danger.
## Current reviewer considerations

Source SHA-256: `1d9f2983a64fec28f0a013c8a3302395764cd785de3c5a8b61b2bd43a35f01a3`.

# Decisions for `1ce259f214c8`

## D1 — Preserve the rule authority and core grammar

**Decision.** Keep `RULE_HASH = "8b24eb18c704"`, the centered full-height gray divider, equal panels, one connected monochrome object per panel, distinct non-divider colors, and occupancy XOR as the output. Keep overlap, left-only, and right-only relations in every scene. The selected Racket authority is unchanged.

**Why.** Existing source-sync and execution-parity evidence showed that the official rule was already correct. The defect was in the teaching distribution, not the authority.

**Rejected alternatives.** Rewriting the Racket source, changing the semantic rule, or weakening the all-three-global-relations constraint would add risk or revive already known OR/AND/copy/difference ambiguities.

## D2 — Expand the threat model from one border shortcut to a regional family

**Decision.** Retain the whole-border-zero shortcut and add 70 executable lesson competitors. Each regional competitor uses XOR outside one canonical-empty region and substitutes zero, OR, AND, either panel, or either directional difference inside that region. Regions are the full border, four edges, all corners, and four individual corners.

**Why.** The first repair eliminated the single “zero the entire border” rule but did not test smaller spatial exceptions. Independent enumeration showed all 70 regional rules fit 5/5 canonical pairs. On version 2.1.0, 68/70 caused dangerous two-demo lessons in each band, and 66–67 remained dangerous even when the old lessons were lengthened to five demonstrations.

**Rejected alternatives.** Treating the first border rival as representative, adding only prose warnings, or sampling more random generalized scenes. The measured five-demo failures show that probability alone does not establish identifiability.

**Evidence.** `checks/round2_custom/before_regional_shortcut_probe.json`, `checks/round2_custom/before_five_demo_regional_shortcut_probe.json`, and `workspace/regional_shortcut_probe.py`.

## D3 — Respect the fixed-coordinate observation lower bound

**Decision.** Raise `EXAMPLES_NEEDED` from two to five and coordinate relation coverage across the lesson schedule.

**Why.** At a fixed corner, distinguishing XOR from all seven alternate Boolean operations requires seeing left-only, right-only, and overlap. No two-example lesson can display three states at one coordinate. With exact canonical scenes contributing only the empty state at every border coordinate, the schedule must supply at least three generalized demonstrations. Five is the maximum contract-compliant lesson length that can do so while retaining a substantial exact-canonical prior.

**Rejected alternatives.** Keep two demos and declare fewer rivals; set `EXAMPLES_NEEDED` above five; remove canonical scenes; or claim that global relation coverage transfers automatically to each coordinate. The first hides a measured defect, the second violates the return schema contract, the third discards useful manifold support, and the fourth is exactly the shortcut class under test.

## D4 — Use an 18-slot linked schedule with a one-third canonical prior

**Decision.** Use six canonical and twelve generalized slots in a circular 18-slot cycle. Canonical slots follow every pair of generalized slots. The generalized subsequence cycles through phases 0, 1, and 2. A seed-derived rotation prevents an absolute sample-index residue from identifying the profile.

**Why.** Every circular five-slot window then contains at least three generalized scenes, and those generalized scenes include all three phases. One-third exact-canonical support remains far above the profile floor while making the anti-shortcut guarantee possible within the five-demo limit.

**Rejected alternatives.** Preserve the interim 9/20 mixture. Any five-slot window under a near-alternating 45% canonical schedule can contain three canonical scenes and only two generalized scenes, which is insufficient for three corner states. A longer lesson would exceed the supported 2..5 contract.

**Evidence.** The focused schedule regression exhausts all 18 starts for multiple seeds and bands. The official profile floor reports 17/60 exact profiles, and the semantic census observed 202/600 strict canonical scenes (33.7%).

## D5 — Construct the phase witnesses instead of rejection-sampling them

**Decision.** Each generalized phase assigns a Latin-style relation pattern to the four corners. Across phases, every corner is left-only, right-only, and overlap; within each phase, the corner set already includes all three relation classes. For each panel, randomized shortest paths connect required corners while forbidden corners preserve exclusivity, followed by keyed connected growth.

**Why.** Pure rejection sampling could not provide a deterministic lesson guarantee and became increasingly unlikely on small panels. Required/forbidden corner cells make the relation contract exact for every legal dimension, including 4×3 panels, while retaining connected objects and stochastic interior paths.

**Rejected alternatives.** Fill the full border as a fixed scaffold, which would create a conspicuous morphology shortcut; require larger minimum dimensions, which would make the declared override range dishonest; or precompute a small template library, which would reduce diversity.

**Evidence.** Focused tests cover all bands, schedule phases, minimum/maximum overrides, connectivity, determinism, and exact corner relations. The diversity gate reports 100% unique inputs and 95% unique outputs over 300 pairs.

## D6 — Keep the executable semantic and override contracts honest

**Decision.** Expose the 70 regional functions through `REGIONAL_LESSON_COMPETITORS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; retain the basic seven rivals, witness mappings, Python rule mirror, and `lesson_identifiable`. Keep object-color domains at `1..9 (≠5)` with all same-color pairs declared incompatible.

**Why.** An executable contract lets both focused tests and the generic semantic gate name surviving alternatives. Exact axis metadata prevents a cheaper contract defect from obscuring the curriculum result.

**Evidence.** The official semantic gate reports 12/12 identifiable five-demo lessons, no weak witnesses, and no errors or warnings. The override stage passes 29,070 draws and 900 expected structured rejections.

## D7 — Retain before/after causal evidence and state the limits

**Decision.** Keep the original whole-border probe, add the regional probe, preserve TDD red/green logs, and report both the two-demo and five-demo baseline failures. Do not claim exhaustive program-space identifiability.

**Why.** A clean generic battery alone did not discover the second-round shortcut family. The checked-in probe measures the causal quantity of interest: a rival fitting every demonstration and then disagreeing on the query.

**Remaining limits.** The 70-rule family is broad but finite. It does not enumerate arbitrary interior subsets, coordinate-specific lookup tables, or synthesized programs. The five-window guarantee assumes one seed and consecutive sample indices, matching `run_one`; callers selecting arbitrary indices must invoke `lesson_identifiable` or enforce equivalent phase coverage. The one-third canonical/two-thirds generalized mixture is justified by identifiability and gate coverage, not by downstream model-accuracy experiments.
