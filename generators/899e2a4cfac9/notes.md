# Working notes: 899e2a4cfac9

## Current decision: version 2.1.0

The unchanged authoritative Racket rule removes every **same-color, four-connected, nonzero component** with at least one cell on the top, bottom, left, or right grid edge. Every fully interior component survives at its original coordinates and color. Background is fixed at zero; the output starts as an all-zero grid. Adjacent different colors remain different components, and diagonal-only contact does not merge components. The selected canonical rule hash is `50ed982b7d21`; executable rule-text SHA256 is `e3be5a37984b21bbb87a5d1347a612058e29f5c34c30306dbe716914a789fcc3`.

The frozen generator SHA256 is `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`. The generator constructs inputs; the Racket runtime supplies labels. No local output implementation is used to accept generated draws.

### Axes and input domain

| Exact axis | Supported values | Meaning |
|---|---|---|
| `grid_h` | 6..12 | Returned row count |
| `grid_w` | 7..14 | Returned column count |
| `n_blobs` | 3..7 | Number of same-color four-connected foreground components |
| `n_distinct_colors` | 3..6 | Total distinct pixel colors, **including zero** |

Foreground colors are sampled from 1..9; zero never moves during palette variation. Three total colors means two foreground colors. All four axes are recovered from the returned pixels by `observe_overrides`. Unknown axes, booleans/noninteger/out-of-range values, and negative/noninteger sample indices are rejected. The former `palette_kind`, `texture`, `palette_size`, `density`, and `position_bias` controls are not supported.

Component color roles impose these explicit incompatibilities: `n_blobs=3` or `4` cannot use total palette size 5 or 6; `n_blobs=5` cannot use total palette size 6. Three-component draws allow up to four total colors; larger draws repeat a foreground color and allow at most `min(6, n_blobs)` total colors. An even draw with a standalone request for five or six colors switches to the rich construction rather than silently reducing the requested count.

The generation ranges are narrower than the validator's lawful domain. `self_check` and `strict_canonical_like` accept rectangular integer-color grids with 3..30 rows and columns, some zero background, at least one border component, and at least one interior component. They do not demand seven components, three survivors, a particular shape, or a most-frequent zero background. This retains all canonical inputs, which each have three components and one survivor. The strict hook is a broad mixed-outcome semantic domain, not a claim of exact official morphology or exclusive stochastic support; `MIN_STRICT_FRAC=1.0` refers to that declared domain.

### Default period-two curriculum

`LESSON_SCHEDULE_PERIOD=2`; profiles are `canonical_support` at even indices and `rich_witnesses` at odd indices. The schedule's phase is independent of seed and difficulty. Dimensions are biased toward canonical anchors 7x8, 8x9, and 9x10 while retaining the full declared ranges; height and width draws can recombine anchor marginals. Exact linked canonical size pairs are therefore favored, not universally imposed.

Even default draws contain three separated components: two border dominoes and one interior L, square, or T. They use three foreground colors, four colors including zero. Shapes, anchors, transposition, row/column reflection, and palettes vary.

Odd default draws contain seven components: four border objects establishing isolated contacts with all four edges, and **three interior survivors consisting of a mandatory singleton plus two larger components**. A border/interior pair has equal size and repeated color but only diagonal contact; another border/interior pair has different colors in orthogonal contact. This breaks size-only filtering, global border-color deletion, same-color eight-connectivity, and all-nonzero four-connectivity. Border tails distinguish removing entire objects from removing only perimeter cells. The singleton and larger survivors distinguish dropping isolated interior cells and keeping only the largest interior components. Rich shapes grow independently while preserving their edge sets and preventing same-color peer absorption. Easy growth is capped at three cells, hard at five, and medium/default at four, apart from the guaranteed one-cell survivor.

Three consecutive default demonstrations include a rich example. Four consecutive default draws contain two rich examples, so each three-demonstration query rotation retains one. This is a curriculum argument for this consecutive-index pattern, not proof over arbitrary demonstration selections, rejection schedules, or overrides. The materialized lessons and named rivals are checked explicitly.

