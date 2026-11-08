"""Generator for ARC task 8ce1331089a3.

Four distinct edge colors define four routes.  Interior pixels matching an
edge color move to the inner cell adjacent to that edge while preserving their
other coordinate.  One-off non-edge colors are distractors and disappear.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8ce1331089a3"
VERSION = "3.0.0"
TASK_ID = "8ce1331089a3"
RULE_HASH = "3f9dcd988189"

SUMMARY = (
    "A rectangular grid has four distinct nonzero border colors: top, bottom, "
    "left, and right, with zero corners. Sparse interior pixels sit at least "
    "one blank cell away from the border. Pixels matching a border color move "
    "to the adjacent inner wall while preserving the perpendicular coordinate; "
    "one-off non-border distractor colors are removed."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "8..18 by 8..18 grid; four constant, distinct nonzero edges and zero corners",
    "6..16 sparse interior pixels occupy rows/columns 2..h-3/w-3",
    "one to three non-edge colors occur exactly once each and are removed",
    "matching colors represent at least three routes and have collision-free destinations",
]

AXES = {
    "grid_h": {"type": "int", "default": "4-profile schedule", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "4-profile schedule", "valid": "8..18"},
    "n_pixels": {"type": "int", "default": "4-profile schedule", "valid": "6..16"},
    "palette_size": {"type": "int", "default": "4-profile schedule", "valid": "6..8"},
}

# Every declared boundary combination is intended to work; no silent fallback.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# (height, width, total input palette size including zero, interior pixels)
CANONICAL_PROFILES: tuple[tuple[int, int, int, int], ...] = (
    (12, 12, 7, 7),
    (10, 15, 6, 7),
    (14, 11, 6, 6),
    (14, 17, 8, 13),
)
SCHEDULE_PROFILES = tuple(range(len(CANONICAL_PROFILES)))
_LAYOUT_PROFILES = ("scattered", "centered", "corners", "row_lean")
_ROUTES = ("top", "bottom", "left", "right")
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the reproducible four-residue curriculum profile."""
    del seed, difficulty
    return int(sample_index) % len(CANONICAL_PROFILES)


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override key(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _scheduled_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    scheduled: int,
    lo: int,
    hi: int,
) -> int:
    """Record a scheduled default while accepting the full declared range."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _coordinate_order(values: list[int], mode: str, rng) -> list[int]:
    values = list(values)
    ties = {value: rng.random() for value in values}
    midpoint = (values[0] + values[-1]) / 2
    if mode == "centered":
        return sorted(values, key=lambda value: (abs(value - midpoint), ties[value]))
    if mode == "corners":
        return sorted(
            values,
            key=lambda value: (min(value - values[0], values[-1] - value), ties[value]),
        )
    rng.shuffle(values)
    return values


def _position_score(
    position: tuple[int, int],
    *,
    mode: str,
    height: int,
    width: int,
    lean_row: int,
) -> tuple[float, float]:
    row, col = position
    if mode == "centered":
        return (
            abs(row - (height - 1) / 2) + abs(col - (width - 1) / 2),
            0.0,
        )
    if mode == "corners":
        corners = ((2, 2), (2, width - 3), (height - 3, 2), (height - 3, width - 3))
        return (min(abs(row - rr) + abs(col - cc) for rr, cc in corners), 0.0)
    if mode == "row_lean":
        return (abs(row - lean_row), abs(col - (width - 1) / 2))
    return (0.0, 0.0)


def _route_sequence(
    count: int,
    capacities: dict[str, int],
    profile_index: int,
) -> list[str]:
    rotated = list(_ROUTES[profile_index:] + _ROUTES[:profile_index])
    sequence = rotated[: min(count, len(rotated))]
    counts = Counter(sequence)
    preferences = (
        ("top", "bottom", "left", "right"),
        ("top", "left", "top", "bottom", "right"),
        ("left", "right", "left", "top", "bottom"),
        ("bottom", "right", "bottom", "left", "top"),
    )[profile_index]
    cursor = 0
    while len(sequence) < count:
        route = preferences[cursor % len(preferences)]
        cursor += 1
        if counts[route] >= capacities[route]:
            if cursor > 20 * count:
                raise ValueError(
                    f"unable to allocate {count} matching pixels within route capacities {capacities}"
                )
            continue
        sequence.append(route)
        counts[route] += 1
    return sequence


def _matching_positions(
    *,
    ctx,
    height: int,
    width: int,
    routes: list[str],
    mode: str,
    profile_index: int,
) -> list[tuple[int, int]]:
    safe_rows = list(range(2, height - 2))
    safe_cols = list(range(2, width - 2))
    lean_row = safe_rows[ctx.draw_rng("lean-row").randrange(len(safe_rows))]

    route_targets: dict[str, list[int]] = {}
    for route in _ROUTES:
        values = safe_cols if route in {"top", "bottom"} else safe_rows
        route_targets[route] = _coordinate_order(
            values,
            mode,
            ctx.draw_rng(f"targets:{profile_index}:{route}"),
        )

    target_offsets = Counter()
    tokens: list[tuple[str, int]] = []
    for route in routes:
        offset = target_offsets[route]
        tokens.append((route, route_targets[route][offset]))
        target_offsets[route] += 1

    candidates: list[list[tuple[int, int]]] = []
    for token_index, (route, target) in enumerate(tokens):
        if route in {"top", "bottom"}:
            options = [(row, target) for row in safe_rows]
        else:
            options = [(target, col) for col in safe_cols]
        tie_rng = ctx.draw_rng(f"source:{profile_index}:{token_index}:{route}:{target}")
        ranked = [
            (
                _position_score(
                    position,
                    mode=mode,
                    height=height,
                    width=width,
                    lean_row=lean_row,
                ),
                tie_rng.random(),
                position,
            )
            for position in options
        ]
        ranked.sort(key=lambda item: (item[0], item[1], item[2]))
        candidates.append([position for _, _, position in ranked])

    matched_position_to_token: dict[tuple[int, int], int] = {}
    token_to_position: dict[int, tuple[int, int]] = {}

    def assign(token_index: int, seen: set[tuple[int, int]]) -> bool:
        for position in candidates[token_index]:
            if position in seen:
                continue
            seen.add(position)
            incumbent = matched_position_to_token.get(position)
            if incumbent is None or assign(incumbent, seen):
                matched_position_to_token[position] = token_index
                token_to_position[token_index] = position
                return True
        return False

    for token_index in range(len(tokens)):
        if not assign(token_index, set()):
            raise ValueError(
                f"could not place route token {token_index + 1}/{len(tokens)} "
                f"in {height}x{width}"
            )
    return [token_to_position[index] for index in range(len(tokens))]


def _distractor_positions(
    *,
    ctx,
    height: int,
    width: int,
    occupied: set[tuple[int, int]],
    count: int,
    mode: str,
    profile_index: int,
) -> list[tuple[int, int]]:
    safe = [
        (row, col)
        for row in range(2, height - 2)
        for col in range(2, width - 2)
        if (row, col) not in occupied
    ]
    lean_rows = list(range(2, height - 2))
    lean_row = lean_rows[ctx.draw_rng("distractor-lean-row").randrange(len(lean_rows))]
    tie_rng = ctx.draw_rng(f"distractor-positions:{profile_index}")
    ranked = [
        (
            _position_score(
                position,
                mode=mode,
                height=height,
                width=width,
                lean_row=lean_row,
            ),
            tie_rng.random(),
            position,
        )
        for position in safe
    ]
    ranked.sort(key=lambda item: (item[0], item[1], item[2]))
    if len(ranked) < count:
        raise ValueError(
            f"n_pixels leaves only {len(ranked)} distractor slots, need {count}"
        )
    return [position for _, _, position in ranked[:count]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    profile_index = schedule_profile(seed, sample_index, difficulty)
    # Keep the canonical shape/palette schedule fixed while making difficulty
    # an observable curriculum control over route balance and placement.
    band_offset = {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    layout_index = (profile_index + band_offset) % len(_LAYOUT_PROFILES)
    scheduled_h, scheduled_w, scheduled_palette, scheduled_pixels = CANONICAL_PROFILES[
        profile_index
    ]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = _scheduled_int(ctx, overrides, "grid_h", scheduled_h, 8, 18)
    width = _scheduled_int(ctx, overrides, "grid_w", scheduled_w, 8, 18)
    n_pixels = _scheduled_int(ctx, overrides, "n_pixels", scheduled_pixels, 6, 16)
    palette_size = _scheduled_int(
        ctx, overrides, "palette_size", scheduled_palette, 6, 8
    )

    capacity = (height - 4) * (width - 4)
    if n_pixels > capacity:
        raise ValueError(
            f"n_pixels={n_pixels} exceeds safe interior capacity {capacity} "
            f"for grid_h={height}, grid_w={width}"
        )

    colors = ctx.draw_distinct_colors("palette", n=palette_size - 1, exclude={0})
    top_color, bottom_color, left_color, right_color = colors[:4]
    distractor_colors = list(colors[4:])
    route_colors = {
        "top": top_color,
        "bottom": bottom_color,
        "left": left_color,
        "right": right_color,
    }

    matching_count = n_pixels - len(distractor_colors)
    capacities = {
        "top": width - 4,
        "bottom": width - 4,
        "left": height - 4,
        "right": height - 4,
    }
    routes = _route_sequence(matching_count, capacities, layout_index)
    mode = _LAYOUT_PROFILES[layout_index]
    matching_positions = _matching_positions(
        ctx=ctx,
        height=height,
        width=width,
        routes=routes,
        mode=mode,
        profile_index=layout_index,
    )

    grid = full_grid(height, width, 0)
    for col in range(1, width - 1):
        grid[0][col] = top_color
        grid[height - 1][col] = bottom_color
    for row in range(1, height - 1):
        grid[row][0] = left_color
        grid[row][width - 1] = right_color

    for route, (row, col) in zip(routes, matching_positions, strict=True):
        grid[row][col] = route_colors[route]

    distractor_positions = _distractor_positions(
        ctx=ctx,
        height=height,
        width=width,
        occupied=set(matching_positions),
        count=len(distractor_colors),
        mode=mode,
        profile_index=layout_index,
    )
    color_rng = ctx.draw_rng(f"distractor-color-order:{layout_index}")
    color_rng.shuffle(distractor_colors)
    for color, (row, col) in zip(
        distractor_colors, distractor_positions, strict=True
    ):
        grid[row][col] = color
    return grid


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    facts: dict[str, Any] = {
        "errors": errors,
        "valid": False,
        "height": 0,
        "width": 0,
        "palette_size": 0,
        "n_pixels": 0,
        "edge_colors": (),
        "matching": [],
        "distractors": [],
        "route_counts": Counter(),
    }
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        errors.append("grid must be a nonempty list of rows")
        return facts
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        errors.append("grid must be rectangular with nonempty rows")
        return facts
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid colors must be integers in 0..9")
        return facts

    height = len(grid)
    facts["height"] = height
    facts["width"] = width
    if not 8 <= height <= 18:
        errors.append(f"grid_h must be in 8..18, found {height}")
    if not 8 <= width <= 18:
        errors.append(f"grid_w must be in 8..18, found {width}")
    if height < 4 or width < 4:
        facts["palette_size"] = len({value for row in grid for value in row})
        return facts

    corners = (grid[0][0], grid[0][width - 1], grid[height - 1][0], grid[height - 1][width - 1])
    if any(corner != 0 for corner in corners):
        errors.append(f"border corners must be zero, found {list(corners)}")

    top, bottom = grid[0][1], grid[height - 1][1]
    left, right = grid[1][0], grid[1][width - 1]
    edge_colors = (top, bottom, left, right)
    facts["edge_colors"] = edge_colors
    if any(color == 0 for color in edge_colors) or len(set(edge_colors)) != 4:
        errors.append(
            f"edge colors must be four distinct nonzero values, found {list(edge_colors)}"
        )
    if any(grid[0][col] != top for col in range(1, width - 1)):
        errors.append("top edge must be constant between its corners")
    if any(grid[height - 1][col] != bottom for col in range(1, width - 1)):
        errors.append("bottom edge must be constant between its corners")
    if any(grid[row][0] != left for row in range(1, height - 1)):
        errors.append("left edge must be constant between its corners")
    if any(grid[row][width - 1] != right for row in range(1, height - 1)):
        errors.append("right edge must be constant between its corners")

    palette = {value for row in grid for value in row}
    palette_size = len(palette)
    facts["palette_size"] = palette_size
    if not 6 <= palette_size <= 8:
        errors.append(f"palette_size must be in 6..8, found {palette_size}")

    colored: list[tuple[int, int, int]] = []
    unsafe: list[tuple[int, int]] = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = grid[row][col]
            if value == 0:
                continue
            colored.append((row, col, value))
            if row in {1, height - 2} or col in {1, width - 2}:
                unsafe.append((row, col))
    n_pixels = len(colored)
    facts["n_pixels"] = n_pixels
    if not 6 <= n_pixels <= 16:
        errors.append(f"n_pixels must be in 6..16, found {n_pixels}")
    if unsafe:
        errors.append(
            "interior pixels must be separated from the border by one blank cell; "
            f"found {unsafe[:4]}"
        )

    route_by_color = {
        top: "top",
        bottom: "bottom",
        left: "left",
        right: "right",
    }
    matching: list[tuple[int, int, int, str]] = []
    distractors: list[tuple[int, int, int]] = []
    route_counts: Counter[str] = Counter()
    destination_keys: dict[str, set[int]] = {route: set() for route in _ROUTES}
    collision_routes: set[str] = set()
    for row, col, value in colored:
        route = route_by_color.get(value)
        if route is None:
            distractors.append((row, col, value))
            continue
        matching.append((row, col, value, route))
        route_counts[route] += 1
        key = col if route in {"top", "bottom"} else row
        if key in destination_keys[route]:
            collision_routes.add(route)
        destination_keys[route].add(key)

    facts["matching"] = matching
    facts["distractors"] = distractors
    facts["route_counts"] = route_counts
    if len(matching) < 3:
        errors.append("at least three matching pixels are required")
    if len(route_counts) < 3:
        errors.append(
            f"matching pixels must demonstrate at least three routes, found {sorted(route_counts)}"
        )
    if collision_routes:
        errors.append(
            "matching pixels create duplicate destination cells for routes "
            + ", ".join(sorted(collision_routes))
        )

    distractor_counts = Counter(value for _, _, value in distractors)
    expected_distractor_colors = palette_size - 5
    if len(distractor_counts) != expected_distractor_colors:
        errors.append(
            f"expected {expected_distractor_colors} non-edge distractor colors, "
            f"found {len(distractor_counts)}"
        )
    repeated_distractors = sorted(
        color for color, count in distractor_counts.items() if count != 1
    )
    if repeated_distractors:
        errors.append(
            "each distractor color must occur exactly once, bad colors "
            f"{repeated_distractors}"
        )

    facts["valid"] = not errors
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    facts = _analysis(grid)
    if facts["errors"]:
        return list(facts["errors"])
    profile = (
        facts["height"],
        facts["width"],
        facts["palette_size"],
        facts["n_pixels"],
    )
    if profile not in set(CANONICAL_PROFILES):
        return [
            f"profile {profile} is outside canonical support {list(CANONICAL_PROFILES)}"
        ]
    return []


def observe_overrides(grid) -> dict[str, int]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(facts["errors"][:3]))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_pixels": facts["n_pixels"],
        "palette_size": facts["palette_size"],
    }


def _blank_with_border(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for col in range(width):
        output[0][col] = grid[0][col]
        output[height - 1][col] = grid[height - 1][col]
    for row in range(height):
        output[row][0] = grid[row][0]
        output[row][width - 1] = grid[row][width - 1]
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket rule."""
    height, width = len(grid), len(grid[0])
    top, bottom = grid[0][1], grid[height - 1][1]
    left, right = grid[1][0], grid[1][width - 1]
    output = _blank_with_border(grid)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = grid[row][col]
            if value == top:
                output[1][col] = value
            elif value == bottom:
                output[height - 2][col] = value
            elif value == left:
                output[row][1] = value
            elif value == right:
                output[row][width - 2] = value
    return output


