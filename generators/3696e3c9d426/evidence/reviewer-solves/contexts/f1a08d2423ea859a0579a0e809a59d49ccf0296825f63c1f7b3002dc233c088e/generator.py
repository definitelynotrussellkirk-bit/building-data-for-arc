"""Semantic generator for ARC task 3696e3c9d426.

Each nonempty column is an independent gravity lane.  Reading from top to
bottom, preserve the nonzero color order and pack those cells at the bottom of
the same column.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3696e3c9d426"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e51db089d1da"
SUMMARY = (
    "For each column independently, collect its nonzero cells from top to "
    "bottom, clear that column, and place the collected values at the bottom "
    "without changing their order. Empty columns remain empty."
)
EXAMPLES_NEEDED = 3

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "canonical column-count profile or a novel lawful gravity scene",
    },
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

INVARIANTS = [
    "background is zero",
    "three to five columns contain nonzero cells",
    "at least two active columns contain multiple ordered cells",
    "every nonzero cell has a unique role color",
    "at least one active column has a gap or empty space below its cells",
    "gravity changes only row positions within each column",
]

_PUBLIC_INPUTS = (
    (
        (2, 0, 0, 0, 7, 0),
        (0, 0, 4, 0, 0, 0),
        (3, 0, 0, 0, 0, 0),
        (0, 0, 5, 0, 0, 0),
        (0, 0, 0, 0, 8, 0),
        (0, 0, 6, 0, 0, 0),
    ),
    (
        (0, 2, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 6, 0),
        (0, 3, 0, 5, 0, 0, 0),
        (0, 4, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 7, 0),
        (0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0),
    ),
    (
        (2, 0, 0, 0, 0, 3, 0, 0),
        (0, 0, 5, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 8, 0, 0),
        (4, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 6, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 9),
        (0, 0, 7, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0),
    ),
)


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _active_profile(grid):
    return tuple(
        (col, sum(grid[row][col] != 0 for row in range(len(grid))))
        for col in range(len(grid[0]))
        if any(grid[row][col] != 0 for row in range(len(grid)))
    )


def _mirror_profile(profile, width):
    return tuple(
        sorted((width - 1 - col, count) for col, count in profile)
    )


_PUBLIC_PROFILE_KEYS = tuple(
    (
        len(grid),
        len(grid[0]),
        min(
            _active_profile(grid),
            _mirror_profile(_active_profile(grid), len(grid[0])),
        ),
    )
    for grid in _PUBLIC_INPUTS
)


def _profile_key(grid):
    profile = _active_profile(grid)
    return (
        len(grid),
        len(grid[0]),
        min(profile, _mirror_profile(profile, len(grid[0]))),
    )


def _gravity_down(grid):
    height = len(grid)
    width = len(grid[0])
    output = full_grid(height, width, 0)
    for col in range(width):
        values = [
            grid[row][col]
            for row in range(height)
            if grid[row][col] != 0
        ]
        top = height - len(values)
        for offset, value in enumerate(values):
            output[top + offset][col] = value
    return output


def _has_descending_witness(grid):
    for col in range(len(grid[0])):
        values = [
            grid[row][col]
            for row in range(len(grid))
            if grid[row][col] != 0
        ]
        if any(left > right for left, right in zip(values, values[1:])):
            return True
    return False


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
    if not 4 <= height <= 14 or not 4 <= width <= 14:
        errors.append("grid dimensions must be 4..14")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    values = [value for row in grid for value in row if value != 0]
    active = _active_profile(grid)
    if not 3 <= len(active) <= 5:
        errors.append("exactly three to five columns must be active")
    if any(count > 3 for _, count in active):
        errors.append("active columns may contain at most three cells")
    if sum(count >= 2 for _, count in active) < 2:
        errors.append("at least two active columns need multiple cells")
    if not 6 <= len(values) <= 9:
        errors.append("scene must contain six to nine nonzero cells")
    if len(set(values)) != len(values):
        errors.append("nonzero role colors must be unique")
    output = _gravity_down(grid)
    if output == [list(row) for row in grid]:
        errors.append("gravity must visibly change the scene")
    facts = None
    if not errors:
        profile_index = next(
            (
                index
                for index, public_key in enumerate(_PUBLIC_PROFILE_KEYS)
                if _profile_key(grid) == public_key
            ),
            None,
        )
        facts = {
            "height": height,
            "width": width,
            "active_profile": active,
            "cell_count": len(values),
            "profile_index": profile_index,
            "scene_family": (
                "linked" if profile_index is not None else "generalized"
            ),
            "sorting_counterexample": _has_descending_witness(grid),
            "output": output,
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
    counts = "-".join(str(count) for _, count in facts["active_profile"])
    return f"generalized:{facts['height']}x{facts['width']}:{counts}"


def rule_mirror(grid):
    """Input-pure Python mirror used only for focused parity evidence."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["output"])