Exact overrides may replace the default curriculum. In particular `n_blobs=3` selects the simple construction, 4..6 select partial rich constructions, and only seven-object rich draws guarantee all four edges and the singleton. A small component-count or palette request can require different demonstrations. Such grids remain lawful; the override contract does not promise universal lesson identification. Density, shape, foreground color IDs, edge, and texture are not separate override axes.

### Twelve declared rivals and witness contracts

`SEMANTIC_RIVALS` and `LESSON_COMPETITORS` contain:

1. `erase_domino`: erase two-cell objects regardless of border contact.
2. `keep_largest`: keep only maximum-size objects globally.
3. `border_colors_global`: delete a color everywhere if it occurs on the border.
4. `same_color_8`: merge same-color diagonal neighbors.
5. `nonzero_4`: merge orthogonal foreground neighbors regardless of color.
6. `border_cells_only`: erase perimeter cells while retaining an object's interior tail.
7. `drop_interior_singletons`: apply border filtering, then discard one-cell survivors.
8. `largest_interior_only`: apply border filtering, then retain only maximum-size survivors.
9. `omit_top`: ignore top contact in the border test.
10. `omit_bottom`: ignore bottom contact.
11. `omit_left`: ignore left contact.
12. `omit_right`: ignore right contact.

Witnesses bind equal-size opposite roles, repeated-color opposite roles, same-color diagonal bridges, different-color orthogonal bridges, border tails, small/large interior survivors, and isolated contact with each individual edge to their precise rivals. Eight plausible rivals fit all three labeled canonical pairs: size deletion, global largest, global border-color deletion, same-color eight-connectivity, all-nonzero four-connectivity, omission of left contact, interior singleton deletion, and largest-interior-only. All-nonzero eight-connectivity already fails canonical train 0, where retained color 3 diagonally touches removed color 4; it is not needed as a surviving canonical shortcut.

`lesson_identifiable` compares actual labeled demonstrations and query against these finite rivals. It reports any rival fitting every demonstration but changing the query answer. It does not prove identification against every possible hypothesis.

## Retained diagnosis and reversals

The imported version 1.2.0 source (`3f5dc2b5704c96aaf9ac3bb33dc6e8c75c1772692fcb431b63a397f139edcf0e`) always used border dominoes and interior three-cell L shapes, with four distinct foreground colors. Erasing all dominoes and keeping all largest objects fit every canonical label and all 480 ordinary diagnosis draws. Its `_components` merged all nonzero orthogonal neighbors, which contradicted the reference's same-color segmentation but was hidden by separated layouts. Its advertised variation did not uncouple geometry from border role. Initial exact counterexamples are retained in `counterexamples/border-filtering-rivals/` with Racket outputs and source provenance. A final-source emitted witness is retained separately in `counterexamples/generated-rich-witness/`: `generate(seed=3298638998, sample_index=93, difficulty="easy")`, no overrides, returns a 6x7 grid with seven components and five total colors. Exact regeneration matched the final census input, and public Racket application matched its label. All twelve actual declared competitors disagree on this single input. This establishes positive emission of rich rival-refuting semantics; it does not establish emission of every historical handmade grid.

An intermediate candidate (`a6817c68d30e5a07ce38d7b2988258568b72cf4f865dcb77bbf28c66392cc364`) added size/color/connectivity witnesses but did not guarantee the smallest interior survivor. `WORK/checks/code-review/additional-rivals.json` records two further canonical-fitting hypotheses: dropping internal singletons and retaining only largest internal components. These found ambiguous production lessons and query rotations in that intermediate candidate. They were added as declared competitors, and seven-object rich draws now preserve one singleton beside two larger survivors. Those old failures are source-bound historical findings, not final failures. `WORK/checks/code-review/final_controls.json` binds the final source and reports 24 formerly failing seed rotations now refuted, plus exact component/palette controls and invalid-index rejection.

Imported associated history remains in `evidence/associated_notes.jsonl`. Source snapshots and older receipts remain provenance, not proof for the current bytes.

## Final evidence and limits

Evidence paths below are relative to the enclosing review packet's `WORK` directory; from this task home they are under `../../../checks/`.

