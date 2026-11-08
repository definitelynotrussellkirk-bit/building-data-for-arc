# Solve notes

These are a human work log based only on `solve/challenge.json` during the solve phase. I had already inspected the task's generator/rule semantics earlier in the required generator-review phase, so this is **not a blind solve**; I will declare earlier exposure as `yes`. I did not consult a reference solution, private labels, generator source, or Racket source during this phase.

## Visible-example observations

1. Each input contains one connected colored object using colors outside `{0,3,4,5,6}` and several isolated cells colored 3–6.
2. The original colored object disappears from the output. Copies of its full bounding-box pattern appear with their top-left bounding-box coordinates at the isolated marker locations.
3. From training example 1, the source bounding box is:

   ```text
   9 7 0
   0 9 0
   2 1 9
   ```

   - At marker 3, the same matrix appears: identity.
   - At marker 4, each row is reversed: left/right reflection.
   - At marker 5, row order is reversed: top/bottom reflection.
   - At marker 6, the observed matrix is `[[2,0,9],[1,9,7],[9,0,0]]`: 90° clockwise rotation.

4. Training example 2 has a 2×4 source, so it distinguishes rotation from a square-only transpose. The marker-6 copy is 4×2 and agrees with clockwise rotation.
5. Training example 2 repeats marker 4, and both locations receive copies. Therefore the rule applies to every marker occurrence, not just the first marker of a color.
6. Output starts from an empty grid; source pixels and standalone marker pixels are not retained except where a transformed copy paints them.

## Hypotheses considered

- **H1: all markers receive an unchanged copy.** Rejected by the visibly different copies at colors 4, 5, and 6.
- **H2: marker 4 rotates and marker 6 reflects.** Rejected by direct matrix comparison in examples 1 and 2.
- **H3: marker 6 is transpose or counterclockwise rotation.** Rejected by the non-square 2×4 example; dimensions and ordered colors match clockwise rotation.
- **H4: only one marker per code is active.** Rejected by the two color-4 markers in training example 2, both of which produce output copies.
- **H5: marker coordinate aligns to a nonzero corner of the object.** Rejected by treating each source as a full bounding box, including zero cells; the observed placements align marker coordinates to the transformed bounding box's top-left coordinate.

## Implementation

`solution.py` extracts the bounding box of all nonzero, non-marker colors, snapshots every marker in the original input, creates the four transformations, and stamps all nonzero transformed cells into a fresh same-size zero grid. It raises on an out-of-bounds transformed box rather than silently clipping.
