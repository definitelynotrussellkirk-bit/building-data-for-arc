# Proposed color-swap-location family

Parameter: `swap_location = source | reflection`. `source` is the selected canonical rule byte-for-byte: swap the original two-color shape and reflect an unswapped copy. `reflection` preserves the original and swaps only the reflected copy. The single separator, geometric reflection, two-color role, and empty opposite half remain invariant.

Inputs are independent of the private setting. Every 2–6-demo prefix identifies the setting, four distinct queries are available independently, and query four is a substantive 30×30 case. `visible_turn()` emits one current masked query without setting, seed, answer, ordinal, or total-count hints.

```bash
python3 review.py run python3 -m pytest -q generators/c6a422753abe/tests
python3 review.py run python3 generators/c6a422753abe/workspace/parametric/verify.py --out ../checks/parametric/c6a422753abe
```

This is a proposed task-local extension; it is not accepted or training-admitted.
