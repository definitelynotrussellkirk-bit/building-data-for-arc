# Working notes: 996fc37f49d9

## 2026-10-02 review: version 2.1.0 candidate

Original generator `57e4744c366cd942f344ef316a0a006120068d74213df3d639914b0a4c1324ce`; final `8ca3ae432da24852b9302c1509d02a3b0f2af966cb8fa4a597a5fc7172463745`. Selected Racket `b8683f5eb53430e9f49ad5eda58f3dc450320ad34d851ac7e3664df78717ff5c` is unchanged. The immutable review assignment is `review-8d7412087342e122`.

Repaired rank-conditioned palettes, fixed general dimensions/size tuples and fixed rank zones. Added strict sparse/compact box-area counterexamples and executable rival declarations. A 12-slot schedule preserves 50% canonical anchors while providing a box/scan diagnostic in every contiguous default three-demo window. Explicit overrides do not inherit that guarantee. General shapes use finite frontier growth and bounded placement.

Native and portable task suites pass 80 tests. Final battery is 12/12 green; standalone lint passes. At seeds 0..599 / index 0, each band has 255/600 box-order inversions, 600 unique inputs and 300 strict anchors. A separate 1,080-overlapping-window lesson probe has zero ambiguity against the five declared rivals, over 1,254 distinct grids. These are bounded checks, not learner-training or unrestricted-identifiability evidence.

The repository-wide suite still has the independently reproduced 0.2-second child-startup timeout failure; see root REVIEW and FEEDBACK. Audit-target sources were not changed. Fresh solve records disclose prior exposure and withhold query correctness.

