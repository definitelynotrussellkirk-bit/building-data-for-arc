# Working notes: a78185b4bd20

## Current decision

The canonical authority does **not** select a unique or largest symmetric object. It enumerates monochrome 4-connected components in row-major order, selects the first component whose binary bounding-box crop is left-right symmetric, crops that box, and recolors nonzero cells cyan. Preserve the no-match `[[0]]` fallback in the mirror even though generated lessons always contain a target.

## Repair implemented in v3.2.0

- Replace the prior four-component-only curriculum with schedule counts `3,5,5,3`.
- Anchor every three-component profile at canonical dimensions/palette: `11x11`, four colors including background, one symmetric target between asymmetric distractors.
- In five-component profiles, add a later same-color symmetric competitor and reverse target/competitor size ordering across profiles; order must win over size and color.
- Keep only exact observable axes `grid_h` (`7..14`) and `grid_w` (`9..16`); reject unknown/non-integer/out-of-range overrides.
- Validate scene structure independently of generation and declare the complete nine-mask output codomain.

## Retained evidence

Final source SHA-256: `ccee4a2b457fdaa49abbbd154447c2a804a075f738af6ba410da52e3880c26a9`; rule hash unchanged: `4f60736ed86a`.

- 16 task tests pass.
- 43 representative cases match bundled Racket exactly, including all canonical pairs, first-vs-largest witness, no-match fallback, schedule roles, and dimension corners.
- Rule smoke applies 120/120 cases with nine outputs and zero mirror mismatches.
- All twelve framework stage types pass on the final source; incomplete aggregate-controller attempts were replaced by isolated receipts.
- Independent census passes 40,000 lessons, all declared dimensions, all nine outputs, 64 override corners, and 11 invalid calls.

## Remaining limit

The sampler uses a finite `3x3` shape bank and does not generate no-match lessons. Those are intentional curriculum bounds, not claims about the full authority domain.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4ad5ac744301bbda:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ec3a852ab4430af45d109f3e784803ccab16f641d556662feb8d00b6b3b1b44a`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit owner disposition after accepted reviewer repair review-f4376d42cd307532: current repo/generators/a78185b4bd20/generator.py SHA256 ccee4a2b457fdaa49abbbd154447c2a804a075f738af6ba410da52e3880c26a9. Reviewer-reported evidence: 16focused tests,43Racket parity cases and bounded40,000scene census. Authority selects the first qualifying component, so multiple qualifying objects are lawful. Ordered/repeated-color rivals, strict role structure and exact controls replace the old uniqueness/degenerate model. No owner battery rerun, universal identifiability or training admission. The audit on ec3a852ab4430af45d109f3e784803ccab16f641d556662feb8d00b6b3b1b44a is resolved only for these repaired findings. Retained target-local evidence references: `checks/audit/a78185b4bd20-task-tests-command.log` `checks/audit/a78185b4bd20-task-tests/RUNTIME_MANIFEST.json` `checks/audit/a78185b4bd20-task-tests/result.json` `checks/audit/a78185b4bd20/apply-command.log` `checks/audit/a78185b4bd20/input.json` `checks/audit/a78185b4bd20/racket.json` `checks/audit/a78185b4bd20/reproducer.json`

### Assessment or prior finding

## a78185b4bd20

**Reproduced defect: declared invariants and controls are not enforced.** Generator SHA-256: `ec3a852ab4430af45d109f3e784803ccab16f641d556662feb8d00b6b3b1b44a`.

1. `generate(seed=23, sample_index=0, texture="no_blobs")` returns a 9×12 all-zero grid. The generator declares background 0, exactly one left-right-symmetric blob, and at least one left-right-asymmetric blob, yet `self_check` returns `[]`. The canonical Racket rule still emits a valid `[[0]]`, so output validity does not repair the input-domain violation.
2. For seed 23/index 1/hard, supplying `palette_size=2`, `n_distinct_colors=4`, `palette_kind="warm"`, `position_bias="isolated_blobs"`, and `density="sparse"` returns a grid byte-identical to the unoverridden draw. The grid has nonzero colors `[1,4,8]`, directly contradicting at least the requested palette-size interpretation. The axes appear ignored rather than exact or observable controls.

Exact reproducer and grids: `checks/audit/a78185b4bd20/reproducer.json`. Supported Racket receipt: `checks/audit/a78185b4bd20/racket.json`. The optional task-test command found no task-local or selected frozen tests and exited 5; see `checks/audit/a78185b4bd20-task-tests/result.json` and `checks/audit/a78185b4bd20-task-tests-command.log`.

Suggested maintainer action: reject impossible domain choices such as `no_blobs` when blobs are required, make `self_check` independently count symmetric/asymmetric blobs, and either implement each advertised axis with observable postconditions or remove/reject it explicitly.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-4ad5ac744301bbda-v0001/audit_assets.json), manifest SHA-256 `da6123742c22c59acb8bac768537a8c33b29598330e465019cc6e881e45bf45e`.
<!-- arcpuzzles-current-audit-assessment:end -->
