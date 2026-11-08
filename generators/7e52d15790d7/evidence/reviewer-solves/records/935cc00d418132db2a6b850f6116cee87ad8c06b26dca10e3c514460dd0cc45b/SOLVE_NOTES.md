# Blind solve notes — 7e52d15790d7

Earlier exposure: none known. I used only `solve-blind/challenge.json` and local
Python reasoning; I did not inspect a generator, rule, private label, prior
solution, or audit record.

## Observations

Each input contains three separated, monochrome nonzero objects. The output is a
compact horizontal strip of the objects' tight bounding boxes, preserving their
pixels, with one all-zero separator column. Every crop is top-aligned in a canvas
whose height is the maximum crop height.

The output order agrees in all three visible lessons with decreasing bounding-box
area:

- lesson 1: areas 6, 6, 4 -> colors 1, 7, 9;
- lesson 2: areas 9, 6, 4 -> colors 5, 3, 6;
- lesson 3: areas 9, 6, 3 -> colors 7, 1, 3.

Lesson 1 leaves one unresolved tie. Its two area-6 objects have identical 3x2
box dimensions and equal foreground counts; the visible output puts color 1
before color 7. I therefore use ascending color as a deterministic final tie
break after area. This does not prove the hidden tie policy. Test 1 contains two
area-6 objects with different orientations (2x3 color 1 and 3x2 color 8), so a
possible intended secondary key could instead be width or another geometric
feature. My chosen prediction orders color 1 before color 8.

## Revision 1

Implement 4-connected monochrome component extraction, tight crop, sort by
`(-bounding_box_area, color, top, left)`, and top-aligned horizontal packing with
a one-column zero separator. This exactly reconstructs all visible outputs.
