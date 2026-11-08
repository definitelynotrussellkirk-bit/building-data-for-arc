# Solve work log

I had no earlier exposure to the rule, generator, private labels, or prior solve
notes for task `28ba67946524`.  I used only the visible challenge presentation and
small scripts that measured connected components.

## Revision 1 — structural region hypothesis

The input always has one largest multicoloured connected object plus detached
monochrome clues.  Every visible output is a union of complete monochrome regions
inside that largest object.  In both one-cell-wide towers, the output is the third
colour run from the top.  In the wider object, two row bands contain side-by-side
regions; the output takes the larger colour label in each band (9 over 7, and 8
over 6).  I implemented that rule, with a horizontal-strip analogue and a
centre-region fallback for unseen geometry.

This is deliberately an honest hypothesis, not a claim that colour labels are
semantically numeric.  Alternatives considered but not adopted included matching
detached shapes into the main object, arithmetic relations among colour labels,
and selecting a centrally placed template.  Those alternatives were ambiguous on
at least one visible example.  The present rule is compact and exactly testable on
all visible examples, but the role of the detached clues remains uncertain.