| Evidence | Final result and scope |
|---|---|
| `checks/after-final/checks/899e2a4cfac9_after_battery_summary.json` | Final source pinned; all 12 stages green, zero failures/advisories |
| `checks/task-tests-final/result.json` | 19 task tests passed through the copied runtime |
| `checks/after-final/checks/899e2a4cfac9_after_semantic_gate.json` | 600/600 strict hits across easy/medium/hard; both profiles exercised; finite witness/rival checks passed |
| `checks/lesson-census-final.json` | Final source; 300 lessons, 1,200 unique inputs and 1,200 query rotations; no declared-rival ambiguity, hook warnings, scoring errors, or materialization errors |
| `checks/schedule-census-final.json` | Explicit period-two enumeration at seed 0 over three bands: six lessons and 24 rotations; no ambiguity; nine unique inputs |
| `checks/code-review/final_controls.json` | Final source; 2,784 exact three-object draws, 5,568 exact seven-object draws, 256 standalone high-palette controls, 256 default controls; no failures |
| `checks/regression-final-v2.log` | Additional focused regression run: 19 passed |
| `checks/generated-witness/witness.json` and `racket.json` | Exact final-source easy draw at seed 3298638998/index 93; public reference output; all twelve competitors refuted |

The main lesson census warns that the short schedule was not explicitly enumerated in that run; the separate schedule census supplies fixed-seed residue coverage. Fixed-seed enumeration does not exhaust random support, rejected-pair schedules, or all cyclic windows. Generic searched label-mutation candidates are reported separately from the declared-rival verdict. The full battery used diagnostic rotations rather than the strict required-rotation admission setting; the two final lesson censuses explicitly used required rotation checking. These finite successes are source-bound evidence, not universal identifiability, approval, or training-data admission. Current approval remains a catalog decision tied to exact source and rule bytes.
## Current reviewer considerations

Source SHA-256: `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`.

# Decisions for 899e2a4cfac9

Assignment: `review-57e51df327ebb479`. Final implementation: v2.1.0, SHA256 `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`. The selected canonical Racket rule remains `50ed982b7d21`. Finding IDs match `REVIEW.md`; exact commands and hashes are in `RESULTS.json` and the cited evidence.

## D1 — Keep the authoritative operation, repair the distribution (R1, R2)

**Prior choice:** border dominoes and interior Ls were simple, easy to place, and safe from accidental joins; the original author's deeper rationale is unknown. The source tied removal to size two and survival to size three, so a learner could ignore the border. An independent baseline probe measured that shortcut on 480/480 ordinary draws, and the original validator rejected all three canonical inputs because they contain only one interior object.

**Decision:** preserve Racket's exact rule: four-neighbor, same-color components, fixed zero background, remove whole components touching any edge. Broaden ordinary inputs so location changes the outcome independently of object size, color, and connectivity. Correct `_components` before allowing differently colored objects to touch. Neither a rule rewrite nor a task merger is needed.

**Rejected alternative:** changing the authority to delete dominoes would redefine the task to match an accidental sampler correlation. Increasing only palette/size randomization would leave the correlation intact. Merely weakening self-check would admit inputs without generating the missing evidence. Four Racket-verified initial distinctions and a final directly emitted witness are retained in the task's `counterexamples/` and `checks/generated-witness/`.

## D2 — Separate a lawful validator domain from the emitted support (R2)

The validator accepts nonempty rectangular list/tuple grids, integer colors 0..9 excluding booleans, dimensions 3..30, a present zero background, at least one border component and at least one wholly interior component. Components are defined by same color and four neighbors. It neither requires two survivors nor merges adjacent colors. The new malformed-input regressions test the boundary of this contract.

`strict_canonical_like` deliberately uses the same semantic domain, with `MIN_STRICT_FRAC = 1.0`; it is not a claim that every accepted grid has a canonical size or shape. The independent shared profile-floor check supplies the concrete canonical support measurement: 11/20, 12/20 and 14/20 exact shape/palette hits, all three bands, with 3/3 canonical inputs accepted. `notes.md` explicitly distinguishes these meanings.

