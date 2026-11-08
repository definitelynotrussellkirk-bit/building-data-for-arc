# Post-repair visible-only solve notes

This is a human work log based only on the visible examples in `solve/README.md`
and `solve/challenge.json`. I had already seen the task rule while reviewing the
generator, so the finish declaration must say `earlier-exposure yes`. During this
solve I did not reopen the generator, Racket source, canonical data, reference
solutions, private labels, or an earlier solution explanation.

## Observations

- Every input has two equal vertical bars of color 3 and two equal vertical bars
  of color 8.
- The output keeps each bar pair and extends it both upward and downward.
- The two branches move outward: the left branch moves left and the right branch
  moves right.
- Horizontal displacement increases by one only after a full block equal to that
  color's bar height. Example 2 makes this especially clear: the height-4 green
  bars produce four output rows at each displacement, while the height-1 cyan
  bars change column on every row.
- When a green and cyan ray occupy the same cell, the visible examples use color
  6 rather than one color overwriting the other.
- Rays are clipped at the grid boundary; output shape equals input shape.

## Implemented hypothesis

For each nonzero color independently, find its two columns and contiguous shared
row interval. For every row, compute the number of whole bar-height blocks from
that interval (zero inside it, then 1, 2, ... outward). Draw the left column minus
that step and the right column plus that step. Merge different colors as 6.

I stopped after this single hypothesis matched every visible example. I did not
manufacture a failed revision because the examples distinguish the height-scaled,
bidirectional, overlap-aware rule directly.
