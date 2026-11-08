# Visible-only solve notes

This is a human work log made from the public presentation printed by
`solve prepare`. I did not reopen the generator, Racket rule, reference
solutions, or private labels during this solve. I had earlier rule exposure from
the required generator repair and will declare that at finish.

## Hypothesis

Each input `2` independently proposes a `5` exactly one row down and one column
to the right. The input is copied first. The proposed cell changes only when it
exists and was `0` in the input; every original nonzero cell is preserved.

Evidence from the visible demonstrations:

- Train 0: all three `2` cells have empty in-bounds lower-right neighbours, and
  exactly those three cells become `5`.
- Train 1: the `2` at `(0,6)` points to existing `4` at `(1,7)`, which remains
  `4`, while the other three markers create `5`. The unrelated `6` is inert.
- Train 2: the marker at `(6,6)` is clipped by the bottom/right boundary and
  creates nothing; the other three markers create `5`.

This distinguishes the rule from both “overwrite every destination” and “every
nonzero input cell casts.” The implementation consults the original input when
testing destination emptiness and writes into a copied output.
