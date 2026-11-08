# Retained counterexample: row-1 gating matters

The rival `all_top_non_background` treats every non-background cell in row 0 as
an active vertical XOR marker. It fits all six usable labeled canonical records,
but the input in `input.json` contains an inert top marker at column 13 because
rows 0 and 1 are both color 2 there.

The authoritative Racket output in `racket.json` preserves that column. The rival
changes all 19 body cells in the column, beginning with `(1, 13): 2 -> 8` and
ending with `(19, 13): 8 -> 2`. `intended-python.json` is an independently spelled
oracle and exactly matches Racket. The focused regression test
`test_strongest_canonical_shortcut_fits_all_labels_and_exact_decoy_refutes_it`
covers this witness.

Replay from the packet root:

```sh
python3 run_with_racket.py python3 -m arcpuzzles apply b38782448e7b \
  --input generators/b38782448e7b/counterexamples/review-0bdef3bb637751b2-v0001/input.json \
  --out ../checks/replayed-shortcut-racket.json
```

The supported apply receipt records canonical rule hash `06479b7ecc39` and the
reviewed generator SHA-256.
