# cf4fdf474ad5

Constructive version `3.0.0` generates three or four separated, completely filled rectangular patches on a `22..28 × 22..28` zero background. Patches use cyan `8` with green `3` overlays. The pinned rule ignores patches whose bounding-box height exceeds eight, then selects the valid patch with the greatest **absolute** green count; ties use smaller bounding-box area and then top-left position. The output is the exact crop of that patch.

Every default four-patch scene contains a valid large-area decoy, a taller invalid decoy with more green, the intended winner, and a smaller high-density valid decoy. The schedule alternates unique-count scenes with equal-green area-tie scenes, so three-demonstration lessons refute height-blind, density, largest-area, first-patch, identity, and canonical-fitting top-left-on-tie shortcuts. Exact controls are limited to `grid_h`, `grid_w`, and `n_patches`; all are pixel-observable and strictly validated.

Authority pin: `RULE_HASH = 9316ff1c04fa`. Final generator SHA-256: `f577c3f69219ac465b9cb03c36352de625653e76d71f3ebff9df78d87093c286`.
