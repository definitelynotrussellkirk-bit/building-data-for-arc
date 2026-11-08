# Working notes: bf8910eef99b

## Current rule
A solid 2×2 block has four distinct colors. Each source cell paints a 2×2 patch in the diagonally opposite quadrant at offsets two and three from the block. Patches are clipped by the grid boundary; existing nonzero source cells are preserved.

## 2026-10-08 review-draw decisions
- Prior evidence used as a lead: retained return `review-3f8d164b5cf34823:v0001`. Its override and validator findings reproduced on the pinned source. Its claim that clipping is absent from the canonical domain was rejected: canonical train pair 0 visibly contains clipped top/left stamps, and the canonical Racket rule clips naturally.
- Root cause: the 1.1.1 sampler described a full-margin task that is not the authority, advertised nine controls while several were unused/coerced, allowed repeated colors, accepted malformed inputs, and had no `RULE_HASH`.
- Replacement contract: four strict, pixel-recoverable axes only (`grid_h`, `grid_w`, `placement_profile`, `palette_id`). Four placement profiles deliberately clip exactly one side while leaving the orthogonal axis interior, so every production example contains both complete and clipped stamp evidence.
- Dimensions 6–9 preserve canonical 6×6 support. Every source color is distinct. The source stays far enough inside that each of the four target colors remains visible at least once.
- Six executable rivals now cover: dropping partial stamps, canonical-palette memorization, copying one cell, same-quadrant stamping, absolute grid-corner stamping, and rotating color roles. Every production input is intended to refute every declared rival, making arbitrary one-query rotations safe against this finite set.

## Known limits
The finite rivals do not prove unique program induction. The production sampler emphasizes boundary clipping and does not sample fully interior source placement, although `self_check` continues to accept all four canonical inputs, including interior cases. Grid size is intentionally bounded to 6–9 for compact lessons.

## Final evidence for review-57a3a445b41d171c
- Final generator SHA-256: `5b5151d0418ca8579a86380f47917939f3395159e11a728e18f0cfb02636cd82`; canonical rule hash remains `f45b7e9216b7`.
- Pristine before battery on hash `6c6a44c3c2d754dff7d4bbbe01aeec2cfd90cf215f2846b403d0937897adab16`: 6 green, 2 advisory, 4 failed (lint, defect lint, override, authority sync).
- Final battery with required query rotations: 12/12 green. Portable focused tests: 139 passed.
- Joint controls: 1,536/1,536 legal combinations passed across all difficulty settings; 14/14 invalid controls rejected; 1,485 unique inputs.
- Semantic sample: 1,000 generated cases (905 unique), every one refuted all five declared rivals; 69/69 sampled Racket parity checks passed.
- Lesson census: 300 three-demo/one-query lessons, 1,200 pairs, 1,200 query rotations, 1,062 unique inputs, zero measured ambiguity or scoring/hook errors.
- Active selected Racket text was synchronized to the canonical text; this was a behavior-equivalent source cleanup, not a canonical rule change.

## Open limits
- Rival checks cover six explicit hypotheses and do not prove unique induction.
- Production deliberately always clips one side; fully interior inputs remain lawful and canonical-supported but are outside the production sampler.
## 2026-10-20 review-82816a8e1b9631b7

- Prior return used as a lead: `review-3f8d164b5cf34823:v0001`; all current claims were re-measured on the pinned source.
- Baseline SHA-256 `5b5151d0418ca8579a86380f47917939f3395159e11a728e18f0cfb02636cd82` passed 11/12 battery stages. `defect_lint` found 48 accepted-invalid-scalar warnings across `seed`, `sample_index`, and `difficulty`.
- Added exact call validation: integer seed, nonnegative integer sample index, and difficulty in `{None,easy,medium,hard}`. Valid-call sampling, `VERSION=2.0.0`, and canonical Racket behavior are unchanged.
- Added `canonical_palette_memorization`, a shortcut that fits all four labeled canonical pairs but drops clipped stamps on unseen palettes. Seed 314/sample 0/right-clip/palette 0 is a Racket-checked generated counterexample.
- Added an isolated proposed `stamp_size` episode prototype under `workspace/parametric/`: canonical/default 2x2 stamps versus nearby 1x1 stamps, with exact Racket programs, two identifiable episodes, masked public challenges, and a differing witness. This is not production or approval evidence.
- Final source SHA-256 `5897f2509f47c19a2ebbe1fb8ee53d2430b26317ce856ee3daa09b800b4f0543`; strict battery 12/12 green; portable tests 159 passed; 300 lessons and 1,200 rotations had zero measured ambiguity.
## Current reviewer considerations

Source SHA-256: `5897f2509f47c19a2ebbe1fb8ee53d2430b26317ce856ee3daa09b800b4f0543`.

# Decisions: bf8910eef99b — review-82816a8e1b9631b7

## D1 — Reject invalid call scalars before keyed generation

**Prior choice:** `generate` validated advertised overrides but delegated `seed`, `sample_index`, and `difficulty` without an explicit task-local domain check. The reason is unknown.

**New choice:** require `type(seed) is int`; require `type(sample_index) is int` and `sample_index >= 0`; and require difficulty to be exactly `None`, `easy`, `medium`, or `hard`. Existing override validation remains the final step of the same preflight.

