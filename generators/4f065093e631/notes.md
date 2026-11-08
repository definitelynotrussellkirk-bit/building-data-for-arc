# Current notes: 4f065093e631

Reviewed version **3.1.0**, generator SHA-256 `44637c626bd95413b08cf1a4620a026c2b1f6e792faee54969a52d3580bfd99e`; selected normalized rule hash `6d3fbf3d14b4`. This is review `review-996842bdd046f186`, original family training `890034e9`. Approval remains a separate catalog action.

## Rule and accepted domain

Select the largest nonzero monochrome rectangular frame with a zero interior; paint the first other zero-interior slot of the same dimensions in row-major order with its color. Production inputs have a unique largest source and exactly one eligible, disjoint target. The broad Racket rule preserves its historical reverse-enumeration tie order when equal-area frames exist. The Python mirror now follows the same `(area,color,top,bottom,left,right)` descending order.

Production retains the 21×21 canvas, all four demonstrated source dimensions, dense two-color background and count bounds, and the exact observable `scene_profile` control. Even indices use the original four-color construction. Odd indices add a fresh-color, disjoint 3×3 hollow frame with eight cells. That smaller frame is rarer than the true source. The validator accepts only the complete structured extension; a lone extra color or incomplete decoy still fails. The original four-color branch alone supplies strict canonical palette-size support.

Three demonstrations and one query are the evaluated lesson format. The decoy branch has period two; a separate full-palette bijection cycles the source through low, interior and high numeric rank with period three. `LESSON_SCHEDULE_PERIOD=6` reports their joint period. Each four-pair window retains counterevidence to rarity and both numeric-extreme conditional rivals after any one pair is held out. Exact seed/index inputs remain deterministic and use keyed RNGs. Signed integer seeds are supported; Boolean/noninteger seeds and negative/noninteger indices fail explicitly.

## Reversed decisions and evidence

- **Four-color-only sampling → retained anchors plus scheduled smaller-frame decoys.** Previously, the rarest nonzero color located the source on all four canonical pairs and 24 retained baseline draws. `counterexamples/rare_color_shortcut_v2.json` is a lawful final-source generated counterexample at seed 817/index 1/medium/profile `frame_4x5_balanced`. Actual Racket and mirror outputs agree; the rarity rival differs on 22 cells. The earlier unscheduled witness is retained with its earlier hash.
- **Unconstrained random palette roles → independent three-step rank cycle.** The first after-run found three exact query rotations where min/max conditional rivals survived the demonstrations. Their retained lessons drove the period-six repair. Declared rivals now include rarity, identity, first-color-only and last-color-only; the latter two are conditional transformation rivals, not canonical-fitting shortcuts.
- **Repeated rectangle cell-list scans → prefix counts and necessary corner guards.** The stored source is `workspace/performance/optimized_rule.rkt`. It preserves candidate ordering and the exact selector/paint fragments. Twenty-seven distinct inputs agree with original Racket behavior, including four anchors and equal-area/multiple-target cases. A broad 30×30 stress case dropped from 18.592250 seconds to 0.103885 seconds in one diagnostic comparison. The normal timeout remains unchanged. The originally reported seed4/index3 timeout did not reproduce deterministically in an isolated bridge; infrastructure startup failures are recorded separately.
- **Divergent active authority text → identical canonical and selected base target.** Archival raw code remains unchanged. Its normalized hash is `04dc58ab5b0ed9048b0c9b19eb6fc5583f61fac391583ab74b2e22bbcf59db96`.

## Proposed extension and useful tools

`workspace/parametric/target_policy.py` constructs episodes for `first`, `last` and `all` eligible targets. Default `first` is the exact active canonical program. Multiple-target demonstrations and larger queries teach the fixed episode policy. Labels are actual Racket executions. Anonymous public challenge files contain no parameter or query label, and an independent RNG shuffles their numbering. This is proposed authoring work outside the calibrated production validator, not approved variants.

`workspace/tools/verify_parametric_bundle.py` independently verifies source/program/grid hashes and exact public projections, then optionally executes every setting on every pair and recomputes production/rotation ambiguity. Its contract is self-contained Racket lambdas, not the full DSL. `workspace/performance/probe_rule.py` retains exact-source timing and differential comparisons. Both use public runtime APIs and refuse evidence overwrite.

The final selected-task gate passed **129 JUnit cases, zero failures/errors/skips**, including the inherited 1,200-draw distribution regression. The fixed-seed schedule census covers six starts × three bands = **18 lessons, 72 rotations and 27 unique inputs**. Larger final-census and battery receipts are in the return's `checks/` manifest; their exact commands and source bindings are recorded in `RESULTS.json`.

## Known limits

The canonical generator remains fixed at 21×21, four source dimensions, one target and source border counts of 14/18. Count/shape heuristics beyond the declared rival set may remain. The original single-target domain cannot distinguish first/last/all; the proposed extension supplies that evidence separately. Random census results and fixed-seed schedule enumeration do not prove all-seed or universal identifiability. Wall-clock measurements are subject to machine contention. Visible-only solve success leaves masked-query accuracy unknown.

