# Current notes: 3977ec54e4a0 / training:896d5239

## Rule and current support

Color-3 near-connected chevrons on a noisy binary {0,1} background identify an apex, two 45-degree arms and supported depth. Fill the entire triangular wedge with 8, preserve every marker and every outside cell. All four orientations, missing arm markers and unequal arm masks remain supported. The canonical Racket authority and RULE_HASH 780d64b3096e are unchanged.

Canonical generation supports 12..22 rows and columns, 1..4 components, and depth 1..3. These are meaningful finite bounds; this return does not claim 30x30 support. Explicit controls bypass the teaching schedule. asymmetric_arms=true with max_depth=1 is incompatible.

## Current repair

Selected source SHA-256: 406ea39bd1050f238678d02ce90c50e02a8dd6e24e214d739398783ec7c5e603.
Previous selected source: 3f25acd65aab6959faf1754b7bcb2cd9a2ae5f455b58852a1032ade83e2e2d20.
VERSION remains 4.1.1 as the stable RNG salt. The source hash identifies the validation repair; valid seeds must keep their former grids.

Prior behavior silently coerced integer-axis strings/floats/bools, accepted malformed seed/index types, and fell back on unknown difficulty values. Current behavior rejects those arguments explicitly, using the existing strict integer draw helper. Seed remains a Python integer (including signed values); sample_index is a nonnegative Python integer; difficulty is None/easy/medium/hard. The boolean axis accepts actual bool or the existing None sentinel.

Evidence: counterexamples/scalar_coercion.json, tests/test_scalar_contract.py, checks/scalar-contract/{red.log,green.log,baseline-valid-draws.json}, and the before/after batteries. The regression moved from 38 failed/12 passed to 50 passed. Six fixed valid-draw hashes and seven production episode pairs remain identical. No reference-rule text or approval record was changed.

## Teaching contract and measured limitation

Use three consecutive scheduled demonstrations: orientation_01, orientation_23, canonical, cyclically. The two teaching anchors expose all orientations, depth three, exact arm asymmetry, multiple components and missing markers; the canonical slot preserves linked official profiles. Their placement predicate preserves exclusive painted support for required orientations and a depth-three outer shell. The earlier exact-mask, near-relation and overlap fixes remain active.

The current four-query production probe uses seed17, three demonstrations and four distinct queries (seven distinct inputs total), with seven canonical Racket labels. Every query is identified against all eight declared lesson competitors from the demonstrations alone.

Arbitrary query rotations are NOT part of this contract. The after battery found 12/12 identifiable ordered lessons but six ambiguous rotations among 48 holdouts. A separate nine-lesson diagnostic found zero production ambiguities but five ambiguous rotations among 36 holdouts. Exact example: easy, seed194175174, start0, query pair1, demonstrations [0,2,3]; omit_left fits all demonstrations and changes six query cells. Preserve this limit when consumers reassemble lessons. Evidence: checks/after/checks/3977ec54e4a0_after_semantic_gate.json, checks/four-query/rotation-witness-final.json and cyclic-rotations-final.json. Explicit overrides likewise make no teaching-schedule guarantee.

## Separate proposed parametric extension

workspace/parametric/ keeps the canonical execution path unchanged. Parameters are fill_color in {2,4,6,8} and fill_edges in {false,true}, fixed for a whole episode. Default (8,true) materializes the exact canonical Racket bytes. false fills the strict diagonal interior while leaving missing edge positions untouched; object grouping, orientations, depth support and green marker preservation remain.

The extension uses real instantiated Racket programs for labels and alternate-setting comparisons, independent demo/query counts, distinct inputs, bounded sampling, and demonstration-only rival refutation. Public challenges contain no hidden settings, rule source or query answers. See its README for exact commands and checks/parametric/ for executed evidence. This is a proposed prototype, not production variant approval or training admission.

## Portable authoring tools and limits

workspace/canonical_episode_probe.py checks saved public-generation episodes against the live LESSON_COMPETITORS, rejects stale source bindings/duplicates, and reports production and query-rotation verdicts separately. It evaluates saved Racket labels; it does not independently certify arbitrary input files or establish universal identifiability.

The finite rival families and finite source-bound examples do not establish all-seed behavior or model accuracy. Backtracking remains deterministic and nonuniform over legal placements. The preexisting review index records the previous accepted source and no unresolved target audits; this return does not refresh approval hashes. Earlier imported notes remain in evidence/associated_notes.jsonl.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. Focused naming/writer checks passed; the source-bound owner receipt records the exact group count. This correction does not approve the prototype or rerun its full repair battery.
## Current reviewer considerations

