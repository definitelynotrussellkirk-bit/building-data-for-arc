"""Crossing-band generator for task 7b0cb3b9a618.

A scene is made by painting distinct-coloured full horizontal and vertical
bands on a zero background.  Their paint order is visible at crossings.  The
last band is uninterrupted ("clean"):

* a clean horizontal band is itself the answer;
* when the clean band is vertical, it is one column wide and interrupts a
  nearly uniform horizontal band, so its colour is the unique anomaly.

The six scheduled profiles exactly cover the canonical (height, width, palette
size) triples.  Every profile is emitted once with each winner orientation in a
12-sample cycle.  ``clean_color`` is the sole public control because it is the
only independent quantity this task can recover exactly from every valid grid.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "7b0cb3b9a618"
TASK_ID = "7b0cb3b9a618"
VERSION = "2.0.0"
RULE_HASH = "20196c190154"
SUMMARY = "Layered crossing bands; output the uninterrupted band's colour."
EXPECTED_OUTPUT_CODOMAIN = 9
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is literal color 0",
    "every nonzero color names one contiguous full horizontal or vertical band",
    "band crossings encode an acyclic paint order",
    "exactly one answer-bearing band is uninterrupted",
    "a vertical winner is width 1, is not column 0, and is the anomaly in a dirty row",
]

# (name, height, width, number of nonzero band colours)
PROFILES = (
    ("tiny_3x3_c3", 3, 3, 2),
    ("h8_w12_c5", 8, 12, 4),
    ("h9_w11_c5", 9, 11, 4),
    ("h11_w11_c6", 11, 11, 5),
    ("h11_w12_c6", 11, 12, 5),
    ("h11_w13_c5", 11, 13, 4),
)
PROFILE_BY_SHAPE = {(h, w): (name, nonzero) for name, h, w, nonzero in PROFILES}
PROFILE_NAMES = tuple(name for name, _, _, _ in PROFILES)
SCHEDULE_PROFILES = tuple(
    f"{name}:{orientation}"
    for name in PROFILE_NAMES
    for orientation in ("horizontal", "vertical")
)

AXES = {
    "clean_color": {
        "type": "color",
        "default": "keyed draw from 1..9",
        "valid": "1..9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic profile/orientation slot for audit tooling."""
    del seed, difficulty
    profile = PROFILES[(sample_index // 2) % len(PROFILES)][0]
    orientation = "horizontal" if sample_index % 2 == 0 else "vertical"
    return f"{profile}:{orientation}"


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if "clean_color" in overrides:
        value = overrides["clean_color"]
        if type(value) is not int or not 1 <= value <= 9:
            raise ValueError("clean_color must be a literal integer in 1..9")


def _profile(sample_index: int) -> tuple[str, int, int, int]:
    return PROFILES[(sample_index // 2) % len(PROFILES)]


def _choose_widths(length: int, colors: list[int], *, force_single: set[int], rng, difficulty) -> dict[int, int]:
    """Choose canonical-like widths while retaining at least three clear lines.

    The 3x3 profile necessarily retains two clear lines around its one band.
    Larger profiles use widths 1 or 2; leaving >=3 clear lines makes each
    band's orientation observable from its bounding box even after crossings.
    """
    widths = {color: 1 for color in colors}
    if length == 3:
        return widths

    capacity = max(0, (length - 3) - len(colors))
    probability = {"easy": 0.25, "medium": 0.55, "hard": 0.80}.get(difficulty, 0.55)
    candidates = [color for color in colors if color not in force_single]
    rng.shuffle(candidates)
    for color in candidates:
        if capacity <= 0:
            break
        if rng.random() < probability:
            widths[color] += 1
            capacity -= 1
    return widths


def _place_spans(length: int, colors: list[int], widths: dict[int, int], rng) -> dict[int, tuple[int, ...]]:
    """Place non-overlapping contiguous spans with random background gaps."""
    order = list(colors)
    rng.shuffle(order)
    occupied = sum(widths[color] for color in order)
    if occupied >= length:
        raise ValueError("band spans leave no background line")

    gaps = [0] * (len(order) + 1)
    for _ in range(length - occupied):
        gaps[rng.randrange(len(gaps))] += 1

    cursor = gaps[0]
    spans: dict[int, tuple[int, ...]] = {}
    for index, color in enumerate(order):
        width = widths[color]
        spans[color] = tuple(range(cursor, cursor + width))
        cursor += width + gaps[index + 1]
    return spans


def _reverse_spans(spans: dict[int, tuple[int, ...]], length: int) -> dict[int, tuple[int, ...]]:
    return {
        color: tuple(sorted(length - 1 - position for position in positions))
        for color, positions in spans.items()
    }


def _paint_horizontal(grid: list[list[int]], rows: tuple[int, ...], color: int) -> None:
    width = len(grid[0])
    for row in rows:
        for col in range(width):
            grid[row][col] = color


def _paint_vertical(grid: list[list[int]], cols: tuple[int, ...], color: int) -> None:
    height = len(grid)
    for col in cols:
        for row in range(height):
            grid[row][col] = color


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
    clean_color = ctx.draw_color("clean_color", exclude={0})
    _, height, width, nonzero_colors = _profile(sample_index)
    winner_orientation = "horizontal" if sample_index % 2 == 0 else "vertical"

    palette_rng = ctx.draw_rng("palette")
    other_colors = palette_rng.sample(
        [color for color in range(1, 10) if color != clean_color],
        nonzero_colors - 1,
    )
    palette_rng.shuffle(other_colors)

    # At least one band of each orientation.  The split is hidden nuisance
    # variation rather than a public axis because it is not independently
    # recoverable from the output label.
    split_rng = ctx.draw_rng("orientation_split")
    horizontal_count = split_rng.randint(1, nonzero_colors - 1)
    if winner_orientation == "horizontal":
        horizontal_colors = [clean_color, *other_colors[: horizontal_count - 1]]
        vertical_colors = other_colors[horizontal_count - 1 :]
    else:
        horizontal_colors = other_colors[:horizontal_count]
        vertical_colors = [clean_color, *other_colors[horizontal_count:]]

    h_rng = ctx.draw_rng("horizontal_spans")
    v_rng = ctx.draw_rng("vertical_spans")
    h_widths = _choose_widths(
        height,
        horizontal_colors,
        force_single=set(),
        rng=h_rng,
        difficulty=difficulty,
    )
    v_widths = _choose_widths(
        width,
        vertical_colors,
        force_single={clean_color} if winner_orientation == "vertical" else set(),
        rng=v_rng,
        difficulty=difficulty,
    )
    h_spans = _place_spans(height, horizontal_colors, h_widths, h_rng)
    v_spans = _place_spans(width, vertical_colors, v_widths, v_rng)

    # The Racket fallback reads column 0 as the dirty row's major colour, so a
    # vertical winner must be elsewhere.  Reflection preserves every span and
    # avoids rejection sampling.
    if winner_orientation == "vertical" and v_spans[clean_color] == (0,):
        v_spans = _reverse_spans(v_spans, width)

    grid = full_grid(height, width, 0)
    order_rng = ctx.draw_rng("paint_order")
    if winner_orientation == "horizontal":
        # Every nonwinner horizontal band is interrupted by a later vertical;
        # only the final horizontal band remains clean.
        early_horizontal = [color for color in horizontal_colors if color != clean_color]
        order_rng.shuffle(early_horizontal)
        order_rng.shuffle(vertical_colors)
        for color in early_horizontal:
            _paint_horizontal(grid, h_spans[color], color)
        for color in vertical_colors:
            _paint_vertical(grid, v_spans[color], color)
        _paint_horizontal(grid, h_spans[clean_color], clean_color)
    else:
        # Every nonwinner vertical is interrupted by a later horizontal.  The
        # final width-1 vertical creates the single anomaly used by the rule.
        early_vertical = [color for color in vertical_colors if color != clean_color]
        order_rng.shuffle(early_vertical)
        order_rng.shuffle(horizontal_colors)
        for color in early_vertical:
            _paint_vertical(grid, v_spans[color], color)
        for color in horizontal_colors:
            _paint_horizontal(grid, h_spans[color], color)
        _paint_vertical(grid, v_spans[clean_color], clean_color)

    errors = self_check(grid)
    if errors:  # Construction failures must be loud; never return retry residue.
        raise AssertionError(f"constructed invalid crossing-band grid: {errors}")
    return grid


def _is_contiguous(values: list[int]) -> bool:
    return bool(values) and values == list(range(values[0], values[-1] + 1))


def _clean_rows(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row_index, row[0])
        for row_index, row in enumerate(grid)
        if row[0] != 0 and len(set(row)) == 1
    ]


def _clean_cols(grid: list[list[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    result = []
    for col in range(width):
        values = [grid[row][col] for row in range(height)]
        if values[0] != 0 and len(set(values)) == 1:
            result.append((col, values[0]))
    return result


def _acyclic(nodes: set[int], edges: set[tuple[int, int]]) -> bool:
    outgoing: dict[int, set[int]] = {node: set() for node in nodes}
    indegree = {node: 0 for node in nodes}
    for earlier, later in edges:
        if later not in outgoing[earlier]:
            outgoing[earlier].add(later)
            indegree[later] += 1
    queue = deque(node for node in nodes if indegree[node] == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for later in outgoing[node]:
            indegree[later] -= 1
            if indegree[later] == 0:
                queue.append(later)
    return visited == len(nodes)


def _analysis(grid) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {
        "errors": errors,
        "orientation": None,
        "answer": None,
        "horizontal": {},
        "vertical": {},
        "edges": set(),
    }

    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a nonempty row sequence")
        return result
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        errors.append("every row must be a nonempty sequence")
        return result
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be literal ARC color integers 0..9")
        return result

    height = len(grid)
    profile = PROFILE_BY_SHAPE.get((height, width))
    if profile is None:
        errors.append(f"shape {height}x{width} is outside the six canonical profiles")
        return result
    profile_name, expected_nonzero = profile
    colors = {value for row in grid for value in row}
    if 0 not in colors:
        errors.append("background color 0 must remain visible")
    nonzero = sorted(colors - {0})
    if len(nonzero) != expected_nonzero:
        errors.append(
            f"{profile_name} requires {expected_nonzero} nonzero band colors; found {len(nonzero)}"
        )
    if errors:
        return result

    cells: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value:
                cells[value].append((row, col))

    horizontal: dict[int, tuple[int, ...]] = {}
    vertical: dict[int, tuple[int, ...]] = {}
    for color in nonzero:
        positions = cells[color]
        rows = sorted({row for row, _ in positions})
        cols = sorted({col for _, col in positions})
        bbox_height = rows[-1] - rows[0] + 1
        bbox_width = cols[-1] - cols[0] + 1
        if bbox_width > bbox_height:
            if not _is_contiguous(rows):
                errors.append(f"horizontal color {color} has a noncontiguous row span")
            if len(rows) > 3:
                errors.append(f"horizontal color {color} is thicker than canonical bands")
            horizontal[color] = tuple(rows)
        elif bbox_height > bbox_width:
            if not _is_contiguous(cols):
                errors.append(f"vertical color {color} has a noncontiguous column span")
            if len(cols) > 3:
                errors.append(f"vertical color {color} is thicker than canonical bands")
            vertical[color] = tuple(cols)
        else:
            errors.append(f"color {color} has an orientation-ambiguous square footprint")

    if not horizontal or not vertical:
        errors.append("at least one horizontal and one vertical band are required")
    if errors:
        return result

    row_owner = [0] * height
    for color, rows in horizontal.items():
        for row in rows:
            if row_owner[row] not in (0, color):
                errors.append(f"horizontal bands overlap at row {row}")
            row_owner[row] = color
    col_owner = [0] * width
    for color, cols in vertical.items():
        for col in cols:
            if col_owner[col] not in (0, color):
                errors.append(f"vertical bands overlap at column {col}")
            col_owner[col] = color
    if 0 not in row_owner:
        errors.append("at least one background row is required")
    if 0 not in col_owner:
        errors.append("at least one background column is required")

    edges: set[tuple[int, int]] = set()
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            h_color, v_color = row_owner[row], col_owner[col]
            if not h_color and not v_color:
                if value != 0:
                    errors.append(f"cell ({row},{col}) lies outside every inferred band")
            elif h_color and not v_color:
                if value != h_color:
                    errors.append(f"horizontal band {h_color} is broken at ({row},{col})")
            elif v_color and not h_color:
                if value != v_color:
                    errors.append(f"vertical band {v_color} is broken at ({row},{col})")
            elif value == h_color:
                edges.add((v_color, h_color))
            elif value == v_color:
                edges.add((h_color, v_color))
            else:
                errors.append(f"crossing ({row},{col}) contains neither incident band color")

    if not _acyclic(set(nonzero), edges):
        errors.append("crossing choices imply a cyclic paint order")

    clean_rows = _clean_rows(grid)
    clean_cols = _clean_cols(grid)
    if clean_rows:
        clean_colors = {color for _, color in clean_rows}
        if len(clean_colors) != 1:
            errors.append("more than one horizontal band is clean")
        winner = clean_rows[0][1]
        winner_rows = {row for row, _ in clean_rows}
        if winner not in horizontal or winner_rows != set(horizontal.get(winner, ())):
            errors.append("clean rows do not equal one inferred horizontal band")
        if clean_cols:
            errors.append("a horizontal-winner scene must have no clean vertical band")
        if any((v_color, winner) not in edges for v_color in vertical):
            errors.append("the clean horizontal band is not visibly later than every vertical band")
        result["orientation"] = "horizontal"
        result["answer"] = winner
    else:
        if len(clean_cols) != 1:
            errors.append(f"vertical-winner scene requires exactly one clean column; found {len(clean_cols)}")
            winner = None
        else:
            winner_col, winner = clean_cols[0]
            if winner_col == 0:
                errors.append("vertical winner cannot occupy column 0")
            if winner not in vertical or vertical.get(winner) != (winner_col,):
                errors.append("clean column does not equal one width-1 vertical band")
            if any((h_color, winner) not in edges for h_color in horizontal):
                errors.append("the clean vertical band is not visibly later than every horizontal band")

            eligible: list[tuple[int, int]] = []
            for row_index, row_values in enumerate(grid):
                major = row_values[0]
                differences = [value for value in row_values if value != major]
                if major != 0 and len(differences) == 1:
                    eligible.append((row_index, differences[0]))
            if not eligible:
                errors.append("no dirty row has exactly one anomaly for the Racket fallback")
            elif eligible[0][1] != winner:
                errors.append("the first Racket-eligible dirty row points to the wrong color")
            result["orientation"] = "vertical"
            result["answer"] = winner

    result.update(
        profile=profile_name,
        horizontal=horizontal,
        vertical=vertical,
        edges=edges,
        row_owner=tuple(row_owner),
        col_owner=tuple(col_owner),
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


strict_canonical_like = self_check


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python spelling of the selected canonical Racket rule."""
    if not isinstance(grid, (list, tuple)) or not grid or not grid[0]:
        raise ValueError("empty grid")
    width = len(grid[0])
    for row in grid:
        value = row[0]
        if value != 0 and all(cell == value for cell in row[1:]):
            return [[value]]
    for row in grid:
        major = row[0]
        if major != 0 and sum(cell == major for cell in row) > width - 2:
            for value in row:
                if value != major:
                    return [[value]]
    raise ValueError("grid has neither a clean row nor an eligible dirty row")


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError(errors[0])
    return {"clean_color": rule_mirror(grid)[0][0]}


def _vertical_clean_band(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["orientation"] == "vertical"


def _uniform_row_only(grid) -> list[list[int]]:
    """Plausible wrong rule: use the row's majority, not its anomaly."""
    width = len(grid[0])
    for row in grid:
        value = row[0]
        if value != 0 and all(cell == value for cell in row[1:]):
            return [[value]]
    for row in grid:
        major = row[0]
        if major != 0 and sum(cell == major for cell in row) > width - 2:
            return [[major]]
    return [[0]]


SEMANTIC_WITNESSES = {
    "vertical_clean_band": _vertical_clean_band,
}
SEMANTIC_RIVALS = {
    "uniform_row_only": _uniform_row_only,
}
WITNESS_RIVALS = {
    "vertical_clean_band": ["uniform_row_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Any] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Name any declared rival that demos fail to refute but query needs."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the crossing-band rule")
    if reasons:
        return reasons
    if query["output"] != rule_mirror(query["input"]):
        return ["query output disagrees with the crossing-band rule"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} survives the demos but changes the query answer")
    return reasons
