# 36adc51834d3

A command token at `(0,0)` selects how to transform the remaining monochrome object after the token is removed and the object is cropped: `1` identity, `2` clockwise 90°, `3` 180°, `4` counterclockwise 90°.

Kind: `per_puzzle`. Reviewed version: `2.0.1`. Canonical `RULE_HASH`: `112ba59ebc7e`.

The sampler exposes five exact, pixel-observable axes (`grid_h`, `grid_w`, `blob_size`, `cmd`, `color_relation`). Four consecutive sample indices cover all commands, shapes have four distinct quarter-turn views, and every declared override value is constructive in every difficulty band. The canonical Racket rule remains the sole output authority.
