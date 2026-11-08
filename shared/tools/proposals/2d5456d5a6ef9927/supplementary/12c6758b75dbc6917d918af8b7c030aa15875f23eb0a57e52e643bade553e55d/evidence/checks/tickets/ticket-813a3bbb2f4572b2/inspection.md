# Bounded allocation-quality proposal

**Outcome: completed owner experiment proposal; no allocation or approval changes.** This is not a new safety audit. Existing findings remain source-bound, reviewer-reported and unresolved as recorded by the owner.

## Reproducible sample and freshness

Ticket seed: `5b8271e35324230b77c7398e068ff133fd0279afc7b6a2217cfd21548317a4ae`. Include the pinned anchor `2a43e4f3a796`, then take the two lowest lexicographic SHA-256 values of UTF-8 `seed + ':' + task_id` over actual `PACKET-MANIFEST.json/main_draw_policy/ids`, excluding the anchor. This selects `1d14de95c43e` and `1ea2cf5a712b`. This is one purposive record plus two reproducibly sampled records, not a population estimate. All three happen to be bank families.

`inspection.json` records the exact packet/catalog/context/evidence hashes, seed ranks and current source identities. All three generator hashes match the manifest; canonical rule hashes computed by `Catalog.describe` match the pinned rules. Every inspected file with a packet hash matches that hash. Current source/rule pairs are:

| Task | Current generator SHA-256 | Rule hash | Current version |
|---|---|---|---|
| 2a43e4f3a796 | 6c977b7266d34103024a3670a6f7d2254c6e8e0b7b2060b0af1fe96f51496cc9 | 7b698fc27b90 | 3.1.0 |
| 1d14de95c43e | 56ed271acad477a92d2ff734fd42e24a260fed37bba904d00c232fdbe9d9dd94 | 2d8fe86a8d56 | 1.2.1 |
| 1ea2cf5a712b | 827d15a366ab9d9fdd93e4ffbf6da2071b923e165963a364a8ff75fc53ba7c30 | d20eedb326dc | 3.0.0 |

The derived generator catalog is dated June 21 and describes versions 2.0.0, 1.1.0 and 2.2.0 respectively. Its diversity scores, combinatorial reach and `lint_status: warn` are stale for every selected current generator. They were not used as current quality measurements. The October 23 training context describes frozen r6/r6-h3 exports, not this packet's current production distribution. Configured NVARC item share (28%), materialized item shares (47% ARCpuzzles, 24% NVARC), and token shares (37/36/16/11% ARCpuzzles/NVARC/ARC-GEN/RE-ARC) are different denominators. The older 7.3% large-output share versus 47% public evaluation motivates a question; it is not a fresh estimate for these bytes or a measured optimal mixture. High loss alone is not a defect.

## Actual allocation surfaces

The main reviewer draw is uniform over 500 packet IDs; the manifest marks 297 approved. The packet is a selected subset of 3,941 owner generators, with 3,893 reviewable roots. Inclusion quotas reserve 150 coverage slots, 150 unfinished-original roots, 60 recent-focus roots and 50 public-evaluation roots; these are inclusion policy, not generator draw weights. Independent authoring inspiration has probability 1/10 over 120 public-evaluation anchors (119 inspired extensions and one needing repair/parameters), with unchanged uniform main selection. Ancestry does not establish equivalence or admission.

The actual catalog has 497 `mix_weight=1.0` and three zero-weight rows. Positive weight does not establish approval: the two sampled unapproved records both have weight 1.0 and `not_reviewed_safe` exclusions. Source memberships are bank 273, training 221, augmented 109 and custom four; categories overlap. Parameter-priority metadata lists 151 approved originals needing parameters, 43 originals needing repair/parameters and 29 current prototypes; prototype presence is not production support. Supplementary ticket weights are separate heuristic weights (allocation-quality 10; full mapping in `inspection.json`), sampled among eligible types without replacement.

## Representation, teachability and cost

| Record | Evidence relevant to allocation | Support and cost implication |
|---|---|---|
| Gravity anchor | Current source deliberately mixes dense and sparse long-column teaching. Retained source-matched Racket census reports 300 four-demo/one-query lessons, 1,500 rotations, no listed-rival ambiguity. Retained battery remains failed: 10/12 green, selfcheck and defect-lint fail; grammar, Racket lint and authority synchronization pass. | Stronger teaching support than stale v2 metadata implies. Old one-query census does not itself establish four-query export support. Lawful blank/solid endpoints explain some rejection warnings; a separate current-source invalid-scalar API finding remains unresolved. Do not erase either distinction. |
| Column majority | Current-source retained 400-grid survey found no multicolor columns; first-nonzero fits generated support, although the Racket majority rule differs on an accepted multicolor witness. The new bounded episode likewise gives zero demo refutations of first-nonzero. | Cheap labels and distinct inputs do not teach counting when no noise color appears. Repair effort should purchase the missing semantic branch rather than more same-support draws. No fresh source-matched grammar/battery result was available for this sampled record. |
| Rotated template | Current-source retained audit reports corner-only rival agreement on 300/300 draws, while canonical examples require interior matches. Retained semantic and distribution gates passed (`exit_code=0`, `passed=true`). Earlier imported notes report 599/600 unique inputs but only 60 outputs, and a finite 3×3 grammar; those notes lack an exact current-source hash and are historical context only. | Existing gates and input uniqueness miss position support. Fixing interior-anchor coverage has more potential value than extending the finite grammar blindly. A small board or 3×3 template can still teach useful structure; large size alone is not quality. |

