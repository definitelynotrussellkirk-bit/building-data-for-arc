"""Generator for 9b5d72b45563 — singleton seeds expand to clipped diagonal Xs.

The selected Racket authority scans input cells in row-major order.  Every
nonzero singleton paints its center and four diagonal neighbours into a fresh
zero canvas; out-of-bounds arms are clipped and later seeds overwrite earlier
colors where two X footprints overlap.

The previous sampler advertised nine mostly unused axes, forced a border seed
into every generated instance, rejected three of four canonical inputs, and
forbade the overlap/overwrite branch that one canonical demonstration contains.
This version exposes one exact ``scene_profile`` axis.  Its deterministic
schedule alternates comprehensive teaching scenes with simpler canonical-scale
controls, so every four-demo lesson and every single-query rotation retains a
counterexample to the strongest canonical-fitting shortcuts.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9b5d72b45563"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "cc30c7127a64"

SUMMARY = (
    "On a fresh same-size color-0 canvas, process every isolated nonzero seed "
    "in row-major order. Paint its center and four one-step diagonal neighbours "
    "with the seed color, clip arms at the border, and let later seeds overwrite "
    "earlier colors where X footprints overlap."
)

INVARIANTS = [
    "background is literal color 0",
    "all nonzero input cells are 8-neighbourhood-isolated singleton seeds",
    "each seed paints its center plus four diagonal neighbours on a fresh canvas",
    "diagonal arms clip at the grid boundary",
    "overlapping X footprints are lawful and resolve by row-major last-writer precedence",
    "the declared scene_profile is exactly recoverable from returned pixels",
]

# Profiles alternate teaching/control.  Every five consecutive generated pairs
# contain at least two teaching scenes; after holding out any one query, every
# four-demo rotation still contains a complete shortcut witness.
SCENE_SPECS = {
    "teaching_8x9": {"size": (8, 9), "kind": "teaching"},
    "canonical_5x5_overlap": {"size": (5, 5), "kind": "control"},
    "teaching_9x11": {"size": (9, 11), "kind": "teaching"},
    "canonical_7x7_disjoint": {"size": (7, 7), "kind": "control"},
    "teaching_10x12": {"size": (10, 12), "kind": "teaching"},
    "canonical_6x8_disjoint": {"size": (6, 8), "kind": "control"},
    "teaching_11x13": {"size": (11, 13), "kind": "teaching"},
    "canonical_7x8_disjoint": {"size": (7, 8), "kind": "control"},
}
SCENE_PROFILES = tuple(SCENE_SPECS)
TEACHING_PROFILES = tuple(
    name for name, spec in SCENE_SPECS.items() if spec["kind"] == "teaching"
)
CONTROL_PROFILES = tuple(
    name for name, spec in SCENE_SPECS.items() if spec["kind"] == "control"
)
SCHEDULE_PROFILES = SCENE_PROFILES
LESSON_SCHEDULE_PERIOD = len(SCENE_PROFILES)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic eight-profile sample-index cycle",
        "valid": (
            "teaching_8x9|canonical_5x5_overlap|teaching_9x11|"
            "canonical_7x7_disjoint|teaching_10x12|canonical_6x8_disjoint|"
            "teaching_11x13|canonical_7x8_disjoint"
        ),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CENTER_AND_DIAGONALS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
_DIAGONALS_ONLY = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_CARDINAL_PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_PALETTE_PROFILES = frozenset(
    {(7, 7, 3), (6, 8, 3), (5, 5, 3), (7, 8, 3)}
)
_SIZE_TO_PROFILE = {spec["size"]: name for name, spec in SCENE_SPECS.items()}
if len(_SIZE_TO_PROFILE) != len(SCENE_SPECS):
    raise AssertionError("scene-profile dimensions must be unique")

_CONTROL_POSITIONS = {
    "canonical_5x5_overlap": ((0, 4), (2, 2)),
    "canonical_7x7_disjoint": ((1, 1), (5, 5)),
    "canonical_6x8_disjoint": ((2, 5), (4, 1)),
    "canonical_7x8_disjoint": ((1, 6), (3, 3)),
}


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (4 <= len(grid) <= 30 and 4 <= width <= 30):
        return ["grid dimensions must each be in 4..30"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _seed_cells(grid) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def _is_boundary(row: int, col: int, height: int, width: int) -> bool:
    return row in (0, height - 1) or col in (0, width - 1)


def _is_corner(row: int, col: int, height: int, width: int) -> bool:
    return row in (0, height - 1) and col in (0, width - 1)


def _is_isolated(positions) -> bool:
    return all(
        max(abs(row_a - row_b), abs(col_a - col_b)) >= 2
        for (row_a, col_a), (row_b, col_b) in combinations(positions, 2)
    )


def _has_same_row_overlap(grid) -> bool:
    seeds = _seed_cells(grid)
    return any(
        row_a == row_b and abs(col_a - col_b) == 2 and color_a != color_b
        for (row_a, col_a, color_a), (row_b, col_b, color_b) in combinations(seeds, 2)
    )


def _has_repeated_color(grid) -> bool:
    colors = [color for _, _, color in _seed_cells(grid)]
    return len(set(colors)) < len(colors)


def _has_boundary_seed(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(_is_boundary(row, col, height, width) for row, col, _ in _seed_cells(grid))


def _is_comprehensive_teaching_scene(grid) -> bool:
    return (
        len(_seed_cells(grid)) >= 3
        and _has_boundary_seed(grid)
        and _has_repeated_color(grid)
        and _has_same_row_overlap(grid)
    )


def _profile_of(grid) -> str | None:
    errors = _grid_errors(grid)
    if errors:
        return None
    return _SIZE_TO_PROFILE.get((len(grid), len(grid[0])))


def _profile_errors(grid, profile: str) -> list[str]:
    spec = SCENE_SPECS[profile]
    expected_size = spec["size"]
    if (len(grid), len(grid[0])) != expected_size:
        return [f"profile {profile!r} requires size {expected_size}"]

    seeds = _seed_cells(grid)
    height, width = expected_size
    if spec["kind"] == "teaching":
        counts = sorted(Counter(color for _, _, color in seeds).values())
        errors = []
        if len(seeds) != 4:
            errors.append("teaching profile requires exactly four seeds")
        if counts != [1, 1, 2]:
            errors.append("teaching profile requires three colors with one repeated")
        if sum(_is_boundary(r, c, height, width) for r, c, _ in seeds) != 1:
            errors.append("teaching profile requires exactly one boundary seed")
        if sum(_is_corner(r, c, height, width) for r, c, _ in seeds) != 0:
            errors.append("teaching profile boundary seed must not be a corner")
        if not _has_same_row_overlap(grid):
            errors.append("teaching profile requires a different-color same-row overlap pair")
        if not _is_comprehensive_teaching_scene(grid):
            errors.append("teaching profile lost a required shortcut witness")
        return errors

    errors = []
    if len(seeds) != 2 or len({color for _, _, color in seeds}) != 2:
        errors.append("control profile requires two differently colored seeds")
    if profile == "canonical_5x5_overlap":
        if sum(_is_corner(r, c, height, width) for r, c, _ in seeds) != 1:
            errors.append("5x5 control requires one corner seed")
        positions = [(r, c) for r, c, _ in seeds]
        if max(abs(positions[0][0] - positions[1][0]), abs(positions[0][1] - positions[1][1])) != 2:
            errors.append("5x5 control requires overlapping X footprints")
    elif any(_is_boundary(r, c, height, width) for r, c, _ in seeds):
        errors.append("disjoint canonical-scale controls require interior seeds")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the rule grammar; overlap is lawful, adjacency is not."""
    errors = _grid_errors(grid)
    if errors:
        return errors

    seeds = _seed_cells(grid)
    if len(seeds) < 2:
        return ["at least two nonzero singleton seeds are required"]
    if len(seeds) > 12:
        errors.append("at most twelve singleton seeds are supported")
    positions = [(row, col) for row, col, _ in seeds]
    if not _is_isolated(positions):
        errors.append("all nonzero cells must be 8-neighbourhood-isolated singleton seeds")

    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is not None:
        if requested not in SCENE_SPECS:
            errors.append(f"unknown scene profile {requested!r}")
        elif _profile_of(grid) != requested:
            errors.append(f"scene profile drifted from {requested!r} to {_profile_of(grid)!r}")
        else:
            errors.extend(_profile_errors(grid, requested))
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every valid sampler input belongs to the selected singleton-X grammar."""
    return list(self_check(grid))


def canonical_profile_signature(grid) -> str | None:
    if self_check(grid):
        return None
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PALETTE_PROFILES:
        return None
    return f"{profile[0]}x{profile[1]}:palette{profile[2]}"


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    if profile is None:
        raise ValueError("grid dimensions do not identify a declared scene profile")
    profile_errors = _profile_errors(grid, profile)
    if profile_errors:
        raise ValueError("; ".join(profile_errors))
    return {"scene_profile": profile}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _reflect_positions(positions, height, width, *, vertical, horizontal):
    result = []
    for row, col in positions:
        if vertical:
            row = height - 1 - row
        if horizontal:
            col = width - 1 - col
        result.append((row, col))
    return result


def _teaching_positions(height, width, rng):
    pair_row = height // 2
    pair_left = max(2, width // 2 - 2)
    base = [(0, 1), (pair_row, pair_left), (pair_row, pair_left + 2), (height - 2, width - 2)]
    variant = rng.randrange(4)
    return _reflect_positions(
        base,
        height,
        width,
        vertical=bool(variant & 1),
        horizontal=bool(variant & 2),
    )


def _control_positions(profile, height, width, rng):
    base = _CONTROL_POSITIONS[profile]
    variant = rng.randrange(4)
    return _reflect_positions(
        base,
        height,
        width,
        vertical=bool(variant & 1),
        horizontal=bool(variant & 2),
    )


def _construct_profile(profile, rng):
    spec = SCENE_SPECS[profile]
    height, width = spec["size"]
    grid = full_grid(height, width, 0)
    if spec["kind"] == "teaching":
        positions = _teaching_positions(height, width, rng)
        repeated, left_color, right_color = rng.sample(range(1, 10), 3)
        colors = (repeated, left_color, right_color, repeated)
    else:
        positions = _control_positions(profile, height, width, rng)
        colors = tuple(rng.sample(range(1, 10), 2))
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color
    return grid


def _relabel_for_difficulty(grid, difficulty):
    """Make built-in difficulty bands observably distinct without changing grammar."""
    shift = {None: 0, "easy": 0, "medium": 3, "hard": 6}[difficulty]
    if shift == 0:
        return [row[:] for row in grid]
    return [
        [0 if value == 0 else ((value - 1 + shift) % 9) + 1 for value in row]
        for row in grid
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic input grid; the Racket rule remains authority."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if overrides.get("scene_profile") is not None else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    grid = _construct_profile(profile, ctx.draw_rng(f"layout:{profile}"))
    grid = _relabel_for_difficulty(grid, difficulty)
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": {"scene_profile": profile}})
    if errors:
        raise RuntimeError(f"constructed invalid scene for {profile}: {errors}")
    return [row[:] for row in grid]


def _paint(grid, offsets, seeds) -> list[list[int]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for row, col, color in seeds:
        for delta_row, delta_col in offsets:
            next_row, next_col = row + delta_row, col + delta_col
            if 0 <= next_row < height and 0 <= next_col < width:
                output[next_row][next_col] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected row-major Racket authority."""
    return _paint(grid, _CENTER_AND_DIAGONALS, _seed_cells(grid))


