"""Constructive inputs for ``sorted sizes of the red components``.

The Racket authority finds 4-connected monochromatic objects, keeps color 2,
sorts their cell counts, and returns those counts as a one-row grid.  This
sampler stays on the five canonical canvas/palette profiles while deliberately
teaching three distinctions that the canonical examples leave ambiguous:
repeated component sizes, diagonal-only contact, and component sizes above 5.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations, combinations_with_replacement
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "52d56c2a0191"
TASK_ID = GENERATOR_ID
RULE_HASH = "5c9566dd0981"
VERSION = "4.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, str]] = []

SCENE_PROFILES = ("canonical", "repeated", "diagonal", "large")
CANVAS_PROFILES = (
    "h10_w12_p7",
    "h10_w13_p5",
    "h11_w10_p4",
    "h13_w11_p5",
    "h13_w13_p5",
)
CANVAS_SPECS = {
    "h10_w12_p7": (10, 12, 7),
    "h10_w13_p5": (10, 13, 5),
    "h11_w10_p4": (11, 10, 4),
    "h13_w11_p5": (13, 11, 5),
    "h13_w13_p5": (13, 13, 5),
}
_SPEC_TO_CANVAS = {spec: name for name, spec in CANVAS_SPECS.items()}

SUMMARY = (
    "A canonical-profile ARC canvas contains three to five 4-connected red (2) "
    "components plus non-red distractors. Return one row containing every red "
    "component's cell count in ascending order. Repeated sizes are retained, "
    "diagonal contact does not connect components, and lawful sizes can exceed 5."
)

INVARIANTS = [
    "canvas dimensions and palette count exactly match one selected canonical profile",
    "three to five 4-connected red components, each with 1..9 cells",
    "at least two distinct non-red distractor colors are present",
    "the output is the sorted multiset of red 4-connected component sizes",
]

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "4-slot schedule: canonical, repeated, diagonal, large",
        "valid": "|".join(SCENE_PROFILES),
    },
    "canvas_profile": {
        "type": "str",
        "default": "5-slot cycle over the exact canonical shape/palette profiles",
        "valid": "|".join(CANVAS_PROFILES),
    },
}

# Every construction fits in a 10x10 local frame.  Five separated slots hold
# arbitrary connected prefixes of a 3x3 spiral; the narrow top-right slot still
# supports every <=5 canonical/repeated size.  Diagonal/large profiles reserve
# that top-right region for an intentional diagonal pair of red singletons.
_PATH_3X3 = (
    (0, 0), (0, 1), (1, 1), (1, 0), (2, 0),
    (2, 1), (2, 2), (1, 2), (0, 2),
)
_PATH_3X2 = ((0, 0), (0, 1), (1, 1), (1, 0), (2, 0), (2, 1))
_STANDARD_SLOTS = (
    ((0, 0), _PATH_3X3),
    ((0, 4), _PATH_3X3),
    ((0, 8), _PATH_3X2),
    ((4, 0), _PATH_3X3),
    ((4, 4), _PATH_3X3),
)
_WIDE_SLOTS = (
    ((0, 0), _PATH_3X3),
    ((0, 4), _PATH_3X3),
    ((4, 0), _PATH_3X3),
    ((4, 4), _PATH_3X3),
)
_DIAGONAL_SINGLETONS = (((0, 8),), ((1, 9),))
_DISTRACTOR_SLOTS = ((9, 0), (9, 2), (9, 4), (9, 6), (9, 8))

_CANONICAL_SIZE_OPTIONS = tuple(
    values
    for count in (3, 4, 5)
    for values in combinations(range(1, 6), count)
)
_REPEATED_SIZE_OPTIONS = tuple(
    values
    for values in combinations_with_replacement(range(1, 6), 4)
    if len(set(values)) < 4
)
_DIAGONAL_SIZE_OPTIONS = tuple(
    (1, 1, small, large)
    for small in range(2, 6)
    for large in range(6, 10)
)
_LARGE_SIZE_OPTIONS = tuple(
    (1, 1, small_a, small_b, large)
    for small_a in range(2, 6)
    for small_b in range(small_a, 6)
    for large in range(6, 10)
)
_SIZE_OPTIONS = {
    "canonical": _CANONICAL_SIZE_OPTIONS,
    "repeated": _REPEATED_SIZE_OPTIONS,
    "diagonal": _DIAGONAL_SIZE_OPTIONS,
    "large": _LARGE_SIZE_OPTIONS,
}


def _validate_request(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{name} must be a string")
        domain = SCENE_PROFILES if name == "scene_profile" else CANVAS_PROFILES
        if value not in domain:
            raise ValueError(f"{name} must be one of {domain}")


def _scheduled_choice(ctx, label: str, domain: tuple[str, ...], scheduled: str) -> str:
    """Record a one-slot schedule while keeping every exact override lawful."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, domain)
    return ctx.draw_choice(label, (scheduled,))


