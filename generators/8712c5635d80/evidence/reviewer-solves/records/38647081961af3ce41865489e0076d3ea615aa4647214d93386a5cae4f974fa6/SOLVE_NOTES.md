# Solve work log

## Exposure disclosure

I had already inspected and repaired this task's generator before this required post-repair solve, so `earlier-exposure=yes`. During this solve I did not reopen the generator, Racket rule, reference solution, private labels, or prior solve explanation; I used only `challenge.json`, the rendered visible examples, and execution/check feedback.

## Hypothesis

Every input has two equal-width panels separated by a full-height color-9 column. The left panel contains a nonzero shape on a zero background. The right panel contains a rectangular border in one color. Across all three visible training pairs, the output leaves the input unchanged except that the left shape's occupied coordinates are copied to the corresponding coordinates of the right panel and recolored with the border color.

This explains every changed cell and predicts no deletion, movement, rotation, reflection, or bounding-box normalization. In particular, the placement uses absolute panel-relative coordinates: right-column = separator + 1 + left-column.

## Implementation and probe

`solution.py` locates the unique full-height 9 separator, verifies equal-width panels, extracts the unique nonzero right-panel color, copies the grid, and paints that color at each right-panel coordinate corresponding to a nonzero left-panel cell. It includes structural validation so malformed inputs fail explicitly rather than silently producing an unrelated grid.

Alternatives considered from the examples were copying only a bounding-box-normalized mask or aligning the shape to a corner of the frame. Both are contradicted by the visible examples: the copied cells retain their exact row and left-panel column offsets, including leading empty columns and rows.

Remaining uncertainty is limited to unseen malformed layouts; all visible examples share the same separator/panel/frame grammar.
