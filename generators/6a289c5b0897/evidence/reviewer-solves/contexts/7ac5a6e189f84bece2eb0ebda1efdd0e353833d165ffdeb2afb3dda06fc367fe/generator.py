"""Input generator for ARC task 6a289c5b0897.

The unchanged Racket authority chooses the row-major first terminal as the
start and runs breadth-first search with neighbours ordered Up, Down, Left,
Right.  Ties are therefore meaningful: the canonical pairs admit other BFS
orders, so every three-sample curriculum cycle contains a generated tie that
separates UDLR from the strongest surviving left-first rival.  A staggered
second witness makes every four-pair window safe under leave-one-out query
rotation.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6a289c5b0897"
TASK_ID = GENERATOR_ID
VERSION = "4.0.1"
RULE_HASH = "d0e77b114425"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 4..6 by 5..8 grid contains gray(5) walls and exactly two terminals "
    "of one other color. Starting from the row-major first terminal, paint "
    "the BFS path selected by neighbour order Up, Down, Left, Right on an "
    "otherwise black output. Three scheduled profiles cover canonical scale, "
    "broad geometry, and a tie that distinguishes the ordered BFS rule. "
    "A staggered witness guarantees that rotating any one of four consecutive "
    "pairs into the query still leaves a counterexample in the demonstrations."
)

INVARIANTS = [
    "cells are 0 background, 5 walls, or exactly two copies of one terminal color",
    "the number of walls is never two, so gray cannot be mistaken for the terminal pair",
    "terminal distance is 3..10 and a shortest orthogonal path always exists",
    "row-major terminal order and U,D,L,R neighbour order determine tied shortest paths",
    "every three consecutive ordinary samples include a left-vs-down BFS tie witness",
    "every four consecutive samples include at least two such witnesses for query rotation",
]

AXES = {
    "h": {"type": "int", "default": "scheduled/difficulty-shaped", "valid": "4..6"},
    "w": {"type": "int", "default": "scheduled/difficulty-shaped", "valid": "5..8"},
    "wall_density": {
        "type": "float",
        "default": "scheduled/difficulty-shaped",
        "valid": "0.10..0.50",
    },
    "color": {
        "type": "int",
        "default": "canonical palette anchor or keyed RNG",
        "valid": "1|2|3|4|6|7|8",
    },
    "min_path_len": {
        "type": "int",
        "default": "scheduled/difficulty-shaped exact path length",
        "valid": "3..10",
    },
}

# Some advertised triples are geometrically impossible (for example 4x5 with
# path length 8).  The generator accepts every feasible combination and raises
# a structured ValueError for only these dimension/path incompatibilities.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    ("w", "min_path_len"),
    ("h", "w", "min_path_len"),
)

SCHEDULE_PROFILES = ("canonical_anchor", "broad", "order_witness")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_ENDPOINT_COLORS = (1, 2, 3, 4, 6, 7, 8)
_CANONICAL_COLORS = (2, 3, 4, 6)
_DIRS_UDLR = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIRS_LDRU = ((0, -1), (1, 0), (0, 1), (-1, 0))
_BANDS = ("easy", "medium", "hard")
_ALLOWED_OVERRIDES = frozenset(AXES)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic three-sample curriculum branch.

    A seed-dependent phase avoids globally aligning all lessons while preserving
    the key contract: every three consecutive sample indices cover all profiles.
    """
    _band(difficulty)
    return SCHEDULE_PROFILES[(int(sample_index) + int(seed) % 3) % 3]


