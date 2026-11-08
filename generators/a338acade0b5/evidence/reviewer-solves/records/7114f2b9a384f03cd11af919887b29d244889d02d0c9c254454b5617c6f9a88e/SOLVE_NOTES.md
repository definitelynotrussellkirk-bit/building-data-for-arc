# Solve work log

Earlier exposure: yes. I repaired this task's generator and therefore already
knew the intended rule family before this fresh visible-only episode. During
this solve I did not reopen the generator, Racket rule, reference solutions,
private labels, or the retained prior solve.

The three demonstrations show exactly two nonzero cells and a one-row output of
8s. Their endpoint displacements are horizontal span 5, vertical span 7, and
diagonal span 5, respectively. A single hypothesis explains all three: output
one cyan cell for every position in the inclusive straight endpoint span, whose
length is `max(abs(dr), abs(dc)) + 1`.

This also predicts query 0 as length 7 (same column, rows 0 through 6) and query
1 as length 5 (diagonal displacement 4 by 4). I implemented only that hypothesis.
The vertical demonstration rules out the plausible column-span-only shortcut.
