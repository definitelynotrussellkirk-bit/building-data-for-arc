# Review `db63430eeffa` — canonical repair plus path-selection prototype

Assignment: `review-7d8f4fcc562b905b`.
Baseline generator SHA-256: `7c732860b8701c13d24771feba4fbaec9103d541a7c8c903ff42c16a596dd581`.
Current generator SHA-256: `2531249a89d6991dc3644274518f787d6de3bd2a734000d9119c708c9a399acf`.
Canonical default Racket source is unchanged: exact SHA-256 `738576fedc01cbcd29e0e5a381777ed10929461bca3c60994cee0a3fb4010c46`.
The generator now rejects unknown controls, lossy scalar types, invalid difficulty values, and negative/non-integral sample indices before `gen_ctx`.
The intentional `square_diagonal` coincidence is explicitly declared lawful rather than ambiguously overlapping ordinary and degenerate domains.
A task-local `path_mode` prototype materializes `both`, `diagonal_first`, and `straight_first` Racket rules while keeping the exact canonical rule as the default.
Each setting has three identifying demonstrations and four distinct queries on the same sampled inputs; public exports hide the setting/program/seed/query answers.
No variant approval, catalog selection, audit resolution, or training admission is claimed.

## Built artifacts

- `generator.py`: strict control validation plus `LAWFUL_DEGENERATE_TEXTURES`; valid-call draw behavior and version remain unchanged.
- Focused regressions: portable canonical lookup, strict-invalid-control cases, lawful-degenerate declaration, and prototype behavior/privacy tests.
- `workspace/parametric/prototype.py`: deterministic episode generation, Python mirror, exact default pin, alternative Racket materialization, declared-rival analysis, and public/private projection.
- `workspace/parametric/verify.py`: protected-Racket materializer/verifier that checks all canonical pairs and all three seven-pair episodes, then emits private evidence and opaque public challenges.

## Verification

- Baseline focused tests failed at the staged canonical path; the repaired portable test boundary plus new red cases were observed failing before implementation (`12 failed, 5 passed, 10 subtests passed`).
- After repair: `17 passed, 48 subtests passed` in `checks/final/db63430eeffa-task-tests/progress.log`.
- Baseline defect lint reproduced strict-scalar and texture-domain findings; after repair it passes in `checks/final/db63430eeffa-defect-lint/progress.log`.
- The full baseline override matrix was started but exceeded the 220-second native budget before completion; it is retained as partial evidence, not reported as a pass. Targeted strict-control tests and the defect linter cover the repaired boundary.
- Racket-backed prototype report: `checks/final/db63430eeffa-path-selection/report.json`; exact canonical default passed all eight labeled canonical pairs and every selected label matched Racket/Python parity.
- Adversarial export/sampler sweep: `checks/final/db63430eeffa-path-selection-adversarial.json` (32 seeds, 96 episodes, 672 pairs, 96 unique public IDs).

## Supplementary tickets

- `ticket-4751e7f506690bb7`: pinned source/index/record/manifest and all retained assets matched; the existing `7768dfc99e25` single-object validator defect reproduced exactly. The existing audit remains unresolved pending maintainer assessment.
- `ticket-be6a9b6a2f843f97`: actual safety finding for `235a1d06b9d3`. The wrong `(1,1)` background-anchor shortcut fits every canonical pair and all 16 declared generated profiles because the validator forces `(1,1) == (2,1)`; a Racket-executed reference-lawful discriminator differs in five cells but is rejected by the target validator. See `AUDIT.md`.

## Remaining limits

The parameter evidence covers three declared settings and finite sampled episodes, not arbitrary program rivals. A complete post-repair 119,700-draw override matrix and a full production battery were intentionally not run: they are unnecessary for the scoped prototype/control repair, and the baseline matrix already exceeded the wrapper budget.
