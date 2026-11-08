# 33c7c507a8ef — review-c163cb377b0acf2c

## Rule and authority

Version 4.0.0 retains canonical rule pin `a03a4d8f590f`. The top-left code selects identity (1), clockwise (2), half-turn (3), or counterclockwise (4) rotation of the complete gray frame's interior. Gray inside the frame is content and survives. The canonical Racket program and stored public labels are unchanged.

## Repair and evidence

The baseline independent code sampler could put an unseen code in the query. Seed 0, hard, start index 1 produced demonstrations [3,2,2,4] and query 1; a code-1-as-clockwise rival fit every demonstration and failed the live Racket query. The exact source-bound lesson is retained in `counterexamples/missing-code-1-before.json` and the review's `checks/baseline-lesson/` evidence. No selected-task review index or previous return was used as a repair lead.

The default sampler now uses a seed-shuffled, phase-shifted 16-slot cycle. Every eight consecutive draws contain each code twice, with opposite interior-gray states. `EXAMPLES_NEEDED = 7` supports one held-out query at any position in such a window. Each window also contains at least two expanded frames and at least two compact gray/non-3 examples, preserving demonstrated refutations of both fixed cropping and a size-conditioned gray/half-turn shortcut after any single holdout.

The explicit schedule has ten compact and six expanded slots, keyed by the positions of codes 1 and 3 in the shuffled order. The retained finite search examined all 24 code orders and found ten compact slots minimal under the chosen constraints. Public-draw regressions independently discover all twelve relevant position combinations and verify the resulting inputs rather than copying the table. This is bounded curriculum support, not a proof against undeclared hypotheses.

## Distribution choices

Exactly three slots per cycle preserve the linked public role-and-geometry profiles, one each for codes 2,3,4. Code/content color equality is part of the signature. Seven further slots preserve the 5×6 input and four-total-color envelope but vary the interior beyond the exact public profiles. Six expanded generalizations vary dimensions, placement, margins, palette and texture. Strict public support is 3/16; coarse compact support is 10/16.

The compact share meets the battery's actual 25% size/palette floor while retaining independent shortcut witnesses. An intermediate compact candidate kept gray perfectly correlated with code 3 within small inputs; its source-bound counterexample and failing tests are retained in the return. The final schedule breaks that conditional correlation. Naive larger compact shares were rejected because they could leave just one expanded-frame witness in a lesson.

Explicit non-None overrides disable the lesson schedule and remain exact per-draw controls. Known None overrides equal omission; unknown keys and lossy scalar coercions are rejected. Seed and sample index require nonnegative integers and reject booleans. No teaching guarantee is claimed for arbitrary override sequences or an untested downstream sampler.

## Executable review support

The semantic contract declares 16 rivals: twelve single-code wrong rotations plus fixed public cropping, gray-implies-half-turn, compact-gray-implies-half-turn, and gray erasure. Claimed canonical shortcuts are checked against every linked public pair. The lesson hook learns code meanings only from demonstration inputs and outputs, without reading a query answer; separate rival checks cover extraction and color shortcuts. The existing domain still requires four distinct quarter-turn results, a complete frame, lawful colors, and its documented size and placement bounds.

Tests live under this task's `tests/` directory and use portable `reviewer_support` discovery. All seven prior selected tests were preserved; the deprecated recorder accessor and private import/fixed-depth canonical path were migrated. The return contains direct and staged tests, actual Racket checks, 100 production lessons per band, every declared cyclic start at seed 0 with every query position, and an exact-patch fresh-copy replay. Full source hashes, measured counts, failed candidates, and limits are in its `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json`.

Training admission remains false. Other assigned generators received findings-only audits; no other task or shared tool was edited.
## Current reviewer considerations

Source SHA-256: `1e0fba152cbbdc340d753d076450a3004ce7b519417bf7d1c4970ae475c622b2`.

# Decisions for 33c7c507a8ef

## R1 — Teach query codes under the actual lesson policy

The reference rule crops the gray rectangle's interior and applies the corner code: 1 identity, 2 clockwise, 3 half-turn, 4 counterclockwise. The public demonstrations contain codes 2–4. The prior default generator sampled codes independently and declared four required demonstrations. The exact seed-0 hard lesson in `checks/baseline-lesson/` makes the resulting unobserved-code failure reproducible. There was no selected-task review index and no prior return was used as a repair lead.

The repaired default has a 16-position schedule, seeded by task identity and version. It shuffles the four codes and chooses a phase; every eight consecutive draws contain each code twice, once with gray interior content and once without. All eight inputs are therefore distinct. `EXAMPLES_NEEDED = 7` supports any one held-out pair from such a window, including arbitrary reordering of those seven demonstrations. The live production census and the required query-rotation census are reported separately in `REVIEW.md`.

An ordered four-code demonstration cycle would be cheaper, but a query held out of those four leaves its meaning unobserved. Independent draws with a larger count reduce the risk without eliminating it. Seven demonstrations plus one query are the smallest window under the chosen class of four independently learned meanings that can contain every meaning twice. This is a statement about that hypothesis class, not about every conceivable induction strategy.

The schedule applies only when overrides are absent or all their values are `None`. Explicit non-None overrides request a lawful controlled draw and intentionally disable the teaching schedule. No lesson-level guarantee is made for arbitrary override sequences, arbitrary gaps in accepted sample indices, or a different downstream sampler. The public censuses exercise the actual production sampler, including its rejection behavior.

