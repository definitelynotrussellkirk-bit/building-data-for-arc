# Working notes: 44e865b6a43e

## Review-0367f02076a54545: current source 2.1.0

The canonical operation and rule pin `de38c98a1856` are unchanged: rotate the
color sequence right one and the height sequence left one, preserving bar
columns and canvas dimensions. The selected base target text was aligned to
canonical whitespace only; its archival raw source was preserved.

The unresolved historical lead `review-7d48ecdd64859355:v0001` is substantiated:
version 2.0.0 used endpoint/minimum-only repeated heights and only a cyclic family
of distinct mixed orders. Version 2.1.0 reverses those restrictions. General
repeat draws support arbitrary nonconstant repeated-height arrangements; mixed
draws support every distinct nonmonotone permutation. The historical evidence
index is retained unchanged for maintainer resolution.

Default lesson assembly uses three demonstrations and one query. A period-four
schedule alternates two rectangular crossed-repeat witnesses with a canonical
square anchor and a varied draw. Any one held-out pair leaves a witness among
the demonstrations. Explicit overrides take precedence and may remove this
guarantee; the semantic hook scores the actual lesson.

`nearest_equal_height_association` and `square_canvas` both fit every labeled
canonical pair. Eight wrong signed rotations complete the finite ten-rival
teaching test; they are not claimed to fit canonical examples. The nonadjacent
repeat heights `[1,2,1,3]` distinguish the nearest-association rival, and a 7×9
canvas also distinguishes the square assumption. Exact live-Racket outputs and
the ordinary generated witness at seed 73000/index 5/easy are in `counterexamples/`.

The retained review reports cover 300 lessons and 1,200 held-out rotations with
no ambiguity against these ten rivals, plus every declared schedule start at
seed 0. These are finite checks, not universal identifiability or approval.
Strict integer request validation, observable override metadata, and portable
task tests are included.

`workspace/probe_rotation_rivals.py` is a reusable Racket-backed rival and
distribution probe. `workspace/parametric/prototype.py` separately proposes
color/height shifts in `{-1,0,1}` sampled once per episode, with canonical default
`(+1,-1)`. Its public filenames depend only on input grids; hidden settings and
labels remain in authoring evidence. The prototype is not a canonical rule edit
or a training-admission decision. See its README and the return's DECISIONS.md.

Imported associated notes retain their original evidence and timestamps in
`evidence/associated_notes.jsonl`; no historical finding was silently closed.

## Current owner source and evidence limits

Accept intentional2.0.0->2.1.0 support/curriculum repair: arbitrary nonconstant repeat multiplicities/positions/ranks and all nonmonotone distinct orders,with rectangular crossed-repeat witnesses. Literal integer seeds preserve sign;nonnegative indices and valid difficulties enforced. Canonical rule unchanged;one selected target_code whitespace normalization statically verified. Reviewer reports12/12 battery,64 tests+17 subtests repeated fresh344/96910-file dependency closure,300 lessons/1200 rotations/1200 unique inputs clean against10 rivals;seed0 covers12 lessons/48 rotations/21 unique inputs. Fresh retry passes;first lost test session exit remains unknown. Nine color/height-shift settings have9 episodes/72 eliminations/341 Racket evaluations and9 distinct witness outputs. Default lambda uses modular indexing and differs from exact canonical text:raw canonical f0df22d0/prototype f6ef7764;only four reported canonical parity cases,not exact-source equivalence or variant approval. Final matrix-v4 fixes earlier hidden-setting filename leak with input-only identifiers;old numbered exports superseded. Explicit overrides may remove default witnesses. Closure is not fully hermetic:NumPy/Pillow from host installation. No production variants or training admission. Owner checks source hashes and public/private projection statically;reported labels/tests are not owner reruns.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7d48ecdd64859355:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0a61a0c780bc44a0e01741ab8c133f6d0fb43af7b5d3eea5ef67a9c142988a3f`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolve exact repeated-minimum/endpoints support defect on accepted81e85f5e/version2.1.0. General repeat branch samples multiplicities/ranks and shuffles positions;crossed-repeat witnesses independently sample duplicate rank with interior nonendpoint second position. Retained distribution regressions,counterexamples and64 tests+17 subtests reported green,with300 lessons/1200 rotations clean. Canonical authority unchanged;finite evidence,no owner rerun.

### Assessment or prior finding

## 44e865b6a43e

**Finding: the only repeated-height profile leaks both duplicate position and
rank.** `_height_sequence(..., pattern="repeat")` starts from sorted distinct
heights and returns `[h0, h1, ..., h(n-2), h0]`. Therefore the duplicate is
always the minimum height and always occupies the first and last bars.

Reproducer:

```text
generate(seed=0, sample_index=0, difficulty="medium",
         grid_h=10, n_bars=4, height_pattern="repeat")
