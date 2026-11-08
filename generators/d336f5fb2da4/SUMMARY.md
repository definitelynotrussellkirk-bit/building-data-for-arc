# d336f5fb2da4

A zero-background grid contains an arbitrary connected blue source shape, one
singleton control, and red/green singleton markers defining a nonzero vector.
Control 4 keeps the source orientation, control 6 rotates it clockwise, and
control 7 reflects it top-to-bottom. Normalize the transformed shape, stamp it
in cyan starting at the red marker, and continue along the red-to-green vector
until the next complete copy would leave the grid.

The reviewed sampler covers six asymmetric source profiles, all three controls,
horizontal, vertical, and diagonal vectors in both directions, and 8×8 through
30×30 canvases. Its three-example lessons explicitly defeat the imported
shortcut that assumed one fixed L-tromino and vector `(0,+3)`.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash:
`722859cc9e88`.

A separate task-local proposal adds `magenta_rotation = cw | ccw`. The default
`cw` program is the selected canonical Racket authority byte-for-byte; the
alternate changes only control-6 handedness. This finite family is proposed and
source-bound, not owner-qualified, accepted, or training-admitted.
