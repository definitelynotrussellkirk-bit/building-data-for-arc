# X-Shape Selector — current authoring notes

Version **2.0.0**. Reference pin **76b666ea1233**; the canonical and archival Racket authorities are unchanged. Return: `review-559c80d6820285f7`.

## Intended rule and validation domain

A target is a maximal same-color eight-connected component of color 3 whose normalized coordinates are exactly the four corners and center of a 3×3 box. Recolor every such component to 2. Preserve every other cell. A same-color attached cell invalidates the entire target; a different-color touching cell or a colored cell in a gap does not. A 5×5 X remains unchanged.

The validator accepts rectangular integer row lists up to 30×30, using a bounded motif domain: 3×3 Xs, 3×3 pluses, 5×5 Xs, a green X with one additional attached green cell, and foreign singleton cells accompanying a motif. It accepts lawful no-target identity witnesses, all three canonical inputs, and colored-gap/contact witnesses. It rejects blank grids, isolated singleton scenes, malformed grids, and unrecognized components. This is a declared sampling/validation domain, not a characterization of every input accepted by the reference program.

## Default distribution and lesson contract

The five-phase schedule is **core, mixed, core, mixed, core**. Core phases use 7×7 with one target, 7×8 with one target, and 8×8 with two targets, respectively; all include one yellow plus. Rotations/reflections randomize placement and may swap rectangular dimensions. Mixed scenes contain two or three targets, a green plus, a larger green X, wrong-color Xs below and above green numerically, and a foreign-colored cell inside a target's gap. One wrong color has more X components than green. Small motifs are randomized on separated lattice slots.

Four demonstrations plus one query are the supported lesson assembly. Every five consecutive default inputs contain two complete contrasts and two core examples with equal green/yellow foreground counts. The three core canvas families differ, and consecutive mixed examples have different observable gap colors, so those five inputs are distinct before production duplicate filtering. Holding out any one pair leaves both witness kinds in the demonstrations. The combined scene/color schedule has period 35. Explicitly shorter lessons or arbitrary override mixtures are outside this guarantee.

The executable contract contains 14 distinct rival behaviors, including 11 that fit all labeled canonical pairs. The contract is finite; it does not claim unique induction against all conceivable rules. Easy and medium share the same semantic mixture; hard increases inter-slot spacing. Difficulty never narrows exact override legality.

## Exact controls

| Control | Legal values | Visible measurement |
| --- | --- | --- |
| `n` | integers 1–3 | Number of qualifying green components |
| `padding` | integers 0–2 | Minimum empty outer border width |
| `distractor_color` | 1, 4, 5, 6, 7, 8, 9 | Core plus color or mixed target-gap color |
| `scene` | `core`, `mixed` | Presence of the larger green X |

Every joint combination is constructive. `None` preserves the no-override convention. Boolean/coerced integer values, unknown keys, and retired controls are rejected explicitly. Retired height/width/palette/texture/density/position aliases were contradictory or inactive; padding now controls outer space without promising independently infeasible geometry.

## Reversed decisions and resolved prior finding

The imported v1.1.0 supplied only green Xs and rejected canonical yellow distractors. Prior audit `review-b1e0b02aa4b00790:v0001`, source `b7a29d264025556fa6f46553b5a112fbcd1ff0f0c333fec6dbf439bd6698b255`, was used as a lead and independently reproduced. Its missing-distractor, validator, missing-pin and dead-control findings are resolved by this repair, with final-source public evidence in `checks/after-final/` and `checks/selector-contract-complete/` of this return. The immutable imported evidence index is left intact for maintainer reconciliation; a changed source hash alone is not the resolution argument.

The first rewrite alternated crowded contrasts with core scenes and failed morphology/defect checks. The 60/40 schedule restores small-scene support. A subsequent 12-rival pass still missed a real majority-color ambiguity (seed 1, start 0); its exact Racket-labeled lesson is retained under `checks/implementation-review/`. The final schedule fixes that defect and also counters X-color frequency. These failed iterations remain evidence, not final claims.

## Measured evidence and limits

