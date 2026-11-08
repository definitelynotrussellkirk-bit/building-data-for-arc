# Visible-only solve notes — d59da25908ca

This is a human work log for the post-repair exposed solve. I had earlier rule
exposure from reviewing the generator, but during this solve I read only
`solve/challenge.json` and did not consult the generator, Racket source,
reference solutions, or private labels.

## Visible evidence

Across the three demonstrations, maximal vertical green runs of exact length 2
become orange. Runs of lengths 1, 3, 4, and 5 remain green. One demonstration
has no length-4 run yet still transforms a length-2 run, refuting any requirement
that length 4 be present.

## Hypothesis and implementation

Scan each column, measure each maximal contiguous run of green (`3`), and recolor
the whole run orange (`7`) iff its length is exactly two. Preserve all other
cells. The implementation applies this independently to every column.
