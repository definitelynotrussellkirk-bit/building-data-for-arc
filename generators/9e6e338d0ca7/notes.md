# Working notes: 9e6e338d0ca7

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Reconciliation decision — generator v4.1.0

Returns `review-7719bd275d086941:v0001` and `review-d50e23a8ffe7b31e:v0001` independently identified the same teaching defect in source SHA-256 `da9ca7307253f3d1309a278a0994ae0b500023f9609b268b6e99d51b1597e33c`: every generated seed was wall-adjacent, so wall-touch-gated and edge-count shortcuts survived. Version 4.1.0 (`207607de7e991132cbba593495a9ffbf935d61feada8fe404d2f662cf865b063`) preserves all five exact public inputs and the canonical rule, but requires each generalized lesson to contain one interior singleton and one mixed edge/interior two-seed chamber.

This is a targeted curriculum repair rather than a new rule. The remaining seeds still use edge positions, retaining 70.9% wall-adjacent seed cells across the bounded 12,000-case sweep; no production approval or training-admission change is implied. Evidence: `../../../checks/reconciliation/comparison.json` and `../../../checks/reconciliation/adversarial-sampler.json`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d50e23a8ffe7b31e:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `da9ca7307253f3d1309a278a0994ae0b500023f9609b268b6e99d51b1597e33c`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Original source da9ca7307253f3d1309a278a0994ae0b500023f9609b268b6e99d51b1597e33c sampled all seeds on walls. Accepted exact repair 207607de7e991132cbba593495a9ffbf935d61feada8fe404d2f662cf865b063 forces an interior singleton and mixed interior/edge two-seed chamber, refuting the touch-gated rival at11cells and edge-count rival at21cells. Exact Racket parity and bounded focused/sampler evidence in `generators/9e6e338d0ca7/evidence/wall-adjacency-resolution/manifest.json`. Reviewer-reported; owner did not rerun programs. Only these two wall-proxy findings are resolved.

### Assessment or prior finding

## 9e6e338d0ca7

**Reproduced shortcut/domain defect; no source was modified.** Audited generator
SHA-256:
`da9ca7307253f3d1309a278a0994ae0b500023f9609b268b6e99d51b1597e33c`.
Catalog state at execution was approved / `reviewed_safe`; executed rule hash was
`81c0076a1d08`.

The general generator places every singleton chamber seed only in `edge_cells`,
meaning adjacent to a wall. All singleton seeds in the five canonical pairs are
also wall-adjacent. This supports a plausible rival: fill a chamber only when it
contains exactly one seed **and that seed touches a wall**.

I constructed an in-domain counterexample by moving the singleton seed in a
canonical-style chamber from `(2,11)` to the off-wall interior cell `(3,8)`.
The target `self_check` returns no errors; the chamber/seed-count profile remains
lawful. Canonical Racket fills that chamber, while the wall-adjacent-only rival
leaves it unfilled. The input, domain precheck, Racket output, Python intended
mirror, and rival output are retained at:

- `checks/audit/9e6e338d0ca7/input.json`
- `checks/audit/9e6e338d0ca7/precheck.json`
- `checks/audit/9e6e338d0ca7/racket.json`
- `checks/audit/9e6e338d0ca7/intended_python_mirror.json`
- `checks/audit/9e6e338d0ca7/wall_adjacent_only_rival.json`

The supported `arcpuzzles apply` command exited 0; its exact command and source
hashes are embedded in `racket.json`. This demonstrates an accepted
counterfactual that separates the canonical rule from a feature perfectly
correlated by the current generator. It does not prove every generated lesson
is ambiguous, and no repair was requested for this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d50e23a8ffe7b31e-v0001/audit_assets.json), manifest SHA-256 `5c43b610bcd4fc5024678497ab75e9b25b4daf8a64c2a6a5e5ddc2c6ad828e72`.
<!-- arcpuzzles-current-audit-assessment:end -->
