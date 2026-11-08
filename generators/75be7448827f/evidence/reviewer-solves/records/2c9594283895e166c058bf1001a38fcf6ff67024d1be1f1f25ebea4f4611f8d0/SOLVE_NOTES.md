# Solve work log

## Exposure declaration

I had already read the authoritative rule during the assigned generator repair, so this is not a blind solve and `earlier_rule_exposure` must be `yes`. During this final-source episode I used only `challenge.json`, my own Python, and visible check feedback. I did not reopen the generator, Racket source, private labels, reference solutions, or earlier solve explanations.

## Revision 1

Each input contains two or three separated hollow rectangles whose border is color 1. The output removes one border and returns that frame's interior without recoloring.

The visible examples distinguish raw foreground count from simple size or density shortcuts:

- Example 0 has interior-color counts 5, 6, and 7; the 7-cell interior is returned.
- Example 1 returns an 8-cell 3x3 interior over a larger 4x4 interior with 7 cells, so largest frame area is wrong.
- Example 2 has counts 4, 5, and 7; the 7-cell interior is returned.

Hypothesis: identify exact hollow color-1 rectangular borders, crop each interior, count its nonzero cells, and return the unique maximum-count crop unchanged. The implementation finds 4-connected border components, verifies each is the complete perimeter of its bounding rectangle, and applies the count rule. The query counts are consistent with this hypothesis as well, but their outputs remain masked by the episode protocol.
