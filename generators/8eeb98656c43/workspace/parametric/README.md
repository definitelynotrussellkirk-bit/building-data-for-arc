# Native parametric family: mirror, then measure the orange ray

This family preserves the exact canonical program as the default setting and
adds one bounded alternative:

- `canonical`: mirror only red (`2`) cells from the left half and paint the
  reflected copies orange (`7`).
- `ray_tail`: run the canonical mirror first.  A unique color-1 marker on the
  center axis reads the first contiguous orange run to its right, then appends
  an equal-length color-1 tail.

The source grid contains the red run but no orange run.  Therefore the tail's
position and length are not available before Stage A.  The protected
counterfactual keeps the mirror but substitutes a fixed one-cell tail; every
sample uses a run of length at least two, so the ablation changes the final
output.

`audit.py` is a reusable bounded audit.  It sweeps all declared demo/query
count combinations, matched settings, complete query-bank prefixes, the 30x30
case, and protected-Racket replay.  Its reports are reviewer evidence only;
they do not imply owner acceptance or training admission.
