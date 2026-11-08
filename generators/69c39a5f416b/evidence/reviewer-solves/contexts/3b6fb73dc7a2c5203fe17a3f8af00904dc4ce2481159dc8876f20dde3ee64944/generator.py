"""Generator for H61 — apply a two-row color key, then remove the key.

Each nonzero cell in row 0 is a source color and the cell directly beneath it
is its destination color.  The body begins at row 2.  The output drops the two
key rows and replaces every body source exactly once by its paired destination.

The six-slot lesson schedule interleaves three linked canonical profiles with
three shortcut-rebutting profiles.  Every three-example window therefore shows
both a key column after column two and an overlapping source/destination map,
which refutes the strongest canonical shortcut (read only the first three
columns) and iterative/cascading recoloring.
"""
from __future__ import annotations

from collections.abc import Callable
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "69c39a5f416b"
TASK_ID = "69c39a5f416b"
VERSION = "3.0.0"
RULE_HASH = "d3105e4a99fb"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Rows 0 and 1 are an aligned old-color→new-color key. Drop those two "
    "rows and recolor the sparse body once by the column-wise mapping. The "
    "curriculum interleaves all three canonical size/palette profiles with "
    "scattered late key columns and overlapping mappings so fixed-first-three "
    "and cascading shortcuts are explicitly falsified."
)

INVARIANTS = [
    "background is color 0",
    "rows 0 and 1 contain 2..4 aligned nonzero source/destination pairs",
    "sources and destinations are each unique and every pair is non-identity",
    "every source color appears in the sparse body below row 1",
    "the body contains source colors only",
    "the output removes exactly two rows and applies the mapping exactly once",
]

LEGEND_LAYOUTS = ("left", "shifted", "scattered")
MAPPING_KINDS = ("disjoint", "chain", "swap")
SCHEDULE_PROFILES = tuple(range(6))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-slot canonical/difficulty schedule",
        "valid": "7..11",
    },
    "grid_w": {
        "type": "int",
        "default": "six-slot canonical/difficulty schedule",
        "valid": "7..12",
    },
    "n_pairs": {
        "type": "int",
        "default": "six-slot schedule",
        "valid": "2..4",
    },
    "legend_layout": {
        "type": "enum",
        "default": "left on canonical profiles; scattered on rebuttal profiles",
        "valid": LEGEND_LAYOUTS,
    },
    "mapping_kind": {
        "type": "enum",
        "default": "scheduled disjoint/chain/swap",
        "valid": MAPPING_KINDS,
    },
}

# Profiles 0, 2 and 4 reproduce the three canonical linked signatures
# (height, width, full palette size): (8,8,7), (8,9,5), (9,9,6).
_CANONICAL_PROFILE_DEFAULTS = {
    0: (8, 8, 3, "left", "disjoint"),
    2: (8, 9, 3, "left", "swap"),
    4: (9, 9, 3, "left", "chain"),
}

