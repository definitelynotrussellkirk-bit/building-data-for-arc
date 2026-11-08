# 6c8eefa043e1 — independently seeded connected regions

Version **3.0.0**. Gray (5) walls divide a black (0) grid into actual orthogonally
connected non-wall regions. Place 2–5 distinct single-cell colored seeds in
separate regions, each with background to fill, and leave at least one region
unseeded. Flood-fill the seeded regions; preserve walls and unseeded background.
The unchanged canonical Racket rule supplies exported outputs.

Exact controls are `grid_h=7..20`, `grid_w=7..20`, and `palette_size=2..5` (number
of seed colors, excluding background and walls), independently supported in
every band. Default sampling favors canonical 7×7/9×9 profiles while retaining
larger rectangles. Each sampled board distinguishes five declared alternatives;
this is a finite teaching contract, not a claim of universal identifiability.

Version 2's geometric room lists could place competing seeds into one true
component. Version 3 measures connectivity before placement and rejects invalid
or unknown overrides rather than ignoring/clipping them. See `notes.md` for the
intentional interface migration and restrictions. Catalog approval is unchanged.
