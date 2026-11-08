"""Generator for arc_additional_puzzles_21_set19_bundle:M129.

Rule: three command-labeled 3×3 blocks (cols 1, 5, 9) are transformed by
their command codes and packed horizontally.

Combinatorial axes (8): grid_h/w, palette_kind, command_offset,
palette_size, position_bias, n_distinct_colors, command_density, texture.
Degenerates: no_commands, no_blocks, missing_block.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef648b57df8c"
VERSION = "2.1.0"  # difficulty bands now vary motif mass; axes are lint-validated literals
TASK_ID = "ef648b57df8c"
SUMMARY = (
    "Fixed 5x13 grid with THREE 3x3 blocks at rows 2-4, cols starting 1/5/9. "
    "Each block is a varied 3x3 pattern in a distinct color, with a COMMAND "
    "code above its center (g[0][start+1]) chosen INDEPENDENTLY from {1,2,3,4}: "
    "1=identity, 2=rotate-cw, 3=flip-lr, 4=rotate-180. Rule: transform each "
    "block by its command and pack the three left-to-right with a 1-col gap "
    "(output 3x11). Commands vary independently (repeats allowed, all 4 "
    "covered); block patterns and colors vary. (Was a fixed L-tetromino in "
    "each block and consecutive-distinct commands.)"
)

INVARIANTS = [
    "three 3x3 blocks at rows 2-4, cols starting 1/5/9; row 1 blank",
    "each block has a command code in {1,2,3,4} above its center",
    "block commands are independent (may repeat); across data all 4 appear",
    "block patterns are non-empty 3x3 motifs in distinct colors",
    "difficulty bands vary motif cell count: easy 3-4, hard 5-6",
]

PALETTE_KINDS = ("default", "varied_offset", "warm_blocks", "cool_blocks")
DEGENERATE_TEXTURES = ("no_commands", "no_blocks", "missing_block")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5"},
    "grid_w":         {"type": "int", "default": "13", "valid": "13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|varied_offset|warm_blocks|cool_blocks"},
    "command":        {"type": "int", "default": "rng 1..4 per block (independent)", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "3 (one per block)", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed_starts",
                       "valid": "fixed_starts"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|varied_offset|warm_blocks|cool_blocks|no_commands|no_blocks|missing_block"},
}


def _motif_cell_range(difficulty):
    """Return the motif cell-count band used to make difficulty visible."""
    if difficulty == "easy":
        return 3, 4
    if difficulty == "hard":
        return 5, 6
    return 3, 6


def _pattern(rng, *, min_cells=3, max_cells=6):
    """Random non-empty connected 3x3 motif."""
    k = rng.randint(min_cells, max_cells)
    cells = {(rng.randint(0, 2), rng.randint(0, 2))}
    tries = 0
    while len(cells) < k and tries < 40:
        tries += 1
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr <= 2 and 0 <= nc <= 2:
            cells.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    colors = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    rng = ctx.draw_rng("layout")
    min_cells, max_cells = _motif_cell_range(difficulty)
    g = full_grid(5, 13, 0)
    starts = [1, 5, 9]
    for start, color in zip(starts, colors):
        cmd = rng.choice([1, 2, 3, 4])           # independent per block (may repeat)
        g[0][start + 1] = cmd
        for (dr, dc) in _pattern(rng, min_cells=min_cells, max_cells=max_cells):
            g[2 + dr][start + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 13, 0)
    starts = [1, 5, 9]
    if name == "no_commands":
        # blocks but no command codes — no transform to apply
        for start, color in zip(starts, [5, 6, 7]):
            for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
                g[2 + dr][start + dc] = color
        return g
    if name == "no_blocks":
        # commands but no blocks below — rule has nothing to transform
        for start, cmd in zip(starts, [1, 2, 3]):
            g[0][start + 1] = cmd
        return g
    if name == "missing_block":
        # 3 commands but only 2 blocks — third command has no payload
        commands = [1, 2, 3]
        for start, cmd in zip(starts, commands):
            g[0][start + 1] = cmd
        for start, color in zip(starts[:2], [5, 6]):
            for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
                g[2 + dr][start + dc] = color
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if len(grid) != 5 or len(grid[0]) != 13:
        return ["expected fixed 5x13 command grid"]
    starts = [1, 5, 9]
    block_colors = []
    for start in starts:
        cmd = grid[0][start + 1]
        if cmd not in (1, 2, 3, 4):
            msgs.append(f"bad command {cmd} above block {start}")
        vals = {grid[r][c] for r in range(2, 5) for c in range(start, start + 3) if grid[r][c] != 0}
        cells = [(r, c) for r in range(2, 5) for c in range(start, start + 3) if grid[r][c] != 0]
        if len(vals) != 1:
            msgs.append(f"block at {start} should have exactly one payload color, got {vals}")
        else:
            block_colors.append(next(iter(vals)))
        if not (3 <= len(cells) <= 6):
            msgs.append(f"block at {start} has {len(cells)} cells outside 3..6")
    if len(block_colors) == 3 and len(set(block_colors)) != 3:
        msgs.append("block colors are not distinct")
    return msgs
