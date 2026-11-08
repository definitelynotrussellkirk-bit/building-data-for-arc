# Solve work log

## Exposure statement

I had already inspected this task's generator and canonical rule while repairing
it, so this is **not a blind solve**. After `solve_episode.py prepare`, I kept
the generator, Racket source, reference solutions, private labels, and prior
solution explanations closed. The implementation below was checked against only
the visible train examples.

## Revision 1

Hypothesis: count each nonzero color over the entire input. Preserve every cell
of a color iff that color occurs exactly twice; replace all other nonzero cells
with zero. The output keeps the input dimensions and positions.

Visible evidence:

- Train 0 keeps colors 4, 7, and 8 (each count 2) and removes colors 1 and 2
  (each count 1). This rejects “keep all nonzero” and “keep at most two.”
- Train 1 keeps 7 and 8 (count 2) while removing counts 1, 3, 4, and 5. This
  rejects “keep repeated colors” and any threshold such as count >= 2.
- Train 2 keeps only color 4 (count 2) while removing three colors of count 4,
  a singleton, and a color of count 5. In particular, removing count 4 rejects
  “keep even-frequency colors.”

Predicted queries from the same rule:

- Query 0 keeps colors 4 and 7; it erases color 8 (count 1), color 1 (count 4),
  and color 5 (count 5).
- Query 1 keeps colors 3, 4, and 6; it erases color 8 (count 3).

Implementation uses `collections.Counter` and preserves exact cell positions.
No additional geometric assumption is needed. Remaining uncertainty is limited
to masked query scoring; the visible examples determine the frequency rule
cleanly.
