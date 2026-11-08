# Exposed post-repair solve notes

Earlier exposure: **yes**. I reviewed this task's generator before this episode,
so this is not a blind solve. During the episode I used only `challenge.json` and
did not consult the generator, Racket source, private labels, or prior solution
files.

## Visible-example observations

- All examples are grids of framed 5x5 tiles separated by all-zero rows and
  columns.
- The frame's nonzero color identifies a group. Colors may occur in multiple
  tiles at unrelated positions.
- Comparing input/output, every same-color tile ends with the union of the local
  colored offsets seen in **all** tiles of that color.
- The first training example is especially diagnostic: color 2 has different
  partial interior marks in separate frames, and the output merges both marks
  into both frames. This rejects “copy the first nonempty source only” and
  “fill only blank targets.”
- Separator cells and tiles of other colors remain unchanged.

## Implementation plan

1. Detect maximal row and column bands between all-zero separator lines.
2. Enumerate each tile with its top-left color.
3. For each color, collect every local `(dr, dc)` whose cell already equals that
   color in any same-color tile.
4. Paint that union into every tile of the color on a deep copy.

The algorithm deliberately includes frame offsets in the union; frames are
already complete, so this is equivalent to copying only interior motifs and
avoids hard-coding a 5x5 interior convention.