def _first_two_seeds_only(grid):
    return _paint(grid, _CENTER_AND_DIAGONALS, _seed_cells(grid)[:2])


def _right_to_left_within_rows(grid):
    seeds = sorted(_seed_cells(grid), key=lambda item: (item[0], -item[1]))
    return _paint(grid, _CENTER_AND_DIAGONALS, seeds)


def _first_seed_per_color(grid):
    seen = set()
    seeds = []
    for seed in _seed_cells(grid):
        if seed[2] not in seen:
            seeds.append(seed)
            seen.add(seed[2])
    return _paint(grid, _CENTER_AND_DIAGONALS, seeds)


def _ignore_boundary_seeds(grid):
    height, width = len(grid), len(grid[0])
    seeds = [
        seed for seed in _seed_cells(grid)
        if not _is_boundary(seed[0], seed[1], height, width)
    ]
    return _paint(grid, _CENTER_AND_DIAGONALS, seeds)


def _omit_seed_center(grid):
    return _paint(grid, _DIAGONALS_ONLY, _seed_cells(grid))


def _cardinal_plus(grid):
    return _paint(grid, _CARDINAL_PLUS, _seed_cells(grid))


def _fixed_color_eight(grid):
    seeds = [(row, col, 8) for row, col, _ in _seed_cells(grid)]
    return _paint(grid, _CENTER_AND_DIAGONALS, seeds)


