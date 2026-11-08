# Solve work log

Earlier exposure before this step: none known for task `be7f70e60fb7`; I did not inspect its generator, rule, notes, solutions, audit records, or private labels.

## Revision 1 — exact-two aligned endpoints

Visible examples suggest treating each nonzero color independently. When a color occurs exactly twice and the two cells share a row or column, fill the inclusive straight segment between them with that color. Colors with one point, more than two points, or two diagonally separated points remain unchanged. This explains the unchanged three green points in training example 4 and the unchanged diagonal red pair in training example 3.

Implementation copies the grid, indexes coordinates by color, and fills only background or same-color cells so unrelated markers are preserved if a path happens to cross one. Remaining uncertainty: examples do not establish whether a crossing should overwrite another color, but the generated instances appear to avoid that ambiguity.
