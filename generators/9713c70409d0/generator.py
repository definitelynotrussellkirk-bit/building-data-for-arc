"""Generator for ``9713c70409d0`` — completed-closure overlap matrices.

Each non-zero color is one sparse object.  Complete every object in two steps:
fill between its leftmost/rightmost cell in each occupied row, then fill between
its topmost/bottommost cell in every occupied column.  Sort colors ascending and
emit a KxK relation matrix: 5 on the diagonal, 8 when two completed closures
intersect, otherwise 0.

The public examples are also explained by the easier shortcut "intersect raw
bounding boxes".  This generator therefore uses a four-profile curriculum.  Two
profiles stay on the canonical size/morphology manifold, one profile is a
row-then-column ordering witness that defeats both bounding-box and row-only
closure rules, and one profile supplies varied five-object relation graphs.
Every four consecutive draws contain all four profiles.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9713c70409d0"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "c6c3ba6e25a0"

SUMMARY = (
    "Sparse colored objects are completed by row closure followed by column "
    "closure. Colors are sorted ascending and the output is a KxK overlap "
    "matrix with diagonal 5 and off-diagonal 8/0. A deterministic four-profile "
    "cycle preserves canonical 3- and 4-color scenes, includes a counterexample "
    "to the bounding-box shortcut, and varies five-object relation graphs."
)

INVARIANTS = [
    "background is 0 and every non-zero color denotes exactly one object",
    "ordinary objects have 3 or 4 endpoint cells distributed over exactly two rows",
    "ordinary lessons contain at least one closure overlap and at least one non-overlap",
    "output size is the number of distinct non-zero colors sorted ascending",
    "the canonical Racket program is the sole label authority",
]

SCHEDULE_PROFILES = (
    "canonical_3",
    "canonical_4",
    "closure_order",
    "graph_5",
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled four-profile cycle",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# An object is represented by two horizontal intervals: (row, left, right).
Interval = tuple[int, int, int]
ObjectSpec = tuple[Interval, Interval]

_PROFILE_SIGNATURES: dict[str, tuple[int, int, int]] = {
    "canonical_3": (7, 12, 3),
    "canonical_4": (8, 13, 4),
    "closure_order": (9, 14, 3),
    "graph_5": (10, 15, 5),
}
_SIGNATURE_TO_PROFILE = {value: key for key, value in _PROFILE_SIGNATURES.items()}
_CANONICAL_SIGNATURES = {(7, 12, 3), (8, 13, 4)}

# The canonical-scale profiles preserve canonical dimensions, endpoint grammar,
# and mixed relations while varying the relation graph itself.
_CANONICAL_3_VARIANTS: tuple[tuple[ObjectSpec, ...], ...] = (
    # One edge plus an isolated vertex (the first public demonstration graph).
    (
        ((1, 1, 3), (3, 1, 3)),
        ((2, 3, 5), (4, 3, 5)),
        ((1, 8, 10), (2, 8, 10)),
    ),
    # A three-vertex path (two overlaps, one non-overlap).
    (
        ((1, 1, 3), (3, 1, 3)),
        ((2, 3, 5), (4, 3, 5)),
        ((3, 5, 7), (5, 5, 7)),
    ),
)

_CANONICAL_4_VARIANTS: tuple[tuple[ObjectSpec, ...], ...] = (
    # Two disjoint edges (the second public demonstration graph).
    (
        ((1, 1, 4), (2, 1, 4)),
        ((2, 3, 6), (3, 3, 6)),
        ((4, 8, 10), (6, 8, 10)),
        ((5, 9, 11), (7, 9, 11)),
    ),
    # K1,3 star.
    (
        ((3, 1, 11), (4, 1, 11)),
        ((1, 2, 3), (6, 2, 3)),
        ((1, 5, 6), (6, 5, 6)),
        ((1, 8, 9), (6, 8, 9)),
    ),
    # C4 = K2,2.
    (
        ((2, 1, 11), (3, 1, 11)),
        ((5, 1, 11), (6, 1, 11)),
        ((1, 2, 3), (7, 2, 3)),
        ((1, 8, 9), (7, 8, 9)),
    ),
    # P4 path.
    (
        ((1, 1, 5), (2, 1, 5)),
        ((0, 4, 5), (4, 4, 5)),
        ((3, 3, 9), (5, 3, 9)),
        ((4, 8, 9), (7, 8, 9)),
    ),
    # K3 plus an isolated vertex.
    (
        ((2, 1, 7), (5, 1, 7)),
        ((1, 3, 6), (6, 3, 6)),
        ((3, 0, 8), (4, 0, 8)),
        ((2, 10, 11), (5, 10, 11)),
    ),
    # One edge plus two isolated vertices.
    (
        ((1, 1, 4), (3, 1, 4)),
        ((2, 3, 6), (4, 3, 6)),
        ((1, 8, 9), (2, 8, 9)),
        ((5, 9, 11), (6, 9, 11)),
    ),
    # Triangle with a one-edge tail.
    (
        ((1, 1, 7), (4, 1, 7)),
        ((0, 3, 6), (5, 3, 6)),
        ((2, 0, 9), (3, 0, 9)),
        ((2, 8, 10), (6, 8, 10)),
    ),
    # K4 with one missing edge: the horizontal pair is disjoint while both
    # vertical rectangles cross it and each other.
    (
        ((1, 1, 11), (2, 1, 11)),
        ((5, 1, 11), (6, 1, 11)),
        ((0, 3, 6), (7, 3, 6)),
        ((0, 5, 9), (7, 5, 9)),
    ),
)

# Both variants preserve the same pair of anti-shortcut facts: A and B overlap
# only after column closure, while B's raw bounding box overlaps C although the
# true B/C closures are disjoint.  The second variant additionally makes A/C
# overlap, expanding the three-color relation alphabet.
_CLOSURE_ORDER_VARIANTS: tuple[tuple[ObjectSpec, ...], ...] = (
    (
        ((1, 3, 5), (6, 3, 5)),
        ((3, 1, 7), (8, 10, 12)),
        ((5, 8, 10), (7, 8, 10)),
    ),
    (
        ((1, 3, 5), (6, 3, 5)),
        ((3, 1, 7), (8, 10, 12)),
        ((5, 5, 7), (7, 5, 7)),
    ),
)

# Five-object rectangle families. Color assignment is randomized, so each
# unlabeled graph yields many labeled output matrices without changing the rule.
_GRAPH_5_VARIANTS: tuple[tuple[ObjectSpec, ...], ...] = (
    # K1,4 star: one horizontal center, four disjoint vertical leaves.
    (
        ((4, 1, 13), (5, 1, 13)),
        ((1, 2, 3), (8, 2, 3)),
        ((1, 5, 6), (8, 5, 6)),
        ((1, 8, 9), (8, 8, 9)),
        ((1, 11, 12), (8, 11, 12)),
    ),
    # K2,3: two disjoint horizontal bars crossed by three vertical bars.
    (
        ((2, 1, 13), (3, 1, 13)),
        ((6, 1, 13), (7, 1, 13)),
        ((1, 2, 3), (8, 2, 3)),
        ((1, 6, 7), (8, 6, 7)),
        ((1, 10, 11), (8, 10, 11)),
    ),
    # P5 path, realized with alternating horizontal and vertical rectangles.
    (
        ((1, 1, 6), (3, 1, 6)),
        ((0, 4, 5), (5, 4, 5)),
        ((4, 3, 9), (6, 3, 9)),
        ((3, 8, 9), (8, 8, 9)),
        ((7, 7, 13), (9, 7, 13)),
    ),
    # Disjoint K3 and K2 components.
    (
        ((2, 1, 7), (6, 1, 7)),
        ((1, 3, 6), (7, 3, 6)),
        ((3, 0, 8), (5, 0, 8)),
        ((2, 10, 12), (4, 10, 12)),
        ((3, 11, 13), (6, 11, 13)),
    ),
    # C4 plus an isolated vertex.
    (
        ((2, 1, 10), (3, 1, 10)),
        ((6, 1, 10), (7, 1, 10)),
        ((1, 2, 3), (8, 2, 3)),
        ((1, 8, 9), (8, 8, 9)),
        ((4, 12, 13), (5, 12, 13)),
    ),
    # K4 plus an isolated vertex.
    (
        ((2, 1, 10), (7, 1, 10)),
        ((1, 3, 8), (8, 3, 8)),
        ((3, 0, 11), (6, 0, 11)),
        ((4, 2, 9), (5, 2, 9)),
        ((1, 12, 13), (2, 12, 13)),
    ),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'; "
            f"got {difficulty!r}"
        )


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _points_by_color(grid: Sequence[Sequence[int]]) -> dict[int, set[tuple[int, int]]]:
    result: dict[int, set[tuple[int, int]]] = defaultdict(set)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                result[int(value)].add((r, c))
    return dict(result)


def _row_close(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    by_row: dict[int, list[int]] = defaultdict(list)
    for r, c in cells:
        by_row[r].append(c)
    return {
        (r, c)
        for r, cols in by_row.items()
        for c in range(min(cols), max(cols) + 1)
    }


def _col_close(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    by_col: dict[int, list[int]] = defaultdict(list)
    for r, c in cells:
        by_col[c].append(r)
    return {
        (r, c)
        for c, rows in by_col.items()
        for r in range(min(rows), max(rows) + 1)
    }


def _double_close(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    return _col_close(_row_close(cells))


def _matrix_from_sets(
    colors: Sequence[int],
    occupied: dict[int, set[tuple[int, int]]],
) -> list[list[int]]:
    return [
        [
            5 if i == j else (8 if occupied[color_i] & occupied[color_j] else 0)
            for j, color_j in enumerate(colors)
        ]
        for i, color_i in enumerate(colors)
    ]


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains authoritative."""
    points = _points_by_color(grid)
    colors = sorted(points)
    closures = {color: _double_close(points[color]) for color in colors}
    return _matrix_from_sets(colors, closures)


