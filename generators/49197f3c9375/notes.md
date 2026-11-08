# Working notes: 49197f3c9375

## Current rule and authority

Extract every nonzero monochrome 4-connected component. Canonicalize each shape under the eight dihedral transforms. Exactly two classes occur twice and one class occurs once; return the singleton component's four-neighbour boundary, in its original color, cropped to the component bounding box.

The selected canonical Racket authority is unchanged. `RULE_HASH` remains `4303be5db475`; final generator SHA-256 is `a23b045bf7c4c3f8bb72e8aaf5eb7662f156e835d24711308ad6b25422b41dcd` (version `3.0.0`). The canonical prose still does not independently disambiguate boundary-only from whole-component crop, so executable Racket remains the label authority.

## Repaired defects

The inherited `2.0.0` validator rejected all three lawful 8x15 canonical inputs because it required generated-only dimensions and required one strictly rotation-only plus one strictly reflection-only witness even when a canonical pair is symmetry-ambiguous. It also emitted no canonical-size/six-color profiles in the sampled floor, accepted unknown controls, declared no executable rivals, and supplied no task-local regressions.

Version `3.0.0` now:

- accepts and mirrors all three canonical pairs without mutating them;
- keeps the stronger rotation-only/reflection-only requirement on generated draws, not on lawful canonical inputs;
- rejects unknown or mistyped overrides and exposes exact observable controls for grid size, target topology, target scan slot, and color scheme;
- declares the canonical-fit rivals `whole_singleton` and `last_motif_boundary` plus executable witnesses;
- cycles six semantic roles (first/middle/last × interior-bearing/boundary-only) and makes every consecutive four-pair window identifiable against both rivals under every one-pair query holdout;
- pins the first six draws in each 24-draw block to the canonical 8x15/six-color profile, giving 25% canonical-profile support without eliminating broader canvases or color reuse modes.

## Evidence and limits

Final checks: all 12 battery stages green (`checks/after/result.json`), 28/28 task-local regressions green (`checks/task-tests-final-source/result.json`), and a required-rotation census of 300 lessons / 1,200 unique inputs found zero production or rotation ambiguity against the six declared rival entries (`checks/lesson-census.json`). The exhaustive task-local schedule test covers all 24 cyclic starts, three bands, and all four query positions.

`counterexamples/strongest-rivals.json` is a Racket-verified lawful 8x15 input that simultaneously refutes both canonical-fit rivals. It is covered by the source-bound regression suite.

Finite rival checks are not a proof of unique induction against every conceivable hypothesis. The six-role deterministic curriculum and 24-draw profile anchoring are intentional ordering constraints; downstream assemblers that ignore ordering should retain the query-rotation check. The generated domain remains 8..12 by 15..20 with five motifs and signature multiplicities `[1,2,2]`.
## Current reviewer considerations

Source SHA-256: `a23b045bf7c4c3f8bb72e8aaf5eb7662f156e835d24711308ad6b25422b41dcd`.

# Decisions for 49197f3c9375

Final generator: version `3.0.0`, SHA-256 `a23b045bf7c4c3f8bb72e8aaf5eb7662f156e835d24711308ad6b25422b41dcd`.

## D1 — Separate lawful task-domain validation from generated-distribution strength

**Prior choice:** `self_check` accepted only the generator's 9..12-row domain and required the two pairs to classify exactly as one `rotation_only` and one `reflection_only` relation.

**Problem:** all three canonical inputs are 8x15, and lawful D4-equivalent pairs can be symmetry-ambiguous (`rotation_or_reflection`). The baseline therefore rejected every canonical pair even though the selected Racket authority labeled them correctly.

**Decision:** make `self_check`/`strict_canonical_like` accept 8..12 by 15..20 lawful inputs with multiplicities `[1,2,2]`; keep the stronger one-rotation-only/one-reflection-only constraint inside generation before return.

**Rejected alternative:** weaken generated draws to any two D4 pairs. That would restore canonical parity but reduce evidence that both transformation types are understood.

