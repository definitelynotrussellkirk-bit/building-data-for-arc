# Mirror Inside the Frame — current decisions

Selected repair: version **3.1.0**, generator SHA-256
`437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f`.
Canonical `RULE_HASH = 64f526c95424` is unchanged. These are proposed source
repairs; this review does not grant training approval or resolve audit metadata.

## Rule and domain

Inside one hollow blue (1) rectangle on black (0), reflect each yellow (4) cell
left-to-right about the frame's vertical axis. Paint orange (7) only at an empty
mirror target. Preserve yellow partners and yellow axis marks. The sampler uses
one frame, 1–7 interior yellow marks and at least one productive target. The
Racket authority also handles some multi-frame/no-op inputs outside this narrower
sampling grammar. Colors encode fixed rule roles; arbitrary palette permutations
are not lawful counterfactuals for this task.

## Decisions reversed by this review

- **Canonical profiles:** hard defaults previously had no canonical-scale draws.
  Every third ordinary sample now selects one of 9×11, 10×12 and 11×13, cycling
  across all bands; the other two thirds retain the prior difficulty ranges.
  Exact user overrides retain precedence. This restores canvas/palette profile
  support; it does not promise every canonical arrangement is sampled.
- **Teaching order:** the prior three-branch cycle could put a branch's only
  evidence in the query. Ordinary draws now alternate occupied-pair plus
  productive-target scenes and axis-mark plus productive-target scenes. Four
  consecutive accepted inputs contain two of each; any one held-out pair leaves
  both in three demonstrations. `EXAMPLES_NEEDED` remains 3.
- **Axis evidence:** an offset rectangle alone was a false witness. The witness
  now compares local and whole-grid predictions. Ordinary placements are
  horizontally off-center, and mark placement reserves an empty local target plus
  the whole-grid and top-to-bottom preimages that would let rivals paint it.
  The first repair lacked the direction reservation; an actual rotated-lesson
  failure required the additional reservation.
- **Spatial attribution:** the full semantic search found four rotated lessons
  ambiguous under a real input-only rival that paints only targets nearer to the
  frame than to yellow (with either tie policy). Ordinary axis draws now require
  height ≥5 and odd width ≥7, with a productive source one column from the axis,
  at least two cells from the horizontal borders, and an axis yellow on the same
  row. The target is distance 1 from yellow and at least 2 from blue, refuting both
  rivals. Either of the two odd draws retains this evidence after a query holdout.
  The two rivals and the fifth executable witness are declared explicitly.
- **Input contract:** seed and sample_index must be nonnegative plain integers,
  excluding bools, floats and strings. Validation returns detected grammar errors
  before indexing reflected coordinates; outside yellow marks no longer crash.

## Executable teaching contract

Eight pure diagnostic rivals cover identity, copying yellow, overwriting non-axis
partners, recoloring axis marks, whole-grid reflection, top-to-bottom reflection,
and two nearest-frame attribution rules with different tie policies.
The latter is named `vertical_empty` in existing receipts. Python rival predictions
are diagnostic; reference labels come from the unchanged Racket rule.

`lesson_identifiable` rejects a rival only when it fits all three demonstrations
and disagrees on the query. Answer-equivalent survivors are allowed. All three
canonical pairs admit the overwrite-partner, recolor-axis, whole-grid and
nearest-frame-with-ties shortcuts, so those four are explicitly declared in
`CANONICAL_SHORTCUTS`. The strict nearest-frame rival fits only two canonical pairs.

`LESSON_SCHEDULE_PERIOD = 90` is the least common multiple of the branch period 2,
profile period 9, origin period 5 and hard-count period 3. It describes deterministic
schedule residues, not repeated grids: random draws still depend on the complete
sample index. Fixed-seed schedule enumeration and finite rival censuses do not
prove all-seed or universal rule identifiability.

## Intentional restrictions and remaining decisions

All canonical inputs remain validator-accepted. Their exact arrangements are
outside ordinary support: they are horizontally centered and contain neither an
occupied pair nor an axis mark. Ordinary teaching scenes deliberately require
those distinguishing features. This restriction needs acknowledgment when choosing
an eventual curriculum; exact canvas/color profile support is the measured gate.

Strict direction reservations apply to ordinary draws. Explicit small/dense
controls can legitimately give weaker lessons: a 4×6 frame with seven yellow marks
has only one empty interior cell, and left/right and top-to-bottom reflection can
both fill it. The ordinary occupied branch also omits 4×5 frames because its two
interior rows cannot provide the required occupied and direction witnesses at once;
explicit lawful 4×5 requests remain supported. The required same-row axis pattern
and minimum 5×7 odd frame are additional ordinary-axis restrictions, not claims of
full layout support. Do not silently apply ordinary
rotation guarantees to arbitrary override bundles.