def _relation_counts(output: Sequence[Sequence[int]]) -> tuple[int, int]:
    k = len(output)
    edges = sum(output[i][j] == 8 for i in range(k) for j in range(i + 1, k))
    possible = k * (k - 1) // 2
    return edges, possible - edges


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, off-grammar, or relation-trivial input scenes."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors

    points = _points_by_color(grid)
    colors = sorted(points)
    signature = (height, width, len(colors))
    if signature not in _SIGNATURE_TO_PROFILE:
        errors.append(
            "expected one declared (height,width,color-count) signature; "
            f"found {signature}"
        )

    for color in colors:
        cells = points[color]
        if not 3 <= len(cells) <= 4:
            errors.append(
                f"color {color} has {len(cells)} endpoint cells; expected 3 or 4"
            )
            continue
        rows: dict[int, list[int]] = defaultdict(list)
        for r, c in cells:
            rows[r].append(c)
        if len(rows) != 2:
            errors.append(
                f"color {color} occupies {len(rows)} rows; expected exactly 2"
            )
            continue
        if any(not 1 <= len(cols) <= 2 for cols in rows.values()):
            errors.append(
                f"color {color} must contribute one or two endpoint cells per row"
            )

    if not errors:
        edges, nonedges = _relation_counts(rule_mirror(grid))
        if edges == 0:
            errors.append("completed closures must contain at least one overlap")
        if nonedges == 0:
            errors.append("completed closures must contain at least one non-overlap")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept exact canonical size/color-count profiles and endpoint grammar."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    signature = (len(grid), len(grid[0]), len(_points_by_color(grid)))
    if signature not in _CANONICAL_SIGNATURES:
        reasons.append(
            "canonical profile must be 7x12 with 3 colors or 8x13 with 4 colors; "
            f"found {signature}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, str]:
    height, width, errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    signature = (height, width, len(_points_by_color(grid)))
    try:
        profile = _SIGNATURE_TO_PROFILE[signature]
    except KeyError as exc:
        raise ValueError(f"grid has no declared scene profile: {signature}") from exc
    return {"scene_profile": profile}


def _profile_objects(profile: str, rng) -> tuple[ObjectSpec, ...]:
    if profile == "canonical_3":
        return _CANONICAL_3_VARIANTS[rng.randrange(len(_CANONICAL_3_VARIANTS))]
    if profile == "canonical_4":
        return _CANONICAL_4_VARIANTS[rng.randrange(len(_CANONICAL_4_VARIANTS))]
    if profile == "closure_order":
        return _CLOSURE_ORDER_VARIANTS[rng.randrange(len(_CLOSURE_ORDER_VARIANTS))]
    if profile == "graph_5":
        return _GRAPH_5_VARIANTS[rng.randrange(len(_GRAPH_5_VARIANTS))]
    raise ValueError(f"unknown scene_profile {profile!r}")


def _transform_object(
    obj: ObjectSpec,
    *,
    height: int,
    width: int,
    flip_vertical: bool,
    flip_horizontal: bool,
) -> ObjectSpec:
    transformed: list[Interval] = []
    for row, left, right in obj:
        if flip_vertical:
            row = height - 1 - row
        if flip_horizontal:
            left, right = width - 1 - right, width - 1 - left
        transformed.append((row, left, right))
    transformed.sort(key=lambda item: item[0])
    return transformed[0], transformed[1]


def _paint_endpoints(
    grid: list[list[int]],
    obj: ObjectSpec,
    color: int,
) -> None:
    for row, left, right in obj:
        for col in {left, right}:
            if grid[row][col] != 0:
                raise RuntimeError(
                    f"profile endpoint collision at ({row},{col}): "
                    f"{grid[row][col]} versus {color}"
                )
            grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))

    scheduled = schedule_profile(seed, sample_index, difficulty)
    effective_overrides = {"scene_profile": scheduled}
    effective_overrides.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    height, width, n_colors = _PROFILE_SIGNATURES[profile]
    colors = ctx.draw_distinct_colors("object_colors", n=n_colors, exclude={0})
    rng = ctx.draw_rng(f"layout:{difficulty or 'none'}")

    specs = list(_profile_objects(profile, rng))
    rng.shuffle(specs)
    flip_vertical = bool(rng.getrandbits(1))
    flip_horizontal = bool(rng.getrandbits(1))
    specs = [
        _transform_object(
            obj,
            height=height,
            width=width,
            flip_vertical=flip_vertical,
            flip_horizontal=flip_horizontal,
        )
        for obj in specs
    ]

    grid = full_grid(height, width, 0)
    for obj, color in zip(specs, colors):
        _paint_endpoints(grid, obj, color)

    findings = self_check(grid)
    if findings:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(findings))
    observed = observe_overrides(grid)
    requested = {"scene_profile": profile}
    if observed != requested:
        raise RuntimeError(
            f"realized exact axes {observed} disagree with requested {requested}"
        )
    return grid