**Evidence:** the before defect-lint reported 48 accepted-invalid-scalar warnings over three bands. Sixteen focused values were encoded as tests and observed failing before the implementation. They pass after the change; the final defect-lint and all other battery stages are green.

**Alternatives rejected:** relying on `gen_ctx` was rejected because the measured baseline showed it did not enforce these call scalars. Coercing strings/floats was rejected because it preserves ambiguous API behavior. Rejecting negative integer seeds was not added: the detector and declared contract only require nonnegative sample indices.

**Failure mode / limit:** this changes only invalid-call behavior. It does not validate semantic meaning of arbitrary large integer seeds, which are intentionally acceptable deterministic keys.

## D2 — Preserve generator version and valid-call schedule

**Prior choice:** version `2.0.0` determines keyed random draws.

**New choice:** keep version `2.0.0` and the valid-call sampling code byte-for-byte apart from the preflight call.

**Reason:** a patch-version bump would alter all valid generated instances because `VERSION` participates in `gen_ctx`, even though the repair does not intend a distribution migration. Final evidence binds the new source hash separately.

**Alternative rejected:** bumping to `2.0.1` for conventional release bookkeeping. Here that cosmetic change would have a substantive sampling effect.

## D3 — Declare the canonical-palette memorization shortcut

**Prior choice:** five rivals were declared, and `CANONICAL_SHORTCUTS` was empty because none of those five fit all four labeled canonical pairs.

**New choice:** add `canonical_palette_memorization`: execute the intended rule for the four exact canonical palette sets, but on any unseen palette discard partially clipped stamps. Keep it in `SEMANTIC_RIVALS` and `CANONICAL_SHORTCUTS`; the lesson hook explicitly merges canonical shortcuts with ordinary competitors.

**Reason:** this is the strongest compact overfit found that actually fits 4/4 labeled canonical pairs. It directly tests whether the generator teaches clipping independently of memorized colors. The existing six production palettes are all unseen and every input clips one side, so each production input refutes it.

**Evidence:** independent implementation parity and purity are tested. Seed 314/sample 0/right-clip/palette 0 is Racket-labelled and disagrees. The semantic gate found its witness firing 600/600 sampled inputs; the 300-lesson census refuted it in all lessons and all rotations.

**Alternatives rejected:** a literal full-grid lookup was too arbitrary to teach anything about the sampler. The existing `complete_stamps_only` rival was plausible but does not fit canonical pair 0. A train-only palette overfit was weaker than the chosen variant because the chosen rival fits all four labeled pairs, including the canonical test label available to authoring diagnostics.

**Failure mode / limit:** palette memorization is only one family of canonical overfit. Finite declarations do not prove that no other shortcut survives.

## D4 — Prototype `stamp_size`, once per episode, outside production

**Prior choice:** the selected task had no current parametric evidence.

**New choice:** prototype one bounded parameter with values `{1,2}`. Value 2 is canonical/default. Value 1 emits the nearest one-cell copy for each source role while retaining the same source block, diagonal-opposite mapping, and clipping semantics.

**Reason:** patch size is a nearby transformation parameter already represented by a plausible rival, so it changes executed behavior without replacing the task's reasoning structure. It is simpler and more defensible than varying quadrant direction or color-role permutation, which would alter the central relational concept.

**Episode policy:** choose the hidden value deterministically once from the episode seed; use it for all three demonstrations and the query. Inputs do not encode or depend on the chosen value. Demonstrations must refute the alternative and the query must separate it.

**Evidence:** exact Racket text is materialized for both values. Two complete episodes (one per setting), a direct differing witness, hashes, full private labels, and solver-safe public challenges are retained under `checks/parametric/stamp-size-900/`. The report passes 2/2 identifiability and 2/2 query-separation checks.

**Alternatives rejected:** changing only grid size or placement would not be a rule parameter. Randomizing the parameter per pair would make the episode incoherent. Integrating it into `generate()` would violate the fixed-rule production boundary and approval hash.

**Failure mode / limit:** only two sizes and two retained seeds were assessed. The prototype does not prove unique human/model induction and is not admitted to production or training.

## D5 — Keep canonical Racket authority unchanged

No change was justified. The selected and canonical rule sources remain synchronized, execution parity passes, and declared rule hash remains `f45b7e9216b7`. The single-cell program lives only in the isolated prototype. No shared base solution, canonical ledger, catalog approval, or training metadata was edited.

## D6 — Verification and stopping rule

Implementation followed red/green tests for both repairs: strict scalar tests first failed 16 cases, then passed; the parametric API and evidence exporter were each introduced behind failing focused tests. The direct task-local suite finished at 159 passed. Required portable tests, the full strict after battery, standalone lint, and the 300-lesson rotation census all completed successfully.

The post-repair solve was prepared only after generator source stabilized. It passed all three visible examples on revision 1, declared prior rule exposure, and did not consult a reference during solving. Work stopped after required audits and documentation because all selected-task gates were green and remaining limitations are authoring-policy questions rather than unresolved execution failures. The packaged source patch was then replayed onto a fresh full extraction of the original 85,117-file packet; changed-file hashes matched, and the fresh checkout passed all 159 selected task tests.
