# Current design: bd05f2963d17

## Source and authority

Review assignment `review-70a0f19396e55ef7` repairs imported version 1.2.1 to 2.0.0. The generator SHA-256 is `1ac8661d588b8a0c172451f52346522319e2a72a497eab251a8b770d431cf823`; baseline SHA-256 is `e933f69a972474932475d7eac8268a3f06361aad7ef433c4e16080e73b1beb2a`.

The selected Racket rule remains `97705631e594`, with normalized source SHA-256 `97705631e594b7818bc43b500af59b534dfd19cd80a380c26f8e9236d3c1f3b6`. Its exact callable-text SHA-256 is `4b01d437846ec92d03fa3288b451db668d6ce98f13385ef9b1d0a71d70dc1cdf`. No rule, canonical pair, catalog entry, shared runtime, or audit target was edited. The selected and archival authorities already differ; the authority-sync stage reports selected execution parity and preserves that distinction.

The rule finds color-3 four-neighbor components, sorts by `(cell count, bounding-box top row, bounding-box left column)`, takes the second component, and doubles each of its cells at the bounding-box origin. It paints those doubled cells color 8 in a blank color-0 grid of the original dimensions. Neither a component's first occupied cell nor its bounding-box area determines the anchor or rank.

## Reproduced defects and changes

**R1 — Unteachable rank distinctions.** The baseline emitted exactly three components. On that support, second-smallest, second-largest, lower median, and upper median select the same object. All four canonical pairs have the same size-2 domino, size-4 S target, and size-5 L distractor; they additionally permit fixed-size, fixed-shape, bounding-box-rank, position, and first-cell-anchor shortcuts. The repair introduces actual counts 3, 4, and 5 and varied component sizes, shapes, and positions. It declares eight executable rivals and checks each claimed canonical shortcut against every usable canonical pair.

**R2 — Controls and profile claims differed from behavior.** Baseline metadata exposed ignored controls, silently accepted unknown keys, and described widths down to 12 even though ordinary samples started at 13. Difficulty clamping could break explicit dimensions, and the canonical 11×11 canvas was unreachable. The repair advertises only three actual integer controls, rejects unknown/removed keys and noninteger values, and observes exact dimensions and actual component count. Every combination of the advertised controls is supported in every difficulty band. Eleven-row and eleven-column profiles have substantial default probability while the full declared ranges remain available.

**R3 — Validator failures.** The old validator could raise on malformed grids and accept illegal cell types or ragged inputs. The repair returns reasons for malformed rows, colors, booleans, size ties, too few components, and an out-of-bounds doubled target. Canonical inputs remain accepted. The validator deliberately accepts lawful inputs with more than five distinct-size components; sampling 3..5 components is a distribution choice, not a claim that the Racket rule stops at five.

## Sampling and lesson policy

Exact controls are `grid_h` from 10 through 16, `grid_w` from 11 through 17, and `n_components` from 3 through 5. Values must be actual integers, excluding booleans. A known key with value `None` requests its default. Colors remain fixed at 0 and 3; the Racket rule tests color 3 and writes color 8, so an arbitrary palette permutation would change the task.

Even sample indices use a general family. Counts are drawn from 3..5; easy sizes come from 1..7, medium/default sizes from 1..9, and hard sizes from 3..9. Connected polyomino growth uses bounding boxes of up to 3×3 or 4×4. Rank positions are shuffled and only actual four-neighbor contact is prohibited; diagonal proximity does not merge components. The target's full doubled bounding box must fit.

Odd default indices use a five-component teaching family. There is one smaller component of size 1..4, a size-5 target, a solid size-6 rectangle, and size-7 and size-8 distractors. The target is sampled from all 14 connected five-cell 3×3 shapes whose top-left bounding-box cell is empty. Its bounding-box area therefore exceeds the size-6 rectangle's area, its first occupied cell differs from the correct anchor, its shape differs from the canonical S, and it is placed away from the bottommost rank position. Each such example refutes all eight named rivals.

The semantic/profile schedule has declared period 4: profile/general, profile/teaching, varied/general, varied/teaching. Phases 0 and 1 weight 11×11 strongly; the other phases use broader difficulty-dependent dimensions. Random content is not periodic. Four consecutive default sample indices contain two teaching examples, so three demonstrations and one query retain at least one complete witness under every one-query holdout. `EXAMPLES_NEEDED=3` and the declared lesson hook express this policy. Actual assembled episodes must still be checked: skipped indices, smaller demonstration sets, multiple held-out examples, and explicit count overrides can change the guarantee. Count 3 or 4 overrides are honest input controls and explicitly do not promise the default rank-identification contract.

## Placement and bounded fallback

Random placement makes at most 40 full attempts. If these fail, the generator uses six separated 3×3 slots at rows 0/4 and columns 0/4/8. These fit even the minimum 10×11 canvas. The target is selected only from slots where its doubled bounding box fits; teaching targets use the top row. General-family shapes are regenerated compactly with the same sizes before this fallback. Dimensions, counts, distinct sizes, connectivity, and the transformation are preserved.

