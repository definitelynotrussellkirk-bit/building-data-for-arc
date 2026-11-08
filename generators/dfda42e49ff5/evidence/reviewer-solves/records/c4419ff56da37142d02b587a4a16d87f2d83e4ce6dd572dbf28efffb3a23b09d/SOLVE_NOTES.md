# Solve notes

The visible examples preserve dimensions and colors. Within each same-color
four-connected object, every occupied row is filled between that row's leftmost
and rightmost object cell. Blank space between disconnected objects is preserved,
even when the objects share a color. The first example also rules out extending
a row to the component-wide right edge because its first row ends earlier than
the solid connector row.

Implementation: find same-color four-connected components, group each component's
cells by row, and fill each row's own inclusive horizontal span.
