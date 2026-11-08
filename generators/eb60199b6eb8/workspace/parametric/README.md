# Native parametric family

`closure=horizontal_only` is the exact canonical program.  The alternate setting
runs canonical horizontal completion first, then completes only columns with
exactly two same-colored cells in that frozen intermediate.

From the packet root:

```sh
python3 review.py run python3 -m pytest generators/eb60199b6eb8/tests/test_parametric_eb60199b6eb8.py -q
python3 review.py run python3 -m arcpuzzles parametric qualify eb60199b6eb8 \
  --out ../checks/eb60199b6eb8/qualification --summary
```