## R2 — Preserve the public examples' roles, not just a silhouette

The former profile comparison normalized content colors without preserving equality between an interior role and the corner code. That admitted nominally canonical examples with a different total palette and lost the code/content relationship visible in the public pairs. The repaired signature distinguishes the corner-code role, frame role, and other colors. Codes 2 and 4 preserve their public code/content equality; code 3 uses gray content with a separate non-code color. Public examples remain valid and the Racket source remains unchanged.

Exactly three of each 16 default slots retain the strict public role-and-geometry profiles, one each for codes 2, 3, and 4. This is 18.75% strict support, close to the previous intended approximately 20% family prior, with deterministic coverage instead of an independent coin flip. A code-1 strict profile is not invented because it is absent from the linked public family. Code 1 is taught in generalized scenes.

## R3 — Meet the actual profile floor without making geometry the rule

The first after battery revealed that the enforced profile gate requires at least 25% canonical-size/palette support; the packet duties describe a weaker one-hit-per-20 condition. Increasing only the exact family prior would repeat the small public templates more often. Instead, compact generalized examples keep the public 5×6/four-total-color envelope while varying the interior arrangement beyond the exact public signature. Expanded scenes continue to vary rectangle dimensions, placement, and outer margins. Bounded rejection excludes accidentally exact compact signatures rather than silently mislabeling family provenance.

An intermediate plan used eight compact slots out of 16. Independent review showed that its compact scenes retained a perfect gray/half-turn cue. Merely moving the eight compact slots could expose that cue, but some eight-example windows would then contain only one refutation, and holding that pair out recreated a lesson ambiguity. Increasing compact support naively to 12 slots caused the opposite risk: too few expanded examples to refute a fixed public crop after a query holdout.

The final plan uses **10 compact and six expanded slots**: three exact public profiles, seven generalized compact profiles, and six expanded generalizations. A small exhaustive search found a valid schedule for every possible placement of codes 1 and 3 in the shuffled order. Each cyclic eight-slot window has at least two expanded inputs and at least two compact inputs with gray content and a non-3 code. Every code also has both gray states within compact scenes over the full period. No nine-compact schedule satisfied all these requirements; see `checks/final-code-review/schedule-search.json` and its retained search script. The explicit table avoids runtime search and makes the finite schedule reviewable.

Compact support is therefore 62.5% over the cycle, while exact support remains 18.75%. This is a deliberate restriction in geometry frequency, retained to balance the enforced public-profile gate with independent shortcut refutations. It does not expand the documented legal domain beyond the existing interior-size, palette, placement, and asymmetry bounds.

## R4 — Make the known rivals executable

The task declares 16 distinct competitors: the 12 wrong assignments of an individual code to another rotation, a fixed public crop, a gray-implies-half-turn rule, its compact-size-conditioned variant, and a rule that erases gray content. All claimed canonical shortcuts are tested against every linked public pair. Witness names map to the actual rival declarations rather than a copied name list in an external probe.

The `lesson_identifiable` hook intersects rotation meanings learned from demonstration inputs and outputs, then asks whether the query's code has a unique demonstrated meaning. It never reads the query answer. The separate rival machinery tests extraction and color shortcuts. A successful hook alone is not a claim that every plausible rule was refuted. The finite rival set is justified by concrete failures and natural public-data shortcuts; new counterexamples remain possible.

## R5 — Enforce exact call and override contracts

Seed and sample index must be nonnegative integers, with booleans rejected. Advertised integer overrides reject booleans, fractional values, and numeric strings; boolean overrides require booleans; the scene family requires a string. Unknown keys fail even if their value is `None`. Known `None` overrides are removed before compatibility decisions, so they behave exactly like omission rather than changing the draw or raising a spurious canonical conflict.

Coercion was rejected because an advertised exact control should not silently change its value or type. The existing lawful value ranges and explicit incompatibility checks remain in force. The selected regression suite includes previously failing type cases, omission equivalence, public-profile roles, cyclic lessons, and query-answer independence.

## Portable tests and scope

The existing selected test file was migrated to the supported `reviewer_support` root and generator-loading helpers. Its seven prior tests remain; no frozen root fixture or shared test was rewritten. This fixes a selected-file fixed-depth import/path assumption that failed before portable execution. New tests remain under the selected task's `tests/` directory and are explicitly run through the public staged `task_tests` check, because the root pytest suite does not discover them.

Both assigned audits are findings-only. Their reproduced shortcomings and exact source bindings are recorded in `AUDIT.md`; their generator, rule, notes, and tests are unchanged. The broad repository failures are separately diagnosed rather than attributed to this repair without evidence. No admission status, canonical Racket program, shared runtime, other generator, or training policy is modified.

## Evidence and stopping rule

Baseline failures and all meaningful failed candidate iterations remain in the return. Reports identify their source hashes so an intermediate pass cannot be substituted for a final-source check. Large evidence is compressed losslessly with verified original-byte hashes and a restoration tool. The final handoff applies the exact packaged delta to a fresh copy, compares every changed file, and reruns the focused regressions and live reference smoke check there. Masked solve labels remain unknown to the reviewer and are reserved for maintainer scoring.
