# 2692a3e47a66

Version `3.0.1`; pinned rule hash `f5a9e05539e5`.

A 7–30 by 7–30 color-7 grid contains one solid square block at each corner. Blocks have side lengths 1–4. A foreground color may occupy one, two, three, or four disconnected corner blocks. For every color occupying at least two blocks, erase those blocks and translate each block inward by that block's own bounding-box height and width. A color occupying only one block stays fixed.

The default four-example cyclic curriculum contains:

1. four same-colored equal-size blocks;
2. one repeated color across unequal block sizes plus a singleton;
3. one repeated pair plus two singleton colors;
4. two independently repeated colors with different block sizes.

The last two semantic dimensions refute canonical-fitting shortcuts that move only one repeated color or reuse one global movement size. Public exact overrides are `grid_h`, `grid_w`, and `scene_profile`; `schedule_profile` and `observe_overrides` expose the realized curriculum.

Final generator SHA-256: `afa164c22fc4a1bf696a2c6c7dcc6531cec4d7214700305a86178dff3888cb94`. The final battery is 12/12 green, focused tests are 14/14 passed, and the selected Racket target is textually synchronized to canonical while archival `raw_code` remains preserved.
