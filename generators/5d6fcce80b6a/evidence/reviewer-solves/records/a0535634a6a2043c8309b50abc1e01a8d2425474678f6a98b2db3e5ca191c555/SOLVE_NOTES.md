# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit evidence, or previous solve notes. I used only the visible
examples emitted by `python3 review.py blind prepare` and local Python checks.

## Hypothesis 1

The output is a canvas of shape `(2*h, 2*w)` containing two unchanged copies of
the input: one in the top-left quadrant and one in the bottom-right quadrant.
The other two quadrants are zero. Every completely-zero input row that is not
the final input row is promoted to a full-width horizontal line of color 3 in
both copies' corresponding output rows. The exclusion of the final row is
required by train example 2, whose trailing zero row remains zero, while its
interior zero row becomes color 3. Train example 3 indicates that multiple
qualifying zero rows are all marked.

Planned probes: replay all four visible training pairs exactly; add local edge
probes for a trailing zero row and for consecutive leading zero rows. The latter
is not directly distinguished by training data, so the assumption remains that
each qualifying row is treated independently.