def _requires_order_witness(seed: int, sample_index: int, profile: str) -> bool:
    """Guarantee two semantic witnesses in every four consecutive draws.

    The named profile preserves explicit curriculum coverage.  Independent
    parity staggering supplies the redundancy needed when any one of four
    materialized pairs is rotated into the held-out query.
    """
    return profile == "order_witness" or (int(seed) + int(sample_index)) % 2 == 0


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    for name, lo, hi in (("h", 4, 6), ("w", 5, 8), ("min_path_len", 3, 10)):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")

    value = overrides.get("color")
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, int) or value not in _ENDPOINT_COLORS:
            raise ValueError(f"color must be one of {_ENDPOINT_COLORS}")

    value = overrides.get("wall_density")
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("wall_density must be numeric in 0.10..0.50")
        if not 0.10 <= float(value) <= 0.50:
            raise ValueError(f"wall_density={value!r} outside 0.10..0.50")


def _incompatible(message: str, *axes: str) -> None:
    exc = ValueError(f"incompatible overrides: {message}")
    exc.incompatible_axes = tuple(axes)  # consumed by the override-contract checker
    raise exc


def _axis_choice(ctx, label: str, domain: Sequence[Any], default: Any, overrides: dict[str, Any]):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, tuple(domain))
    return ctx.draw_choice(label, (default,))


