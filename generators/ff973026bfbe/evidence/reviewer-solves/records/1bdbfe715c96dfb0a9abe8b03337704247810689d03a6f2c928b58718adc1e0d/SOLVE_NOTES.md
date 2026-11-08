# Solve work log

This is a human work log. I had earlier rule exposure while repairing this task's
generator, so this episode is not blind. During this solve I kept the generator,
Racket source, reference solutions, private labels, and earlier solution notes
closed and used only the newly prepared visible examples.

## Revision 1 — row markers × top-row column markers

Hypothesis: every row containing a colour-1 cell is active, wherever that blue
cell lies. Every column containing colour 2 specifically in row 0 is active.
Copy the input and paint the Cartesian product of those rows and columns with
colour 3, overwriting an existing cell when an intersection lands on it. All
other cells and distractor colours remain unchanged.

Visible evidence:

- Train 0 activates rows 1, 2, and 6 and top-row columns 5 and 8, producing the
  six green cells. The red cell at (2, 1) is below row 0 and does not activate
  column 1.
- Train 1 puts blue markers away from column 0, so a left-border-only rule is
  impossible. Rows 3, 6, and 9 cross top-row columns 2 and 10. The blue marker
  at (6, 10) is overwritten by green, explaining why the output has one fewer
  blue cell.
- Train 2 again ignores an off-top red cell at (1, 8), while rows 1, 3, and 8
  cross top-row columns 0, 3, and 9. The blue marker at (8, 3) is overwritten.
- Colours 4, 6, and 7 behave as inert distractors on inactive rows.

The two queries contain the same marker relationships, including an off-top red
in query 0 and off-border blue markers in query 1. I implemented this rule
without adding a speculative special case. Remaining uncertainty is only the
withheld query scoring; all three visible demonstrations should match exactly.
