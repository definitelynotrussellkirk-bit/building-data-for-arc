# Solve work log

## Exposure

Before this solve I had not opened this task's generator, Racket rule, reference
solution, private labels, prior solve notes, or any repair/audit target. I used
only the visible examples produced by `python3 review.py blind prepare` and the
public `challenge.json`.

## Revision 1 — enclosed-region fill

**Observation.** Every example keeps the grid shape and all existing colored
cells. The four corners act as a color key. The non-background corner color that
repeats is used to recolor the zero cells inside each closed gray (`3`) outline.
Example 3 is important because two corners are background: it still selects the
repeated nonzero color `1`, rather than taking a four-corner majority including
background.

**Implementation.** Select the most frequent corner color excluding background
`0` and outline color `3`. Flood-fill zero cells reachable from every zero-valued
boundary cell using 4-neighbor connectivity. Any remaining zero cell is enclosed,
so recolor it with the selected marker color. This handles one or many closed
outlines and does not assume rectangular dimensions.

**Alternatives considered.** Detecting rectangular bounding boxes would fit the
shown examples but would unnecessarily encode shape assumptions. Flood-filling
exterior background directly expresses the visible topological rule.

**Local probe.** A visible-example harness first failed on the untouched
`NotImplementedError`, then passed all four training examples after this
revision. Remaining uncertainty is limited to hidden cases outside the visible
contract, such as no nonzero corner markers or open outlines; the implementation
returns the input unchanged when no marker can be inferred and fills only truly
enclosed zero regions.
