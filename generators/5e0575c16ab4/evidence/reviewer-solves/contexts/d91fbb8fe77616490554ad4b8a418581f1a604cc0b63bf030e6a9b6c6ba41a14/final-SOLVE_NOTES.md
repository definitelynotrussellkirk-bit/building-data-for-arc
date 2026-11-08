# Solve notes

These are a human work log based only on `solve/challenge.json` during the solve episode.

## Hypothesis

A nonzero color is extended across a row only when all of the following hold:

1. the color occurs exactly twice in the entire input;
2. both occurrences are in the same row;
3. every cell strictly between them is zero.

The endpoints and blank cells between them become that color. Everything else is copied unchanged.

## Evidence from visible examples

- Training example 1 has two independent positive bridges.
- Training example 2 rejects a row-local shortcut: color 5 forms two apparent row pairs but occurs four times globally, so neither pair changes; color 3 occurs exactly twice and fills.
- Training example 3 rejects ignoring blockers: the two 7s share a row but color 8 lies between them, so they remain unchanged; the 6 pair fills.
- Training example 4 rejects orientation/count shortcuts: the two 8s are vertical and the 9 appears three times, so both are unchanged; the two 3s fill.

## Implementation

Build a global color-to-position index, then apply the three guards before painting an inclusive horizontal segment into a copied grid. The input is not mutated.
