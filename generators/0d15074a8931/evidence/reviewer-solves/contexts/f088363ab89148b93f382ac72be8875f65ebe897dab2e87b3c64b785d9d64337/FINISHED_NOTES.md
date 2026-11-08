# Visible-only solve notes

Each demonstration contains solid odd-by-odd colored rectangles on a black
background. The output deletes each rectangle except for its geometric center,
which retains the rectangle's color. Repeated colors remain separate objects:
the fourth demonstration has two color-9 rectangles and keeps both centers.

The second query deliberately places two color-8 3x3 rectangles in diagonal
corner contact. They are disconnected under cardinal adjacency, so I treat
foreground objects as 4-connected same-color components rather than one object
per color or 8-connected components. For each component I take the midpoint of
its bounding row and column ranges and write that color into an otherwise-zero
grid of the original dimensions.

This is the first genuine hypothesis. During this solve phase I read only the
visible challenge and did not consult the generator, Racket rule, private query
labels, reference solutions, or previous solve explanation. Earlier rule
exposure from generator review is declared separately at finish.
