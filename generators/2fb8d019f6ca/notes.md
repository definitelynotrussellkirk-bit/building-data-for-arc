# 2fb8d019f6ca — current generator decisions

## Rule and identity

Version 3.0.0 keeps canonical Racket rule `b1a2d9fb3e21`: extract the
four-connected non-{0,8} component rooted at (0,0), clear the canvas, and stamp
its nonzero colored cells at every color-8 position. Background 0 and anchor 8
are fixed semantic roles. Canonical program text and archival raw_code are
unchanged. The selected target_code copy was synchronized to canonical text
using the public authority-sync proposal; only comments were removed.

## Distribution and reversals

- Prior six-template bank -> connected growth in a 3x3 box and longer 2x4/4x2
  templates. There are 3..8 template cells and 1..3 template colors; every chosen
  color is actually painted. All five canonical inputs remain accepted.
- Prior asymmetric anchor test and capped retry loop -> finite constructive
  rectangle tilings. Source and every stamp bbox are disjoint, counts are exact,
  and no copy clips. Anchors can lie in top/left bands and against the far edges.
- Prior ignored palette controls -> exact `palette_size` (nonzero colors,
  including 8). `n_distinct_colors` remains an explicit compatibility alias;
  conflicting requests raise. It is not counted as an independent axis.
- Removed inert `palette_kind`, `texture`, `position_bias`, and `density` names;
  requests now fail explicitly. Old degenerates are outside the production
  sampler, not reclassified as invalid Racket programs. Rootless/no-anchor
  examples produce blank under the actual runtime but are excluded here.
- All six advertised integer axes work throughout their ranges in every band.
  Reject unknown keys, noninteger/bool overrides, malformed sample indices and
  invalid difficulty names. A seed is a Python integer; indices are nonnegative.
- The validator checks integer grids, component size, color cardinality,
  distractor count/palette, bounds and symmetric source/stamp collision.

## Teaching contract

Ordinary default samples alternate even `canonical_core` and odd
`extraction_witness` profiles. Core grids use one of the four canonical size
pairs, two anchors, two template colors and no distractor. Witness grids use
3/4 anchors, a 4-long template axis, and one diagonally adjacent disconnected
pixel. Placement guarantees at least one translated distractor would appear
in bounds outside every true stamp, so its exclusion is observable.

The four declared canonical-fitting rivals are: all non-anchor pixels,
8-connected extraction, first two anchors, and fixed 3x3 extraction. A default
four-pair consecutive window contains two rich witnesses, so any single query
rotation retains a witness in its three demonstrations. `EXAMPLES_NEEDED=3`
and `LESSON_SCHEDULE_PERIOD=2`. These are finite rival claims, not universal
identifiability. The census records actual accepted indices because rejection
or duplicate filtering could otherwise invalidate the consecutive-window claim.
Explicit overrides can narrow or disable the teaching guarantees.

## Evidence and remaining limits

`tests/test_stamp_contract.py` covers the inherited defects, canonical labels,
scalar guards, joint boundary controls, determinism and broad rival separation.
`counterexamples/current-contract-regressions.json` records minimal regressions.
Return checks retain live Racket labels, final source hashes, all earlier
failures, fixed-seed schedule enumeration and 300 production lessons / 1,200
query rotations. The return's REVIEW.md and RESULTS.json own measured counts.

This sampler deliberately excludes overlapping stamp bboxes, clipping,
zero anchors and absent roots. It therefore does not teach transparent-zero
overlap, clipping, or order of conflicting stamps. Larger 3x4+ boxes and arbitrary
free-position placements are also outside this bounded distribution. The tiling
construction is a documented spatial bias. No training admission is implied.

The inherited audit `review-e935ce7fbf9f51fb:v0001` remains explicitly retained
under evidence/review_index.json. Its ignored-count and asymmetric-placement
findings are addressed by the named regressions; maintainer audit resolution
is still required. No unrelated audit status was changed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e935ce7fbf9f51fb:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `1a3ecf35167772ff0d0248e3657c91ac50c4325e254214ebe3fda5159b360fb0`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

