# Native transform/overlap family for 63784d19dd2d

`overlap_mode=transform_only` is the exact selected canonical Racket program.
`overlap_mode=mark_b_overlap` first infers the unique transform mapping panel A
to B, applies it to C, then recolors to red only transformed-C cells occupying
coordinates also occupied in B.

The sampler uses matched inputs across settings, supports 2–6 demonstrations
and 1–4 prefix-stable queries, and always constructs partial overlap. The first
two demonstrations reject the declared finite shortcuts. The largest lawful
input is 9×29: with three equal N×N panels and two full-height separator columns,
N=9 gives width 29 and N=10 would exceed ARC's 30-column limit. Exact 30×30 is
therefore not compatible with this unchanged panel grammar.
