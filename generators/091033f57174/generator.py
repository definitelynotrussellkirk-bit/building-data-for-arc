"""Generator for 091033f57174 — Commanded L-Links.

The selected Racket program is the label authority.  A command marker at
``(0, 0)`` chooses which of the two possible L bends connects every other
colour that occurs exactly twice:

* command 1: horizontal from the first (row-major) endpoint, then vertical;
* command 2: vertical from the first endpoint, then horizontal.

Version 3 makes every public axis exact and observable, preserves canonical
profile support, and schedules enough counterexamples to refute the most
plausible canonical-fitting shortcuts in every three-demo/four-pair lesson.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "091033f57174"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0ce03c4c47d8"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

SUMMARY = (
    "A command cell at (0,0) is 1 or 2. Every other colour occurring "
    "exactly twice marks endpoints on distinct rows and columns. Command 1 "
    "draws horizontally from the first row-major endpoint and then vertically "
    "to the second; command 2 draws vertically first and then horizontally. "
    "Colours with any count other than two, and the command colour itself, "
    "remain unchanged."
)

INVARIANTS = [
    "the unique row-0 marker is command 1 or 2 at (0,0)",
    "there are one to four non-command endpoint colours, each occurring twice",
    "each endpoint pair occupies distinct rows and distinct columns",
    "optional three-cell and command-colour guards lie outside canonical paths",
]

TEXTURES = ("plain", "three_cells", "cmd_color_pair", "both")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled profile in 8..12",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled profile in 8..12",
        "valid": "8..12",
    },
    "n_pairs": {
        "type": "int",
        "default": "scheduled 2|2|3|4",
        "valid": "1..4",
    },
    "command": {
        "type": "int",
        "default": "scheduled 1|2|1|2",
        "valid": "1..2",
    },
    "texture": {
        "type": "str",
        "default": "scheduled plain|plain|both|both",
        "valid": "plain|three_cells|cmd_color_pair|both",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple = ()

_CANONICAL_DIMENSIONS = ((8, 8), (9, 9), (10, 10), (8, 10), (9, 10))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_PAIR_COLOURS = (3, 4, 5, 6, 7, 8, 9)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of {_VALID_DIFFICULTIES!r}; got {difficulty!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis: {unknown[0]}")

    for name, lo, hi in (
        ("grid_h", 8, 12),
        ("grid_w", 8, 12),
        ("n_pairs", 1, 4),
        ("command", 1, 2),
    ):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    if "texture" in overrides:
        value = overrides["texture"]
        if type(value) is not str:
            raise TypeError("texture override must be a string")
        if value not in TEXTURES:
            raise ValueError(f"texture override {value!r} not in {TEXTURES!r}")


def _scheduled_axes(ctx, difficulty: str | None) -> tuple[int, int, int, int, str, bool]:
    """Return the four-slot lesson schedule.

    Slots 0/1 deliberately preserve a canonical input profile.  Slots 2/3
    carry two independent guard families and at least three endpoint pairs.
    Consequently deleting any one pair from a four-pair lesson still leaves
    both commands and every shortcut-killing guard among the demonstrations.
    """
    slot = ctx.sample_index % LESSON_SCHEDULE_PERIOD
    if slot in (0, 1):
        profile_rng = ctx.draw_rng("canonical_profile")
        h, w = profile_rng.choice(_CANONICAL_DIMENSIONS)
        n_pairs, command, texture, force_crossing = 2, slot + 1, "plain", False
    else:
        if difficulty == "easy":
            options = ((10, 10), (10, 11), (11, 10))
        elif difficulty == "hard":
            options = ((11, 11), (11, 12), (12, 11), (12, 12))
        else:
            options = tuple((h, w) for h in range(10, 13) for w in range(10, 13))
        h, w = ctx.draw_rng("teaching_profile").choice(options)
        n_pairs = 3 if slot == 2 else 4
        command = 1 if slot == 2 else 2
        texture = "both"
        force_crossing = True

    # Singleton choices record all public axes through the normal provenance
    # API without allowing an implicit schedule to override an explicit call.
    h = ctx.draw_choice("grid_h", (h,))
    w = ctx.draw_choice("grid_w", (w,))
    n_pairs = ctx.draw_choice("n_pairs", (n_pairs,))
    command = ctx.draw_choice("command", (command,))
    texture = ctx.draw_choice("texture", (texture,))
    return h, w, n_pairs, command, texture, force_crossing


def _free_axes(ctx) -> tuple[int, int, int, int, str, bool]:
    """Draw the full declared product; explicit values are never band-clamped."""
    h = ctx.draw_int_strict("grid_h", 8, 12)
    w = ctx.draw_int_strict("grid_w", 8, 12)
    n_pairs = ctx.draw_int_strict("n_pairs", 1, 4)
    command = ctx.draw_choice("command", (1, 2))
    texture = ctx.draw_choice("texture", TEXTURES)
    return h, w, n_pairs, command, texture, False


def _route_cells(points: Sequence[tuple[int, int]], command: int) -> tuple[tuple[int, int], ...]:
    if len(points) != 2:
        raise ValueError(f"expected two endpoints, found {len(points)}")
    a, b = sorted(points)
    if command == 1:
        leg_a = [(a[0], c) for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
        leg_b = [(r, b[1]) for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
    else:
        leg_a = [(r, a[1]) for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
        leg_b = [(b[0], c) for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
    return tuple(dict.fromkeys(leg_a + leg_b))


def _quadrant_pairs(h: int, w: int, n_pairs: int, rng) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Place up to four pairs in disjoint rectangles, without retry truncation."""
    row_cut = 1 + (h - 1) // 2
    col_cut = w // 2
    row_groups = (tuple(range(1, row_cut)), tuple(range(row_cut, h)))
    col_groups = (tuple(range(0, col_cut)), tuple(range(col_cut, w)))
    regions = [(rows, cols) for rows in row_groups for cols in col_groups]
    rng.shuffle(regions)

    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for rows, cols in regions[:n_pairs]:
        selected_rows = sorted(rng.sample(list(rows), 2))
        selected_cols = sorted(rng.sample(list(cols), 2))
        if rng.randrange(2):
            points = ((selected_rows[0], selected_cols[0]), (selected_rows[1], selected_cols[1]))
        else:
            points = ((selected_rows[0], selected_cols[1]), (selected_rows[1], selected_cols[0]))
        pairs.append(points)
    return pairs


