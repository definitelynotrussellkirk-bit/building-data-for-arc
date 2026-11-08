# Review — a9c4475d7cda parametric threshold extension
Task/source: `review-fdc6a9b2aee6af87`; production generator SHA-256 `1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51`; rule hash `8cfb5cf9c2c4`.
Defect → repair: the approved canonical generator had no small rule-parameter surface; added a task-local `threshold ∈ {1,2,3}` prototype with canonical default `2`.
Reference rule: production `generator.py` and the selected base solution are unchanged; `threshold=2` is byte-identical to the canonical Racket program.
Checks: focused plus canonical tests pass 83/83 (`checks/final-tests.log`).
Racket/export: three retained settings, 3 demos + 4 queries each, 39 protected-Racket executions (`checks/parametric/a9c4475d7cda-threshold-cli.log`).
Adversarial: six extreme-seed parity cases, 42 protected-Racket executions, ten exact-type rejections, and export/ID attacks pass (`checks/parametric/a9c4475d7cda-adversarial/report.json`).
Official gate: six jobs qualified across thresholds 1/2/3 and seeds 0/17 (`checks/parametric/a9c4475d7cda-qualification/qualification.json`).
Remaining failures: none in the scoped prototype, tests, or retained evidence.
Limit: this is a qualified proposal only—no parameter acceptance, production API change, variant approval, or training admission was performed.
Status: routine maintainer review; inspect the qualification receipt and explicitly accept only if the proposed family is wanted.

## Built artifact

The prototype lives under `repo/generators/a9c4475d7cda/workspace/parametric/`:

- `prototype.py` generates deterministic, fixed-threshold episodes with 1–16 demonstrations and 1–16 queries, distinct inputs, bounded retries, demonstration-only identifiability, and public/private projection.
- `programs/threshold-{1,2,3}.rkt` are the exact materialized rule programs; threshold 2 matches the canonical program byte for byte.
- `adapter.py` and `promotion.json` provide the repository's thin qualification interface without modifying production.
- `evidence/manifest.json` binds the retained source, programs, tests, CLI evidence, adversarial evidence, and official qualification receipt.

## Changed-surface checks

`tests/test_parametric_threshold.py` covers strict integer semantics (including bool/float rejection), canonical-default equality, per-setting output differences, seed determinism, count boundaries, distinct inputs, one-demo finite identifiability, four-query generation, Racket parity, visible-only public IDs, public/private separation, duplicate visible-payload rejection, and adapter contracts.

The official qualification ran all three settings at seeds 0 and 17 with 3 demonstrations and 4 queries. Its receipt remains source-bound to the unchanged production generator and rule. The retained adversarial probe separately exercised seeds 0 and `2**63-1`, all three thresholds, malformed numeric types, hidden/private mutations, visible mutations, duplicate exports, and tampered exports.

## Supplementary tickets

- `ticket-1257fe617c6e2a9e` (`adversarial_witness`): the pinned peer source still generates a lawful ordinary witness where the nearest-pair-only shortcut fits all four canonical pairs but differs from the true output in four cells. This is a bounded no-finding result; no peer source was edited.
- `ticket-48a7bace35d369ce` (`nvarc_visual`): the locked blind prediction for pair 4 was exact. After reveal, the refined rule—move each monochromatic nine-cell plus five columns right when the full translation fits, otherwise leave it in place; preserve all non-plus pixels—matches all 22 pairs. Verdict: `ok`.