Emitted dimensions are a smaller range, 6..12 by 7..14, chosen to fit distinguishable components at the minimum size without relying on rejection. A weighted canonical dimension/palette branch supplies familiar 7×8, 8×9 and 9×10 examples. Dense grids, nonmodal-zero backgrounds, arbitrary component counts and every possible placement are outside ordinary support even when accepted by the broader validator. No universal-domain sampling claim is made.

## D3 — Make every advertised exact control honest (R3)

| Axis | Current meaning and domain | Why |
|---|---|---|
| `grid_h` | Exact height, integer 6..12 | Minimum geometry supports the rich distinctions; canonical heights retained. |
| `grid_w` | Exact width, integer 7..14 | Independently observable; transformations respect requested final dimensions. |
| `n_blobs` | Exact same-color four-connected component count, integer 3..7 | Three restores canonical support; seven permits all mandatory teaching objects. |
| `n_distinct_colors` | Exact total grid colors **including zero**, integer 3..6 | Matches profile counting and allows repeated-color opposite roles. |

Every numeric axis rejects booleans, strings, fractional values and out-of-range values. Unknown keys are rejected. `sample_index` must be a nonnegative integer excluding booleans; string seeds remain supported by the shared deterministic context. The former `palette_kind`, `palette_size`, `texture`, `density` and `position_bias` knobs were removed because their advertised behavior was ignored, contradictory or unobservable. This is a documented API change rather than a silent fallback.

Joint incompatibilities are explicit: `(n_blobs=3, colors=5 or 6)`, `(n_blobs=4, colors=5 or 6)`, and `(n_blobs=5, colors=6)`. The three-component branch can use four total colors; rich constructions reserve repeated-color roles, hence fewer independent color slots. A standalone request for five or six colors at an even index chooses a compatible seven-component scene. It does not silently alter an explicitly requested component count.

The final public override gate ran its 238-case plan with 30 seeds per case across three bands: 21,420 calls, 20,970 accepted, 450 declared incompatibility rejections, zero findings/warnings. Independent final controls enumerate all advertised height/width combinations for exact three- and seven-component requests, every compatible palette, four difficulty settings, and repeated minimum-size draws. Controls for intermediate counts also remain in the task tests and public override matrix. The initial independent 18,096-grid control probe belongs to intermediate v2.0.0 and is not reused as final-source evidence.

## D4 — Retain exact canonical-support draws alongside rich teaching draws (R2, R4)

**Default even sample indices:** three separated components, two border dominoes and one wholly interior L, square or T with three/four cells. With no palette override, use four total colors. These draws recover ordinary one-survivor and canonical-palette support.

**Default odd sample indices:** seven components, four border objects that individually demonstrate each edge and three wholly interior objects. One interior singleton is frozen; the other two have at least two cells. Anchors create a same-color diagonal-only border/interior contact and a different-color orthogonal border/interior contact. Repeated colors occur in opposite survival roles. Object growth preserves the original border-contact set and cannot absorb a same-color peer.

Random keyed palettes select foreground colors from 1..9 while fixing zero. Random anchors, polyomino growth and all eight dihedral orientations vary shape and position while preserving the relationship being taught. Size growth remains bounded so foreground does not dominate the background. This is a deliberately constrained teaching distribution, not a claim that a fixed scaffolding is the whole task domain.

**Rejected alternative:** seven-component-only output restored semantic distinctions but still omitted the canonical one-survivor regime. A purely random mixture could leave an entire three-demo lesson without the crucial witness. The deterministic alternating mixture gives both canonical support and a small, inspectable guarantee about lesson assembly.

## D5 — Declare rivals, then test actual predictions (R1, R4)

The final declarations enumerate twelve executable alternatives: erase dominoes; keep largest objects; delete every object whose color appears on the border; use same-color eight-connectivity; merge all adjacent nonzero colors; erase perimeter cells only; drop interior singletons; keep only largest interior components; and omit each of the four edges. Eight of these fit all three usable canonical pairs and are also declared as `CANONICAL_SHORTCUTS`. The census independently verifies those fit claims; rivals already contradicted by canonical pairs remain useful semantic controls without being mislabeled as canonical shortcuts.