Prior audits `review-68e586aabe594108:v0001` and `review-921182f345e32906:v0001`
were leads for the profile, weak-witness and scalar defects. Their original
`needs_triage` records remain unchanged. Current fixes are candidates for a
maintainer to resolve against the new source and this return's measured evidence.

## Reproducers and proposed extension

Minimal cases: `counterexamples/review-0daf74b2dce0d3b4/`. Focused tests are under
`tests/`; `workspace/mirror_contract_probe.py` replays the validator, witness and
lesson failures with actual Racket labels and independently implemented rivals.

`workspace/parametric/` is a separate runnable prototype: reflection axis
(vertical/horizontal) and paint color (7/2) are fixed once per episode. The default
vertical/orange program is byte-identical to canonical Racket. Other settings are
proposals, not selected rules or approved training data. Public challenge files
contain visible demonstrations and masked query inputs only; hidden settings,
programs, query answers and rival evidence remain in private authoring artifacts.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-921182f345e32906:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `d90880567da7d2f2f8f49659fca648c072d2fb941def67ef1de7bb0e2d84cc0a`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused closure against accepted source 437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f: canonical profile mixture now reports 26/60 exact (14 easy, 6 medium, 6 hard) and 29/60 envelope; strict scalar checks reject invalid seed/index and negative indices. Five Racket-verified witnesses and an expanded nearest-frame rival inventory repair the earlier weak teaching evidence. Source-bound checks/after-verified/ profile_floor and semantic_gate receipts, 12/12 battery and 84 portable tests are reviewer-reported evidence; closure is not inferred from source edits or generic approval. Finite profile support and declared-rival coverage remain stated limits.

### Assessment or prior finding

## 72f0b65569a4

**Source inspected:** generator SHA-256
`d90880567da7d2f2f8f49659fca648c072d2fb941def67ef1de7bb0e2d84cc0a`.
No files under this target were modified.

**Reproduced defect — hard-band canonical-profile gap.** The strict profile gate
accepted all 3 canonical inputs, but among its pinned 20 draws per band it found
exact canonical profiles in easy 4/20, medium 1/20, and hard **0/20**; hard also
had 0/20 inclusive-envelope hits.  Total support was 5 exact and 17 envelope
hits in 60 draws.  This is a training-domain gap rather than a wrong label: the
hard curriculum moves entirely beyond the canonical 9×11–11×13, three-color
profile range.  Evidence:
`checks/audit/72f0b65569a4/checks/72f0b65569a4_audit_profile_floor.json`.

**Semantic evidence gap.** Four useful branches fire frequently, but all four
witnesses have no `WITNESS_RIVALS` claim, so the strict semantic gate reports
WARN rather than proving that a plausible shortcut is refuted.  It measured
600/600 strict-lawful draws; the issue is falsifiability, not generation
crashes.  Evidence:
`checks/audit/72f0b65569a4/checks/72f0b65569a4_audit_semantic_gate.json`.