An independent review forced exhaustion across 48 combinations of difficulty, count, index parity, and minimum/maximum dimensions, then checked all 14 teaching shapes. Permanent regressions now force that path too. This bounds failure behavior without replacing ordinary randomized placement with a fixed spatial template.

## Verification and useful tools

The two task-local suites contain 144 passing cases under the public isolated `task_tests` stage. They use the portable `reviewer_support` root and canonical-pair helpers. `test_sampler_contract.py` covers exact controls, canonical support, and malformed inputs. `test_semantics.py` includes an independent component/scaling oracle, canonical-fit checks for the actual rival declarations, source- and rule-bound Racket fixtures, default lesson windows, query holdouts, general-family target diversity, and forced fallback.

`counterexamples/semantic_rivals.json` contains small handmade fixtures labeled by the selected Racket rule. They are validator-supported examples; their presence is not proof of exact sampler emission. The retained review evidence includes a reusable baseline probe, an independent rival/design probe, and the public lesson-census reports. Use the existing `arcpuzzles lesson-census` tool instead of duplicating it.

Measured final results at the source hash above: all 12 public battery stages green; 600/600 strict-domain draws; 9,990/9,990 override draws accepted with no findings; 30/60 exact canonical-size profile hits; 300/300 random production lessons and 1,200/1,200 one-query rotations without declared-rival ambiguity. The random census contains 1,200 unique input hashes. Enumeration of all four declared start residues at seed 0 across three bands gives 12 passing lessons, 48 passing rotations, and 21 unique inputs because windows overlap. These counts test eight distinct algorithms, even though the census lists them under several declaration namespaces.

The original 125 sampler tests first failed 103 cases and passed 22; the original 16 semantic tests first failed 12 and passed 4. Those real red results and their source/test hashes are retained. The public isolated run initially lacked pytest; an independent virtual environment containing the declared dependencies fixed that infrastructure prerequisite without weakening isolation.

## Limits and rejected alternatives

The task domain still excludes size ties and fewer than three components. This preserves the imported domain and keeps the targeted rank lesson clear; changing tie behavior would be separate work. Five components suffice to separate the tested rank alternatives without overcrowding the smallest canvas. Larger counts and every possible connected shape are not exhausted by the sampler.

Teaching examples correlate size 5 with the target. General-family samples deliberately include five-component inputs with non-five targets, and the regression verifies those occur; the mixed distribution reduces that specific shortcut. The repair nevertheless certifies only its named rivals and measured seed ranges, not universal identifiability or any measured gain in Qwen3.5-9B accuracy.

Rejected alternatives were keeping exactly three components, adding descriptive axes without observable behavior, uniformly sampling wider canvases while losing canonical-size support, always placing objects in fixed slots, and changing the reference rule to accommodate palette controls. Broad shared-tool edits and repair of unrelated audit targets are outside this assignment. Imported historical notes remain in `evidence/associated_notes.jsonl`; this file records the current design.
## Current reviewer considerations

Source SHA-256: `1ac8661d588b8a0c172451f52346522319e2a72a497eab251a8b770d431cf823`.

# Decisions for review-70a0f19396e55ef7

## Scope and authority

Repair only `repo/generators/bd05f2963d17/`, retaining the assigned task, question, blind solve, and two audit draws. Version moves from 1.2.1 to 2.0.0 because sampling support and override behavior change materially. Racket rule `97705631e594` is unchanged. Final generator SHA-256: `1ac8661d588b8a0c172451f52346522319e2a72a497eab251a8b770d431cf823`.

R1 is the rank/shape/anchor teaching defect; R2 is the inaccurate control/profile contract; R3 is the malformed-input validator defect. The source delta, permanent tests, and current task notes address these directly. No shared source, catalog, canonical labels, audit source, or approval state was edited.

## Distribution decisions

| Decision | Reason and rejected alternative |
|---|---|
| Sample 3..5 distinct-size components | Exactly three makes second-smallest indistinguishable from second-largest and both medians. Four separates some ranks; five separates both medians. Counts above five add packing cost without being needed for this repair. |
| Alternate general draws with complete five-component witnesses | General randomness alone does not ensure a particular lesson contains a refuting example. A complete witness every other index supplies redundancy for query rotation. Sampling only the witness family would teach a size-5 shortcut, so the general family remains broad and includes non-five targets with five components. |
| Three demonstrations, one query; every one-query holdout supported on default consecutive four-pair bundles | Such a bundle contains two complete witnesses. One remains after any single holdout. This policy is tested both on materialized production lessons and on all allowed query rotations. Count overrides 3/4, arbitrary skipped indices, fewer demonstrations, and multiple simultaneous holdouts do not inherit this guarantee. |
| Preserve colors 0/3/8 | The reference selects color 3 and writes color 8. A palette axis would be a false control or require a rule change. Removed keys now fail explicitly. |
| Expose actual `grid_h=10..16`, `grid_w=11..17`, `n_components=3..5` | Values are strict integers and all joint combinations work in every band. Difficulty affects default distributions, not explicit control compliance. |
| Weight 11×11 profiles in two of four phases | All four canonical inputs use that canvas. Baseline sampling missed it completely. Broad phases retain other dimensions; every advertised dimension stays reachable. Final measured profile hits: 30/60, compared with 0/60 before. |
| Random placement with a constructive compact fallback | Forty attempts bound ordinary packing. The fallback preserves exact dimensions/counts/sizes and target fit. Always using a slot template would introduce an unnecessary position cue. |
| Retain distinct-size, ≥3-component validation domain | Ties and tiny component counts were not needed to resolve the observed defects. The rule itself is unchanged, and the validator allows lawful counts above the sampled maximum. |

