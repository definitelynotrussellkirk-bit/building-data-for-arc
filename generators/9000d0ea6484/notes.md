# Working notes: 9000d0ea6484

## Final design

The baseline's random textures did not guarantee evidence for the section priority and exposed dead/illegal axes. Version 3 replaces texture sampling with a shuffled schedule of eleven mandatory signatures—empty, four solos, six pairs—plus five difficulty-controlled extras. Thus every generated input independently identifies the total order `2 > 3 > 0 > 1`.

The canonical palette `(8,5,9,4)` aliases section priority with fixed color order `9 > 4 > 8 > 5`. Defaults avoid each section's own canonical color; all legal colors remain available through exact overrides. Future explicit color pins are reserved before defaults are drawn so legal partial overrides cannot collide due to draw order.

Canonical examples remain accepted under structural validation even though they do not each contain the full synthetic witness set. Noncanonical generated palettes must contain every mandatory signature. Executable rivals, causal witnesses, and `lesson_identifiable` cover all 24 section orders plus fixed-color, scan, numeric, zero-fallback, and ignored-section alternatives.

## Evidence

- Prior approved generator SHA-256: `0c5c72bd81eceadfaae62cdca445f1f559419500f9b3c0d022d276196737e8b2`.
- Current review source SHA-256 after strict call-contract repair: `4ff606f4991bd7f64ab55a0ef47268364bc70dd392314544150da1f35f89a24e`.
- Prior official battery: 12/12 green (`checks/after-final2`); current after-phase receipts are recorded under packet `checks/after`.
- Current direct task suite: 100/100, including strict common-call and parametric-prototype tests.
- Independent probe: 900/900 unique valid draws and 7/7 canonical pairs (`checks/reference-probe-final.json`).
- Lesson census: 300/300 complete lessons, 0 ambiguity, 1,200 unique inputs (`checks/lesson-census-final.json`).
- Strongest shortcut counterexample: `checks/question-shortcut/counterexample.json`.

The selected Racket semantics did not change. Active `target_code` was synchronized textually to canonical executable source; archival `raw_code` is preserved.
## Current reviewer considerations

Source SHA-256: `4ff606f4991bd7f64ab55a0ef47268364bc70dd392314544150da1f35f89a24e`.

# Decisions — 9000d0ea6484

The selected generator's existing D1–D11 design remains in `repo/generators/9000d0ea6484/notes.md`. This review did not reopen its geometry, curriculum, palette, authority, or rival-set choices. The decisions below cover this return's delta.

## D12 — Validate common call arguments before `gen_ctx`

**Choice.** Require exact integer `seed`, exact nonnegative integer `sample_index`, and `difficulty ∈ {None,easy,medium,hard}` at the start of `generate()`.

**Original behavior/rationale.** The generator delegated these values to `gen_ctx`; no task-local rationale for accepting coercible scalars was documented.

**Why changed.** The before defect-lint stage deterministically accepted 48 invalid calls, including booleans, floats, numeric strings, negative indices, and invalid difficulty scalars. Those values can silently alter replay keys or difficulty bands.

**Alternatives rejected.** Validating only overrides leaves the common-call defect. Fixing only the 48 examples is brittle. A global shared-runtime change is desirable but outside the task patch and may require compatibility work across the catalog.

**Probe and failure mode.** Sixteen focused invalid-scalar cases failed before implementation and pass after it; all four documented difficulty values remain accepted. The after defect lint is green. This deliberately breaks previously tolerated invalid calls while preserving all valid-call outputs.

## D13 — Keep generator version `3.0.0`

**Choice.** Do not bump `VERSION` for the validation-only repair.

**Rationale.** `VERSION` participates in keyed sampling. Bumping it would alter every valid generated lesson even though the transformation and valid input distribution are unchanged. The new behavior only rejects calls that violate the shared contract.

**Alternative rejected.** A patch-version bump would make provenance look conventional but would create an unnecessary distribution migration.

**Limit.** Consumers that intentionally relied on invalid scalar coercion now receive an exception; that is the intended contract correction.

## D14 — Parameterize the hidden priority scan outside canonical authority

**Choice.** Build a proposed episode-level prototype with two parameters: `start_section ∈ {0,1,2,3}` and `scan_direction ∈ {forward,reverse}`. The default `(2,forward)` is exactly the canonical order `2,3,0,1`; seed 6 demonstrates `(2,reverse) = 2,1,0,3`.

**Rationale.** This preserves the same 4×19 geometry and aligned-cell operation while yielding eight distinct, interpretable Racket programs. The existing complete lesson contains all six pairwise overlaps, so it supports identification of any total order in this bounded family.

**Alternatives rejected.** Adding parameters to the selected generator API would conflate a proposed rule family with canonical training authority. Supporting all 24 permutations adds unnecessary complexity. Varying geometry changes the task family rather than the hidden rule.

**Probe and limits.** `checks/parametric/final/report.json` records 8 distinct programs, 64/64 Racket–Python label matches, 7/7 canonical pairs under the default, 8/8 pair checks refuting every rival, and 8/8 identifiable query rotations. The prototype is limited to cyclic scans and is not an approval or authority update.

## D15 — Separate private labels from public parametric challenges

**Choice.** Write full labelled episodes under `checks/parametric/final/private/` and answer-masked challenges under `checks/parametric/final/public/`.

**Rationale.** Future agents need replayable ground truth, but challenge consumers must not receive hidden parameters, Racket text, or query answers.

**Alternative rejected.** One combined JSON artifact is simpler but leaks the exact rule and answer.