**Additional strict-input issue.** Defect lint reproduced acceptance of invalid
seed/sample-index scalars, including negative `sample_index`.  I did not find a
wrong Racket output or a frame-reflection counterexample.  Compact summary:
`checks/audit/72f0b65569a4/audit-summary.json`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-921182f345e32906-v0001/audit_assets.json), manifest SHA-256 `0be5477ef573a64120b4c1a6130f602d2c19372771619ad2bdf6649e865a1c1f`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f`.

# Decisions for 72f0b65569a4

Assignment: `review-0daf74b2dce0d3b4`. The selected repair remains version `3.1.0`; the canonical Racket rule remains unchanged with normalized `RULE_HASH = 64f526c95424`. The exact canonical program SHA-256 is `3ca01023e0730d43844cac3ece57bfa2b777270780c3509e52b25eb23b0d7934`.

Selected source SHA-256: **`437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f`**. The nearest-frame repair is implemented and its 40 focused regression cases passed. The final battery has **12/12 green stages**, both final censuses pass, and the complete portable task suite passes **84/84** with no failures, errors or skips. Source `992bc69af4dcc2734a08775cdbe855c15a291ff4b8e70d5eb72b8282215194ee` and the file named `mirror-contract-final.json` are intermediate evidence in this return; that filename does not make its results a check of the selected source above.

## Rule and scope

Within one hollow blue frame, each yellow mark is reflected across the frame's vertical axis. An empty reflected target becomes orange; a yellow mirror partner or a yellow mark on the axis stays yellow. The input generator constructs examples; the selected Racket program remains the output authority. Diagnostic Python rivals are hypotheses used to challenge lessons, not replacement label authorities. See [generator.py](repo/generators/72f0b65569a4/generator.py), the source identities in [the focused probe](checks/diagnosis/mirror-contract-verified.json), and [the canonical program comparison](checks/parametric/suite/private/canonical_check.json).

The teaching grammar keeps one complete frame, input colors `{0, 1, 4}`, one to seven interior marks, and at least one productive off-axis target. It is narrower than the Racket oracle's executable domain. For example, retained tests distinguish a rejected multi-frame or no-mark teaching input from whether the oracle still executes that input. Neither validator acceptance nor correct individual labels establishes a sufficient complete lesson.

## Distribution choices and reversals

| Choice | Earlier behavior or alternative | Decision and reason |
|---|---|---|
| Canonical-scale profiles in every band | Difficulty defaults moved hard examples entirely beyond the canonical canvas envelope in the retained audit samples. An opt-out would preserve that omission. | Every `sample_index % 3 == 0` draw anchors a canonical canvas: `9 x 11`, `10 x 12`, and `11 x 13`, cycling over nine indices. The other draws retain larger difficulty-dependent canvases. Explicit compatible axis controls retain precedence. This addresses the assigned profile requirement without claiming full canonical arrangement support. |
| Three demonstrations and one query | A three-branch schedule could leave the only center-axis example as the query. Increasing the demonstration count was another possible response. | Keep `EXAMPLES_NEEDED = 3` and alternate occupied-pair draws at even indices with center-axis draws at odd indices. Four consecutive ordinary draws contain two opportunities for each exception; any one holdout leaves an example of both in the remaining three demonstrations. |
| Productive mark placement | Merely producing a lawful frame can allow identity or yellow-copy shortcuts. | Reserve an empty off-axis mirror target for a yellow source. This preserves a visible addition and recoloring on every ordinary draw. |
| Frame-local axis evidence | The original witness used an off-center frame as a proxy for prediction disagreement. A lawful off-center fixture still gave the same output under whole-grid reflection. | Reserve the whole-grid reflection preimage when capacity permits, and define the witness by actual disagreement between the declared transformations. An off-center bounding box by itself is insufficient evidence. |
| Direction evidence | The first repaired schedule still allowed top-to-bottom reflection to fit all demonstrations while changing a held-out query. | On ordinary draws, also reserve the source cell that a top-to-bottom reflection would need to paint the chosen horizontal target. The resulting contrast concerns output predictions, not just dimensions or an orientation label. |
| Small ordinary occupied frames | A `4 x 5` frame has only two interior rows and one nonaxis horizontal mirror orbit per row. | Exclude this frame size for ordinary occupied-pair draws: reserving an occupied pair leaves no room for the required direction-distinguishing productive configuration. Keep compatible explicit controls separate from this ordinary teaching restriction. |
| Exact controls | Rejecting all tight but lawful controls would make lesson construction easier. | Preserve the advertised exact dimension and mark controls when they fit the grammar. Tight explicit overrides may provide weaker teaching evidence. A lawful `4 x 6` frame with seven marks can remain direction-ambiguous; validator success for it is not a claim of query-rotation identifiability. |

The earlier source's difficulty ranges and schedule are observable in the retained baseline. Intent beyond its comments and historical review statements is unknown; the repair does not attribute an unstated curriculum rationale to its author. The two prior audit leads and their original source bindings are retained in [review_index.json](repo/generators/72f0b65569a4/evidence/review_index.json).

For a productive target `t`, reserving the corresponding whole-grid preimage prevents that rival from painting `t` from a different yellow source. Reserving the top-to-bottom preimage does the same for the wrong reflection direction. These reservations constrain the ordinary sampler. They are not additional Racket-rule conditions. Explicit overrides intentionally do not inherit every ordinary contrast guarantee. The selected source's `_place_marks` and `generate` functions state that boundary.

The four-grid argument concerns consecutive ordinary generated inputs. Production materialization can reject or deduplicate draws and thereby skip indices. Consequently the actual accepted demonstration/query assembly still needs the rival check; a schedule description alone cannot certify exported lessons.

## Additional nearest-frame shortcut and its repair

The completed battery under `checks/after-complete/` belongs to intermediate source `992bc69af4dcc2734a08775cdbe855c15a291ff4b8e70d5eb72b8282215194ee`. It has **11 green stages and one failed stage**, `semantic_gate`, with process exit 1. Its six declared competitors found no ambiguity in 12 production lessons or 48 declared-rival query rotations, but the broader searched-rival evidence produced genuine ambiguity warnings. This is retained failure evidence, not a final pass. See [result.json](checks/after-complete/result.json) and [the semantic report](checks/after-complete/checks/72f0b65569a4_after_semantic_gate.json), especially `audits[0].lessons.searched_rivals`.

The input-only explanation is to perform the intended empty-target reflection but paint a target only if it is at least as close to the blue frame as to a yellow source. The strict tie variant uses `<` instead of `<=`. These are now declared competitors `nearest_frame_with_ties` and `nearest_frame_strict`, bringing the distinct task rival inventory to eight. The ties variant fits all three canonical pairs and is the fourth entry in `CANONICAL_SHORTCUTS`; the strict variant fits two of three and remains a general lesson competitor. Finding this pair demonstrates the limitation of the earlier six-rival pass.

The selected ordinary-draw restriction refutes both: each odd/axis scene has a frame at least five rows high and seven columns wide, with odd width; a productive source lies one column from the axis and at least two cells from the frame border; a yellow axis mark is placed on the same row. The correct target is then distance one from that yellow axis mark and at least distance two from blue. Either of two such odd scenes can supply the witness after a single holdout. The fifth semantic witness is `nearest_frame_not_required`, with both nearest-frame rivals declared in `WITNESS_RIVALS`. A primary orientation is skipped if its required axis mark collides with the reserved whole-grid preimage. These restrictions apply only to ordinary draws.

The retained [focused regression receipt](checks/nearest-repair-focused.xml) records **40 passed, 0 failures, 0 errors, and 0 skipped**, across `test_distribution_regressions.py` (16 cases), `test_mirror_contract_regressions.py` (15), and `test_nearest_object_regressions.py` (9). The selected source is `437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f`. The final battery has **12/12 green stages**; profile support is **26 exact / 29 envelope hits in 60 draws**, with per-band support and no opt-out. The two final censuses passed as reported below. The complete portable task suite also passes **84/84**, with zero failures, errors or skips; see [its receipt](checks/task-tests-verified/result.json). The geometry argument and focused pass do not establish all-seed or all-rival correctness.

## Material support limitation

The three canonical inputs in `checks/diagnosis/mirror-contract-final.json` are:

| Canonical record | Canvas | Frame horizontally centered | Occupied mirror pairs | Center-axis marks |
|---|---|---|---:|---:|
| `records[0]`, train pair 0 | `9 x 11` | Yes | 0 | 0 |
| `records[1]`, train pair 1 | `10 x 12` | Yes | 0 | 0 |
| `records[2]`, test pair 0 | `11 x 13` | Yes | 0 | 0 |

The validator accepts these inputs. The ordinary sampler deliberately includes an occupied pair or a center-axis mark, so it does **not** reproduce those exact canonical arrangements. Profile anchors restore canonical canvas-size and three-color profile support, not full canonical input support. Additional preimage reservations and the nearest-frame witness further shape the ordinary distribution. These are material teaching restrictions, and the return must not describe their profile results as exhaustive or full canonical support.

The profile floor measures height, width, and distinct-color count together. Its assigned threshold is at least one exact-profile hit per band in 20 draws, with pooled exact support at least `3/60` and envelope support at least `15/60`, assuming all draws succeed. These are acceptance requirements from [DUTIES.md](DUTIES.md), not final measured counts for source `437d196...`.

For intermediate source `992bc69...`, the retained [profile-floor report](checks/after-complete/checks/72f0b65569a4_after_profile_floor.json) measured 25 exact and 27 envelope hits in 60 draws: easy 13 exact / 15 envelope in 20, medium 6 / 6 in 20, and hard 6 / 6 in 20. Its semantic report also measured 600/600 strict-lawful draws. These are intermediate successes within their stated metrics; the same source's battery failed the broader semantic gate, and the counts do not transfer to later generator bytes.

## Validation and portable regressions

The validator now reports malformed grammar and outside marks before computing reflected coordinates. The original positive out-of-bounds marker caused `IndexError` in both `self_check` and `strict_canonical_like`; the retained intermediate focused probe records rejection without exceptions for all six calls across three adversarial rectangular inputs. Inputs with invalid seed/index scalar types, negative values, unknown controls, and incompatible dimensions remain explicit errors. See `validator_results` in [the focused evidence](checks/diagnosis/mirror-contract-final.json).

The retained task-local test was ported to `reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, and `load_selected_generator`. Public `Catalog.apply` and `Catalog.generate` replace private script imports. Canonical exactness, base authority equality, deterministic fresh returns, RNG isolation, exact axes, impostors, broader oracle-domain cases, and materialized lessons remain covered. Repeated A/B/A applications share a reference bridge; the public API purity assertion concerns caller-owned Python inputs, not inspection of private Racket values. Final test counts must come from the final staged receipt; earlier green test runs do not certify later source bytes.

