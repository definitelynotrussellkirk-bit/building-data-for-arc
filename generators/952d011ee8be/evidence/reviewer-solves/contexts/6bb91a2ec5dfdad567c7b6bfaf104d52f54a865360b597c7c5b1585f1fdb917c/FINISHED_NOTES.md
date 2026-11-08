# Solve work log

I had no earlier exposure to this task's generator, Racket rule, reference
solution, private query labels, or prior solution explanation. I used only the
visible examples produced by `python3 review.py blind prepare`.

## Observations and hypothesis

The first two rows are a legend/header.  The first row contains three isolated
nonzero colors other than the structural color 5 and marker color 1.  The first
all-5 row separates that header from a set of chambers whose walls are color 5.
The output leaves the header and walls unchanged, removes every 1 marker, and
fills each chamber uniformly.

Counting 1s per chamber explains the fill color in left-to-right legend order:
one marker selects the first color and two select the second.  Both zero and
three markers select the third color, so the compact rule is cyclic:
`palette[(marker_count - 1) mod 3]`.

I considered a non-cyclic lookup such as 0->third, 1->first, 2->second,
3->third.  The visible data cannot distinguish that wording from modulo 3, but
the cyclic formulation is simpler and generalizes without an arbitrary cutoff.

## Program design

1. Find the first row made entirely of 5s.
2. Read the distinct legend colors above it in row-major order, excluding
   0, 1, and 5.
3. Below the separator, find every four-connected component of non-5 cells.
4. Count 1s in the component and fill the whole component from the cyclic
   palette.  Preserve the header and every 5 wall.

The component formulation does not assume fixed rectangle sizes or a fixed
number of chambers.  Remaining uncertainty is limited to unseen malformed
layouts (for example, no full-width separator or repeated legend colors); the
visible task consistently supplies the stated structure.
