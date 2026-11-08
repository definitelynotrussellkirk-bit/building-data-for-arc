# Visible-only solve notes

This is a human work log based only on `solve/challenge.json`. I had already seen the task's rule while reviewing the generator, so this is intentionally recorded as an exposed solve; I did not reopen the generator, Racket source, reference solution, private labels, or previous solve explanations during this episode.

## Observations

- Each input contains several monochrome 4-connected components on a zero background.
- The largest components repeat one normalized shape. A single smaller component is a strict subset of that shape.
- In training example 1, two complete four-cell zigzags and one three-cell copy yield the complete zigzag.
- In training example 2, two complete six-cell T-like objects are color 5, while the incomplete copy is color 1; the output is the complete shape recolored 1. This rules out merely cropping a largest component.
- In training example 3, same-colored cells must first be split by 4-connectivity: two complete four-cell L-like components coexist with a disconnected two-cell vertical defect. The output reconstructs the full component.

## Hypothesis and implementation

Find all nonzero monochrome 4-connected components, normalize each to its tight bounding box, take the repeated maximum-size shape as the complete template, and identify the unique smaller normalized shape that is a strict subset. Render the complete template in the defective component's color.

Predicted test outputs before checking:

1. A 4×3 six-cell zigzag in color 8: rows `800`, `880`, `088`, `080`.
2. A 3×2 four-cell T/diamond-column shape in color 9: rows `09`, `99`, `09`.

The first implementation directly encodes this hypothesis. No deliberate negative or diagnostic revision was made.
