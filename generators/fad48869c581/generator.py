"""Generator for ``fad48869c581`` — complete isolated L triominoes.

Every active 2×2 window contains three cells of one nonzero color and one
background corner.  The rule fills the missing corner with that color.  The
constructor uses a three-cell lattice so active blocks stay isolated and the
canonical predicate fires exactly on the intended cells.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fad48869c581"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "65f702bea317"

SUMMARY = (
    "A zero-background grid contains isolated monochrome L triominoes in 2x2 "
    "windows. Complete every L by filling its unique missing corner with the "
    "same color; leave all other cells unchanged."
)

INVARIANTS = [
    "background is 0",
    "each active 2x2 block has exactly three cells of one nonzero color",
    "the fourth cell in the block is empty",
    "active blocks are separated by at least one blank row or column",
    "the reference rule fires exactly on the intended missing corners",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_blocks", "full_2x2", "two_corners")

AXES = {
    "grid_h": {"type": "int", "default": "7..10 easy / 10..15 medium / 14..22 hard", "valid": "3..30"},
    "grid_w": {"type": "int", "default": "7..10 easy / 10..15 medium / 14..22 hard", "valid": "3..30"},
    "n_blocks": {"type": "int", "default": "2..3 easy / 3..6 medium / 5..10 hard", "valid": "1..10"},
}

_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 7, 9, 1, 3, 6, 5, 8),
    "cool": (8, 6, 5, 1, 9, 3, 2, 4, 7),
    "varied": (9, 7, 5, 3, 1, 8, 6, 4, 2),
}


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _fires(g):
    """Return exactly the cells the selected Racket rule would fill."""
    if not g or not g[0]:
        return set()
    h, w = len(g), len(g[0])
    out = set()
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [g[r][c], g[r][c + 1], g[r + 1][c], g[r + 1][c + 1]]
            nz = [v for v in vals if v != 0]
            if len(nz) == 3 and len(set(nz)) == 1 and vals.count(0) == 1:
                index = vals.index(0)
                dr, dc = divmod(index, 2)
                out.add((r + dr, c + dc))
    return out


def rule_mirror(grid):
    """Pure Python mirror of the canonical snapshot-window rule."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")
    out = [row[:] for row in grid]
    for r, c in _fires(grid):
        values = [
            grid[rr][cc]
            for rr in (r - 1, r)
            for cc in (c - 1, c)
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0])
        ]
        # A firing cell can belong to more than one 2x2 window in arbitrary
        # inputs. Recover its canonical color from the first matching window.
        for top in range(max(0, r - 1), min(r + 1, len(grid) - 1)):
            for left in range(max(0, c - 1), min(c + 1, len(grid[0]) - 1)):
                vals = [
                    grid[top][left], grid[top][left + 1],
                    grid[top + 1][left], grid[top + 1][left + 1],
                ]
                nz = [value for value in vals if value]
                if len(nz) == 3 and len(set(nz)) == 1 and grid[r][c] == 0:
                    out[r][c] = nz[0]
                    break
            if out[r][c] != 0:
                break
    return out


def _slot_positions(length: int) -> list[int]:
    return list(range(0, length - 1, 3))


def _capacity(h: int, w: int) -> int:
    return len(_slot_positions(h)) * len(_slot_positions(w))


def _choose_slots(h: int, w: int, count: int, rng) -> list[tuple[int, int]]:
    positions = [(r, c) for r in _slot_positions(h) for c in _slot_positions(w)]
    if len(positions) < count:
        raise ValueError(f"cannot place {count} isolated blocks in a {h}x{w} grid")
    rng.shuffle(positions)
    selected: list[tuple[int, int]] = []
    if count >= 4:
        quadrants = [[], [], [], []]
        for r, c in positions:
            q = (2 if r + 0.5 >= h / 2 else 0) + (1 if c + 0.5 >= w / 2 else 0)
            quadrants[q].append((r, c))
        for bucket in quadrants:
            if bucket:
                selected.append(bucket[0])
    for position in positions:
        if position not in selected:
            selected.append(position)
        if len(selected) == count:
            break
    return selected


def _draw_clean_blocks(h: int, w: int, count: int, rng, palette_kind: str):
    grid = full_grid(h, w, 0)
    positions = _choose_slots(h, w, count, rng)
    colors = list(_PALETTES[palette_kind])
    rng.shuffle(colors)
    intended = set()
    for index, (r, c) in enumerate(positions):
        color = colors[index % len(colors)]
        missing = rng.randrange(4)
        cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
        for cell_index, (rr, cc) in enumerate(cells):
            if cell_index != missing:
                grid[rr][cc] = color
        intended.add(cells[missing])
    if _fires(grid) != intended:
        raise RuntimeError("constructed scene has spurious or missing rule fires")
    return grid


def _minimum_axis_for_slots(slot_count: int) -> int:
    return max(3, 3 * slot_count)