def _transform_local(cell: tuple[int, int], *, flip_rows: bool, flip_columns: bool) -> tuple[int, int]:
    row, column = cell
    if flip_rows:
        row = 9 - row
    if flip_columns:
        column = 9 - column
    return row, column


def _slot_component(origin, path, size: int) -> tuple[tuple[int, int], ...]:
    if not 1 <= size <= len(path):
        raise ValueError(f"slot capacity {len(path)} cannot hold component size {size}")
    row0, column0 = origin
    return tuple((row0 + row, column0 + column) for row, column in path[:size])


def _draw_component_sizes(ctx, scene_profile: str) -> tuple[int, ...]:
    options = _SIZE_OPTIONS[scene_profile]
    return tuple(ctx.draw_rng(f"component_sizes_{ctx.difficulty or 'all'}").choice(options))


def _red_components_for_sizes(ctx, scene_profile: str, sizes: tuple[int, ...]):
    rng = ctx.draw_rng(f"component_assignment_{ctx.difficulty or 'all'}")
    if scene_profile in ("canonical", "repeated"):
        slots = list(_STANDARD_SLOTS)
        rng.shuffle(slots)
        # The only six-cell-capacity slot receives a <=5 component; every size
        # in these profiles is <=5, so all shuffled assignments are lawful.
        return [
            _slot_component(origin, path, size)
            for size, (origin, path) in zip(sizes, slots)
        ]

    # Two singleton components are placed diagonally, not orthogonally.  The
    # remaining sizes use full 3x3 slots, including the required >5 witness.
    remaining = list(sizes)
    remaining.remove(1)
    remaining.remove(1)
    slots = list(_WIDE_SLOTS)
    rng.shuffle(slots)
    components = [tuple(cells) for cells in _DIAGONAL_SINGLETONS]
    components.extend(
        _slot_component(origin, path, size)
        for size, (origin, path) in zip(remaining, slots)
    )
    return components


