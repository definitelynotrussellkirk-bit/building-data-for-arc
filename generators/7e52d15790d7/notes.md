# Working notes: 7e52d15790d7

## 2026-10-24 review-d6519a124d84a876

### Decision

Keep the production generator and its exact canonical Racket source unchanged. Add an opt-in parametric family under `workspace/parametric/` with two episode-fixed parameters:

- `metric`: `perimeter` or `area`
- `direction`: `descending` or `ascending`

The default `perimeter/descending` setting returns the canonical program bytes exactly. Non-default programs are derived by guarded one-occurrence substitutions, so an upstream source drift fails closed rather than silently changing a different expression.

### Built

- `workspace/parametric/prototype.py`: deterministic matched input streams; 2–6 demonstrations; 1–4 stable-prefix queries; Python mirror; protected-Racket execution; finite-rival teaching certificate; strict public/private materializer and verifier.
- `workspace/parametric/adapter.py` and `promotion.json`: native promotion-v1 interface and exact parameter/count contract.
- `workspace/parametric/README.md`: runnable materialize/verify commands and admission boundary.
- `tests/test_parametric_7e52d15790d7.py`: exact default-source, count independence, setting identifiability, 30×30, Racket parity, public projection, tamper/extra/symlink rejection.
- Existing canonical test lookup was made portable through `reviewer_support`, because the packet's staged task-test runtime does not preserve a fixed parent depth.

The third query is a 30×30 six-component case with 76 nonzero cells touching all four boundaries. Inputs are setting-neutral; all four settings receive identical demonstrations/queries, while every demonstration distinguishes all four candidate settings.

### Verification

- Focused task tests: **14 passed**.
- Protected Racket edge matrix: minimum and maximum count contracts, all four settings, **52/52** setting/pair executions matched the Python mirror (12 minimum-count plus 40 maximum-count executions).
- Materialized seed 17 batch: 4 episodes, 3 demonstrations and 4 distinct queries each; **28/28** chosen-setting Racket labels matched.
- Public export checker: 4 public files, no findings.
- Separate verifier self-review: forged source/runtime/parity metadata, manifest-count drift, empty nested directories, and declared unreferenced files are all rejected.
- Native evidence manifest: `workspace/parametric/evidence/manifest.json`, SHA-256 `260252b29a658a9c30e9c6a1694d80387b503d9fbadd5ae5dd0943070317bb77`.
- Current verification report: `workspace/parametric/evidence/current/verification.json`.

### Admission boundary

This is reviewer-built proposed evidence only. `training_admitted` remains false; owner qualification, acceptance, and downstream training admission are separate decisions.
