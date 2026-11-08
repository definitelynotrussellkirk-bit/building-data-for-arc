"""SIDEBAR-STAMP concept family: a sidebar recipe (texture swatch, glyph,
corner dot, rotation bar) stamps a textured upscaled glyph onto the field.

Closes the a32d8b75 eval-distribution hole (the last of the flattened
gap frontier): each sidebar walled off by a full-height magenta column
holds a 3x3 texture swatch (applied with its two colors SWAPPED), a
glyph, a dot whose corner inside its box picks which field corner to
anchor at, and a 2-cell bar acting as a 4-way rotation pointer (vertical
hugging its box top = identity, bottom = 180; horizontal hugging the
right = clockwise, left = counter-clockwise). The answer is the field
with each glyph upscaled x3 and painted in the swapped swatch texture at
its anchored corner; the hidden test carries TWO sidebars.

Parity: the shared bridge helper from the extraction family proves the
Python `apply` byte-exact against the Racket `program` (>=25 seeds in
gen1's __main__).
"""
from puzzle_generators.generic.concepts.extraction import parity_check  # noqa: F401
