# Native parametric family: 99601629ab88

`mirror_left_right` is the selected canonical Racket source byte-for-byte.
`largest_block_to_top_left` first extracts the divider-bounded matrix and the
physical row/column band sizes, then uses the unique maximum row band and unique
maximum column band to identify a corner. It flips the extracted matrix along
exactly the axes needed to move that input-derived corner to the output's
upper-left.

The sampler is independent of the private setting, supports 2–6 demonstrations
and 1–4 prefix-stable queries, and puts all four corner branches in the four-query
bank. Query four is a dense 30×30, 4×4 lattice stress case. The first two
examples use top-left and bottom-right largest blocks, so the minimum lesson
separates both declared settings and the retained fixed/one-axis shortcut bank.

From the packet root:

```bash
python3 review.py run python3 -m pytest generators/99601629ab88/tests/test_parameters.py -q
python3 review.py run python3 -m arcpuzzles parametric qualify 99601629ab88 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/99601629ab88/qualification --summary
```
