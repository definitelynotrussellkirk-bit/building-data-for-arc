# Parametric prototype: rectangle move distance

This proposal preserves the marker-8 missing-corner interpretation and full
rectangle reconstruction.  The hidden `move_distance` is either:

- `1` — the exact canonical/default Racket program;
- `2` — move the reconstructed rectangle two diagonal cells toward the marker.

All generated inputs are setting-neutral and reserve enough margin for both
moves.  The default materialization has three demonstrations and four distinct
queries sized 10×10, 16×20, 24×26, and 30×30.  The largest query contains four
substantive, widely separated rectangles.  Public query answers remain private;
`adapter.py` and `promotion.json` provide a narrow future-promotion contract
without changing production behavior.
