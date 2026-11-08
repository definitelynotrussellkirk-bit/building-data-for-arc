# Working notes: 9bfbec04496c

## Current decision — 2026-10-23

- Keep canonical task `9bfbec04496c` and rule hash `25e19a18a7ae` unchanged.
- Replace the source-bound 8-to-1-only distribution with a strict 3×3 separator mosaic in which every generated instance contains both one exactly-single-outlier disagreement and one 2–4-outlier disagreement. This directly separates the selected “mark any non-unanimity blue” rule from both threshold shortcuts.
- Cycle tile shapes through `2x2`, `2x3`, `3x2`, and `3x3`; omit blue 1 from generated inputs so output markers are introduced rather than copied; remove degenerate textures from the declared ordinary domain.
- Expose a pure Python rule mirror, strict structural validation, exact override observation, named semantic rivals/witnesses, and a three-demonstration lesson-identifiability hook.
- Make `easy`, `medium`, and `hard` differ through keyed `n_mut` and `multi_outliers` draws while preserving exact override behavior and deterministic replay.

## Reversals made during implementation

- The first exact-axis implementation returned lawful grids but provided no grid-derived observer. Lint correctly rejected that unverifiable contract, so `observe_overrides()` now recovers `n_mut` as the number of disagreeing local cells and `multi_outliers` as the largest outlier count.
- The first easy-band defaults used raw constants. The override checker correctly found missing keyed provenance, so both singleton defaults now use strict keyed draws.

## Evidence and limits

Final generator SHA-256: `ef12c89d904132ec00ac3ad62ef2513c98e5ca6ac514c9905b206ba14f349ada` (baseline `469f7bc2ac4606eb8f745f8efe949a66c98b47cdf33362d2f211b44485a308a6`). Focused tests pass 54/54; Racket parity passes 120/120; the semantic gate passes 600/600 strict generations, all declared witnesses/rivals, 12/12 lessons, and 0/48 ambiguous rotations; the override matrix passes 7,920/7,920 draws across 88 cases. These are bounded source checks, not a universal proof, approval, or training admission.

## Next useful action

A maintainer should replay the packaged commands, review the source patch against the unchanged Racket authority, and decide whether the repaired generator resolves the two retained audit findings.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-44570f1e4bbb012f:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `469f7bc2ac4606eb8f745f8efe949a66c98b47cdf33362d2f211b44485a308a6`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit closure of this historical-source finding by accepted source ef12c89d904132ec00ac3ad62ef2513c98e5ca6ac514c9905b206ba14f349ada. Every new scene teaches both one-outlier and broader majority disagreements; strict scalar/grid validation, real difficulty bands, canonical-introduced color1, semantic witnesses/rivals and scoped regressions address the retained teaching and API findings. Exact finite evidence and failures remain reviewer_reported under evidence/reported-support-limits-e08ca8b87358096f/manifest.json and the source-bound main review record. Canonical authority unchanged; no owner test rerun or parametric/training admission.

### Assessment or prior finding

## 9bfbec04496c

**Classification: reproduced defects; source left unchanged.** Generator SHA-256:
`469f7bc2ac4606eb8f745f8efe949a66c98b47cdf33362d2f211b44485a308a6`. The strict audit preset found no task-local/frozen tests and failed the
semantic gate because the generator declares none of
`strict_canonical_like`, `SEMANTIC_WITNESSES`, or `lesson_identifiable`.
Therefore there is no executable evidence that a 3-demo lesson teaches the
separator/tile-disagreement rule.

The separate strict defect lint failed with **1 issue and 150 warnings**. The
most consequential distribution finding is `transformation_drift`: the
canonical rule introduces output color 1 in every canonical demonstration, but
only **15/60** generated pairs exercised that behavior. It also reports a
palette-role structural mismatch, a permissive self-check accepting minimal
impostors, dead difficulty bands, degenerate textures inside the ordinary valid
domain, and 144 invalid scalar acceptances. These are source-bound findings, not
approval decisions.

Evidence:

- `checks/audit/9bfbec04496c-combined/result.json` (audit preset, exit 1)
- `checks/audit/9bfbec04496c-combined/checks/9bfbec04496c_audit_semantic_gate.log`
- `checks/audit/9bfbec04496c-defect-lint/result.json` (strict defect lint, exit 1)
- `checks/audit/9bfbec04496c-defect-lint/checks/9bfbec04496c_audit_defect_lint.log`

No generator, rule, note, or test under this audit target was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-44570f1e4bbb012f-v0001/audit_assets.json), manifest SHA-256 `d3cded24e807ba9ba0e339017b343e2af5fdff8dd003337bc8b1132fe95cb8bd`.
<!-- arcpuzzles-current-audit-assessment:end -->
