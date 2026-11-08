# Solve notes

Each input has three panels separated by two full-height columns of color 5. The
first two panels show the same object before and after color-8 markers are added.
The third panel is a differently colored/shaped query object.

Hypothesis: take each newly added 8 in the second panel as an offset from the
first object's nonzero bounding-box top-left. Apply those offsets from the query
object's bounding-box top-left and otherwise preserve the query panel. The fourth
visible example is decisive: an added offset lands on an occupied query cell and
the output replaces that cell with 8, so "paint only empty cells" is not the rule.

The implementation finds the two all-5 separator columns, compares panels A and
B to locate new 8s, translates their offsets to panel C, and paints them
unconditionally. It preserves the panel size and every unaffected query cell.
