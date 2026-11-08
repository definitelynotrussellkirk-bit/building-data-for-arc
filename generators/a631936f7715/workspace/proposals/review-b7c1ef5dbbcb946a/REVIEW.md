# Review — a631936f7715 parametric reconciliation

Task/source: selected generator `1.8.0`, SHA-256 `965a662deb1bad237758745f2b18ad53eda6f8d0bf3c8d3d4febaa74b1e18d30`; canonical rule hash `8097fabedcc2`.
Scope: task-local `component_connectivity ∈ {4,8}` prototype only; `generator.py`, canonical authority, approval state, and prior evidence are unchanged.
Defect → repair: setting-revealing public filenames and 3-demo/1-query evidence became exact visible-byte content IDs, public/private artifact separation, independent demo/query controls, and 3-demo/4-query evidence.
Public contract: each `challenge-<sha256>.json` filename equals SHA-256 of the exact bytes written by `reviewer_support.public_challenge_bytes`; private metadata and query answers do not affect it.
Racket verification: 2 settings × 7 pairs × 2 exact programs = 28 protected executions; all 14 pairs distinguish 4- from 8-connectivity.
Identification: demonstrations alone leave exactly the selected declared setting for both episodes; query answers are not used for selection.
Sampler boundary: exact support is 1,680 unique inputs; requests above the bound fail instead of cloning pairs.
Tests: selected-task staged suite passed 49/49; focused prototype suite passed 7/7.
Adversarial pass: three full-support seeds remained unique and exact-integer; public bytes, IDs, names, and public/private separation all matched the shared contract.
Remaining limits: one retained seed, two declared settings, and one declared rival; this remains a proposed, unapproved prototype rather than production or training admission.
Inherited status: the prior exact-text authority formatting drift remains outside this prototype-only change; no production battery was rerun.
Disposition: routine reconciliation, ready for maintainer review.

## Changed artifacts

- `repo/generators/a631936f7715/workspace/parametric/prototype.py`
  - Enumerates 210 ordered color triples across eight dihedral transforms for exact support of 1,680 non-cloned inputs.
  - Adds duplicate-input rejection and opaque public naming through the shared exact-byte public challenge ID.
- `repo/generators/a631936f7715/workspace/parametric/verify.py`
  - Exposes `--n-train` and `--n-test` independently.
  - Sorts public outputs by public ID, rejects duplicate visible payloads, writes exact public bytes, and keeps setting/program/answer-bearing data private.
  - Checks both Racket programs on every retained demonstration and query, then performs setting selection from demonstrations only.
- `repo/generators/a631936f7715/tests/test_parametric_connectivity.py`
  - Covers independent counts, full finite support, overflow rejection, exact visible-byte IDs, private-field/query-answer invariance, visible-content sensitivity, and public/private materialization.
- `repo/generators/a631936f7715/workspace/parametric/README.md` and `notes.md`
  - Record the reproducible 3-demo/4-query command, exact support, privacy contract, and proposed-only status.

## Evidence

- `checks/parametric-reconcile-final/report.json` — source-bound parameter report, exact programs, 28 Racket executions, and demonstration-only candidate selection.
- `checks/parametric-reconcile-final/materialized/manifest.json` — public IDs/byte hashes and private setting bindings.
- `checks/parametric-reconcile-final/adversarial.json` — finite-support, numeric, privacy, and exact-byte adversarial checks.
- `checks/parametric-reconcile-final/focused-tests.log` — fresh focused prototype regression run, 7 passed.
- `checks/parametric-reconcile-final/static-validation.json` — exact changed-path, source-hash, public-byte, and receipt binding checks.
- `checks/task-tests-final/result.json` — staged selected-task result, 49 passed.

## Supplementary tickets

- `ticket-65c59e52db6ef724` (`tool_reproduction`): completed. The current default battery still has 12 stages and no `task_tests` stage, while the pinned target retains a separate 40/40 task-test receipt. Proposed disposition: accept as an actionable open tooling request. Evidence: `checks/tickets/ticket-65c59e52db6ef724/report.json`.
- `ticket-6f86e10e040c7bbd` (`adversarial_witness`): completed, no peer safety finding. A lowest-color-only rival fits all five canonical examples of `a452b4b4f04a` but is refuted by a lawful multicolor demonstration in the pinned default three-demo lesson using canonical Racket labels. Evidence: `checks/tickets/ticket-6f86e10e040c7bbd/report.json`.