## Evidence and reversals

The baseline source hash `e933f69a972474932475d7eac8268a3f06361aad7ef433c4e16080e73b1beb2a` is retained with its bounded probe and genuine failing tests. The 125-case sampler suite initially had 103 failures; the 16-case semantic suite had 12 failures. The implemented repair passed all 141 initial cases. Independent code review then identified the value of forcing the compact placement path, so two parameterized regression cases were added; a third regression captures the intentional rotation negative used in the question answer. The final count is 144 passing tests. Generator bytes did not change after the post-repair solve.

The Python semantic oracle is independently authored, then checked against four canonical and eight handmade inputs executed through the selected Racket authority: 12/12 agree. Handmade fixtures are labeled as validator support, not claimed emitted samples. Retained probes iterate the generator's actual rival declarations rather than silently maintaining a second list of names.

Final production coverage: 100 hashed seeds per band, requested start indices 0..99, 300 materialized three-demonstration/one-query lessons, 1,200 unique input grids, and 1,200 rotations. No declared-rival ambiguities or materialization/scoring errors occurred. The separate fixed-seed census uses seed 0, start residues 0..3, and easy/medium/hard: 12 lessons, 48 rotations, 21 unique inputs. The latter windows overlap and do not represent 48 independent draws. The full exact seed recipes, accepted indices, grids, and source hashes remain in the two census reports.

The first isolated task-test run correctly reported a missing pytest dependency. Installing NumPy, Pillow, and pytest into an independent per-checkout environment fixed that prerequisite while preserving `PYTHONNOUSERSITE=1`. A public repository-suite run has genuine inherited failures documented in `REVIEW.md`; no out-of-scope assertion or runtime changes were used to make that suite appear green.

## Self-review and limits

The teaching family has deliberate structural cues, including its size-5 target and empty bounding-box corner. General draws contain non-five targets in five-component scenes, varied placements, and larger shape boxes; the permanent tests check these features, while the claim remains limited to eight declared rivals rather than every possible shortcut.

A production-only pass is insufficient if a later exporter moves the only refuting example into the query. The intentional negative in `test_production_success_does_not_bless_witness_query_rotation` demonstrates this cheaply and supports shared suggestion F1. It is a deliberately constructed diagnostic, not a fabricated failed solve.

Both visible solve episodes preserve their actual first attempts and notes. The blind attempt passed five visible pairs but extrapolated an unseen selector with explicit uncertainty. The exposed post-repair attempt passed three visible pairs from final generator bytes. Masked query correctness is unknown in both records; neither is labeled a successful hidden evaluation or admitted training trajectory.

## Native parametric admission — review-fddcc66c90d9a247

The task now has a source-bound native family under `workspace/parametric/`.
The default `rank_order=second_smallest` returns the exact canonical Racket
bytes (`97705631e594b7818bc43b500af59b534dfd19cd80a380c26f8e9236d3c1f3b6`).
The alternate `rank_order=second_largest` keeps component extraction,
normalization, 2x rendering, colors, and anchor semantics fixed, but selects
the second record from the opposite end of the same input-derived size order.
The approved production generator remains byte-identical at
`1ac8661d588b8a0c172451f52346522319e2a72a497eab251a8b770d431cf823`.

The adapter accepts 2..6 demonstrations and 1..4 queries independently. Its
prefixes do not depend on requested totals, both settings receive byte-identical
inputs, and public projection reveals one query without settings, programs,
answers, future queries, or total-count hints. Four private queries are always
available; the last is a 30x30 case with seven distinct-size components and
foreground contact on all four boundaries.

The first two demonstrations are not accepted merely because the intended
settings differ. A deterministic teaching constructor retries scene placement
until both settings refute every declared finite rival: opposite rank,
extremes, median, bounding-box-area order, reading order, missing scaling,
first-cell anchoring, and bounding-box filling. Invalid rival executions on a
lawful demonstration count as refutations. The reusable `self_audit.py` checks
this condition over 64 seeds, count-prefix stability, matched inputs, protected
Racket parity, 30x30 stress properties, and exact content-addressed public
exports. These checks certify only the declared finite candidate set and tested
seeds, not universal identifiability or measured model improvement.

The sequential causal account is: Step A extracts all color-3 four-connected
components and orders complete records by `(size, bbox row, bbox column)`;
Step B selects the episode-directed second record and renders its normalized
shape at 2x scale from the derived bounding-box anchor. The admission witness
counterfactually substitutes the opposite rank-direction program, so the
selected record changes while all downstream rendering logic remains fixed.
