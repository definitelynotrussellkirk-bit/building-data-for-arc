"""Generator for ARC task 7fe59337a0b4 — rotate one motif around a marker.

The input contains one asymmetric, single-color motif and one color-9 marker on
an otherwise black square canvas.  The authoritative Racket rule crops the
motif, recenters the original immediately above the marker, then places 90°,
180°, and 270° clockwise rotations to the right, below, and left.  The marker
is retained at the center of the four-copy collage.

An eight-slot schedule alternates cardinal and diagonal source sectors around
the marker.  Every consecutive eight-example lesson covers all eight sectors,
contains two canonical L-triomino anchors, and includes six larger asymmetric
motifs.  This closes the previous diagonal-only distribution gap while making
single-query rotations refute the same executable shortcut rules.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7fe59337a0b4"
TASK_ID = "7fe59337a0b4"
VERSION = "3.0.0"
RULE_HASH = "e5504f0fdce0"

SUMMARY = (
    "Crop the sole nonzero, non-9 motif. On a fresh black canvas, place the "
    "original immediately above the color-9 marker, then its 90-degree "
    "clockwise, 180-degree, and 270-degree rotations to the right, below, "
    "and left; retain the marker."
)

EXAMPLES_NEEDED = 8
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "the canvas is square, 9..15 cells per side, with background color 0",
    "there is exactly one color-9 marker",
    "all other nonzero cells form one 4-connected single-color motif",
    "the motif has 3..5 cells, fits a 3x3 box, and has four distinct rotations",
    "the marker lies outside the motif bounding box",
    "all four output placements are in bounds and pairwise disjoint",
]

SCENE_PROFILES = (
    "canonical_north_l3",
    "southeast_varied",
    "east_varied",
    "canonical_northwest_l3",
    "south_varied",
    "northeast_varied",
    "west_varied",
    "southwest_varied",
)
SCHEDULE_PROFILES = SCENE_PROFILES
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

_CANONICAL_SHAPE = frozenset({(0, 0), (0, 1), (1, 1)})
_GENERAL_SHAPES: tuple[frozenset[tuple[int, int]], ...] = (
    frozenset({(0, 0), (0, 1), (1, 0)}),
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 1), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 0)}),
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
    frozenset({(0, 1), (1, 0), (1, 1), (1, 2)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)}),
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)}),
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}),
)
_PROFILE_SECTORS = {
    "canonical_north_l3": "north",
    "southeast_varied": "southeast",
    "east_varied": "east",
    "canonical_northwest_l3": "northwest",
    "south_varied": "south",
    "northeast_varied": "northeast",
    "west_varied": "west",
    "southwest_varied": "southwest",
}

_CARDINAL_SECTORS = frozenset({"north", "east", "south", "west"})
_DIAGONAL_SECTORS = frozenset(
    {"northwest", "northeast", "southeast", "southwest"}
)


AXES = {
    "canvas_size": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-aware 9..15",
        "valid": "9..15",
    },
    "motif_color": {
        "type": "int",
        "default": "keyed color draw excluding 0 and 9",
        "valid": "1..8",
    },
    "scene_profile": {
        "type": "str",
        "default": "eight-slot cardinal/diagonal shortcut-refuting schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Every consecutive eight samples contain all source-sector profiles."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")


def _normalize_cells(cells: set[tuple[int, int]] | frozenset[tuple[int, int]]):
    if not cells:
        return frozenset()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _shape_dims(cells: set[tuple[int, int]] | frozenset[tuple[int, int]]):
    normalized = _normalize_cells(cells)
    return (
        max(r for r, _ in normalized) + 1,
        max(c for _, c in normalized) + 1,
    )


def _rotate_cells_cw(cells: frozenset[tuple[int, int]]):
    normalized = _normalize_cells(cells)
    height, _ = _shape_dims(normalized)
    return _normalize_cells({(c, height - 1 - r) for r, c in normalized})


def _rotations(cells: frozenset[tuple[int, int]]):
    result = []
    current = _normalize_cells(cells)
    for _ in range(4):
        result.append(current)
        current = _rotate_cells_cw(current)
    return tuple(result)


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _coerce_grid(grid: Any) -> tuple[list[list[int]], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return [], ["every row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return [], ["grid must be nonempty and rectangular"]
    output: list[list[int]] = []
    for row in grid:
        out_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [], ["cells must be literal ARC integers 0..9"]
            out_row.append(value)
        output.append(out_row)
    return output, []


def _matrix_from_cells(cells: frozenset[tuple[int, int]], color: int):
    height, width = _shape_dims(cells)
    matrix = full_grid(height, width, 0)
    for row, col in cells:
        matrix[row][col] = color
    return matrix


def _rotate_matrix_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _paste_positions(shape: list[list[int]], top: int, left: int):
    return {
        (top + row, left + col)
        for row in range(len(shape))
        for col in range(len(shape[0]))
        if shape[row][col] != 0
    }


def _target_placements(
    shape: list[list[int]], marker: tuple[int, int]
) -> tuple[list[list[list[int]]], list[set[tuple[int, int]]]]:
    mr, mc = marker
    rotations = [shape]
    for _ in range(3):
        rotations.append(_rotate_matrix_cw(rotations[-1]))
    placements = [
        _paste_positions(rotations[0], mr - 1 - len(rotations[0]), mc - len(rotations[0][0]) // 2),
        _paste_positions(rotations[1], mr - len(rotations[1]) // 2, mc + 2),
        _paste_positions(rotations[2], mr + 2, mc - len(rotations[2][0]) // 2),
        _paste_positions(rotations[3], mr - len(rotations[3]) // 2, mc - 1 - len(rotations[3][0])),
    ]
    return rotations, placements


def _analyze(grid: Any) -> dict[str, Any]:
    original, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}
    height, width = len(original), len(original[0])
    if height != width:
        errors.append("canvas must be square")
    if not 9 <= height <= 15:
        errors.append(f"canvas side must be in 9..15, got {height}")

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] == 9
    ]
    if len(markers) != 1:
        errors.append(f"need exactly one color-9 marker, got {len(markers)}")
    marker = markers[0] if len(markers) == 1 else None

    motif_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] not in (0, 9)
    }
    motif_colors = {original[row][col] for row, col in motif_cells}
    if len(motif_colors) != 1:
        errors.append(f"motif must use exactly one non-9 color, got {sorted(motif_colors)}")
    motif_color = next(iter(motif_colors)) if len(motif_colors) == 1 else None
    if not 3 <= len(motif_cells) <= 5:
        errors.append(f"motif must contain 3..5 cells, got {len(motif_cells)}")
    if motif_cells and not _is_connected(motif_cells):
        errors.append("motif cells must be 4-connected")

    normalized = _normalize_cells(motif_cells)
    motif_height = motif_width = 0
    if normalized:
        motif_height, motif_width = _shape_dims(normalized)
        if motif_height > 3 or motif_width > 3:
            errors.append(
                f"motif bounding box must fit 3x3, got {motif_height}x{motif_width}"
            )
        if motif_height < 2 or motif_width < 2:
            errors.append("motif must span at least two rows and two columns")
        if len(set(_rotations(normalized))) != 4:
            errors.append("motif must have four distinct quarter-turn rotations")

    bbox = None
    if motif_cells:
        bbox = (
            min(row for row, _ in motif_cells),
            min(col for _, col in motif_cells),
            max(row for row, _ in motif_cells),
            max(col for _, col in motif_cells),
        )
    if marker is not None and bbox is not None:
        r0, c0, r1, c1 = bbox
        if r0 <= marker[0] <= r1 and c0 <= marker[1] <= c1:
            errors.append("marker must lie outside the motif bounding box")

    source_sector = None
    if marker is not None and bbox is not None:
        r0, c0, r1, c1 = bbox
        if r1 < marker[0] and c1 < marker[1]:
            source_sector = "northwest"
        elif r1 < marker[0] and c0 > marker[1]:
            source_sector = "northeast"
        elif r1 < marker[0]:
            source_sector = "north"
        elif r0 > marker[0] and c1 < marker[1]:
            source_sector = "southwest"
        elif r0 > marker[0] and c0 > marker[1]:
            source_sector = "southeast"
        elif r0 > marker[0]:
            source_sector = "south"
        elif c1 < marker[1]:
            source_sector = "west"
        elif c0 > marker[1]:
            source_sector = "east"

    profile = None
    if normalized == _CANONICAL_SHAPE:
        profile = {
            "north": "canonical_north_l3",
            "northwest": "canonical_northwest_l3",
        }.get(source_sector)
    elif normalized in _GENERAL_SHAPES:
        profile = {
            "southeast": "southeast_varied",
            "east": "east_varied",
            "south": "south_varied",
            "northeast": "northeast_varied",
            "west": "west_varied",
            "southwest": "southwest_varied",
        }.get(source_sector)

    placements: list[set[tuple[int, int]]] = []
    if marker is not None and motif_color is not None and normalized:
        shape = _matrix_from_cells(normalized, motif_color)
        _, placements = _target_placements(shape, marker)
        all_target: set[tuple[int, int]] = set()
        for index, cells in enumerate(placements):
            if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
                errors.append(f"rotated output placement {index} would be clipped")
            if marker in cells:
                errors.append(f"rotated output placement {index} overlaps the marker")
            overlap = all_target & cells
            if overlap:
                errors.append(f"rotated output placements overlap at {sorted(overlap)[:3]}")
            all_target.update(cells)

    return {
        "errors": errors,
        "grid": original,
        "height": height,
        "width": width,
        "marker": marker,
        "motif_cells": motif_cells,
        "motif_color": motif_color,
        "normalized_shape": normalized,
        "bbox": bbox,
        "source_sector": source_sector,
        # Compatibility alias retained for evidence/tools built against v2.
        "source_zone": source_sector,
        "scene_profile": profile,
        "placements": placements,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the authority-safe input grammar; canonical inputs are accepted."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons: list[str] = []
    if analysis["height"] not in (9, 11):
        reasons.append("canonical canvases are 9x9 or 11x11")
    center = (analysis["height"] // 2, analysis["width"] // 2)
    if analysis["marker"] != center:
        reasons.append("canonical marker is at the canvas center")
    if analysis["normalized_shape"] != _CANONICAL_SHAPE:
        reasons.append("canonical motif is the oriented three-cell L")
    if analysis["bbox"] is not None and analysis["bbox"][2] >= analysis["marker"][0]:
        reasons.append("canonical motif lies wholly above the marker")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    observed: dict[str, int | str] = {
        "canvas_size": analysis["height"],
        "motif_color": analysis["motif_color"],
    }
    if analysis["scene_profile"] is not None:
        observed["scene_profile"] = analysis["scene_profile"]
    return observed


def _default_canvas_size(seed: int, sample_index: int, difficulty: Any, profile: str) -> int:
    if profile in {"canonical_north_l3", "canonical_northwest_l3"}:
        return (9, 11)[(int(sample_index) // len(SCENE_PROFILES)) % 2]
    options = {
        "easy": (9, 10, 11),
        "medium": (11, 12, 13),
        "hard": (13, 14, 15),
        None: tuple(range(9, 16)),
    }[difficulty]
    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|canvas_default", VERSION)
    return rng.choice(options)


def _source_top_left(
    size: int,
    shape: frozenset[tuple[int, int]],
    sector: str,
    rng,
) -> tuple[int, int]:
    shape_h, shape_w = _shape_dims(shape)
    center = size // 2
    overlap_row = (
        max(0, center - shape_h + 1),
        min(center, size - shape_h),
    )
    overlap_col = (
        max(0, center - shape_w + 1),
        min(center, size - shape_w),
    )
    if sector == "northwest":
        row_range = (0, center - shape_h)
        col_range = (0, center - shape_w)
    elif sector == "north":
        row_range = (0, center - shape_h)
        col_range = overlap_col
    elif sector == "northeast":
        row_range = (0, center - shape_h)
        col_range = (center + 1, size - shape_w)
    elif sector == "east":
        row_range = overlap_row
        col_range = (center + 1, size - shape_w)
    elif sector == "southeast":
        row_range = (center + 1, size - shape_h)
        col_range = (center + 1, size - shape_w)
    elif sector == "south":
        row_range = (center + 1, size - shape_h)
        col_range = overlap_col
    elif sector == "southwest":
        row_range = (center + 1, size - shape_h)
        col_range = (0, center - shape_w)
    elif sector == "west":
        row_range = overlap_row
        col_range = (0, center - shape_w)
    else:
        raise ValueError(f"unknown source sector: {sector}")
    if row_range[0] > row_range[1] or col_range[0] > col_range[1]:
        raise ValueError(
            f"profile {sector} does not fit canvas {size} with shape {shape_h}x{shape_w}"
        )
    return rng.randint(*row_range), rng.randint(*col_range)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket rule owns output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_overrides(overrides)

    effective = dict(overrides)
    effective.setdefault("scene_profile", schedule_profile(seed, sample_index, difficulty))
    effective.setdefault(
        "canvas_size",
        _default_canvas_size(
            seed, sample_index, difficulty, str(effective["scene_profile"])
        ),
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    size = ctx.draw_int("canvas_size", 9, 15)
    motif_color = ctx.draw_color("motif_color", exclude={0, 9})
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    if profile in {"canonical_north_l3", "canonical_northwest_l3"}:
        shape = _CANONICAL_SHAPE
    else:
        shape = ctx.draw_rng("motif_variant").choice(_GENERAL_SHAPES)
    sector = _PROFILE_SECTORS[profile]
    top, left = _source_top_left(
        size, shape, sector, ctx.draw_rng("source_position")
    )

    grid = full_grid(size, size, 0)
    marker = (size // 2, size // 2)
    grid[marker[0]][marker[1]] = 9
    for row, col in shape:
        grid[top + row][left + col] = motif_color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator defect: {errors}")
    return grid


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror used only for tests and semantic competitors."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(f"invalid task input: {analysis['errors']}")
    shape = _matrix_from_cells(analysis["normalized_shape"], analysis["motif_color"])
    rotations, placements = _target_placements(shape, analysis["marker"])
    output = full_grid(analysis["height"], analysis["width"], 0)
    for rotation, cells in zip(rotations, placements):
        values = [
            rotation[row][col]
            for row in range(len(rotation))
            for col in range(len(rotation[0]))
            if rotation[row][col] != 0
        ]
        for (row, col), value in zip(sorted(cells), values):
            output[row][col] = value
    mr, mc = analysis["marker"]
    output[mr][mc] = 9
    return output


def _paste_matrix(
    output: list[list[int]], shape: list[list[int]], top: int, left: int
) -> None:
    for row in range(len(shape)):
        for col in range(len(shape[0])):
            value = shape[row][col]
            if value:
                rr, cc = top + row, left + col
                if 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                    output[rr][cc] = value


def _rival_all_unrotated(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    shape = _matrix_from_cells(analysis["normalized_shape"], analysis["motif_color"])
    mr, mc = analysis["marker"]
    output = full_grid(analysis["height"], analysis["width"], 0)
    positions = (
        (mr - 1 - len(shape), mc - len(shape[0]) // 2),
        (mr - len(shape) // 2, mc + 2),
        (mr + 2, mc - len(shape[0]) // 2),
        (mr - len(shape) // 2, mc - 1 - len(shape[0])),
    )
    for top, left in positions:
        _paste_matrix(output, shape, top, left)
    output[mr][mc] = 9
    return output


def _rival_reverse_rotation_order(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    shape = _matrix_from_cells(analysis["normalized_shape"], analysis["motif_color"])
    cw = _rotate_matrix_cw(shape)
    r180 = _rotate_matrix_cw(cw)
    ccw = _rotate_matrix_cw(r180)
    mr, mc = analysis["marker"]
    output = full_grid(analysis["height"], analysis["width"], 0)
    wrong = [shape, ccw, r180, cw]
    placements = (
        (mr - 1 - len(shape), mc - len(shape[0]) // 2),
        (mr - len(ccw) // 2, mc + 2),
        (mr + 2, mc - len(r180[0]) // 2),
        (mr - len(cw) // 2, mc - 1 - len(cw[0])),
    )
    for part, (top, left) in zip(wrong, placements):
        _paste_matrix(output, part, top, left)
    output[mr][mc] = 9
    return output


def _rival_preserve_source_position(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    canonical = rule_mirror(grid)
    # Replace the standardized north copy with the motif at its original input
    # position while leaving the other three rotated copies untouched.
    shape = _matrix_from_cells(analysis["normalized_shape"], analysis["motif_color"])
    north = _target_placements(shape, analysis["marker"])[1][0]
    for row, col in north:
        canonical[row][col] = 0
    for row, col in analysis["motif_cells"]:
        canonical[row][col] = analysis["motif_color"]
    mr, mc = analysis["marker"]
    canonical[mr][mc] = 9
    return canonical


def _rival_diagonal_source_only(grid: Any) -> list[list[int]]:
    """Shortcut: learn the rule only for the diagonal source distribution.

    Version 2 generated only diagonal source positions, so this executable
    hypothesis agreed with every generated example while failing canonical
    north-aligned inputs.  Cardinal examples now force it to expose itself by
    repeating the unrotated motif four times.
    """
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    if analysis["source_sector"] in _DIAGONAL_SECTORS:
        return rule_mirror(grid)
    return _rival_all_unrotated(grid)


def _is_profile(name: str) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["scene_profile"] == name

    return predicate


def _source_displaced(grid: Any) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    shape = _matrix_from_cells(analysis["normalized_shape"], analysis["motif_color"])
    north = _target_placements(shape, analysis["marker"])[1][0]
    return analysis["motif_cells"] != north


def _source_in(sectors: frozenset[str]) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["source_sector"] in sectors

    return predicate


SEMANTIC_WITNESSES = {
    **{name: _is_profile(name) for name in SCENE_PROFILES},
    "strict_canonical_anchor": lambda grid: strict_canonical_like(grid) == [],
    "source_displaced_from_standard_north": _source_displaced,
    "cardinal_source": _source_in(_CARDINAL_SECTORS),
    "diagonal_source": _source_in(_DIAGONAL_SECTORS),
}
SEMANTIC_RIVALS = {
    "all_four_unrotated": _rival_all_unrotated,
    "reverse_quarter_turn_order": _rival_reverse_rotation_order,
    "preserve_source_position": _rival_preserve_source_position,
    "diagonal_source_only": _rival_diagonal_source_only,
}
WITNESS_RIVALS = {
    **{name: ["all_four_unrotated", "reverse_quarter_turn_order"] for name in SCENE_PROFILES},
    "strict_canonical_anchor": ["all_four_unrotated"],
    "source_displaced_from_standard_north": ["preserve_source_position"],
    "cardinal_source": ["diagonal_source_only"],
    "diagonal_source": ["all_four_unrotated", "reverse_quarter_turn_order"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Require broad sector coverage and kill every named competitor.

    A nine-pair rolling bundle contains one repeated profile.  Holding out any
    one pair therefore leaves seven or eight profiles, which is the rotation-
    safe coverage floor used here instead of requiring every exact profile.
    """
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    profiles: set[str] = set()
    sectors: set[str] = set()
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis["errors"] or analysis["scene_profile"] is None:
            reasons.append(f"demo {index} input is outside the scheduled teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the task rule")
        profiles.add(analysis["scene_profile"])
        sectors.add(analysis["source_sector"])
        valid_demos.append(demo)

    profile_floor = len(SCENE_PROFILES) - 1
    if len(profiles) < profile_floor:
        reasons.append(
            "demonstrations need at least "
            f"{profile_floor} distinct scene profiles, got {len(profiles)}"
        )
    if not sectors.intersection(_CARDINAL_SECTORS):
        reasons.append("demonstrations need at least one cardinal source sector")
    if not sectors.intersection(_DIAGONAL_SECTORS):
        reasons.append("demonstrations need at least one diagonal source sector")
    if len(valid_demos) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    elif self_check(query["input"]):
        reasons.append("query input is outside the task grammar")
    return reasons
