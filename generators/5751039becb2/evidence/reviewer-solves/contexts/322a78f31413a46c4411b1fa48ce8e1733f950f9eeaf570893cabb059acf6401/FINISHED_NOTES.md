# Solve work log

## Exposure

Before this solve I had read only the packet-wide instructions and the generated
assignment duties. I had not opened task `5751039becb2`'s generator, Racket rule,
reference solution, private labels, audit records, or prior solution notes.

## Revision 1 — same-colour diagonal membership

The outputs preserve exactly the nonzero cells that have a diagonally adjacent
cell of the same colour (one of the four corner-neighbour directions):

- Train 0 removes the lone `5`; every retained nonzero cell lies in a same-colour
  diagonal run.
- Train 1 removes the isolated extra `2` and the lone `8`; the other `2`s, `9`s,
  and `6`s form diagonal runs.
- Train 2 removes the vertical pair of `1`s, showing that ordinary connectivity
  or a component-size threshold is insufficient. The retained `4`, `7`, and `2`
  cells form slope `+1` or `-1` diagonal runs.

I considered "remove singleton components" first, but Train 2 rejects it because
its two-cell vertical component is removed. I also considered preserving every
straight line, but the same example shows only diagonal orientation is accepted.

The program infers the background as the most frequent colour, copies only cells
with a same-colour diagonal neighbour, and therefore supports diagonal runs of
any length in either direction. It does not assume that a colour has only one
component: Train 1 requires retaining one `2` component while deleting another.

Predicted queries:

- Query 0 keeps the three diagonal `1`s, the upper two diagonal `9`s, and the two
  diagonal `5`s; it removes the horizontal `2` pair and isolated lower `9`.
- Query 1 keeps the diagonal `2`, `4`, and `9` runs and removes the lone `5`.

Remaining uncertainty: the visible examples all use `0` as background. Inferring
the modal colour is a conservative generalization, but no visible example tests a
nonzero background or a tie for most frequent colour.