def _bbox_overlap_rival(grid) -> list[list[int]]:
    points = _points_by_color(grid)
    colors = sorted(points)
    boxes: dict[int, tuple[int, int, int, int]] = {}
    for color in colors:
        rows = [r for r, _ in points[color]]
        cols = [c for _, c in points[color]]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        boxes[color] = (top, bottom, left, right)
    occupied = {
        color: {
            (r, c)
            for r in range(boxes[color][0], boxes[color][1] + 1)
            for c in range(boxes[color][2], boxes[color][3] + 1)
        }
        for color in colors
    }
    return _matrix_from_sets(colors, occupied)


def _row_closure_only_rival(grid) -> list[list[int]]:
    points = _points_by_color(grid)
    colors = sorted(points)
    occupied = {color: _row_close(points[color]) for color in colors}
    return _matrix_from_sets(colors, occupied)


def _raw_cells_only_rival(grid) -> list[list[int]]:
    points = _points_by_color(grid)
    colors = sorted(points)
    return _matrix_from_sets(colors, points)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "bbox_overlap": _bbox_overlap_rival,
    "row_closure_only": _row_closure_only_rival,
    "raw_cells_only": _raw_cells_only_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# This shortcut matches every public canonical pair. The closure_order profile
# and its named witness make the required generated counterexample explicit.
CANONICAL_SHORTCUTS = {
    "bbox_overlap": _bbox_overlap_rival,
}


