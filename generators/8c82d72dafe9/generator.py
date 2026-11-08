"""Generator for ``8c82d72dafe9`` — matching corners become borders.

The canonical Racket authority scans colors in row-major first-occurrence order.
A color qualifies only when it appears exactly twice in different rows and
columns.  Its two cells are opposite corners of an axis-aligned rectangle; the
full border is painted in that color on top of the original input.  Non-pair
colors and exactly-two collinear colors are distractors.  When qualifying
borders intersect, the later first-occurring qualifying color wins.

The five-slot curriculum repeats two precedence directions, three collinear
negative controls, and preserved non-pair distractors.  Every four-demo plus
one-query cyclic window remains identifiable under every query rotation against
the declared rivals.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8c82d72dafe9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "70532d39072c"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero-background grid, every nonzero color appearing exactly twice "
    "in different rows and columns marks opposite corners of a rectangle. "
    "Paint that rectangle's complete border in the same color while preserving "
    "all other input cells. Exactly-two collinear colors and colors with other "
    "multiplicities are distractors. Intersecting borders are processed in "
    "row-major first-occurrence color order, so the later qualifying color wins."
)

INVARIANTS = [
    "the grid is rectangular and contains literal ARC colors 0..9",
    "at least one nonzero color appears exactly twice at diagonal corners",
    "ordinary lessons contain one or two connected non-pair distractor colors",
    "some lessons contain an exactly-two collinear negative control",
    "the first two generated qualifying rectangles overlap at border cells",
    "both higher-color and lower-color overlap winners occur in each schedule period",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9..18", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "scheduled 10..18", "valid": "10..18"},
    "n_rects": {"type": "int", "default": "scheduled 2..4", "valid": "1..4"},
    "n_nonpair": {"type": "int", "default": "scheduled 1..2", "valid": "0..2"},
    "n_collinear": {"type": "int", "default": "scheduled 0..1", "valid": "0..1"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_higher",
    "collinear_lower",
    "collinear_higher",
    "canonical_lower",
    "mixed_higher",
)
_CANONICAL_SHAPES = ((10, 12), (11, 11), (9, 13), (12, 10), (10, 10))

Grid = list[list[int]]
Point = tuple[int, int]
Box = tuple[int, int, int, int]

# Each 9x10 template has exactly one overlapping pair (boxes 0 and 1), plus
# two disjoint boxes.  Reflections and offsets preserve that contract.
_BASE_BOX_VARIANTS: tuple[tuple[Box, ...], ...] = (
    ((1, 1, 4, 5), (3, 3, 7, 8), (5, 0, 8, 2), (0, 6, 2, 9)),
    ((1, 2, 5, 6), (3, 0, 7, 4), (0, 7, 2, 9), (6, 6, 8, 9)),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic five-slot teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")


def _draw_axis(ctx, overrides: dict[str, Any], name: str, lo: int, hi: int, default: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return int(ctx.draw_choice(name, (default,)))


def _profile_defaults(seed: int, sample_index: int, difficulty: Any) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index, difficulty)
    selector = (int(seed) * 29 + int(sample_index) * 43) % 997
    relation = "lower" if profile.endswith("lower") else "higher"
    if profile.startswith("canonical"):
        height, width = _CANONICAL_SHAPES[selector % len(_CANONICAL_SHAPES)]
        return {
            "profile": profile,
            "relation": relation,
            "grid_h": height,
            "grid_w": width,
            "n_rects": 2,
            "n_nonpair": 1,
            "n_collinear": 0,
        }
    if difficulty == "easy":
        height, width, rects = 9 + selector % 3, 10 + (selector // 3) % 3, 2
    elif difficulty == "hard":
        height, width, rects = 15 + selector % 4, 15 + (selector // 3) % 4, 4
    else:
        height, width, rects = 11 + selector % 4, 12 + (selector // 3) % 4, 3
    return {
        "profile": profile,
        "relation": relation,
        "grid_h": height,
        "grid_w": width,
        "n_rects": rects,
        "n_nonpair": 2 if profile == "mixed_higher" else 1,
        "n_collinear": 1,
    }


def _grid_errors(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return len(grid), width, [f"ARC grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _positions_by_color(grid: Grid) -> dict[int, list[Point]]:
    positions: dict[int, list[Point]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))
    return positions


def _bbox_border(cells: list[Point] | tuple[Point, Point]) -> set[Point]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _qualifying_rectangles(grid: Grid) -> list[tuple[int, list[Point]]]:
    result = []
    for color, cells in _positions_by_color(grid).items():
        if len(cells) != 2:
            continue
        if cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]:
            continue
        result.append((color, cells))
    return result


def _collinear_pairs(grid: Grid) -> list[tuple[int, list[Point]]]:
    result = []
    for color, cells in _positions_by_color(grid).items():
        if len(cells) == 2 and (
            cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]
        ):
            result.append((color, cells))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the full canonical rule domain, including preserved distractors."""
    del difficulty
    _height, _width, errors = _grid_errors(grid)
    if errors:
        return errors
    rects = _qualifying_rectangles(grid)
    if not rects:
        return ["at least one color must appear exactly twice at diagonal corners"]

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        for axis in AXES:
            if axis in meta:
                requested[axis] = meta[axis]
    if requested:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            return [str(exc)]
        for axis, expected in requested.items():
            if axis in observed and expected is not None and observed[axis] != expected:
                errors.append(f"{axis} requested {expected!r}, observed {observed[axis]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical-supported teaching manifold used by ordinary lessons."""
    errors = list(self_check(grid))
    if errors:
        return errors
    positions = _positions_by_color(grid)
    rect_count = len(_qualifying_rectangles(grid))
    collinear_count = len(_collinear_pairs(grid))
    nonpair = [cells for cells in positions.values() if len(cells) != 2]
    if not 2 <= rect_count <= 4:
        errors.append(f"teaching scenes need 2..4 diagonal rectangle pairs, found {rect_count}")
    if not 0 <= collinear_count <= 1:
        errors.append(f"teaching scenes allow at most one collinear exact pair, found {collinear_count}")
    if not 1 <= len(nonpair) <= 2:
        errors.append(f"teaching scenes need one or two non-pair distractor colors, found {len(nonpair)}")
    bad_counts = sorted(len(cells) for cells in nonpair if len(cells) not in (3, 4))
    if bad_counts:
        errors.append(f"teaching non-pair distractors must have 3 or 4 cells, found {bad_counts}")
    return errors


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; Racket remains the authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("rule_mirror expects a lawful task scene: " + "; ".join(errors))
    out = [list(row) for row in grid]
    # Dict insertion order is row-major first occurrence, matching color-order.
    for color, cells in _positions_by_color(grid).items():
        if len(cells) != 2:
            continue
        if cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]:
            continue
        for r, c in _bbox_border(cells):
            out[r][c] = color
    return out