def _weighted_pairs(profile: str, band: str, feasible: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if profile == "canonical_anchor":
        preferred = [pair for pair in feasible if pair in ((5, 5), (5, 6))]
        if preferred:
            return preferred
    if band == "easy":
        favored = [pair for pair in feasible if pair[0] <= 5 and pair[1] <= 6]
    elif band == "hard":
        favored = [pair for pair in feasible if pair[0] >= 5 and pair[1] >= 7]
    else:
        favored = [pair for pair in feasible if pair[0] == 5]
    return feasible + favored * 5 if favored else feasible


def _draw_dimensions(ctx, profile: str, band: str, overrides: dict[str, Any]) -> tuple[int, int]:
    requested_h = overrides.get("h")
    requested_w = overrides.get("w")
    requested_min = overrides.get("min_path_len")
    feasible = [
        (h, w)
        for h in range(4, 7)
        for w in range(5, 9)
        if (requested_h is None or h == requested_h)
        and (requested_w is None or w == requested_w)
        and (requested_min is None or h + w - 2 >= requested_min)
    ]
    if not feasible:
        _incompatible(
            f"h={requested_h!r}, w={requested_w!r} cannot realize "
            f"min_path_len={requested_min!r}",
            "h",
            "w",
            "min_path_len",
        )
    default_h, default_w = ctx.draw_rng("dimension_pair").choice(
        _weighted_pairs(profile, band, feasible)
    )
    h = int(_axis_choice(ctx, "h", range(4, 7), default_h, overrides))
    w = int(_axis_choice(ctx, "w", range(5, 9), default_w, overrides))
    if requested_min is not None and h + w - 2 < requested_min:
        _incompatible(
            f"{h}x{w} has maximum terminal distance {h + w - 2}, "
            f"below min_path_len={requested_min}",
            "h",
            "w",
            "min_path_len",
        )
    return h, w


def _default_path_len(profile: str, band: str, h: int, w: int, rng) -> int:
    maximum = min(10, h + w - 2)
    if profile == "canonical_anchor" and (h, w) == (5, 5):
        return 6
    if profile == "canonical_anchor" and (h, w) == (5, 6):
        return 9
    if band == "easy":
        lo, hi = 3, min(5, maximum)
    elif band == "hard":
        lo, hi = min(6, maximum), maximum
    else:
        lo, hi = min(4, maximum), min(8, maximum)
    if hi < lo:
        lo = hi = maximum
    return rng.randint(lo, hi)


def _draw_path_len(ctx, profile: str, band: str, h: int, w: int, overrides: dict[str, Any]) -> int:
    maximum = min(10, h + w - 2)
    requested = overrides.get("min_path_len")
    if requested is not None and requested > maximum:
        _incompatible(
            f"{h}x{w} has maximum terminal distance {maximum}, "
            f"below min_path_len={requested}",
            "h",
            "w",
            "min_path_len",
        )
    default = _default_path_len(profile, band, h, w, ctx.draw_rng("path_length"))
    return int(_axis_choice(ctx, "min_path_len", range(3, maximum + 1), default, overrides))


def _draw_color(ctx, profile: str, overrides: dict[str, Any]) -> int:
    default_domain = _CANONICAL_COLORS if profile == "canonical_anchor" else _ENDPOINT_COLORS
    default = ctx.draw_rng("endpoint_color_default").choice(default_domain)
    return int(_axis_choice(ctx, "color", _ENDPOINT_COLORS, default, overrides))


def _draw_density(ctx, profile: str, band: str, overrides: dict[str, Any]) -> float:
    raw = overrides.get("wall_density")
    if raw is not None:
        value = float(raw)
        ctx._record("wall_density", value, from_override=True)
        return value
    if profile == "canonical_anchor":
        value = ctx.draw_rng("wall_density_value").choice((0.30, 0.32))
    else:
        lo, hi = {
            "easy": (0.10, 0.28),
            "medium": (0.18, 0.38),
            "hard": (0.28, 0.50),
        }[band]
        value = ctx.draw_rng("wall_density_value").uniform(lo, hi)
    return float(ctx._record("wall_density", float(value), from_override=False))


def _all_endpoint_pairs(h: int, w: int, distance: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    cells = [(r, c) for r in range(h) for c in range(w)]
    return [
        (left, right)
        for index, left in enumerate(cells)
        for right in cells[index + 1 :]
        if abs(left[0] - right[0]) + abs(left[1] - right[1]) == distance
    ]


def _monotone_path(start: tuple[int, int], goal: tuple[int, int], rng) -> list[tuple[int, int]]:
    row, col = start
    dr = 1 if goal[0] > row else -1
    dc = 1 if goal[1] > col else -1
    steps = [(dr, 0)] * abs(goal[0] - row) + [(0, dc)] * abs(goal[1] - col)
    rng.shuffle(steps)
    path = [start]
    for step_r, step_c in steps:
        row += step_r
        col += step_c
        path.append((row, col))
    if path[-1] != goal:
        raise RuntimeError("constructive monotone path missed its goal")
    return path


def _ordinary_geometry(h: int, w: int, distance: int, rng):
    pairs = _all_endpoint_pairs(h, w, distance)
    if not pairs:
        raise RuntimeError(f"no endpoint pair at distance {distance} in {h}x{w}")
    start, goal = rng.choice(pairs)
    path = _monotone_path(start, goal, rng)
    return start, goal, set(path)


def _order_witness_geometry(h: int, w: int, distance: int, rng):
    """Construct two shortest routes whose first step is Down versus Left."""
    vertical_options = [
        down
        for down in range(1, h)
        if 1 <= distance - down < w
    ]
    if not vertical_options:
        raise RuntimeError(f"cannot realize a two-axis witness of length {distance} in {h}x{w}")
    down = rng.choice(vertical_options)
    left = distance - down
    start = (rng.randint(0, h - down - 1), rng.randint(left, w - 1))
    goal = (start[0] + down, start[1] - left)

    down_cell = (start[0] + 1, start[1])
    left_cell = (start[0], start[1] - 1)
    merge = (start[0] + 1, start[1] - 1)
    tail = _monotone_path(merge, goal, rng)
    protected = {start, down_cell, left_cell, *tail}
    return start, goal, protected


def _paint_instance(
    h: int,
    w: int,
    color: int,
    wall_count: int,
    start: tuple[int, int],
    goal: tuple[int, int],
    protected: set[tuple[int, int]],
    rng,
) -> list[list[int]]:
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in protected
    ]
    if wall_count > len(candidates):
        raise RuntimeError(
            f"cannot place {wall_count} walls outside {len(protected)} protected cells"
        )
    walls = set(rng.sample(candidates, wall_count))
    grid = full_grid(h, w, 0)
    for r, c in walls:
        grid[r][c] = 5
    grid[start[0]][start[1]] = color
    grid[goal[0]][goal[1]] = color
    return grid


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    """Generate a deterministic lawful input and honor every feasible override."""
    _validate_overrides(overrides)
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx, profile, band, overrides)
    path_len = _draw_path_len(ctx, profile, band, h, w, overrides)
    color = _draw_color(ctx, profile, overrides)
    density = _draw_density(ctx, profile, band, overrides)
    wall_count = max(3, round(h * w * density))

    geometry_rng = ctx.draw_rng("protected_route")
    requires_witness = _requires_order_witness(seed, sample_index, profile)
    if requires_witness:
        start, goal, protected = _order_witness_geometry(h, w, path_len, geometry_rng)
    else:
        start, goal, protected = _ordinary_geometry(h, w, path_len, geometry_rng)
    grid = _paint_instance(
        h,
        w,
        color,
        wall_count,
        start,
        goal,
        protected,
        ctx.draw_rng("wall_positions"),
    )
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator produced an invalid grid: {errors}")
    if requires_witness and not _ordered_bfs_tie(grid):
        raise RuntimeError("constructive order witness failed to separate BFS orders")
    return grid


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["rows must be non-empty sequences"]
    width = len(grid[0])
    converted: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return None, ["grid must be rectangular"]
        clean: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, ["cells must be integer ARC colors in 0..9"]
            clean.append(int(value))
        converted.append(clean)
    return converted, []


