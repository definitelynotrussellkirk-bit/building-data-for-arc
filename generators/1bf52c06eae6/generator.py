"""Generator for puzzle 5751f35e / 1bf52c06eae6.

For every non-background color, the canonical rule takes the color's bounding
box, expands it to a square whose side is ``max(height, width)`` anchored at
the bounding-box top-left, then resolves overlaps in increasing square-area
order (the smaller square wins).

This repaired generator makes every declared ordinary control observable.  It
constructs 2--4 sparse colored bounding boxes with distinct square areas and at
least one expanded-square overlap.  Degenerate textures remain explicit and
are never sampled by ordinary generation.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1bf52c06eae6"
VERSION = "1.2.0"
TASK_ID = GENERATOR_ID
SUMMARY = "Sparse colored bboxes expand to top-left-anchored squares; smaller squares win overlaps."
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "2..4 distinct non-background colors",
    "expanded square areas are pairwise distinct",
    "at least one pair of expanded squares overlaps",
]

POSITION_BIASES = ("scattered", "centered_inside", "corners", "spread", "diagonal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("tied_areas", "single_color", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h": {"type": "int", "default": "difficulty band", "valid": "5..16"},
    "grid_w": {"type": "int", "default": "difficulty band", "valid": "8..18"},
    "n_colors": {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "warm|cool|broad|primary"},
    "density_a": {"type": "float", "default": "rng 0.35..0.55", "valid": "0.2..0.7"},
    "density_b": {"type": "float", "default": "rng 0.45..0.65", "valid": "0.2..0.8"},
    "position_bias": {"type": "str", "default": "rng helpful", "valid": "|".join(POSITION_BIASES)},
    "anchor_corner": {"type": "bool", "default": "false", "valid": "true|false"},
    "texture": {"type": "str", "default": "alias for position_bias", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PALETTES = {
    "warm": (2, 3, 4, 6, 9),
    "cool": (1, 5, 7, 8, 3),
    "broad": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "primary": (1, 2, 3, 4, 6),
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        kind = AXES[name]["type"]
        if kind == "int" and type(value) is not int:
            raise TypeError(f"{name} must be a plain integer")
        if kind == "float" and type(value) is not float:
            raise TypeError(f"{name} must be a plain float")
        if kind == "str" and type(value) is not str:
            raise TypeError(f"{name} must be a string")
        if kind == "bool" and type(value) is not bool:
            raise TypeError(f"{name} must be a boolean")


def _difficulty_bounds(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (5, 8), (8, 11)
    if difficulty == "medium":
        return (8, 12), (10, 14)
    if difficulty == "hard":
        return (12, 16), (14, 18)
    if difficulty is None:
        return (7, 12), (10, 14)
    raise ValueError("difficulty must be easy, medium, hard or None")


def _float_control(ctx, label: str, low: float, high: float, default_low: float, default_high: float) -> float:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = ctx.overrides[label]
    else:
        value = ctx.draw_rng(label).uniform(default_low, default_high)
    if type(value) is not float:
        raise TypeError(f"{label} must be a plain float")
    if not low <= value <= high:
        raise ValueError(f"{label} must be in {low}..{high}")
    # Record through the public provenance stores because GenCtx has no float draw.
    ctx.drawn_store[label] = value
    if label in ctx.overrides and ctx.overrides[label] is not None:
        ctx.override_used_store[label] = value
    return value


def _side_lengths(max_side: int, count: int) -> list[int]:
    if max_side < count + 1:
        raise ValueError("grid is too small for the requested number of distinct square areas")
    if count == 1:
        return [max_side]
    values = []
    for index in range(count):
        raw = 2 + round(index * (max_side - 2) / (count - 1))
        if values and raw <= values[-1]:
            raw = values[-1] + 1
        values.append(raw)
    if values[-1] > max_side:
        values = list(range(max_side - count + 1, max_side + 1))
    return values


def _anchor(height: int, width: int, bias: str, anchor_corner: bool, rng) -> tuple[int, int]:
    if anchor_corner:
        return (1 if height > 1 else 0, 1 if width > 1 else 0)
    if bias == "centered_inside":
        return height // 2, width // 2
    if bias == "corners":
        return rng.choice(((1, 1), (1, width - 2), (height - 2, 1), (height - 2, width - 2)))
    if bias == "diagonal":
        row = rng.randrange(1, max(2, height - 1))
        col = min(width - 2, max(1, round(row * (width - 1) / max(1, height - 1))))
        return row, col
    if bias == "spread":
        return rng.randrange(1, height - 1), rng.randrange(1, width - 1)
    return rng.randrange(height), rng.randrange(width)


def _box_candidates(height: int, width: int, side: int, anchor: tuple[int, int], rng):
    ar, ac = anchor
    row_starts = range(max(0, ar - side + 1), min(ar, height - side) + 1)
    col_starts = range(max(0, ac - side + 1), min(ac, width - side) + 1)
    short = max(2, side - 1)
    candidates = []
    for r1 in row_starts:
        for c1 in col_starts:
            for box_h, box_w in ((side, short), (short, side)):
                r2, c2 = r1 + box_h - 1, c1 + box_w - 1
                for diagonal in (0, 1):
                    if diagonal == 0:
                        critical = ((r1, c1), (r2, c2))
                    else:
                        critical = ((r1, c2), (r2, c1))
                    candidates.append((r1, c1, r2, c2, critical))
    rng.shuffle(candidates)
    return candidates


def _overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _construct_scene(height: int, width: int, colors: list[int], densities: tuple[float, float],
                     bias: str, anchor_corner: bool, rng) -> list[list[int]]:
    sides = _side_lengths(min(height, width), len(colors))
    for attempt in range(256):
        attempt_rng = rng if attempt == 0 else type(rng)(rng.getrandbits(128) ^ attempt)
        anchor = _anchor(height, width, bias, anchor_corner, attempt_rng)
        grid = full_grid(height, width, 0)
        occupied: set[tuple[int, int]] = set()
        boxes: list[tuple[int, int, int, int]] = []
        ok = True
        for rank, (color, side) in enumerate(zip(colors, sides, strict=True)):
            candidates = _box_candidates(height, width, side, anchor, attempt_rng)
            if anchor_corner and rank == 0:
                candidates.sort(key=lambda item: 0 if (0, 0) in item[4] else 1)
            if bias == "diagonal":
                candidates.sort(key=lambda item: abs(item[0] - item[1]))
            elif bias == "centered_inside":
                candidates.sort(key=lambda item: abs((item[0] + item[2]) - height + 1)
                                + abs((item[1] + item[3]) - width + 1))
            chosen = next((item for item in candidates if not (set(item[4]) & occupied)), None)
            if chosen is None:
                ok = False
                break
            r1, c1, r2, c2, critical = chosen
            for row, col in critical:
                grid[row][col] = color
                occupied.add((row, col))
            boxes.append((r1, c1, r1 + side - 1, c1 + side - 1))
            probability = densities[rank % 2]
            fill = [(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)
                    if (row, col) not in occupied]
            attempt_rng.shuffle(fill)
            for row, col in fill:
                if attempt_rng.random() < probability:
                    grid[row][col] = color
                    occupied.add((row, col))
        if ok and any(_overlap(left, right) for left, right in combinations(boxes, 2)):
            if self_check(grid) == []:
                return grid
    raise RuntimeError("could not construct distinct overlapping square bboxes")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if any(value is not None for name, value in overrides.items() if name != "texture"):
            raise ValueError("degenerate textures do not support additional overrides")
        return _draw_from_degenerate(texture)

    settings = dict(overrides)
    if texture is not None:
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture: {texture}")
        if settings.get("position_bias") not in (None, texture):
            raise ValueError("texture and position_bias must agree")
        settings["position_bias"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=settings)
    (h_lo, h_hi), (w_lo, w_hi) = _difficulty_bounds(difficulty)
    height = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    width = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    n_colors = ctx.draw_int_strict("n_colors", 2, 4)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    density_a = _float_control(ctx, "density_a", 0.2, 0.7, 0.35, 0.55)
    density_b = _float_control(ctx, "density_b", 0.2, 0.8, 0.45, 0.65)
    bias = ctx.draw_choice("position_bias", POSITION_BIASES)
    anchor_corner = ctx.draw_choice("anchor_corner", (False, True))

    palette_rng = ctx.draw_rng("palette")
    pool = list(_PALETTES[palette_kind])
    if n_colors > len(pool):
        raise ValueError(f"palette {palette_kind!r} cannot provide {n_colors} colors")
    colors = palette_rng.sample(pool, n_colors)
    return _construct_scene(height, width, colors, (density_a, density_b), bias,
                            anchor_corner, ctx.draw_rng("layout"))


def _bbox_squares(grid: list[list[int]]) -> list[tuple[int, int, int, int, int, int]]:
    height, width = len(grid), len(grid[0])
    cells: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                cells.setdefault(color, []).append((row, col))
    result = []
    for color, points in sorted(cells.items()):
        rows = [row for row, _ in points]
        cols = [col for _, col in points]
        r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
        side = max(r2 - r1 + 1, c2 - c1 + 1)
        result.append((side * side, color, r1, c1, min(height - 1, r1 + side - 1),
                       min(width - 1, c1 + side - 1)))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be exact integers in 0..9"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    boxes = _bbox_squares(grid)
    errors = []
    if not 2 <= len(boxes) <= 4:
        errors.append("ordinary scene must contain 2..4 non-background colors")
    areas = [box[0] for box in boxes]
    if len(areas) != len(set(areas)):
        errors.append("expanded square areas must be pairwise distinct")
    rectangles = [(box[2], box[3], box[4], box[5]) for box in boxes]
    if len(rectangles) >= 2 and not any(_overlap(left, right) for left, right in combinations(rectangles, 2)):
        errors.append("at least one pair of expanded squares must overlap")
    return errors


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(8, 12, 0)
    if name == "tied_areas":
        for row, col in ((1, 1), (3, 3)):
            grid[row][col] = 2
        for row, col in ((1, 7), (3, 9)):
            grid[row][col] = 5
    elif name == "single_color":
        for row, col in ((1, 2), (2, 5), (5, 3), (6, 7)):
            grid[row][col] = 4
    elif name == "full_grid":
        grid = full_grid(8, 12, 6)
    else:
        raise ValueError(f"unknown degenerate texture: {name}")
    return grid