def _first_writer_wins(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for row, col, color in _seed_cells(grid):
        for delta_row, delta_col in _CENTER_AND_DIAGONALS:
            next_row, next_col = row + delta_row, col + delta_col
            if 0 <= next_row < height and 0 <= next_col < width and output[next_row][next_col] == 0:
                output[next_row][next_col] = color
    return output


CANONICAL_SHORTCUTS = {
    "first_two_seeds_only": _first_two_seeds_only,
    "right_to_left_within_rows": _right_to_left_within_rows,
    "first_seed_per_color": _first_seed_per_color,
}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS,
    "ignore_boundary_seeds": _ignore_boundary_seeds,
    "omit_seed_center": _omit_seed_center,
    "cardinal_plus_instead_of_diagonal_x": _cardinal_plus,
    "fixed_color_eight": _fixed_color_eight,
    "first_writer_wins_overlap": _first_writer_wins,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)

SEMANTIC_WITNESSES = {
    "third_seed_matters": lambda grid: len(_seed_cells(grid)) >= 3,
    "same_row_overlap_precedence": _has_same_row_overlap,
    "repeated_color_seed": _has_repeated_color,
    "boundary_clipping": _has_boundary_seed,
    "complete_teaching_scene": _is_comprehensive_teaching_scene,
}
WITNESS_RIVALS = {
    "third_seed_matters": ["first_two_seeds_only"],
    "same_row_overlap_precedence": [
        "right_to_left_within_rows",
        "first_writer_wins_overlap",
    ],
    "repeated_color_seed": ["first_seed_per_color"],
    "boundary_clipping": ["ignore_boundary_seeds"],
    "complete_teaching_scene": [
        "omit_seed_center",
        "cardinal_plus_instead_of_diagonal_x",
        "fixed_color_eight",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require at least one complete witness and refute every named rival."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the singleton-X grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the row-major diagonal-X rule")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the singleton-X grammar: {query_errors[0]}")
        return reasons

    if not any(_is_comprehensive_teaching_scene(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations lack a complete multi-seed/clipping/color/overlap witness")

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons
