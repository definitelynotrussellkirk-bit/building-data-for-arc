# b9e736518d82

Version `4.0.0`, canonical rule hash `b8c560eed7ae`.

The input contains orange (`7`) walls around a latent one-cell-wide orthogonal
channel. The channel is a simple boundary-to-boundary path with 2–6 turns. At
each bend the walls include the outer corner cell as well as the cardinal side
neighbors.

The generator cycles three canonical semantic branches across every three
sample indexes:

1. no maroon marker: the authority uses its row-major adjacent-orange component
   choice and fills the selected channel cyan (`8`);
2. a maroon (`9`) marker on a straight channel cell: fill the whole channel,
   including the marker;
3. a maroon marker at a bend: removing it splits the channel, and only the larger
   side is filled cyan.

Exact controls are `grid_h` and `grid_w` (10–20), `turn_count` (2–6), and
`marker_mode` (`none|straight|turn`). `self_check` reconstructs the selected
channel, validates simple-path geometry, endpoints, turns, marker semantics, and
exact orange walls. The canonical Racket program remains the label authority;
the Python authority mirror exists only for tests and audit parity.

The independent reusable probe is `workspace/reference_probe.py`. The selected
task tests are under `tests/test_generator.py`.