Final generator SHA-256: `125e7dd4fc3ef042f24b9b628e01df239466319dd26d4778378a56f732c55a02`.

The final public battery passes all 12 stages. Portable task tests pass 91 cases; the exact-axis test loops cover all 378 scene/count/padding/color/band combinations. Strict canonical support is 355/600; the linked profile gate records 32/60 exact hits and support in every band. The 300-lesson census reports zero production ambiguities and zero ambiguities in 1,500 rotations against the declared rivals. Fixed-seed schedule enumeration covers 105 lessons and 525 rotations, also with zero ambiguities. These populations overlap and are not independent examples.

The current replay helper is `workspace/replay_selector_contract.py`. It obtains outputs through the supported public Racket apply command, verifies all linked rivals for each firing witness, checks canonical shortcut fits and generated coverage, and preserves exact inputs/receipts. The 14 hand fixtures include attachment, gap, scale, color-frequency and count-tie cases. No Python predictor supplies authoritative labels. Passing authoring checks does not grant training approval.
## Current reviewer considerations

Source SHA-256: `125e7dd4fc3ef042f24b9b628e01df239466319dd26d4778378a56f732c55a02`.

# Distribution and teaching decisions

Task `70f97d6b605b`, assignment `review-559c80d6820285f7`, version `2.0.0`.
Final generator SHA-256: `125e7dd4fc3ef042f24b9b628e01df239466319dd26d4778378a56f732c55a02`.

## Scope and authority

The original rationale is unknown: the imported notes were a placeholder. The implemented v1.1.0 sampled only green Xs, although every canonical input also has a yellow plus. Its validator rejected all three canonical inputs. The prior audit `review-b1e0b02aa4b00790:v0001` identified this gap on the same original source; it was used as a lead and independently checked through the before battery and new reference fixtures.

I kept both the selected canonical rule and the archival/base authority unchanged. The target is a maximal monochromatic eight-connected component, not an arbitrary local stencil or a color-blind foreground component. Only color 3 and exactly the normalized five-cell 3×3 X qualify. The live apply receipts pin rule `76b666ea1233`; the source program hash is `76b666ea123361cdc99eb9603dedc2fe47467590d64a9ebeb353ca34940cfbf2`, and the callable rule text hash reported by public apply is `968889a2fc2eb69cd17a4eead5905e8b2d32dd0914521c2192bb61ad3dfeb84e`. These name different serialized reference representations, not different rules.

No Python helper produces authoritative labels. The Python predictions are named wrong hypotheses and independent regression oracles. Public apply, the public battery and the production lesson sampler obtain the reference outputs through Racket.

## Why the mixture has two families

Small core scenes preserve the actual canonical canvas/palette family. Mixed scenes expose mistakes that the canonical examples cannot distinguish: selecting every green cell, accepting a plus or larger X, ignoring the fixed input color, relying on a zero-valued X bounding-box bitmap, and choosing a color by frequency.

Putting a full contrast into every sample would erase the small canonical distribution. The first 50/50 rewrite also made the object-count median too large: the public morphology gate measured 19.5 versus canonical 5.5, and defect lint independently flagged drift. That failed source and its logs are retained under `checks/after-initial/`. The final 60/40 mixture passes both gates while keeping complete contrasts in every supported lesson. This is a task-specific balance, not a proposed universal proportion.

The schedule is:

| Requested index modulo 5 | Family | Default targets | Core canvas before D4 | Teaching role |
| --- | --- | ---: | --- | --- |
| 0 | core | 1 | 7×7 | Equal green/yellow foreground counts |
| 1 | mixed | 2–3 | — | Complete shape/color/scale/frequency contrast |
| 2 | core | 1 | 7×8 | A second equal-count witness |
| 3 | mixed | 2–3 | — | A second complete contrast |
| 4 | core | 2 | 8×8 | Small multi-target canonical support |

Mixed auxiliary colors cycle through seven values by mixed-draw ordinal, with a seed-dependent phase. Two mixed phases per five positions make the full scene/color schedule repeat after 35 indices. Random placements and keyed layout draws are not claimed to repeat after 35.

