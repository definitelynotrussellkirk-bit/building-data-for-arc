# Post-repair visible-example solve

## Exposure and scope

I previously read and repaired this task generator and inspected its reference rule.
This is an exposed post-repair solve, not a blind solve. After `solve prepare`,
I consulted only the displayed challenge examples and query inputs, then wrote
this standalone solver. I did not reopen generator/rule/reference sources or
private query labels during this solving phase. Earlier knowledge can influence
this attempt and is declared explicitly.

## First hypothesis and visible evidence

The black separator lines partition four-by-four framed cells. Each two-by-two
interior has a common fill color. A rare mark copies only between same-color
marks at the same interior offset, independently along a row or column of cells.
All anchor searches use the original input.

Example 0 makes the non-cascading detail visible: the top-left interior channel
contains color 1 at cell (0,1), (2,0), and (2,2). The output fills (2,1), but
leaves cell (1,1) unchanged. A second propagation pass would incorrectly fill
that latter cell. Color 5 separately fills a vertical middle gap. Example 1
has a similar horizontal color-1 span and vertical color-8 span. Example 2
shows multiple colors/offsets and different row/column counts.

The implementation detects black separator rows/columns, obtains interior
coordinates, estimates the common interior color by its frequency, and fills
spans between at least two original anchors. Frames and separators are copied.
It does not assume any fixed special-color identity.

## Revision and stopping policy

This is the first submitted solution revision. I have not manufactured a failed
solution or an intentional negative example. The next official check tests
visible demonstrations and query execution only. If those pass, I will stop:
masked-query correctness is withheld and remains unknown pending independent
maintainer scoring.
