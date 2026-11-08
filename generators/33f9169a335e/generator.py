"""Semantic generator for ARC task 33f9169a335e.

Every inverted U contributes one orange marker at the bottom of its gap
column.  The curriculum mixes transformed public topologies with generalized
same-row and staggered arrangements, varied dimensions, and varied colors.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "33f9169a335e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4ded628201c7"
SUMMARY = (
    "Find every three-cell cap whose next row contains its two legs and a "
    "zero center; preserve the scene and mark the bottom cell of each gap "
    "column orange."
)
EXAMPLES_NEEDED = 4

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "strict transformed public topology or a novel valid topology",
    },
}
INVARIANTS = [
    "background is zero and the bottom row starts empty",
    "input contains no orange cells because orange is the output marker",
    "every nonzero input cell belongs to at least one inverted-U witness",
    "each distinct gap column produces exactly one bottom-row marker",
    "ordinary draws contain one to four gap columns and always change",
]
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
COLORS = (1, 2, 3, 5, 6, 7, 8, 9)

# (height, width, ((top_row, gap_col), ...)); these store input topology only.
_PUBLIC_PROFILES = (
    (5, 5, ((0, 2),)),
    (8, 8, ((0, 2), (2, 6))),
    (5, 7, ((1, 2), (2, 5))),
    (7, 11, ((0, 2), (1, 6), (2, 9))),
)
_PUBLIC_SHAPES = {(height, width) for height, width, _ in _PUBLIC_PROFILES}


def _grid_error(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty sequences"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    height, width = len(grid), next(iter(widths))
    errors = []
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append("grid dimensions must be 5..30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be ARC integers 0..9")
    return errors


def _witness_cells(top: int, gap: int) -> tuple[tuple[int, int], ...]:
    return (
        (top, gap - 1),
        (top, gap),
        (top, gap + 1),
        (top + 1, gap - 1),
        (top + 1, gap + 1),
    )


def _detect_witnesses(grid) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return [
        (top, gap)
        for top in range(height - 1)
        for gap in range(1, width - 1)
        if all(grid[top][col] != 0 for col in (gap - 1, gap, gap + 1))
        and grid[top + 1][gap - 1] != 0
        and grid[top + 1][gap] == 0
        and grid[top + 1][gap + 1] != 0
    ]


def _normalized_topology(witnesses) -> tuple[tuple[int, int], ...]:
    min_top = min(top for top, _ in witnesses)
    min_gap = min(gap for _, gap in witnesses)
    return tuple(
        sorted((top - min_top, gap - min_gap) for top, gap in witnesses)
    )


def _reflected_topology(topology) -> tuple[tuple[int, int], ...]:
    max_gap = max(gap for _, gap in topology)
    return tuple(sorted((top, max_gap - gap) for top, gap in topology))


def _canonical_profile(grid, witnesses) -> str | None:
    shape = (len(grid), len(grid[0]))
    topology = _normalized_topology(witnesses)
    for index, (height, width, public) in enumerate(_PUBLIC_PROFILES):
        if (
            shape[0] < height
            or shape[1] < width
            or len(public) != len(witnesses)
        ):
            continue
        normalized_public = _normalized_topology(public)
        if topology not in (
            normalized_public,
            _reflected_topology(normalized_public),
        ):
            continue
        homogeneous = True
        for top, gap in witnesses:
            values = {grid[row][col] for row, col in _witness_cells(top, gap)}
            if len(values) != 1:
                homogeneous = False
                break
        if homogeneous:
            return f"public_{index + 1}"
    return None


def _analyze(grid):
    errors = _grid_error(grid)
    if errors:
        return {"errors": errors, "facts": None}
    height, width = len(grid), len(grid[0])
    flat = [value for row in grid for value in row]
    if 4 in flat:
        errors.append("input must not contain output marker color 4")
    if any(grid[-1]):
        errors.append("bottom row must start empty")
    witnesses = _detect_witnesses(grid)
    if not witnesses:
        errors.append("input must contain an inverted-U witness")
    gaps = sorted({gap for _, gap in witnesses})
    if len(gaps) != len(witnesses):
        errors.append("each witness must use a distinct gap column")
    covered = {
        cell for top, gap in witnesses for cell in _witness_cells(top, gap)
    }
    foreground = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    if foreground - covered:
        errors.append("all foreground cells must belong to inverted-U witnesses")
    profile = _canonical_profile(grid, witnesses) if witnesses else None
    return {
        "errors": errors,
        "facts": {
            "height": height,
            "width": width,
            "witnesses": tuple(witnesses),
            "gap_columns": tuple(gaps),
            "n_us": len(witnesses),
            "canonical_profile": profile,
            "scene_family": "linked" if profile else "generalized",
            "layout": (
                "row"
                if len({top for top, _ in witnesses}) == 1
                else "staggered"
            ),
            "colors": tuple(sorted(set(flat) - {0})),
        },
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["scene_family"]}


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return analysis["facts"]["canonical_profile"] or (
        f"generalized:{analysis['facts']['layout']}:"
        f"{analysis['facts']['n_us']}"
    )


def rule_mirror(grid):
    """Independent Python mirror used only by focused tests."""
    output = copy.deepcopy(grid)
    for gap in {gap for _, gap in _detect_witnesses(grid)}:
        output[-1][gap] = 4
    return output


def _paint_u(grid, top, gap, color):
    for row, col in _witness_cells(top, gap):
        grid[row][col] = color


def _build_linked(ctx, rng, difficulty):
    base_height, base_width, public = rng.choice(_PUBLIC_PROFILES)
    if difficulty == "easy":
        extra_height, extra_width = rng.randint(0, 2), rng.randint(0, 2)
    elif difficulty == "hard":
        extra_height, extra_width = rng.randint(4, 12), rng.randint(4, 12)
    else:
        extra_height, extra_width = rng.randint(0, 6), rng.randint(0, 6)
    height = min(30, base_height + extra_height)
    width = min(30, base_width + extra_width)
    grid = full_grid(height, width, 0)
    min_top = min(top for top, _ in public)
    max_leg = max(top + 1 for top, _ in public)
    min_gap = min(gap for _, gap in public)
    max_gap = max(gap for _, gap in public)
    row_shift = rng.randint(-min_top, height - 2 - max_leg)
    col_shift = rng.randint(1 - min_gap, width - 2 - max_gap)
    witnesses = [
        (top + row_shift, gap + col_shift) for top, gap in public
    ]
    if rng.random() < 0.5:
        witnesses = [(top, width - 1 - gap) for top, gap in witnesses]
    palette_count = rng.randint(1, len(witnesses))
    palette = list(ctx.draw_distinct_colors(
        "linked_colors",
        n=palette_count,
        exclude={0, 4},
    ))
    colors = [
        palette[index % len(palette)] for index in range(len(witnesses))
    ]
    rng.shuffle(colors)
    for (top, gap), color in zip(witnesses, colors):
        _paint_u(grid, top, gap, color)
    return grid


def _generalized_dimensions(ctx, difficulty):
    if difficulty == "easy":
        heights, widths = range(5, 8), range(8, 11)
    elif difficulty == "hard":
        heights, widths = range(10, 15), range(13, 19)
    else:
        heights, widths = range(7, 11), range(9, 15)
    choices = [
        (height, width)
        for height in heights
        for width in widths
        if (height, width) not in _PUBLIC_SHAPES
    ]
    return ctx.draw_choice("dimensions", choices)


def _build_generalized(ctx, rng, difficulty):
    for attempt in range(40):
        height, width = _generalized_dimensions(ctx, difficulty)
        max_count = min(4, (width - 1) // 3, height - 2)
        min_count = 2
        count = rng.randint(min_count, max(min_count, max_count))
        count = min(count, max_count)
        span = 3 * (count - 1)
        first_gap = rng.randint(1, width - 2 - span)
        gaps = [first_gap + 3 * index for index in range(count)]
        layout = rng.choice(("row", "staggered"))
        if layout == "row":
            top = rng.randint(0, height - 3)
            tops = [top] * count
        else:
            tops = sorted(rng.sample(range(height - 2), count))
            if len(set(tops)) == 1:
                continue
        palette_count = rng.randint(1, min(count, 4))
        palette = list(ctx.draw_distinct_colors(
            f"generalized_colors_{attempt}",
            n=palette_count,
            exclude={0, 4},
        ))
        colors = [palette[index % len(palette)] for index in range(count)]
        rng.shuffle(colors)
        grid = full_grid(height, width, 0)
        for top, gap, color in zip(tops, gaps, colors):
            _paint_u(grid, top, gap, color)
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["n_us"] == count
            and analysis["facts"]["scene_family"] == "generalized"
        ):
            return grid
    raise RuntimeError("could not construct a generalized inverted-U scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice("scene_family", SCENE_FAMILIES)
    rng = ctx.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        _build_linked(ctx, rng, band)
        if family == "linked"
        else _build_generalized(ctx, rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["scene_family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['scene_family']}"
                ]
            )
        )
    return grid
