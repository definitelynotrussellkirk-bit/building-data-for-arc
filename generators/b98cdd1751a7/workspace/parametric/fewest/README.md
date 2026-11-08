# Row-group ordering parameterization

This family preserves the canonical first/last-top-row midpoint partition and
changes only how each resulting two-object group is consumed:

- `left_to_right` is the exact canonical Racket program.
- `fewest_cells_first` sorts each upper/lower group by object cell count, with
  left column as the deterministic tie-break, before copying the crops.

The input stream is matched across settings. The first two demonstrations are
constructive teaching cases: one places all four objects below the literal
canvas midpoint and one places all four above it. Their area, row, column and
color orders are deliberately crossed so the declared finite rivals do not fit
both demonstrations. Four queries are always retained, ending with a substantive
30×30 all-below-midline case.

Sequential dependency: step A finds the objects and derives the canonical
midpoint plus upper/lower membership. Step B receives those input-dependent
lists and orders the members according to the episode setting. Replacing step
A with a literal canvas midpoint changes the final output on the retained causal
case.