**Probe.** Task-local tests assert that public files contain only demonstration input/output pairs and input-only queries, and that encoded public data contains no parameter names or `rule!` text.

## D16 — Preserve audit isolation

**Choice.** Reproduce findings for `0d85790c3f38` and `a61246736c26` without editing either target.

**Rationale.** The assignment defines audits as findings-only. Their source hashes match unresolved retained findings, and independent probes confirm them.

**Limit.** These findings require separate maintainer triage and do not change the acceptance status of the assigned repair.

## Current native result — review-f67b156360beea89

**Reviewer status: ready; owner exact-source acceptance pending.** The production
generator remains version 3.0.0, SHA-256
`4ff606f4991bd7f64ab55a0ef47268364bc70dd392314544150da1f35f89a24e`.
The canonical program and all eight retained fixed cyclic scans are unchanged.
Earlier canonical and prototype evidence above remains historical.

### Rule and implementation decisions

The native contract exposes `start_section = 0,1,2,3,densest,sparsest` and
`scan_direction = forward,reverse`: twelve settings. Integer starts reuse the
retained prototype's exact guarded materializer through an adjacent-path loader.
The canonical default is `(2,forward)`, with raw program SHA-256
`3bec9ede53940dce7bdf0aa83666b99ea3fb754cb6c4d356406e7eab30dade8c`.

For a density start, count nonzero cells per panel, select the extreme with
ties in order `2,3,0,1`, and then choose the cyclic overlay order from that
input-derived panel. The count vector is A's output and B's required input.
The protected causal witness replaces only `(map count-cells indices)` with
`(list 0 0 0 0)`. On seed 0's first demonstration, counts `[9,4,7,6]` choose
panel 0 for densest and panel 1 for sparsest. The wrong intermediate chooses
panel 2 and changes eight and three output cells respectively, leaving all
selector, tie, scan and rendering code unchanged.

The full API admits strict literal integer grids with 1–30 rows and 19 columns,
fixed color-3 dividers, and arbitrary non-divider payload colors or empty panels.
Generated inputs use four distinct monochrome panels with all eleven empty,
solo and pairwise signatures. The existing canonical program has dynamic
height and fixed width-4 sections; 30×19 is meaningful maximum stress.
A 30×30 extension would introduce columns ignored by the default, so it is not
claimed. There is no global-rotation contract.

### Four-demo repair and its cost

Strengthening three demonstrations still left a concrete ignored-candidate
shortcut: the densest rule could ignore section 1, and the sparsest rule could
ignore section 3. Both rivals fit the proposed three-demo prefix and disagree
on five cells of a novel fourth input. These original two-rule lessons,
programs, outputs and minimal distinguishing input remain in
`checks/9000d0ea6484/audit-r1/teaching-gap.json` for optional alternative-answer
research; they are not normal single-answer export labels.

The repaired minimum/default is four demonstrations, up to six, with one to
four queries requested independently. This costs one extra demonstration.
The first four count vectors are `[9,4,7,6]`, `[5,5,9,9]`, `[5,9,5,9]`,
and `[7,10,6,4]`: all four panels win under each density policy. Query
anchors still cover all four panels. The repair preserves query branches.

`sampler.py` builds six training and four query inputs before slicing, with
separate SHA-derived local RNG streams and a 64-attempt duplicate limit.
Settings share identical input banks. Query heights are 3, 7, 18 and 30.
The 30×19 case contains 335 payload cells plus 90 divider cells; all thirty
rows and all four boundaries contain actual content. Output occupancy is
118 cells at seed 0 and 119 at seed 17.

### Executed checks and retained tools

- 60 focused native adapter tests passed, including seven canonical pairs,
  literal outputs, strict types, count boundaries, input-prefix independence,
  matched settings, remote count effects, public masking and substantive stress.
- 24 audit/export guard tests passed. Initial missing-feature and intentional
  guard failures remain in separate red receipts; earlier green stages are
  superseded by the final focused receipts.
- Protected audit: 24 episodes at seeds 0 and 17, 192 intended labels plus
  seven canonical labels, 1,032/1,032 finite rival comparisons refuted on the
  first four demonstrations, 831 evaluations and 3,496 exact cache hits.
  All 96 one-query public files passed strict byte/schema/hash/projection checks.
- Native qualification: twelve settings, 24 jobs, four demos/four queries,
  1,248 protected evaluations, selected setting the sole declared survivor.
- Two causal cases were constructed and independently replayed by the native
  witness helper. Status is `reviewer_replayed`, not owner acceptance.

The reusable tools are the native adapter/family, constructive sampler,
protected teaching audit, exact public-export verifier and focused regressions.
The audit's cached teaching-gap extraction adds no evaluations. The retained
legacy 3+1 seed-filename writer is not the native export path.

Current inventory:
`workspace/parametric/evidence/manifest.json`, SHA-256
`1183531a210b98afd162303642b4d48d860e99ea47d7167eb9bee6eb6ea943f1`.
The inventory includes both new test sources and eleven current evidence
references; it is an author-reported inventory, not an execution claim.
Qualification and sibling execution are in
`checks/9000d0ea6484/qualification/`; causal evidence is in
`checks/9000d0ea6484/causal/`.

### Limits and next action

This is bounded evidence for the named rivals and seeds, not universal rule
uniqueness, every future draw, or measured training benefit. All executable
checks ran from this isolated packet without sibling imports. No production,
shared runtime, approval/index, canonical authority or training setting changed.
After integrating the exact source, the owner must run native qualification and
fresh acceptance under the packet's intake policy. Training admission remains
false. No further main implementation blocker is reported.
