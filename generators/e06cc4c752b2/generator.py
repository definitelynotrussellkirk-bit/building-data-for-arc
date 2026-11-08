"""Generator for E28: isolated singleton markers expand into horizontal 3-bars.

The selected Racket rule scans the original grid row-major.  Each nonzero cell
whose four cardinal neighbours are background keeps its value and paints an
empty immediate neighbour on each horizontal side.  This generator emits a
strict, separated sub-domain where every marker is such a singleton and every
resulting 3-bar remains disjoint from the others.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e06cc4c752b2"
VERSION = "1.3.0"
TASK_ID = "e06cc4c752b2"
RULE_HASH = "4cf331b98beb"
SUMMARY = "Separated singleton markers expand into horizontal bars of length three."

INVARIANTS = [
    "rectangular exact-integer ARC grid with height 3..15 and width 5..16",
    "at least one nonzero marker, never on a horizontal edge",
    "every marker is an isolated singleton in the original grid",
    "expanded 3-bar footprints remain separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "monochrome", "varied")
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "n_markers", "palette_kind", "texture"}
_PALETTES = {
    "default": tuple(range(1, 10)),
    "warm": (2, 3, 4, 6, 7),
    "cool": (1, 5, 8, 9),
    "monochrome": tuple(range(1, 10)),
    "varied": tuple(range(1, 10)),
}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng", "valid": "3..15"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng", "valid": "5..16"},
    "n_markers": {"type": "int", "default": "difficulty-aware rng", "valid": "1..8 and <= layout capacity"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
}


def _validate_overrides(overrides: dict) -> dict:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "n_markers"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an exact integer (not bool)")
    for name in ("palette_kind", "texture"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if type(value) is not str or value not in PALETTE_KINDS:
                raise ValueError(f"{name} must be one of {PALETTE_KINDS}")
    palette = overrides.get("palette_kind")
    texture = overrides.get("texture")
    if palette is not None and texture is not None and palette != texture:
        raise ValueError("palette_kind and texture aliases must agree when both are supplied")
    normalized = dict(overrides)
    if texture is not None:
        normalized["palette_kind"] = texture
    normalized.pop("texture", None)
    return normalized


def _bands(difficulty):
    if difficulty is None:
        return (3, 15), (5, 16), (1, 8)
    if difficulty == "easy":
        return (5, 7), (7, 10), (2, 3)
    if difficulty == "medium":
        return (8, 11), (10, 13), (3, 5)
    if difficulty == "hard":
        return (12, 15), (13, 16), (5, 8)
    raise ValueError("difficulty must be None, easy, medium, or hard")


def _lattices(height: int, width: int) -> list[list[tuple[int, int]]]:
    """Separated center lattices whose expanded 3-bars cannot touch."""
    result: list[list[tuple[int, int]]] = []
    for row_offset in (0, 1):
        rows = list(range(row_offset, height, 2))
        if not rows:
            continue
        for col_offset in (1, 2, 3, 4):
            cols = list(range(col_offset, width - 1, 4))
            if cols:
                result.append([(r, c) for r in rows for c in cols])
    return result


def _palette_values(ctx, kind: str, count: int) -> list[int]:
    options = list(_PALETTES[kind])
    if kind == "monochrome":
        return [ctx.draw_choice("marker_color", options)] * count
    rng = ctx.draw_rng("marker_colors")
    if kind == "varied":
        rng.shuffle(options)
        return [options[index % len(options)] for index in range(count)]
    return [rng.choice(options) for _ in range(count)]


def self_check(grid, *, difficulty=None, meta=None):
    """Return all structural domain errors without raising or mutating ``grid``."""
    errors: list[str] = []
    if type(grid) is not list or not grid:
        return ["grid must be a nonempty list of rows"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be nonempty lists"]
    height, width = len(grid), len(grid[0])
    if not 3 <= height <= 15 or not 5 <= width <= 16:
        errors.append("grid dimensions must be height 3..15 and width 5..16")
    for index, row in enumerate(grid):
        if type(row) is not list or len(row) != width:
            errors.append(f"row {index} is ragged or not a list")
            continue
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                errors.append("cells must be exact integer colors 0..9")
                break
    if errors:
        return errors

    markers = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0]
    if not markers:
        return ["at least one singleton marker is required"]
    for r, c in markers:
        if c in (0, width - 1):
            errors.append(f"marker at horizontal edge {(r, c)}")
        for rr, cc in markers:
            if (rr, cc) == (r, c):
                continue
            if abs(rr - r) <= 1 and abs(cc - c) <= 3:
                errors.append(
                    f"marker {(r, c)} is too close to {(rr, cc)} for isolated separated expansion"
                )
                break
    return errors


def rule_mirror(grid):
    """Python mirror of the exact selected Racket scan on the admitted domain."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid generator-domain grid: " + "; ".join(errors))
    source = deepcopy(grid)
    output = deepcopy(grid)
    height, width = len(source), len(source[0])
    for r in range(height):
        for c in range(width):
            value = source[r][c]
            if value == 0:
                continue
            isolated = all(
                not (0 <= nr < height and 0 <= nc < width and source[nr][nc] != 0)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            )
            if not isolated:
                continue
            if c - 1 >= 0 and output[r][c - 1] == 0:
                output[r][c - 1] = value
            if c + 1 < width and output[r][c + 1] == 0:
                output[r][c + 1] = value
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    normalized = _validate_overrides(overrides)
    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _bands(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )
    height = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    width = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    lattices = _lattices(height, width)
    capacity = max((len(cells) for cells in lattices), default=0)
    if capacity < 1:
        raise ValueError("grid has no legal singleton-expansion capacity")

    if normalized.get("n_markers") is not None:
        target = ctx.draw_int_strict("n_markers", 1, 8)
    else:
        target = ctx.draw_int("n_markers", n_lo, min(n_hi, capacity))
    if target > capacity:
        raise ValueError(
            f"n_markers={target} exceeds separated layout capacity {capacity} "
            f"for grid {height}x{width}"
        )

    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    feasible = [cells for cells in lattices if len(cells) >= target]
    layout_rng = ctx.draw_rng("layout")
    candidates = list(layout_rng.choice(feasible))
    positions = layout_rng.sample(candidates, target)
    colors = _palette_values(ctx, kind, target)

    grid = full_grid(height, width, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    errors = self_check(grid, difficulty=difficulty)
    if errors:  # defensive: generation should make this unreachable
        raise RuntimeError("generated invalid grid: " + "; ".join(errors))
    return grid