## Evidence scope and remaining counts

| Evidence | Source and population | Recorded result |
|---|---|---|
| [mirror-contract-before.json](checks/diagnosis/mirror-contract-before.json) | Baseline `d90880567da7d2f2f8f49659fca648c072d2fb941def67ef1de7bb0e2d84cc0a`; easy seed 2, start 0; 11 records, one lesson, four holdouts | Five failure entries: two validator exceptions, one false witness, and the hook/rival reports of one ambiguous rotation. |
| [mirror-contract-after.json](checks/diagnosis/mirror-contract-after.json) | First intermediate `4ed08f875dd6149aaeb1dd15aff530e5fcc87668a8abef13fdaa5440514bc83f`; seeds 0 and 2, all bands, starts 0–5; 61 records, 36 lessons, 144 holdouts | Four failure entries describing two direction-ambiguous rotations; retained rather than overwritten. |
| [mirror-contract-final.json](checks/diagnosis/mirror-contract-final.json) | Later intermediate `992bc69af4dcc2734a08775cdbe855c15a291ff4b8e70d5eb72b8282215194ee`; same 61-record, 36-lesson, 144-holdout focused scope | Zero failures against six distinct transformations, represented by 21 namespaced declaration/diagnostic entries. This does not cover the later nearest-frame rivals. |
| [after-complete/result.json](checks/after-complete/result.json) | Same `992bc69...` intermediate source | Completed nonpassing battery: 11 green stages, one semantic-stage failure. Preserve the searched-rival findings. |
| [nearest-repair-focused.xml](checks/nearest-repair-focused.xml) | Selected `437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f`; three regression files | 40 passed, no failures/errors/skips. This is a focused test receipt, not the final battery or census. |
| [Final production census](checks/lesson-census-final.summary.json) | Selected `437d196…`; 100 lessons per band, 3 demos and 1 query | 300/300 lessons, 1,200/1,200 rotations; 1,193 unique inputs. Both verdicts `no_ambiguity_found`; zero errors/warnings. |
| [Final schedule census](checks/schedule-census-final.summary.json) | Selected `437d196…`; 90 starts × 3 bands at seed 0 | 270/270 lessons, 1,080/1,080 rotations; 272 unique inputs. `complete_fixed_seed`; both verdicts `no_ambiguity_found`; zero errors/warnings. |
| [Final battery](checks/after-verified/checks/72f0b65569a4_after_battery_summary.json) and [profile floor](checks/after-verified/checks/72f0b65569a4_after_profile_floor.json) | Selected `437d196…`, with matching fixed-seed receipt | 12/12 stages green; 600/600 strict-lawful draws. Exact/envelope: easy 14/17 of 20, medium 6/6 of 20, hard 6/6 of 20; pooled 26/29 of 60. No failures or opt-out. |

The declared period is `90 = lcm(2, 9, 5, 3)`: branch parity, canvas-profile schedule, origin mode, and the hard-band mark-count cycle. It describes the semantic index schedule, not byte-for-byte repetition of random grids. A complete fixed-seed enumeration checks starts 0–89 and their allowed holdouts across the requested bands using actual accepted inputs. It does not exhaust seeds, arbitrary rejection patterns, all inputs, or undeclared rivals. Random censuses and fixed-seed residue enumeration answer different coverage questions. Neither grants universal identifiability.

## Parametric assessment

**Status: proposed, unselected task-local prototype.** Two meaningful parameters are suitable: frame-local axis (`vertical` or `horizontal`) and output paint color (`7` orange or `2` red). Each is fixed once per episode. The explicit/default path and seeded parameter selection preserve that episode-level contract. The selected canonical generator API and Racket authority remain separate. See [the prototype README](repo/generators/72f0b65569a4/workspace/parametric/README.md).

The default vertical/orange program is byte-for-byte the canonical source, SHA-256 `3ca01023e0730d43844cac3ece57bfa2b777270780c3509e52b25eb23b0d7934`. Every chosen output and competing parameter prediction in the retained evidence comes from actual Racket execution, with content-addressed reuse of previously executed results; there is no Python label fallback.

