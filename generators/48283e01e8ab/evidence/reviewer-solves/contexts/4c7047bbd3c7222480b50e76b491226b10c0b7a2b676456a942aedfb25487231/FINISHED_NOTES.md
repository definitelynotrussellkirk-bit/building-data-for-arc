# Post-repair visible-example solve

This is an exposed solve: the author previously inspected this task's generator
and reference during repair. During this solve phase I read only the public
challenge/preparation display and my own code. I did not open generator code,
Racket source, private query labels, or previous solution explanations.
These notes summarize decisions and experiments; they are not a token-level trace.

## Revision 1 — component recoloring

All four visible demonstrations preserve dimensions and non-6 cells. The
working hypothesis groups 6s by orthogonal adjacency, maps component sizes
2/4/5/6 to colors 9/8/3/5, and distinguishes straight three-cell components
(color 2) from bent ones (color 4). Demonstrated sizes 1, 7, and 8 remain 6.
This supports an unchanged-color fallback for other unrecognized sizes; it does
not prove that extension for unseen sizes.

`visible_probe.py` reads only visible training pairs and records component
counts and output colors in `visible-observations.json`. It also checks whether
diagonal grouping would merge cells that receive different visible colors,
which distinguishes the orthogonal component interpretation in these examples.
The implementation copies the input and computes every component on the original
grid, so earlier recoloring cannot change connectivity.

The visible-only probe found one consistent output color for each observed
class and preserved every non-6 cell. Diagonal grouping creates mixed-color
components in examples 0, 1, and 2 (counts 1, 2, and 1), supporting orthogonal
grouping. The supported checker completed revision 1 and passed 4/4 visible
examples. Both masked queries executed; their correctness is withheld.

I stopped because the hypothesis matches all demonstrations, its component
interpretation has a visible separating observation, and the checker reports
successful execution. There is no deliberately wrong solver revision and no
fabricated failed attempt. Masked-query correctness remains unknown.