**Probe:** canonical parity and input-purity regression over all three pairs; final `selfcheck`, `rule_smoke`, and `authority_sync` stages are green.

## D2 — Declare and execute the two canonical-fit rivals

**Decision:** expose `whole_singleton` and `last_motif_boundary` in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; bind them to `interior_boundary` and `singleton_not_last` witnesses.

**Reason:** both rivals fit every canonical example for accidental reasons: canonical singleton shapes have no interior, and they are last in scan order. These are stronger and more realistic than arbitrary color or size shortcuts.

**Rejected alternative:** list rivals only in prose. The semantic gate and lesson census require executable hypotheses to test whether demonstrations actually refute them.

**Probe:** `counterexamples/strongest-rivals.json` gives one Racket-verified input that refutes both. The regression first confirms each rival fits all canonical pairs, then confirms disagreement on this generated case.

## D3 — Use a six-role semantic schedule

**Decision:** cycle target positions `first, middle, last, first, middle, last` while alternating `interior_bearing, boundary_only, ...`.

**Reason:** every consecutive four generated pairs then contains enough witnesses that, after any one pair is held out as query, the remaining three demonstrations refute both declared rivals.

**Rejected alternatives:**

- independent random slot/topology draws: positive marginal witness frequency does not guarantee a complete lesson contains both witnesses;
- only interior-bearing targets: strong boundary evidence but excessive repeated ring outputs and weaker topology diversity;
- only non-last targets: defeats positional selection but leaves whole-crop semantics underdetermined.

**Probe:** source-bound tests enumerate all 24 cyclic starts, easy/medium/hard, and four possible query positions. The required-rotation census independently checked 300 production lessons and 1,200 held-out query rotations with zero ambiguity.

## D4 — Pin 25% canonical-profile anchors without collapsing the curriculum

**Baseline:** the profile floor found zero 8x15/six-color draws in 60 samples.

**Intermediate attempt:** one anchor every five samples yielded only 8/60 envelope hits (13.3%) and an after-phase warning. That evidence is retained under `checks/after-profile_floor/`.

**Final decision:** in each 24-draw period, pin the first six semantic roles to 8x15 with five distinct foreground colors plus background. The remaining 18 draws retain broader sizes and distinct/reused/monochrome schemes.

**Reason:** this gives exactly 25% scheduled canonical-profile support while the six pinned cases cover every slot/topology role rather than privileging one role.

**Rejected alternative:** pin every draw to 8x15/distinct. It would pass profile parity by eliminating useful size and color-confound variation.

**Probe:** final profile-floor stage is green in every band; diversity and distribution stages also remain green.

## D5 — Keep target size and bounding box non-unique

**Decision:** every singleton shares its cell count and bbox dimensions (allowing transposition) with another motif.

**Reason:** otherwise “choose the uniquely sized object” or “choose the unique dimensions” would solve the task without D4 grouping.

**Probe:** `self_check` enforces both properties; generated-distribution and semantic gates passed.

## D6 — Preserve color confounds as exact controls

**Decision:** support `distinct`, `reused`, and `monochrome` component-color schemes, with distinct colors heavily weighted outside exact overrides and required on canonical anchors.

**Reason:** fixed unique colors can make component identity or scan order easier; reused/monochrome cases force shape-based grouping. Distinct anchors preserve canonical palette support and avoid making difficult color segmentation the only default.

**Failure mode considered:** adjacent different-colored components can form a single foreground mass but are still separate monochrome components. Generated layouts keep background separation; canonical validator does not falsely reject lawful different-colored contact.

**Probe:** all exact controls are observable in every difficulty band; final override stage rejects unknown keys and is green.

## D7 — Keep Racket authority unchanged

**Decision:** no shared rule or canonical ledger edit. Keep `RULE_HASH=4303be5db475`.

**Reason:** the selected executable authority is consistent with every canonical output and with generated counterexamples. The unresolved issue is descriptive: canonical prose does not explicitly say boundary-only, but assignment policy makes the executable authority controlling.

**Probe:** Racket rule smoke, grammar, lint, authority sync, and exact counterexample apply all pass. Archival raw-code formatting remains divergent but execution parity is PASS.

