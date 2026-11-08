# Visible-only solve notes

The three demonstrations preserve the input dimensions and use one nonzero color. In each case, the output is otherwise reset to zero and contains the rectangular outline of the minimal row/column bounding box containing every nonzero input cell. This explains both two-marker diagonal cases and the three-marker case: the middle marker helps determine or lies inside the same extrema, while the output contains only the border.

Hypothesis: collect all nonzero cells, compute minimum/maximum row and column, and draw the four sides of that rectangle on a fresh same-sized zero grid using the observed color. Source markers not on the border disappear.

The two queries exercise both a four-marker input with interior/extrema information and a two-marker diagonal input, so the same construction applies without special cases.
