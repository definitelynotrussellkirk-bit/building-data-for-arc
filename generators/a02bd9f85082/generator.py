"""Semantic generator for ARC task a02bd9f85082.

The first four cells are a color legend.  A monochrome source motif and a
gray pivot appear below it.  The solution makes quarter-turn copies of the
motif around the pivot and colors turns 0, 1, 2, and 3 with the corresponding
legend colors.  Later turns overwrite earlier ones where copies overlap.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a02bd9f85082"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "8efe879cb0b7"
SUMMARY = (
    "Read the contiguous four-color legend, then rotate the monochrome source "
    "motif by quarter turns around the gray pivot and recolor the four turns "
    "in legend order; later turns win at overlaps."
)
EXAMPLES_NEEDED = 4

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "a public relative motif or a novel connected relative motif",
    },
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

INVARIANTS = [
    "background is zero and the first four top-row cells are distinct colors",
    "the rest of the top row is blank",
    "one gray cell below the legend is the rotation pivot",
    "all other nonzero cells form one monochrome motif connected directly or through the pivot",
    "the source color differs from the pivot and all four legend colors",
    "every quarter-turn copy stays in bounds and all four turn colors remain visible",
    "overlap cases preserve the rule's later-turn overwrite order",
]

_PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)

# Relative coordinates are measured from the pivot.  These are the five
# official source/pivot arrangements, before optional whole-scene D4 turns.
_PUBLIC_PROFILES = (
    ((-2, -1), (-1, -1), (-1, 0)),
    ((-2, 0), (-1, 0), (-1, 1), (0, 1)),
    ((-3, 0), (-2, 0), (-2, 1)),
    ((-2, -1), (-1, -1), (-1, 0), (0, -1)),
    ((-2, 0), (-1, 0), (0, -1), (0, 1)),
)

# Lawful connected motifs that are not D4 copies of the public profiles.
_GENERALIZED_PROFILES = (
    ((-3, -1), (-2, -1), (-1, -1), (-1, 0)),
    ((-3, -2), (-2, -2), (-2, -1), (-2, 0), (-1, 0)),
    ((-3, 0), (-2, 0), (-1, 0), (-1, 1), (0, 1)),
    ((-2, -1), (-2, 0), (-2, 1), (-1, 0)),
    ((-3, -1), (-2, -1), (-1, -1), (-2, 0), (-2, 1)),
    ((-3, -2), (-3, -1), (-2, -1), (-1, -1), (-1, 0), (-1, 1)),
    ((-2, 0), (-1, 0), (0, -1), (0, 1), (1, 1)),
)


def _turn_cell(delta, turn):
    row, col = delta
    return (
        (row, col),
        (col, -row),
        (-row, -col),
        (-col, row),
    )[turn]


def _transform_profile(profile, turn, reflect):
    transformed = []
    for row, col in profile:
        if reflect:
            col = -col
        transformed.append(_turn_cell((row, col), turn))
    return tuple(sorted(transformed))


def _profile_variants(profile):
    return {
        _transform_profile(profile, turn, reflect)
        for turn in range(4)
        for reflect in (False, True)
    }


_PUBLIC_VARIANTS = tuple(_profile_variants(profile) for profile in _PUBLIC_PROFILES)
_GENERALIZED_VARIANTS = tuple(
    _profile_variants(profile) for profile in _GENERALIZED_PROFILES
)


def _profile_index(relative_cells):
    key = tuple(sorted(relative_cells))
    return next(
        (
            index
            for index, variants in enumerate(_PUBLIC_VARIANTS)
            if key in variants
        ),
        None,
    )


def _generalized_profile_index(relative_cells):
    key = tuple(sorted(relative_cells))
    return next(
        (
            index
            for index, variants in enumerate(_GENERALIZED_VARIANTS)
            if key in variants
        ),
        None,
    )


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    todo = [next(iter(remaining))]
    seen = {todo[0]}
    while todo:
        row, col = todo.pop()
        for delta_row, delta_col in (
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
        ):
            neighbor = (row + delta_row, col + delta_col)
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    return seen == remaining


def _rule_output(grid, legend, pivot, source):
    height = len(grid)
    width = len(grid[0])
    output = full_grid(height, width, 0)
    for col, color in enumerate(legend):
        output[0][col] = color
    output[pivot[0]][pivot[1]] = 5
    for turn in range(4):
        color = legend[turn]
        for row, col in source:
            relative = (row - pivot[0], col - pivot[1])
            delta_row, delta_col = _turn_cell(relative, turn)
            target_row = pivot[0] + delta_row
            target_col = pivot[1] + delta_col
            if 0 <= target_row < height and 0 <= target_col < width:
                output[target_row][target_col] = color
    return output


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if not (9 <= height <= 13 and 9 <= width <= 13):
        errors.append("grid dimensions must be 9..13")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    if errors:
        return {"errors": errors, "facts": None}

    legend = tuple(grid[0][:4])
    if (
        len(legend) != 4
        or any(color not in _PALETTE for color in legend)
        or len(set(legend)) != 4
    ):
        errors.append("top-left legend must contain four distinct nonzero non-gray colors")
    if any(value != 0 for value in grid[0][4:]):
        errors.append("top row cells after the four-color legend must be zero")

    pivots = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] == 5
    ]
    if len(pivots) != 1:
        errors.append(f"expected one gray pivot below row zero, found {len(pivots)}")
    source_cells = [
        (row, col, grid[row][col])
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]
    source_colors = {value for _row, _col, value in source_cells}
    if not 3 <= len(source_cells) <= 6:
        errors.append(f"source motif must contain 3..6 cells, found {len(source_cells)}")
    if len(source_colors) != 1:
        errors.append("source motif must be monochrome")
    elif next(iter(source_colors)) in legend:
        errors.append("source color must differ from all legend colors")
    source = tuple((row, col) for row, col, _value in source_cells)
    if source and not (
        _connected(source)
        or (
            len(pivots) == 1
            and _connected(source + (pivots[0],))
        )
    ):
        errors.append("source motif must be connected directly or through the pivot")

    facts = None
    if len(pivots) == 1 and source and not errors:
        pivot = pivots[0]
        relative = tuple(
            sorted((row - pivot[0], col - pivot[1]) for row, col in source)
        )
        if (0, 0) in relative:
            errors.append("source motif may not occupy the pivot")
        owners = {}
        out_of_bounds = []
        for turn in range(4):
            for delta in relative:
                delta_row, delta_col = _turn_cell(delta, turn)
                target = (pivot[0] + delta_row, pivot[1] + delta_col)
                if not (0 <= target[0] < height and 0 <= target[1] < width):
                    out_of_bounds.append((turn, target))
                owners[target] = turn
        if out_of_bounds:
            errors.append("all generated quarter-turn cells must stay in bounds")
        visible_turns = set(owners.values())
        if visible_turns != {0, 1, 2, 3}:
            errors.append("all four legend turns must remain visible after overwrites")
        if not errors:
            profile_index = _profile_index(relative)
            generalized_profile_index = _generalized_profile_index(relative)
            unique_positions = len(owners)
            total_turn_cells = 4 * len(source)
            facts = {
                "height": height,
                "width": width,
                "legend": legend,
                "pivot": pivot,
                "source": source,
                "relative": relative,
                "source_color": next(iter(source_colors)),
                "source_size": len(source),
                "profile_index": profile_index,
                "generalized_profile_index": generalized_profile_index,
                "scene_family": (
                    "linked" if profile_index is not None else "generalized"
                ),
                "unique_orbit_positions": unique_positions,
                "overlap_count": total_turn_cells - unique_positions,
                "visible_turns": tuple(sorted(visible_turns)),
                "output": _rule_output(grid, legend, pivot, source),
            }
    return {"errors": errors, "facts": facts}


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
    facts = analysis["facts"]
    if facts["profile_index"] is not None:
        return f"public_profile_{facts['profile_index'] + 1}"
    if facts["generalized_profile_index"] is not None:
        return (
            f"generalized_profile_{facts['generalized_profile_index'] + 1}:"
            f"overlaps={facts['overlap_count']}"
        )
    return (
        f"generalized:size={facts['source_size']}:"
        f"overlaps={facts['overlap_count']}"
    )


def rule_mirror(grid):
    """Input-pure Python mirror used only for focused parity evidence."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["output"])