Workspace tools: `probe_distribution.py`, `audit_findings.py`, `verify_portable.py`; runnable instructions in `workspace/README.md`. Rejected generator and audit-oracle iterations are intentionally retained, not active alternatives. Full review rationale/evidence lives in root REVIEW.md, DECISIONS.md, QUESTION_ANSWER.md and AUDIT.md in the review return.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`; none were rewritten. Approval remains catalog-derived; this note does not grant approval or training admission.
## Current reviewer considerations

Source SHA-256: `8ca3ae432da24852b9302c1509d02a3b0f2af966cb8fa4a597a5fc7172463745`.

# Decisions for 996fc37f49d9

All measured claims below refer to final generator `8ca3ae432da24852b9302c1509d02a3b0f2af966cb8fa4a597a5fc7172463745` unless marked original/intermediate. The Racket authority `b8683f5eb53430e9f49ad5eda58f3dc450320ad34d851ac7e3664df78717ff5c` is unchanged. The original file is retained as `checks/probes/baseline_generator.py`; rejected intermediate source snapshots are in the task workspace.

## D1 / G1: distinguish occupied area from bounding-box area

Original source used connected random shapes but supplied no explicit bounding-box rival. Its general size tuples and small shape boxes made box order mostly agree with occupied-area order. All five canonical pairs also agree with box ranking. The historical reason for omitting this rival is unknown; I do not infer an intent from missing code.

Choice: introduce a variable sparse L and a denser connected object with more cells but smaller box area. Mix these with unconstrained connected shapes, and retain exact counterexamples with actual Racket outputs. Add the rival to both lesson identification and the semantic gate. Rejected: changing the Racket rule, merely renaming a witness, or treating more random seeds as sufficient. Evidence: `checks/census-final/bbox_counterexample.json`, `generated_bbox_witness.json`.

## D2 / G2: remove input-colour and position labels

Original source explicitly sampled a short list of rank-ordered palettes and placed general objects in rank-specific zones. This may have helped deterministic, collision-free construction; the historical motivation is not established by this review. In the original two-object multicolour branch, colour membership itself identified the answer rank.

Choice: sample without replacement from the six legal nonzero, non-output colours and assign independently of area rank; choose whole-canvas placements without fixed rank zones, including borders. Monochrome scenes stay because the canonical task requires object individuation independent of colour. Rejected: requiring a different colour per component everywhere (contradicts canonical scenes), globally permuting output colours (changes the task), or placing small/large objects in different fixed quadrants.

Input colours 2/3/4 remain excluded, as inherited, to avoid accidental output-identity cases. This is a distribution boundary, not a general theorem about ARC. Tests independently exercise both general profiles with colour overrides and require support at every rank.

## D3 / G2: broaden sizes and dimensions without changing the task

Original general two-component scenes had one canvas size and three fixed size pairs; three-component scenes had one other canvas size and three triples. Canonical anchors had legitimate fixed public profiles. The narrow general choices were not a consequence of the area-ranking rule.

Choice: independently sample both general dimensions in 13..24 and size sets from 3..18. The free general branch grows connected shapes through a finite frontier inside a bounded box. No output is constructed by the sampler; canonical Racket remains the labelling authority. Rejected: arbitrarily huge scenes, singleton/zero-size components, or equal sizes without tie semantics. Relative-rank overlap is explicitly tested: the same occupied area can receive different output ranks depending on its peers.

The generator is still not an unrestricted polyomino sampler. Diagnostic L/compact shapes have narrower support and correlations; free scenes and anchored scenes remain necessary. Dimension diversity is an input-variation metric, not demonstrated training benefit.

## D4 / G3: preserve canonical support and make default lessons informative

Original prior was 50% strict canonical-like profiles, with randomized placement and transformations. Keeping that fraction preserves the supplied profile-floor contract rather than replacing the public task with a synthetic one.

First attempted repair retained the four-slot schedule and independently randomized general scenes. It passed 75 tests but failed an existing rotated-lesson test after the new box rival was added: demonstrations could remain ambiguous. The failed source is `workspace/rejected_v1_generator.py`; log `checks/probes/green_regressions_v1.log`.

Final choice: a 12-slot schedule with six canonical slots, four monochrome diagnostic slots at offsets 1/4/7/10, and two general multicolour slots. Every three consecutive default slots include a diagnostic. The diagnostic forces both a strict box-order inversion and nonascending scan order. Reflections are selected so the latter property survives the difficulty transform. Generic override use remains available and is not falsely covered by the default-lesson guarantee.

Rejected: dropping the canonical floor to put a diagnostic in every second sample; deleting the failing lesson test; filtering all ambiguous lessons after generation without improving inputs; or pretending finite rival tests prove unique inference. A larger expressive hypothesis class could still identify another shortcut.

The 1,080-window census is **overlapping**, not 1,080 independent episodes: 30 seeds, 12 offsets, 3 bands, with 3 demonstrations and 1 query each. Final unique-grid count is 1,254, down from 1,348 original. We retain this trade-off in the report rather than reporting only the improved ambiguity rate.

## D5 / G3: executable witness semantics

The schedule-only version passed 76 unit tests but its after battery failed semantic validation: feature-presence witnesses were being interpreted as unsupported causal claims. That source is `workspace/rejected_v2_generator.py`; its hash is bound in `checks/after/result.json`.

Choice: keep feature-only witnesses in `BRANCH_WITNESSES`; bind order witnesses to actual rival functions in `WITNESS_RIVALS`; export `SEMANTIC_RIVALS`, `LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS`. A new failing-then-passing test checks the binding and witness implications. Rejected: weakening the semantic gate or marking its nonzero exit as advisory. Final stage is genuinely green.

## D6 / G4: native and portable verification

The inherited task test assumed the copied legacy directory tree. The initial native collection error showed this assumption. Choice: discover the native shared runtime when present, otherwise use the legacy staged layout. `verify_portable.py` prepares an independent runtime in `/tmp`, explicitly stages the new review-tool tests, removes Python path leakage, denies Python file reads under the original repository, and verifies module origins. It retains the exact runtime directory and source hash but deletes the runtime after verification. No installed environment or duplicate runtime goes into the return ZIP.

The canonical runtime map does not automatically include newly authored workspace tools/tests. The verifier stages those explicitly; this does not edit the shared mapping. Future intake should run both the native task directory and an explicit staged test manifest rather than assuming bare repository pytest discovers them.

## D7: independent probes and retained mistakes

`probe_distribution.py` uses an independent set-based flood fill, not the generator's component routine. Racket checks validate a declared subset; Python-only counts are labelled as such. `audit_findings.py` is read-only for the two assigned audit targets. Its first translation oracle incorrectly treated crop selection as a mask; the failed report and source remain, and a new regression tests marker copying. Final audit semantics follow the unchanged Racket authority, while disagreements with generator prose are reported separately.

No audit target was repaired because assignment scope reserves changes for 996fc37f49d9. No shared runtime timeout fix was smuggled into this patch. The timeout diagnostic is retained under checks and isolates startup sensitivity; a maintainer must decide the shared-test repair.

## D8: no authority change, no approval promotion

Occupied-area ranking already matches all stored canonical outputs. Input-distribution defects do not justify relabelling that rule. The authority-sync stage reports selected authority agreement with an existing archival raw-code divergence and passing execution parity. That inherited archival distinction is not described as byte-for-byte equality of every historical copy.

Racket authority, canonical rows, runtime helpers and approval metadata are unchanged. Fresh solve evaluation follows the packet's visible-only policy with disclosed earlier exposure. Correctness of masked queries and trained-model transfer remain unmeasured here.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/996fc37f49d9/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Native parametric family — 2026-10-25

The production generator and canonical authority remain unchanged. The native
adapter at `workspace/parametric/` keeps exact canonical `rank_metric=cells` as
the default and adds `rank_metric=bounding_box`. Step A discovers every nonzero
4-connected component and orders it by the selected metric; step B consumes that
ordered coordinate list and repaints ranks 2/3/4.

The first qualification exposed a real teaching defect: at the two-demo minimum,
density, scan position, width or height could fit both demonstrations yet disagree
on a query. The sampler was repaired rather than increasing the count. Its first
two demonstrations are now a constructive contrast set whose occupied-cell,
bounding-box, density, scan, input-color, perimeter, width and height orders do
not collapse to the same lesson. The pre-repair finding is retained at
`checks/996fc37f49d9/adversarial-teaching-before.json`; the current audit reports
no surviving shortcut in that finite set.

The adapter supports 2–6 demonstrations and 1–4 query projection, with four
private queries and a substantive 30x30 boundary case. Sixty-four seeds passed
11,008 contract assertions; the complete task suite is 112/112 green. Fresh
qualification executed 32 protected-Racket labels, and a two-direction causal
witness replayed cells→box and box→cells counterfactuals. Sixteen saved
single-query public views passed identity/privacy structure checks.

Evidence: `checks/996fc37f49d9/qualification/`,
`checks/996fc37f49d9/causal/`,
`checks/996fc37f49d9/adversarial-teaching.json`, and
`checks/996fc37f49d9/public-export-check.json`. These are finite reviewer checks,
not universal identifiability, measured training gain, owner acceptance, or
training admission.
