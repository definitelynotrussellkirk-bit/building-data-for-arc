# Visible-only solve notes

This is a human work log for the final generator bytes. I had already seen the
rule while repairing the generator, so this is an exposed solve (`earlier_rule_exposure=yes`),
not an independent blind solve. During this episode I used only the displayed
examples and did not reopen the generator, Racket rule, private labels, earlier
solution files, or reference solutions.

## Hypothesis before revision 1

Every input has one full-height column of 9s. The left side is a small pattern
panel and the right side is the search board; output dimensions equal the board.
Crop the nonzero object in the left panel to its bounding box. Slide that crop
over the board without rotation. A nonzero template cell must equal the board
cell, while a zero template cell is unconstrained: train example 1 contains a
color-1 distractor inside such a zero position and still marks the match. For
each matching window, place color 8 at the window's bottom-right corner on an
otherwise zero output.

Revision 1 implements that rule directly. I will stop if it matches all three
visible examples because the examples cover three board sizes, wildcard clutter,
and multiple same-color distractor components.
