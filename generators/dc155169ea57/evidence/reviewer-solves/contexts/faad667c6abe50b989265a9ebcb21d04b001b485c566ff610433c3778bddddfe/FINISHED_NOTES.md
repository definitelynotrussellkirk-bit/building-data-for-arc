# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — gravity through a one-cell sieve

Visible examples contain background 8, one horizontal row of 2s, and 4-connected
objects of color 1 above it.  Comparing wide and narrow components suggests that
objects fall straight down.  The 2-row acts like a sieve: a candidate position is
allowed when at most one cell of that object lies on the sieve row, but motion
stops before a position that would put two or more object cells on the row.
Components never blocked by the sieve settle at the bottom; every sieve cell they
traversed becomes background, and an object cell coincident with the sieve in its
final bottom-aligned position is omitted.  A blocked component can remain lodged
with one cell occupying the sieve.

I checked this hypothesis manually against all three visible pairs: vertical bars
and the singleton reach the bottom and punch one hole; the two-row-wide bottoms
stop above the line; the T-like/narrow-tail objects stop with their one-cell tail
on the line.  Remaining uncertainty: examples do not show interacting components
or a one-cell-per-row snake that changes columns while traversing the sieve.
