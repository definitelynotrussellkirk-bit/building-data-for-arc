# Current notes: 0b8ba9bb3c63 (4.1.0)

## Canonical semantics and authority

Original family: `training:6ffe8f07`. A cyan rectangle emits yellow horizontal
and vertical bands; red rectangles are transparent, while other objects clip
each ray and are restored with their original colors. The selected canonical
Racket rule remains `757441c9ab4a` (full normalized hash
`757441c9ab4aa17070a3826de76e0b0f74e66636398f3f3aaa4392e47af17bcb`).
The exact canonical source SHA-256 is
`e73f49035ca5d73e3c73948c0b15e2b6f1985366674de313cbf978463088d977`.
Two selected base authority `target_code` copies were synchronized to that
exact text; the canonical ledger and archival `raw_code` were not changed.

## Current repair: review-df70d81c42d5aa27

Baseline 4.0.0 source hash:
`06b6e79989cf7d2b850ff4aa327930c33cb603c3e3089c000662fa4a6420f965`.
Final 4.1.0 source hash:
`480c7ae04f31b1cd2d48c8b4af0dd9f71ef9365507a557c9fc6d60cb44ddc20d`.

The retained open audit `review-faed4b356c087333:v0001` was reproduced afresh:
seed 8/default, samples 0,1,2 provide public scenes fitting the blue-only-blocker
rival, while sample 3 is generalized and differs in 18 cells. The exact lesson
and selected-Racket results are in `counterexamples/blue_only_lesson_seed8.json`.
This is an ordinary emitted lesson, not a validator-only construction.

Ordinary generation now uses `public, generalized, public, generalized,
generalized`, indexed by `(seed + sample_index) % 5`. Every emitted generalized
scene must actually differ from the blue-only rival: a non-blue object at a
border without a shadow is insufficient. Four consecutive successful draws
contain at least two witnesses, so holding out any pair leaves a witness among
the other three. The ordinary family ratio stays 2:3. Explicit family overrides
bypass the schedule, and arbitrary subsets or skipped/reset indices need their
own lesson checks. `lesson_identifiable` checks actual labeled pairs.

`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` bind the same
one rival, with a real witness predicate. The rival clips only on blue objects
but still restores every opaque object. It matches all 12 canonical pair
occurrences (6 unique inputs); declaring it three times does not create three
independent competitors. Literal integer seeds (including negative seeds) are
accepted; Boolean/coercible non-integers and negative/non-integer indices fail.

## Evidence and limitations

The strict battery passed 12/12 stages; task-local portable tests passed 61
tests and 49 subtests, without skips. The real-Racket seed-8 replay now has
family sequence generalized/generalized/public/generalized and mismatch counts
`[1,31,0,2]`, so all four query placements retain a refuting demonstration.
The source-bound large census covers 300 production lessons, 1,200 distinct
inputs and 1,200 rotations, with no ambiguity against the declared rival.
The fixed seed-0 schedule census covers five residues in all three bands:
15 lessons, 60 rotations, 60 pair occurrences and 16 unique inputs. These are
finite checks, not proof against every possible hypothesis or geometry.

The review's `checks/lesson-regression/`, `checks/after/`,
`checks/lesson-census.summary.json`, `checks/schedule-census.summary.json`, and
`checks/task-tests/` retain exact commands and results. The reusable
`workspace/probe_blue_only.py` obtains labels via public selected-Racket apply.
The test suite uses public `reviewer_support` root/canonical/module helpers.
Old evidence and associated notes retain their original timestamps in
`evidence/associated_notes.jsonl`; the maintainer's audit/approval dispositions
are not modified. This review proposes resolving the reproduced blue-only
finding after intake, without claiming unrelated audit closure.

## Separate parametric proposal

`workspace/parametric/` implements `beam_axes = both | horizontal | vertical`,
fixed once per episode. `both` is exact canonical source. Inputs are independent
of setting; all labels and rival predictions execute the included Racket bridge.
Three seeds × three settings produce nine episodes with 9/9 production and
36/36 query-placement checks passing against the two alternative settings.
Public challenges omit parameters, source and query answers. The constructor
uses a deliberately narrow four-blocker/five-red template. See its README and
the review's `checks/parametric/evidence-final/verification.json`.

Status: runnable, proposed, **unapproved**. It does not change canonical rule
selection, the production generator API, or training admission.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. The twelve focused naming/writer checks passed across six tasks. This correction does not approve the prototype or rerun its full repair battery.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-faed4b356c087333:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `06b6e79989cf7d2b850ff4aa327930c33cb603c3e3089c000662fa4a6420f965`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve blue-only clipping lesson ambiguity: 4.1.0 supplies a non-blue shadow witness in every three-demo window; exact retained seed8 regression, reviewer61 tests+49 subtests,300 lessons/1200 rotations and all period5 starts pass. Current source 480c7ae04f31b1cd2d48c8b4af0dd9f71ef9365507a557c9fc6d60cb44ddc20d. Evidence remains reviewer-reported and finite; no universal or training-admission claim.

### Assessment or prior finding

## 0b8ba9bb3c63

**Reproduced ordinary lesson ambiguity: clipping is attributed to blue rather than the non-red blocker role.** Target source SHA-256 `06b6e79989cf7d2b850ff4aa327930c33cb603c3e3089c000662fa4a6420f965`; selected/executed canonical rule hash `757441c9ab4a`; actual executed rule-text SHA-256 `1fd0b769321c4e1e0e50fc1dbfb5ea510c27709fcad3ede959d318e292d1bced`.

At seed **8**, default difficulty, no overrides, sample indices **0, 1, 2** are three ordinary public-family demonstrations, and consecutive index **3** is an ordinary generalized-family query. All four inputs pass `self_check`. A deliberately constructed rival—only blue(1) clips the cross, restore every blocker rectangle, keep red(2) transparent—fits **3/3 actual Racket demonstration outputs** but differs from the actual query output at **18 cells**. The generator declares `EXAMPLES_NEEDED = 3`; this is the corresponding three-demo/one-query consecutive assembly, with no scene override or hand-edited query. The rival also fits all **12 canonical pair records / 6 unique labelled inputs** inspected. Racket independently agrees with the Python mirror on the retained four-input lesson.

This is a finite teaching ambiguity, not a wrong reference label or a claim that every lesson fails. Generalized draws supply the needed color-role counterexamples; the problem is that the first three public demonstrations can omit them before a generalized query. A targeted improvement would declare the blue-only rival and ensure that a query needing a non-blue clipping role has a prior demonstration establishing that role, or reject/resample that lesson under its declared export policy. The target source was left unchanged.

**Bounded method and limits.** Initially inspected **24 ordinary draws**, seed0/indices0..23: 5 public and 19 generalized, all validator-clean; the blue-only rival matched the mirror on the 5 public draws, and no failing consecutive window was found in that range. Then inspected only family-choice metadata for seeds1..8, four positions each, and materialized the four ordinary scenes at the first matching seed8. Total scene draws: **28**. This adversarial seed selection establishes a concrete failure, not its prevalence. Reference checks cover **17 retained inputs**: 12 canonical records, one validator-admitted color-role counterfactual, and the four ordinary lesson inputs. No battery or source edit was performed.

Evidence: `checks/audit/0b8ba9bb3c63/lesson.json` retains the four exact generated inputs, Racket outputs, rival predictions, all differing query cells and source/rule hashes. `lesson-racket.json` is the public reference-execution receipt; `lesson_probe.py` reproduces the directed family search and lesson; `verify_lesson.py` checks actual Racket labels. `probe.json` and `racket.json` retain canonical and initial bounded diagnostic evidence. Exact commands, working directories, exit codes and recorder evidence are in `checks/audit/0b8ba9bb3c63/commands.json`. The initial relative payload-interpreter path error is preserved under `prepare/` and corrected under `prepare-corrected/`; it is an audit launcher mistake, not a generator failure.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-faed4b356c087333-v0001/audit_assets.json), manifest SHA-256 `d54b02c3c3ad601067a98c47f5c3d7f95d845da92a25a4570a206f1c9072e098`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Current alternative transparent-color proposal

