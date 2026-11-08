"""Generator for the size-to-color legend task ``a7e26e20850c``.

The first row is a legend: each nonzero run's length is an object size and the
run color is that size's output color.  Three separated gray objects occupy the
body.  The canonical Racket rule remains the label authority; the Python solver
below exists only to define and test a declared canonical-fitting rival.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations, product
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a7e26e20850c"
TASK_ID = GENERATOR_ID
RULE_HASH = "704fe040d74c"
VERSION = "2.0.0"

SUMMARY = (
    "Separated top-row run lengths map gray body-object sizes to recolor "
    "targets; every instance contains exactly three gray objects."
)

INVARIANTS = [
    "background is 0 and the separator row is blank",
    "the top row has 2..4 zero-separated, distinct-color runs of unique lengths 2..5",
    "the body has exactly three pairwise 8-separated, 4-connected gray(5) objects",
    "every gray object size occurs in the legend",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "7..13; three-entry schedule uses canonical 10/11/12 anchors",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "12..18; four-entry legends require 17..18",
        "valid": "12..18",
    },
    "n_sizes": {
        "type": "int",
        "default": "period-4 schedule 2,4,3,4",
        "valid": "2..4",
    },
}

# Four distinct lengths 2+3+4+5 plus three mandatory separator cells need 17
# columns.  Enumerating exact pairs makes the override contract machine-readable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = tuple(
    {"n_sizes": 4, "grid_w": width} for width in range(12, 17)
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "two_sizes",
    "four_sizes_a",
    "three_sizes",
    "four_sizes_b",
)
MIN_STRICT_FRAC = 1.0

_PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)
_SIZE_DOMAIN = (2, 3, 4, 5)
_PROFILE_SIZE_COUNT = {
    "two_sizes": 2,
    "three_sizes": 3,
    "four_sizes_a": 4,
    "four_sizes_b": 4,
}

# Seed shapes are expanded through every dihedral orientation below.  Each one
# is 4-connected and fits a 3x3 box, which makes minimum-canvas placement
# constructive rather than retry-based.
_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (
        ((0, 0), (0, 1)),
    ),
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _orientations(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    original = tuple(cells)
    for reflected in (False, True):
        points = tuple((r, -c if reflected else c) for r, c in original)
        for _ in range(4):
            variants.add(_normalize(points))
            points = tuple((c, -r) for r, c in points)
    return tuple(sorted(variants))


SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    size: tuple(
        sorted(
            {
                orientation
                for base in bases
                for orientation in _orientations(base)
            }
        )
    )
    for size, bases in _BASE_SHAPES.items()
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the fixed teaching profile for a sample index."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    bounds = {"grid_h": (7, 13), "grid_w": (12, 18), "n_sizes": (2, 4)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool, float, or string)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    if overrides.get("n_sizes") == 4 and overrides.get("grid_w") in range(12, 17):
        raise ValueError("incompatible overrides: a four-entry legend requires grid_w >= 17")


def _has_override(overrides: dict[str, Any], name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _difficulty_tag(difficulty: str | None) -> str:
    return "none" if difficulty is None else difficulty


def _weighted_height_options(difficulty: str | None) -> tuple[int, ...]:
    full = tuple(range(7, 14))
    if difficulty == "easy":
        return full + (10, 10, 11, 11, 12)
    if difficulty == "medium":
        return full + (9, 10, 11, 12, 13)
    if difficulty == "hard":
        return full + (7, 8, 9, 12, 13, 13)
    return full + (10, 10, 11, 11, 12, 12)


def _weighted_width_options(n_sizes: int, difficulty: str | None) -> tuple[int, ...]:
    legal = tuple(range(17, 19)) if n_sizes == 4 else tuple(range(12, 19))
    if n_sizes == 4:
        return legal + ((17, 17, 18) if difficulty != "hard" else (17, 18, 18))
    if difficulty == "easy":
        favored = (14, 14, 15, 15, 16)
    elif difficulty == "medium":
        favored = (13, 14, 15, 16, 17)
    elif difficulty == "hard":
        favored = (12, 13, 16, 17, 18, 18)
    else:
        favored = (14, 14, 15, 15, 16, 16)
    return legal + favored


def _draw_axes(ctx, seed: int, sample_index: int, difficulty, overrides):
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_n = _PROFILE_SIZE_COUNT[profile]

    if _has_override(overrides, "n_sizes"):
        n_sizes = ctx.draw_int_strict("n_sizes", 2, 4)
    else:
        # A lone narrow-width override remains usable: adapt the unspecified
        # count instead of turning a valid scalar override into a hidden pair
        # rejection.  Unoverridden lessons retain the declared schedule.
        requested_w = overrides.get("grid_w")
        chosen_n = 3 if scheduled_n == 4 and requested_w in range(12, 17) else scheduled_n
        n_sizes = ctx.draw_choice("n_sizes", (chosen_n,))

    anchor_pair = None
    if profile == "three_sizes" and n_sizes == 3:
        band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
        anchor_pair = ((10, 14), (11, 15), (12, 16))[
            (seed + sample_index // LESSON_SCHEDULE_PERIOD + band_offset) % 3
        ]

    if _has_override(overrides, "grid_h"):
        height = ctx.draw_int_strict("grid_h", 7, 13)
    elif anchor_pair is not None:
        height = ctx.draw_choice("grid_h", (anchor_pair[0],))
    else:
        height = ctx.draw_choice("grid_h", _weighted_height_options(difficulty))

    if _has_override(overrides, "grid_w"):
        width = ctx.draw_int_strict("grid_w", 12, 18)
    elif anchor_pair is not None:
        width = ctx.draw_choice("grid_w", (anchor_pair[1],))
    else:
        width = ctx.draw_choice("grid_w", _weighted_width_options(n_sizes, difficulty))

    if n_sizes == 4 and width < 17:
        raise ValueError("incompatible n_sizes/grid_w: four legend entries require width >= 17")
    return height, width, n_sizes


def _feasible_size_sets(n_sizes: int, width: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        choice
        for choice in combinations(_SIZE_DOMAIN, n_sizes)
        if sum(choice) + n_sizes - 1 <= width
    )


def _legend_layouts(sizes: tuple[int, ...], width: int):
    layouts = []
    for gaps in product((1, 2), repeat=max(0, len(sizes) - 1)):
        occupied = sum(sizes) + sum(gaps)
        for start in range(width - occupied + 1):
            layouts.append((start, gaps))
    return tuple(layouts)


def _slot_layouts(width: int):
    """Enumerate three >=3-column slots separated by one or two blanks."""
    layouts = []
    for gaps in product((1, 2), repeat=2):
        for widths in product(range(3, width + 1), repeat=3):
            occupied = sum(widths) + sum(gaps)
            if occupied > width:
                continue
            for left_margin in range(width - occupied + 1):
                starts = (
                    left_margin,
                    left_margin + widths[0] + gaps[0],
                    left_margin + widths[0] + gaps[0] + widths[1] + gaps[1],
                )
                layouts.append(tuple(zip(starts, widths)))
    return tuple(layouts)


def _shape_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _paint(grid, cells, top, left, color):
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _place_three_objects(grid, object_sizes, rng) -> None:
    h, w = len(grid), len(grid[0])
    layouts = _slot_layouts(w)
    if not layouts:
        raise RuntimeError(f"no constructive three-slot layout for width {w}")
    slots = rng.choice(layouts)
    assignments = list(object_sizes)
    rng.shuffle(assignments)
    for size, (slot_start, slot_width) in zip(assignments, slots):
        choices = [
            shape
            for shape in SHAPES[size]
            if _shape_dims(shape)[0] <= h - 2 and _shape_dims(shape)[1] <= slot_width
        ]
        if not choices:
            raise RuntimeError(f"no size-{size} orientation fits {h}x{slot_width} body slot")
        shape = rng.choice(choices)
        shape_h, shape_w = _shape_dims(shape)
        top = rng.randint(2, h - shape_h)
        left = rng.randint(slot_start, slot_start + slot_width - shape_w)
        _paint(grid, shape, top, left, 5)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_sizes = _draw_axes(ctx, seed, sample_index, difficulty, overrides)
    tag = _difficulty_tag(difficulty)

    legend_rng = ctx.draw_rng(f"legend:{tag}")
    feasible = _feasible_size_sets(n_sizes, w)
    if not feasible:
        raise ValueError(f"no {n_sizes}-entry size legend fits width {w}")
    sizes = list(legend_rng.choice(feasible))
    legend_rng.shuffle(sizes)
    sizes_tuple = tuple(sizes)
    colors = tuple(legend_rng.sample(_PALETTE, n_sizes))
    layouts = _legend_layouts(sizes_tuple, w)
    if not layouts:
        raise RuntimeError("legend layout enumeration unexpectedly empty")
    start, gaps = legend_rng.choice(layouts)

    grid = full_grid(h, w, 0)
    col = start
    for index, (size, color) in enumerate(zip(sizes_tuple, colors)):
        for offset in range(size):
            grid[0][col + offset] = color
        if index < len(gaps):
            col += size + gaps[index]

    object_rng = ctx.draw_rng(f"objects:{tag}")
    if n_sizes == 2:
        object_sizes = [sizes[0], sizes[1], object_rng.choice(sizes)]
    elif n_sizes == 3:
        object_sizes = list(sizes)
    else:
        # Always use the fourth run in a four-entry lesson.  This makes the
        # declared first-three-only shortcut observably wrong while retaining
        # one intentionally unused legend entry, as canonical data permits.
        object_sizes = object_rng.sample(sizes[:3], 2) + [sizes[3]]
    _place_three_objects(grid, object_sizes, object_rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator violated its invariants: " + "; ".join(errors))
    return grid


def _legend_runs(grid) -> list[tuple[int, int, int, int]]:
    """Return ``(size, color, start, end)`` for each top-row run."""
    row = grid[0]
    runs = []
    col = 0
    while col < len(row):
        if row[col] == 0:
            col += 1
            continue
        color = row[col]
        start = col
        while col < len(row) and row[col] == color:
            col += 1
        runs.append((col - start, color, start, col))
    return runs


def _gray_components(grid) -> list[frozenset[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r in range(1, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 5
    }
    components = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(frozenset(component))
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer ARC colors 0..9"]

    height = len(grid)
    errors = []
    if not 7 <= height <= 13:
        errors.append(f"grid_h={height} outside [7,13]")
    if not 12 <= width <= 18:
        errors.append(f"grid_w={width} outside [12,18]")
    if height < 2:
        return errors + ["grid needs a legend row and separator row"]
    if any(grid[1][c] != 0 for c in range(width)):
        errors.append("row 1 must be a blank separator")

    row = grid[0]
    # Adjacent differently colored cells would be separate Racket runs but
    # violate the advertised zero-separated legend grammar.
    for col in range(1, width):
        if row[col - 1] != 0 and row[col] != 0 and row[col - 1] != row[col]:
            errors.append("legend runs must be separated by at least one zero")
            break
    runs = _legend_runs(grid)
    if not 2 <= len(runs) <= 4:
        errors.append(f"legend must contain 2..4 runs, found {len(runs)}")
    lengths = [size for size, _, _, _ in runs]
    colors = [color for _, color, _, _ in runs]
    if any(size not in _SIZE_DOMAIN for size in lengths):
        errors.append("legend run lengths must be in 2..5")
    if len(set(lengths)) != len(lengths):
        errors.append("legend run lengths must be unique")
    if any(color in (0, 5) for color in colors):
        errors.append("legend colors may not be background 0 or object gray 5")
    if len(set(colors)) != len(colors):
        errors.append("legend colors must be distinct")

    bad_body = [
        (r, c, grid[r][c])
        for r in range(2, height)
        for c in range(width)
        if grid[r][c] not in (0, 5)
    ]
    if bad_body:
        errors.append("body rows may contain only background 0 and gray 5")

    components = _gray_components(grid)
    if len(components) != 3:
        errors.append(f"body must contain exactly three gray objects, found {len(components)}")
    legal_sizes = set(lengths)
    for component in components:
        if len(component) not in legal_sizes:
            errors.append(
                f"gray object size {len(component)} is absent from legend sizes {sorted(legal_sizes)}"
            )

    owner = {point: index for index, component in enumerate(components) for point in component}
    diagonally_touching = False
    for (r, c), index in owner.items():
        for dr, dc in product((-1, 0, 1), repeat=2):
            if not (dr or dc):
                continue
            other = owner.get((r + dr, c + dc))
            if other is not None and other != index:
                diagonally_touching = True
                break
        if diagonally_touching:
            break
    if diagonally_touching:
        errors.append("distinct gray objects must be separated in the 8-neighborhood")
    return errors


def strict_canonical_like(grid):
    """Accept exactly the lawful manifold documented by this generator."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every declared exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_sizes": len(_legend_runs(grid)),
    }


