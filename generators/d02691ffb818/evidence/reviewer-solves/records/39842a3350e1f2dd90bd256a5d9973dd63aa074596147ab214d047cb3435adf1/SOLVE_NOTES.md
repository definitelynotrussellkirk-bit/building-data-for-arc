# Visible-example solve log

This is a human work log based only on `solve/challenge.json`. I had earlier rule
exposure from reviewing the assigned generator, so this is an exposed solve, not
a blind solve. I did not consult the generator, Racket rule, private labels, or a
prior solution record during this episode.

## Hypothesis 1

Every blue input marker (color 1) independently stamps orange (color 7) onto a
fresh zero grid at its own location and the four one-step diagonal locations.
Out-of-bounds diagonal arms are clipped, and stamps combine by set union.

Visible evidence:

- The first pair shows separated markers becoming five-cell diagonal X shapes.
- The second pair includes top- and left-border markers, whose out-of-grid arms
  disappear while their centers and in-bounds diagonals remain.
- The second and third pairs contain nearby markers; their orange contributions
  overlap without preserving blue centers or adding orthogonal arms.

I implemented exactly that geometry while preserving the input dimensions. No
alternative rule remained necessary after checking all three demonstrations.
