"""Generator for task 06da3d8c94fe: infer a binary mask operation.

Each input is five equal-width panels separated by full-height color-5 columns.
The third panel is exactly one of union/intersection/xor applied to the first
two panels.  The selected canonical rule infers that unique operation and
applies it to panels four and five, painting occupied output cells color 2.

The production curriculum deliberately schedules all three operations twice in
every six consecutive draws.  Even sample indices use a canonical-scale
4x24, three-color profile; odd indices explore the full declared size domain.
No malformed/fallback demonstration is part of the valid distribution.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "06da3d8c94fe"
TASK_ID = GENERATOR_ID
RULE_HASH = "b01bd9f14dbe"
VERSION = "4.0.0"

SUMMARY = (
    "Five panels separated by gray columns encode p1 op p2 = p3 for exactly "
    "one of union, intersection, or xor; apply that operation to p4 and p5. "
    "The sampler schedules every operation twice per six draws, guarantees "
    "distinct candidate outputs on both the demonstration and query, and "
    "anchors every difficulty band at the canonical 4x24 three-color profile."
)

EXAMPLES_NEEDED = 5
KINDS = ("union", "intersection", "xor")

INVARIANTS = [
    "width is exactly 5*panel_w+4 and the four separator columns are color 5",
    "p3 is a literal 0/2 mask matching exactly one of union/intersection/xor",
    "all three demo candidates and all three query candidates are pairwise distinct and non-empty",
    "every six consecutive default draws contain each operation exactly twice",
    "even sample indices default to the canonical 4x24 palette {0,2,5} profile",
]

AXES = {
    "panel_w": {
        "type": "int",
        "default": "4 on canonical-profile draws; weighted 3..5 otherwise",
        "valid": "3..5",
    },
    "grid_h": {
        "type": "int",
        "default": "4 on canonical-profile draws; weighted 4..10 otherwise",
        "valid": "4..10",
    },
    "kind": {
        "type": "str",
        "default": "sample_index mod 3",
        "valid": "union|intersection|xor",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_CANONICAL_PROFILE = "canonical"
_BROAD_PROFILE = "broad"
SCHEDULE_PROFILES = tuple(
    f"{profile}:{kind}"
    for profile in (_CANONICAL_PROFILE, _BROAD_PROFILE)
    for kind in KINDS
)
_PANEL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_request(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("panel_w", "grid_h"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    if overrides.get("kind") is not None and type(overrides["kind"]) is not str:
        raise TypeError("kind must be a string")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic default curriculum cell for one draw."""
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    profile = _CANONICAL_PROFILE if sample_index % 2 == 0 else _BROAD_PROFILE
    return f"{profile}:{KINDS[sample_index % len(KINDS)]}"


def _binop(kind, left, right):
    if kind not in KINDS:
        raise ValueError(f"unknown operation {kind!r}")
    height = len(left)
    width = len(left[0]) if height else 0
    result = [[0] * width for _ in range(height)]
    for row in range(height):
        for column in range(width):
            a = left[row][column] != 0
            b = right[row][column] != 0
            if kind == "union":
                keep = a or b
            elif kind == "intersection":
                keep = a and b
            else:
                keep = a != b
            result[row][column] = 2 if keep else 0
    return result


