"""Generator for d336f5fb2da4: transform a source and stamp along a vector.

The canonical rule reads an arbitrary blue source shape, a singleton control
(4 identity, 6 rotate clockwise, 7 reflect top/bottom), and singleton markers
2 and 3.  It normalizes the transformed source and repeatedly stamps it in cyan
from marker 2 along the 2->3 vector until the next complete stamp is out of
bounds.

The reviewed sampler deliberately schedules multiple source morphologies,
vectors, and controls.  This closes the old lesson shortcut that hardcoded the
three-cell L and horizontal stride three while still preserving the selected
canonical Racket authority.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d336f5fb2da4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "722859cc9e88"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A zero-background grid contains an arbitrary connected blue source shape, "
    "one control singleton (4 identity, 6 clockwise rotation, 7 top/bottom "
    "reflection), and red/green singleton markers defining a nonzero vector. "
    "Normalize the transformed source and stamp it in cyan from red along the "
    "red-to-green vector until the next complete copy leaves the grid."
)

SOURCE_SHAPES = {
    "l3": ((0, 0), (0, 1), (1, 0)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "zig4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "asym5": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    "hook5": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    "stair6": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
}
SOURCE_PROFILES = tuple(SOURCE_SHAPES)
VECTOR_DELTAS = {
    "right3": (0, 3),
    "down3": (3, 0),
    "left3": (0, -3),
    "up3": (-3, 0),
    "diag_down_right": (3, 3),
    "diag_down_left": (3, -3),
    "diag_up_right": (-3, 3),
    "diag_up_left": (-3, -3),
}
VECTOR_PROFILES = tuple(VECTOR_DELTAS)
CONTROL_COLORS = (4, 6, 7)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

INVARIANTS = [
    "one nonempty color-1 source shape is present",
    "exactly one singleton control is 4, 6, or 7",
    "colors 2 and 3 are singleton markers defining a nonzero vector",
    "at least two complete transformed stamps fit from marker 2",
    "scheduled lessons vary source geometry, vector, and control",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty schedule", "valid": "8..30"},
    "grid_w": {"type": "int", "default": "difficulty schedule", "valid": "8..30"},
    "control_color": {"type": "int", "default": "scheduled 4|6|7", "valid": "4|6|7"},
    "source_profile": {
        "type": "str",
        "default": "scheduled",
        "valid": "l3|t4|zig4|asym5|hook5|stair6",
    },
    "vector_profile": {
        "type": "str",
        "default": "scheduled",
        "valid": "right3|down3|left3|up3|diag_down_right|diag_down_left|diag_up_right|diag_up_left",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    return _normalize((c, -r) for r, c in normalized)


def _rotate_ccw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    return _normalize((-c, r) for r, c in normalized)


def _flip_rows(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    rmax = max(r for r, _ in normalized)
    return _normalize((rmax - r, c) for r, c in normalized)


def _transformed(
    source: Iterable[tuple[int, int]],
    control: int,
    *,
    magenta_rotation: str = "cw",
) -> tuple[tuple[int, int], ...]:
    source = _normalize(source)
    if control == 6:
        if magenta_rotation == "cw":
            return _rotate_cw(source)
        if magenta_rotation == "ccw":
            return _rotate_ccw(source)
        raise ValueError("magenta_rotation must be 'cw' or 'ccw'")
    if control == 7:
        return _flip_rows(source)
    if control == 4:
        return source
    raise ValueError(f"unsupported control color {control}")


def _stamp_count(
    height: int,
    width: int,
    anchor: tuple[int, int],
    delta: tuple[int, int],
    cells: Iterable[tuple[int, int]],
) -> int:
    count = 0
    ar, ac = anchor
    dr, dc = delta
    while True:
        placed = [(ar + r, ac + c) for r, c in cells]
        if not all(0 <= r < height and 0 <= c < width for r, c in placed):
            return count
        count += 1
        ar += dr
        ac += dc


def _analyze_grid(grid: list[list[int]]) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC colors 0..9")
    cells_by_color = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in range(10)
    }
    source = tuple(cells_by_color[1])
    controls = [(color, cells_by_color[color][0]) for color in CONTROL_COLORS if len(cells_by_color[color]) == 1]
    if len(source) < 2:
        raise ValueError("expected at least two source cells")
    if len(controls) != 1 or any(len(cells_by_color[color]) > 1 for color in CONTROL_COLORS):
        raise ValueError("expected exactly one singleton control from 4, 6, 7")
    if len(cells_by_color[2]) != 1 or len(cells_by_color[3]) != 1:
        raise ValueError("markers 2 and 3 must each be singleton")
    allowed = {0, 1, 2, 3, 4, 6, 7}
    unexpected = sorted({value for row in grid for value in row} - allowed)
    if unexpected:
        raise ValueError(f"unexpected input colors {unexpected}")
    start = cells_by_color[2][0]
    nxt = cells_by_color[3][0]
    delta = (nxt[0] - start[0], nxt[1] - start[1])
    if delta == (0, 0):
        raise ValueError("marker vector must be nonzero")
    control = controls[0][0]
    return {
        "source": source,
        "normalized_source": _normalize(source),
        "control": control,
        "control_pos": controls[0][1],
        "start": start,
        "next": nxt,
        "delta": delta,
        "transformed": _transformed(source, control),
    }


def _dimension(ctx, overrides, name: str, band: tuple[int, int]) -> int:
    if name in overrides and overrides[name] is not None:
        return _exact_int(name, overrides[name], 8, 30)
    return ctx.draw_int(name, *band)


def _profile(overrides, name: str, options: tuple[str, ...], index: int) -> str:
    value = overrides.get(name)
    if value is None:
        return options[index % len(options)]
    if type(value) is not str or value not in options:
        raise ValueError(f"{name} must be one of {options}")
    return value


def _construct_grid(
    *,
    height: int,
    width: int,
    source_profile: str,
    vector_profile: str,
    control_color: int,
    rng,
    prefer_long: bool,
) -> list[list[int]]:
    source_shape = SOURCE_SHAPES[source_profile]
    delta = VECTOR_DELTAS[vector_profile]
    transformed = _transformed(source_shape, control_color)

    anchors: list[tuple[int, tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            count = _stamp_count(height, width, (r, c), delta, transformed)
            if count >= 2:
                anchors.append((count, (r, c)))
    if not anchors:
        raise ValueError(
            f"grid {height}x{width} cannot fit two {source_profile} stamps along {vector_profile}"
        )
    if prefer_long:
        best = max(count for count, _ in anchors)
        pool = [anchor for count, anchor in anchors if count >= max(2, best - 1)]
    else:
        pool = [anchor for count, anchor in anchors if count >= 3] or [anchor for _, anchor in anchors]
    start = rng.choice(pool)
    nxt = (start[0] + delta[0], start[1] + delta[1])
    reserved = {start, nxt}

    sh = max(r for r, _ in source_shape) + 1
    sw = max(c for _, c in source_shape) + 1
    source_positions = []
    for top in range(height - sh + 1):
        for left in range(width - sw + 1):
            cells = {(top + r, left + c) for r, c in source_shape}
            if cells.isdisjoint(reserved):
                # Keep the source visually separate from both markers.
                if all(max(abs(r - rr), abs(c - cc)) > 1 for r, c in cells for rr, cc in reserved):
                    source_positions.append((top, left))
    if not source_positions:
        raise ValueError("no legal source placement separate from markers")
    top, left = rng.choice(source_positions)
    source_cells = {(top + r, left + c) for r, c in source_shape}
    reserved |= source_cells

    control_positions = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in reserved
        and all(max(abs(r - rr), abs(c - cc)) > 1 for rr, cc in reserved)
    ]
    if not control_positions:
        control_positions = [
            (r, c) for r in range(height) for c in range(width) if (r, c) not in reserved
        ]
    if not control_positions:
        raise ValueError("no legal control position")
    control_pos = rng.choice(control_positions)

    grid = full_grid(height, width, 0)
    for r, c in source_cells:
        grid[r][c] = 1
    grid[start[0]][start[1]] = 2
    grid[nxt[0]][nxt[1]] = 3
    grid[control_pos[0]][control_pos[1]] = control_color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")

    bands = {
        None: ((10, 20), (12, 22)),
        "easy": ((8, 13), (10, 16)),
        "medium": ((14, 22), (14, 24)),
        "hard": ((22, 30), (22, 30)),
    }
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _dimension(ctx, overrides, "grid_h", bands[difficulty][0])
    width = _dimension(ctx, overrides, "grid_w", bands[difficulty][1])
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    source_profile = _profile(
        overrides,
        "source_profile",
        SOURCE_PROFILES,
        sample_index + offset,
    )
    vector_profile = _profile(
        overrides,
        "vector_profile",
        VECTOR_PROFILES,
        sample_index * 3 + offset,
    )
    control = overrides.get("control_color")
    if control is None:
        control = CONTROL_COLORS[(sample_index + offset) % len(CONTROL_COLORS)]
    if type(control) is not int or control not in CONTROL_COLORS:
        raise ValueError("control_color must be exactly one of 4, 6, 7")

    grid = _construct_grid(
        height=height,
        width=width,
        source_profile=source_profile,
        vector_profile=vector_profile,
        control_color=control,
        rng=ctx.draw_rng("layout"),
        prefer_long=difficulty == "hard" or max(height, width) == 30,
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def observe_overrides(grid):
    scene = _analyze_grid(grid)
    source_profile = next(
        (name for name, cells in SOURCE_SHAPES.items() if _normalize(cells) == scene["normalized_source"]),
        None,
    )
    vector_profile = next(
        (name for name, delta in VECTOR_DELTAS.items() if delta == scene["delta"]),
        None,
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "control_color": scene["control"],
        "source_profile": source_profile,
        "vector_profile": vector_profile,
    }


def rule_mirror(grid, *, magenta_rotation: str = "cw"):
    """Input-pure reconstruction of the selected canonical transformation."""
    scene = _analyze_grid(grid)
    cells = _transformed(
        scene["source"], scene["control"], magenta_rotation=magenta_rotation
    )
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    ar, ac = scene["start"]
    dr, dc = scene["delta"]
    while True:
        placed = [(ar + r, ac + c) for r, c in cells]
        if not all(0 <= r < height and 0 <= c < width for r, c in placed):
            return output
        for r, c in placed:
            output[r][c] = 8
        ar += dr
        ac += dc


def _rival_identity_control(grid):
    scene = _analyze_grid(grid)
    original = scene["control"]
    rewritten = [row[:] for row in grid]
    r, c = scene["control_pos"]
    rewritten[r][c] = 4
    try:
        return rule_mirror(rewritten)
    finally:
        rewritten[r][c] = original


def _rival_hardcoded_l_horizontal(grid):
    scene = _analyze_grid(grid)
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    cells = _transformed(SOURCE_SHAPES["l3"], scene["control"])
    ar, ac = scene["start"]
    while True:
        placed = [(ar + r, ac + c) for r, c in cells]
        if not all(0 <= r < height and 0 <= c < width for r, c in placed):
            return output
        for r, c in placed:
            output[r][c] = 8
        ac += 3


def _rival_start_at_green(grid):
    """Common shortcut: treat the green marker as the first stamp anchor."""
    scene = _analyze_grid(grid)
    cells = _transformed(scene["source"], scene["control"])
    out = full_grid(len(grid), len(grid[0]), 0)
    ar, ac = scene["next"]
    dr, dc = scene["delta"]
    while True:
        placed = [(ar + r, ac + c) for r, c in cells]
        if not all(0 <= r < len(grid) and 0 <= c < len(grid[0]) for r, c in placed):
            return out
        for r, c in placed:
            out[r][c] = 8
        ar += dr
        ac += dc


LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_control": _rival_identity_control,
    "hardcoded_l_horizontal": _rival_hardcoded_l_horizontal,
    "start_at_green": _rival_start_at_green,
}
CANONICAL_SHORTCUTS = {"hardcoded_l_horizontal": _rival_hardcoded_l_horizontal}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            if rule_mirror(pair["input"]) != pair["output"]:
                reasons.append(f"demo {index} does not match the canonical stamp rule")
        except Exception as exc:
            reasons.append(f"demo {index} is outside the reviewed domain: {exc}")
    try:
        query_input = query["input"]
        query_output = query["output"]
    except Exception as exc:
        return reasons + [f"query is malformed: {exc}"]
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query_input) != query_output:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty not in _VALID_DIFFICULTIES:
        return [f"invalid difficulty {difficulty!r}"]
    try:
        scene = _analyze_grid(grid)
    except Exception as exc:
        return [str(exc)]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 8 <= height <= 30 or not 8 <= width <= 30:
        errors.append(f"grid dimensions {height}x{width} outside reviewed 8..30 bounds")
    cells = _transformed(scene["source"], scene["control"])
    copies = _stamp_count(height, width, scene["start"], scene["delta"], cells)
    if copies < 2:
        errors.append(f"expected at least two complete stamps, found {copies}")
    return errors
