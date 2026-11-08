# Solve work log

I had no earlier exposure to task `f7660051ec70`, its rule, generator, labels,
or prior solution notes. I used only the visible grids in `challenge.json`.

## Revision 1 — independent marked frames

**Observation.** Every non-background object is a rectangular outline in blue
(1). Some strict interiors contain red (2) markers. The output changes only
zeros inside those marked frames to green (3); red markers, blue borders, empty
frames, and the external background stay unchanged. This explains all changed
cells in all three training pairs, including frames of different sizes and one
example with two adjacent red markers.

**Implementation choice.** Find four-connected blue components, verify each
component's bounding box has complete blue top, bottom, left, and right borders,
then inspect its strict interior. If the interior contains red, replace only its
zeros with green. Component detection avoids conflating spatially separate
frames; explicit border checks avoid treating an arbitrary blue component as a
frame.

**Alternatives considered.** Filling the rectangle around each individual red
cell would be ambiguous when a frame contains multiple markers and could repeat
work. Filling every framed interior would incorrectly modify the unmarked
control frames. The marker-conditioned frame rule is the simplest rule matching
all visible examples.

**Remaining uncertainty.** The examples do not show touching frames or malformed
blue objects. The solution conservatively ignores blue components that are not
complete rectangular borders.
