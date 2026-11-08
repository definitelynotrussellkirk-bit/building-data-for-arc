"""Generator for e297c9504f64 — keep the leftmost red component.

Canonical rule
--------------
Find the 4-connected color-2 components.  Select the component whose bounding
box starts furthest left, erase everything else, and repaint the selected
component color 8 on a same-size black canvas.

The generated curriculum deliberately varies the selected component's size,
vertical rank, and absolute column.  Some scenes also put a differently colored
single-cell distractor further left, so "leftmost nonzero object" is not a
valid shortcut for the intended color-2 selection rule.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e297c9504f64"
TASK_ID = "e297c9504f64"
VERSION = "2.0.0"
RULE_HASH = "a6e9d91342d0"

SUMMARY = (
    "A black 8..10 by 11..14 grid contains three or four isolated red (2) "
    "4-connected components with distinct left bounding-box columns. The "
    "strictly leftmost RED component is selected, all other cells are erased, "
    "and the selected shape is repainted cyan (8) in place. Some scheduled "
    "lessons include one non-red distractor further left; it is never selected."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "there are exactly three or four color-2 4-connected components",
    "the red components have distinct bounding-box left columns",
    "the leftmost red component is therefore unique",
    "red component sizes are between two and six cells",
    "there is at most one non-red component, a one-cell distractor",
    "different-colored nonzero cells do not touch orthogonally",
]

# Every declared axis is exact, independently overrideable across all bands,
# and recoverable from the returned grid through observe_overrides().
AXES = {
    "grid_h": {
        "type": "int",
        "default": "rng 8..10",
        "valid": "8..10",
        "doc": "Canvas height.",
    },
    "grid_w": {
        "type": "int",
        "default": "rng 11..14",
        "valid": "11..14",
        "doc": "Canvas width.",
    },
    "n_red_components": {
        "type": "int",
        "default": "rng 3..4",
        "valid": "3..4",
        "doc": "Number of color-2 connected components.",
    },
}

_SIZE_RELATIONS = ("smallest", "middle", "largest")
_VERTICAL_RELATIONS = ("top", "middle", "bottom")

# A 9-profile Latin-square schedule crosses target size rank with target
# vertical rank.  target_left varies independently enough to eliminate the
# canonical fixed-column shortcut.  Every run of three consecutive profiles
# contains all three size ranks, at least one non-top target, at least one
# non-column-1 target, and at least one left-side non-red distractor.
_PROFILE_TABLE = (
    ("smallest", "top", 2),
    ("middle", "middle", 0),
    ("largest", "bottom", 1),
    ("smallest", "middle", 0),
    ("middle", "bottom", 1),
    ("largest", "top", 2),
    ("smallest", "bottom", 0),
    ("middle", "top", 1),
    ("largest", "middle", 2),
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILE_TABLE)))
_DISTRACTOR_PROFILES = frozenset({0, 2, 5, 7})


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic curriculum profile for gate diagnostics."""
    del seed
    if difficulty == "medium":
        offset = 1
    elif difficulty == "hard":
        offset = 2
    elif isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        offset = round(2 * float(difficulty))
    else:
        offset = 0
    return (int(sample_index) + offset) % len(_PROFILE_TABLE)


def _validate_request(difficulty, overrides) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if difficulty is None:
        return
    if isinstance(difficulty, str):
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValueError(f"unknown difficulty: {difficulty!r}")
        return
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        if 0.0 <= float(difficulty) <= 1.0:
            return
    raise ValueError(f"invalid difficulty: {difficulty!r}")