def _rival_clear_interior(grid: list[list[int]]) -> list[list[int]]:
    return _blank_with_border(grid)


def _rival_keep_distractors(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    facts = _analysis(grid)
    for row, col, value in facts["distractors"]:
        output[row][col] = value
    return output


def _rival_move_first_per_route(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    top, bottom = grid[0][1], grid[height - 1][1]
    left, right = grid[1][0], grid[1][width - 1]
    mapping = ((top, "top"), (bottom, "bottom"), (left, "left"), (right, "right"))
    output = _blank_with_border(grid)
    seen: set[str] = set()
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = grid[row][col]
            route = next((name for color, name in mapping if value == color), None)
            if route is None or route in seen:
                continue
            seen.add(route)
            if route == "top":
                output[1][col] = value
            elif route == "bottom":
                output[height - 2][col] = value
            elif route == "left":
                output[row][1] = value
            else:
                output[row][width - 2] = value
    return output


def _rival_swap_vertical_routes(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    top, bottom = grid[0][1], grid[height - 1][1]
    left, right = grid[1][0], grid[1][width - 1]
    output = _blank_with_border(grid)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = grid[row][col]
            if value == top:
                output[height - 2][col] = value
            elif value == bottom:
                output[1][col] = value
            elif value == left:
                output[row][1] = value
            elif value == right:
                output[row][width - 2] = value
    return output


def _rival_swap_horizontal_routes(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    top, bottom = grid[0][1], grid[height - 1][1]
    left, right = grid[1][0], grid[1][width - 1]
    output = _blank_with_border(grid)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = grid[row][col]
            if value == top:
                output[1][col] = value
            elif value == bottom:
                output[height - 2][col] = value
            elif value == left:
                output[row][width - 2] = value
            elif value == right:
                output[row][1] = value
    return output


def _witness_route(route: str) -> Callable[[list[list[int]]], bool]:
    def witness(grid: list[list[int]]) -> bool:
        facts = _analysis(grid)
        return not facts["errors"] and facts["route_counts"].get(route, 0) > 0

    return witness


def _witness_distractor(grid: list[list[int]]) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and bool(facts["distractors"])


def _witness_repeated_route(grid: list[list[int]]) -> bool:
    facts = _analysis(grid)
    return not facts["errors"] and max(facts["route_counts"].values(), default=0) >= 2


SEMANTIC_WITNESSES = {
    "routes_to_top": _witness_route("top"),
    "routes_to_bottom": _witness_route("bottom"),
    "routes_to_left": _witness_route("left"),
    "routes_to_right": _witness_route("right"),
    "removes_distractor": _witness_distractor,
    "preserves_multiple_same_route": _witness_repeated_route,
}

SEMANTIC_RIVALS = {
    "clear_interior": _rival_clear_interior,
    "keep_distractors": _rival_keep_distractors,
    "move_first_per_route": _rival_move_first_per_route,
    "swap_vertical_routes": _rival_swap_vertical_routes,
    "swap_horizontal_routes": _rival_swap_horizontal_routes,
}

WITNESS_RIVALS = {
    "routes_to_top": ["swap_vertical_routes"],
    "routes_to_bottom": ["swap_vertical_routes"],
    "routes_to_left": ["swap_horizontal_routes"],
    "routes_to_right": ["swap_horizontal_routes"],
    "removes_distractor": ["keep_distractors"],
    "preserves_multiple_same_route": ["move_first_per_route"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos: list[dict], query: dict) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, found {len(demos)}"
        )
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival([row[:] for row in demo["input"]]) == demo["output"]
                for demo in demos
            )
            if not survives:
                continue
            rival_query = rival([row[:] for row in query["input"]])
            if rival_query != query["output"]:
                reasons.append(f"competitor {name!r} survives all demonstrations")
        except Exception as exc:  # gate reports this reason without hiding it
            reasons.append(f"competitor {name!r} errored: {type(exc).__name__}: {exc}")
    return reasons