_GENERAL_PROFILE_DEFAULTS = {
    "easy": {
        1: (8, 9, 4, "scattered", "swap"),
        3: (7, 8, 2, "scattered", "chain"),
        5: (8, 9, 4, "scattered", "disjoint"),
    },
    "medium": {
        1: (9, 10, 4, "scattered", "swap"),
        3: (9, 10, 2, "scattered", "chain"),
        5: (10, 11, 4, "scattered", "disjoint"),
    },
    "hard": {
        1: (11, 12, 4, "scattered", "swap"),
        3: (10, 12, 2, "scattered", "chain"),
        5: (11, 12, 4, "scattered", "disjoint"),
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Return the deterministic six-way lesson profile."""
    del seed, difficulty
    return int(sample_index) % 6


def _scheduled_defaults(profile: int, difficulty: str | None) -> tuple[int, int, int, str, str]:
    if profile in _CANONICAL_PROFILE_DEFAULTS:
        return _CANONICAL_PROFILE_DEFAULTS[profile]
    band = difficulty if difficulty in _GENERAL_PROFILE_DEFAULTS else "medium"
    return _GENERAL_PROFILE_DEFAULTS[band][profile]


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_exact_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _legend_columns(rng, width: int, n_pairs: int, layout: str) -> list[int]:
    left = tuple(range(n_pairs))
    shifted = tuple(range(1, n_pairs + 1))
    if layout == "left":
        return list(left)
    if layout == "shifted":
        return list(shifted)

    candidates = [
        combo
        for combo in combinations(range(width), n_pairs)
        if combo != left
        and combo != shifted
        and max(combo) >= 3
    ]
    if not candidates:
        raise ValueError(
            f"no scattered {n_pairs}-column legend fits width {width} while exposing a column after 2"
        )
    return list(rng.choice(candidates))


def _draw_palette(ctx, n_pairs: int, mapping_kind: str) -> tuple[list[int], list[int]]:
    if mapping_kind == "disjoint":
        colors = list(ctx.draw_distinct_colors("palette", n=2 * n_pairs, exclude={0}))
        return colors[:n_pairs], colors[n_pairs:]

    if mapping_kind == "chain":
        colors = list(ctx.draw_distinct_colors("palette", n=2 * n_pairs - 1, exclude={0}))
        sources = colors[:n_pairs]
        destinations = [sources[1], *colors[n_pairs:]]
        return sources, destinations

    colors = list(ctx.draw_distinct_colors("palette", n=2 * n_pairs - 2, exclude={0}))
    sources = colors[:n_pairs]
    destinations = [sources[1], sources[0], *colors[n_pairs:]]
    return sources, destinations


def _build_motif(rng, size: int) -> list[tuple[int, int]]:
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(cells)
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        nxt = row + dr, col + dc
        if nxt not in seen:
            seen.add(nxt)
            cells.append(nxt)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return [(row - min_row, col - min_col) for row, col in cells]


def _place_connected_body(grid: list[list[int]], sources: list[int], rng, difficulty: str | None) -> bool:
    height, width = len(grid), len(grid[0])
    max_size = 2 if difficulty == "easy" else (4 if difficulty == "hard" else 3)
    occupied: set[tuple[int, int]] = set()
    for source in sources:
        shape = _build_motif(rng, rng.randint(2, max_size))
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        placements = [
            (row0, col0)
            for row0 in range(2, height - shape_h + 1)
            for col0 in range(0, width - shape_w + 1)
            if all((row0 + row, col0 + col) not in occupied for row, col in shape)
        ]
        if not placements:
            return False
        row0, col0 = rng.choice(placements)
        for row, col in shape:
            cell = row0 + row, col0 + col
            occupied.add(cell)
            grid[cell[0]][cell[1]] = source
    return len({row for row, _ in occupied}) >= 2


def _place_scattered_body(grid: list[list[int]], sources: list[int], rng, difficulty: str | None) -> None:
    height, width = len(grid), len(grid[0])
    uses = 2 if difficulty == "easy" else (4 if difficulty == "hard" else 3)
    stream = [source for source in sources for _ in range(uses)]
    rng.shuffle(stream)

    positions = [(row, col) for row in range(2, height) for col in range(width)]
    rng.shuffle(positions)
    # Force two occupied rows even for unlucky shuffles.
    if len(stream) >= 2 and positions[0][0] == positions[1][0]:
        replacement = next(index for index in range(2, len(positions)) if positions[index][0] != positions[0][0])
        positions[1], positions[replacement] = positions[replacement], positions[1]
    for source, (row, col) in zip(stream, positions):
        grid[row][col] = source


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the selected Racket rule is authority."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_pairs, default_layout, default_mapping = _scheduled_defaults(
        profile, difficulty
    )

    height = _draw_exact_int(ctx, "grid_h", 7, 11, default_h)
    width = _draw_exact_int(ctx, "grid_w", 7, 12, default_w)
    n_pairs = _draw_exact_int(ctx, "n_pairs", 2, 4, default_pairs)
    layout = _draw_exact_choice(ctx, "legend_layout", LEGEND_LAYOUTS, default_layout)
    mapping_kind = _draw_exact_choice(ctx, "mapping_kind", MAPPING_KINDS, default_mapping)

    sources, destinations = _draw_palette(ctx, n_pairs, mapping_kind)
    grid = full_grid(height, width, 0)
    rng = ctx.draw_rng("layout")
    columns = _legend_columns(rng, width, n_pairs, layout)
    for column, source, destination in zip(columns, sources, destinations):
        grid[0][column] = source
        grid[1][column] = destination

    # Canonical-linked profiles use connected motifs; rebuttal profiles use
    # dispersed repeats so neither geometry nor one-object-per-color is needed.
    if profile % 2 == 0:
        if not _place_connected_body(grid, sources, rng, difficulty):
            for row in range(2, height):
                grid[row] = [0] * width
            _place_scattered_body(grid, sources, rng, difficulty)
    else:
        _place_scattered_body(grid, sources, rng, difficulty)
    return grid


def _legend(grid: list[list[int]]) -> tuple[list[int], list[int], list[int]]:
    width = len(grid[0])
    columns = [column for column in range(width) if grid[0][column] != 0 or grid[1][column] != 0]
    sources = [grid[0][column] for column in columns]
    destinations = [grid[1][column] for column in columns]
    return columns, sources, destinations


def _mapping(grid: list[list[int]], *, first_columns: int | None = None) -> dict[int, int]:
    width = len(grid[0])
    stop = width if first_columns is None else min(width, first_columns)
    mapping: dict[int, int] = {}
    for column in range(stop):
        source = grid[0][column]
        if source != 0 and source not in mapping:
            mapping[source] = grid[1][column]
    return mapping


def _solve_grid(grid: list[list[int]]) -> list[list[int]]:
    mapping = _mapping(grid)
    return [[mapping.get(value, value) for value in row] for row in grid[2:]]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror used for tests and adversarial probes."""
    return _solve_grid(grid)


def _mapping_kind(sources: list[int], destinations: list[int]) -> str:
    mapping = dict(zip(sources, destinations))
    if any(mapping.get(destination) == source for source, destination in mapping.items()):
        return "swap"
    if set(sources) & set(destinations):
        return "chain"
    return "disjoint"


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact AXES value from a generated grid."""
    columns, sources, destinations = _legend(grid)
    left = list(range(len(columns)))
    shifted = list(range(1, len(columns) + 1))
    if columns == left:
        layout = "left"
    elif columns == shifted:
        layout = "shifted"
    else:
        layout = "scattered"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(columns),
        "legend_layout": layout,
        "mapping_kind": _mapping_kind(sources, destinations),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-specific two-row permutation grammar."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be rectangular"]

    errors: list[str] = []
    if not (7 <= height <= 11 and 7 <= width <= 12):
        errors.append(f"expected dimensions 7..11 by 7..12, got {height}x{width}")
    for row_index, row in enumerate(grid):
        for column, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({row_index},{column}) has invalid ARC color {value!r}")
    if errors:
        return errors

    columns, sources, destinations = _legend(grid)
    if not (2 <= len(columns) <= 4):
        errors.append(f"expected 2..4 key columns, got {len(columns)}")
    if any(source == 0 or destination == 0 for source, destination in zip(sources, destinations)):
        errors.append("every key column must contain a nonzero source and destination")
    if len(set(sources)) != len(sources):
        errors.append("key source colors must be unique")
    if len(set(destinations)) != len(destinations):
        errors.append("key destination colors must be unique")
    if any(source == destination for source, destination in zip(sources, destinations)):
        errors.append("identity key pairs hide whether recoloring fired")

    body_values = [value for row in grid[2:] for value in row if value != 0]
    if not body_values:
        errors.append("body has no cells to recolor")
    foreign = sorted(set(body_values) - set(sources))
    if foreign:
        errors.append(f"body contains colors absent from the source key: {foreign}")
    missing = [source for source in sources if source not in body_values]
    if missing:
        errors.append(f"body fails to exercise source colors: {missing}")
    if len(body_values) > 20:
        errors.append(f"body is too dense for the sparse canonical family: {len(body_values)} cells")
    occupied_rows = {
        row
        for row in range(2, height)
        if any(grid[row][column] != 0 for column in range(width))
    }
    if len(occupied_rows) < 2:
        errors.append("body must occupy at least two rows")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _drop_only_rival(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid[2:]]


def _keep_header_rival(grid: list[list[int]]) -> list[list[int]]:
    mapping = _mapping(grid)
    return [[mapping.get(value, value) for value in row] for row in grid]


def _first_three_columns_rival(grid: list[list[int]]) -> list[list[int]]:
    mapping = _mapping(grid, first_columns=3)
    return [[mapping.get(value, value) for value in row] for row in grid[2:]]


def _cascade_rival(grid: list[list[int]]) -> list[list[int]]:
    mapping = _mapping(grid)

    def cascade(value: int) -> int:
        seen: set[int] = set()
        while value in mapping and value not in seen:
            seen.add(value)
            value = mapping[value]
        return value

    return [[cascade(value) for value in row] for row in grid[2:]]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "drop_key_without_recoloring": _drop_only_rival,
    "recolor_but_keep_key_rows": _keep_header_rival,
    "first_three_columns_only": _first_three_columns_rival,
    "cascade_mapping_until_stable": _cascade_rival,
}

CANONICAL_SHORTCUTS = {
    "first_three_columns_only": _first_three_columns_rival,
}

LESSON_COMPETITORS = SEMANTIC_RIVALS


def _legend_after_column_two(grid: list[list[int]]) -> bool:
    columns, _, _ = _legend(grid)
    return bool(columns) and max(columns) >= 3


def _overlapping_mapping(grid: list[list[int]]) -> bool:
    _, sources, destinations = _legend(grid)
    return bool(set(sources) & set(destinations))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "legend_after_column_two": _legend_after_column_two,
    "overlapping_mapping": _overlapping_mapping,
    "nonidentity_body_recolor": lambda grid: _drop_only_rival(grid) != _solve_grid(grid),
    "key_rows_are_removed": lambda grid: len(grid) >= 3,
}

WITNESS_RIVALS = {
    "legend_after_column_two": ["first_three_columns_only"],
    "overlapping_mapping": ["cascade_mapping_until_stable"],
    "nonidentity_body_recolor": ["drop_key_without_recoloring"],
    "key_rows_are_removed": ["recolor_but_keep_key_rows"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each query-changing named rival to be contradicted by a demo."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        if pair["output"] != _solve_grid(pair["input"]):
            reasons.append(f"pair {index} output disagrees with one-step key recoloring")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
