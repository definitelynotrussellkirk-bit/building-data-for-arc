# Solve notes — 9a35b20efa99

## Exposure disclosure

I had already inspected the generator and canonical rule while repairing the assigned task. This is therefore an **exposed post-repair solve**, not a blind solve. During this solve episode I used only the visible examples produced by `solve_episode.py prepare`; I did not reopen the generator, Racket source, reference outputs, or private labels.

## Visible-example hypothesis

Each input has exactly one color-9 anchor and one other monochrome object. The output erases the original object, preserves the anchor, and stamps four copies around it:

1. upper-left: original crop,
2. upper-right: 90° clockwise crop,
3. lower-left: 180° crop,
4. lower-right: 90° counter-clockwise crop.

The object is cropped to its nonzero bounding box. The upper and left offsets are based on the original crop height and width, with one blank row/column between the crop frame and the anchor. The 3×2 example is the useful nonsquare probe: it distinguishes using the original crop dimensions for all four anchor-relative offsets from independently centering each rotated bounding box.

## Implementation

`solution.py` locates the single 9, crops all non-{0,9} cells, constructs the three rotations, starts with a blank same-size grid containing only the anchor, and pastes nonzero crop cells at the four inferred offsets. It validates that both an anchor and motif exist.

## Attempt 1

Intent: solve. No diagnostic or deliberately wrong attempt. Expected all three visible examples to pass; the two masked queries remain unavailable to me.