## D8 — Strict call contract and portable task tests

**Decision:** reject unknown controls and wrong types before generation; use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` in task-local tests. Persist the exact Racket counterexample under the task directory and replay it in tests.

**Reason:** silent controls make requested datasets irreproducible, and fixed parent-depth paths fail in isolated verification runtimes.

**Probe:** initial counterexample-file regression failed before the artifact existed; final source-bound run passes 28/28 in the isolated runtime.

## Remaining limits

The rival set is finite. Passing it does not prove unique identification against all programs. The ordered six-role schedule matters; assemblers that arbitrarily reorder or subsample pairs should rerun rotation/lesson checks. The generator intentionally covers a constrained five-motif `[1,2,2]` manifold rather than every lawful input to the rule.

## Native parametric build — current design

The native proposal keeps the reviewed full-shape D4 grouping and unique-singleton selection, then renders `boundary`, `whole`, or `interior`. The selected component's cells, color and original bounding box are the causal intermediate. The boundary default preserves the exact selected Racket bytes. Interior excludes the canonical four-neighbour boundary, including hole-adjacent cells; an empty interior retains the original output dimensions.

The native grammar expands to 5, 7 or 9 components on 8..30 by 15..30 grids, with exactly one singleton class and all other D4 classes paired. Target area and bbox remain confounded with other components. Deterministic complete six-demo/four-query banks use role-specific local random streams; the mandatory three demonstrations vary target position, palette and topology, including thick nonrectangular and hollow targets. The 30x30 role uses nine large motifs. Implementation order: independent geometry/contract regressions, native family and constructive sampler, strict adapter, finite protected-Racket rival review, source inventory, qualification, executed causal witness and public projection verification. Production approval and owner acceptance are separate from this proposal.

### Native teaching repair

The first three-demo construction admitted five plausible feature shortcuts: group by exposed-edge perimeter; group by perimeter plus interior count; group by D4 orbit size; group by sorted row/column projection histograms; or choose minimum D4 orbit size. Bounded independent review found 16 seed/setting cases across seeds 0 and 17, all subsequently confirmed through protected Racket. The thin interior demonstration had an all-zero output, which concealed some incorrect selections. Original grids, exact rival programs and nine source/test snapshots are retained in `checks/49197f3c9375/self-review-*`.

Repair the existing first demonstration using an asymmetric hollow target and a D4-distinct paired shape with the same area, bbox, perimeter, interior count, orbit size and projection histogram. Put that target in the middle and include a more symmetric paired ring; distinct colors expose incorrect intermediate choices. Move the second demonstration's ring target to first, retain the third thin control, and keep the three-demo count and all query inputs. Add the exact observed rivals to the audit menu and replay the retained cases against the repaired demonstrations. This strengthens visible evidence without weakening the query distribution or changing canonical semantics.

The first repair refuted all 16 original findings, but its protected audit retained two new interior-setting query conflicts for rotation-only grouping. Final construction makes the first demo's chiral pair reflection-only and ensures a member precedes the actual middle target. The role-specific guard preserves all other roles and query bytes. The intermediate audit remains under `checks/49197f3c9375/audit-repaired/`; three failing rotation regressions precede the passing 47-test sampler suite. No additional demonstration, query simplification or new shape template was needed.

### Native reviewer readiness

Final focused suite:104 passing tests. Final protected rival audit:6 episodes,134 comparisons,128 demonstration refutations,6 finite-consistent boundary-grouping cases,zero query conflicts or execution errors. Maximum-seed6+4 requests produced30 matching protected labels. Native qualification passed all3 settings at seeds0 and17 (6 jobs,78 Racket evaluations), with3 source-bound wrong-intermediate cases built and replayed. Public projection produced24 one-query views and rejected all3 corrupted-copy cases without modifying the originals. Evidence is under `checks/49197f3c9375/`; the task-local inventory binds final source and current checks. Reviewer status is ready; owner qualification and fresh acceptance after integration remain pending. Training admission remains false.
