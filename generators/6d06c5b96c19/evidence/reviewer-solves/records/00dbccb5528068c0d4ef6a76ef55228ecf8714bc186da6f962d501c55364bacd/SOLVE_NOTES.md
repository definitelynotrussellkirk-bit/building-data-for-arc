# Solve work log

I had not opened this task's generator, rule, reference solution, private labels,
or prior solution notes. I only saw the visible examples printed by
`solve_episode.py blind prepare` and the identical public README.

## Revision 1 — crop and marker-controlled cyclic row shift

Observation: every input has `H` rows and `H+1` columns, while every output is
`H x H`. The first column is an instruction strip: it consists of one color-2
cell and otherwise a repeated filler color. Removing that column exactly
produces train examples 0 and 1, where the color-2 marker is in row 0.

In train example 2 the marker is in row 1. Removing the first column gives all
output rows, but in input order; the observed output moves the last cropped row
to the top. This is a cyclic downward row shift by the marker's zero-based row
index (equivalently, move the last `marker_row` rows to the front).

Program: find the color-2 row in column 0, remove column 0, and cyclically shift
the cropped rows down by that amount. I use a no-marker fallback of zero only as
defensive handling; all visible examples contain exactly one marker.

Alternative considered: simply delete the first column. Train example 2 rejects
that. No visible example distinguishes alternate verbal descriptions of the
same cyclic permutation, but the implemented permutation matches all three.
