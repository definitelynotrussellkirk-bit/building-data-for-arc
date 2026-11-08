# Solve work log

I had not opened any generator, canonical rule, prior solution, audit evidence, or private label for this task before this solve. I used only the visible challenge prepared in `solve-blind/` and local Python inspection of those public pairs.

## Revision 1 — aligned marker segments

**Hypothesis.** Each grid is an array of identical framed tiles separated by color 0. Most tile interiors use one filler color. A few interior cells are colored markers. For every marker color at a fixed relative location inside a tile, copies that share a tile-row or tile-column are endpoints; the output fills the same relative cell in every tile between the outermost endpoints.

**Visible evidence.** In train 0, the two color-6 bottom-right markers in the first tile-column fill the missing middle tile, while the two color-8 bottom-left markers in the last tile-row fill its middle tile. Train 1 repeats the same vertical/horizontal behavior with colors 6 and 9. A direct input/output diff of train 2 showed four additions: color 5 between two horizontal endpoints, color 6 between two vertical endpoints, and color 7 filling one horizontal and one vertical gap. This ruled out copying only a single pair or only one orientation.

**Implementation.** Detect non-background row/column runs as tiles, identify the dominant interior filler, group non-filler cells by `(color, relative row, relative column)`, and fill aligned spans in tile coordinates. The transformation is applied from the original marker set rather than repeatedly taking closure.

**Remaining uncertainty.** The visible tasks all have a solid separator frame, rectangular equal-sized tiles, a single dominant interior filler, and markers restricted to tile interiors. The program intentionally follows those demonstrated constraints.