def _endpoint_data(grid: Sequence[Sequence[int]]) -> tuple[int, tuple[int, int], tuple[int, int]]:
    counts = Counter(value for row in grid for value in row)
    endpoint_colors = [
        color
        for color, count in counts.items()
        if color not in (0, 5) and count == 2
    ]
    if len(endpoint_colors) != 1:
        raise ValueError(
            f"expected exactly one non-0/non-5 color appearing twice; found {endpoint_colors}"
        )
    color = endpoint_colors[0]
    if any(value not in (0, 5, color) for row in grid for value in row):
        raise ValueError("grid contains a foreground color outside 0, 5, and the terminal color")
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    return color, points[0], points[1]


def _ordered_path(
    grid: Sequence[Sequence[int]],
    directions: Iterable[tuple[int, int]],
) -> tuple[int, list[tuple[int, int]]]:
    color, start, goal = _endpoint_data(grid)
    h, w = len(grid), len(grid[0])
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            path: list[tuple[int, int]] = []
            cursor: tuple[int, int] | None = current
            while cursor is not None:
                path.append(cursor)
                cursor = previous[cursor]
            path.reverse()
            return color, path
        for dr, dc in directions:
            nxt = current[0] + dr, current[1] + dc
            if (
                0 <= nxt[0] < h
                and 0 <= nxt[1] < w
                and nxt not in previous
                and grid[nxt[0]][nxt[1]] in (0, color)
            ):
                previous[nxt] = current
                queue.append(nxt)
    return color, []


def _ordered_bfs_output(
    grid: Sequence[Sequence[int]],
    directions: Iterable[tuple[int, int]] = _DIRS_UDLR,
) -> list[list[int]]:
    color, path = _ordered_path(grid, directions)
    output = full_grid(len(grid), len(grid[0]), 0)
    for r, c in path:
        output[r][c] = color
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror of the pinned U,D,L,R Racket authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    return _ordered_bfs_output(grid, _DIRS_UDLR)


