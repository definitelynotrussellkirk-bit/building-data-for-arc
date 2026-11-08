# Solve work log

I had no earlier exposure to this task's generator, Racket rule, private labels,
reference solution, or prior solve explanation. I used only the visible examples
created by `blind prepare`.

## Revision 1 — red test of the provided stub

The initial `solution.py` raised `NotImplementedError`. I ran the visible checker
once before implementation so the missing behavior was recorded honestly. It
reported an execution error and 0/3 visible examples passed.

## Hypothesis from the visible examples

Each input has height `N` and width `3N + 2`. Two full color-9 columns divide it
into three `N x N` panels. The first panel is a pattern, the second is a symmetry
transform of that pattern, and the output applies the same transform to the third
panel.

Evidence:

- In training examples 0 and 1, panel 2 is panel 1 reflected top-to-bottom; the
  given output is panel 3 reflected top-to-bottom.
- In training example 2, panel 2 is panel 1 reflected across the anti-diagonal.
  The colored 7, 4, and 3 objects all land exactly at their shown positions under
  the same coordinate map `(r, c) -> (N-1-c, N-1-r)`. Applying it to panel 3
  reproduces the output's 8, 5, and 1 objects.

This rules out a color-specific object motion: the full spatial mapping, including
object orientation and position, is shared across all colors.

## Revision 2 — general symmetry inference

I implemented all eight dihedral symmetries of a square. The solver splits the
three panels, finds every transform that maps panel 1 exactly to panel 2, and
applies the matching transform to panel 3. It rejects malformed framing, no-match
cases, and genuinely ambiguous demonstrations where matching transforms disagree
on panel 3.

Predictions before checking:

- Query 0 demonstrates anti-diagonal reflection. The two 4 cells should become a
  horizontal pair at row 1, columns 3–4; the three 5 cells should become a pair at
  row 3, columns 3–4 plus one cell at row 4, column 3.
- Query 1 demonstrates top-to-bottom reflection. Its bottom vertical 2 becomes a
  top vertical 2, and its upper 1 object moves to the corresponding lower rows.

Remaining uncertainty: a deliberately symmetric first panel could make the
transformation underdetermined. The implementation allows such a case only when
all matching transforms produce the same third-panel output.
