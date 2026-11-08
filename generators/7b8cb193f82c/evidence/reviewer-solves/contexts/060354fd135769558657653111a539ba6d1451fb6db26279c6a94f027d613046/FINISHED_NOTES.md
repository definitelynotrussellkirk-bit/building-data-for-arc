# Visible-only solve notes

The visible examples keep the grid shape and every color-8 cell fixed. Only zero
cells fully enclosed by a rectangular 8-frame change. The outermost enclosed
layer becomes 2, the next inward layer becomes 3, and the colors continue
alternating with inward distance. Multiple frames are handled independently;
background zero regions touching the canvas edge remain zero.

Implementation: find 4-connected zero components. Ignore components touching a
canvas border. For each enclosed component, run a multi-source BFS from its
boundary cells to assign inward depth, then map odd depth to 2 and even depth to
3. This also covers thickness-2 frames because thickness affects enclosure but
not the layer depth inside the zero hole.