Current selected source 480c7ae04f31b1cd2d48c8b4af0dd9f71ef9365507a557c9fc6d60cb44ddc20d already has blue-only shortcut/scalar repair and beam_axes prototype. Returned repair is bound to superseded 06b6e79989cf7d2b850ff4aa327930c33cb603c3e3089c000662fa4a6420f965 and would remove current lesson_identifiable hook/change schedule and helper return contract. Preserve as needs_evidence proposal; new transparent_color extension may be rebased independently. Exact source-bound proposal: `generators/0b8ba9bb3c63/workspace/proposals/465e544783c5c91bec80ff11a7ef7fe8bc16c303cc81c2c71b8de70b2ce884ac/manifest.json`. Both new peer audits remain separate unresolved findings; earlier main audit decisions are unchanged.

## Current reviewer considerations

Source SHA-256: `480c7ae04f31b1cd2d48c8b4af0dd9f71ef9365507a557c9fc6d60cb44ddc20d`.

# Decisions for 0b8ba9bb3c63

## Intent and implementation plan

The packet prioritizes a small parametric extension of training:6ffe8f07. Build an unapproved task-local `beam_axes` prototype first, with `both` as its canonical default and `horizontal`/`vertical` as alternatives. Preserve the cyan source, per-ray clipping, red transparency, and restoration of opaque objects. Execute the emitted Racket for all retained labels. Supply demonstrations that distinguish every declared parameter alternative, public/private file separation, and portable tests.

Next repair measured canonical issues: reproduce the retained blue-only blocker shortcut on ordinary seed 8; replace independent family selection with a five-position public/generalized schedule; require an observable non-blue blocker counterexample in each generalized draw; expose executable semantic/rival declarations; reject invalid scalar seed/index inputs; synchronize selected authority text without changing the canonical rule or archival raw text. Run focused regressions, the strict battery, production lesson/query-rotation census and all fixed-seed schedule residues. Then finish the exposed solve, both findings-only audits, and exact fresh-packet patch replay with focused tests.

## Distribution choice and alternatives

Use `public, generalized, public, generalized, generalized`, rotated by `seed % 5`, for ordinary consecutive draws. This preserves the existing 40%/60% population while ensuring every four consecutive accepted draws has at least two generalized witnesses. Holding out any one pair leaves at least one witness in the three demonstrations. This guarantee assumes all four generated inputs are accepted and assembly preserves consecutive indices; saved census receipts record actual accepted indices and rejections. Arbitrary externally selected subsets are not guaranteed identifiable.

The old independent 2:3 family draw permits three public demonstrations followed by a generalized query. Keeping randomness and adding only rival metadata detects the defect without fixing it. Raising the demonstration count increases cost and still leaves a random omission probability. Forcing all draws generalized discards canonical support. The fixed semantic schedule retains random geometry and palettes within its constrained positions. Exact family overrides remain available and bypass the ordinary schedule; users assembling override lessons must check their own coverage.

## Boundaries

Canonical labels still come from the unchanged selected Racket rule. Python mirrors and rivals support validation and sampling decisions; they are not reference authorities. Source version will advance to 4.1.0 for changed sampling behavior, and source hashes bind the exact implementation. The existing tests/ file is patchable and will be migrated to the public portable helpers; no frozen root fixture exists for this task. The test's archival raw-code check will compare normalized semantics, while selected target text must match canonical exactly.

Prior audit `review-faed4b356c087333:v0001` is a lead, not fresh evidence. Current-source reproduction, source-bound regression results, and finite Racket-labeled census results will support the proposed resolution. This return does not modify an approval ledger or declare the maintainer's audit disposition resolved.

## Implemented result and evidence

The planned schedule and strict scalar validation are implemented in version
4.1.0, generator SHA-256
`480c7ae04f31b1cd2d48c8b4af0dd9f71ef9365507a557c9fc6d60cb44ddc20d`.
Before the repair, the independent Racket-backed seed-8 probe found rival
differences `[0,0,0,18]`; after it, the differences are `[1,31,0,2]`.
The focused semantic regression first failed for the missing demonstration
witness and then passed all 27 task-local cases. Its 58 distinct generation-call configurations
cover two seeds, three bands, five consecutive starts and explicit overrides.
Those calls can produce duplicate input grids (including default/medium and
public-family overlaps); 58 is not a distinct-grid count. See
checks/lesson-regression/count-clarification.json.

