"""Generator for 76e0bd03e098 — connect color pairs with clear elbows.

The canonical authority processes pair colors in first-seen row-major order.
For each pair it tries the horizontal-then-vertical elbow; if that path is not
clear in the ORIGINAL input, it uses the vertical-then-horizontal path without
a second clearance requirement.  Painting preserves color-8 walls and later
pair colors overwrite earlier paths at intersections.

Ordinary production scenes deliberately teach every consequential branch:
* a pair whose two elbows are clear (horizontal preference),
* a pair whose horizontal elbow is blocked but vertical is clear,
* a pair whose two elbows are wall-blocked (authoritative vertical fallback),
* selected-path overlap where later row-major color wins, and
* a nonnumeric color order so numeric-order processing is visibly wrong.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "76e0bd03e098"
TASK_ID = GENERATOR_ID
RULE_HASH = "43d5e3caf0e0"
VERSION = "2.0.0"
SUMMARY = (
    "Three color pairs and 4-5 color-8 walls teach H-first preference, "
    "H-blocked/V-clear routing, both-blocked V fallback, wall preservation, "
    "and row-major overwrite order."
)
EXAMPLES_NEEDED = 4

SCENE_PROFILES = ("8x10", "8x11", "8x12", "9x10", "9x11")
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted canonical profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "n_walls": {"type": "int", "default": "rng 4..5", "valid": "4..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "shape is one of the five canonical height/width profiles",
    "exactly three non-{0,8} colors, each appearing exactly twice",
    "exactly 4 or 5 color-8 walls",
    "all endpoints are diagonal rather than row/column aligned",
    "at least one pair has two clear elbows and at least one has H blocked",
    "selected paths overlap, so later row-major pair colors overwrite earlier paths",
]

# A compact 8x10 teaching scene.  Coordinates are transformed by translation
# and optional left/right reflection before colors are assigned.
_BASE_PAIRS = {
    "fallback": ((0, 3), (5, 8)),       # H wall at (0,6), V wall at (4,3)
    "preference": ((1, 1), (3, 4)),     # H and V are both clear
    "detour": ((2, 7), (6, 5)),         # H wall at (2,6), V is clear
}
_MANDATORY_WALLS = ((0, 6), (4, 3), (2, 6))
_EXTRA_WALLS = ((7, 0), (7, 9))

_PROFILE_CHOICES = {
    "easy": SCENE_PROFILES + ("8x10", "8x10", "8x11", "8x11"),
    "medium": SCENE_PROFILES + ("8x11", "8x12", "9x10", "9x10"),
    "hard": SCENE_PROFILES + ("8x12", "8x12", "9x11", "9x11"),
    None: SCENE_PROFILES,
}


def _between(a: int, b: int) -> list[int]:
    step = 1 if b >= a else -1
    return list(range(a, b + step, step))


def _elbow_path(a, b, first: str):
    r1, c1 = a
    r2, c2 = b
    if first == "h":
        return [(r1, c) for c in _between(c1, c2)] + [
            (r, c2) for r in _between(r1, r2)[1:]
        ]
    if first == "v":
        return [(r, c1) for r in _between(r1, r2)] + [
            (r2, c) for c in _between(c1, c2)[1:]
        ]
    raise ValueError(f"unknown first direction: {first!r}")


def _color_order(grid):
    seen = set()
    colors = []
    for row in grid:
        for value in row:
            if value not in (0, 8) and value not in seen:
                seen.add(value)
                colors.append(value)
    return colors


def _endpoints(grid, color):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _path_clear(grid, path, pair):
    endpoints = set(pair)
    return all(grid[r][c] == 0 or (r, c) in endpoints for r, c in path)


def _path_records(grid, *, order="reading", policy="authority"):
    colors = _color_order(grid)
    if order == "numeric":
        colors = sorted(colors)
    elif order != "reading":
        raise ValueError(f"unknown color order: {order!r}")

    records = []
    for color in colors:
        pair = _endpoints(grid, color)
        if len(pair) != 2:
            continue
        horizontal = _elbow_path(pair[0], pair[1], "h")
        vertical = _elbow_path(pair[0], pair[1], "v")
        h_clear = _path_clear(grid, horizontal, pair)
        v_clear = _path_clear(grid, vertical, pair)
        if policy == "authority":
            selected = horizontal if h_clear else vertical
        elif policy == "vertical_first":
            selected = vertical if v_clear else horizontal
        elif policy == "clear_required":
            selected = horizontal if h_clear else (vertical if v_clear else [])
        elif policy == "horizontal_only":
            selected = horizontal
        else:
            raise ValueError(f"unknown path policy: {policy!r}")
        records.append(
            {
                "color": color,
                "pair": pair,
                "horizontal": horizontal,
                "vertical": vertical,
                "h_clear": h_clear,
                "v_clear": v_clear,
                "selected": selected,
            }
        )
    return records


def _render(
    grid,
    *,
    order="reading",
    policy="authority",
    first_wins=False,
    preserve_walls=True,
):
    original = deepcopy(grid)
    output = deepcopy(grid)
    painted = set()
    for record in _path_records(original, order=order, policy=policy):
        color = record["color"]
        for r, c in record["selected"]:
            if preserve_walls and output[r][c] == 8:
                continue
            if first_wins and (r, c) in painted:
                continue
            output[r][c] = color
            painted.add((r, c))
    return output


def rule_mirror(grid):
    """Pure Python mirror used only for tests/rival contracts, not label authority."""
    return _render(grid)


def _rival_vertical_first(grid):
    return _render(grid, policy="vertical_first")


def _rival_clear_required(grid):
    return _render(grid, policy="clear_required")


def _rival_horizontal_only(grid):
    return _render(grid, policy="horizontal_only")


def _rival_first_wins(grid):
    return _render(grid, first_wins=True)


def _rival_numeric_order(grid):
    return _render(grid, order="numeric")


def _rival_paints_over_walls(grid):
    return _render(grid, preserve_walls=False)


def _has_horizontal_preference(grid):
    return any(record["h_clear"] and record["v_clear"] for record in _path_records(grid))


def _has_vertical_detour(grid):
    return any((not record["h_clear"]) and record["v_clear"] for record in _path_records(grid))


def _has_blocked_vertical_fallback(grid):
    return any(
        (not record["h_clear"])
        and (not record["v_clear"])
        and any(grid[r][c] == 8 for r, c in record["vertical"])
        for record in _path_records(grid)
    )


def _has_late_color_overlap(grid):
    return rule_mirror(grid) != _rival_first_wins(grid)


def _has_reading_order_precedence(grid):
    return rule_mirror(grid) != _rival_numeric_order(grid)


def _has_wall_preservation(grid):
    return rule_mirror(grid) != _rival_paints_over_walls(grid)


SEMANTIC_WITNESSES = {
    "horizontal_preference": _has_horizontal_preference,
    "vertical_detour": _has_vertical_detour,
    "blocked_vertical_fallback": _has_blocked_vertical_fallback,
    "late_color_wins_overlap": _has_late_color_overlap,
    "reading_order_precedence": _has_reading_order_precedence,
    "wall_preservation": _has_wall_preservation,
}
SEMANTIC_RIVALS = {
    "vertical_first": _rival_vertical_first,
    "clear_required": _rival_clear_required,
    "horizontal_only": _rival_horizontal_only,
    "first_wins": _rival_first_wins,
    "numeric_order": _rival_numeric_order,
    "paints_over_walls": _rival_paints_over_walls,
}
WITNESS_RIVALS = {
    "horizontal_preference": ["vertical_first"],
    "vertical_detour": ["horizontal_only"],
    "blocked_vertical_fallback": ["clear_required"],
    "late_color_wins_overlap": ["first_wins"],
    "reading_order_precedence": ["numeric_order"],
    "wall_preservation": ["paints_over_walls"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _profile_shape(profile: str):
    h_text, w_text = profile.split("x", 1)
    return int(h_text), int(w_text)


def _transform(point, *, row_shift, col_shift, reflected):
    r, c = point
    if reflected:
        c = 9 - c
    return r + row_shift, c + col_shift


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        if type(overrides["scene_profile"]) is not str:
            raise TypeError("scene_profile override must be a string")
    if "n_walls" in overrides and overrides["n_walls"] is not None:
        if type(overrides["n_walls"]) is not int:
            raise TypeError("n_walls override must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    choices = _PROFILE_CHOICES.get(difficulty, SCENE_PROFILES)
    profile = ctx.draw_choice("scene_profile", choices)
    n_walls = ctx.draw_int_strict("n_walls", 4, 5)
    h, w = _profile_shape(profile)

    row_shift = ctx.draw_rng("row_shift").randint(0, h - 8)
    col_shift = ctx.draw_rng("col_shift").randint(0, w - 10)
    reflected = bool(ctx.draw_rng("horizontal_reflection").randint(0, 1))

    selected_colors = sorted(ctx.draw_rng("palette").sample([1, 2, 3, 4, 5, 6, 7, 9], 3))
    role_colors = {
        # The first-seen order is max,min,middle, never numeric order.
        "fallback": selected_colors[2],
        "preference": selected_colors[0],
        "detour": selected_colors[1],
    }

    grid = full_grid(h, w, 0)
    for role, pair in _BASE_PAIRS.items():
        color = role_colors[role]
        for point in pair:
            r, c = _transform(
                point,
                row_shift=row_shift,
                col_shift=col_shift,
                reflected=reflected,
            )
            grid[r][c] = color

    walls = list(_MANDATORY_WALLS)
    if n_walls == 4:
        walls.append(ctx.draw_rng("fourth_wall").choice(_EXTRA_WALLS))
    else:
        walls.extend(_EXTRA_WALLS)
    for point in walls:
        r, c = _transform(
            point,
            row_shift=row_shift,
            col_shift=col_shift,
            reflected=reflected,
        )
        if grid[r][c] != 0:
            raise RuntimeError("constructive wall placement collided with an endpoint")
        grid[r][c] = 8

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive scene violated its contract: {errors}")
    return grid


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)):
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if not width or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    return {
        "scene_profile": f"{len(grid)}x{width}",
        "n_walls": sum(value == 8 for row in grid for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not (0 <= value <= 9) for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (not bool)"]

    errors = []
    profile = f"{len(grid)}x{width}"
    if profile not in SCENE_PROFILES:
        errors.append(f"shape {profile} is outside canonical profiles {SCENE_PROFILES}")

    counts = Counter(value for row in grid for value in row)
    pair_colors = [color for color in counts if color not in (0, 8)]
    if len(pair_colors) != 3:
        errors.append(f"expected exactly 3 pair colors, found {len(pair_colors)}")
    bad_counts = sorted(color for color in pair_colors if counts[color] != 2)
    if bad_counts:
        errors.append(f"pair colors must appear exactly twice: {bad_counts}")
    if counts.get(8, 0) not in (4, 5):
        errors.append(f"expected 4 or 5 color-8 walls, found {counts.get(8, 0)}")
    if errors:
        return errors

    records = _path_records(grid)
    endpoint_cells = {
        point
        for record in records
        for point in record["pair"]
    }
    both_clear = 0
    h_blocked = 0
    selected_sets = []
    for record in records:
        a, b = record["pair"]
        if a[0] == b[0] or a[1] == b[1]:
            errors.append(f"color {record['color']} endpoints must be diagonal")
        both_clear += int(record["h_clear"] and record["v_clear"])
        h_blocked += int(not record["h_clear"])
        crossed_endpoints = (set(record["selected"]) - set(record["pair"])) & endpoint_cells
        if crossed_endpoints:
            errors.append(
                f"color {record['color']} selected path crosses another endpoint: "
                f"{sorted(crossed_endpoints)}"
            )
        selected_sets.append(set(record["selected"]))

    if both_clear == 0:
        errors.append("need at least one pair with both elbows clear to teach H preference")
    if h_blocked == 0:
        errors.append("need at least one H-blocked pair to teach vertical selection")
    if not any(
        selected_sets[i] & selected_sets[j]
        for i in range(len(selected_sets))
        for j in range(i + 1, len(selected_sets))
    ):
        errors.append("selected paths must overlap to expose overwrite order")
    return errors


def strict_canonical_like(grid):
    """Lawful instances on the declared canonical-profile teaching manifold."""
    return self_check(grid)
