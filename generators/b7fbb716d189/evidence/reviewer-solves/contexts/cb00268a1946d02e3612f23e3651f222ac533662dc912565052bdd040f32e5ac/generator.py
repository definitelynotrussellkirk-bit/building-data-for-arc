"""Generator for ARC task b7fbb716d189, "Crop and Rotate by Token".

A unique transform token (1..4) occupies one corner.  A separate connected
multicolor motif occupies the interior.  The authoritative rule crops the motif
and applies 1=identity, 2=clockwise rotation, 3=180-degree rotation, or
4=transpose.  Token value and token corner are intentionally independent so a
lesson cannot substitute the canonical corner pattern for reading the token.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b7fbb716d189"
TASK_ID = GENERATOR_ID
RULE_HASH = "5ac5138de6ce"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

CORNERS = ("top_left", "top_right", "bottom_right", "bottom_left")
_CANONICAL_CORNER_FOR_TOKEN = {
    1: "bottom_left",
    2: "top_left",
    3: "bottom_right",
    4: "top_right",
}
_CORNER_CODE_RIVAL = {
    "top_left": 2,
    "top_right": 4,
    "bottom_right": 3,
    "bottom_left": 1,
}
_MOTIF_COLORS = (5, 6, 7, 8, 9)

SUMMARY = (
    "A unique token 1..4 appears in any corner, independently of its value. "
    "A connected 5..9-cell motif in 2..5 colors from 5..9 appears in the "
    "interior. Crop the motif and transform it according to the token: "
    "1=identity, 2=rotate clockwise, 3=rotate 180 degrees, 4=transpose."
)

INVARIANTS = [
    "exactly one token color 1..4, in exactly one corner",
    "all other border cells are background",
    "one 4-connected interior motif of 5..9 cells using 2..5 colors from 5..9",
    "the four token transforms produce distinct outputs for the motif",
    "token value and corner role vary independently",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted 8..12", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "weighted 8..13", "valid": "8..13"},
    "token": {"type": "int", "default": "uniform 1..4", "valid": "1..4"},
    "token_corner": {
        "type": "str",
        "default": "four-corner schedule independent of token value",
        "valid": "top_left|top_right|bottom_right|bottom_left",
    },
    "motif_cells": {"type": "int", "default": "weighted 5..9", "valid": "5..9"},
    "motif_colors": {"type": "int", "default": "weighted 2..5", "valid": "2..5"},
}

# Every advertised cross-product is constructively supported in every band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list = []


def _weighted_axis(ctx, name: str, values: Iterable, favored: Iterable):
    """Draw an exact axis while retaining every declared value in the options."""
    options = list(values) + list(favored)
    return ctx.draw_choice(name, options)


def _corner_position(height: int, width: int, corner: str) -> tuple[int, int]:
    positions = {
        "top_left": (0, 0),
        "top_right": (0, width - 1),
        "bottom_right": (height - 1, width - 1),
        "bottom_left": (height - 1, 0),
    }
    try:
        return positions[corner]
    except KeyError as exc:
        raise ValueError(f"unknown token corner {corner!r}") from exc


def _token_hits(grid) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (1, 2, 3, 4)
    ]


def _motif_hits(grid) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in _MOTIF_COLORS
    ]


def _normalize(points: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    row0 = min(row for row, _ in points)
    col0 = min(col for _, col in points)
    return tuple(sorted((row - row0, col - col0) for row, col in points))


def _random_connected_shape(rng, cell_count: int) -> tuple[tuple[int, int], ...] | None:
    cells = {(0, 0)}
    for _ in range(600):
        if len(cells) == cell_count:
            shape = _normalize(cells)
            height = max(row for row, _ in shape) + 1
            width = max(col for _, col in shape) + 1
            if height >= 2 and width >= 2:
                return shape
            return None
        row, col = rng.choice(sorted(cells))
        drow, dcol = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        candidate = (row + drow, col + dcol)
        if candidate in cells:
            continue
        grown = cells | {candidate}
        rows = [r for r, _ in grown]
        cols = [c for _, c in grown]
        if max(rows) - min(rows) + 1 > 4 or max(cols) - min(cols) + 1 > 4:
            continue
        cells = grown
    return None


def _apply_transform(crop: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in crop]
    if code == 2:
        return [list(row) for row in zip(*crop[::-1])]
    if code == 3:
        return [row[::-1] for row in crop[::-1]]
    if code == 4:
        return [list(row) for row in zip(*crop)]
    raise ValueError(f"transform token must be in 1..4, got {code!r}")


def _crop_from_hits(grid, hits: list[tuple[int, int, int]]) -> list[list[int]]:
    if not hits:
        raise ValueError("motif is empty")
    row0 = min(row for row, _, _ in hits)
    row1 = max(row for row, _, _ in hits)
    col0 = min(col for _, col, _ in hits)
    col1 = max(col for _, col, _ in hits)
    return [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]


def _distinct_transform_outputs(crop: list[list[int]]) -> bool:
    encodings = {
        tuple(tuple(row) for row in _apply_transform(crop, code))
        for code in range(1, 5)
    }
    return len(encodings) == 4


def _random_motif(ctx, cell_count: int, color_count: int) -> tuple[tuple[int, int, int], ...]:
    rng = ctx.draw_rng("motif")
    for _ in range(256):
        shape = _random_connected_shape(rng, cell_count)
        if shape is None:
            continue
        palette = rng.sample(list(_MOTIF_COLORS), color_count)
        colors = palette[:] + [rng.choice(palette) for _ in range(cell_count - color_count)]
        rng.shuffle(colors)
        motif = tuple((row, col, color) for (row, col), color in zip(shape, colors))
        height = max(row for row, _, _ in motif) + 1
        width = max(col for _, col, _ in motif) + 1
        crop = [[0] * width for _ in range(height)]
        for row, col, color in motif:
            crop[row][col] = color
        if _distinct_transform_outputs(crop):
            return motif
    raise RuntimeError("could not construct a transform-distinguishing connected motif")


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "token", "motif_cells", "motif_colors"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    corner = overrides.get("token_corner")
    if corner is not None and (type(corner) is not str or corner not in CORNERS):
        raise ValueError(f"token_corner must be one of {CORNERS}, got {corner!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Canonical-size/palette support is deliberately present in every band,
    # while the full exact override domains remain available everywhere.
    core = ctx.draw_choice("curriculum_profile", ("canonical",) * 4 + ("broad",)) == "canonical"
    if core:
        height_bias = (8, 8, 9, 9) * 8
        width_bias = (8, 9, 10) * 10
        cell_bias = (5, 6) * 12
        color_bias = (3,) * 24
    elif difficulty == "easy":
        height_bias = (8, 9, 10) * 4
        width_bias = (8, 9, 10, 11) * 3
        cell_bias = (5, 6) * 5
        color_bias = (2, 3) * 5
    elif difficulty == "hard":
        height_bias = (10, 11, 12) * 4
        width_bias = (11, 12, 13) * 4
        cell_bias = (7, 8, 9) * 5
        color_bias = (3, 4, 5) * 5
    else:
        height_bias = (8, 9, 10, 11, 12) * 2
        width_bias = (8, 9, 10, 11, 12, 13) * 2
        cell_bias = (5, 6, 7, 8, 9) * 2
        color_bias = (2, 3, 4, 5) * 2

    height = _weighted_axis(ctx, "grid_h", range(8, 13), height_bias)
    width = _weighted_axis(ctx, "grid_w", range(8, 14), width_bias)
    token = ctx.draw_int_strict("token", 1, 4)
    motif_cells = _weighted_axis(ctx, "motif_cells", range(5, 10), cell_bias)
    motif_colors = _weighted_axis(ctx, "motif_colors", range(2, 6), color_bias)

    if overrides.get("token_corner") is not None:
        corner = ctx.draw_choice("token_corner", CORNERS)
    else:
        # Offset 0 reproduces the canonical association; offsets 1..3 refute it.
        # Any three consecutive sample indices therefore contain an explicit
        # token/corner-independence demonstration.
        canonical = _CANONICAL_CORNER_FOR_TOKEN[token]
        corner = CORNERS[(CORNERS.index(canonical) + sample_index % 4) % 4]
        corner = ctx.draw_choice("token_corner", (corner,))

    motif = _random_motif(ctx, motif_cells, motif_colors)
    motif_height = max(row for row, _, _ in motif) + 1
    motif_width = max(col for _, col, _ in motif) + 1
    position_rng = ctx.draw_rng("motif_position")
    row0 = position_rng.randint(1, height - motif_height - 1)
    col0 = position_rng.randint(1, width - motif_width - 1)

    grid = full_grid(height, width, 0)
    token_row, token_col = _corner_position(height, width, corner)
    grid[token_row][token_col] = token
    for row, col, color in motif:
        grid[row0 + row][col0 + col] = color
    return grid


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    pending = deque([next(iter(cells))])
    seen = {pending[0]}
    while pending:
        row, col = pending.popleft()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + drow, col + dcol)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen == cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 12:
        errors.append(f"grid height {height} outside 8..12")
    if not 8 <= width <= 13:
        errors.append(f"grid width {width} outside 8..13")

    tokens = _token_hits(grid)
    if len(tokens) != 1:
        errors.append(f"expected exactly one transform token, found {len(tokens)}")
    else:
        row, col, _ = tokens[0]
        if (row, col) not in {
            (0, 0),
            (0, width - 1),
            (height - 1, width - 1),
            (height - 1, 0),
        }:
            errors.append("transform token must occupy a corner")

    border_nonzero = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
        and (row in (0, height - 1) or col in (0, width - 1))
        and not (value in (1, 2, 3, 4) and len(tokens) == 1 and (row, col) == tokens[0][:2])
    ]
    if border_nonzero:
        errors.append(f"non-token border cells must be background: {border_nonzero[:6]}")

    motif = _motif_hits(grid)
    if not 5 <= len(motif) <= 9:
        errors.append(f"motif must contain 5..9 cells, found {len(motif)}")
    distinct_colors = {value for _, _, value in motif}
    if not 2 <= len(distinct_colors) <= 5:
        errors.append(f"motif must use 2..5 colors, found {len(distinct_colors)}")
    motif_cells = {(row, col) for row, col, _ in motif}
    if motif_cells and not _connected(motif_cells):
        errors.append("motif must be 4-connected")
    if motif:
        crop = _crop_from_hits(grid, motif)
        if len(crop) > 4 or len(crop[0]) > 4:
            errors.append("motif bounding box must fit within 4x4")
        if not _distinct_transform_outputs(crop):
            errors.append("motif must distinguish all four token transforms")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful generated/canonical inputs for this selected sampler."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid input: " + "; ".join(errors))
    row, col, token = _token_hits(grid)[0]
    height, width = len(grid), len(grid[0])
    corner = {
        (0, 0): "top_left",
        (0, width - 1): "top_right",
        (height - 1, width - 1): "bottom_right",
        (height - 1, 0): "bottom_left",
    }[(row, col)]
    motif = _motif_hits(grid)
    return {
        "grid_h": height,
        "grid_w": width,
        "token": token,
        "token_corner": corner,
        "motif_cells": len(motif),
        "motif_colors": len({value for _, _, value in motif}),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent pure-Python mirror for tests and declared rival scoring."""
    tokens = _token_hits(grid)
    if len(tokens) != 1:
        raise ValueError(f"expected exactly one transform token, found {len(tokens)}")
    crop = _crop_from_hits(grid, _motif_hits(grid))
    return _apply_transform(crop, tokens[0][2])


