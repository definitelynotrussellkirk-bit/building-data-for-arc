# Solve work log

## Exposure declaration before solving

I had not opened the task's generator, canonical rule, reference solution, private
query labels, audit evidence, or any generator in the repair packet. I used only
the visible examples printed by `python3 review.py blind prepare` and the local
visible-only checker.

## Revision 1 — harness diagnostic

The packet-provided `NotImplementedError` stub was checked with intent
`diagnostic_probe`. It failed all three visible examples with execution status
`error`, confirming that the checker was exercising this file before I wrote a
solution.

## Revision 2 — two-column tile-order reversal

Observation: every nonzero pattern occupies columns in aligned two-column cells.
The output does not mirror pixels within those cells. Instead, it reverses the
left-to-right order of all width-2 column tiles while preserving the order of the
two columns inside every tile and leaving row positions unchanged.

For width 10, the output column order is therefore
`[8, 9, 6, 7, 4, 5, 2, 3, 0, 1]`. This explains all three demonstrations:

- the symmetric 2×2 motifs move from the anti-diagonal to the main diagonal;
- the asymmetric 2×2 motifs retain their internal orientation while their block
  positions move from the main diagonal to the anti-diagonal;
- the sparse motifs at block columns 2, 1, 0 move to block columns 2, 3, 4.

Implementation: split each row into consecutive two-column tiles, reverse the
tile list, and flatten it. The visible grids all have even width. The code also
behaves deterministically for an odd width by treating the last one-column slice
as a final tile, though that case is not supported by visible evidence.

Alternative rejected: ordinary horizontal reflection. It would reverse the two
pixels inside each motif and fails the asymmetric second demonstration.