def _shape_for_size(size: int, rng) -> list[tuple[int, int]]:
    """Connected templates with width <=2 and height <=3.

    The narrow envelope guarantees every declared axis combination can be
    packed into the smallest 8x11 canvas with a blank column between red
    bounding boxes.
    """
    variants = {
        2: [
            [(0, 0), (1, 0)],
        ],
        3: [
            [(0, 0), (1, 0), (2, 0)],
        ],
        4: [
            [(0, 0), (0, 1), (1, 0), (1, 1)],
            [(0, 0), (1, 0), (2, 0), (1, 1)],
            [(0, 1), (1, 0), (1, 1), (2, 1)],
        ],
        5: [
            [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],
            [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)],
            [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)],
        ],
        6: [
            [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
        ],
    }
    return list(rng.choice(variants[size]))


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = list(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _sizes_for_relation(
    n_components: int, relation: str, *, compact: bool
) -> list[int]:
    """Return distinct sizes with both canonical-scale and wide-scale support."""
    if n_components == 3:
        pool = [2, 3, 4] if compact else [2, 4, 6]
    else:
        pool = [2, 3, 4, 5] if compact else [2, 3, 5, 6]
    if relation == "smallest":
        target = min(pool)
    elif relation == "largest":
        target = max(pool)
    else:
        target = sorted(pool)[1]
    others = list(pool)
    others.remove(target)
    return [target, *others]


def _choose_tops(heights: list[int], h: int, relation: str, rng) -> list[int]:
    target_max = h - heights[0]
    other_max = [h - height for height in heights[1:]]
    if relation == "top":
        upper = min(target_max, min(limit - 1 for limit in other_max))
        target_top = rng.randint(0, max(0, upper))
        return [
            target_top,
            *[rng.randint(target_top + 1, limit) for limit in other_max],
        ]
    if relation == "bottom":
        target_top = rng.randint(1, target_max)
        return [
            target_top,
            *[rng.randint(0, min(target_top - 1, limit)) for limit in other_max],
        ]

    # Strictly middle: at least one component starts above and one below.
    candidates = [
        top
        for top in range(1, target_max + 1)
        if any(limit >= top + 1 for limit in other_max)
    ]
    if not candidates:
        raise RuntimeError("canvas cannot realize a middle target vertical rank")
    target_top = rng.choice(candidates)
    below_index = next(i for i, limit in enumerate(other_max) if limit >= target_top + 1)
    tops = [target_top]
    for i, limit in enumerate(other_max):
        if i == 0:
            tops.append(rng.randint(0, min(target_top - 1, limit)))
        elif i == below_index:
            tops.append(rng.randint(target_top + 1, limit))
        else:
            options = [x for x in range(limit + 1) if x != target_top]
            tops.append(rng.choice(options))
    return tops


def _horizontal_positions(
    widths: list[int], w: int, target_left: int, rng
) -> list[int]:
    minimum = sum(widths) + len(widths) - 1
    if target_left + minimum > w:
        raise RuntimeError(
            f"profile cannot fit widths={widths} at target_left={target_left} in w={w}"
        )
    gaps = [1] * (len(widths) - 1)
    trailing = 0
    extra = w - target_left - minimum
    for _ in range(extra):
        slot = rng.randrange(len(widths))
        if slot < len(gaps):
            gaps[slot] += 1
        else:
            trailing += 1
    del trailing  # explicitly sampled but not otherwise needed
    lefts = [target_left]
    for width, gap in zip(widths[:-1], gaps):
        lefts.append(lefts[-1] + width + gap)
    return lefts


def _place_left_distractor(grid, target_left: int, rng) -> None:
    """Place one non-red singleton strictly left of the selected red bbox."""
    if target_left <= 0:
        return
    h = len(grid)
    occupied = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    candidates = []
    for c in range(target_left):
        for r in range(h):
            if (r, c) in occupied:
                continue
            if any(
                (nr, nc) in occupied
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            ):
                continue
            candidates.append((r, c))
    if not candidates:
        raise RuntimeError("could not place the scheduled left-side color distractor")
    r, c = rng.choice(candidates)
    grid[r][c] = rng.choice([1, 3, 4, 5, 6, 7, 9])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 8, 10)
    w = ctx.draw_int("grid_w", 11, 14)
    n_components = ctx.draw_int("n_red_components", 3, 4)

    profile = schedule_profile(seed, sample_index, difficulty)
    size_relation, vertical_relation, target_left = _PROFILE_TABLE[profile]
    layout_rng = ctx.draw_rng("layout")
    shape_rng = ctx.draw_rng("shapes")

    compact_sizes = (int(seed) + int(sample_index)) % 2 == 0
    sizes = _sizes_for_relation(
        n_components, size_relation, compact=compact_sizes
    )
    other_sizes = sizes[1:]
    layout_rng.shuffle(other_sizes)
    sizes = [sizes[0], *other_sizes]
    shapes = [_shape_for_size(size, shape_rng) for size in sizes]
    dims = [_shape_dims(shape) for shape in shapes]
    tops = _choose_tops([height for height, _ in dims], h, vertical_relation, layout_rng)
    lefts = _horizontal_positions(
        [width for _, width in dims], w, target_left, layout_rng
    )

    grid = full_grid(h, w, 0)
    for shape, top, left in zip(shapes, tops, lefts):
        for dr, dc in shape:
            grid[top + dr][left + dc] = 2

    # The profile set has no cyclic run of three without a member, so every
    # EXAMPLES_NEEDED=3 lesson receives a color-selection counterexample while
    # the cue is not locked to one size or vertical-rank profile.
    if profile in _DISTRACTOR_PROFILES:
        _place_left_distractor(grid, target_left, ctx.draw_rng("distractor"))
    return grid


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    errors = []
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) must be an integer color 0..9")
    return errors


