"""Generator for puzzle 54d9e175.

Rule: 3x3 cells separated by color 5. Each block has exactly one
non-bg, non-5 marker in [1..4]. Output: each block is filled with
color + 5 (so 1→6, 2→7, 3→8, 4→9), preserving the 5 separators.

Combinatorial axes (8): block_rows, block_cols, marker_position,
palette_subset, separator_color, anchor_corner, asymmetry_force,
include_decoy.
Degenerates: empty_block, full_block, mismatched_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5fc361f309a"
VERSION = "1.1.1"  # add executable self_check for block/separator/marker invariants
TASK_ID = "d5fc361f309a"
SUMMARY = "3x3 cells with markers 1..4; rule fills each block with marker+5."

INVARIANTS = [
    "every 3x3 block contains exactly one non-bg non-5 marker",
    "separator rows and cols are color 5",
    "marker colors in 1..4 so output colors stay in 6..9",
]

MARKER_POSITIONS = ("center", "corner", "edge_mid", "scattered",
                    "diagonal")
DEGENERATE_TEXTURES = ("empty_block", "full_block", "mismatched_marker")
HELPFUL_TEXTURES = MARKER_POSITIONS

AXES = {
    "block_rows":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "block_cols":      {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "marker_position":{"type": "str", "default": "rng helpful",
                       "valid": "center|corner|edge_mid|scattered|diagonal"},
    "palette_subset":  {"type": "str", "default": "all (1..4)",
                       "valid": "all|warm|cool"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "include_decoy":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for marker_position",
                       "valid": "center|corner|edge_mid|scattered|diagonal|empty_block|full_block|mismatched_marker"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify separator lattice and one 1..4 marker inside every 3x3 block."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if (h + 1) % 4 != 0 or (w + 1) % 4 != 0:
        errs.append(f"grid shape {h}x{w} is not a 3x3-block lattice separated every 4th row/col")
        return errs
    for r in range(3, h, 4):
        bad = [c for c in range(w) if grid[r][c] != 5]
        if bad:
            errs.append(f"separator row {r} has non-5 cells at {bad[:4]}")
            break
    for c in range(3, w, 4):
        bad = [r for r in range(h) if grid[r][c] != 5]
        if bad:
            errs.append(f"separator col {c} has non-5 cells at {bad[:4]}")
            break
    for br in range((h + 1) // 4):
        for bc in range((w + 1) // 4):
            top, left = br * 4, bc * 4
            block = [grid[top + dr][left + dc] for dr in range(3) for dc in range(3)]
            markers = [v for v in block if v not in (0, 5)]
            if len(markers) != 1:
                errs.append(f"block {(br, bc)} has {len(markers)} markers, expected exactly one")
            elif markers[0] not in (1, 2, 3, 4):
                errs.append(f"block {(br, bc)} marker {markers[0]} is outside 1..4")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        br_lo, br_hi, bc_lo, bc_hi = 1, 1, 2, 3
    elif difficulty == "hard":
        br_lo, br_hi, bc_lo, bc_hi = 3, 4, 4, 5
    else:
        br_lo, br_hi, bc_lo, bc_hi = 1, 3, 2, 4
    block_rows = int(overrides.get("block_rows",
                                   ctx.draw_int("block_rows", br_lo, br_hi)))
    block_cols = int(overrides.get("block_cols",
                                   ctx.draw_int("block_cols", bc_lo, bc_hi)))
    block_rows = max(1, min(4, block_rows))
    block_cols = max(1, min(5, block_cols))
    marker_pos = (overrides.get("texture") or
                  overrides.get("marker_position")
                  or ctx.draw_choice("marker_position",
                                     list(MARKER_POSITIONS)))
    palette_subset = overrides.get("palette_subset", "all")
    if palette_subset == "warm":
        pal = [2, 3, 4]
    elif palette_subset == "cool":
        pal = [1, 4]
    else:
        pal = [1, 2, 3, 4]
    h = block_rows * 4 - 1
    w = block_cols * 4 - 1
    g = full_grid(h, w, 0)
    for r in range(3, h, 4):
        for c in range(w):
            g[r][c] = 5
    for c in range(3, w, 4):
        for r in range(h):
            g[r][c] = 5
    for br in range(block_rows):
        for bc in range(block_cols):
            top = br * 4
            left = bc * 4
            rr, cc = _marker_pos(marker_pos, top, left, rng)
            g[rr][cc] = rng.choice(pal)
    return g


def _marker_pos(kind, top, left, rng):
    if kind == "center":
        return top + 1, left + 1
    if kind == "corner":
        dr, dc = rng.choice([(0, 0), (0, 2), (2, 0), (2, 2)])
        return top + dr, left + dc
    if kind == "edge_mid":
        dr, dc = rng.choice([(0, 1), (1, 0), (1, 2), (2, 1)])
        return top + dr, left + dc
    if kind == "diagonal":
        dr = rng.choice([0, 1, 2])
        return top + dr, left + dr
    rr = top + rng.randint(0, 2)
    cc = left + rng.randint(0, 2)
    return rr, cc


def _draw_from_degenerate(name, rng):
    block_rows = 2; block_cols = 3
    h = block_rows * 4 - 1; w = block_cols * 4 - 1
    g = full_grid(h, w, 0)
    for r in range(3, h, 4):
        for c in range(w):
            g[r][c] = 5
    for c in range(3, w, 4):
        for r in range(h):
            g[r][c] = 5
    if name == "empty_block":
        # Skip marker in middle block — rule's for/first returns #f
        for br in range(block_rows):
            for bc in range(block_cols):
                if (br, bc) == (0, 1):
                    continue
                top = br * 4; left = bc * 4
                g[top + 1][left + 1] = rng.choice([1, 2, 3, 4])
        return g
    if name == "full_block":
        # Every cell of every block has a marker (extra info)
        for br in range(block_rows):
            for bc in range(block_cols):
                top = br * 4; left = bc * 4
                color = rng.choice([1, 2, 3, 4])
                for dr in range(3):
                    for dc in range(3):
                        g[top + dr][left + dc] = color
        return g
    if name == "mismatched_marker":
        # Markers >4 (out of range)
        for br in range(block_rows):
            for bc in range(block_cols):
                top = br * 4; left = bc * 4
                g[top + 1][left + 1] = rng.choice([6, 7, 8, 9])
        return g
    return g
