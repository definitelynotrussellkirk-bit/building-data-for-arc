# Solve notes

## Prior exposure

I had already repaired this task's generator before this required post-repair solve, so this is **not blind**. I did not open the generator, Racket source, canonical labels, private query labels, or earlier solution files after `solve prepare`.

## Visible-example hypothesis

- Color 1 is an impassable wall; color 0 is traversable background.
- Color 2 is the start and color 3 is the final endpoint.
- Any present colors 4 through 7 are waypoints visited in ascending numeric order.
- For each consecutive pair, use a four-neighbor shortest path and recolor only traversed 0 cells to 8, preserving walls and markers.
- The visible outputs are consistent with deterministic BFS neighbor order up, down, left, right when shortest paths tie.

## Implementation

The solver collects the markers, forms `2 -> sorted(4..7 present) -> 3`, runs BFS for each leg on the original input while blocking color 1, reconstructs the path, and overlays color 8 on zero-valued interior path cells. It raises on a disconnected leg rather than inventing a route.