def _draw_dimensions(ctx, band: str, n_blocks: int) -> tuple[int, int]:
    ordinary = {
        "easy": ((7, 10), (7, 10)),
        "medium": ((10, 15), (10, 15)),
        "hard": ((14, 22), (14, 22)),
    }
    h_range, w_range = ordinary[band]
    h_override = ctx.overrides.get("grid_h")
    w_override = ctx.overrides.get("grid_w")
    if h_override is not None and (type(h_override) is not int or not 3 <= h_override <= 30):
        raise ValueError("grid_h must be an exact integer in 3..30")
    if w_override is not None and (type(w_override) is not int or not 3 <= w_override <= 30):
        raise ValueError("grid_w must be an exact integer in 3..30")

    if h_override is not None and w_override is not None:
        if _capacity(h_override, w_override) < n_blocks:
            raise ValueError(f"cannot place {n_blocks} isolated blocks in a {h_override}x{w_override} grid")
        return ctx.draw_int("grid_h", h_override, h_override), ctx.draw_int("grid_w", w_override, w_override)

    if h_override is not None:
        row_slots = len(_slot_positions(h_override))
        needed_cols = math.ceil(n_blocks / max(1, row_slots))
        low = max(w_range[0], _minimum_axis_for_slots(needed_cols))
        if low > w_range[1]:
            raise ValueError(f"cannot place {n_blocks} isolated blocks with grid_h={h_override}")
        h = ctx.draw_int("grid_h", h_override, h_override)
        w = ctx.draw_int("grid_w", low, w_range[1])
        return h, w

    if w_override is not None:
        col_slots = len(_slot_positions(w_override))
        needed_rows = math.ceil(n_blocks / max(1, col_slots))
        low = max(h_range[0], _minimum_axis_for_slots(needed_rows))
        if low > h_range[1]:
            raise ValueError(f"cannot place {n_blocks} isolated blocks with grid_w={w_override}")
        h = ctx.draw_int("grid_h", low, h_range[1])
        w = ctx.draw_int("grid_w", w_override, w_override)
        return h, w

    side_slots = math.ceil(math.sqrt(n_blocks))
    minimum = _minimum_axis_for_slots(side_slots)
    h = ctx.draw_int("grid_h", max(h_range[0], minimum), h_range[1])
    w = ctx.draw_int("grid_w", max(w_range[0], minimum), w_range[1])
    return h, w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    allowed = set(AXES) | {"texture", "palette_kind"}
    unknown = set(overrides) - allowed
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if "texture" in overrides and "palette_kind" in overrides:
        raise ValueError("texture and palette_kind are aliases; provide only one")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if len(overrides) != 1:
            raise ValueError("degenerate texture cannot be combined with other overrides")
        return _draw_from_degenerate(texture)
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture: {texture!r}")
    palette_override = overrides.get("palette_kind")
    if palette_override is not None and palette_override not in PALETTE_KINDS:
        raise ValueError(f"unknown palette_kind: {palette_override!r}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    ordinary_counts = {"easy": (2, 3), "medium": (3, 6), "hard": (5, 10)}
    if "n_blocks" in overrides:
        n_blocks = ctx.draw_int("n_blocks", 1, 10)
    else:
        n_blocks = ctx.draw_int("n_blocks", *ordinary_counts[band])
    h, w = _draw_dimensions(ctx, band, n_blocks)
    palette_kind = texture or palette_override
    if palette_kind is None:
        palette_kind = ctx.draw_choice("texture", PALETTE_KINDS)
    grid = _draw_clean_blocks(h, w, n_blocks, ctx.draw_rng("layout"), palette_kind)
    errors = self_check(grid, difficulty=band, meta={"n_blocks": n_blocks})
    if errors:
        raise RuntimeError(f"internal generator defect: {errors}")
    return grid


def _draw_from_degenerate(name):
    grid = full_grid(7, 7, 0)
    if name == "no_blocks":
        return grid
    if name == "full_2x2":
        for dr in range(2):
            for dc in range(2):
                grid[2 + dr][2 + dc] = 4
        return grid
    if name == "two_corners":
        grid[1][1] = 4
        grid[2][2] = 4
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")


def observe_overrides(grid) -> dict[str, int]:
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blocks": len(_fires(grid))}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["invalid cell"]
    fires = _fires(grid)
    errors: list[str] = []
    expected = meta.get("n_blocks") if isinstance(meta, dict) else None
    if expected is not None:
        if len(fires) != expected:
            errors.append(f"expected exactly {expected} fillable blocks, got {len(fires)}")
    else:
        band = _band(difficulty)
        low, high = {"easy": (2, 3), "medium": (3, 6), "hard": (5, 10)}[band]
        if not low <= len(fires) <= high:
            errors.append(f"expected {low}-{high} fillable blocks, got {len(fires)}")
    for r, c in fires:
        if grid[r][c] != 0:
            errors.append(f"rule fire at {(r, c)} is not on background")
    output = rule_mirror(grid)
    changed = {(r, c) for r in range(h) for c in range(w) if output[r][c] != grid[r][c]}
    if changed != fires:
        errors.append("rule mirror changed cells other than the intended missing corners")
    return errors