Source SHA-256: `406ea39bd1050f238678d02ce90c50e02a8dd6e24e214d739398783ec7c5e603`.

# Decisions for review-e019ad4b3d0824e6

## D1 — Preserve the original chevron reasoning family

The assignment prioritizes an executable extension of original training family `896d5239`. The issued source already contains the earlier near-relation, exact arm-mask, and overlap teaching repairs; its review index has no unresolved selected-task audit. Those inherited records were context, not fresh measurements. We developed a separate prototype and made only a reproduced scalar-boundary correction in the selected generator. Original public-evaluation difficulty or new model-performance claims are outside this evidence.

## D2 — Retain lawful input choices and the established teaching schedule

| Choice | Retained behavior and rationale | Alternative considered and decision |
|---|---|---|
| Input palette | Binary 0/1 noise, fixed green 3 markers | Arbitrary color relabeling could change the canonical role semantics; not added |
| Output paint | Canonical color 8, preserving markers and exterior | Alternative paints belong to the separate parameterized programs |
| Canvas bounds | 12–22 rows and columns | No evidence requires 30×30 support; no unsupported generalization claim |
| Components and depth | 1–4 chevrons, depth 1–3, all four orientations | Increasing maxima would require new placement/profile/teaching evidence; no concrete defect justifies it |
| Arm masks | Complete, missing-marker, and unequal-arm cases retained | Restricting to complete or symmetric arms would admit known shortcuts |
| Background and placement | Existing deterministic keyed noise and bounded nonuniform placement | No claim of uniform sampling; valid distribution unchanged |
| Demo count and order | Three consecutive schedule roles, then independently requested queries | Two demos or arbitrary holdouts do not inherit this contract |
| Exact overrides | Existing supported values; explicit incompatibilities retained | Overrides bypass teaching scheduling and are not certified as whole lessons |

The current schedule uses orientation anchors plus a canonical-profile slot. Placement preserves exclusive painted witnesses so overlap cannot erase the required depth/orientation distinctions. Final strict profile and semantic reports support the retained finite distribution: 21/60 exact and 34/60 envelope profile hits, and 200/600 strict semantic draws. The older engineering rationale beyond the retained notes is unknown; this return does not invent it.

## D3 — Replace permissive scalar coercion with exact validation

Finding C-3977-1 is concrete: `grid_h=12.75` silently became 12, `asymmetric_arms=1` became true, an unknown difficulty became medium, and a negative sample index generated a grid. The before defect lint reported 132 findings. Keeping coercion would make exact controls untrustworthy; changing the common runtime would exceed the task scope. The selected repair uses the already supported strict integer helper and rejects malformed call values locally.

`None` is preserved as the existing omitted-override sentinel. Signed integer seeds remain lawful; sample indices must be nonnegative exact Python integers, booleans are not integers for this API, and difficulty must be `None`, `easy`, `medium`, or `hard`. VERSION remains 4.1.1 because it salts the keyed RNG; source SHA-256 identifies the new validation behavior. A version bump would unnecessarily change valid outputs. Red/green tests, six fixed compatibility hashes, seven identical production pairs, and the independent 17-call baseline comparison support this choice.

## D4 — Treat ordered and rotated lessons as distinct measured policies

Finding T-3977-1 is a downstream assembly limitation. The after battery has 12/12 identifiable production lessons but 6/48 ambiguous holdouts. The separate three-start-per-band census has 9/9 identifiable production lessons but 5/36 ambiguous holdouts. Its exact seed194175174 witness leaves the `omit_left` rival alive when the unique useful orientation example becomes the query.

We retained the intentional ordered curriculum and built a reusable checker that reports both verdicts. Broadening every demonstration to teach all branches would change an already passing distribution and is not required by the stated assembly policy. A consumer that rotates queries must enforce the rotated verdict after assembly. Period 3 in the census is a reporting modulus, not a newly declared exhaustive schedule contract. All rival evidence is finite; eight declared competitors do not exhaust plausible rules.

## D5 — Use two semantic parameters with a canonical identity point

Finding P-3977-1 is implemented under the task's `workspace/parametric/`. `fill_color ∈ {2,4,6,8}` varies an output role without colliding with the input palette; `fill_edges ∈ {false,true}` varies diagonal inclusion while preserving the detected objects, orientations, far-depth bound, and completion structure. The exact canonical point is `(8,true)`. Each of the other seven programs changes only guarded paint/comparison sites in the pinned Racket text.

