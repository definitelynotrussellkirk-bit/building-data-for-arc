# Winner-width relay parametric family

`mode=canonical` is the selected canonical Racket source byte-for-byte.
`mode=winner_width_relay` composes the same perimeter-sorted stack with a real
input-dependent relay:

1. rank same-color components by true perimeter descending, then color ascending;
2. measure the first ranked crop's width (`1`, `2`, or `3` in the admitted grammar);
3. use that width as a 1-based rank and recolor that ranked crop to color `8`.

The inputs are matched across modes.  Demonstrations begin with width selectors
2 and 3 so fixed-rank, spatial-first, area-winner, bbox-winner, canonical-only,
and winner-height shortcuts are constructively separated with only two examples.
The fourth query is a 30x30 seven-component boundary case with 64 nonzero cells.

The native adapter supports 2–6 demonstrations and 1–4 prefix-stable queries.
`verify.py` performs protected-Racket parity, the finite named-rival audit,
public-turn masking checks, and a wrong-intermediate causal replay.  Native
qualification remains the promotion authority; this workspace does not accept
or admit the family to training.
