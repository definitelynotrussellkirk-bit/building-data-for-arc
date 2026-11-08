# Solve work log

## Exposure declaration before solving

I had already read and repaired this task's generator and had seen the selected
Racket-backed rule behavior before this solve episode. I therefore treat this as
an exposed post-repair validation, not a blind solve. During this episode I used
only the prepared visible examples and did not reopen the generator, Racket rule,
reference solutions, or private labels.

## Revision 1 — per-row header recoloring

All three visible examples preserve shape and background. In rows whose first
cell is nonzero, every later nonzero cell changes to that first-cell color; cells
already matching it remain unchanged. Rows whose first cell is zero are copied
unchanged, including their nonzero payloads. This explains the contrasting row
behaviors in every visible example and rules out a single global replacement
color.

Implementation: deep-copy the grid; for each row with a nonzero column-0 header,
replace each nonzero cell in columns 1 onward by the header. Preserve zero cells,
all column-0 cells, and every payload in headerless rows.

Remaining uncertainty before checking: none within the visible distribution;
ragged inputs are also handled row-by-row without assuming a shared width.
