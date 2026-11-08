# Solve work log

## Prior exposure declaration

I had already inspected and repaired this task's generator and knew the intended family before this solve episode, so this is not blind. During the episode itself I used only the visible examples and did not reopen the generator, Racket source, reference solutions, or private query labels.

## Visible-example hypothesis

Each input contains three meaningful objects:

1. a small color-4 shape that acts as a reusable template,
2. a single color-7 marker next to one endpoint of a color-1 path, and
3. a nonbranching orthogonal color-1 wire.

The outputs erase the input and place copies of the normalized color-4 shape at direction changes of the wire. The wire must be traversed from the cell adjacent to color 7 so the first and last color-1 cells are endpoints rather than turns. Each copy is top-left aligned: the turn cell is the top-left origin of the normalized template.

Evidence from the visible examples:

- Example 0 has a three-cell horizontal template and two wire turns; its output is two adjacent three-cell horizontal copies at those turn anchors.
- Example 1 has an L template and three direction changes; its output contains three copies of that L.
- Example 2 has a three-cell horizontal template and three direction changes; the output has three corresponding copies.

## Implementation

The program extracts and top-left normalizes all color-4 cells, traces the unique color-1 path beginning at the sole wire neighbor of color 7, compares incoming and outgoing unit directions at internal path cells, and stamps the template at every changed direction on a fresh zero grid.

No alternative rule was needed after comparing all three demonstrations. Remaining uncertainty is limited to malformed inputs outside the visible grammar; the generated lesson presents one template, one marker, and one simple wire.
