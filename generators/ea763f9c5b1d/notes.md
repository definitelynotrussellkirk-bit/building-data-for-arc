# Working notes: ea763f9c5b1d

## Current review decision

Built a native, task-local two-setting parametric family without changing the selected production generator or canonical ledger.

- `area_parity` is the byte-exact canonical default: odd-area nonzero components become 3 and even-area components become 4.
- `anchor_threshold` is the alternative: find the unique red component, bind its input-dependent area `k`, then paint every component 3 when its area is below `k` and 4 otherwise.
- The alternative has a real A→intermediate→B dependency. A protected-Racket counterfactual changes only `k` to `k+1`; on the retained qualified query this changes 10 final cells.
- Episodes support 2–6 demonstrations and 1–4 queries. Inputs are setting-matched, deterministic, prefix-stable, query-count independent, and expose only visible demonstrations plus one query input at a time.
- The fourth query is a substantive 30×30 scene with 12 components of sizes 2–12, 24 occupied rows, 24 occupied columns, and boundary contact.

## Evidence retained

- `workspace/parametric/evidence/current/summary.json`: 640 lessons, 6,720 finite-rival checks, 640 public-projection checks, and 68 protected-Racket evaluations; no failures in the declared bounded audit.
- `workspace/parametric/evidence/manifest.json`: source-bound native inventory.
- `checks/ea763f9c5b1d/qualification/qualification.json`: native qualification for both settings at seeds 0 and 17, three demonstrations and four queries.
- `checks/ea763f9c5b1d/sequential-witness/witness.json`: source-bound protected-Racket causal witness.
- `checks/ea763f9c5b1d-tests/result.json`: copied-runtime result, 24 tests and 26 subtests passing.

The existing generator test had a copied-runtime portability defect: it derived the canonical path from a fixed parent depth and imported the unstaged package namespace directly. The test now uses `reviewer_support.find_root`, `canonical_path`, and `load_selected_generator`.

## Limits / next action

The rival inventory and sampled seeds are finite; this is not a proof against arbitrary programs or a measured learning result. Exact-source owner acceptance and training admission remain pending. The next action is owner-side admission of this exact qualification/witness bundle, not another reviewer-side redesign.
