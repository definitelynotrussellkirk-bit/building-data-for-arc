# Solve work log

This is a human work log based only on `solve/challenge.json` during the solve
phase. I had already inspected the task's canonical rule while improving the
generator, so this is **not blind**; that earlier exposure will be declared at
finish. During this phase I did not reopen the generator, Racket authority,
reference solutions, private labels, or earlier solution explanations.

## Visible-example observations

All three training inputs contain exactly one full-height gray (`5`) column.
The output preserves the entire input and adds colored cells on the right at the
same row and equal horizontal distance from that gray column. Colors are
unchanged.

The third training example is especially diagnostic: its width is 14 and the
gray column is index 6, leaving an extra blank column at the far right. The
expected copy of source column 5 is at column 7, so the axis is the gray column,
not the geometric center of the whole grid. The same example mirrors the
connected `9,9` pair as a pair, while training example 2 mirrors the connected
`7,7` pair. Therefore the operation applies to every colored source cell, not
only isolated markers.

## Hypotheses considered

1. **Mirror around the geometric center.** Rejected from visible example 3:
   center mirroring would send source column 5 to column 8, but the output puts
   it at column 7.
2. **Mirror only isolated colored markers.** Rejected from visible examples 2
   and 3, which mirror connected horizontal pairs.
3. **Copy the whole left panel across the gray divider.** Equivalent on the
   shown inputs to mirroring every non-background, non-gray source cell. I used
   the sparse-cell formulation because it leaves the input and any unmatched
   far-right padding unchanged.

## Revision 1

Implementation finds the unique full-height gray column, copies the grid, and
for each nonzero/non-gray cell to its left writes the same color to
`2 * divider - source_column`. It raises on an ambiguous/missing divider rather
than silently choosing an axis. The extra far-right column in the off-center
example remains blank because it has no source counterpart.

Remaining uncertainty before checking: none about the visible transformation;
masked-query correctness remains intentionally unavailable.
