# Native parametric family

The exact canonical default keeps even block rows and columns flipped. The two
phase parameters retain the existing parity-phase prototype. `finish=tile_only`
returns that 3×3 mosaic. `finish=erase_center_component` then finds the complete
monochromatic component containing the central block's top-left seam cell `(N,N)`
and erases it to color 0. That second stage consumes the phase-specific mosaic;
a wrong phase changes the component and final answer.

Inputs are matched across all eight settings. The first three demonstrations use
sides 3, 4, and 5; the four-query bank uses sides 4, 7, 8, and 10, so the final
query exercises a substantive 30×30 output. Queries are exposed one at a time by
`public_turn`.

`verify.py` is the task-local regression entry point. It replays the current
three-parameter API through the protected Racket bridge, checks stored labels,
teaching rivals, one-query masking, and first-turn prefix stability.