def _left_down_right_up_bfs(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Plausible wrong rule: BFS uses L,D,R,U instead of U,D,L,R."""
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    return _ordered_bfs_output(grid, _DIRS_LDRU)


def _analysis(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    facts: dict[str, Any] = {"errors": errors}
    if converted is None:
        return facts
    h, w = len(converted), len(converted[0])
    facts.update({"grid": converted, "h": h, "w": w})
    if not 4 <= h <= 6:
        errors.append("grid height must be in 4..6")
    if not 5 <= w <= 8:
        errors.append("grid width must be in 5..8")
    try:
        color, start, goal = _endpoint_data(converted)
    except ValueError as exc:
        errors.append(str(exc))
        return facts
    facts.update({"color": color, "start": start, "goal": goal})

    wall_count = sum(value == 5 for row in converted for value in row)
    facts["wall_count"] = wall_count
    if wall_count == 2:
        errors.append("gray wall count must not be two (it would compete with the terminal pair)")
    if not 3 <= wall_count <= round(h * w * 0.50):
        errors.append(
            f"wall count {wall_count} outside the declared density envelope "
            f"3..{round(h * w * 0.50)}"
        )

    _, path = _ordered_path(converted, _DIRS_UDLR)
    facts["path"] = path
    facts["path_len"] = len(path) - 1 if path else None
    if not path:
        errors.append("no orthogonal terminal path through 0s")
    elif not 3 <= len(path) - 1 <= 10:
        errors.append(f"shortest path length {len(path) - 1} outside 3..10")
    return facts


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept exactly the lawful declared sampler manifold, including canonicals."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact non-float axis directly from returned pixels."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError(facts["errors"][0])
    return {
        "h": facts["h"],
        "w": facts["w"],
        "color": facts["color"],
        "min_path_len": facts["path_len"],
    }


def _ordered_bfs_tie(grid: Any) -> bool:
    try:
        return rule_mirror(grid) != _left_down_right_up_bfs(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "ordered_bfs_tie": _ordered_bfs_tie,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "left_down_right_up_bfs": _left_down_right_up_bfs,
}
WITNESS_RIVALS = {
    "ordered_bfs_tie": ["left_down_right_up_bfs"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Reject a lesson only when a declared rival survives demos and changes query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with ordered BFS")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
        return reasons
    query_truth = rule_mirror(query["input"])
    if "output" in query and query["output"] != query_truth:
        reasons.append("query output disagrees with ordered BFS")

    if reasons or len(valid_demos) != len(demos):
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in valid_demos)
            differs = rival(query["input"]) != query_truth
        except (TypeError, ValueError) as exc:
            reasons.append(f"competing rule {name!r} raised: {exc}")
            continue
        if survives and differs:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named malformed grids for the defect linter and future maintainers."""
    valid = generate(
        19,
        2,
        difficulty="medium",
        h=5,
        w=6,
        color=3,
        min_path_len=6,
        wall_density=0.30,
    )
    facts = _analysis(valid)
    color, start, goal = facts["color"], facts["start"], facts["goal"]
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_terminal = deepcopy(valid)
    missing_terminal[start[0]][start[1]] = 0
    fixtures.append(("missing_terminal", missing_terminal))

    third_terminal = deepcopy(valid)
    zero = next(
        (r, c)
        for r, row in enumerate(third_terminal)
        for c, value in enumerate(row)
        if value == 0
    )
    third_terminal[zero[0]][zero[1]] = color
    fixtures.append(("third_terminal", third_terminal))

    foreign_color = deepcopy(valid)
    zero = next(
        (r, c)
        for r, row in enumerate(foreign_color)
        for c, value in enumerate(row)
        if value == 0
    )
    foreign_color[zero[0]][zero[1]] = 9 if color != 9 else 8
    fixtures.append(("foreign_color", foreign_color))

    two_walls = full_grid(4, 5, 0)
    two_walls[0][0] = color
    two_walls[3][4] = color
    two_walls[0][2] = two_walls[2][2] = 5
    fixtures.append(("two_walls", two_walls))

    blocked = full_grid(4, 5, 0)
    blocked[0][0] = color
    blocked[3][4] = color
    for c in range(5):
        blocked[1][c] = 5
    fixtures.append(("blocked_path", blocked))

    ragged = deepcopy(valid)
    ragged[-1] = ragged[-1][:-1]
    fixtures.append(("ragged", ragged))
    return fixtures
