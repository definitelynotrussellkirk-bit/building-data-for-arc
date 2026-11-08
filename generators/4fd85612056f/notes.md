# Working notes: 4fd85612056f

## Current intended rule

Treat orthogonally touching nonzero cells as one component even when colors differ. Select the component with greatest bounding-box height; break height ties by larger cell count and then smaller leftmost column. Return its tight crop with source colors preserved and background 0 inside unoccupied cells.

Canonical Racket authority is unchanged and pinned by `RULE_HASH = "2ea4086e36a6"`. Current generator version is `2.0.0`; final reviewed generator SHA-256 is `7019f006e75253b5c03864e97c96b045ad4773dcde13f37d7fec4adb7bb5d814`.

## Reversed prior choices

The baseline (`092210979fa6dfad9ee4dcf0b6c4d887ba7f58e23bab19bffb0c3bfb3010e705`) made the answer the only irregular component and explicitly rejected solid rectangular winners. Retained return `review-e112c2eed9e98149:v0001` identified that shortcut and an ignored `grid_h` override; its ZIP SHA-256 is `cf72348467467f182a8927e042343be6d3abdb96d062e64777b62c6b900d6efb`. This review used it as a lead and reproduced the issues against the pinned baseline.

The new generator allows the canonical rectangle, removes dead/ambiguous controls, and makes an earlier shorter distractor irregular, larger, wider, and left of the winner. Thus the intended height comparison is required rather than irregularity, size, width, or reading-order selection.

## Current distribution and lesson policy

* Every ordinary grid is 8..11 × 10..13 with exactly three color-agnostic nonzero components of bounding-box heights 3, 2, and 1 and exactly three nonzero colors.
* Five scheduled dimension rows exactly cover the canonical `(height, width, distinct-color-count)` profiles.
* Winner free shapes are rectangle, elbow, T, and cross.
* Public exact axes are `grid_h`, `grid_w`, and `target_shape`; all are returned-grid observable. Invalid types/ranges and unknown keys fail loudly.
* A ten-slot deterministic schedule alternates mixed-color and monochrome winners and two placements. `EXAMPLES_NEEDED = 4`; any of five consecutive examples may be the query.
* Mixed-color winners refute the strongest canonical-fitting shortcut, same-color component segmentation. Exact retained witness: `counterexamples/review-484b6daa042b533a-v0001/mixed_color_shortcut.json`.
* Declared rivals also cover largest-cell, widest, leftmost, rightmost, and first-nonrectangular selection. Named witnesses and `lesson_identifiable` are executable.
* Difficulty changes keyed colors only; structure and semantics remain constant.

## Final evidence

* All 12 strict after-battery stages green; strict support 600/600; canonical acceptance 5/5; exact/envelope profile support 60/60; override audit 5,490 draws with zero findings.
* Focused tests: 38/38 direct and 38/38 portable staged runtime.
* Semantic smoke: 12/12 lessons identifiable and 0/60 ambiguous rotations.
* Fixed-seed schedule census: all 10 starts × 3 bands, 30/30 lessons and 150/150 query rotations identifiable.
* Production census: 300/300 lessons materialized, 0 ambiguous, 1,500/1,500 rotations identifiable, 1,290 unique inputs.
* Post-repair visible solve: 4/4 examples; earlier exposure honestly recorded as yes; reference consulted during solve recorded as no.

Primary receipts are under `checks/after-final/`, `checks/lesson-census-final.summary.json`, `checks/shortcut-witness/`, and `checks/task-tests-final/` in return `review-484b6daa042b533a`.

## Known limits and open questions

* The generated manifold has unique component heights 3/2/1, matching canonical structure; it does not teach cell-count or leftmost tie breakers.
* The four winner shapes and finite named-rival set are bounded coverage, not universal identifiability.
* Exhaustive schedule coverage is fixed-seed; broader seed coverage is the 300-lesson sample rather than an exhaustive proof.
* The heavy distractor has one fixed free shape. It is always a losing component and no checked rival uses it as a correct label, but future diversity work could vary losing shapes while preserving the same adversarial inequalities.
* Passing checks do not imply training admission or approval.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e112c2eed9e98149:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `092210979fa6dfad9ee4dcf0b6c4d887ba7f58e23bab19bffb0c3bfb3010e705`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved only the named old-source findings on generator092210979fa6dfad9ee4dcf0b6c4d887ba7f58e23bab19bffb0c3bfb3010e705: unique-irregular answer cue, rejected canonical rectangle, ignored grid_h. Accepted replacement7019f006e75253b5c03864e97c96b045ad4773dcde13f37d7fec4adb7bb5d814 adds shorter larger irregular decoys, rectangular winners and exact observed dimensions. Reviewer reports38portabletests,5490overridechecks and300productionlessons/1500rotations without findings; checks/after-final/ and checks/shortcut-witness/comparison.json retain bounded evidence. No independent maintainer battery/model rerun or universal identifiability claim. Tie-break curriculum remains unexercised and explicitly documented.

