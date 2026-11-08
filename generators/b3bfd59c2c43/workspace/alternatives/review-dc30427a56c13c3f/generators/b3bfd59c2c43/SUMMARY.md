# b3bfd59c2c43 — Recolor the Outermost Layer

Version: `2.0.0`  
Selected rule pin: `28b8cf49f820`

Inputs contain exactly two separated, thick 4-connected occupied components on
one of the three canonical canvas/palette profiles. The selected rule treats all
occupied colors as one binary mask per component and recolors exactly the
outermost cardinal layer to cyan (`8`); deeper cells keep their original color.
Off-grid exposure counts as boundary exposure.

The sampler cycles every three sample indices through:

1. `canonical` — separated monochrome thick components;
2. `edge` — a solid component flush to a canvas edge, refuting a shortcut that
   ignores off-grid neighbors; and
3. `multicolor` — one connected solid component split across two colors,
   refuting a shortcut that peels each color separately.

The only advertised exact control is `canvas_profile = 11x15 | 12x12 | 13x15`.
Every value is constructively honored and recoverable through
`observe_overrides(grid)`. `self_check` accepts all three canonical inputs and
requires two colors, two moat-separated components, and a nonempty interior in
each component.

Focused regressions are in `tests/test_generator_b3bfd59c2c43.py`. The reusable
source-bound lesson census is `workspace/lesson_probe.py`.
