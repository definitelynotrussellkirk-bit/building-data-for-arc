# a4a506dda35f — Frequency-Sorted Color Bar

Count every nonzero cell by color, sort colors by frequency descending and by
numeric color ascending on ties, then emit one row containing each color once
per counted cell.

The repaired sampler uses six observable layout profiles and four observable
palette profiles. It preserves all four canonical shape families, includes
adjacent same-color cells to distinguish cell count from connected-component
count, and alternates tied and distinct frequency profiles so the numeric tie
break is taught explicitly. Frequency signatures and their assignments to
colors vary independently of shape and palette, preventing a profile lookup
from replacing actual counting. The exact supported output codomain has 552
bars.

Kind: `per_puzzle`. Generator version: `3.1.0`. Canonical rule hash:
`639443b5cb4a`. Approval remains a catalog/maintainer decision.
