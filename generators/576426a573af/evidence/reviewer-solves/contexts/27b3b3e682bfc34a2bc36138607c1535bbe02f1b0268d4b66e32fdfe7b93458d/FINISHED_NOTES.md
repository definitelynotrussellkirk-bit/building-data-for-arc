# Exposed visible-only solve notes

## Exposure declaration

This solve is exposed, not blind. Earlier in this session I reviewed and edited
this family's separate parametric prototype, which exposed the reflection and
overlay behavior and its default setting. That prior exposure informs my first
hypothesis and must be recorded as `earlier-exposure yes`.

During this solve phase I have read only the newly prepared public solve README
and challenge, used my own Python experiments, and received official visible-only
preparation feedback. I have not reopened a generator, Racket source, reference
solution, private label, prior solution explanation, or private review material.
No reference was consulted during this solve phase.

## Visible observations and hypothesis

All four public demonstrations preserve input dimensions. A zero at row r,
column c receives the original input color at row height-1-r, column c. An
already occupied cell keeps its own original color, including where its
reflected partner has a different nonzero color. This uses the original grid
for every lookup, keeps color values unchanged, and leaves an odd-height middle
row unchanged.

The proposed rule is therefore to overlay the original input on its up/down
reflection, with zero transparent and original nonzero cells taking precedence.

## Actual experiments and revision history

Before writing the solver I calculated this rule on the public training pairs.
It matched all four exactly, with mismatch counts 0, 0, 0, 0. Their dimensions
were 10x4, 10x4, 12x9, and 7x10.

In the same exploratory calculation I checked two alternatives against the
public labels. Giving the reflected nonzero cell priority produced mismatch
counts 0, 4, 0, 8, so examples 1 and 3 establish original-cell precedence.
Reflecting left/right while preserving original nonzero cells produced mismatch
counts 16, 12, 16, 16, distinguishing the reflection direction. These were
Python hypothesis diagnostics, not submitted solver revisions or failed official
checks.

I confirmed that the two public query entries contain input grids only. Their
expected outputs are unavailable and their correctness remains unknown.

I then wrote the first and only solver revision. There have been no failed
submitted revisions or official checks at this point. The next action is the
official visible-only check, which freezes this source and contemporaneous log.
If it confirms all four demonstrations, I intend to stop because the available
labels support the same rule across dimensions and occupied conflicts. This
will remain an exposed solve with no claim about private query correctness.
