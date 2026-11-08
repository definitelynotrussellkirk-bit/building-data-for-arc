# Solve notes

## Revision 1 — decode each 3×3 glyph as a compass address

The examples contain nine solid 3×3 tiles on a zero background.  Eight tiles
have gray 5 plus one colored glyph; one is entirely gray.  The output is a 9×9
gray canvas partitioned into nine 3×3 slots.  Each colored tile is copied
unchanged into the slot indicated by the local extent of its non-gray cells:
colored rows confined to 0..1 mean top, confined to 1..2 mean bottom, otherwise
middle; the same rule on columns gives left/right/middle.  The all-gray tile
leaves the center unchanged.  Input position and signal color are irrelevant.

Implementation scans for solid nonzero 3×3 windows, checks that there are nine,
decodes the colored-cell row and column extents, and stamps the original tile.
This is a human work log based only on the prepared visible examples.  I had
seen the family earlier while reviewing the generator, but did not consult the
generator, Racket rule, reference answers, or private query labels during this
solve phase.