def observe_overrides(grid: Grid) -> dict[str, int]:
    _height, _width, errors = _grid_errors(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    positions = _positions_by_color(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_rects": len(_qualifying_rectangles(grid)),
        "n_nonpair": sum(1 for cells in positions.values() if len(cells) != 2),
        "n_collinear": len(_collinear_pairs(grid)),
    }


def _transform_box(box: Box, *, flip_rows: bool, flip_cols: bool, row_offset: int, col_offset: int) -> Box:
    r0, c0, r1, c1 = box
    if flip_rows:
        r0, r1 = 8 - r1, 8 - r0
    if flip_cols:
        c0, c1 = 9 - c1, 9 - c0
    return r0 + row_offset, c0 + col_offset, r1 + row_offset, c1 + col_offset


def _draw_boxes(ctx, height: int, width: int, count: int) -> list[Box]:
    rng = ctx.draw_rng("rectangle_layout")
    template = list(rng.choice(_BASE_BOX_VARIANTS))
    flip_rows = bool(rng.randrange(2))
    flip_cols = bool(rng.randrange(2))
    row_offset = rng.randint(0, height - 9)
    col_offset = rng.randint(0, width - 10)
    boxes = [
        _transform_box(
            box,
            flip_rows=flip_rows,
            flip_cols=flip_cols,
            row_offset=row_offset,
            col_offset=col_offset,
        )
        for box in template[:count]
    ]
    return boxes


def _corners(box: Box, anti: bool) -> tuple[Point, Point]:
    r0, c0, r1, c1 = box
    return ((r0, c1), (r1, c0)) if anti else ((r0, c0), (r1, c1))


def _shape_candidates(free: set[Point], height: int, width: int, size: int) -> list[frozenset[Point]]:
    candidates: set[frozenset[Point]] = set()
    for r in range(height - 1):
        for c in range(width - 1):
            block = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            if not set(block) <= free:
                continue
            if size == 4:
                candidates.add(frozenset(block))
            else:
                for omit in range(4):
                    candidates.add(frozenset(point for index, point in enumerate(block) if index != omit))
    return sorted(candidates, key=lambda cells: tuple(sorted(cells)))


def _select_shapes(
    free: set[Point], height: int, width: int, sizes: list[int], rng
) -> list[frozenset[Point]] | None:
    if not sizes:
        return []
    candidates = _shape_candidates(free, height, width, sizes[0])
    rng.shuffle(candidates)
    for cells in candidates:
        rest = _select_shapes(free - set(cells), height, width, sizes[1:], rng)
        if rest is not None:
            return [cells, *rest]
    return None


def _collinear_candidates(free: set[Point], height: int, width: int):
    candidates: list[tuple[Point, Point, frozenset[Point]]] = []
    for r in range(height):
        for c0 in range(width - 2):
            for c1 in range(c0 + 2, width):
                segment = frozenset((r, c) for c in range(c0, c1 + 1))
                if segment <= free:
                    candidates.append(((r, c0), (r, c1), segment))
    for c in range(width):
        for r0 in range(height - 2):
            for r1 in range(r0 + 2, height):
                segment = frozenset((r, c) for r in range(r0, r1 + 1))
                if segment <= free:
                    candidates.append(((r0, c), (r1, c), segment))
    return candidates


def _place_controls(
    grid: Grid,
    boxes: list[Box],
    nonpair_colors: list[int],
    collinear_colors: list[int],
    ctx,
) -> None:
    height, width = len(grid), len(grid[0])
    border_cells = set().union(*(_bbox_border([(r0, c0), (r1, c1)]) for r0, c0, r1, c1 in boxes))
    free = {(r, c) for r in range(height) for c in range(width)} - border_cells
    rng = ctx.draw_rng("negative_controls")

    collinear_options = [None]
    if collinear_colors:
        collinear_options = _collinear_candidates(free, height, width)
        rng.shuffle(collinear_options)
    # Reserve the entire segment, not only its endpoints, so the bbox rival has
    # an observable background cell to fill.
    for option in collinear_options:
        segment = set() if option is None else set(option[2])
        remaining = free - segment
        if len(nonpair_colors) == 2:
            size_orders = ([3, 4], [3, 3], [4, 3])
        elif len(nonpair_colors) == 1:
            size_orders = ([3], [4]) if rng.randrange(2) == 0 else ([4], [3])
        else:
            size_orders = ([],)
        selected = None
        for sizes in size_orders:
            selected = _select_shapes(remaining, height, width, list(sizes), rng)
            if selected is not None:
                break
        if selected is None:
            continue
        if option is not None:
            first, second, _full_segment = option
            color = collinear_colors[0]
            grid[first[0]][first[1]] = color
            grid[second[0]][second[1]] = color
        for color, cells in zip(nonpair_colors, selected):
            for r, c in cells:
                grid[r][c] = color
        return
    raise ValueError("could not place exact distractor controls outside target borders")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    _validate_call(difficulty, overrides)
    defaults = _profile_defaults(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_axis(ctx, overrides, "grid_h", 9, 18, int(defaults["grid_h"]))
    width = _draw_axis(ctx, overrides, "grid_w", 10, 18, int(defaults["grid_w"]))
    n_rects = _draw_axis(ctx, overrides, "n_rects", 1, 4, int(defaults["n_rects"]))
    n_nonpair = _draw_axis(ctx, overrides, "n_nonpair", 0, 2, int(defaults["n_nonpair"]))
    n_collinear = _draw_axis(ctx, overrides, "n_collinear", 0, 1, int(defaults["n_collinear"]))

    boxes = _draw_boxes(ctx, height, width, n_rects)
    corner_rng = ctx.draw_rng("corner_diagonals")
    box_corners = [_corners(box, bool(corner_rng.randrange(2))) for box in boxes]

    total_colors = n_rects + n_nonpair + n_collinear
    colors = list(ctx.draw_distinct_colors("scene_colors", n=total_colors, exclude={0}))
    target_colors = list(colors[:n_rects])
    if n_rects >= 2:
        first_two = [0, 1]
        earlier, later = sorted(first_two, key=lambda index: min(box_corners[index]))
        low, high = sorted(target_colors[:2])
        if defaults["relation"] == "higher":
            target_colors[earlier], target_colors[later] = low, high
        else:
            target_colors[earlier], target_colors[later] = high, low

    grid = full_grid(height, width, 0)
    for color, corners in zip(target_colors, box_corners):
        for r, c in corners:
            if grid[r][c] != 0:
                raise AssertionError("target corner templates collided")
            grid[r][c] = color

    nonpair_colors = colors[n_rects : n_rects + n_nonpair]
    collinear_colors = colors[n_rects + n_nonpair :]
    _place_controls(grid, boxes, nonpair_colors, collinear_colors, ctx)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced malformed scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != expected[axis]:
            raise AssertionError(
                f"axis {axis!r} drifted: keyed={expected[axis]!r} observed={observed[axis]!r}"
            )
    return [list(row) for row in grid]


def _render_with_precedence(grid: Grid, chooser: Callable[[list[int]], int]) -> Grid:
    out = [list(row) for row in grid]
    candidates: dict[Point, list[int]] = {}
    for color, cells in _qualifying_rectangles(grid):
        for point in _bbox_border(cells):
            candidates.setdefault(point, []).append(color)
    for (r, c), colors in candidates.items():
        out[r][c] = chooser(colors)
    return out


def _rival_expand_all_exactly_two_bboxes(grid: Grid) -> Grid:
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) == 2:
            for r, c in _bbox_border(cells):
                out[r][c] = color
    return out


def _rival_higher_color_wins(grid: Grid) -> Grid:
    return _render_with_precedence(grid, max)


def _rival_lower_color_wins(grid: Grid) -> Grid:
    return _render_with_precedence(grid, min)


def _rival_fresh_canvas(grid: Grid) -> Grid:
    blank = full_grid(len(grid), len(grid[0]), 0)
    candidates: dict[Point, list[int]] = {}
    for color, cells in _qualifying_rectangles(grid):
        for point in _bbox_border(cells):
            candidates.setdefault(point, []).append(color)
    # The intended row-major order is the order in each candidates list.
    for (r, c), colors in candidates.items():
        blank[r][c] = colors[-1]
    return blank


def _identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _overlap_relations(grid: Grid) -> set[str]:
    rects = _qualifying_rectangles(grid)
    relations: set[str] = set()
    for index, (earlier_color, earlier_cells) in enumerate(rects):
        earlier_border = _bbox_border(earlier_cells)
        for later_color, later_cells in rects[index + 1 :]:
            if earlier_border & _bbox_border(later_cells):
                relations.add("higher" if later_color > earlier_color else "lower")
    return relations


def _witness_nonpair(grid: Grid) -> bool:
    return any(len(cells) != 2 for cells in _positions_by_color(grid).values())


def _witness_collinear(grid: Grid) -> bool:
    return bool(_collinear_pairs(grid))


def _witness_higher_overlap(grid: Grid) -> bool:
    return "higher" in _overlap_relations(grid)


def _witness_lower_overlap(grid: Grid) -> bool:
    return "lower" in _overlap_relations(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "preserved_nonpair_distractor": _witness_nonpair,
    "collinear_exact_pair": _witness_collinear,
    "higher_color_wins_overlap": _witness_higher_overlap,
    "lower_color_wins_overlap": _witness_lower_overlap,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "expand_all_exactly_two_bboxes": _rival_expand_all_exactly_two_bboxes,
    "higher_color_wins_crossings": _rival_higher_color_wins,
    "lower_color_wins_crossings": _rival_lower_color_wins,
    "erase_distractors_fresh_canvas": _rival_fresh_canvas,
    "identity": _identity,
}
WITNESS_RIVALS = {
    "preserved_nonpair_distractor": ["erase_distractors_fresh_canvas"],
    "collinear_exact_pair": ["expand_all_exactly_two_bboxes"],
    "higher_color_wins_overlap": ["lower_color_wins_crossings"],
    "lower_color_wins_overlap": ["higher_color_wins_crossings"],
}

# Both reproduce all five canonical train/test pairs.  Canonical inputs have no
# collinear exactly-two color, and their only qualifying-border overlap has the
# later first-occurring color numerically larger.
CANONICAL_SHORTCUTS = {
    "expand_all_exactly_two_bboxes": _rival_expand_all_exactly_two_bboxes,
    "higher_color_wins_crossings": _rival_higher_color_wins,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared rival fits demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    rows = [*demos, query]
    reasons: list[str] = []
    for index, row in enumerate(rows):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(row, dict) or "input" not in row or "output" not in row:
            reasons.append(f"{role} is missing input/output")
            continue
        structural = strict_canonical_like(row["input"])
        if structural:
            reasons.append(f"{role} input is outside the teaching domain: {structural[0]}")
            continue
        if row["output"] != rule_mirror(row["input"]):
            reasons.append(f"{role} output disagrees with the matching-corner border rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(row["input"]) == row["output"] for row in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} matches every demo but changes the query")
    return reasons


def mutation_fixtures():
    """Task-linked malformed near-misses for the mutation-sensitivity probe."""
    blank = full_grid(6, 7, 0)
    singleton = full_grid(6, 7, 0)
    singleton[1][1] = 3
    collinear_only = full_grid(6, 7, 0)
    collinear_only[2][1] = collinear_only[2][5] = 4
    invalid_color = full_grid(6, 7, 0)
    invalid_color[1][1] = invalid_color[4][5] = 2
    invalid_color[0][0] = 10
    ragged = [[0, 2, 0], [0, 0], [0, 0, 2]]
    return [
        ("all_background", blank),
        ("singleton_without_rectangle", singleton),
        ("collinear_without_rectangle", collinear_only),
        ("invalid_arc_color", invalid_color),
        ("ragged_grid", ragged),
    ]
