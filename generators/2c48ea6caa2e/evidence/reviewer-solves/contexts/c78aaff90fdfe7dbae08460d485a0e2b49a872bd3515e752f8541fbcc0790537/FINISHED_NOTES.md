# Solve notes

## Revision 1

I inspected only the visible examples in `README.md` during this solve. The blue
cells define a bounding rectangle. Blue cells are preserved. Empty cells inside
that rectangle become red when either their complete row or complete column has
at least four blue cells; all other cells remain/become background zero.

Checks against the visible examples:

- Rows with four or more blue cells have every interior gap filled red.
- Columns with four or more blue cells likewise fill their interior gaps.
- A cell is red when either condition holds, so qualifying rows and columns form
  a union rather than an intersection.
- Padding outside the blue bounding box remains zero.
- The numeric threshold appears fixed at four rather than proportional to the
  rectangle dimensions: the examples include different bounding-box shapes but
  retain the same qualifying count.

Earlier rule exposure exists because I repaired this generator before this
required solve. I did not reopen or consult the generator, Racket program,
reference solutions, private query labels, or earlier solution explanations
while preparing this revision.