### Assessment or prior finding

## 4fd85612056f

**Classification: suspected shortcut, with a separate reproduced override defect.** The reference rule produced correct labels for all five canonical examples checked. The main concern is that the generated distribution lets a rival ignore the task's defining height comparison. No generator, rule, notes, tests, metadata, or shared source was changed during this audit.

### Audited source and existing context

| Item | Exact identity |
|---|---|
| Selected generator | `generators/4fd85612056f/generator.py`, version `1.4.0` |
| Generator SHA-256 | `092210979fa6dfad9ee4dcf0b6c4d887ba7f58e23bab19bffb0c3bfb3010e705` |
| Canonical record | Exact task `4fd85612056f`, `shared/data/canonical/puzzles.jsonl`, line 2398; four train pairs and one test pair |
| Canonical record SHA-256, including its original newline | `f374563d7846dd10855175e35859538b68f4847cbc8a845559a58b8c656a5b6e` |
| Canonical `program_solution` UTF-8 SHA-256 | `2ea4086e36a62772a46d2b2f66aad8afd06edf29c9748eefeda9c19bf6ac5f7a` |
| Executed/catalog rule identity | `2ea4086e36a6`; actual application reports `rule_hash_matches_catalog: true` |
| Runtime-reported `rule_text_sha256` | `9e9adeeef10bd8e6b532d7a46ec42e837ee0e7810b790ac6338a1dd32511628c` |

The canonical program string and runtime-reported rule text are identified separately above. `notes.md` is only the current empty working-notes template, associated notes are empty, and `generators/4fd85612056f/evidence/review_index.json` is absent. The source describes the task as selecting the component with greatest bounding-box height. Its version comment says version 1.4.0 added an arm to the winner and forbade rectangular winners to avoid solid output blocks. Exact source and canonical snapshots, current notes, and the audit-index absence are retained in `WORK/checks/audit/4fd85612056f/`.

### A1 — The only irregular component always reveals the generated answer

`generate()` builds the designated winner from a vertical spine with one or two arms. Every distractor is a filled rectangle, separated from existing components by a background gap. Consequently, the winner is the only nonrectangular component in every accepted helpful generated input. A rival that chooses **the first nonrectangular nonzero 4-connected component in reading order and crops it** can answer without comparing component heights. The rival implementation is retained in `probe.py`.

This agreement was reproduced on **18/18 generated inputs**: seeds `0`, `1`, and `17`, sample indices `0` and `1`, crossed with difficulty `easy`, `medium`, and `hard`, with overrides `{}`. All 18 passed the generator's actual `self_check` with `[]`, had exactly one nonrectangular component, and had rival outputs equal to actual Racket outputs. The source construction explains why the shortcut is systematic; this bounded audit does not claim that a particular trained model has learned it.

A compact witness within the declared `5..22` by `5..24` grid-size ranges has two irregular components. It is handwritten, so seed, sample index, difficulty, and overrides are not applicable:

```json
[[2,2,0,1,0],
 [2,0,0,1,0],
 [0,0,1,1,0],
 [0,0,0,0,0],
 [0,0,0,0,0]]
```

**Domain result:** `self_check(input) == []`. The color-2 component has height 2; the color-1 component has height 3. Both are nonrectangular and separated by background. The actual Racket output is:

```json
[[0,1],[0,1],[1,1]]
```

The height-free rival instead outputs:

```json
[[2,2],[2,0]]
```

This distinction is also present in the exact canonical record. The rival disagrees on zero-based `train[1]` and `train[2]`; `train[2]` passes current `self_check`. Canonical `train[1]` has a legitimate solid rectangular height winner, with actual Racket output `[[7,7],[7,7],[7,7]]`, but current `self_check` rejects it with `tallest component is a solid rectangle/line — cropped output would be a single-color block`. That exclusion is part of the distribution restriction, rather than evidence of a Racket labeling error.