def _teaching_pairs(h: int, w: int, n_pairs: int, command: int, rng):
    """A finite crossing construction used by the two guarded lesson slots."""
    if h < 10 or w < 10 or n_pairs < 2:
        raise ValueError("crossing construction requires h,w>=10 and at least two pairs")
    if command == 1:
        pairs = [
            ((1, w - 3), (h - 4, 2)),
            ((3, 1), (h - 2, w - 4)),
        ]
    else:
        pairs = [
            ((1, 2), (h - 4, w - 3)),
            ((3, w - 4), (h - 2, 1)),
        ]
    if n_pairs >= 3:
        pairs.append(((h - 3, w - 2), (h - 1, w - 1)))
    if n_pairs >= 4:
        pairs.append(((h - 3, 0), (h - 1, 1)))

    if rng.randrange(2):
        pairs = [tuple((r, w - 1 - c) for r, c in pair) for pair in pairs]
    return [tuple(sorted(pair)) for pair in pairs]


def _colour_points(grid: Sequence[Sequence[int]], colour: int, *, omit_command_cell=False):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == colour and not (omit_command_cell and (r, c) == (0, 0))
    ]


def _colour_order(grid: Sequence[Sequence[int]]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                ordered.append(value)
    return ordered


def _marker_pair(
    available: set[tuple[int, int]],
    command: int,
    rng,
) -> tuple[list[tuple[int, int]], tuple[int, int]]:
    """Choose two markers plus a reserved zero that proves routing is visible."""
    cells = sorted(available)
    rng.shuffle(cells)
    for left in cells:
        for right in cells:
            if left >= right or left[0] == right[0] or left[1] == right[1]:
                continue
            route = _route_cells((left, right), command)
            witnesses = [cell for cell in route if cell not in (left, right) and cell in available]
            if witnesses:
                return [left, right], witnesses[0]
    raise RuntimeError("could not place a visible two-marker guard")


def _triple_markers(
    available: set[tuple[int, int]],
    command: int,
    rng,
) -> tuple[list[tuple[int, int]], tuple[int, int]]:
    """Choose three markers whose first/last routing adds a reserved zero."""
    cells = sorted(available)
    rng.shuffle(cells)
    for left in cells:
        for right in cells:
            if left >= right or left[0] == right[0] or left[1] == right[1]:
                continue
            middle_options = [cell for cell in cells if left < cell < right and cell not in (left, right)]
            if not middle_options:
                continue
            route = _route_cells((left, right), command)
            for middle in middle_options:
                witnesses = [
                    cell for cell in route
                    if cell not in (left, middle, right) and cell in available
                ]
                if witnesses:
                    return [left, middle, right], witnesses[0]
    raise RuntimeError("could not place a visible three-marker guard")


def _build_grid(
    h: int,
    w: int,
    n_pairs: int,
    command: int,
    texture: str,
    *,
    force_crossing: bool,
    rng,
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    grid[0][0] = command

    colours = list(_PAIR_COLOURS)
    rng.shuffle(colours)
    pair_colours = colours[:n_pairs]
    spare_colours = colours[n_pairs:]
    pairs = (
        _teaching_pairs(h, w, n_pairs, command, rng)
        if force_crossing
        else _quadrant_pairs(h, w, n_pairs, rng)
    )

    pair_paths: set[tuple[int, int]] = set()
    for colour, points in zip(pair_colours, pairs):
        for r, c in points:
            grid[r][c] = colour
        pair_paths.update(_route_cells(points, command))

    available = {
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if (r, c) not in pair_paths and grid[r][c] == 0
    }
    reserved: set[tuple[int, int]] = set()

    if texture in ("cmd_color_pair", "both"):
        markers, witness = _marker_pair(available - reserved, command, rng)
        for r, c in markers:
            grid[r][c] = command
        reserved.add(witness)
        available.difference_update(markers)

    if texture in ("three_cells", "both"):
        if not spare_colours:
            raise RuntimeError("no non-command colour remains for three-cell guard")
        markers, witness = _triple_markers(available - reserved, command, rng)
        triple_colour = spare_colours[0]
        for r, c in markers:
            grid[r][c] = triple_colour
        reserved.add(witness)
        available.difference_update(markers)

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides:
        h, w, n_pairs, command, texture, force_crossing = _free_axes(ctx)
    else:
        h, w, n_pairs, command, texture, force_crossing = _scheduled_axes(ctx, difficulty)

    grid = _build_grid(
        h,
        w,
        n_pairs,
        command,
        texture,
        force_crossing=force_crossing,
        rng=ctx.draw_rng("layout"),
    )
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_pairs": n_pairs,
        "command": command,
        "texture": texture,
    }
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError(f"internal construction failed: {errors}")
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"axis construction mismatch: expected {expected}, observed {observed}")
    return grid