Every final strict battery stage passed (12/12, zero advisory). The larger
source-bound Racket census materialized 300 lessons/1,200 distinct inputs and
checked 1,200 query rotations; no declared-rival ambiguity or execution/scoring
errors were found. A separate fixed seed-0 enumeration covered all five schedule
residues in three bands: 15 lessons, 60 rotations and 16 distinct inputs.
The one rival is shared across three declaration namespaces. These are finite
measurements and do not certify all seeds or undeclared hypotheses. The complete
portable task suite passed 61 tests and 49 subtests with no skips. Exact command
indexes and receipts are in `RESULTS.json` and `checks/`.

The baseline battery exposed two additional concrete issues: invalid scalar
inputs were accepted (13 failing focused checks), and two selected base files
differed from canonical source by formatting. Scalar checks are now 14/14 green.
The supported authority-sync proposal/application changed only the two selected
`racket_target.target_code` strings. Exact canonical source remains
`e73f49035ca5d73e3c73948c0b15e2b6f1985366674de313cbf978463088d977`;
normalized semantics, the ledger and archival `raw_code` remain unchanged.
An incorrect first apply invocation used `--out`; it was rejected, and the
corrected application omitted that dry-run-only argument. Recovery originals
were preserved under `checks/authority-recovery/`, with the original location
documented in `REVIEW.md`.

## Parametric rules assessment and implemented boundary

`beam_axes` is suitable because it changes which emission bands execute while
preserving the family's object roles, clipping, red transparency and object
restoration. The proposed settings are `both` (exact original/default),
`horizontal`, and `vertical`. The two alternative programs replace only one
traversal range with an empty list. The ordinary production API and canonical
selection were not extended or relabeled.

The prototype chooses the setting once per episode when requested by seed,
then uses that fixed Racket program for all three demonstrations and the query.
Separate deterministic seed domains choose setting and geometry. Input grids
are identical across settings at a fixed seed, preventing an input-only setting
cue. Every input contains observable horizontal and vertical activity, partial
blocker clipping, reached red and occluded red. Each demonstration therefore
distinguishes the declared settings before a query needs that distinction.

The chosen small constructor has one cyan emitter, four 2×2 blockers and five
red rectangles, with random positions, blocker colors, rotations/reflections,
and 23–27 sized demonstration grids. The 30×30 query exercises longer rays in
the same rule family. This template is intentionally narrower than the canonical
generator, so approval and training admission remain separate decisions.

Retained evidence at seeds 11,29,47 covers all three settings: nine episodes,
36 pair occurrences on 12 distinct inputs, 108 episode Racket applications,
and 12 canonical occurrences on six distinct inputs. Nine production lessons
(18 rival checks) and 36 query placements (72 rival checks) pass. Nine focused
tests plus 24 subtests pass. The initial missing-feature failure, exact-source
formatting failure, and export runtime-identity property error are preserved;
the export error has a failing-then-passing regression. The final artifact audit
checks all public/private projections, exact program hashes and runtime identity.
See `checks/parametric/commands.json`, `artifact-audit.json`, and
`evidence-final/verification.json`.

## Portability, solve discipline, and remaining work

The old task test used a repository-only base-data path. It now uses public
`reviewer_support` discovery and canonical helpers while preserving all eleven
test methods (eight method bodies unchanged). The lesson test was moved from a
temporary root tests path into the allowed task tests directory; the old command
receipts retain their actual executed paths. The portable isolated suite proves
collection of all four task test files, including the prototype tests.

Blind and exposed solve records each contain one real attempt, 3/3 visible
matches, unscored query predictions and frozen human-readable work notes. The
blind solve preceded reference inspection; the later solve declares repair
exposure and is bound to final generator bytes. No reference source or private
answer was consulted during either solve phase. These are authored work logs,
not captured token-level model traces.

Both assigned audits are findings-only. They retain four concrete peer issues
without altering those targets or expanding the selected repair's scope. No
maintainer approval or audit resolution has been simulated. The final fresh
packet replay verified all 15 changed files and repeated all four task test
files in that checkout's own Python/Racket environment. It passed 61 methods
and 49 subtests with zero failures/errors/skips. The explicit extraction scope
was the 374-file runtime closure of the 103,281-file original packet. Exact
receipts are in checks/replay-final/.

The original outer wrapper arguments for the dedicated scalar red/green tests and authority-sync mutation were not retained. Output/operation receipts are preserved, while the exact final verification commands are recorded. This logging limitation and its independent verification are explicit in checks/historical-command-logging.json; no unretained command is reconstructed.