def _split_panels(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if width < 19 or (width - 4) % 5:
        raise ValueError("width must equal 5*panel_w+4")
    panel_width = (width - 4) // 5
    panels = []
    for index in range(5):
        left = index * (panel_width + 1)
        panels.append([list(row[left:left + panel_width]) for row in grid])
    return panels, panel_width


def _matching_kinds(grid):
    panels, _ = _split_panels(grid)
    return [
        kind
        for kind in KINDS
        if _binop(kind, panels[0], panels[1]) == panels[2]
    ]


def _infer_kind(grid):
    matches = _matching_kinds(grid)
    if len(matches) != 1:
        raise ValueError(f"demo must identify exactly one operation, got {matches}")
    return matches[0]


def rule_mirror(grid):
    """Pure Python mirror of the selected canonical Racket rule on valid inputs."""
    panels, _ = _split_panels(grid)
    return _binop(_infer_kind(grid), panels[3], panels[4])


# Compatibility for prior local probes; selected code and new tests use rule_mirror.
_mirror = rule_mirror


def _weighted_values(lo: int, hi: int, difficulty) -> tuple[int, ...]:
    values = list(range(lo, hi + 1))
    if difficulty == "easy":
        favored = values[: max(1, (len(values) + 1) // 2)]
    elif difficulty == "hard":
        favored = values[len(values) // 2 :]
    else:
        favored = values
    return tuple(values + favored * 5)


def _draw_int_axis(ctx, name: str, lo: int, hi: int, default_options: Iterable[int]) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(default_options))


def _draw_kind(ctx, default_kind: str) -> str:
    if ctx.overrides.get("kind") is not None:
        return ctx.draw_choice("kind", KINDS)
    return ctx.draw_choice("kind", (default_kind,))


def _empty_mask(height: int, width: int) -> list[list[int]]:
    return [[0] * width for _ in range(height)]


def _paint_cells(height: int, width: int, cells, color: int) -> list[list[int]]:
    grid = _empty_mask(height, width)
    for row, column in cells:
        grid[row][column] = color
    return grid


def _structured_pair(rng, height: int, width: int, color_left: int, color_right: int):
    """Connected subset/superset pair with three distinct connected binops."""
    orientations = ["vertical"]
    if width >= 4:
        orientations.append("horizontal")
    orientation = rng.choice(orientations)
    if orientation == "horizontal":
        row = rng.randrange(height)
        start = rng.randrange(width - 3)
        whole = [(row, start + offset) for offset in range(4)]
    else:
        column = rng.randrange(width)
        start = rng.randrange(height - 3)
        whole = [(start + offset, column) for offset in range(4)]
    half = whole[:2] if rng.randrange(2) == 0 else whole[2:]
    return (
        _paint_cells(height, width, half, color_left),
        _paint_cells(height, width, whole, color_right),
    )


def _broad_pair(rng, height: int, width: int, color_left: int, color_right: int, difficulty):
    """Random masks with explicit overlap, left-only, and right-only witnesses."""
    positions = [(row, column) for row in range(height) for column in range(width)]
    rng.shuffle(positions)
    state_by_position = {
        positions[0]: (1, 1),
        positions[1]: (1, 0),
        positions[2]: (0, 1),
    }
    occupied_probability = {
        "easy": 0.30,
        "medium": 0.45,
        "hard": 0.60,
        None: 0.45,
    }[difficulty]
    for position in positions[3:]:
        if rng.random() >= occupied_probability:
            state_by_position[position] = (0, 0)
            continue
        roll = rng.randrange(3)
        state_by_position[position] = ((1, 1), (1, 0), (0, 1))[roll]
    left = _empty_mask(height, width)
    right = _empty_mask(height, width)
    for (row, column), (a, b) in state_by_position.items():
        if a:
            left[row][column] = color_left
        if b:
            right[row][column] = color_right
    return left, right


def _join_panels(panels):
    height = len(panels[0])
    panel_width = len(panels[0][0])
    width = 5 * panel_width + 4
    grid = full_grid(height, width, 5)
    for index, panel in enumerate(panels):
        left = index * (panel_width + 1)
        for row in range(height):
            for column in range(panel_width):
                grid[row][left + column] = panel[row][column]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    profile, scheduled_kind = schedule_profile(seed, sample_index, difficulty).split(":")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if profile == _CANONICAL_PROFILE:
        panel_width = _draw_int_axis(ctx, "panel_w", 3, 5, (4,))
        height = _draw_int_axis(ctx, "grid_h", 4, 10, (4,))
    else:
        panel_width = _draw_int_axis(
            ctx, "panel_w", 3, 5, _weighted_values(3, 5, difficulty)
        )
        height = _draw_int_axis(
            ctx, "grid_h", 4, 10, _weighted_values(4, 10, difficulty)
        )
    kind = _draw_kind(ctx, scheduled_kind)

    if profile == _CANONICAL_PROFILE:
        demo_colors = query_colors = (2, 2)
        p1, p2 = _structured_pair(
            ctx.draw_rng("demo_masks"), height, panel_width, *demo_colors
        )
        p4, p5 = _structured_pair(
            ctx.draw_rng("query_masks"), height, panel_width, *query_colors
        )
    else:
        color_rng = ctx.draw_rng("panel_colors")
        c1, c2, c4, c5 = [color_rng.choice(_PANEL_COLORS) for _ in range(4)]
        p1, p2 = _broad_pair(
            ctx.draw_rng("demo_masks"), height, panel_width, c1, c2, difficulty
        )
        p4, p5 = _broad_pair(
            ctx.draw_rng("query_masks"), height, panel_width, c4, c5, difficulty
        )
    p3 = _binop(kind, p1, p2)
    grid = _join_panels((p1, p2, p3, p4, p5))
    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError("constructive generator violated its contract: " + "; ".join(findings))
    return grid


def _all_distinct(grids) -> bool:
    frozen = {
        tuple(tuple(row) for row in grid)
        for grid in grids
    }
    return len(frozen) == len(grids)


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    try:
        panels, panel_width = _split_panels(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    height = len(grid)
    width = len(grid[0])
    if not 4 <= height <= 10:
        errors.append(f"grid_h={height} outside 4..10")
    if not 3 <= panel_width <= 5:
        errors.append(f"panel_w={panel_width} outside 3..5")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (not bool)")
        return errors
    divider_columns = [panel_width + index * (panel_width + 1) for index in range(4)]
    if any(grid[row][column] != 5 for row in range(height) for column in divider_columns):
        errors.append("all four divider columns must be full-height color 5")
    if any(value == 5 for panel in panels for row in panel for value in row):
        errors.append("color 5 is reserved for divider columns")
    if any(value not in (0, 2) for row in panels[2] for value in row):
        errors.append("p3 must be a literal color-2/background operation mask")

    demo_outputs = [_binop(kind, panels[0], panels[1]) for kind in KINDS]
    matches = [kind for kind, output in zip(KINDS, demo_outputs) if output == panels[2]]
    if len(matches) != 1:
        errors.append(f"p3 must identify exactly one operation, got {matches}")
    if not _all_distinct(demo_outputs):
        errors.append("union/intersection/xor must be pairwise distinct on p1,p2")
    if any(not any(value for row in output for value in row) for output in demo_outputs):
        errors.append("every demonstration candidate output must be non-empty")

    query_outputs = [_binop(kind, panels[3], panels[4]) for kind in KINDS]
    if not _all_distinct(query_outputs):
        errors.append("union/intersection/xor must be pairwise distinct on p4,p5")
    if any(not any(value for row in output for value in row) for output in query_outputs):
        errors.append("every query candidate output must be non-empty")
    return errors


def strict_canonical_like(grid):
    """Accept exactly the lawful task manifold enforced by self_check."""
    return self_check(grid)


def observe_overrides(grid):
    _, panel_width = _split_panels(grid)
    return {
        "panel_w": panel_width,
        "grid_h": len(grid),
        "kind": _infer_kind(grid),
    }


def _fixed_operation(grid, kind):
    panels, _ = _split_panels(grid)
    return _binop(kind, panels[3], panels[4])


def _always_union(grid):
    return _fixed_operation(grid, "union")


def _always_intersection(grid):
    return _fixed_operation(grid, "intersection")


def _always_xor(grid):
    return _fixed_operation(grid, "xor")


def _never_union(grid):
    kind = _infer_kind(grid)
    return _fixed_operation(grid, "xor" if kind == "union" else kind)


def _kind_witness(kind):
    def witness(grid):
        try:
            return _infer_kind(grid) == kind
        except (TypeError, ValueError):
            return False

    return witness


SEMANTIC_WITNESSES = {
    "union_branch": _kind_witness("union"),
    "intersection_branch": _kind_witness("intersection"),
    "xor_branch": _kind_witness("xor"),
}
SEMANTIC_RIVALS = {
    "always_union": _always_union,
    "always_intersection": _always_intersection,
    "always_xor": _always_xor,
    "never_union": _never_union,
}
WITNESS_RIVALS = {
    "union_branch": ["always_intersection", "always_xor", "never_union"],
    "intersection_branch": ["always_union", "always_xor"],
    "xor_branch": ["always_union", "always_intersection"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Name any declared query-changing rival that survives every demo."""
    reasons = []
    try:
        query_input = query["input"]
        true_query = rule_mirror(query_input)
    except Exception as exc:
        return [f"invalid query: {type(exc).__name__}: {exc}"]
    for name, rival in LESSON_COMPETITORS.items():
        try:
            rival_query = rival(query_input)
            if rival_query == true_query:
                continue
            if all(rival(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"{name} fits every demo but changes the query answer")
        except Exception as exc:
            reasons.append(f"{name} could not be evaluated: {type(exc).__name__}: {exc}")
    return reasons
