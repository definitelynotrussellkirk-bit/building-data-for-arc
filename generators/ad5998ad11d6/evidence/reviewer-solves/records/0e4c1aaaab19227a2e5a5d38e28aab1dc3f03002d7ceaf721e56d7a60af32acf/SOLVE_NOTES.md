# Visible-only solve notes

## Revision 1

Across all three demonstrations, every changed cell is black (`0`) and becomes
yellow (`4`); every green (`3`) cell and every unchanged black cell is preserved.
The changed black cells form regions cut off from the outer grid boundary by the
green cells when movement is restricted to up/down/left/right. Diagonal contact
does not provide an escape route. The natural global rule is therefore:

1. Flood-fill all black cells reachable from any boundary black cell by
   4-neighbor moves.
2. Preserve those exterior cells and all green cells.
3. Change every remaining black cell to `4`.

This accounts for singleton holes, irregular holes, and multiple holes without
assuming rectangular green outlines. I implemented that flood-fill directly.