A recoloring-only variant would supply less structural variation. Changing connectivity, which arm determines depth, or object grouping would alter the family’s reasoning more substantially and require separate domain analysis. Therefore those alternatives were not implemented. The two chosen values are fixed once for an entire episode, with deterministic seed selection when not explicitly supplied.

All labels and all alternate-setting predictions execute Racket. The Python mirror and adapted branch competitors remain diagnostics. Complete arms alone can hide `fill_edges`; the explicit complete-arm/sparse-arm diagnostic demonstrates why geometry and labels alone are insufficient. The episode builder consequently chooses a demonstration window that eliminates all seven nonchosen settings and all eight adapted branch rivals before generating four distinct queries. Bounded exhaustion fails with private diagnostic evidence, never a shortened/cloned public challenge. Query labels, parameters, and program text remain in separate private files.

The evidence is eight settings at seeds 271828–271835, not an all-seed success guarantee. The collection has 56 distinct inputs; each seven-pair episode accepts indices 0–6 and has four query assessments from the same three demonstrations. Additional seeds occur in unit tests and the CLI fixture but are not pooled into an unexplained prevalence denominator. Prototype acceptance remains separate from canonical repair and future training admission.

## D6 — Build tools future reviewers can replay

`workspace/canonical_episode_probe.py` reads the live declared competitors, verifies episode/task/source provenance, checks duplicate and malformed data, and keeps production/rotation verdicts separate. It uses stored Racket labels and never borrows a query output to refute a rival for another query. The CLI is a rescorer of saved evidence, not a certificate for untrusted arbitrary labels.

`workspace/parametric/prototype.py` exposes small importable interfaces plus a complete artifact CLI. It writes exact programs, hashes, source snapshots, public challenges, private outputs, rival evidence, and honest bounded failures. Both tools have focused behavioral tests. Audit reproducers live in `checks/audit/` because those targets are findings only. No shared tool was changed; F1 proposes the smallest follow-on integration at the consumer's final assembly step.

## D7 — Preserve evidence boundaries and failed attempts

The blind solve preceded reference inspection and declares no prior exposure. The later solve declares authoring exposure, uses the final selected source, and does not consult the reference during solving. Both masked-query scores remain unknown. Designed ambiguity probes and deliberately insufficient attempt limits are labeled diagnostics, not natural model mistakes.

Retained failed iterations include the before battery, scalar TDD failures, missing-prototype/API/CLI test failures, the probe's rotation-score development failure, stale-source rejection, one prototype bound exhaustion, and the audit script's source-versus-lowered-hash assertion error. Later success does not erase them. Exact command arrays, exits, source hashes, and paths are recorded in RESULTS.json and the detailed command ledgers.

The first fresh-replay convenience-wrapper test invocation also exited 2 because the declared runtime closure excludes ASSIGNMENT.json. The explicit public check command supplied the task ID and passed all 106 tests and 347 subtests using the fresh environment. Both the failed attempt and successful resolution are retained under checks/handoff/; no immutable assignment or source file was changed to resolve it.

## D8 — Keep audits findings only and separate canonical support from label correctness

For A-db67-1, the unchanged selected validator excludes four of five canonical inputs. Both the previously reported two-lowest-colors shortcut and the newly tested first-pair-per-orientation shortcut match all 36 generated draws, yet each matches only one canonical pair. This independently reaffirms `review-744c58f59a7bb8e9:v0001`; the fresh canonical train-pair-2 witness differs from the prior retained witness. The excluded canonical cases diagnose a domain restriction, not an observed production-query ambiguity.

For A-5d0082374b4d-001, seed136/easy produces three all-even-width demonstration sets followed by odd-width query frames. A marker-preserving rival fits all demos and differs at two query cells. Racket, the independent full-stripe implementation, and the target mirror agree on all ten checked inputs. This is a demonstrated lesson-identifiability defect without an observed label error. Existing note GNOTE-001240 was context; the production episode and minimal reduction are newly executed evidence. Neither audit changes target source or approval.

## D9 — Finish with an actual patch replay

The original packet is immutable and the return uses its supplied builder. Final handoff replays the exact source delta into a fresh runtime-closure extraction with a verified WORK Git root and per-file hash comparison, then runs task tests with the fresh copy's own environment. The partial extraction scope and test receipts are recorded under `checks/handoff/` and in REVIEW.md. The task-local implementation plan is frozen before packaging; final handoff receipts live outside the source patch to avoid a self-referential delta.
