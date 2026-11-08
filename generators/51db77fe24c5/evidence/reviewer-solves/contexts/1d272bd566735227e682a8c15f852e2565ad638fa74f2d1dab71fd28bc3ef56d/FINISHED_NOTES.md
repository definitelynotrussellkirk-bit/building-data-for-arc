# Solve work log

## Exposure declaration

I had already inspected this task's rule and generator while repairing it before this
required post-repair solve, so `earlier_rule_exposure=yes`. During this solve episode I
kept the Racket rule, generator source, prior solution, private labels, and reference
solutions closed and used only the newly prepared `challenge.json`.

## Revision 1

The three visible examples consistently recolor only blue (`1`) objects that are exactly
four cells forming a filled 2×2 square. Other blue objects stay unchanged even when they
have four cells (a T/zigzag-like control), occupy a 2×2 bounding box but have only three
cells (an L control), or contain a 2×2 subset inside a larger component.

I implemented 4-neighbor connected-component enumeration, then recolor a component iff
it has exactly four cells, exactly two occupied rows, and exactly two occupied columns.
This distinguishes the observed target from the visible size, bounding-box, and embedded-
square alternatives. Remaining uncertainty is only whether hidden examples introduce a
new color or connectivity convention not represented in the visible task; the visible
training evidence strongly supports the component rule above.
