# Solve work log

## Exposure declaration before solving

I had already inspected this task's generator and canonical rule during the repair,
so this is an **exposed post-repair solve**, not a blind solve. During this solve I
used only the prepared visible examples and did not reopen the generator, Racket
rule, reference solutions, private labels, or earlier solution explanations.

## Revision 1 hypothesis

Row 0 behaves as a frequency legend. Ignore zeros, count each color, and choose
the unique most frequent color. In the body (rows 1 onward), decompose that color
into 4-connected components and select its largest component. Crop the component's
bounding box from the input and duplicate every row and column, producing a 2x
nearest-neighbor enlargement.

Evidence from the three visible examples:

- Example 0: color 5 occurs three times in row 0 versus two 2s and one 7. The
  larger 5-object is the five-cell shape at bottom right; its 2x crop matches the
  4x6 output.
- Example 1: color 3 occurs four times versus one each of 1, 4, and 8. The lower
  five-cell 3-object, not the earlier three-cell one, is selected and enlarged.
- Example 2: color 3 occurs three times versus two 2s and one 5. The lower
  five-cell 3-object is selected rather than the earlier three-cell one.

The queries contain the same deliberate controls: the legend winner is not the
leftmost color, there are two winner-colored body components, and the earlier one
is smaller. I therefore implemented the full count + largest-component rule rather
than a positional shortcut. For completeness I use smallest color for a frequency
tie and top-left order for an equal-size object tie, though neither ambiguity is
visible in the prepared examples.

Remaining uncertainty before checking: none material for the displayed domain;
component connectivity is inferred as orthogonal (4-connected), not diagonal.
