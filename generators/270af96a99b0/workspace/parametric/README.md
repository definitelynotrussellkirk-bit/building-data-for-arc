# Native parametric family: perimeter tie-break

The selected default is byte-for-byte the canonical program: sort objects by
`(true perimeter, source top row, source left column)`, then crop and top-pack
with one zero column between objects.

The alternate setting changes only the tie-break among equal-perimeter objects:
`smaller_area` sorts by `(true perimeter, occupied area, source top row, source
left column)`.  Inputs are matched across settings.  Every demonstration has a
true-perimeter tie with unequal occupied areas, so the visible labels identify
the episode setting without changing the input distribution.

Causal chain: extract components and measure true perimeter/area -> obtain an
input-dependent ordered component sequence -> crop and place each component in
that sequence.  The output slot for each shape cannot be selected before the
ordered sequence is known.
