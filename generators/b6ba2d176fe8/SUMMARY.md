# b6ba2d176fe8

Find every nonzero monochrome 4-connected object, sort the objects by their left bbox column, and paint each solid bbox rectangle on a fresh same-size zero grid. The first rectangle starts at (0,0). After painting a rectangle of height h and width w, advance the next top-left by (h-1,w-1), so consecutive rectangles share exactly one corner and the later color overwrites that shared cell.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
