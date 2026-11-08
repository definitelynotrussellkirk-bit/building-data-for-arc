# Blind solve notes — f99263121e8a

## Visible evidence and hypotheses

1. The output preserves small nonzero shapes but removes their absolute canvas
   positions.  It stacks them vertically, placing one zero row between pieces.
2. The stack order is increasing leftmost input column, with topmost row breaking
   ties.  This explains every demonstration, including the two color-3 singleton
   pieces in example 4.
3. Pieces are monochromatic **4-connected** components.  Different colors that
   touch orthogonally remain separate (example 1), and same-colored diagonal
   cells remain separate (example 4).
4. A piece contributes the rectangular crop of the original input over its
   component bounding box, rather than a mask containing only that component.
   In example 1, the touching 9 and 2 components therefore duplicate one another's
   pixels inside their overlapping bounding boxes; this exactly explains the
   output's increased counts for both colors.
5. Every crop is left-aligned and right-padded with zeros to the maximum component
   bounding-box width in that instance.

## Revision 1

Implemented the five-part rule directly: discover per-color 4-connected
components, compute boxes, sort left-to-right/top-to-bottom, crop original input,
pad, and insert blank separators.  No generator, canonical rule, private label,
or prior solution was consulted.
