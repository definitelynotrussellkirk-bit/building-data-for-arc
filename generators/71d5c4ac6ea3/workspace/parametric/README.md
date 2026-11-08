# Native parametric candidate: anchor-relative offset stamping

This source-bound candidate keeps the canonical rule as the exact default and
adds one setting, `offset_mode=rotate_cw`.  Both settings receive byte-for-byte
identical inputs.  Stage A must locate the unique color-9 anchor and extract the
color-1 cells as relative offsets.  Stage B either uses those offsets as drawn
or rotates each `(dr, dc)` to `(dc, -dr)`, then stamps the result in color 8 at
every color-2 seed on a blank canvas.

The lesson generator moves the anchor on every demonstration.  This directly
repairs the retained audit in which three demonstrations shared one anchor and
a fixed-origin shortcut fit training but failed the query.  It also varies
shape, dimensions, seed count, and placement, with a lawful 30×30 stress query.
All labels are checked against the bundled protected Racket runtime during the
authoring preflight.  This remains a proposal: `variant_approved` and
`training_admitted` are false until the owner qualification process accepts it.