New finite disjoint stamp placement and exact controls address prior overlap/ignored-axis findings;59reportedtests and exact source required before explicit bounded reviewer-reported resolution. Exact repair accepted with reviewer-reported evidence; no maintainer rerun or closure of other findings.

### Assessment or prior finding

## 2fb8d019f6ca

Generator SHA256: `1a3ecf35167772ff0d0248e3657c91ac50c4325e254214ebe3fda5159b360fb0`.
Declared rule ID: `b1a2d9fb3e21`. Exact executed canonical rule-source SHA256: `bb6e38b7dc3193d85f4b7df6ad27868b76888a694c357aa70a1d1ebfa309a31a`. These are recorded as separate identities, not assumed to be interchangeable hashes.

**A1.1 — reproduced placement-contract violation.** 12/192 ordinary inputs have overlapping nonzero pixels in the stamped copies; 187 inputs are unique. The generator/notes promise collision-free placement, but its check considers existing anchors rather than reserving the whole future painted footprint symmetrically. All 192 generated inputs pass `self_check`.

Concrete case: **medium, seed 12, sample index 1012, no overrides**. Anchors at zero-based `(6,4)` and `(6,5)` produce a shared stamped nonzero cell `(7,5)`. See `checks/audits/2fb8d019f6ca.json#witnesses.stamp_overlap`. Actual Racket output is saved and executes without error. This does not prove wrong labels: stamp overlap still has deterministic reference behavior. It contradicts the advertised isolated-placement distribution and is invisible to its validator.

Suggested future repair: reserve the translated nonzero template cells for every placed anchor and check symmetric set intersection before committing a new anchor. Decide explicitly whether overlapping copies belong in the teaching domain; do not accidentally mix the two policies.

**A1.2 — reproduced ignored overrides.** At **medium, seed 7, sample index 19**, request `palette_size=4, n_distinct_colors=4`. The generator returns exactly the same grid as with no overrides, with only two nonzero colors (shape color plus the reserved anchor color). Dimensions are 12×11. The validator accepts it; actual Racket output is saved at `witnesses.ignored_overrides`. This is a requested-input contract failure, not a claim that the resulting grid is an invalid Racket argument.

**Checked nonfailures and limits.** All five canonical pairs pass the validator and match actual Racket output. No crash or output disagreement was reproduced. The 192-draw sweep is finite and does not estimate prevalence in an external training pipeline. Fixed color 8 is semantically meaningful here; indiscriminate nonzero-color permutation would be an invalid audit transformation. No palette-invariance defect is asserted for this task.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e935ce7fbf9f51fb-v0001/audit_assets.json), manifest SHA-256 `e8f836dee1a3fae7dd223d4dd2e9b29d8c6976c9453a3be20b4ad6f13e6226f0`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `95bd2548bd79c429eb3c5f27584de455463528a41c7697da90cf28dab26f1ad0`.

# Decisions and reversals

Assignment: `review-ccdb2f0e56d5f493`; repair `2fb8d019f6ca`; final generator SHA-256 `95bd2548bd79c429eb3c5f27584de455463528a41c7697da90cf28dab26f1ad0`.

## D1 — Preserve the actual rule, synchronize its selected text copy

The canonical Racket authority was the source of labels. The inherited selected target copy differed in comments, so I used the public authority-sync proposal and applied only its selected-file change. The normalized rule ID remains `b1a2d9fb3e21`; canonical source SHA remains `bb6e38b7dc3193d85f4b7df6ad27868b76888a694c357aa70a1d1ebfa309a31a`. The canonical ledger and archival `raw_code` remain unchanged. The selected JSON's hash changed from `9cbe3c24a082eea2270f2607909e3020db786b76cc77dff255b2a073c287909d` to `c6e776e5987e5d033301e9ded6857dd09139fb5abe67298bfa18a1cea6249cac`.