**Suggested follow-up:** allow irregular shorter distractors so examples require the height comparison, and reconsider the blanket rejection of rectangular winners against the canonical task. These are findings only; no repair was applied.

### A2 — Declared `grid_h` override is silently ignored

**Classification: reproduced defect.** The declared axis accepts heights `5..22`. The minimal reproduction is `generate(0, 0, difficulty="medium", grid_h=5)`. It returns a **14×14** grid, byte-for-byte identical as a grid to `generate(0, 0, difficulty="medium")`; `self_check` returns `[]`. The generator passes `overrides` to `gen_ctx`, but chooses `h` using `rng.randint` without consuming the `grid_h` override. A caller requesting a legal height therefore receives an unrelated height with no rejection.

`override_probe.json` retains the exact arguments, declared axis, input, measured dimensions, equality result, and self-check result. Because this input equals case `generated_medium_0_0`, its actual Racket output is already retained in the shared application evidence: `[[0,8,0],[0,8,0],[0,8,0],[0,8,0],[8,8,8]]`. No broader override matrix was run.

### Evidence, scope, and replay

All evidence paths below are relative to the packet root, under `WORK/checks/audit/4fd85612056f/`:

- `source_hashes.json`, `audited_generator.py`, `audited_notes.md`, `audited_SUMMARY.md`, `canonical_record.json`, and `canonical_rule.rkt` bind the audited source and exact canonical task.
- `probe.py` and `run_checks.py` reproduce the bounded preparation, source inspection, override comparison, and rival comparison.
- `cases.json`, `input.json`, and `witness_input.json` retain the complete inputs and exact generation arguments.
- `racket.json` retains the public CLI's actual execution of **24 inputs**, with **zero Racket errors**: 18 generated inputs, all five canonical pairs, and the handwritten witness.
- `comparisons.json`, `findings.json`, and `override_probe.json` retain the measured results. All five canonical outputs matched Racket.
- `command_receipts.json` records exact argument arrays, invocation and effective working directories, exit codes, and retained evidence paths for each meaningful check. All three checks exited 0; stdout and stderr logs are retained.

From `/workspace/scratch/86ed75615dbe/packet`, replay the actual rule application using a fresh output filename:

```bash
WORK/.venv-review/bin/python -B review.py run /workspace/scratch/86ed75615dbe/packet/WORK/.venv-review/bin/python -B -m arcpuzzles apply 4fd85612056f --input ../checks/audit/4fd85612056f/input.json --out ../checks/audit/4fd85612056f/racket-replay.json
```

To regenerate the bounded inputs and direct override check, run from the same directory:

```bash
WORK/.venv-review/bin/python -B review.py run /workspace/scratch/86ed75615dbe/packet/WORK/.venv-review/bin/python -B ../checks/audit/4fd85612056f/probe.py prepare
```

This audit did not run a battery, full-library tests, an additional assignment draw, or any solve workflow. The findings are source-bound observations, not an approval or a training-admission claim.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e112c2eed9e98149-v0001/audit_assets.json), manifest SHA-256 `0bbad3a88d63514b350fc6fb9965203190f9a0a638425be39c7f3bfb96b87810`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `7019f006e75253b5c03864e97c96b045ad4773dcde13f37d7fec4adb7bb5d814`.

# Decisions — `4fd85612056f`

## D1 — Keep the canonical authority unchanged

**Choice.** Pin `RULE_HASH = "2ea4086e36a6"` and repair only the generator, validator, metadata, tests, notes, and counterexamples.

**Rationale.** The canonical Racket rule matched all five canonical examples and all generated labels checked. The defects were distribution and public-contract defects, not evidence of incorrect authority.

**Alternatives rejected.** Rewriting the Racket rule or canonical row would increase review risk without addressing the shortcut. A Python-only label path was rejected because the Racket authority must remain the source of truth.

**Probe/evidence.** Authority sync, rule smoke, and the exact shortcut witness all bind to the same rule hash in `checks/after-final/` and `checks/shortcut-witness/comparison.json`.

**Limit.** This decision does not certify every possible off-manifold input; it preserves the existing authority.

