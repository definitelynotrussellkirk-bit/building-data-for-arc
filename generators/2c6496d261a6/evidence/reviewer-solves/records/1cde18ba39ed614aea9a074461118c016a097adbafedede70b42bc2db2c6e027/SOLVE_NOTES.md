# Solve work log

I had no earlier exposure to task `2c6496d261a6`, its generator, rule,
solutions, audit records, or private labels. I used only the visible grids in
`challenge.json` / `README.md`.

## Revision 1 — colors confined to one row

Hypothesis: erase every nonzero color whose cells occupy more than one row; keep
a color unchanged when all of its cells lie in a single row. A singleton is
therefore retained. The output size and all retained coordinates stay unchanged.

Evidence from the visible examples:

- Train 0 keeps color 2 (four cells, all on row 4) and singleton color 4;
  color 5 spans rows 0, 1, and 5 and is erased.
- Train 1 keeps color 2 on row 0, color 8 on row 3, and singleton color 5.
  The vertical pairs 6 and 7 are erased, which argues against a generic
  "straight line" rule and specifically favors a horizontal-row criterion.
- Train 2 keeps color 6 on row 4 and singleton color 1. Every erased color
  occupies two or more rows.

Predicted queries:

- Query 0 retains color 7 on row 0 and singleton color 5; all color-4 cells are
  erased because color 4 spans rows 2, 3, 4, and 6.
- Query 1 retains singleton color 7, color 3 on row 6, and color 6 on row 8.
  Colors 2, 4, and 9 span multiple rows and are erased.

Alternatives considered and rejected from visible evidence:

- Keep any monochrome straight line: contradicted by the erased vertical color-6
  and color-7 pairs in Train 1.
- Keep colors with a particular frequency: colors with the same count can be
  treated differently, while both singletons and several different horizontal
  run/gap patterns are retained.
- Keep connected objects: retained colors can be split into disconnected groups,
  such as color 2 in Train 0 and color 6 in Train 2.

The implementation records the set of occupied row indices for each nonzero
color and replaces colors with more than one occupied row by zero. Remaining
uncertainty: none apparent on the visible examples; private query labels remain
unseen as required.
