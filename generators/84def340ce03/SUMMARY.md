# 84def340ce03 — four-pixel tiles to concentric rings

Version 3.0.0. Canonical rule hash: `e27cc4c77443`.

Read nonoverlapping 2×2 input tiles in row-major order. Tile 0 becomes the central 2×2 square; subsequent tiles become successive outer rings. A tile's top-left, top-right, bottom-left and bottom-right cells independently color the corresponding ring quadrants. Zero is an ordinary color. With B = h*w/4 tiles, output side = 2B = h*w/2.

The validator accepts the complete bounded rule domain: nonempty rectangular list/tuple grids, even dimensions 2..30, h*w ≤ 60, and plain integer colors 0..9. Uniform tiles, repeated tiles and monochrome grids are lawful. The separate `strict_canonical_like` hook asks whether a draw actually teaches nesting and heterogeneous quadrant routing.

## Sampler

Three consecutive draws with the same seed and no overrides visit canonical, contrast and broad profiles, with starting phase (seed + sample_index) modulo 3.

- **Canonical:** fresh random pixels at exact shape/palette profiles (4,4,10), (4,6,8), or (6,4,9); includes zero. No canonical input is copied.
- **Contrast:** both dimensions exceed 4, with a repeated heterogeneous tile pair consecutive in row-major order and a separate uniform tile. This refutes four canonical-fit shortcuts.
- **Broad:** varied legal even shapes, palettes and tile structures. Easy/hard changes broad shape weights, while retaining the canonical and contrast profiles.

Five supported controls are `grid_h`, `grid_w`, `palette_size`, `include_zero`, and `texture`. Dimensions, palette count and zero presence are exact and directly observable. Textures are `independent`, `repeat_tiles`, `mixed_uniform`, `contrast`, and `uniform_blocks`. Known controls set to None are unset, following GenCtx. Unknown or retired controls fail; impossible combinations raise a ValueError naming the supplied incompatible axes.

## Verification and limits

Final-source task suite: 156 passed. The unchanged Racket authority supplies labels. Four canonical-fit rivals and two additional wrong rules are executable declarations; the task-local probe tests complete lessons against them. Training approval remains unchanged. Generic self-check mutation gates still fail because they misclassify lawful color edits as invalid inputs; see the returned REVIEW.md and domain evidence.

Default canonical and contrast draws share values across difficulty bands for the same seed/index. Deduplicate exports or use disjoint seed ranges per band. Finite rival elimination is not universal induction.
