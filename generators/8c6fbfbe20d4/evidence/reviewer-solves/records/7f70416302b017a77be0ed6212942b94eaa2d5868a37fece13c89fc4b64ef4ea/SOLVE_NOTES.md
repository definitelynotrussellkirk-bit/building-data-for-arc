# Solve work log

## Prior exposure

Before this blind solve I had not opened task `8c6fbfbe20d4`'s generator, Racket
rule, notes, reference solutions, private labels, or earlier solution
explanations. I had only read the packet-wide instructions and the public
visible examples produced by `python3 solve_episode.py blind prepare`.

## Hypothesis

The input begins with a two-row palette key. Read each key row left to right,
discarding background zeroes. Pair the nonzero colors by position, stopping at
the shorter list. The first-row color in each pair is replaced by the
corresponding second-row color in every later row. Unpaired and non-key colors
remain unchanged. The output is the body below the two key rows, so it has two
fewer rows and the same width.

Evidence from the four visible examples:

- Example 0 pairs `[6, 1, 9]` with the first three colors of
  `[5, 7, 3, 8]`, giving `6→5`, `1→7`, and `9→3`; the extra `8` is unused.
- Example 1 gives `6→7`, `4→9`, `1→2`, and `8→5`, while body colors `2` and
  `3` not used as source-key entries remain unchanged.
- Example 2 pairs only `4→1` and `2→5`; the extra source-key `9` is unpaired
  and remains `9` in the body.
- Example 3 gives `9→7` and `2→3`; the extra target-key `6` is unused.

This also distinguishes ordered pairing from same-column pairing, because the
nonzero key entries occur in different columns.

## Probe and implementation

I made a local visible-example regression check that imports only
`solve-blind/solution.py` and `solve-blind/challenge.json`. It first failed on
the untouched `NotImplementedError`, then passed after implementing the ordered
nonzero-color pairing and applying it to `grid[2:]`.

The two visible queries therefore use these maps:

- Query 0: `4→8`, `6→2`, `7→5`.
- Query 1: `7→9`, `4→5`, `2→6`, `1→3`.

Remaining uncertainty is limited to malformed inputs (fewer than two rows) or
repeated source colors; neither appears in the visible task contract. Python's
ordered `zip` and dictionary replacement implement the simplest rule consistent
with every example.
