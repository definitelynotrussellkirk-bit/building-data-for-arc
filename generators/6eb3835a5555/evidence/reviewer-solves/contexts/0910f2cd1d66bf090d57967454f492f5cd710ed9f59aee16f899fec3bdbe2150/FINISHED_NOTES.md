# Visible-example solve notes

This is a human work log based only on the prepared visible examples. I had earlier exposure to the task rule while repairing the generator, so this is an exposed rather than blind solve; I did not reopen the generator, Racket source, reference solutions, or private answers during this episode.

## Hypothesis

Gray 5 cells are impermeable walls. Treat every four-neighbor connected component of non-5 cells as one room. Collect the room's nonzero, non-5 colors:

- exactly one distinct color: replace every zero in that room with the color;
- zero or multiple distinct colors: leave the room unchanged;
- preserve all gray walls and existing colored cells.

Evidence from the visible demonstrations:

- Example 0 leaves the upper-left room unchanged because it contains 1, 2, and 9, while both lower rooms fill with 6 despite one room containing three 6 cells.
- Example 1 fills the upper-right room from its single 9 and the merged lower room from repeated 7s, but leaves the upper-left 4/9/3 conflict unchanged.
- Example 2 fills the repeated-3 room and single-9 room; the merged 6/9/2 room stays unchanged.

The implementation uses a four-neighbor flood fill, so it also handles partial interior walls and merged rooms rather than assuming a rectangular chamber grid.
