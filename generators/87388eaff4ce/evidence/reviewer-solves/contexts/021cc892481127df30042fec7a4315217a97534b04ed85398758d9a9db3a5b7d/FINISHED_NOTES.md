# Post-repair visible solve notes

## Revision 1

From the three visible demonstrations:

1. Each monochrome 4-connected object is preserved, including holes, but cropped
   to its own bounding box.
2. The crops are stacked vertically, left-aligned, with one all-zero row between
   adjacent crops; output width is the widest crop.
3. Primary order is descending bounding-box height. In examples 0 and 2, the
   height-4 line precedes the two height-3 shapes; in example 1 the height-4 line
   precedes both height-2 shapes.
4. Equal-height objects are ordered by ascending color. Example 0 puts color 2
   before 7, example 1 puts 4 before 9, and example 2 puts 3 before 7.

I implemented connected-component extraction, bbox crops, the key
`(-height, color)`, and vertical packing. This is an exposed post-repair solve:
I had earlier rule/generator exposure during review, but I did not consult any
reference implementation while writing or checking this solve.
