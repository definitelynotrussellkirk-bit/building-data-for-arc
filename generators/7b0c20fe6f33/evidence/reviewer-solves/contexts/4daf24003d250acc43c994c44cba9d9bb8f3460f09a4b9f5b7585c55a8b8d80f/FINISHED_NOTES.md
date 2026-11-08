# Solve work log

## Exposure declaration

Before this solve I had already reviewed and repaired this task's generator and
had seen its rule authority, so earlier rule exposure is **yes**. During this
solve phase I used only the prepared visible challenge and did not consult the
generator, Racket source, reference solutions, or private query labels.

## Revision 1 — marker vector translates the whole green object

Across all three visible examples, the output preserves every input cell and
adds one cyan (8) copy of every green (3) cell. The displacement equals the
vector from the unique blue (1) marker to the unique red (2) marker:

- example 0: blue `(2,0)` to red `(6,5)` gives `(+4,+5)`; the three green
  cells at `(3,1),(3,2),(4,1)` reappear at `(7,6),(7,7),(8,6)`;
- example 1: `(+5,+1)` moves all four cells, not merely the first three;
- example 2: `(-2,-1)` moves all five cells, showing negative directions and
  preservation of a non-rectangular object.

I implemented the transformation per output cell: preserve markers first, then
paint cyan when the inverse-translated input cell is green, otherwise preserve
any other nonzero input cell. This directly supports both query directions and
all visible motif sizes. Remaining uncertainty is limited to collision policy,
which the visible examples do not exercise; marker preservation is the safest
visible-consistent priority.