All three defaults were freshly exercised once with four demonstrations and four queries, difficulty `null`. Each produced eight distinct inputs in eight attempts, zero rejections and four distinct query-input hashes. Labels came through canonical Racket. Per-episode wall times were 2.44, 2.44 and 2.38 seconds, including runtime preparation; these are not isolated Racket CPU timings. Default large-output query counts were 0/4 for each, an observation from three episodes only. The template episode refuted all five declared lesson rivals, but that rival list omits the known corner-only shortcut. The gravity default refuted all eleven listed rivals. No lesson check proves universal identifiability.

A fourth episode on the same gravity source used exact existing controls `grid_h=24, grid_w=18`: four distinct 24×18 query outputs, eight distinct inputs, no rejection, 2.32 seconds. This source's declared bounds are height 3..24 and width 2..18. Overrides disable its dense/sparse teaching construction, and these four demonstrations did not refute `modal_background`. **This is a successfully exercised research control, not a validated production training override.** No new prototype or 20–30-size capability was invented for the other two sources (majority declares height ≤10/width ≤12; template declares height 7..9/board width 8..9). The size control needs teaching support before export recommendation.

The one targeted probe consumed 9.71 seconds internally, 10.21 seconds including the wrapper, below 120 seconds. The retained gravity battery's stage durations sum to 125 seconds, so rerunning it would be disproportionate for this ticket. Four-query materialization checks are inexpensive here; semantic review and repair dominate. Exact within-episode dedup is cheap but cannot establish cross-episode novelty or cross-library overlap. Output duplication may be legitimate shared structure and should not be counted as independent semantic coverage. ARC-GEN/RE-ARC source-specific lint, rejection, repair, ambiguity and grammar receipts are absent from the packet's named inventory. This is an evidence coverage gap, not a quality ranking or a reason to move their mixture shares. NVARC's saved-pair protocol and upstream screens are dated context, not rerun here.

## One concrete alternative and explicit estimates

**Proposed authoring experiment only:** compare current 100% uniform main draws with 80% uniform plus 20% directed at current-source, unresolved support gaps with concrete witnesses. Initial directed candidates are the majority/noise and template/interior-anchor repairs above. Preserve the independent 10% inspiration policy, every catalog weight and admission decision. Do not target a source merely because of ancestry or loss.

Define one quality unit as one distinct query in a source-bound four-query lesson whose demos refute the preregistered shortcut and whose query exercises a previously missing lawful branch. Count zero for an unverified repair or merely larger padding. This is a local curation proxy, not measured model improvement.

The following are **planning assumptions, not measured yields or timing forecasts**. For a uniform slot assume a 0.40 chance of delivering a qualifying four-query lesson at six human minutes (3.5 authoring, two review, 0.5 novelty/dedup assessment). For a directed slot assume 0.70 at eight human minutes (five repair, 2.5 review, 0.5 novelty assessment). Runtime is reported separately, with a 120-second hard cap per slot; the current ~2.4-second episode observations cannot forecast repair validation cost.

| Ten-slot plan | Expected quality units | Estimated human minutes | Quality units/minute |
|---|---:|---:|---:|
| Current: 10 uniform | 10 × 0.40 × 4 = 16.0 | 60 | 0.267 |
| Proposed: 8 uniform + 2 directed | 8 × 0.40 × 4 + 2 × 0.70 × 4 = 18.4 | 64 | 0.288 |

This scenario gives an estimated 7.8% improvement per human minute, not evidence of superiority. At the stated costs the directed success rate must exceed 0.533 (=0.40×8/6) to beat uniform; at 0.40 it loses. All failed attempts and dedup review time must remain in the denominator. The proposal narrows work to documented gaps while keeping 80% breadth; it could still overfit a small rival family and miss new representations.

**Bounded pilot/stopping rule:** the owner could run six slots, three uniform and three directed, alternating arms with independently seed-ranked selections and at most one slot per family per arm. Pre-register the relevant branch/rival and hashes, cap each slot at ten authoring minutes and one 120-second probe, and stop after six slots or 60 authoring minutes/12 runtime minutes, whichever limit arrives first. Keep four independent demos and four distinct queries, record accepted/rejected indices, source hashes, cross-slot input hashes, branch novelty and actual human/runtime cost. Stop a candidate immediately when source identity drifts, Racket labels disagree, the chosen rival survives the demos, or the probe cap is exhausted; count its cost and zero qualifying units. Two repeated already-covered branches end a directed family attempt. Retain small cases alongside meaningful large cases. Continue to a larger owner experiment only if directed quality/minute exceeds uniform by at least 10%, achieves at least two qualifying lessons in three slots, and introduces no unresolved sampled lesson ambiguity; otherwise retain current allocation. A six-slot pilot is only a go/no-go screen, not a statistically established optimum. Nothing in this proposal has been applied.

## Exact executed command

From `/workspace/scratch/531bd5d78e91/arc_review` (the wrapper executes payloads from `WORK/repo`):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 review.py run --receipt checks/tickets/ticket-813a3bbb2f4572b2/command.json python3 -B ../checks/tickets/ticket-813a3bbb2f4572b2/probe.py
```

Episode seed recipe: unsigned integer from the first eight hex digits of SHA-256 of UTF-8 `ticket_seed + ':episode:' + task_id`, giving 2534582885, 881303497 and 994417137. Sample index is zero. The gravity size comparison reuses its default episode seed. `probe.py` is the exact executed script; `command.json` records exit zero and wall time; `probe.json` preserves hashes, shapes, sampling receipts and finite-rival results without grid dumps. The sole residual temporary runtime copy was removed after completion; no copied runtime tree is retained.