def _build_scene(ctx, scene_profile: str, canvas_profile: str):
    height, width, palette_count = CANVAS_SPECS[canvas_profile]
    grid = full_grid(height, width, 0)
    rng = ctx.draw_rng(f"layout_{ctx.difficulty or 'all'}")

    # Transform the complete 10x10 construction together, preserving every
    # connectivity and separation property. Extra canonical canvas space allows
    # a deterministic translation as another source of layout diversity.
    flip_rows = rng.choice((False, True))
    flip_columns = rng.choice((False, True))
    row_offset = rng.randint(0, height - 10)
    column_offset = rng.randint(0, width - 10)

    def place(cell: tuple[int, int], color: int) -> None:
        local_row, local_column = _transform_local(
            cell, flip_rows=flip_rows, flip_columns=flip_columns
        )
        row, column = local_row + row_offset, local_column + column_offset
        if grid[row][column] != 0:
            raise RuntimeError(f"constructive template overlap at {(row, column)}")
        grid[row][column] = color

    sizes = _draw_component_sizes(ctx, scene_profile)
    components = _red_components_for_sizes(ctx, scene_profile, sizes)
    for component in components:
        for cell in component:
            place(cell, 2)

    distractor_count = palette_count - 2  # background 0 and red 2 occupy two slots
    colors = list(
        ctx.draw_distinct_colors(
            f"distractor_colors_{ctx.difficulty or 'all'}", n=distractor_count, exclude=(0, 2)
        )
    )
    slots = list(_DISTRACTOR_SLOTS[:distractor_count])
    rng.shuffle(colors)
    rng.shuffle(slots)
    for cell, color in zip(slots, colors):
        place(cell, color)

    expected = {"scene_profile": scene_profile, "canvas_profile": canvas_profile}
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(
            "constructed scene violated its exact observable contract: "
            f"expected {expected}, observed {observed}, sizes={sizes}"
        )
    return grid


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
    scene_profile = _scheduled_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        SCENE_PROFILES[sample_index % len(SCENE_PROFILES)],
    )
    canvas_profile = _scheduled_choice(
        ctx,
        "canvas_profile",
        CANVAS_PROFILES,
        CANVAS_PROFILES[sample_index % len(CANVAS_PROFILES)],
    )
    return _build_scene(ctx, scene_profile, canvas_profile)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"grid dimensions must be within ARC bounds, got {len(grid)}x{width}"]
    return []


def _components_of_color(grid, color: int, *, diagonal: bool = False) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        directions.extend(((-1, -1), (-1, 1), (1, -1), (1, 1)))
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for column in range(width):
            start = (row, column)
            if grid[row][column] != color or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_column = queue.popleft()
                cells.append((current_row, current_column))
                for dr, dc in directions:
                    nr, nc = current_row + dr, current_column + dc
                    neighbor = (nr, nc)
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            components.append(tuple(cells))
    return components


def _all_nonzero_components(grid) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    result: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for color in sorted({value for row in grid for value in row} - {0}):
        result.extend((color, cells) for cells in _components_of_color(grid, color))
    return result


def _red_sizes(grid, *, diagonal: bool = False) -> list[int]:
    return sorted(len(cells) for cells in _components_of_color(grid, 2, diagonal=diagonal))


def _scene_profile(grid) -> str | None:
    sizes4 = _red_sizes(grid)
    if not sizes4:
        return None
    sizes8 = _red_sizes(grid, diagonal=True)
    count = len(sizes4)
    repeated = len(sizes4) != len(set(sizes4))
    diagonal_contact = sizes4 != sizes8
    maximum = max(sizes4)

    if not diagonal_contact and maximum <= 5 and 3 <= count <= 5:
        return "repeated" if count == 4 and repeated else "canonical"
    if diagonal_contact and maximum > 5 and count == 4:
        return "diagonal"
    if diagonal_contact and maximum > 5 and count == 5 and repeated:
        return "large"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected canonical-profile domain, not merely ARC syntax."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    canvas_profile = _SPEC_TO_CANVAS.get((height, width, len(palette)))
    if canvas_profile is None:
        errors.append(
            "canvas dimensions/palette must match one canonical profile; "
            f"got {height}x{width} with {len(palette)} colors"
        )
    if 0 not in palette:
        errors.append("background color 0 must be present")
    if 2 not in palette:
        errors.append("at least one red (2) component is required")
    if len(palette - {0, 2}) < 2:
        errors.append("at least two distinct non-red distractor colors are required")
    if errors:
        return errors

    sizes = _red_sizes(grid)
    if not 3 <= len(sizes) <= 5:
        errors.append(f"expected 3..5 red components, got {len(sizes)}")
    if any(not 1 <= size <= 9 for size in sizes):
        errors.append(f"red component sizes must be in 1..9, got {sizes}")
    scene_profile = _scene_profile(grid)
    if scene_profile is None:
        errors.append(
            "red components do not match a supported semantic profile "
            f"(4-connected sizes={sizes}, 8-connected sizes={_red_sizes(grid, diagonal=True)})"
        )
    return errors


