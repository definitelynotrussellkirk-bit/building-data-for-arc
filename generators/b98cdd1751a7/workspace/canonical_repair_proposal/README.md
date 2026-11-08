# Canonical repair proposal for `b98cdd1751a7`

This directory preserves a tested repair without altering the production generator's approved source binding.

The proposal changes only two canonical-generator behaviors:

1. updates the declared authority pin from `62a9653b2441` to the live catalog hash `781a5f8cfaee` and bumps the generator version to `3.1.0`;
2. samples balanced, all-above-canvas-midpoint, and all-below-canvas-midpoint row layouts while preserving the canonical first/last-object-top-row 2+2 split. This defeats the literal canvas-midpoint shortcut identified by the retained audit.

It also includes portable tests that resolve repository and copied-runtime layouts, plus a distribution regression requiring both shifted layout directions and observable disagreement with the shortcut.

Run from the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/b98cdd1751a7/workspace/canonical_repair_proposal/test_generator_repair.py -q
```

`generator.patch` is the exact production-source delta. Owner integration must be followed by canonical re-approval and fresh native parametric qualification because source-bound approval intentionally becomes stale after this change.
