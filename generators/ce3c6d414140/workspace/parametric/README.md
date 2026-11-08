# Proposed parametric extension: shift distance

This prototype leaves the selected production generator and canonical Racket
rule unchanged. It varies one meaningful rule parameter:

- `shift_distance`: allowed values `1` and `2`; canonical/default value `1`.
- Cells on each object's bounding-box bottom row or rightmost column still stay
  fixed. Every other object cell moves right by the episode's distance.
- The value is chosen once per episode and reused for all three demonstrations
  and the query.

Both exact Racket programs are retained in `rules/`. The probe derives every
label by executing those programs with the packet's protected Racket bridge,
checks a Python audit mirror, verifies that the alternative parameter predicts a
different output for every pair, and writes public challenge JSON with query
answers omitted.

From the outer extracted packet, run:

```sh
python3 review.py run python3 generators/ce3c6d414140/workspace/parametric/prototype.py \
  --out ../checks/parametric/shift-distance
```

The evidence is bounded to the retained seeds and examples. It does not approve
this variant for production, prove identifiability against every possible rule,
or change the selected authority hash.
