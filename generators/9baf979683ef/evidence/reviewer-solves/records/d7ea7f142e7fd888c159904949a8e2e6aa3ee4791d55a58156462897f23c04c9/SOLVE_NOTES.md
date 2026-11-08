# Solve notes

## Visible evidence

All three training inputs contain one vertical color-5 line spanning the grid. The output preserves that line and every original cell, then places a same-colored copy on the other side at equal horizontal distance. The examples vary the line position, grid width, palette, number of colors, and source arrangement, so the line itself—not the geometric center, color identity, or object connectivity—is the reflection axis.

## Hypothesis

Let `d` be the unique column filled with color 5. For each nonzero, non-5 cell `(r, c)` left of `d`, write the same color at `(r, 2*d-c)` and leave the rest unchanged.

## Visible checks

- Training 1: divider 5 maps columns 0, 2, 3, and 4 to 10, 8, 7, and 6.
- Training 2: divider 4 maps the extended colors 1, 7, and 9 without treating any palette specially.
- Training 3: off-center divider 7 in a width-16 grid maps columns 2, 3, 4, and 5 to 12, 11, 10, and 9.

## Revision record

One implementation revision encoded the direct reflection rule with shape and divider validation. The rule was already familiar from earlier work on this assigned generator, which is disclosed in the finish record. During this frozen solve episode I used only the visible challenge and did not consult the generator, Racket authority, private labels, or reference solution.
