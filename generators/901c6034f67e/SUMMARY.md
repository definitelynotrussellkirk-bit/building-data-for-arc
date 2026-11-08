# 901c6034f67e — contour-length rank recolouring

A zero-background grid contains exactly three monochrome, same-color
4-connected objects. Different-colored objects may touch. For each object,
count the object cells that have at least one missing orthogonal neighbor; this
is the authority's **contour-cell count**. Sort objects by that count ascending,
then by top-left row and column, and repaint them on a blank grid with colors
2, 3, and 4. Input colors do not determine output rank.

Kind: `per_puzzle`. Selected version: `3.1.1`. Canonical rule pin:
`3646fc9eedbe`.

## Sampling policy

The canonical rectangles make contour count correlate with occupied area,
bounding-box area, and bounding-box perimeter. The default three-slot sampler
therefore cycles through:

1. one source-bound canonical morphology;
2. one contour-vs-area inversion; and
3. one contour-vs-bounding-box inversion.

Every three consecutive default examples contain all three roles. Input palettes
cycle through distinct arbitrary colors, one shared color, and a derangement of
rank colors `{2,3,4}`. Shared colors exclude output color 2 in the default
transformation fingerprint; explicit rank-color examples retain input/output
palette overlap. Non-shared canonical anchors require differently colored
objects to touch, while shared-color anchors keep them separated so they remain
three objects. Exact observable controls are `scene_profile` and `palette_mode`;
all 18 legal cross-products are supported in each difficulty band.

## Executable semantic contract

Declared competitors are occupied area, bounding-box area, bounding-box
perimeter, scan order, largest contour first, color-blind nonzero connectivity,
and identity. Pixel-bound witnesses cover each rival and each profile/palette
branch. `lesson_identifiable` checks that demonstration labels match the pinned
contour rule and that no declared competitor can fit the demonstrations while
disagreeing on the query.

This is finite-rival curriculum evidence, not a proof of universal induction.
See `workspace/probe_lessons.py` for a quick cyclic-window check and the review
return's `checks/lesson-census-final-v311.json` for the source-bound
100-lessons-per-band measurement.
