# c84e2a641055 — Drop the Whole Object to the Floor

Version: `2.0.0`

Rule hash: `b08466eb063e`

One 4-connected nonzero object is translated straight down by one shared offset
until its lowest cell reaches the last row. Shape and colors are preserved.

The repaired sampler exposes six exact observable axes (`grid_h`, `grid_w`,
`n_cells`, `n_colors`, `drop_distance`, `bottom_profile`) and uses a four-profile
teaching schedule. Every four consecutive demonstrations includes monochrome and
multicolor objects, flat and uneven lower boundaries, and objects larger than the
canonical 4/5-cell regime. Multicolor objects put both colors above the
floor-facing row while withholding one color from that row, avoiding a vertical
color-layer proxy and refuting independent per-color falling. The schedule also
refutes identity, independent-column gravity, and a 5-cell size cap.