## Current owner source and evidence limits

Accepted version3.1.0 prefix-count rectangle optimization, exact scalar guards, rare-color decoys, a six-position source-rank schedule and broad-mirror reverse-enumeration ties. Canonical program and selected target now use reviewed optimized Racket,normalized hash6d3fbf3d14b4;archival raw_code is preserved. Owner isolated the canonical diff to this one program field and reviewed predicate/order preservation;27-input original/archival/optimized parity remains reviewer-reported. Reviewer reports12 green stages,129 portable tests repeated in a fresh334/98737-file dependency closure,300 lessons/1200 clean rotations/1200 unique inputs and18 seed-zero lessons/72 rotations/27 unique inputs. Intermediate searched-rival findings9 production/40 rotation ambiguities were repaired;final seven-candidate search is clean. The1200-context semantic-alias scan is Python diagnostic,not1200 new Racket calls. One30x30 timing comparison18.592s->0.104s is a single-case observation;the old seed4/index3 timeout did not reproduce consistently. The first/last/all target-policy prototype has3 episodes/12 pairs,4 canonical anchors and36 independent verifier executions with no label/declared-policy errors. Public filenames are shuffled independently,with32-seed regression. The task-local general verifier remains an unapproved shared-tool proposal. Production support remains21x21/four profiles;finite rivals do not rule out all count/shape heuristics. No variant or training admission.
## Current reviewer considerations

Source SHA-256: `44637c626bd95413b08cf1a4620a026c2b1f6e792faee54969a52d3580bfd99e`.

# Decisions — 4f065093e631, review-996842bdd046f186

## Scope and sequence

This is the assigned original family, training `890034e9`. The separate blind solve was completed before repair/reference inspection. A runnable parameter prototype was developed before changing the canonical production generator. Proposed parameter variants remain separate from the canonical repair and need their own maintainer decision. No audit target is edited.

The original generator was version 3.0.0, SHA-256 `ecc388975e999108832bff4d4bf8ab788f2583152a40a392b26cd5c626daa836`. Its calibrated source profiles and input examples supplied the design constraints. Earlier retained task notes were a placeholder; no undocumented historical rationale is assumed.

## The rule and its authority

Find the largest nonzero monochrome rectangular border with an entirely zero interior. Its dimensions determine the eligible zero-interior slots. Exclude the source and paint the first remaining slot in row-major order with the source color. The production domain has a unique largest source and exactly one eligible target. The broader Racket program also has defined ordering when there are multiple targets or equal-area frames; those orders were preserved.

The active canonical program and selected base `target_code` initially differed in text, although their outputs agreed on the checked inputs. Both active locations now contain the same reviewed optimized program. The archival `raw_code` is preserved byte for byte. Only the selected canonical row and selected base field were changed; `checks/authority-integration.json` records the before/after hashes and unchanged-field checks.

The optimizer replaces repeated rectangle cell-list construction with per-color prefix counts and necessary corner tests. It retains the original candidate enumeration, reverse-cons accumulation, stable descending-area sort, slot enumeration, and final painting. This avoids changing a task definition merely to solve an execution-cost problem. A larger timeout or a narrower input domain was rejected.

The 26-case comparison covers all four canonical anchors, twelve profile/band draws, the originally reported seed/index, and nine constructed cases. It contains 78 successful executions across original canonical, archival, and optimized rules. An additional broad-domain stress input gives identical original/optimized outputs. These are finite comparisons, supported by a predicate/order preservation argument in the performance README; they are not an exhaustive proof over every ARC grid.

The retained stress input timed out at the ordinary 10-second budget. With a diagnostic 60-second budget, the original completed in 18.592250 seconds and the optimized program in 0.103885 seconds. Production timeouts were not increased. The exact seed 4/index 3 originally seen in the failed battery did not deterministically time out in an isolated bridge. One separate readiness probe also timed out before evaluating a rule. The reports distinguish algorithm cost from startup/contention evidence.

The broad Python mirror had an independent equal-area tie defect. Racket's ordering corresponds to descending `(area, color, top, bottom, left, right)`. Two retained failing examples and a passing control justified correcting that order. Production's unique-largest requirement was retained.

## Canonical distribution: retain anchors, teach geometry

The original 21×21 canvas, four source dimensions, noise envelopes, exact `scene_profile` control, unique-largest source, and single target are retained. They preserve measurable support for the canonical demonstrations. Broadening everything to arbitrary dimensions would obscure whether the original family still had support; that broader exploration belongs in the separate prototype.

The original four-color scenes let the rarest nonzero color identify the source without recognizing frames. The executable `rarest_color_bbox` rival fits all four canonical pairs and all 24 retained baseline generated probes. That is a demonstrated shortcut, not a guess about model behavior.