def _recolor_unique(rng, grid):
    values = [value for row in grid for value in row if value != 0]
    for _ in range(100):
        palette = rng.sample(range(1, 10), len(values))
        mapping = dict(zip(values, palette))
        recolored = [
            [mapping.get(value, value) for value in row]
            for row in grid
        ]
        if _has_descending_witness(recolored):
            return recolored
    raise RuntimeError("could not construct an order-preservation witness")


def _jitter_rows(rng, grid):
    height = len(grid)
    output = full_grid(height, len(grid[0]), 0)
    for col, count in _active_profile(grid):
        values = [
            grid[row][col]
            for row in range(height)
            if grid[row][col] != 0
        ]
        positions = sorted(rng.sample(range(height - 1), count))
        for row, value in zip(positions, values):
            output[row][col] = value
    return output


def _build_linked(rng):
    source = [list(row) for row in rng.choice(_PUBLIC_INPUTS)]
    if rng.random() < 0.08:
        return source
    if rng.random() < 0.5:
        source = [row[::-1] for row in source]
    source = _jitter_rows(rng, source)
    return _recolor_unique(rng, source)


def _count_pattern(rng, active_count):
    for _ in range(100):
        counts = [rng.randint(1, 3) for _ in range(active_count)]
        if 6 <= sum(counts) <= 9 and sum(count >= 2 for count in counts) >= 2:
            return counts
    raise RuntimeError("could not sample a feasible gravity count pattern")


def _ordered_colors(rng, counts):
    colors = rng.sample(range(1, 10), sum(counts))
    offset = 0
    has_descending = False
    first_multi_offset = None
    for count in counts:
        if count >= 2 and first_multi_offset is None:
            first_multi_offset = offset
        lane = colors[offset : offset + count]
        has_descending |= any(
            left > right for left, right in zip(lane, lane[1:])
        )
        offset += count
    if not has_descending:
        assert first_multi_offset is not None
        colors[first_multi_offset], colors[first_multi_offset + 1] = (
            colors[first_multi_offset + 1],
            colors[first_multi_offset],
        )
    return iter(colors)


def _build_generalized(rng, band):
    height = {"easy": 6, "medium": 7, "hard": 8}[band]
    width = height + rng.choice((-1, 0, 1))
    for _ in range(100):
        active_count = rng.randint(3, min(5, width))
        columns = sorted(rng.sample(range(width), active_count))
        counts = _count_pattern(rng, active_count)
        colors = _ordered_colors(rng, counts)
        grid = full_grid(height, width, 0)
        for col, count in zip(columns, counts):
            rows = sorted(rng.sample(range(height - 1), count))
            for row in rows:
                grid[row][col] = next(colors)
        if _profile_key(grid) not in _PUBLIC_PROFILE_KEYS:
            return grid
    raise RuntimeError("could not construct a non-canonical gravity scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = context.draw_choice("scene_family", SCENE_FAMILIES)
    rng = context.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        _build_linked(rng)
        if family == "linked"
        else _build_generalized(rng, band)
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