## The four-demonstration contract

The supported production assembly has four demonstrations followed by one query. Query rotations hold out each of the same five labeled pairs once, preserving the remaining order.

Every five consecutive default draws contain two complete contrasts and two equal-count core witnesses. The three core canvas families are different even after swapping dimensions, and the two mixed inputs have distinct observable gap colors. Mixed canvases are larger than all three core families. Therefore the five default inputs are distinct; production duplicate filtering does not silently remove a needed witness. Every single-pair holdout leaves at least one witness of each kind in the demonstrations.

The independent tests enumerate 35 starting residues for three seeds and three difficulty bands, in addition to testing the actual public production sampler. The final public semantic smoke check materialized 12 lessons and checked 60 rotations. The wider random census materialized 300 lessons (100 per band), 1,500 labeled pair occurrences and 1,500 rotations, with 648 distinct inputs. The fixed-seed enumeration covers all 35 starts across three bands: 105 lessons, 525 pair occurrences and 525 rotations, with 51 distinct inputs. Every final production and rotation result is `no_ambiguity_found`, with zero materialization/scoring errors or hook warnings.

Those overlapping windows and reused inputs are not independent trials. The finite checks concern 14 distinct rival behaviors, represented by 39 namespace-qualified entries across the three declaration dictionaries. They do not establish unique induction over all possible programs, certify every seed through sampling, or grant training admission. Explicitly shorter lessons and arbitrary override mixtures are outside the declared lesson guarantee.

Evidence: `checks/lesson-census-final-summary.json`, `checks/schedule-census-summary.json`, their complete `.json.gz` reports, and `checks/after-final/checks/70f97d6b605b_after_semantic_gate.json`.

## The additional shortcut found during review

An intermediate repair passed all twelve public stages and a 300-lesson census against its twelve named rivals. Independent review still found a real teaching failure on source `114c20dec13a2fc74e181b3491a479d21ab6dccd123cee56ea917513268d3fde`: seed 1, start 0, easy, accepted indices `[0,1,2,3,4]`. The rival “select exact Xs in the unique most frequent foreground color; preserve on a count tie” fit all four demonstrations and changed five cells of the query answer. A direct production-runner call with live Racket reproduced it with no rejected indices. The exact episode, source snapshot, command and failed setup attempt are retained in `checks/implementation-review/`.

I fixed that defect by making two core phases equal-count witnesses. I also added a stronger canonical-fitting color-frequency rival: choose the uniquely most frequent color among exact X components. Mixed scenes now contain `n+1` wrong-color Xs in one color and one in another color, compared with only `n` green Xs. The wrong colors remain below and above 3 numerically. Thus neither color ordering nor X frequency supplies the target color.

Keeping the third core phase at two targets preserves ordinary small multi-target examples. This is preferable to changing every small core input to one target. The phase-bound canvas families make the additional count-tie guarantee safe under duplicate filtering.

## What distinguishes each rival

| Rival | Decisive generated feature |
| --- | --- |
| All green cells | Green plus and green 5×5 X remain unchanged |
| Any-color exact X | Wrong-color Xs remain unchanged |
| Any five-cell green component | Green plus remains unchanged |
| Any green component with a 3×3 bounding box | Green plus remains unchanged |
| Local green X stencil | The central stencil inside the larger connected X is not selected |
| Zero-hole local bitmap | A selected X has a nonzero foreign cell in one gap |
| Exact component requiring zero holes | The same colored-gap witness |
| Green X of any odd size | Green 5×5 X remains unchanged |
| Minimum X color | A color-1 X is not selected |
| Maximum X color | An X above color 3 is not selected |
| Most frequent X color | A wrong color has `n+1` Xs while green has `n` |
| First qualifying X only | Each default mixed scene has at least two targets |
| Every nonzero cell | Unselected colored motifs remain unchanged |
| Unique foreground-majority X color | A one-target core scene ties green and yellow at five cells each |

Eleven of these fit all three labeled canonical pairs. First-only fits two, all-nonzero fits none, and unique foreground majority fits one. Canonical-refuted hypotheses can still be teaching defects on generated lessons, as the retained intermediate counterexample shows.