def strict_canonical_like(grid):
    """The full sampler and all selected canonical inputs are strict-profile cases."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    spec = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    return {
        "scene_profile": _scene_profile(grid),
        "canvas_profile": _SPEC_TO_CANVAS[spec],
    }


def rule_mirror(grid):
    """Independent Python mirror for checks; Racket remains label authority."""
    return [_red_sizes(grid)]


# --- Named plausible rivals -------------------------------------------------

def _unique_red_sizes(grid):
    """WRONG: collapse repeated sizes instead of retaining their multiplicity."""
    return [sorted(set(_red_sizes(grid)))]


def _eight_connected_red_sizes(grid):
    """WRONG: diagonal red cells belong to the same component."""
    return [_red_sizes(grid, diagonal=True)]


def _clip_sizes_at_five(grid):
    """WRONG: infer the canonical demonstrations' observed maximum as a cap."""
    return [[min(size, 5) for size in _red_sizes(grid)]]


def _all_nonzero_component_sizes(grid):
    """WRONG: count every colored component rather than selecting red only."""
    return [sorted(len(cells) for _color, cells in _all_nonzero_components(grid))]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "unique_red_sizes": _unique_red_sizes,
    "eight_connected_red_sizes": _eight_connected_red_sizes,
    "clip_sizes_at_five": _clip_sizes_at_five,
    "all_nonzero_component_sizes": _all_nonzero_component_sizes,
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "unique_red_sizes",
        "eight_connected_red_sizes",
        "clip_sizes_at_five",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _distinguishes(grid, rival_name: str) -> bool:
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "repeated_size_counterexample": lambda grid: (
        len(_red_sizes(grid)) != len(set(_red_sizes(grid)))
        and _distinguishes(grid, "unique_red_sizes")
    ),
    "diagonal_contact_counterexample": lambda grid: (
        _red_sizes(grid) != _red_sizes(grid, diagonal=True)
        and _distinguishes(grid, "eight_connected_red_sizes")
    ),
    "over_five_counterexample": lambda grid: (
        bool(_red_sizes(grid))
        and max(_red_sizes(grid)) > 5
        and _distinguishes(grid, "clip_sizes_at_five")
    ),
    "red_selection_counterexample": lambda grid: _distinguishes(
        grid, "all_nonzero_component_sizes"
    ),
}
WITNESS_RIVALS = {
    "repeated_size_counterexample": ["unique_red_sizes"],
    "diagonal_contact_counterexample": ["eight_connected_red_sizes"],
    "over_five_counterexample": ["clip_sizes_at_five"],
    "red_selection_counterexample": ["all_nonzero_component_sizes"],
}


def lesson_identifiable(demos, query):
    """Finite named-rival check, not a claim of unique universal induction."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    pairs = list(demos) + [query]
    for pair in pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["lesson pair must contain input and reference output"]
        errors = self_check(pair["input"])
        if errors:
            return errors
        if rule_mirror(pair["input"]) != pair["output"]:
            return ["authoring mirror disagrees with reference output"]
    return [
        f"rival {name} fits all demonstrations but disagrees on query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]


def mutation_fixtures():
    """Task-semantic must-reject near misses for the validator power probe."""
    no_red = [[0] * 12 for _ in range(10)]
    two_red = [[0] * 12 for _ in range(10)]
    two_red[1][1] = two_red[3][3] = 2
    for column, color in zip((0, 2, 4, 6, 8), (1, 3, 4, 5, 6)):
        two_red[9][column] = color
    diagonal_without_large = [[0] * 12 for _ in range(10)]
    diagonal_without_large[1][1] = diagonal_without_large[2][2] = 2
    diagonal_without_large[1][5] = diagonal_without_large[1][6] = 2
    diagonal_without_large[5][1] = diagonal_without_large[5][2] = 2
    for column, color in zip((0, 2, 4, 6, 8), (1, 3, 4, 5, 6)):
        diagonal_without_large[9][column] = color
    return [
        ("no_red_components", no_red),
        ("only_two_red_components", two_red),
        ("diagonal_profile_without_over_five_witness", diagonal_without_large),
    ]