def _components_for_color(grid, color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _bbox(component: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    return min(rows), min(cols), max(rows), max(cols)


def _analyze(grid):
    errors = _validate_grid(grid)
    if errors:
        return {}, errors
    h, w = len(grid), len(grid[0])
    red = _components_for_color(grid, 2)
    red_rows = [
        {
            "cells": component,
            "bbox": _bbox(component),
            "size": len(component),
        }
        for component in red
    ]
    red_rows.sort(key=lambda row: (row["bbox"][1], row["bbox"][0]))

    nonred = []
    for color in sorted({value for row in grid for value in row} - {0, 2}):
        for component in _components_for_color(grid, color):
            nonred.append(
                {
                    "color": color,
                    "cells": component,
                    "bbox": _bbox(component),
                    "size": len(component),
                }
            )

    target = red_rows[0] if red_rows else None
    size_relation = None
    vertical_relation = None
    if target is not None and len(red_rows) >= 2:
        other_sizes = [row["size"] for row in red_rows[1:]]
        if target["size"] < min(other_sizes):
            size_relation = "smallest"
        elif target["size"] > max(other_sizes):
            size_relation = "largest"
        else:
            size_relation = "middle"
        target_top = target["bbox"][0]
        other_tops = [row["bbox"][0] for row in red_rows[1:]]
        if target_top < min(other_tops):
            vertical_relation = "top"
        elif target_top > max(other_tops):
            vertical_relation = "bottom"
        else:
            vertical_relation = "middle"

    return {
        "grid_h": h,
        "grid_w": w,
        "red": red_rows,
        "nonred": nonred,
        "target": target,
        "n_red_components": len(red_rows),
        "target_size_relation": size_relation,
        "target_vertical_relation": vertical_relation,
    }, []


def observe_overrides(grid) -> dict[str, int]:
    analysis, errors = _analyze(grid)
    if errors:
        return {}
    return {axis: analysis[axis] for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    analysis, errors = _analyze(grid)
    if errors:
        return errors
    h, w = analysis["grid_h"], analysis["grid_w"]
    if not 8 <= h <= 10:
        errors.append("grid height must be 8..10")
    if not 11 <= w <= 14:
        errors.append("grid width must be 11..14")

    red = analysis["red"]
    if not 3 <= len(red) <= 4:
        errors.append("grid must contain exactly three or four red components")
    if any(not 2 <= row["size"] <= 6 for row in red):
        errors.append("every red component must contain two to six cells")
    lefts = [row["bbox"][1] for row in red]
    if len(lefts) != len(set(lefts)):
        errors.append("red component bounding boxes must have distinct left columns")

    nonred = analysis["nonred"]
    if len(nonred) > 1:
        errors.append("at most one non-red distractor component is allowed")
    if any(row["size"] != 1 for row in nonred):
        errors.append("the non-red distractor must be exactly one cell")
    if any(row["color"] == 8 for row in nonred):
        errors.append("color 8 is reserved for the output and cannot appear in input")

    # Different colors must not be orthogonally joined into a cue cluster.
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            for nr, nc in ((r + 1, c), (r, c + 1)):
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other != 0 and other != value:
                        errors.append("different-colored nonzero cells touch orthogonally")
                        return errors
    return errors


def rule_mirror(grid):
    """Pure Python mirror of the canonical leftmost-red-component rule."""
    analysis, errors = _analyze(grid)
    if errors or analysis.get("target") is None:
        raise ValueError(errors[0] if errors else "no red component")
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for r, c in analysis["target"]["cells"]:
        output[r][c] = 8
    return output


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------

MIN_STRICT_FRAC = 0.05


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis, _ = _analyze(grid)
    if not 8 <= analysis["grid_h"] <= 10:
        reasons.append("canonical-like canvases are 8..10 rows high")
    if not 11 <= analysis["grid_w"] <= 14:
        reasons.append("canonical-like canvases are 11..14 columns wide")
    if analysis["nonred"]:
        reasons.append("canonical inputs contain only black and red")
    return reasons


def _witness_leftmost_vs_second(grid) -> bool:
    analysis, errors = _analyze(grid)
    return not errors and len(analysis["red"]) >= 2


def _witness_target_not_topmost(grid) -> bool:
    analysis, errors = _analyze(grid)
    return not errors and analysis["target_vertical_relation"] != "top"


def _witness_target_not_largest(grid) -> bool:
    analysis, errors = _analyze(grid)
    return not errors and analysis["target_size_relation"] != "largest"


def _witness_target_not_smallest(grid) -> bool:
    analysis, errors = _analyze(grid)
    return not errors and analysis["target_size_relation"] != "smallest"


def _witness_nonred_left_of_target(grid) -> bool:
    analysis, errors = _analyze(grid)
    if errors or not analysis["nonred"] or analysis["target"] is None:
        return False
    target_left = analysis["target"]["bbox"][1]
    return min(row["bbox"][1] for row in analysis["nonred"]) < target_left


def _witness_target_not_canonical_column(grid) -> bool:
    analysis, errors = _analyze(grid)
    return (
        not errors
        and analysis["target"] is not None
        and analysis["target"]["bbox"][1] != 1
    )


SEMANTIC_WITNESSES = {
    "leftmost_red_beats_second_leftmost": _witness_leftmost_vs_second,
    "target_not_topmost": _witness_target_not_topmost,
    "target_not_largest": _witness_target_not_largest,
    "target_not_smallest": _witness_target_not_smallest,
    "nonred_distractor_left_of_target": _witness_nonred_left_of_target,
    "target_not_fixed_at_canonical_column_1": _witness_target_not_canonical_column,
}


def _paint_component(grid, component):
    output = full_grid(len(grid), len(grid[0]), 0)
    if component is not None:
        for r, c in component:
            output[r][c] = 8
    return output


def _rival_second_leftmost_red(grid):
    analysis, errors = _analyze(grid)
    if errors or len(analysis["red"]) < 2:
        return full_grid(len(grid), len(grid[0]), 0)
    return _paint_component(grid, analysis["red"][1]["cells"])


def _rival_topmost_red(grid):
    analysis, errors = _analyze(grid)
    if errors or not analysis["red"]:
        return full_grid(len(grid), len(grid[0]), 0)
    selected = min(analysis["red"], key=lambda row: (row["bbox"][0], row["bbox"][1]))
    return _paint_component(grid, selected["cells"])


def _rival_largest_red(grid):
    analysis, errors = _analyze(grid)
    if errors or not analysis["red"]:
        return full_grid(len(grid), len(grid[0]), 0)
    selected = max(
        analysis["red"],
        key=lambda row: (row["size"], -row["bbox"][1], -row["bbox"][0]),
    )
    return _paint_component(grid, selected["cells"])


def _rival_smallest_red(grid):
    analysis, errors = _analyze(grid)
    if errors or not analysis["red"]:
        return full_grid(len(grid), len(grid[0]), 0)
    selected = min(
        analysis["red"],
        key=lambda row: (row["size"], row["bbox"][1], row["bbox"][0]),
    )
    return _paint_component(grid, selected["cells"])


def _all_monochrome_components(grid):
    rows = []
    for color in sorted({value for row in grid for value in row} - {0}):
        for component in _components_for_color(grid, color):
            rows.append({"cells": component, "bbox": _bbox(component), "color": color})
    return rows


def _rival_leftmost_nonzero(grid):
    components = _all_monochrome_components(grid)
    if not components:
        return full_grid(len(grid), len(grid[0]), 0)
    selected = min(components, key=lambda row: (row["bbox"][1], row["bbox"][0]))
    return _paint_component(grid, selected["cells"])


def _rival_fixed_column_one(grid):
    analysis, errors = _analyze(grid)
    if errors:
        return full_grid(len(grid), len(grid[0]), 0)
    candidates = [row for row in analysis["red"] if row["bbox"][1] == 1]
    if not candidates:
        return full_grid(len(grid), len(grid[0]), 0)
    selected = min(candidates, key=lambda row: row["bbox"][0])
    return _paint_component(grid, selected["cells"])


SEMANTIC_RIVALS = {
    "keep_second_leftmost_red": _rival_second_leftmost_red,
    "keep_topmost_red": _rival_topmost_red,
    "keep_largest_red": _rival_largest_red,
    "keep_smallest_red": _rival_smallest_red,
    "keep_leftmost_nonzero_regardless_of_color": _rival_leftmost_nonzero,
    "keep_red_component_at_canonical_column_1": _rival_fixed_column_one,
}

WITNESS_RIVALS = {
    "leftmost_red_beats_second_leftmost": "keep_second_leftmost_red",
    "target_not_topmost": "keep_topmost_red",
    "target_not_largest": "keep_largest_red",
    "target_not_smallest": "keep_smallest_red",
    "nonred_distractor_left_of_target": "keep_leftmost_nonzero_regardless_of_color",
    "target_not_fixed_at_canonical_column_1": "keep_red_component_at_canonical_column_1",
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every real canonical target begins in column 1, so this WRONG fixed-position
# rule is answer-equivalent on all four canonical pairs.  Generated profiles at
# target columns 0 and 2 are the required counterexamples.
CANONICAL_SHORTCUTS = {
    "keep_red_component_at_canonical_column_1": _rival_fixed_column_one,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the canonical rule")

    try:
        query_expected = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query_expected != query["output"]:
        reasons.append("query output disagrees with the canonical rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives:
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo but answers the query differently"
                )
            else:
                reasons.append(
                    f"competitor {name!r} survives every demo and the query"
                )
    return reasons
