# Solve work log

No task-specific generator, rule, notes, private labels, reference solution, or audit material was inspected before this solve. I used only the visible examples printed by `solve_episode.py blind prepare` and the files in `solve-blind/`.

## Revision 1

Each input contains four separated monochrome objects. The output preserves each object's cropped pixels, top-aligns the objects, inserts one zero column between adjacent objects, and discards the surrounding input canvas.

The three completely filled rectangular objects (including one-cell and one-column rectangles) are ordered by increasing bounding-box height. The remaining non-rectangular object is placed last, even when its height is less than the tallest rectangle. This explains all three demonstrations:

- example 0: 2-high block, 3-high line, 4-high line, then the irregular 3-high object;
- example 1: point, 3-high block, 4-high line, then the irregular 3-high object;
- example 2: 2-high line, 4-high block, 5-high line, then the irregular 4-high object.

The two queries closely repeat examples 0 and 1 with different colors and minor reflection of the irregular object, so the program groups nonzero cells by color, crops each bounding box, classifies a crop as solid exactly when every bounding-box cell is occupied, sorts solid crops by height, appends non-solid crops, and assembles them top-aligned.

Remaining uncertainty: the visible data contains exactly one object of each color and exactly one irregular object. The tie-break among multiple solid objects of equal height is not identified by the examples, nor is behavior with multiple irregular objects. The implementation uses deterministic width/color tie-breaks only as a fallback.