Rejected alternative: change the rule to justify existing sampler behavior or manually modify shared authority tooling. The actual defects were in generation, validation and text synchronization. Evidence: `checks/authority-proposal.json`, `checks/authority-apply.log`, final authority-sync stage.

## D2 — Make every retained control observable and exact

The former palette control did not guarantee its requested distinct color count. `palette_size` now means the exact number of nonzero input colors, including the fixed marker 8. A template therefore uses `palette_size - 1` colors; a distractor reuses that palette. The constructor places every chosen color before adding repeats, so all values 2–4 are possible even at the three-cell template minimum.

`n_distinct_colors` remains a compatibility alias, without becoming a duplicate axis. Conflicting alias/canonical values raise an explicit error. The four inert names `palette_kind`, `texture`, `position_bias` and `density` were removed from the advertised interface; accepting them silently would preserve a misleading contract. A future caller needing those controls should introduce defined observable behavior first.

Height 8–16, width 10–16, anchors 1–4, palette 2–4, template cells 3–8 and distractors 0–1 are all integer axes, and every advertised combination is feasible under the constructor. No structured incompatibility exception is needed. Seeds are Python integers; sample indices are nonnegative integers; difficulty is `None`, `easy`, `medium` or `hard`. Booleans and coercible strings/floats are rejected instead of silently converted. These guards were added only after the intermediate defect-lint result and the new regression failures demonstrated the gap.

Evidence: R1 in `REVIEW.md`; 37,530-draw final override report; `tests/test_stamp_contract.py`; retained before/intermediate failures.

## D3 — Use constructive disjoint placement

The prior asymmetric anchor test could accept intersecting stamp footprints, and a retry cap could return fewer anchors than requested. The new placement enumerates feasible row/column tilings and chooses a complete set of rectangles. It reserves the source bbox, requires each destination bbox to be in bounds and disjoint, and keeps the input distractor outside every destination rectangle. Anchor counts are therefore exact, including the smallest grid with the largest requested template/count.

Rejected alternatives: increase the retry limit, stop after a partial placement, or silently lower the count. None establishes the public exact-count contract. A general backtracking packer was also unnecessary for this bounded set of template boxes; finite tilings have a smaller and more inspectable failure surface. The independent review checked all 4,032 geometry configurations.

Tradeoff: arbitrary free-position placement is not sampled, and row/column alignment remains a spatial bias. The validator accepts some broader lawful arrangements; it is not an exact membership oracle for constructor support. Collision-free generation also leaves the semantics of transparent zeros and conflicting writes unlearned. This is a bounded distribution choice, not evidence that Racket cannot process overlap.

## D4 — Broaden shape support while retaining linked canonical profiles

The six-shape bank was replaced with connected growth. Ordinary even samples choose a canonical height/width pair, use two anchors and two template colors, and grow a 4–6-cell shape within 3×3. Ordinary odd samples use a 2×4 or 4×2 bbox, 5–8 cells, at least three anchors and one same-palette diagonal distractor. Explicit overrides extend the exact scalar range, including three-cell templates and one anchor.

The even profile protects recognizable canonical support; the odd profile supplies distinctions absent from all five canonical examples. The final linked-profile check records 35/60 exact matches and 36/60 envelope matches, compared with 7/60 and 13/60 before repair. Those rates are observations from pinned draws, not promises for every random sample or the meaning of the strict-domain hook. Both profiles operate in each difficulty band; no monotone human difficulty claim is made.

Rejected alternative: maximize visual diversity independently of rule teaching. More colors, sizes or random noise alone would not guarantee a surviving rival is refuted. Larger boxes were also deferred because they expand packing constraints and weaken the simple lesson argument without being necessary for the assigned defects.

## D5 — Make the production lesson and rotation policy explicit

The generator declares three demonstrations and a two-profile period. Production assembly takes four consecutive accepted indices and uses the last pair as query. Each complete window has two ordinary odd witnesses. Holding out any one pair leaves at least one witness among the three demonstrations, refuting all four declared canonical-fitting rivals at once.

