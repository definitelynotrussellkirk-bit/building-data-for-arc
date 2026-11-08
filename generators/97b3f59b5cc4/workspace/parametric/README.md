# Native connectivity family

`connectivity=four` is the exact selected canonical rule. `connectivity=eight`
changes only same-color component segmentation. Generated lessons contain an
interior block that touches a same-color frame tail diagonally but not
cardinally, plus a repeated-color component with the opposite border fate.
This makes the setting demonstrable while refuting global-color and
edge-cells-only shortcuts.

Run focused tests through the packet launcher:

```bash
python3 review.py run python3 -m pytest -q generators/97b3f59b5cc4/tests/test_parametric_connectivity.py
```
