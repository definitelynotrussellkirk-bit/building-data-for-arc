# Solve notes

## Visible-example hypothesis

The input consists of separated nonzero 4-connected objects. The output preserves every object's cells but erases its original color. Objects enclosing a background region become 8; objects with no enclosed background region become 4.

The decisive contrast is not merely “bounding box incomplete.” The visible U/C-like objects have missing cells that remain connected to the object's bounding-box edge, and those become 4. Closed rings, including irregular and double-hole examples, become 8.

## Planned implementation

1. Find same-color 4-connected components.
2. For each component, inspect zero cells inside its bounding box.
3. Flood-fill each such zero region. A region that never reaches the bounding-box boundary is an enclosed hole.
4. Recolor all component cells 8 when at least one enclosed region exists, otherwise 4; preserve zero background.

## Prior exposure

I had already reviewed the generator and canonical rule before this required exposed solve, so this is not blind. During this solve I used only `solve/challenge.json` and did not consult the Racket source, generator source, reference solutions, private labels, or earlier solution notes.