| Retained run | Scope | Recorded outcome |
|---|---|---|
| [suite receipt](checks/parametric/suite/private/receipt.json) | Seeds 0 and 17; all four settings; eight episodes, 24 demonstrations, eight queries | Passed; 24 parameter-rival comparisons, all competing settings refuted; 39 actual execution rows and 96 cache hits. |
| [seeded receipt](checks/parametric/seeded/private/receipt.json) | Seed 20261019; one episode with parameters sampled once; three demonstrations, one query | Passed; three parameter-rival comparisons; 23 actual execution rows. |
| [integrity receipt](checks/parametric/integrity.json) | Hash/binding checks of both retained runs | Passed; 128 plus 16 = **144 retained output bindings** verified. These are bindings, not 144 independent Racket executions or 144 episodes. |

Exact variant programs and their distinct hashes are retained in each evidence run's `private/rules/` and `program_hashes`. Both runs execute all three default canonical comparisons and retain a witness distinguishing all six pairs of parameter settings. The suite and seeded manifests bind the source files, runtime, programs, private labels, and public challenges.

The prototype sampler is independent of the selected generator and uses the same input distribution for different parameter settings at a given seed. Its productive asymmetric corner, empty targets along both candidate axes, and empty diagonal partner are intentional teaching constraints. This is finite evidence for four settings and the retained seeds within a small one-frame grammar; it does not establish unrestricted parameter identifiability or full canonical-domain support. Only individual `public/episode-NNN.json` files are model-visible; settings, programs, hashes, rival predictions, and query labels remain private authoring evidence.

## Prior audits, rejected alternatives, and authority boundaries

The prior leads `review-68e586aabe594108:v0001` and `review-921182f345e32906:v0001` remain `needs_triage` in [review_index.json](repo/generators/72f0b65569a4/evidence/review_index.json). They are source-bound historical findings, not fresh measurements of the repair. Their assets and failures are retained. An earlier intake acceptance entry or this repair does not independently resolve their audit status.

The repair rejects several shortcuts in the review process: changing the canonical rule to suit an easier sampler; waiving the assigned profile floor; treating geometric witness frequency as proof of complete-lesson teaching; rejecting every surviving rival even when its query answer is equivalent; and silently dropping lawful explicit controls to improve lesson statistics. The proposed extra export/admission gate is discussed separately in [QUESTION_ANSWER.md](QUESTION_ANSWER.md).

No training admission or approval metadata is edited by this work. Finite reviewer checks, successful prototype execution, a generator repair, and admission of model trajectories are distinct decisions. Claims about Qwen3.5-9B learning gains remain unmeasured; this review supplies reproducible data-quality defects and bounded repairs.

## Final replay and acceptance

The repaired task has no remaining failing verification gate. Its exact official
source delta passed a fresh extraction, an explicitly verified Git root,
`git apply --check`, actual application, and all 18 changed-file hashes, including
13 new files. All 84 task tests passed again there. The source and the completed
exposed solve remain bound to `437d19653cc59e2bac06cd40ab0f31685edf5488a82060e35d96f95e9b0ef35f`.
`checks/replay/` retains the actual commands, outputs, file identities and runtime
location; no old repository source was used for the fresh tests.

The clean extraction runs on a separate temporary filesystem because the shared
overlay repeatedly exhausted its inodes. Reusing the installed Python packages
and Racket executable preserves dependency availability without copying prior
source into the fresh tree. The original extraction was released only after its
unchanged input ZIP, officially validated delta and all changed-file backups were
verified. No unrelated workspace or temporary files were removed.

The initial replay-helper refusal was a portability check on case-distinct file
names, not a malformed patch. The fix keeps strict portable behavior by default
and makes its exception contingent on an actual filesystem probe; returned
archive validation stays strict. An expected-files manifest additionally checks
the exact patch path set and each post-apply byte hash. The original helper,
initial refusal and 12 passing guard regressions are retained in `checks/`.

Acceptance is **routine for the selected repair**. Both required read-only audits
are complete and have independently documented findings for maintainer triage;
those unselected sources were not edited. The parametric extension remains a
proposed prototype, with no catalog selection or training admission change.
