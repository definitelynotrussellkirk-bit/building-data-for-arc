"""Generator for H67 — seed-fill wall compartments.

The outer color-7 frame and an internal color-5 wall network partition the
canvas into rectangular rooms.  Every seeded room contains exactly one colored
cell; the rule fills that room's zeros with the seed color and leaves a
seedless room unchanged.

The public controls are deliberately small and observable from the returned
input: room-count profile, wall-network orientation, and whether one room is
seedless.  Geometry, seed positions, and seed colors remain keyed random draws.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ce0b0e843251"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ecbd69f623c3"

SUMMARY = (
    "A color-7 outer frame encloses a color-5 guillotine wall network. One or "
    "two spanning backbone walls form two or three strips; compartment-local "
    "perpendicular branches split selected strips, producing 3-6 rectangular "
    "rooms and genuine T-junctions. Every seeded room has exactly one distinct "
    "non-{0,5,7} seed; either all rooms are seeded or exactly one is seedless. "
    "Fill each seeded room's zeros with its seed color, preserving walls, "
    "seeds, and the seedless room."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the complete outer border is color 7 and no interior cell is color 7",
    "color-5 backbones and strip-local branches partition the interior into 3-6 rooms",
    "every room contains zero or one seed cell, and seed colors are globally distinct",
    "either every room is seeded or exactly one room is seedless",
    "at least two seeded rooms remain, so walls and per-room color choice are both necessary",
]

LAYOUT_PROFILES = ("three_room", "four_room", "five_room", "six_room")
ORIENTATIONS = ("vertical", "horizontal")
SEED_COVERAGES = ("all_seeded", "one_seedless")
SEED_COLORS = (1, 2, 3, 4, 6, 8, 9)

# Base dimensions are for the vertical-backbone form. Horizontal instances are
# exact transposes, making the orientation recoverable without hidden metadata.
_PROFILE_SPECS = {
    "three_room": {"height": 9, "width": 11, "strips": 2, "splits": 1},
    "four_room": {"height": 10, "width": 11, "strips": 2, "splits": 2},
    "five_room": {"height": 9, "width": 12, "strips": 3, "splits": 2},
    "six_room": {"height": 10, "width": 12, "strips": 3, "splits": 3},
}
_PROFILE_BY_BASE_SHAPE_AND_ROOMS = {
    ((spec["height"], spec["width"]), spec["strips"] + spec["splits"]): name
    for name, spec in _PROFILE_SPECS.items()
}

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "uniform keyed draw",
        "valid": "|".join(LAYOUT_PROFILES),
    },
    "orientation": {
        "type": "str",
        "default": "uniform keyed draw",
        "valid": "|".join(ORIENTATIONS),
    },
    "seed_coverage": {
        "type": "str",
        "default": "uniform keyed draw",
        "valid": "|".join(SEED_COVERAGES),
    },
}

_CANONICAL_SIGNATURES = {
    # (height, width, palette size, rooms, seeded rooms)
    (9, 11, 6, 3, 3),
    (9, 12, 7, 5, 4),
    (10, 12, 8, 6, 5),
}


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))


def _open_widths(interior_width: int, n_strips: int, rng) -> list[int]:
    """Positive room widths with at least two open cells per strip."""
    open_total = interior_width - (n_strips - 1)
    if open_total < 2 * n_strips:
        raise ValueError("profile is too narrow for the requested strips")
    widths = [2] * n_strips
    for _ in range(open_total - 2 * n_strips):
        widths[rng.randrange(n_strips)] += 1
    rng.shuffle(widths)
    return widths


def _room_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Four-connected components after treating colors 5 and 7 as walls."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    rooms: list[list[tuple[int, int]]] = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] in (5, 7):
                continue
            seen.add((sr, sc))
            stack = [(sr, sc)]
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] not in (5, 7)
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rooms.append(cells)
    rooms.sort(key=lambda cells: min(cells))
    return rooms


def _build_vertical(profile: str, rng, difficulty: str) -> list[list[int]]:
    spec = _PROFILE_SPECS[profile]
    h, w = spec["height"], spec["width"]
    grid = full_grid(h, w, 0)

    for c in range(w):
        grid[0][c] = 7
        grid[h - 1][c] = 7
    for r in range(h):
        grid[r][0] = 7
        grid[r][w - 1] = 7

    widths = _open_widths(w - 2, spec["strips"], rng)
    boundaries = [0]
    cursor = 0
    for width in widths[:-1]:
        cursor += width + 1
        boundaries.append(cursor)
        for r in range(1, h - 1):
            grid[r][cursor] = 5
    boundaries.append(w - 1)

    split_strips = sorted(rng.sample(range(spec["strips"]), spec["splits"]))
    candidate_rows = list(range(2, h - 2))
    # Distinct branch rows prevent the branches from accidentally joining into
    # a second spanning backbone, so orientation remains directly observable.
    split_rows = rng.sample(candidate_rows, spec["splits"])
    if difficulty == "easy":
        split_rows.sort(key=lambda row: (abs(row - (h - 1) / 2), row))
    else:
        rng.shuffle(split_rows)

    for strip, row in zip(split_strips, split_rows):
        left, right = boundaries[strip], boundaries[strip + 1]
        for c in range(left + 1, right):
            grid[row][c] = 5

    return grid


def _seed_cell(room: list[tuple[int, int]], rng, difficulty: str) -> tuple[int, int]:
    if difficulty == "easy":
        mean_r = sum(r for r, _ in room) / len(room)
        mean_c = sum(c for _, c in room) / len(room)
        ranked = sorted(room, key=lambda p: (abs(p[0] - mean_r) + abs(p[1] - mean_c), p))
        return rng.choice(ranked[: min(3, len(ranked))])
    if difficulty == "medium":
        room_set = set(room)
        interior = [
            (r, c)
            for r, c in room
            if all((r + dr, c + dc) in room_set for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        ]
        # Prefer an isolated marker when the room is thick enough. Thin rooms
        # remain legal and keep canonical wall-adjacent seed cases reachable.
        return rng.choice(interior or room)
    if difficulty == "hard":
        # Edge-biased seeds prevent a center-marker shortcut while remaining
        # uniformly lawful under the room-fill rule.
        min_r = min(r for r, _ in room)
        max_r = max(r for r, _ in room)
        min_c = min(c for _, c in room)
        max_c = max(c for _, c in room)
        edge = [
            p
            for p in room
            if p[0] in (min_r, max_r) or p[1] in (min_c, max_c)
        ]
        return rng.choice(edge)
    return rng.choice(room)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("layout_profile", LAYOUT_PROFILES)
    orientation = ctx.draw_choice("orientation", ORIENTATIONS)
    coverage = ctx.draw_choice("seed_coverage", SEED_COVERAGES)
    rng = ctx.draw_rng("geometry")

    grid = _build_vertical(profile, rng, band)
    rooms = _room_components(grid)
    expected_rooms = _PROFILE_SPECS[profile]["strips"] + _PROFILE_SPECS[profile]["splits"]
    if len(rooms) != expected_rooms:
        raise AssertionError(f"constructed {len(rooms)} rooms, expected {expected_rooms}")

    seedless_index = None
    if coverage == "one_seedless":
        seedless_index = rng.randrange(len(rooms))
    seeded_rooms = [room for index, room in enumerate(rooms) if index != seedless_index]
    colors = rng.sample(SEED_COLORS, len(seeded_rooms))
    for room, color in zip(seeded_rooms, colors):
        r, c = _seed_cell(room, rng, band)
        grid[r][c] = color

    if orientation == "horizontal":
        grid = _transpose(grid)

    findings = self_check(grid)
    if findings:
        raise AssertionError("internal generator defect: " + "; ".join(findings))
    return grid


def _vertical_wall_structure(grid: list[list[int]]) -> tuple[dict[str, Any] | None, list[str]]:
    """Recognize the vertical-backbone grammar on an already basic-valid grid."""
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    backbones = [
        c
        for c in range(1, w - 1)
        if all(grid[r][c] == 5 for r in range(1, h - 1))
    ]
    if len(backbones) not in (1, 2):
        return None, [f"expected one or two spanning vertical color-5 backbones, got {len(backbones)}"]

    boundaries = [0, *backbones, w - 1]
    branch_rows: list[tuple[int, int]] = []
    for strip, (left, right) in enumerate(zip(boundaries, boundaries[1:])):
        if right - left - 1 < 2:
            errors.append(f"strip {strip} has fewer than two open columns")
            continue
        rows_here = []
        for r in range(1, h - 1):
            values = [grid[r][c] for c in range(left + 1, right)]
            has_wall = any(value == 5 for value in values)
            if has_wall and not all(value == 5 for value in values):
                errors.append(f"partial branch inside strip {strip} at row {r}")
            if has_wall:
                rows_here.append(r)
        if len(rows_here) > 1:
            errors.append(f"strip {strip} has more than one branch wall: {rows_here}")
        for row in rows_here:
            if not (2 <= row <= h - 3):
                errors.append(f"branch row {row} leaves an empty-height room")
            branch_rows.append((strip, row))

    allowed = set(backbones)
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 5 or c in allowed:
                continue
            strip = next(
                (i for i, (left, right) in enumerate(zip(boundaries, boundaries[1:])) if left < c < right),
                None,
            )
            if strip is None or (strip, r) not in branch_rows:
                errors.append(f"stray color-5 wall cell at {(r, c)}")

    if not branch_rows:
        errors.append("at least one compartment-local branch wall is required")
    rows_only = [row for _, row in branch_rows]
    if len(rows_only) != len(set(rows_only)):
        errors.append("branch rows align into an ambiguous second backbone")

    if errors:
        return None, errors
    return {
        "backbones": backbones,
        "boundaries": boundaries,
        "branches": branch_rows,
        "strips": len(boundaries) - 1,
        "expected_rooms": len(boundaries) - 1 + len(branch_rows),
    }, []


def _analyze(grid: list[list[int]]) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"errors": errors}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid must be a non-empty list of rows")
        return result
    h, w = len(grid), len(grid[0])
    result.update({"height": h, "width": w})
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return result
    if not (9 <= h <= 12 and 9 <= w <= 12):
        errors.append(f"grid dimensions must both be in 9..12, got {h}x{w}")

    border = [*grid[0], *grid[-1], *(row[0] for row in grid[1:-1]), *(row[-1] for row in grid[1:-1])]
    if any(value != 7 for value in border):
        errors.append("outer border must be entirely color 7")
    if any(grid[r][c] == 7 for r in range(1, h - 1) for c in range(1, w - 1)):
        errors.append("color 7 may occur only on the outer border")
    if errors:
        return result

    vertical, vertical_errors = _vertical_wall_structure(grid)
    transposed = _transpose(grid)
    horizontal_as_vertical, horizontal_errors = _vertical_wall_structure(transposed)
    candidates = []
    if vertical is not None:
        candidates.append(("vertical", vertical))
    if horizontal_as_vertical is not None:
        candidates.append(("horizontal", horizontal_as_vertical))
    if len(candidates) != 1:
        if not candidates:
            errors.append(
                "wall network matches neither orientation: vertical=("
                + "; ".join(vertical_errors[:3])
                + "), horizontal=("
                + "; ".join(horizontal_errors[:3])
                + ")"
            )
        else:
            errors.append("wall network has both spanning orientations; orientation is ambiguous")
        return result

    orientation, structure = candidates[0]
    rooms = _room_components(grid)
    if len(rooms) != structure["expected_rooms"]:
        errors.append(
            f"wall topology predicts {structure['expected_rooms']} rooms, found {len(rooms)}"
        )

    seed_colors: list[int] = []
    room_records = []
    for index, room in enumerate(rooms):
        seeds = [(r, c, grid[r][c]) for r, c in room if grid[r][c] not in (0, 5, 7)]
        zeros = sum(grid[r][c] == 0 for r, c in room)
        if len(room) < 2:
            errors.append(f"room {index} has only {len(room)} open cell")
        if len(seeds) > 1:
            errors.append(f"room {index} contains {len(seeds)} seed cells; expected at most one")
        if seeds:
            seed_colors.append(seeds[0][2])
            if zeros < 1:
                errors.append(f"seeded room {index} has no zero cell to fill")
        room_records.append({"cells": room, "seeds": seeds, "zeros": zeros})

    if len(seed_colors) != len(set(seed_colors)):
        errors.append("seed colors must be distinct across rooms")
    seedless = len(rooms) - len(seed_colors)
    if seedless not in (0, 1):
        errors.append(f"expected zero or one seedless room, found {seedless}")
    if len(seed_colors) < 2:
        errors.append("at least two seeded rooms are required")

    result.update(
        {
            "orientation": orientation,
            "structure": structure,
            "rooms": rooms,
            "room_records": room_records,
            "room_count": len(rooms),
            "seed_colors": seed_colors,
            "seeded_rooms": len(seed_colors),
            "seedless_rooms": seedless,
            "palette": sorted({value for row in grid for value in row}),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    signature = (
        analysis["height"],
        analysis["width"],
        len(analysis["palette"]),
        analysis["room_count"],
        analysis["seeded_rooms"],
    )
    errors = []
    if analysis["orientation"] != "vertical":
        errors.append("canonical inputs use vertical spanning backbones")
    if signature not in _CANONICAL_SIGNATURES:
        errors.append(f"canonical linked signature not matched: {signature!r}")
    return errors


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(analysis["errors"]))
    base_shape = (
        (analysis["height"], analysis["width"])
        if analysis["orientation"] == "vertical"
        else (analysis["width"], analysis["height"])
    )
    key = (base_shape, analysis["room_count"])
    if key not in _PROFILE_BY_BASE_SHAPE_AND_ROOMS:
        raise ValueError(f"unrecognized generated profile: {key!r}")
    return {
        "layout_profile": _PROFILE_BY_BASE_SHAPE_AND_ROOMS[key],
        "orientation": analysis["orientation"],
        "seed_coverage": "one_seedless" if analysis["seedless_rooms"] else "all_seeded",
    }


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"valid": False, "errors": list(analysis["errors"])}
    observed = observe_overrides(grid)
    return {
        "valid": True,
        "shape": [analysis["height"], analysis["width"]],
        "palette_size": len(analysis["palette"]),
        "rooms": analysis["room_count"],
        "seeded_rooms": analysis["seeded_rooms"],
        "seedless_rooms": analysis["seedless_rooms"],
        **observed,
        "strict_canonical_like": strict_canonical_like(grid) == [],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected Racket rule."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("rule_mirror requires a non-empty rectangular grid")
    output = [list(row) for row in grid]
    for room in _room_components(grid):
        colors = {
            grid[r][c]
            for r, c in room
            if grid[r][c] not in (0, 5, 7)
        }
        if len(colors) != 1:
            continue
        color = next(iter(colors))
        for r, c in room:
            if grid[r][c] == 0:
                output[r][c] = color
    return output
