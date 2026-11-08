# Visible-only solve notes

## Observations

- All outputs preserve the input dimensions and replace selected input cells by cyan (8), with every other cell cleared to 0.
- Each input has one connected blue (1) object. I treated this as a shape template.
- In train 0, exactly two green (3) tetrominoes are retained. Their normalized shapes are rotations of the blue tetromino; the remaining green object is not.
- Train 1 separates color role from geometry: a color-5 object has the template geometry but is omitted, while two green objects with the template geometry are retained.
- Train 2 again retains two green rotational matches and rejects the equal-size green nonmatch.

## Hypothesis

Find the unique 4-connected blue component. Among 4-connected green components, retain exactly those congruent to the blue shape under translation and quarter-turn rotation. Reflection alone is not assumed. Paint retained cells cyan and clear everything else. Matching shapes in colors other than green are distractors.

## Implementation probe

`solution.py` extracts monochrome 4-connected components, normalizes coordinates, builds the four rotations of the blue template, and paints only matching green components. The code deliberately compares full coordinate sets rather than size or bounding box.

## Exposure record

I had already inspected the assigned generator and canonical rule during the repair phase before this post-repair solve. During this solve episode I used only the visible examples printed by `solve prepare`; I did not reopen the generator, Racket rule, reference solution, or private labels.

## Revision 2 — execution repair

The first check did not reach any example comparison. `_rotate` passed a generator into `_normalize`, and `_normalize` iterated it once to find the top coordinate before trying to iterate the already exhausted generator for the left coordinate. I now materialize the coordinate iterable as a tuple at the start of `_normalize`. This is an implementation correction; the visible-example hypothesis is unchanged.