The shared witness contract requires at least one linked rival disagreement per firing. The new replay helper deliberately verifies the stronger task-local statement that **every** linked rival disagrees whenever that witness fires. It also requires generated coverage for every witness and at least one generated refutation of each lesson competitor, so a core-only or missing-witness regression cannot pass vacuously.

## Constructive geometry and controls

Core scenes place their target Xs and one plus into distinct corner slots. Mixed scenes place small motifs on a four-column lattice with a reserved 2×2 slot region for the 5×5 X. The gaps prevent same-color motifs from merging under eight-connectivity. Module slots and global D4 transforms vary placement. The largest legal explicit grid is 22×22, including padding. There is no rejection-placement loop or fallback that silently changes requested controls.

All 378 joint combinations across three bands are tested: two scene choices, three target counts, three padding widths and seven auxiliary colors. Every combination is deterministic, validator-accepted and independently observable. Counts, padding, the auxiliary color and the scene are all recorded through public GenCtx draws. None of the controls uses private GenCtx bookkeeping. Explicit integer controls reject booleans, floats and strings; `None` means no override.

The old independent height/width controls were replaced by outer padding, because scene geometry determines the feasible canvas. Palette/texture aliases, singleton density and position labels, and the old palette-size/count labels were removed rather than retained as inactive promises. Unknown and retired keys now fail explicitly. The auxiliary palette excludes 0 (background), 3 (target input color) and 2 (fixed output color); using 2 for an unselected X would weaken its counterexample because recoloring it to 2 would be observationally invisible.

## Validator scope and minimal witnesses

The validator uses maximal same-color eight-components and accepts the generated motif grammar plus minimal reference-lawful probes. It handles malformed inputs with diagnostics. Foreign singleton cells are allowed alongside motifs so colored gaps/contact are lawful, but a singleton-only scene is rejected. The early rewrite accidentally allowed foreign singleton-only inputs; the public defect detector caught that and the regression now covers it.

The validator intentionally accepts no-target plus, wrong-color-X, attached-green-X and larger-X cases as identity examples. Defaults still contain at least one target. A completely blank grid, arbitrary foreign blobs and general unbounded reference inputs are outside the declared validation grammar. That limit is explicit rather than a claim about the reference's total domain.

Fourteen minimal fixtures are retained in the selected task's `counterexamples/selector_cases.json`; the final public-reference replay labels them together with all canonical pairs and 105 generated inputs. The 122-case replay passes with no disagreements or validator failures.

## Reusable tooling and evidence retention

`workspace/replay_selector_contract.py` is a standard-library command that follows portable root/canonical-data conventions, reads the current declarations dynamically and batches supported public apply calls. It preserves binary subprocess logs, exact commands, authority receipts, source/fixture/verifier identities, witness and rival results, and malformed output values on failure. It refuses existing output directories and fails when declarations or generated witness coverage are absent.

An initial version of that tool incorrectly required core scenes to refute all mixed-scene rivals. Its failed output is retained and labeled as a verifier mistake, not a generator defect. The final helper follows the separate witness contracts.

Native reports totaling more than the return's 25 MiB limit were compressed losslessly. `checks/compressed-evidence.json` records original paths, byte counts and SHA-256 values, plus compressed-file identities. `checks/restore_evidence.py` restores and verifies the exact original bytes before following raw paths inside native receipts. No failed evidence was discarded to fit the budget.

## Remaining limits

The final source has no known task-local blocker against the stated checks. Broader repository pytest is not represented as passing: its full run reports 611 passes, five failures, three missing-Torch skips and 48 passing subtests. An isolated original-source replay reproduces the three non-environment failures; the other two unchanged tests pass when their temporary destination is moved from prohibited private `/dev` to `/dev/shm`. See `checks/repository-failure-analysis/classification.json`. No unrelated source was edited.

The two separate audit targets receive findings only. Both solve episodes preserve their genuine first attempts and masked-query uncertainty. The post-repair solve is explicitly marked exposed because the rule had already been read during repair.
