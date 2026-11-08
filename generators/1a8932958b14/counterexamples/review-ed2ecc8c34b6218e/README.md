# Counterexamples retained by review-ed2ecc8c34b6218e

- `rotation_baseline.json`: exact baseline seed/window where holding out sample 7
  leaves two monochrome up-right demonstrations. Both the canonical-up-right and
  modal-color rivals fit the demonstrations and differ on the query.
- `strict_scalar_cases.json`: the eleven invalid seed/sample-index values watched
  fail the new red tests before strict validation was added.

Baseline generator SHA-256: `60833338187fe73b858c1c2bb7ff6e118e0023b2092a55492116bfb5dd6c3717`.
The focused task tests cover both contracts; these files preserve the concrete
inputs and baseline finding without modifying the canonical Racket authority.
