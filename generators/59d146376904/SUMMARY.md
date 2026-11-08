# 59d146376904

Split an even-sized input grid into four equal quadrants. In each quadrant,
ignore background color 0 and select the **unique most-frequent nonzero color**.
Return those four selected colors as a 2×2 grid in spatial order: top-left,
top-right, bottom-left, bottom-right.

The selected color is a unique nonzero plurality; canonical examples do not
require it to occupy more than half of every quadrant. Ordinary generated scenes
contain a visible minority nonzero color and may contain background cells. The
four selected colors are distinct.

Kind: `per_puzzle`. Current repaired version: `4.0.0`. Canonical rule hash:
`f575832a27ff`.

The task-local parametric family adds an episode-fixed `summary_order` parameter:

- `spatial` — exact canonical behavior and exact canonical Racket source.
- `majority_count_desc` — compute each quadrant's selected color and count, rank
  quadrant indices by count descending, then emit the selected colors in that
  input-derived order.

The alternate setting preserves the quadrant-summary reasoning while adding a
real count → rank → output-order dependency.
