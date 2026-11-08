# Solve work log

Earlier exposure before this solve: none to this task's generator, rule, notes,
reference solution, or private labels. I only read the packet instructions and
the visible examples produced by `python3 review.py blind prepare`.

## Revision 1 — chamber flood fill

Hypothesis: color 5 is an unchanged wall network. Treat every maximal
4-connected component of cells whose color is not 5 as a chamber. Each visible
chamber contains exactly one nonzero/non-5 seed; replace every cell in that
chamber with the seed color.

Evidence from the examples:

- In train 0, the 3x6 upper-right chamber contains seed 6 and becomes all 6;
  the 2x6 middle-right chamber contains seed 7 and becomes all 7.
- In train 1, an irregular lower chamber remains connected through gaps around
  internal wall cells; it contains seed 7 and every reachable non-wall cell
  becomes 7. This rules out merely filling axis-aligned rectangles.
- Every 5 stays fixed, and every non-wall component has one seed in all three
  demonstrations.

Implementation: breadth-first search over non-5 cells, collect the component
and its nonzero seed set, then fill when the seed is unique. A malformed or
unsupported component with zero or multiple seeds is preserved rather than
assigned an arbitrary color.

Remaining uncertainty: the examples consistently use wall color 5 and
background 0, so the implementation intentionally binds to those visible
constants. The masked queries are not consulted.