Witness predicates identify a relation that changes a prediction: opposite roles of equal-sized objects, repeated colors in opposite roles, diagonal and mixed-color bridges, retained small/large interiors, tails extending inward from the edge, and an object reaching each edge alone. The Racket-backed semantic gate checks the claimed disagreement. `lesson_identifiable` evaluates the actual labeled demonstration and query predictions; it does not equate the mere presence of a visual cue with identifying the rule.

**Revision after independent review:** v2.0.0 passed a 300-lesson census against its initial ten rivals, but two undeclared rules exposed real ambiguity. Dropping singletons fit 20/300 production lessons and changed their query, with 61/1,200 ambiguous rotations; retaining only largest interior components did so on 10/300 and 26/1,200. The exact intermediate windows, including seeds 531125654/start 21 and 223740448/start 11, remain in `checks/code-review/additional-rivals.json`. No counts are added because these sets can overlap.

The new choice is a mandatory unexpanded singleton plus two larger interior components in each rich scene, with both rivals added to the declarations and to independent tests. Those tests genuinely failed before the repair, and the final independent review replayed six retained windows through all four query positions, 24 successful distinctions. This is evidence for the repair; it is not evidence that all plausible hypotheses have been enumerated.

## D6 — State the lesson assembly and query policy precisely (R4)

`EXAMPLES_NEEDED = 3`. Ordinary lessons take **three demonstrations and one query from four consecutive accepted default draws**. `LESSON_SCHEDULE_PERIOD = 2`, with canonical-support and rich-witness profiles alternating. Each four-draw window contains two rich inputs. Whichever single pair is held out as query, at least one rich input remains in the demonstrations and refutes the declared alternatives. The default generator validates without recorded rejections in the final census, so these measured accepted indices do not skip the intended branch schedule.

We support holding out every pair once while retaining the other pairs' order. We do not claim arbitrary independently sampled, subsetted or overridden lesson assembly is necessarily identifiable. Explicit overrides can replace the default schedule, so callers assembling such lessons must run the actual rival/lesson guard rather than borrowing the default guarantee. This limitation is written into the generator and current notes.

Measured final policy: 100 lessons per band, starts 0..99 with the public hashed seed recipe; 300/300 materialized lessons, 1,200/1,200 unique inputs, 0 production ambiguities and 0/1,200 ambiguous rotations. The separate required-rotation semantic gate passes 12 lessons and 48 rotations. The period census enumerates starts 0 and 1 at seed 0 over all three bands, giving 6 lessons, 24 rotations and 9 distinct inputs, all passing. The census's generic reporting modulus is 6; the actual declared/enumerated schedule period is **2**, so these are not six starting residues.

## D7 — Keep canonical output authority in Racket

New tests contain an independently written flood fill and concrete expected-output cases. They verify segmentation, axes, canonical acceptance, deterministic sampling and lesson contracts. Authoritative labels still come from supported `arcpuzzles apply` and production materialization through the selected Racket rule. Python mirrors are explanatory/test comparisons, not replacement authorities. The before, intermediate and final runtime manifests retain copied file hashes.

The smallest directly emitted final witness is 6×7, seed 3298638998, sample index 93, easy, no overrides. It reproduces a census input exactly, passes the actual validator, and all twelve actual declared rival callables disagree with its retained Racket output. A separate public application command rechecks that output. In contrast, the older handmade four-component/five-color witnesses are lawful but not exactly emitted by the revised four-component constructor; this difference is explicit in their provenance.

## D8 — Make checks usable for later agents

The portable task runner correctly disables user-site packages. Here pytest was initially only in user-site, so the supported preflight failed before executing any tests. `workspace/bootstrap_test_env.py` now creates a **new** venv from the installed distribution-owned files of NumPy, Pillow, pytest and dependencies. It retains distribution versions and every copied file hash, then verifies isolated imports with `-s`. It does not borrow another source checkout, turn off isolation, install from the network, or include the resulting environment in the return.

