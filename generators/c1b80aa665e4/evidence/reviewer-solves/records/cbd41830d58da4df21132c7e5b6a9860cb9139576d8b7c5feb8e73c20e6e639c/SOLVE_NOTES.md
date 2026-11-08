# Solve work log

I had not opened task `c1b80aa665e4`'s generator, rule, notes, prior solves,
or private labels before this episode. I used only `challenge.json` and the
visible checker.

## Revision 1 — isolated-object recoloring

**Hypothesis.** The output preserves every orthogonally connected nonzero object
with at least two cells and recolors each one-cell nonzero object to 9. Object
color does not matter. Evidence across the demonstrations:

- In training pair 1, the adjacent two-cell 7 object remains 7, while the three
  isolated 7 cells become 9.
- In pair 2, the vertical two-cell 7 object remains, while isolated 3 and 2 cells
  become 9.
- In pair 3, the four-cell 8 object and three-cell 3 object remain, while one-cell
  objects of colors 8, 2, 3, and 6 become 9.

I implemented 4-neighbor, same-color connected components and recolor only
components of size one. A simpler local-neighbor test would produce the same
answers, but explicit components make the object interpretation unambiguous.
The examples do not determine whether diagonal touching counts as connected;
ARC object conventions and the demonstrated horizontal/vertical objects support
4-connectivity, which is the assumption used here.
