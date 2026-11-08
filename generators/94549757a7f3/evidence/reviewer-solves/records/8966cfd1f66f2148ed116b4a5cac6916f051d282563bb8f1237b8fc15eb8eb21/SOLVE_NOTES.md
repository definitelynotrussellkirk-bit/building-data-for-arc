# Solve work log

## Prior exposure

Before this solve I had not opened this task's generator, Racket rule, reference
solution, private labels, audit evidence, or prior solution explanation. I had
only read the visible examples printed by `python3 review.py blind prepare`.

## Revision 1 — baseline red check

The supplied `solution.py` was an unimplemented stub. I ran the visible checker
before changing it so the expected failure was recorded. It produced an
execution error and passed 0/5 visible examples.

## Revision 2 — horizontal green segments receive a red endpoint

Observed transformation: each maximal horizontal run of green (`3`) cells with
length at least two gains one red (`2`) cell immediately to its right, provided
that location exists and is background (`0`). Vertical green runs are unchanged;
azure (`8`) runs are unchanged. A horizontal run touching the right boundary is
also unchanged because there is no cell in which to place the marker.

Evidence across visible examples:

- Example 0 marks both length-2 horizontal green runs but not the vertical green
  run or the azure run.
- Examples 1–4 mark horizontal runs of lengths 2, 3, and 4 consistently.
- Example 1's right-edge length-2 run and example 2's run followed by azure are
  not altered, distinguishing the rule from recoloring a green endpoint.

Implementation scans each row for maximal green runs, copies the input, and
writes red only into an in-bounds background cell directly after a qualifying
run. Remaining uncertainty: unseen data could encode a more semantic notion of
"right-facing green object," but maximal horizontal runs are the simplest rule
that explains every visible positive and negative case.