Every other generated input now adds a smaller 3×3 zero-interior frame in a fresh color. Its eight cells make it rarer than the true source's 14 or 18 border cells. The decoy is disjoint from source and target. Candidate positions are enumerated and shuffled using a keyed RNG, checked against the original count bounds and full semantic validator, and either yield a lawful scene or fail explicitly. No silent fallback drops a requested decoy. The ordinary four-color branch remains the strict canonical profile; the five-color extension is lawful but is not counted as an exact canonical palette-size match.

The concrete seed 817/index 1 witness was checked through the selected Racket authority, and its actual output differs from the rarity rival on 22 cells. Exact inputs, outputs, settings and hashes are retained in `counterexamples/rare_color_shortcut.json` and source-bound semantic check reports. Earlier witness revisions remain intermediate evidence if their generator hash has been superseded.

The first after-battery exposed two additional issues. Invalid scalar requests were accepted: Boolean/floating/string seeds and Boolean/negative indices. The repair follows the public call contract: signed integer seeds are allowed; indices must be nonnegative integers; Booleans are not integers for this API. Separately, three searched numeric-color rivals survived three demonstrations under a query rotation. The exact failed lessons are retained in `checks/semantic/numeric_color_rotation_failures.json`.

The teaching schedule therefore combines the two-step anchor/decoy branch with a separate three-step low/interior/high source-color rank cycle. A full palette bijection preserves geometry and color roles. The combined declared period is six. Every four consecutive examples have enough non-low and non-high sources that holding out any one pair leaves demonstrations refuting both numeric-extreme conditional rivals. This avoids fixing the source to one numeric rank or coupling rank directly to whether a decoy exists.

Three demonstrations and one query are the evaluated lesson format. The random census uses 100 lessons per difficulty band, and required query rotations hold out each of the four saved pairs. A separate fixed-seed census enumerates all declared start residues in every band. Counts and final-source hashes are in the final review and RESULTS ledger. Overlapping windows are not counted as distinct inputs; unique-input counts are reported separately.

## Parametric extension: first, last, or all targets

`workspace/parametric/target_policy.py` implements one episode-level parameter: `target_policy ∈ {first, last, all}`. The default materialized program is exactly the active canonical program. `last` changes target selection; `all` paints every eligible target. Every pair in an episode uses the same fixed policy and obtains its label by executing that instantiated Racket program.

The constructive sampler supplies multiple eligible targets, a unique larger source, and a smaller rare-color decoy. Three demonstrations have two targets; the held-out example has four, so it also tests a target-count change. The default bundle varies dimensions across 18×21, 21×18, 21×21 and 30×30. Legal explicit sizes are checked for geometric fit instead of silently coerced. These are proposed examples outside the canonical generator's narrow acceptance domain.

The public challenge contains only demonstration inputs/outputs and query inputs. Parameters, reference programs, query labels and rival verdicts stay in the private authoring manifest. Independent review found that fixed numbered filenames originally encoded the policy. The writer now shuffles the episode-to-filename mapping using an independent seeded stream. A 32-seed regression checks that every numbered filename takes all three policies and that shuffling does not alter the episodes.

Changing source-selection semantics, adding several unrelated parameters, or declaring all three policies approved were rejected. The proposed parameter preserves frame detection, dimension matching, and border transfer. Finite teaching checks distinguish the declared policy alternatives; they do not establish unique induction against every possible program.

## Reusable tools and verification

The source-bound performance probe retains exact programs, inputs, outputs, timings and runtime identities. Its tests use independently constructed expected outputs; they contain no brittle timing threshold.

`workspace/tools/verify_parametric_bundle.py` independently checks source/program/grid hashes and exact public projections. Optional execution evaluates every declared setting on every saved pair, verifies selected labels, and recomputes ordinary-query and rotation ambiguity. It does not trust the author's rival verdicts. Mutation tests cover stale hashes, wrong parameters, hidden query answers, malformed metadata, duplicate JSON keys, altered rule files, and Python's Boolean/float equality trap. A real Racket integration test checks the runtime path.

The verifier deliberately supports self-contained `rule!` lambdas through the existing bridge and public wrapper parser. Full DSL shorthand is outside its declared contract because the direct-library wrapper currently imports a missing `scripts.comment_solutions` package. No shared runtime file was changed to work around the allowed patch boundary; the concrete shared-tool request is in F1.

## Limits and stopping criteria

The production generator remains a calibrated family: fixed 21×21 size, four source dimensions, dense two-color noise, one target, and source colors confined to their borders. Count/shape heuristics beyond the declared rivals can still exist. The prototype addresses multiple-target selection separately. Neither a passing battery nor this review grants training admission or variant approval.

Successful final checks must bind the final generator/rule bytes. Failed and intermediate runs stay in the return. The post-repair solve is prepared from those final bytes, with honest exposure metadata and hidden-query accuracy left unknown. Exact patch replay is followed by focused tests in the fresh checkout's own environment; extraction alone is not claimed as test execution.
