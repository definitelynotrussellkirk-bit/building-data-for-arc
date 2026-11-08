"""Generator for ARC task 8d510a79 / canonical id 91ba301501c5.

A full gray row divides the grid. Blue cells extend vertically *away* from
that row; red cells extend vertically *toward* it.  Every generated instance
shows all four color/side branches, while a controlled boundary-blue case
teaches that a ray may legitimately have length zero at the grid edge.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "91ba301501c5"
VERSION = "2.0.0"
TASK_ID = "91ba301501c5"
RULE_HASH = "c850a30c9e63"
SUMMARY = "Horizontal gray line; blue extends away and red extends toward it."

GRID_PROFILES = {
    "canonical": (10, 10),
    "wide": (10, 14),
    "tall": (14, 10),
}
LINE_POSITIONS = ("upper", "mid", "center")

INVARIANTS = [
    "exactly one full gray(5) row and no off-line gray cells",
    "the gray line leaves at least two rows on each side",
    "blue(1) and red(2) both occur above and below the line",
    "red marks have a non-empty clear ray toward the gray line",
    "each side has a blue mark with a non-empty clear ray away from the line",
    "a blue mark may sit at its away-facing boundary and therefore extend zero cells",
    "marks on the same side occupy distinct columns",
]

AXES = {
    "grid_profile": {
        "type": "str",
        "default": "rng",
        "valid": "canonical|wide|tall",
    },
    "line_position": {
        "type": "str",
        "default": "rng",
        "valid": "upper|mid|center",
    },
    "n_blue": {
        "type": "int",
        "default": "difficulty-aware 3..5",
        "valid": "3..5",
    },
    "n_red": {
        "type": "int",
        "default": "difficulty-aware 2..5",
        "valid": "2..5",
    },
    "edge_blue": {
        "type": "bool",
        "default": "rng",
        "valid": "true|false",
    },
}


def _line_row(grid: list[list[int]]) -> int | None:
    rows = [r for r, row in enumerate(grid) if row and all(value == 5 for value in row)]
    return rows[0] if len(rows) == 1 else None


def _line_position_row(line_position: str, height: int) -> int:
    rows = {
        "upper": 3,
        "mid": height // 2 - 1,
        "center": height // 2,
    }
    try:
        return rows[line_position]
    except KeyError as exc:
        raise ValueError(f"unknown line position: {line_position!r}") from exc


def _direction(color: int, row: int, line_row: int, *, blue_mode: str = "away", red_mode: str = "toward") -> int:
    above = row < line_row
    mode = blue_mode if color == 1 else red_mode
    if mode == "away":
        return -1 if above else 1
    if mode == "toward":
        return 1 if above else -1
    raise ValueError(f"unknown ray mode: {mode!r}")


def _ray_length(grid: list[list[int]], color: int, row: int, col: int, line_row: int) -> int:
    direction = _direction(color, row, line_row)
    rr = row + direction
    length = 0
    while 0 <= rr < len(grid) and grid[rr][col] == 0:
        length += 1
        rr += direction
    return length


def _positive_rows(color: int, side: str, line_row: int, height: int) -> list[int]:
    if color == 1 and side == "above":
        return list(range(1, line_row))
    if color == 1 and side == "below":
        return list(range(line_row + 1, height - 1))
    if color == 2 and side == "above":
        return list(range(0, line_row - 1))
    if color == 2 and side == "below":
        return list(range(line_row + 2, height))
    raise ValueError((color, side))


def _add_balanced_extras(specs: list[dict[str, object]], color: int, count: int, rng) -> None:
    """Add positive-ray marks to the currently less populated side."""
    for _ in range(count):
        counts = {
            side: sum(spec["side"] == side for spec in specs)
            for side in ("above", "below")
        }
        if counts["above"] == counts["below"]:
            side = rng.choice(("above", "below"))
        else:
            side = min(counts, key=counts.get)
        specs.append({"color": color, "side": side, "kind": "positive"})


def _build_specs(n_blue: int, n_red: int, edge_blue: bool, rng) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = [
        {"color": 1, "side": "above", "kind": "positive", "tag": "blue_above"},
        {"color": 1, "side": "below", "kind": "positive", "tag": "blue_below"},
        {"color": 2, "side": "above", "kind": "positive", "tag": "red_above"},
        {"color": 2, "side": "below", "kind": "positive", "tag": "red_below"},
    ]
    used_blue = 2
    if edge_blue:
        side = rng.choice(("above", "below"))
        specs.append({"color": 1, "side": side, "kind": "edge", "tag": "edge_blue"})
        used_blue += 1
    _add_balanced_extras(specs, 1, n_blue - used_blue, rng)
    _add_balanced_extras(specs, 2, n_red - 2, rng)
    return specs


def _assign_columns(specs: list[dict[str, object]], width: int, rng) -> None:
    """Use distinct columns per side and one deliberate cross-line shared column."""
    used = {"above": set(), "below": set()}
    by_tag = {spec.get("tag"): spec for spec in specs if spec.get("tag")}
    pair = rng.choice(
        (
            (by_tag["red_above"], by_tag["blue_below"]),
            (by_tag["blue_above"], by_tag["red_below"]),
        )
    )
    shared_col = rng.randrange(width)
    for spec in pair:
        spec["col"] = shared_col
        used[str(spec["side"])].add(shared_col)

    remaining = [spec for spec in specs if "col" not in spec]
    rng.shuffle(remaining)
    for spec in remaining:
        side = str(spec["side"])
        choices = [col for col in range(width) if col not in used[side]]
        if not choices:
            raise RuntimeError(f"no free column on {side} side")
        col = rng.choice(choices)
        spec["col"] = col
        used[side].add(col)


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    messages: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid is empty"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is not rectangular"]
    bad_values = sorted({value for row in grid for value in row if value not in {0, 1, 2, 5}})
    if bad_values:
        messages.append(f"unexpected colors: {bad_values}")

    line_row = _line_row(grid)
    if line_row is None:
        return messages + ["expected exactly one full gray row"]
    if not (2 <= line_row <= height - 3):
        messages.append("gray row does not leave two rows on each side")
    if any(grid[r][c] == 5 for r in range(height) for c in range(width) if r != line_row):
        messages.append("gray cell occurs off the divider row")

    locations = {1: [], 2: []}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in locations:
                locations[value].append((r, c))

    if len(locations[1]) < 3:
        messages.append("fewer than three blue marks")
    if len(locations[2]) < 2:
        messages.append("fewer than two red marks")

    for color in (1, 2):
        for side in ("above", "below"):
            side_marks = [(r, c) for r, c in locations[color] if (r < line_row) == (side == "above")]
            if not side_marks:
                messages.append(f"color-{color} missing on {side} side")

    for side in ("above", "below"):
        side_marks = [
            (r, c)
            for color in (1, 2)
            for r, c in locations[color]
            if (r < line_row) == (side == "above")
        ]
        columns = [c for _, c in side_marks]
        if len(columns) != len(set(columns)):
            messages.append(f"multiple marks share a column on {side} side")

    for r, c in locations[2]:
        if _ray_length(grid, 2, r, c, line_row) == 0:
            messages.append("red mark has no visible toward-line extension")
            break

    for side in ("above", "below"):
        blue = [(r, c) for r, c in locations[1] if (r < line_row) == (side == "above")]
        positive = [(r, c) for r, c in blue if _ray_length(grid, 1, r, c, line_row) > 0]
        if not positive:
            messages.append(f"no blue mark on {side} side has a visible away extension")
        for r, c in blue:
            if _ray_length(grid, 1, r, c, line_row) == 0:
                boundary = r == 0 if side == "above" else r == height - 1
                if not boundary:
                    messages.append("blue mark is blocked in its away direction")
                    break
    return messages


def observe_overrides(grid):
    """Recover every exact declared axis from the returned input grid."""
    line_row = _line_row(grid)
    if line_row is None:
        raise ValueError("cannot observe overrides on a grid without one divider")
    dims = (len(grid), len(grid[0]))
    inverse_profiles = {value: key for key, value in GRID_PROFILES.items()}
    if dims not in inverse_profiles:
        raise ValueError(f"unknown grid profile dimensions: {dims}")
    observed_positions = {
        _line_position_row(name, len(grid)): name
        for name in LINE_POSITIONS
    }
    if line_row not in observed_positions:
        raise ValueError(f"unknown line position row: {line_row}")
    line_position = observed_positions[line_row]
    return {
        "grid_profile": inverse_profiles[dims],
        "line_position": line_position,
        "n_blue": sum(value == 1 for row in grid for value in row),
        "n_red": sum(value == 2 for row in grid for value in row),
        "edge_blue": any(
            grid[row][col] == 1
            for row in (0, len(grid) - 1)
            for col in range(len(grid[0]))
        ),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("grid_profile", tuple(GRID_PROFILES))
    height, width = GRID_PROFILES[profile]
    line_position = ctx.draw_choice("line_position", LINE_POSITIONS)
    line_row = _line_position_row(line_position, height)
    n_blue = ctx.draw_int_diff("n_blue", 3, 5)
    n_red = ctx.draw_int_diff("n_red", 2, 5)
    edge_blue = ctx.draw_choice("edge_blue", (False, True))
    rng = ctx.draw_rng("placement")

    grid = full_grid(height, width, 0)
    grid[line_row] = [5] * width
    specs = _build_specs(n_blue, n_red, bool(edge_blue), rng)
    _assign_columns(specs, width, rng)

    for spec in specs:
        color = int(spec["color"])
        side = str(spec["side"])
        if spec["kind"] == "edge":
            row = 0 if side == "above" else height - 1
        else:
            rows = _positive_rows(color, side, line_row, height)
            row = rng.choice(rows)
        grid[row][int(spec["col"])] = color

    problems = self_check(grid, difficulty=difficulty)
    if problems:
        raise RuntimeError("generated invalid grid: " + "; ".join(problems))
    return grid


def _apply_variant(grid: list[list[int]], *, blue_mode: str, red_mode: str) -> list[list[int]]:
    line_row = _line_row(grid)
    if line_row is None:
        return [list(row) for row in grid]
    result = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color not in (1, 2):
                continue
            direction = _direction(
                color,
                r,
                line_row,
                blue_mode=blue_mode,
                red_mode=red_mode,
            )
            rr = r + direction
            while 0 <= rr < height and grid[rr][c] == 0:
                result[rr][c] = color
                rr += direction
    return result


def _blue_toward_rival(grid):
    return _apply_variant(grid, blue_mode="toward", red_mode="toward")


def _red_away_rival(grid):
    return _apply_variant(grid, blue_mode="away", red_mode="away")


def _has_positive_branch(grid, color: int, side: str) -> bool:
    line_row = _line_row(grid)
    if line_row is None:
        return False
    return any(
        _ray_length(grid, color, r, c, line_row) > 0
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color and ((r < line_row) == (side == "above"))
    )


def strict_canonical_like(grid):
    """Return reasons when a grid is outside this task's lawful input manifold."""
    return self_check(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "blue_above_away": lambda grid: _has_positive_branch(grid, 1, "above"),
    "blue_below_away": lambda grid: _has_positive_branch(grid, 1, "below"),
    "red_above_toward": lambda grid: _has_positive_branch(grid, 2, "above"),
    "red_below_toward": lambda grid: _has_positive_branch(grid, 2, "below"),
}
SEMANTIC_RIVALS = {
    "blue_toward": _blue_toward_rival,
    "red_away": _red_away_rival,
}
WITNESS_RIVALS = {
    "blue_above_away": ["blue_toward"],
    "blue_below_away": ["blue_toward"],
    "red_above_toward": ["red_away"],
    "red_below_toward": ["red_away"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
MIN_STRICT_FRAC = 0.95
EXAMPLES_NEEDED = 2


def lesson_identifiable(demos, query):
    """Reject a lesson when a declared wrong rule fits all demos but changes the query."""
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(demo["input"]) == demo["output"]
                for demo in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} could not be evaluated: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demo but changes the query answer")
    return reasons

