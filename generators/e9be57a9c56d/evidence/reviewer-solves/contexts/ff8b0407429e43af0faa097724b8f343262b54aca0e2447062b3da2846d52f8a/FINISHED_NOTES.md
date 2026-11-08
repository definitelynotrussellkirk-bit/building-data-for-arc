# Solve work log

## Prior exposure

I had already reviewed this task's generator and canonical rule before this required
post-repair solve, so this is intentionally an **exposed** solve. During this solve I
used only the prepared visible examples and my own Python; I did not reopen the
Racket source, generator implementation, reference solutions, or private labels.

## Revision 1 — template-chain hypothesis

The visible examples contain one monochrome connected multi-cell template and a
collinear sequence of isolated colored markers. Exactly one marker has the template
color, so I treat that marker as the anchor for the template's existing bounding-box
origin. For each neighboring marker, the next copy origin advances by the template's
axis extent minus one plus the coordinate difference between the two markers. I copy
the same normalized shape in that marker's color, retain the original markers and
anchor template, and support both horizontal and vertical chains.

The spacing formula was checked directly against all three visible examples: e.g. a
3-row template and marker-row difference 2 produce a 4-row origin shift; differences
4 and 5 produce shifts 6 and 7. Remaining uncertainty before checking: whether an
unseen query could contain more than one multi-cell foreground component, but every
visible example supports the single-template grammar.