def _corner_encodes_transform(grid) -> list[list[int]]:
    """Rival: infer transform from canonical token corner, ignoring token color."""
    tokens = _token_hits(grid)
    if len(tokens) != 1:
        raise ValueError(f"expected exactly one transform token, found {len(tokens)}")
    row, col, _ = tokens[0]
    height, width = len(grid), len(grid[0])
    corner = {
        (0, 0): "top_left",
        (0, width - 1): "top_right",
        (height - 1, width - 1): "bottom_right",
        (height - 1, 0): "bottom_left",
    }.get((row, col))
    if corner is None:
        raise ValueError("token is not in a corner")
    return _apply_transform(_crop_from_hits(grid, _motif_hits(grid)), _CORNER_CODE_RIVAL[corner])


def _token_corner_independence(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _corner_encodes_transform(grid)


SEMANTIC_WITNESSES = {"token_corner_independence": _token_corner_independence}
SEMANTIC_RIVALS = {"corner_encodes_transform": _corner_encodes_transform}
WITNESS_RIVALS = {"token_corner_independence": ["corner_encodes_transform"]}
CANONICAL_SHORTCUTS = {"corner_encodes_transform": _corner_encodes_transform}
LESSON_COMPETITORS = {"corner_encodes_transform": _corner_encodes_transform}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared canonical-fit shortcut."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