## D2 — Use the exact canonical structural envelope

**Choice.** Ordinary examples have three color-agnostic nonzero components with bounding-box heights 3, 2, and 1, exactly three nonzero colors, and grid dimensions selected from the five canonical profiles.

**Rationale.** The previous broad size/axis surface produced little exact canonical support and even rejected a valid canonical rectangle. The compact manifold supplies exact support in every band and keeps the decisive feature—height—unambiguous.

**Alternatives rejected.** Retaining arbitrary 5..22 × 5..24 grids would preserve dead controls and sparse exact support. Restricting winners to irregular shapes was rejected because it caused the original shortcut and contradicted a canonical example.

**Probe/evidence.** Profile floor is 60/60 exact and 60/60 envelope, with 20/20 per band; all five canonical inputs are accepted. See `checks/after-final/checks/4fd85612056f_after_profile_floor.json`.

**Failure mode/limit.** The production manifold has no height ties, so it teaches primary height selection but not cell-count or leftmost tie breakers.

## D3 — Make a shorter distractor dominate nuisance heuristics

**Choice.** Place a connected seven-cell 2×4 irregular component before and left of the true height-3 winner; it is always shorter but larger and wider.

**Rationale.** One component simultaneously refutes “largest area,” “widest,” “leftmost,” and “first nonrectangular,” directly reversing the prior shortcut.

**Alternatives rejected.** Independent random distractors could accidentally fail to distinguish a rival in some lesson window. A filled rectangular decoy would not repair the original irregularity shortcut.

**Probe/evidence.** `dominant_short_decoy` fired on 600/600 semantic census draws, and each associated rival disagreed on 60/60 checked witness draws. The retained old-audit witness is also covered by `test_retained_audit_witness_refutes_first_nonrectangular`.

**Failure mode/limit.** The decoy's fixed free shape is itself regular across samples. It is not a label cue because it always loses, but broader decoy-shape diversity could be added later if needed.

## D4 — Alternate mixed-color and monochrome winners

**Choice.** Even schedule slots paint the connected winner with two alternating colors; odd slots paint it monochromatically. Both use exactly three nonzero palette roles overall.

**Rationale.** The canonical demonstrations cannot distinguish nonzero connectivity from same-color connectivity because all canonical components are monochrome. Mixed winners supply the missing counterexample. Monochrome rows retain exact canonical object/color signatures and avoid making “multicolor means answer” sufficient across a four-demo lesson.

**Alternatives rejected.** All-monochrome generation leaves the strongest canonical shortcut untouched. All-multicolor generation triggered coarse color-specific lint signatures and would introduce a new constant answer cue.

**Probe/evidence.** The same-color rival fits all 5 canonical pairs, but differs on the exact generated witness in `checks/shortcut-witness/comparison.json`. Mixed-color winners fired on 286/600 random semantic draws, and every tested four-demo window refuted the rival.

**Failure mode/limit.** Palette alternation is deterministic by sample-index parity. Lesson tests and all cyclic starts ensure this remains sufficient under the current four-demo assembly policy.

## D5 — Use four observable winner free shapes

**Choice.** Support rectangle, elbow, T pentomino, and cross through the exact `target_shape` axis.

**Rationale.** These cover all free shapes represented by the canonical outputs, including the valid solid 3×2 rectangle. Shape variation prevents “always crop a particular silhouette.”

**Alternatives rejected.** A three-shape bank initially omitted the canonical T pentomino and was corrected before the focused suite went green. Arbitrary shapes were rejected because they would reduce canonical profile overlap and complicate exact observability.

**Probe/evidence.** All four shapes appear in every 30-sample band/default test, all crossed boundary overrides pass, and canonical outputs are mirrored exactly.

**Failure mode/limit.** This is a finite shape bank; it does not attempt to cover all connected height-3 polyominoes.

## D6 — Keep only exact, returned-grid-observable axes

**Choice.** Public axes are `grid_h`, `grid_w`, and `target_shape`. Unknown keys and invalid scalar/range values fail loudly. `observe_overrides` recovers all three from a lawful returned grid.

**Rationale.** The old generator advertised controls that were ignored, clamped, not observable, or diagnostic fixtures masquerading as production texture values.

**Alternatives rejected.** Keeping compatibility aliases would preserve silent failure modes. Advertising component count, palette size, or density was unnecessary because they are fixed invariants, not meaningful controls.