def _choose_dimensions(rng, difficulty):
    if difficulty == "easy":
        options = ((9, 9), (11, 11))
    elif difficulty == "hard":
        options = ((11, 11), (11, 13), (13, 11), (13, 13))
    else:
        options = ((9, 9), (11, 11), (11, 13), (13, 11))
    return rng.choice(options)


def _choose_profile(rng, difficulty, scene_family):
    if scene_family == "linked":
        return rng.choice(_PUBLIC_PROFILES)
    if difficulty == "easy":
        options = _GENERALIZED_PROFILES[:3]
    elif difficulty == "hard":
        options = _GENERALIZED_PROFILES[2:]
    else:
        options = _GENERALIZED_PROFILES
    return rng.choice(options)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_family = ctx.draw_choice("scene_family", SCENE_FAMILIES)
    rng = ctx.draw_rng("layout")
    height, width = _choose_dimensions(rng, difficulty)
    profile = _choose_profile(rng, difficulty, scene_family)
    profile = _transform_profile(
        profile,
        rng.randrange(4),
        bool(rng.randrange(2)),
    )

    grid = full_grid(height, width, 0)
    legend = rng.sample(list(_PALETTE), 4)
    for col, color in enumerate(legend):
        grid[0][col] = color
    source_color = rng.choice(
        [color for color in _PALETTE if color not in legend]
    )
    pivot = (height // 2, width // 2)
    grid[pivot[0]][pivot[1]] = 5
    for delta_row, delta_col in profile:
        grid[pivot[0] + delta_row][pivot[1] + delta_col] = source_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    return grid
