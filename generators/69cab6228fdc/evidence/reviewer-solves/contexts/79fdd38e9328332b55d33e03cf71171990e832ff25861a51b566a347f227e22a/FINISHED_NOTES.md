# Visible-only solve log

This is a human work log, not a captured model trace. I had earlier exposure to
the task rule while repairing its generator, so this episode is **not blind**. I
did not consult the generator, Racket source, reference solution, private labels,
or prior solution notes after `solve_episode.py prepare`.

## Visible observations

- Every input begins with two sparse rows whose nonzero cells line up by column,
  followed by an all-zero third row.
- In train example 1, the aligned pairs are `3→2`, `6→8`, and `7→5`.
  Removing the first three rows and applying those substitutions reproduces the
  shown output exactly.
- Train example 2 gives `6→2` and `1→9`; body colors `3` and `5` are absent from
  the legend and remain unchanged. This rules out replacing every non-source
  color with zero.
- Train example 3 gives `1→7`, `8→4`, and `5→9`; body colors `2` and `6` again
  remain unchanged. This also confirms that all aligned pairs, not just the
  first, are used.

## Hypothesis and implementation

Interpret rows 0 and 1 as a source/target color legend. Discard those two rows
and the all-zero separator row 2. For every cell in rows 3 onward, replace a
legend source by its aligned target and leave every other value unchanged.

I implemented that rule directly. The three visible examples determine the crop,
mapping direction, use of multiple pairs, and passthrough behavior, so I did not
manufacture a failed revision.
