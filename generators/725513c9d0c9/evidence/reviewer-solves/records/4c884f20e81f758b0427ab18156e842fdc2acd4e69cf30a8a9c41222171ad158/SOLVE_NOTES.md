# Solve notes

The visible examples consistently use the color-8 cell as a key. Treating all
other nonzero colors as foreground, form 4-connected components. Exactly one
component has a cell cardinally adjacent to the key; diagonal contact does not
qualify. The output is that component alone, cropped to its tight bounding box,
with any non-component cells inside the box cleared to 0, then enlarged by a
factor of two in both dimensions while preserving every component color.

Implementation plan: find the key, enumerate nonzero/non-8 four-connected
components, select the unique Manhattan-distance-1 component, isolate its crop,
and duplicate each crop cell into a 2x2 block. This also explains the holes and
the multicolor targets in the visible examples.
