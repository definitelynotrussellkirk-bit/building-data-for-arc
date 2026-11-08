# 486375757aca — Seeded Frames

A zero-background grid contains two or three complete blue(1) rectangular
frames, each with a non-{0,1} seed in its interior.  The executable rule works
on **4-connected blue objects**, not on a pre-parsed list of frames.  For each
blue object it takes the object's bounding box, selects the last colored seed
in row-major interior order, and fills the whole bounding-box interior with
that color.

Disconnected frames therefore act independently.  Frames that touch merge
into one blue object: their combined bounding box is filled from the last seed,
so earlier seeds, interior gaps, and blue border segments inside that combined
box are overwritten.  The generator alternates six observable disjoint and
touching scene profiles so every three-example lesson includes a case that
rules out the tempting “fill each frame independently” shortcut.

Kind: `per_puzzle`. Generator version: `3.0.0`. Canonical rule hash:
`32695808b436`.

Approval remains derived by the catalog from current code and retained review
evidence; changing this generator does not itself grant approval.