The witness simultaneously distinguishes rooted four-connectivity from both whole-canvas and eight-connected extraction, more-than-two anchors, and a fixed 3×3 crop. The packer requires a translated distractor cell that remains visible outside true stamp rectangles; merely adding diagonal noise without this output distinction was rejected as insufficient.

The hook flags a rival only when it agrees with every demonstration and changes the query's true answer. A rival that survives demonstrations but gives the same query answer is not automatically a query ambiguity. The declarations reuse the same functions, and probes read those declarations dynamically. Four unique rivals appearing in three declaration dictionaries are not twelve independent hypotheses.

Both production and rotation policies were measured: 300 lessons / 1,200 Racket-labeled unique inputs and 1,200 rotations, all unambiguous; a separate seed-0 run covered both declared residues in all three bands, 6 production lessons / 24 rotations on six unique inputs. The acceptance log confirms all indices were consecutive and all 1,224 attempted pair appearances across the two runs were accepted. Random-census seeds are independently derived per band and lesson index; the fixed-seed run alone exhausts schedule residues at seed 0. These reports establish no all-seed theorem, and explicit overrides may disable the guarantee.

## D6 — Preserve failures and distinguish execution from inference

The first regression run, first after-battery, scalar guard failures, isolated pytest preflight failure, and independent probe mistakes are retained. Passing after fixing those issues does not erase their history. Direct Python oracles and packing matrices are described as differential checks; generated authoritative labels came from the selected canonical Racket program through the supported public runtime.

An early concern that an empty rooted component might crash was rejected after executing Racket: it returned a blank canvas. Rootless inputs stay outside the chosen sampler and validator, but are not mislabeled as a Racket failure. The byte-exact source and wrapped-callable hashes are separately identified because they hash different representations.

The test environment helper copies already installed dependency distributions into a new venv and records their hashes. It avoids relying on user-site pytest, network installation, or imports from another task's repository. The relocation replay uses this interpreter and the already verified host Racket executable, while all task and public runtime imports come from the freshly patched packet. No installed environment is included in the return.

## D7 — Keep the audit lanes findings-only

The two drawn targets stayed unchanged. C83-A1 identifies a canonical-fitting oblique-pair shortcut; C83-A2 reproduces an already documented parity restriction. A41-1 and A41-2 identify capped-area ranking and eight-neighbor connectivity alternatives. Each new claim has an exact input accepted by the target validator and actual Racket output. Source arguments explain why each missing distinction lies outside that sampler's constructive support; a learner's adoption of any shortcut remains unknown.

I did not patch these targets because that would change the assigned findings-only scope and combine unrelated approval decisions with the selected repair. Their finite test counts, ordered/rotated lesson differences and potential follow-up changes are in `AUDIT.md`.

## D8 — Preserve truthful solve exposure

The initial assigned blind puzzle was solved in its visible-only lane before source work. The later solve was prepared from the final generator bytes. It records earlier exposure `yes`, even though the isolated solver read only the visible challenge and public feedback during its attempt. Its notes disclose that the same agent retained conversational context from the earlier, different visible puzzle. Neither record is presented as a model benchmark; both have one genuine revision and three visible matches, and private correctness remains unknown.

## D9 — Keep the return compact and independently replayable

The return builder produces the source patch and INTAKE; neither is handwritten. Exact argument arrays and evidence paths are retained. Large success reports that differ only in metadata can be represented by a verified restoration delta with base/original sizes and SHA-256 hashes, rather than duplicating an entire report. All failed-run evidence remains available. The official evidence bundle supplies a manifest for the remaining check files, and restoration instructions explain the extra lossless delta.

The final source patch is applied from a newly initialized fresh `WORK/` Git root, every changed path is compared by hash, and task tests plus new reference generation are run from the relocated library. Rebuilding the reports must leave that checked patch byte-identical. The original attachment, assignment, audit identities, inherited finding records and shared source remain intact.
