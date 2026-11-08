# Native parametric family

`mode=canonical` is the exact selected canonical Racket source. Inputs retain the
three anchor colors and add one zero cue at an edge midpoint that the canonical
rule ignores. `mode=cue_rotate_erase` first expands the canonical 10×10 symbolic
template, rotates that intermediate clockwise according to the cue, then erases
the complete monochromatic component containing intermediate cell `(0,1)`.

The fixed source task is intrinsically 5×5 → 10×10, so a 30×30 case would change
the source morphology rather than stress the same rule. Four demonstrations cover
all four cue directions; four private queries use fresh palettes and are exposed
one at a time by `public_turn`.
