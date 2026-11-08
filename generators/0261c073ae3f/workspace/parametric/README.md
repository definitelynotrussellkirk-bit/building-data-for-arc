# `0261c073ae3f` native parametric family

The canonical `boolean_op="xor"` program is preserved byte-for-byte.  The
alternative `boolean_op="or"` changes only the Boolean combination after both
panels have been normalized.

## Sequential dependency

1. **Step A:** find the full-height color-5 separator, crop each panel to its
   nonzero bounding box, and convert each crop to a binary mask.
2. **Step B:** top-left align those two content-dependent masks on a common
   canvas and apply the episode-selected Boolean operation (`xor` or `or`),
   painting occupied output cells with color 7.

`counterfactual_raw_or.rkt` applies OR to the uncropped full panels.  Its
protected-Racket output differs from the selected normalized-OR output, so the
final answer depends on the Step-A normalized intermediates rather than merely
on the episode setting.

The full six-demo/four-query bank is generated before slicing.  Inputs are
therefore matched across settings and prefix-stable across requested counts.
The first two demonstrations contain overlap plus cells exclusive to each
operand and use unequal translations, refuting XOR/OR confusion, AND,
one-sided, complement, and raw-panel rivals.  The final query is a substantive
30×30 split-panel case with a 26×13 normalized output canvas.

## Reproduction

Run through the packet wrapper so all Racket execution uses the protected
runtime:

```bash
python3 review.py run python3 -m pytest -q \
  generators/0261c073ae3f/tests/test_parametric_0261c073ae3f.py
python3 review.py run python3 \
  generators/0261c073ae3f/workspace/parametric/audit.py \
  --out ../checks/0261c073ae3f/audit --seeds 32
python3 review.py run python3 \
  generators/0261c073ae3f/workspace/parametric/preflight_compat.py \
  0261c073ae3f --out ../checks/0261c073ae3f/qualification
```

The task-local compatibility entry point is necessary because this packet's
shared preflight assumes every canonical `test` split is a list, while this ARC
record stores its single test pair as an object.  The shim normalizes only that
iteration and preserves the original authority hash and standard receipt.

This is authoring evidence only.  Owner acceptance and training admission
remain pending, separate actions.