def _valid_and_refutes(grid, rivals: Sequence[str]) -> bool:
    if self_check(grid):
        return False
    expected = rule_mirror(grid)
    return all(SEMANTIC_RIVALS[name](grid) != expected for name in rivals)


def _witness_bbox_false_positive(grid) -> bool:
    return _valid_and_refutes(grid, ("bbox_overlap",))


def _witness_column_closure(grid) -> bool:
    return _valid_and_refutes(grid, ("row_closure_only",))


def _witness_completed_not_raw(grid) -> bool:
    return _valid_and_refutes(grid, ("raw_cells_only",))


SEMANTIC_WITNESSES = {
    "bbox_overlap_false_positive": _witness_bbox_false_positive,
    "column_closure_creates_overlap": _witness_column_closure,
    "completed_objects_not_raw_cells": _witness_completed_not_raw,
}
WITNESS_RIVALS = {
    "bbox_overlap_false_positive": ["bbox_overlap"],
    "column_closure_creates_overlap": ["row_closure_only"],
    "completed_objects_not_raw_cells": ["raw_cells_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demonstrations that collectively refute every rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_grid = demo["input"]
        input_errors = self_check(input_grid)
        if input_errors:
            reasons.append(f"demo {index} input is invalid: {input_errors[0]}")
            continue
        expected = rule_mirror(input_grid)
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact double-closure matrix")
        for name, competitor in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or competitor(input_grid) != expected

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def mutation_fixtures():
    """Task-local malformed or semantically trivial scenes to reject."""
    all_background = full_grid(7, 12, 0)

    singleton_color = full_grid(7, 12, 0)
    singleton_color[1][1] = 2
    singleton_color[2][2] = 3
    singleton_color[3][3] = 4

    one_row_object = [list(row) for row in generate(9001, 0, scene_profile="canonical_3")]
    first_color = min(_points_by_color(one_row_object))
    occupied_rows = sorted({r for r, _ in _points_by_color(one_row_object)[first_color]})
    for r, row in enumerate(one_row_object):
        if r == occupied_rows[-1]:
            for c, value in enumerate(row):
                if value == first_color:
                    row[c] = 0

    overfilled_object = [list(row) for row in generate(9002, 0, scene_profile="canonical_3")]
    first_color = min(_points_by_color(overfilled_object))
    cells = _points_by_color(overfilled_object)[first_color]
    closure = _double_close(cells)
    r, c = next(point for point in closure if point not in cells and overfilled_object[point[0]][point[1]] == 0)
    overfilled_object[r][c] = first_color

    no_overlap = full_grid(7, 12, 0)
    isolated = (
        ((1, 1, 2), (2, 1, 2)),
        ((1, 5, 6), (2, 5, 6)),
        ((4, 9, 10), (5, 9, 10)),
    )
    for color, obj in zip((2, 4, 7), isolated):
        _paint_endpoints(no_overlap, obj, color)

    all_overlap = full_grid(7, 12, 0)
    crowded = (
        ((1, 1, 7), (5, 1, 7)),
        ((2, 3, 9), (4, 3, 9)),
        ((0, 5, 10), (6, 5, 10)),
    )
    for color, obj in zip((2, 4, 7), crowded):
        _paint_endpoints(all_overlap, obj, color)

    ragged = [[0, 0], [0]]
    return [
        ("all_background", all_background),
        ("singleton_colors", singleton_color),
        ("one_row_object", one_row_object),
        ("overfilled_object", overfilled_object),
        ("no_overlap_relation", no_overlap),
        ("all_overlap_relation", all_overlap),
        ("ragged_grid", ragged),
    ]