**Probe/evidence.** The final override audit executed 5,490 draws with 0 findings or warnings. Crossed boundary tests run in all four difficulty settings (`None`, easy, medium, hard).

**Failure mode/limit.** Difficulty is intentionally not an axis; it changes keyed colors only.

## D7 — Declare an executable semantic contract

**Choice.** Add `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, named witnesses, witness-to-rival claims, `lesson_identifiable`, and a 10-slot schedule declaration.

**Rationale.** Correct labels on individual grids do not establish a teachable multi-example lesson. Executable rivals turn the design claims into source-bound tests and census evidence.

**Alternatives rejected.** Describing rivals only in notes would not protect future edits. A random resampling loop was rejected in favor of a simple schedule whose cyclic starts are exhaustively testable.

**Probe/evidence.** The semantic gate checked 600 strict draws, 12 smoke lessons, 60 query rotations, 30 schedule-enumerated lessons, and 150 schedule rotations. The larger census checked 300 production lessons and 1,500 rotations.

**Failure mode/limit.** Passing a finite rival set cannot prove uniqueness against every conceivable hypothesis.

## D8 — Four demonstrations plus one query, arbitrary query rotation supported

**Choice.** Set `EXAMPLES_NEEDED = 4`; generate five consecutive schedule rows per lesson and permit any one to be held out as query.

**Rationale.** Four demonstrations guarantee at least two mixed-color and two monochrome structural rows in every current cyclic window while exposing both placement layouts and the adversarial decoy.

**Alternatives rejected.** Two demonstrations were insufficiently robust to query rotation. Ordered-only query placement would make lesson assembly fragile.

**Probe/evidence.** Task tests exhaust all 10 starts × 4 bands × 5 query positions. The fixed-seed semantic census checked 150 rotations, and the production census checked 1,500 rotations, all identifiable against declared rivals.

**Failure mode/limit.** Exhaustive start coverage is at fixed seed 0; the 300-lesson production census provides broader but sampled seed evidence.

## D9 — Preserve audits as findings only

**Choice.** Do not modify `3079e46d051f` or `08b346c559d6`; retain exact probes, Racket outputs, source hashes, and recommendations under `checks/audit/` and summarize them in `AUDIT.md`.

**Rationale.** The assignment authorizes edits only under the selected task. Source-bound findings are more useful than an out-of-scope patch.

**Probe/evidence.** The peer-audit preset completed for both targets and correctly reported absent tests/semantic contracts; custom bounded probes established the concrete distribution and override defects.

**Failure mode/limit.** Neither audit is a full battery or proof of model behavior. A1 is a systematic distribution shortcut, not a claim that a trained model learned it.

## D10 — Treat the prior retained review as a lead, not current evidence

**Choice.** Consult only retained return `review-e112c2eed9e98149:v0001`, ZIP SHA-256 `cf72348467467f182a8927e042343be6d3abdb96d062e64777b62c6b900d6efb`, then reproduce its relevant claims against the pinned baseline.

**Rationale.** The assignment explicitly distinguishes historical reports from measurements of current source.

**Alternatives rejected.** Re-reading all historical returns would add noise; accepting prior counts without reproduction would violate source binding.

**Probe/evidence.** The pinned baseline hash matched the retained audit's audited hash. New baseline checks reproduced canonical rectangle rejection, ignored/dead axes, and the first-irregular shortcut mechanism.


### Supplemental second-pass tools (reviewer-reported, not runtime-approved)

Return SHA-256 `d91c405bcad2bc2ba722ce4979487cd1ee2b02e26d17fd81763652ded5029231` leaves the accepted generator `7019f006e75253b5c03864e97c96b045ad4773dcde13f37d7fec4adb7bb5d814` unchanged. The transport validator rejected executable ZIP metadata on `second-pass/fuzz_generator.py`; no replacement generator or shared tool was integrated. Useful supplemental tools/reports were separately retained under `workspace/reviewer-tools/second-pass-d91c405b/` with content hashes and passive status. The verifier checks response/patch/evidence bindings; the task-specific fuzz tool uses a deterministic stand-in generation context, not the producer runtime or Racket oracle. Its bounded reported runs and nine reported tool tests are retained, not rerun or treated as new approval/training evidence. Original Downloads and rejected managed transport are preserved.
