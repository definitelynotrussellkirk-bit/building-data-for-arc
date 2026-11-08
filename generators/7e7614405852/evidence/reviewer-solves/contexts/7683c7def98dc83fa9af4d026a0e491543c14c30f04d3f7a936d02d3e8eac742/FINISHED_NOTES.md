# Solve work log

## Prior exposure

I had already repaired this task's generator and therefore had earlier exposure
to the task semantics before this solve. I did not consult the generator, Racket
rule, reference solution, private labels, or earlier explanation after preparing
this visible-only episode.

## Revision 1

**Visible evidence.** In all three demonstrations, a maximal horizontal run of
exactly three equal nonzero cells has its middle cell changed to color 8. Runs of
length 2, 4, and 5 remain unchanged. The vertical length-3 objects in each lesson
also remain unchanged, so orientation matters.

**Hypothesis.** Scan each row left to right. For each maximal nonzero
monochromatic horizontal run, replace only its middle cell when its length is
exactly 3. Preserve every other cell.

**Predicted queries.** Query 0 changes the centers of the horizontal color-3 and
color-1 triples; it preserves the vertical color-4 triple and horizontal
color-2 length-5 run. Query 1 changes the centers of the horizontal color-1 and
color-5 triples; it preserves the color-3 length-2 run, color-4 length-5 run,
and vertical color-2 triple.

**Alternatives rejected from visible examples.** “Mark all odd runs” is refuted
by the length-5 runs. “Mark triples in either orientation” is refuted by the
vertical triples. “Mark every run of length at least 3” is refuted by both
length-4 and length-5 runs.