def _analyze(grid: Any) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"], {}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every row must be a list"], {}
    widths = [len(row) for row in grid]
    if not widths or widths[0] == 0 or any(width != widths[0] for width in widths):
        return ["grid must be nonempty and rectangular"], {}
    h, w = len(grid), widths[0]
    if not (8 <= h <= 12 and 8 <= w <= 12):
        errors.append(f"grid dimensions {(h, w)} outside 8..12")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell {(r, c)} must be an integer ARC colour 0..9")
    if errors:
        return errors, {}

    command = grid[0][0]
    if command not in (1, 2):
        errors.append(f"(0,0)={command!r}; expected command 1 or 2")
    if any(grid[0][c] != 0 for c in range(1, w)):
        errors.append("row 0 may contain only the command cell")

    counts = Counter(value for row in grid for value in row if value != 0)
    if command in (1, 2) and counts[command] not in (1, 3):
        errors.append("command colour must occur once or three times")

    ordered = _colour_order(grid)
    pair_colours: list[int] = []
    triple_colours: list[int] = []
    for colour in ordered:
        if colour == command:
            continue
        if colour in (1, 2):
            errors.append("the non-command cue colour 1 or 2 may not be reused")
            continue
        count = counts[colour]
        if count == 2:
            pair_colours.append(colour)
        elif count == 3:
            triple_colours.append(colour)
        else:
            errors.append(f"non-command colour {colour} occurs {count} times; expected 2 or 3")

    if not (1 <= len(pair_colours) <= 4):
        errors.append(f"expected 1..4 endpoint colours, found {len(pair_colours)}")
    if len(triple_colours) > 1:
        errors.append("at most one three-cell guard colour is allowed")

    pair_points = {colour: _colour_points(grid, colour) for colour in pair_colours}
    pair_paths: dict[int, set[tuple[int, int]]] = {}
    for colour, points in pair_points.items():
        if any(r == 0 for r, _ in points):
            errors.append(f"endpoint colour {colour} may not use row 0")
        if len({r for r, _ in points}) != 2 or len({c for _, c in points}) != 2:
            errors.append(f"endpoint colour {colour} must occupy distinct rows and columns")
            continue
        pair_paths[colour] = set(_route_cells(points, command))

    all_endpoints = {
        point: colour for colour, points in pair_points.items() for point in points
    }
    for colour, path in pair_paths.items():
        foreign = [point for point in path if point in all_endpoints and all_endpoints[point] != colour]
        if foreign:
            errors.append(f"path for colour {colour} crosses another endpoint at {foreign[0]}")

    canonical_path_union = set().union(*pair_paths.values()) if pair_paths else set()
    for colour in triple_colours:
        points = sorted(_colour_points(grid, colour))
        if any(r == 0 for r, _ in points):
            errors.append("three-cell guard may not use row 0")
        if any(point in canonical_path_union for point in points):
            errors.append("three-cell guard lies on a canonical path")
        if len(points) == 3:
            first, last = points[0], points[-1]
            if first[0] == last[0] or first[1] == last[1]:
                errors.append("three-cell guard first/last markers must define a nondegenerate L")
            elif not any(
                grid[r][c] == 0 for r, c in _route_cells((first, last), command)
            ):
                errors.append("three-cell shortcut guard has no visible routed zero")

    if command in (1, 2) and counts[command] == 3:
        extras = _colour_points(grid, command, omit_command_cell=True)
        if any(r == 0 for r, _ in extras):
            errors.append("extra command-colour markers may not use row 0")
        if any(point in canonical_path_union for point in extras):
            errors.append("command-colour guard lies on a canonical path")
        if len(extras) == 2:
            if extras[0][0] == extras[1][0] or extras[0][1] == extras[1][1]:
                errors.append("extra command markers must define a nondegenerate L")
            elif not any(
                grid[r][c] == 0 for r, c in _route_cells(extras, command)
            ):
                errors.append("command-colour shortcut guard has no visible routed zero")

    has_triple = bool(triple_colours)
    has_command_pair = command in (1, 2) and counts[command] == 3
    texture = {
        (False, False): "plain",
        (True, False): "three_cells",
        (False, True): "cmd_color_pair",
        (True, True): "both",
    }[(has_triple, has_command_pair)]
    facts = {
        "grid_h": h,
        "grid_w": w,
        "n_pairs": len(pair_colours),
        "command": command,
        "texture": texture,
        "pair_colours": pair_colours,
        "triple_colours": triple_colours,
    }
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Strict structural grammar shared by generation and audit tooling."""
    errors, _ = _analyze(grid)
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, int | str]:
    errors, facts = _analyze(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors}")
    return {
        key: facts[key]
        for key in ("grid_h", "grid_w", "n_pairs", "command", "texture")
    }


def _paint_records(grid, records: Iterable[tuple[int, Sequence[tuple[int, int]]]], command: int):
    out = [list(row) for row in grid]
    for colour, points in records:
        for r, c in _route_cells(points, command):
            out[r][c] = colour
    return out


def rule_mirror(grid):
    """Independent Python mirror used only for checks; Racket remains authority."""
    command = grid[0][0]
    records = []
    for colour in _colour_order(grid):
        if colour == command:
            continue
        points = _colour_points(grid, colour)
        if len(points) == 2:
            records.append((colour, points))
    return _paint_records(grid, records, command)


def _always_command_one(grid):
    command = grid[0][0]
    records = []
    for colour in _colour_order(grid):
        if colour != command:
            points = _colour_points(grid, colour)
            if len(points) == 2:
                records.append((colour, points))
    return _paint_records(grid, records, 1)


def _always_command_two(grid):
    command = grid[0][0]
    records = []
    for colour in _colour_order(grid):
        if colour != command:
            points = _colour_points(grid, colour)
            if len(points) == 2:
                records.append((colour, points))
    return _paint_records(grid, records, 2)


def _route_three_marker_colours(grid):
    command = grid[0][0]
    records = []
    for colour in _colour_order(grid):
        if colour == command:
            continue
        points = _colour_points(grid, colour)
        if len(points) >= 2:
            records.append((colour, (points[0], points[-1])))
    return _paint_records(grid, records, command)


def _exclude_command_cell_only(grid):
    command = grid[0][0]
    records = []
    for colour in _colour_order(grid):
        points = _colour_points(grid, colour, omit_command_cell=True)
        if len(points) == 2:
            records.append((colour, points))
    return _paint_records(grid, records, command)


def _first_two_pairs_only(grid):
    command = grid[0][0]
    records = []
    for colour in _colour_order(grid):
        if colour == command:
            continue
        points = _colour_points(grid, colour)
        if len(points) == 2:
            records.append((colour, points))
            if len(records) == 2:
                break
    return _paint_records(grid, records, command)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "always_command_one": _always_command_one,
    "always_command_two": _always_command_two,
    "route_three_marker_colors": _route_three_marker_colours,
    "exclude_command_cell_only": _exclude_command_cell_only,
    "first_two_pairs_only": _first_two_pairs_only,
}
CANONICAL_SHORTCUTS = {
    "route_three_marker_colors": _route_three_marker_colours,
    "exclude_command_cell_only": _exclude_command_cell_only,
    "first_two_pairs_only": _first_two_pairs_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rival_disagrees(grid, name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "command_one_orientation": lambda grid: (
        grid[0][0] == 1 and _rival_disagrees(grid, "always_command_two")
    ),
    "command_two_orientation": lambda grid: (
        grid[0][0] == 2 and _rival_disagrees(grid, "always_command_one")
    ),
    "three_cell_exact_count_guard": lambda grid: (
        observe_overrides(grid)["texture"] in ("three_cells", "both")
        and _rival_disagrees(grid, "route_three_marker_colors")
    ),
    "whole_command_colour_exclusion": lambda grid: (
        observe_overrides(grid)["texture"] in ("cmd_color_pair", "both")
        and _rival_disagrees(grid, "exclude_command_cell_only")
    ),
    "all_endpoint_pairs_processed": lambda grid: (
        observe_overrides(grid)["n_pairs"] >= 3
        and _rival_disagrees(grid, "first_two_pairs_only")
    ),
}
WITNESS_RIVALS = {
    "command_one_orientation": ["always_command_two"],
    "command_two_orientation": ["always_command_one"],
    "three_cell_exact_count_guard": ["route_three_marker_colors"],
    "whole_command_colour_exclusion": ["exclude_command_cell_only"],
    "all_endpoint_pairs_processed": ["first_two_pairs_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    findings: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"pair {index} is not an input/output pair")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            findings.append(f"pair {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair["output"] != expected:
            findings.append(f"pair {index} output does not match the canonical rule")
    if findings:
        return findings

    expected_query = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query["input"]) != expected_query
        except Exception as exc:
            findings.append(f"competitor {name} raised: {type(exc).__name__}: {exc}")
            continue
        if survives and changes_query:
            findings.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return findings