This helper is a same-host/same-interpreter offline fallback; it requires those installed distributions to be available to its invoking Python. Normal installation of the dependencies is equally suitable. A fresh independent environment was also built in the original-packet extraction for the final replay. `checks/generated-witness/probe.py` extracts a small example from a source-matching public census, directly replays the generator and iterates the actual rival declaration instead of duplicating its names. The source patch contains durable regression tests and minimal task counterexamples; the review ZIP retains the auxiliary audit/review probes.

`checks/final-handoff/replay_return.py` also retains the exact-patch application and source-bound verification procedure. Its first run exposed a fixture-container comparison error after patching, tests and reference application had succeeded; that script and failure are preserved under `attempt-1/`. The corrected continuation rechecks all completed-stage hashes and compares the contained output grids, then performs relocated generation. It neither weakens a test nor changes the task source.

## D9 — Respect the task boundary and expose external failures

Audit targets remain findings-only and their hashes remain unchanged. The broad repository suite was run as additional evidence, not substituted for the selected task stage. Its five final failures all recur on the unpatched original extraction under this environment and invocation; exact node IDs and unchanged source hashes are retained. Their source or frozen expectations were not altered to make this delta look green. The task's required gates are green; the independent maintainer still decides any future shared fixes and training admission.

## D10 — Record solve exposure and limits honestly

The blind task was completed first by an agent given only its public visible challenge and procedure; one revision passed 3/3 visible examples, earlier exposure no. The later selected-task solve was necessarily exposed because the rule had been studied for this repair; it declares exposure yes, kept source/reference/private files closed during the episode, and passed 3/3 visible examples in one revision. Neither record claims masked-query success. Work logs describe the actual attempted implementation and stop reason, without invented failures or claims of recorded token-level traces.

## Optional curriculum annotation

`contextual_gating` is present at generated-input scope: an object's relation to the grid boundary determines whether all of its cells survive, and the emitted example retains an interior domino while deleting an equally sized border domino. The simpler size-only rival disagrees with the Racket output. This is one operation with a context condition; no additional rule, sequential state machine or task-defined symbol has been introduced merely to obtain an annotation. Other axes are recorded as not applicable or unknown, not corpus-wide absence claims.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-6210ca385d85e852:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`. At disposition, audited bytes match the current source.

### Current decision

Audited source repo/generators/899e2a4cfac9/generator.py SHA256 0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5. Bounded no_issue:19tasktests;both schedule starts atseed0 across3bands,6lessons/24rotations,zeroambiguity. Initial semantic run requested enumeration; fixed-seed declared-rival coverage is notallseeds orundeclaredhypotheses. No owner execution or peer source repair. Exact evidence: `checks/audit/.899e2a4cfac9-combined.check.lock` `checks/audit/.899e2a4cfac9-semantic-period.check.lock` `checks/audit/899e2a4cfac9-combined/checks/899e2a4cfac9_audit_battery_summary.json` `checks/audit/899e2a4cfac9-combined/checks/899e2a4cfac9_audit_commands.jsonl` `checks/audit/899e2a4cfac9-combined/checks/899e2a4cfac9_audit_semantic_gate.json` `checks/audit/899e2a4cfac9-combined/checks/899e2a4cfac9_audit_semantic_gate.log` `checks/audit/899e2a4cfac9-combined/checks/899e2a4cfac9_audit_semantic_gate.receipt` `checks/audit/899e2a4cfac9-combined/checks/899e2a4cfac9_audit_summary.json` `checks/audit/899e2a4cfac9-combined/checks/task_tests.xml` `checks/audit/899e2a4cfac9-combined/progress.log` `checks/audit/899e2a4cfac9-combined/result.json` `checks/audit/899e2a4cfac9-command.log` `checks/audit/899e2a4cfac9-semantic-period/checks/899e2a4cfac9_audit_battery_summary.json` `checks/audit/899e2a4cfac9-semantic-period/checks/899e2a4cfac9_audit_commands.jsonl` `checks/audit/899e2a4cfac9-semantic-period/checks/899e2a4cfac9_audit_semantic_gate.json` `checks/audit/899e2a4cfac9-semantic-period/checks/899e2a4cfac9_audit_semantic_gate.log` `checks/audit/899e2a4cfac9-semantic-period/checks/899e2a4cfac9_audit_semantic_gate.ok` `checks/audit/899e2a4cfac9-semantic-period/checks/899e2a4cfac9_audit_semantic_gate.receipt` `checks/audit/899e2a4cfac9-semantic-period/checks/schedule-census-input.json` `checks/audit/899e2a4cfac9-semantic-period/progress.log` `checks/audit/899e2a4cfac9-semantic-period/result.json` `checks/audit/899e2a4cfac9/schedule-period-command.log` `checks/audit/899e2a4cfac9/schedule-period-s0.json` `checks/audit/899e2a4cfac9/schedule-period-s0.summary.json` `checks/audit/899e2a4cfac9/semantic-period-command.log`

