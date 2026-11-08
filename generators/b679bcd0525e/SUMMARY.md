# b679bcd0525e

0-bg grid (h,w ~ 9..14) holding exactly THREE things: ONE color-9 PIVOT cell at an interior position; ONE TOKEN cell of color in {1,2,3,4} (token-1 = the number of 90deg CW quarter-turns); and ONE 4-connected OBJECT (2-6 cells) in a color from {5,6,7,8} (disjoint from pivot 9 and tokens 1-4). The object sits within a radius of the pivot small enough that ALL quarter-turns about the pivot stay in bounds. Rule: erase token and object, ROTATE the object about the pivot by (token-1) quarter-turns, repaint it in its color, and restore the 9 pivot. Net: the object swings around the pivot by the token-selected angle.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
