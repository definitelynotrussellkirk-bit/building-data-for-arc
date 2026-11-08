# Diagonal/minimum-marker corner routing

The default `diagonal` setting returns the selected canonical Racket program
byte-for-byte: clear the four inset marker cells to background and move each
marker to the diagonally opposite outside rectangle corner.

The `min_color_turn` setting first locates the numerically smallest of the four
marker colors. Its quadrant is the input-dependent intermediate: a smallest
marker on the main diagonal selects clockwise routing, while a smallest marker
on the anti-diagonal selects counterclockwise routing. The selected turn is then
applied to all four colors when painting outside corners. Two demonstrations
constructively cover both branches; every episode retains four distinct private
queries, including a substantive 30×30 case.