def _recolor_by_size(grid, *, legend_limit: int | None = None, leave_missing: bool = False):
    """Pure Python semantic probe; never used as generation label authority."""
    out = deepcopy(grid)
    runs = _legend_runs(grid)
    if legend_limit is not None:
        runs = runs[:legend_limit]
    mapping = {size: color for size, color, _, _ in runs}
    for component in _gray_components(grid):
        color = mapping.get(len(component))
        if color is None:
            if leave_missing:
                continue
            raise ValueError(f"no legend entry for object size {len(component)}")
        for r, c in component:
            out[r][c] = color
    return out


def _first_three_legend_entries(grid):
    """Rival: incorrectly ignores every legend run after the third."""
    return _recolor_by_size(grid, legend_limit=3, leave_missing=True)


def _fourth_legend_used(grid) -> bool:
    try:
        runs = _legend_runs(grid)
        if len(runs) < 4:
            return False
        fourth_size = runs[3][0]
        return any(len(component) == fourth_size for component in _gray_components(grid))
    except (IndexError, TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {"fourth_legend_used": _fourth_legend_used}
SEMANTIC_RIVALS = {"first_three_legend_entries": _first_three_legend_entries}
WITNESS_RIVALS = {"fourth_legend_used": ["first_three_legend_entries"]}
CANONICAL_SHORTCUTS = {"first_three_legend_entries": _first_three_legend_entries}
LESSON_COMPETITORS = {"first_three_legend_entries": _first_three_legend_entries}


def lesson_identifiable(demos, query):
    """Reject a lesson only when a declared rival fits demos but changes query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if fits and rival(query["input"]) != query["output"]:
                reasons.append(f"declared rival {name!r} fits demonstrations but changes query")
        except Exception as exc:  # visible diagnostic, never silent acceptance
            reasons.append(f"declared rival {name!r} failed: {type(exc).__name__}: {exc}")
    return reasons