### Assessment or prior finding

## 899e2a4cfac9

**No issue found within the checked declared-rival and schedule scope.** Audited generator SHA-256: `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`.

The isolated audit ran **19/19** task tests successfully. Its first semantic pass requested explicit enumeration of the declared period rather than revealing a rule defect. I then enumerated both schedule starts at seed 0 across easy, medium, and hard and required every query rotation: **6/6 lessons, 24/24 rotations**, zero ambiguity, materialization errors, hook warnings, or scoring errors. The census is `checks/audit/899e2a4cfac9/schedule-period-s0.json`; the strict census-bound semantic gate passes in `checks/audit/899e2a4cfac9-semantic-period/`.

Scope limit: this checks the target’s declared rivals and one fixed-seed exhaustive period, not every seed or undeclared hypothesis. I found no concrete counterexample in that bounded review and made no edits.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## 2026-10-24 native parametric admission proposal: border signal rank

**Decision.** Keep the exact canonical border-filtering program as the default
`retention=all_interior` setting and add a matched-input
`retention=signal_rank` alternative. The production generator and canonical
ledger are unchanged. The default program SHA-256 is
`dfac84282481941b7861b119adf1b123406a38ec1e1b07e67ee0aecc5d91ed42`;
the alternate program SHA-256 is
`3e7a29966353114fc351d40488c76a98daca4494e5fcf471433a1e10fe1c1601`.

**Sequential dependency.** The alternative finds the unique blue border
component, counts its cells, interprets that count as a one-based rank, then
retains only the interior component at that row-major rank. The answer object
cannot be selected before the signal-derived rank exists. The protected-Racket
counterfactual replaces the measured rank with rank 1 on the same input and
produces a different final grid.

**Lesson contract.** The adapter supports 2–6 demonstrations and 1–4
independently requested, prefix-stable queries. Inputs are byte-identical across
settings. The four query profiles are 15x17, 19x21, 24x27, and a substantive
30x30 scene. The first two demonstrations use ranks 2 and 4 and reject the
declared alternative plus ten finite shortcuts: first/last, smallest/largest,
column-major, reversed row-major, size matching, fixed ranks 2/4, and deleting
only perimeter cells. The grammar also exercises all four edges, inward border
tails, repeated colors across roles, and same-color diagonal separation.

**Evidence.** Thirty-eight staged task tests pass. A reusable
`workspace/parametric/audit_lessons.py` checked 768 lessons and 5,888 labeled
pairs across 128 seeds, both settings, and demonstration counts 2, 3, and 6,
with no harmful survivor among the ten named rivals. Eight saved one-query
public projections passed exact-byte, masking, integer-grid, and identity checks.
Native protected-Racket qualification covered both settings at seeds 0 and 17,
three demonstrations and four queries: four jobs, 28 retained labels, and 40
Racket evaluations. Qualification execution SHA-256 is
`38b4a782904ee77b101399b3d32f4e5e87557893b90f8f67554dbf2ffe3ad334`;
causal witness SHA-256 is
`18bd506ec3aad4f0c097ddc15779e1de69a3ba35ec061de561a2ee4e67930daa`.

**Limit.** This is reviewer-ready, source-bound proposal evidence. It does not
approve a variant or admit training data. The owner must integrate the exact
bytes, rerun native qualification and the counterfactual witness, then perform
the fresh acceptance replay before enabling training.

