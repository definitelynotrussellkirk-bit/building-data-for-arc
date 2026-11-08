# Solve work log

## Exposure declaration before solving

I had not opened task `b98cdd1751a7`'s generator, canonical rule, notes, solutions,
audit records, or private labels. Before the assignment was drawn I had read only
packet-level documentation and a broad archive filename listing. No rule-specific
material for this blind task was consulted.

## Revision 1 hypothesis

Each input contains four separated monochrome glyphs. Every glyph occupies a
3-by-3 bounding box. The output is a 7-by-7 panel: preserve the two upper glyphs
in left-to-right order in the top slots, preserve the two lower glyphs in
left-to-right order in the bottom slots, and separate slots by one zero row and
one zero column. I will extract 8-connected nonzero components, normalize each by
its bounding box, split the four components into the two with smallest vertical
centres and the two with largest vertical centres, then place each pair by
horizontal centre.

Visible-example checks made manually:
- Training 1's upper-right glyph normalizes to `[[2,0,0],[2,0,0],[0,2,2]]`,
  exactly the output's upper-right slot.
- Training 2's four normalized glyphs match the four output slots without
  rotation or recoloring.
- Training 3 confirms the same packing with color 4 and different glyph shapes.

Alternative rejected: simply sort all components by top row and then column.
That can misorder a lower-left glyph above an upper-right glyph when the two rows
of objects are vertically staggered. Grouping by the two smallest/largest
vertical centres encodes the visible two-row layout directly.

## Revision 1 result

The implementation reproduced all 3 visible training outputs exactly. The solve
checker reported `visible_passed: 3`, `visible_total: 3`, and successful execution.
No reference material or hidden labels were consulted.

Remaining uncertainty: the visible tasks all give each glyph a 3-by-3 bounding
box and keep the four glyph regions well separated. The implementation includes
a radius-two fallback for a disconnected glyph inside a 3-by-3 tile, but would
reject a hidden instance whose intended glyph exceeds 3-by-3 or whose distinct
tiles lie close enough to merge under that fallback. Those possibilities are not
supported by the visible examples, so I stopped after the first successful rule.
