# Visible-example solve log

## Exposure declaration

This is an exposed post-repair solve, not a blind solve. I knew the task family
from the generator review and had completed earlier solve episodes for prior
source hashes. During this final episode I used only the new
`solve/challenge.json`; I did not consult the Racket source, private labels, or
reference outputs.

## Hypothesis

Overlay the input with its transpose across the main diagonal. Every nonzero
cell at `(r, c)` remains in place and writes its color to `(c, r)` from an
immutable snapshot.

## Evidence from the visible demonstrations

- Demo 1 contains upper-side markers; the output retains them and adds the
  corresponding lower-side markers.
- Demo 2 contains lower-side markers; the output adds the corresponding
  upper-side markers, ruling out an upper-to-lower-only rule.
- Demo 3 contains an unequal occupied transpose pair at `(1,5)=7` and
  `(5,1)=2`. The output has `(1,5)=2` and `(5,1)=7`, so the pair swaps. This
  rules out copying only into empty partner cells and rules out sequential
  in-place propagation.
- Dimensions and marker colors otherwise remain unchanged.

## Implementation

Copy the grid into an immutable `source` and a separate `output`. Iterate over
nonzero source cells and assign `output[c][r] = source[r][c]`. The visible grids
are square, so every transpose coordinate is valid.

## Alternatives rejected

- Pure transpose: would remove unpaired original markers.
- Upper-only or lower-only copying: contradicted by demos 1 and 2.
- Copy-only-if-empty: contradicted by demo 3's occupied-pair swap.
- In-place mirroring: traversal order would smear one conflict value rather than
  swap the two originals.