bar heights -> [1, 2, 3, 1]
```

The same invariant held for the other checked seeds. It does not cover canonical
repeat structure: one canonical training input has heights `[2, 3, 8, 3]`
(duplicate at positions 1 and 3), and the canonical test has
`[10, 1, 4, 4, 5]` (an interior adjacent duplicate that is not the minimum).
A learner can therefore treat “repeat” as a wrap-boundary/minimum special case
instead of learning that color and height attributes rotate independently for
arbitrary equal heights.

A future fix should choose the duplicated rank and two positions independently,
then retain at least two distinct heights. A cheap regression is to require
repeat samples across a census to cover an interior duplicate, a non-minimum
duplicate, and a non-endpoint pair. I did not modify this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `81e85f5ea98487f80ee96ad6c2ea66501a55ad9ffeb0dca16ea4066646c25545`.

# Decisions — 44e865b6a43e

Assignment `review-0367f02076a54545` concerns original ARC family `training:2601afb7`. The selected repair is version `2.1.0`, generator SHA-256 `81e85f5ea98487f80ee96ad6c2ea66501a55ad9ffeb0dca16ea4066646c25545`. The separate rule-parameter extension is a **proposed task-local prototype**. Neither this report nor a passing check changes approval or training admission.

## 1. Preserve the canonical transformation and make authority formatting exact

The intended transformation remains independent cyclic movement of two attributes: colors shift one bar right and heights shift one bar left, with the canvas and bar columns fixed. Changing this rule to make the old restricted sampler look adequate was rejected. The defect was missing input/lesson support, not an incorrect canonical transformation.

The canonical ledger is byte-for-byte unchanged at SHA-256 `a1af567baabfe06f90d62dac826fa51e4d50bf322e6712cbaf6bc6aabc4a757b`. The normalized rule SHA-256 remains `de38c98a18568a2fc509a998ce7bc154fb797ff615dd7ec5367ae9d3178e2443`, pinned as `RULE_HASH="de38c98a1856"`.

The selected base record had exact-text formatting drift despite normalized semantic agreement. Only `racket_target.target_code` was synchronized to the selected canonical formatting; `raw_code` was preserved and the synchronization is recorded as `semantic_change=false`. The final base-record SHA-256 is `b8656806ef5054599a4e8291a235745334114b391435075d133843577cdf617d`. This is a whitespace-only authority synchronization, not a new rule. See [applied.json](checks/authority/applied.json) and [return-scope.patch](checks/authority/return-scope.patch). Earlier evidence remains bound to its actual old base bytes rather than being relabeled as current.

## 2. Retain the scene grammar and supported sizes

The existing canonical grammar is retained: orange background 7; three to five distinct-colored, one-cell-wide, bottom-aligned bars in columns `1,3,...,2*n-1`; orange margins/separators; positive bar heights shorter than the canvas; at least two different heights. Foreground colors may include 0, which must be interpreted as a bar color rather than background. These choices preserve object roles and let the two attributes be read independently. Arbitrary gaps, widths, backgrounds, repeated colors, and empty/full-height bars would introduce different parsing questions and were not added without evidence.

The existing lower bound of three bars has a concrete rationale: with two bars, left and right one-step rotations are the same swap. All-equal heights would also hide the height movement. General production still permits nonconstant periodic patterns such as `[a,b,a,b]`; one individually ambiguous example is lawful, while the lesson's other evidence must distinguish the rule.

Canvas height remains 7..12 and width remains `2*n+1` (7, 9, or 11). The canonical examples have square sizes 7, 9, and 11. Their anchors and the existing rectangle support are retained and tested. The original upper-bound rationale beyond this canonical-scale neighborhood is not documented; we do not invent one.

Larger grids were assessed as a possible extension, not assumed invalid. The [size guidance](ARC-DESIGN.md) recommends an aggregate mixture across suitable families and explicitly does not impose a per-generator quota above 20. No source-bound large-canvas/reference/lesson evidence was developed for this family, and extra padding alone would not establish a new reasoning dependency. Consequently this repair makes no claim about canvases above 12 rows or a longest side above 20. Extending that envelope would require its own meaningful examples, override checks, reference execution, and lesson evidence. Input size variation would also not satisfy the separate request for a rule parameter.

## 3. Reverse the endpoint/minimum repeat restriction

The prior return `review-7d48ecdd64859355:v0001` was used as an audit lead. Its report was not assumed to be a measurement of newly selected bytes. The pinned baseline was independently checked: `_height_sequence(..., pattern="repeat")` returned `[h0,h1,...,h(n-2),h0]` from sorted distinct heights. The duplicate was always the minimum and always occupied the two endpoints. The nearby source comment justified preserving at least two distinct heights; it did not justify fixing the duplicated rank or positions.

That restriction excludes canonical repeats `[2,3,8,3]` and `[10,1,4,4,5]`. It also makes the nearest-association rival indistinguishable from the intended transformation throughout the old construction. The current decision reverses that restriction. On general repeated draws, choose `distinct_count` from `2..n-1`, sample that many distinct height levels, fill remaining slots by choices among those levels, and shuffle. This gives every admitted nonconstant repeat multiplicity and placement positive support when the relevant dimensions/bar count are available or overridden. It includes triples and multiple duplicated groups; it does not pretend to be uniform over all grids or multisets.

Special teaching draws deliberately use one repeated first/interior height, with its numerical rank randomized. Those restricted witnesses are a curriculum component, not the whole repeat family. The general component is essential because replacing the old endpoint-only special case with a different exclusive special case would preserve a distribution defect.

The source-bound comparison uses `seed=73000+i`, `sample_index=37*i+5`, `i=0..119`, separately in each band, with no overrides. The old source is `0a61a0c780bc44a0e01741ab8c133f6d0fb43af7b5d3eea5ef67a9c142988a3f`; versioned RNG means equal replay recipes do not imply equal grids after the repair.

| Observed property | Easy, before → after | Medium, before → after | Hard, before → after |
| --- | ---: | ---: | ---: |
| Repeated-height inputs | 29 → 71 | 29 → 71 | 29 → 71 |
| Nonminimum repeated height | 0 → 40 | 0 → 47 | 0 → 46 |
| Nonendpoint duplicate pair | 0 → 70 | 0 → 69 | 0 → 71 |
| Pair wholly inside the two endpoints | 0 → 4 | 0 → 6 | 0 → 5 |
| Nearest-association counterexample | 0 → 61 | 0 → 64 | 0 → 66 |

Each column compares 120 generated inputs. All 360 production outputs per source were executed through canonical Racket. See the [baseline](checks/rotation-analysis/baseline/summary.json) and [repaired](checks/rotation-analysis/final-v1/summary.json) probe reports. The inherited audit index was not edited: this return records the verified finding, repair, and evidence for an owner disposition, without silently changing the issued audit's administrative status.

## 4. Reverse the one-order mixed family

The old `mixed` branch was always one fixed cyclic rotation of a sorted distinct list. Its documented purpose was to ensure both a rise and a fall, which it achieved, but that did not warrant excluding all other nonmonotone permutations. Canonical distinct-height orders include `[6,3,4]` and `[4,5,3,8,6]`, which require broader order support.

The new branch chooses from all distinct-height permutations except ascending and descending. At most five bars means at most 120 candidates, so bounded enumeration is simple and avoids an unbounded rejection loop. Ascending/descending remain separate observable families. The focused regression reaches every one of the four mixed rank permutations for three bars and every one of the 22 for four bars. See [test_distribution_regressions.py](repo/generators/44e865b6a43e/tests/test_distribution_regressions.py). Full support is a property of the construction; the finite census is coverage evidence rather than an enumeration of every possible numeric height vector.

## 5. Use a deliberate teaching schedule with general draws

Pure independent random draws can leave a canonical-fitting rival unchallenged in demonstrations even when the overall population sometimes refutes it. Sampling only witnesses would cover too little of the legitimate input family. The selected compromise has declared schedule period four:

| Requested sample index modulo 4 | Default role |
| --- | --- |
| 0 | General height family with a square canonical-scale canvas |
| 1 | Rectangular crossed-repeat teaching witness |
| 2 | General height family with ordinary difficulty-biased dimensions |
| 3 | Rectangular crossed-repeat teaching witness |

Odd slots use four bars in easy/medium and four or five in hard. The witness has its sole duplicate at source positions `(0,j)`, `2 <= j <= n-2`, with other heights distinct. Its duplicated numeric rank is random. Matching those duplicates under the intended rotation costs `n` horizontal steps; the wrong crossed match costs `n-2`. Distinct colors guarantee different output predictions. A rectangle simultaneously refutes rebuilding every output as a square.

This is explicitly nonuniform sampling. General draws retain all height families and the existing difficulty biases; there is no claim that each band emits every dimension/bar-count combination uniformly. Exact caller overrides take precedence. For example, a three-bar or all-ascending override can remove the intended crossed-repeat witness. Such requests remain useful lawful controls, but they do not inherit a blanket curriculum guarantee. `lesson_identifiable` evaluates the actual labeled lesson against the declared rivals rather than trusting its requested index or profile name.

## 6. Keep three demonstrations for robust single-query holdouts

`EXAMPLES_NEEDED=3` already existed, but the old module had no executable lesson contract establishing why that number was adequate. The current justification is operational: any four consecutive, unskipped default indices contain two crossed-repeat rectangles. Removing one pair as the query leaves at least one witness among the other three. Its colors/heights also refute every wrong signed attribute shift in the declared competitor set.

One carefully selected rectangular crossed-repeat demonstration can refute all ten declared competitors. Therefore three is not an intrinsic lower bound for the ARC transformation. The local seed-73000 windows instead establish a schedule distinction: one-demo rotations were ambiguous in 19/42 cases, two-demo rotations in 4/54, and three-demo rotations in 0/60. The exact two-demo failure is easy-band demonstrations at indices `[0,2]` with index `1` held out. See [lesson_windows.json](checks/rotation-analysis/final-v1/lesson_windows.json).

Materializer rejections can advance accepted indices, and caller overrides can break the default schedule. The structural argument concerns consecutive default draws; actual materialized lessons are separately checked. The [100-per-band public census](checks/lesson-census.summary.json) completed 300 lessons, 1,200 labeled pairs, and 1,200 single-pair query rotations, with 1,200 unique inputs. It found zero production ambiguities, rotation ambiguities, materialization/scoring errors, or hook warnings.

The [schedule census](checks/schedule-census.summary.json) separately enumerated all four requested starts in each of the three bands at seed 0: 12 lessons and 48 rotations, `complete_fixed_seed`, with no measured ambiguity or errors. Its 21 unique inputs reflect overlapping windows. The report's diagnostic residue modulus 6 must not be confused with the declared schedule period 4. Neither census exhausts all random seeds, arbitrary rejection histories, overrides, or undeclared hypotheses.

## 7. Declare and verify real competitors

The strongest checked structural rival is `nearest_equal_height_association`. It fits all four labeled canonical pairs and the old construction, but fails on the accepted square input with colors `[1,2,3,4]` and heights `[1,2,1,3]`. Canonical Racket predicts colors `[4,1,2,3]`; the rival predicts `[4,3,2,1]`; both predict heights `[2,1,3,1]`. Exact 9×9 input and output arrays, dimensions, proof, and native execution receipts are in [QUESTION_ANSWER.md](QUESTION_ANSWER.md).

The second canonical-fitting rival assumes square output geometry because all four canonical inputs are square. Eight wrong signed combinations of left/fixed/right color and height movement complete the ten unique lesson competitors. The two canonical-fitting rivals are also declared in the semantic and canonical-shortcut namespaces, producing fourteen bindings but only ten unique rivals. Witness mappings connect the crossed-repeat and rectangular predicates to actual rival disagreements.

Global color substitution was considered and rejected as a canonical-fitting hypothesis: color 8 would need to map to 9, 2, and 4 across the demonstrations. No whole-grid memorizer, arbitrary numeric threshold, or unsupported canonical-fitting claim was added merely to enlarge the inventory. Finite rival elimination does not establish uniqueness against every possible rule or what a model will learn.

## 8. Preserve controls and strengthen scalar request validation

The advertised exact axes remain `grid_h`, `n_bars`, and `height_pattern`. Their lawful ranges and pattern meanings are retained, while their descriptions now disclose anchors and witness scheduling. The old default-mixture frequency expectation is no longer a suitable oracle for a deliberately nonuniform teaching distribution; focused regressions test broad general support and the new lesson guarantees instead.

The request validator now requires literal integer `seed` and `sample_index` values and a nonnegative sample index. This addresses the observed invalid-scalar acceptance rather than silently coercing floats, strings, or booleans. Unknown overrides and invalid difficulty/axis values remain errors. RNG is still local and keyed, and replay is version-bound. The final [staged task-test receipt](checks/task-tests-final/result.json) completed with exit 0: 64 tests plus 17 passed subtests, represented as 81 passing JUnit results, with no failures, errors, or skips.

## 9. Propose two episode-fixed rule parameters in a separate prototype

The family's two attributes support small meaningful parameters without replacing its object roles:

| Parameter | Values | Canonical value | Meaning |
| --- | --- | --- | --- |
| `color_shift` | `-1,0,1` | `1` | Left, unchanged, or right cyclic color movement |
| `height_shift` | `-1,0,1` | `-1` | Left, unchanged, or right cyclic height movement |

These values change executed Racket behavior; they are not cosmetic input controls. Both are chosen once per episode, then fixed across its three demonstrations and query. The canonical setting is preserved. The `(0,0)` identity setting is intentional. All variants use the same scene constraints, so dimensions and other input constraints do not directly encode the selected parameters.

The prototype keeps the original sequence of reasoning: find and order bars, infer the two attribute movements independently, and recombine them in fixed columns. It excludes height patterns invariant under one- or two-place rotations so that its parameter demonstrations distinguish left/fixed/right movement. This is a prototype-specific teaching restriction, not a new restriction on the selected canonical generator, which continues to allow lawful general repeats.

Prototype SHA-256 `9869a1298f8686ad581df0f133dff702f8e77c59d15e4ef172d0214f76bec325` is bound by the final [matrix-v4 evidence](checks/parametric/matrix-v4/private/summary.json). That run records nine episodes covering all nine settings, 72 alternative-setting refutations, four canonical agreements, nine distinct outputs on a shared lawful witness, and 341 live Racket evaluations. Exact materialized programs, parameter values, seeds, output evidence, and runtime hashes accompany that authoring report. The [prototype README](repo/generators/44e865b6a43e/workspace/parametric/README.md) gives runnable commands and the separation contract.

An earlier public-filename policy revealed setting information through matrix ordering. Those earlier matrices are retained as superseded evidence rather than treated as current successes. The final writer derives each of its nine public filenames solely from the ordered input grids, excluding hidden parameters, labels, seeds, and emission positions. Public challenge content contains labeled demonstrations and unlabeled query inputs only. Exact rules, parameters, and query labels remain separate authoring evidence. The final staged tests include the end-to-end writer regression for this boundary.

The result remains **proposed prototype, bounded pass**. It adds no production parametric API, changes no catalog kind or approval hash, and does not admit its nine variants to training. Nine retained settings/episodes are not all-seed or arbitrary-rival coverage.

## 10. Composition assessment and remaining limits

Following [ARC-DESIGN.md](ARC-DESIGN.md), this is a modest combination family: two independently inferred rotations act on coupled attributes of the same bars and recombine in a shared output. The whole-bar movement competitors demonstrate why keeping color and height attached is wrong. The two movements are computed from the original input; there is no demonstrated iterative-state dependency, and no extra sequential step or cue-gated mechanism was invented to claim a richer category. This repair and prototype provide no evidence of general reasoning mastery or corpus-wide composition coverage.

Current conclusions are bounded by the documented 7..12-row, 3..5-bar grammar, ten declared production rivals, retained seeds/accepted indices, and nine prototype settings. Exact labels were checked through Racket; those correctness checks are distinct from teaching evidence. The final battery/packaging status and complete command ledger belong in [REVIEW.md](REVIEW.md) and [RESULTS.json](RESULTS.json). The two other assigned generator audits are findings-only and do not alter the selected repair's scope.
