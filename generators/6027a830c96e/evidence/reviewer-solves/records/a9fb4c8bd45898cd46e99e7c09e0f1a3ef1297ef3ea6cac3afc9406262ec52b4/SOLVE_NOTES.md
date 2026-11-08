# Solve work log

## Prior exposure

I had already inspected the task's generator and reference behavior before this
post-repair solve. I therefore record `earlier-exposure=yes`. During this solve I
kept the generator, Racket rule, prior solution, and private labels closed and
used only the visible challenge examples.

## Revision 1

**Visible pattern.** Each input contains two or three large panels outlined by a
single color, plus one isolated colored cell above the panels. In every training
example, the isolated cell's color identifies exactly one panel border:
color 2 in examples 0 and 1, color 3 in example 2, and color 1 in example 3.
The output is that panel's border-free interior, preserving its dimensions and
all interior colors/zeros.

**Implementation.** I enumerate rectangular borders at least 4x4, regardless
of their interior contents. I then scan row-major for the first nonzero cell
outside all panel boxes, use its color as the selector, and crop the strict
interior of the uniquely matching frame. The panel detector deliberately does
not require a blank or monochrome interior.

**Alternatives considered.** Selecting the leftmost, rightmost, or largest
panel fails across the four visible examples. Tight-cropping nonzero interior
content also fails because the outputs preserve zero margins and panel interior
shape.

**Remaining uncertainty.** The visible examples imply one external selector
and one matching frame. The solver raises a clear error rather than guessing if
either uniqueness condition is violated.
