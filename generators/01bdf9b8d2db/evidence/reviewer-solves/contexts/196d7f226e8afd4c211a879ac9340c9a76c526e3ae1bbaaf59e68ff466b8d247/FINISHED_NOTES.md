# Solve work log

## Exposure record

Before this solve I had read only the packet-level instructions and the visible examples produced by `python3 review.py blind prepare`. I did not inspect this task's generator, Racket rule, reference solution, private labels, audit records, or the assigned repair generator.

## Revision 1 — connected-region flood fill

The color 5 forms walls and outer borders. Every 4-connected component of cells that are not 5 contains one colored seed and otherwise zeros. In each training output, all cells in that component are replaced by the seed color while the 5 walls stay unchanged. This also explains the irregular lower-right component in training example 1: the partial internal wall remains 5, but the area connected around it is filled with 9.

I implemented a breadth-first search over every non-5 component, collect its nonzero seed color, and fill the entire component with that color. A component without a seed is left unchanged. The visible examples show one seed per component; multiple seeds in one component remain an untested case.
