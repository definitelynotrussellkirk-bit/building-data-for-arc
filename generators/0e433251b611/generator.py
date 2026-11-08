"""Generator for ARC task 0e433251b611 — flood wall-bounded chambers.

Color 9 forms complete horizontal and vertical walls.  Every chamber contains
zero or one colored seed.  The authoritative rule fills each seeded chamber
with its own seed color and leaves unseeded chambers unchanged.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0e433251b611"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "d0a24e887acb"
SUMMARY = (
    "Treat color 9 as hard walls. Flood every zero cell in a chamber that has "
    "one colored seed with that seed's color; preserve the walls and any "
    "unseeded chamber."
)
INVARIANTS = [
    "the outer border and every internal divider are complete color-9 lines",
    "the wall lines partition the canvas into three through six rectangular chambers",
    "every chamber contains zero or one seed color from 1 through 8",
    "at least two chambers are seeded and every seeded chamber contains zeros to flood",
    "repeated seed colors in separate chambers remain independent",
]

LAYOUT_PROFILES = ("row_3", "grid_2x2", "grid_2x3", "column_3")
SEED_PATTERNS = ("all_seeded", "last_unseeded", "checker_unseeded")
COLOR_RELATIONS = ("all_distinct", "one_repeat")
SIZE_RELATIONS = ("uniform", "varied")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

_LAYOUT_SCHEDULE = ("row_3", "grid_2x2", "grid_2x3", "column_3")
_SEED_SCHEDULE = ("all_seeded", "all_seeded", "checker_unseeded", "last_unseeded")
_COLOR_SCHEDULE = ("all_distinct", "all_distinct", "one_repeat", "all_distinct")
_SIZE_SCHEDULE = ("varied", "uniform", "varied", "uniform")

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "cyclic across four chamber layouts",
        "valid": "|".join(LAYOUT_PROFILES),
    },
    "seed_pattern": {
        "type": "str",
        "default": "cyclic all/last-blank/checker-blank",
        "valid": "|".join(SEED_PATTERNS),
    },
    "color_relation": {
        "type": "str",
        "default": "alternates distinct seeds and one repeated seed color",
        "valid": "|".join(COLOR_RELATIONS),
    },
    "size_relation": {
        "type": "str",
        "default": "alternates uniform and unequal chamber dimensions",
        "valid": "|".join(SIZE_RELATIONS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_LAYOUT_DIMS = {
    "row_3": (1, 3),
    "grid_2x2": (2, 2),
    "grid_2x3": (2, 3),
    "column_3": (3, 1),
}
_DIMS_TO_LAYOUT = {dims: name for name, dims in _LAYOUT_DIMS.items()}

# Canonical-sized templates are deliberately frequent.  They anchor the
# generated distribution to official dimensions while the random branch below
# supplies many unequal chamber widths/heights.
_CANONICAL_GEOMETRY = {
    ("row_3", "uniform"): ([8], [3, 3, 3]),
    ("row_3", "varied"): ([8], [3, 3, 2]),
    ("grid_2x2", "uniform"): ([3, 3], [4, 4]),
    ("grid_2x2", "varied"): ([4, 2], [5, 5]),
    ("grid_2x3", "uniform"): ([3, 3], [3, 3, 3]),
    ("grid_2x3", "varied"): ([3, 4], [3, 4, 3]),
    ("column_3", "uniform"): ([3, 3, 3], [8]),
    ("column_3", "varied"): ([3, 3, 2], [8]),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str, overrides: dict[str, Any]) -> str:
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, list(options))
    return ctx.draw_choice(label, [scheduled])


def _random_sizes(count: int, lo: int, hi: int, rng, relation: str) -> list[int]:
    if count == 1:
        return [rng.randint(lo, hi)]
    if relation == "uniform":
        value = rng.randint(lo, hi)
        return [value] * count
    values = [rng.randint(lo, hi) for _ in range(count)]
    if len(set(values)) == 1:
        values[-1] = values[-1] + 1 if values[-1] < hi else values[-1] - 1
    return values


def _geometry(layout: str, relation: str, band: str, sample_index: int, rng) -> tuple[list[int], list[int]]:
    # One third of ordinary draws use an exact canonical-scale template.  The
    # other draws vary within difficulty bands while preserving the requested
    # uniform/varied relation.
    if sample_index % 4 in (0, 1):
        rows, cols = _CANONICAL_GEOMETRY[(layout, relation)]
        return list(rows), list(cols)
    lo, hi = {"easy": (2, 3), "medium": (2, 5), "hard": (3, 6)}[band]
    n_rows, n_cols = _LAYOUT_DIMS[layout]
    row_lo, row_hi = (max(lo, 5), max(hi, 8)) if n_rows == 1 else (lo, hi)
    col_lo, col_hi = (max(lo, 5), max(hi, 8)) if n_cols == 1 else (lo, hi)
    rows = _random_sizes(n_rows, row_lo, row_hi, rng, relation)
    cols = _random_sizes(n_cols, col_lo, col_hi, rng, relation)
    if relation == "varied" and len(set(rows)) == 1 and len(set(cols)) == 1:
        target = cols if len(cols) > 1 else rows
        target[-1] = target[-1] + 1 if target[-1] < hi else target[-1] - 1
    return rows, cols


def _wall_positions(sizes: list[int]) -> list[int]:
    walls = [0]
    cursor = 0
    for size in sizes:
        cursor += size + 1
        walls.append(cursor)
    return walls


def _chambers_from_walls(row_walls: list[int], col_walls: list[int]) -> list[tuple[int, int, int, int]]:
    return [
        (row_walls[ri] + 1, row_walls[ri + 1] - 1, col_walls[ci] + 1, col_walls[ci + 1] - 1)
        for ri in range(len(row_walls) - 1)
        for ci in range(len(col_walls) - 1)
    ]


def _seeded_indices(n_rows: int, n_cols: int, pattern: str) -> list[int]:
    count = n_rows * n_cols
    if pattern == "all_seeded":
        return list(range(count))
    if pattern == "last_unseeded":
        return list(range(count - 1))
    if pattern == "checker_unseeded":
        return [ri * n_cols + ci for ri in range(n_rows) for ci in range(n_cols) if (ri + ci) % 2 == 0]
    raise ValueError(f"unknown seed pattern: {pattern!r}")


def _seed_colors(count: int, relation: str, rng) -> list[int]:
    palette = list(range(1, 9))
    rng.shuffle(palette)
    if relation == "all_distinct":
        return palette[:count]
    if count < 2:
        raise ValueError("one_repeat requires at least two seeded chambers")
    colors = [palette[0], palette[0]] + palette[1 : count - 1]
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    layout = _scheduled_choice(
        ctx, "layout_profile", LAYOUT_PROFILES,
        _LAYOUT_SCHEDULE[sample_index % len(_LAYOUT_SCHEDULE)], overrides,
    )
    seed_pattern = _scheduled_choice(
        ctx, "seed_pattern", SEED_PATTERNS,
        _SEED_SCHEDULE[sample_index % len(_SEED_SCHEDULE)], overrides,
    )
    color_relation = _scheduled_choice(
        ctx, "color_relation", COLOR_RELATIONS,
        _COLOR_SCHEDULE[sample_index % len(_COLOR_SCHEDULE)], overrides,
    )
    size_relation = _scheduled_choice(
        ctx, "size_relation", SIZE_RELATIONS,
        _SIZE_SCHEDULE[sample_index % len(_SIZE_SCHEDULE)], overrides,
    )

    geometry_rng = ctx.draw_rng("geometry")
    seed_rng = ctx.draw_rng("seed_placement")
    color_rng = ctx.draw_rng("seed_colors")
    n_rows, n_cols = _LAYOUT_DIMS[layout]
    row_sizes, col_sizes = _geometry(layout, size_relation, band, sample_index, geometry_rng)
    row_walls, col_walls = _wall_positions(row_sizes), _wall_positions(col_sizes)
    grid = full_grid(row_walls[-1] + 1, col_walls[-1] + 1, 9)
    chambers = _chambers_from_walls(row_walls, col_walls)
    for r0, r1, c0, c1 in chambers:
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                grid[row][col] = 0

    seeded = _seeded_indices(n_rows, n_cols, seed_pattern)
    colors = _seed_colors(len(seeded), color_relation, color_rng)
    for index, color in zip(seeded, colors):
        r0, r1, c0, c1 = chambers[index]
        row = seed_rng.randint(r0, r1)
        col = seed_rng.randint(c0, c1)
        grid[row][col] = color
    return grid


def _valid_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be nonempty"]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return height, width, ["grid must be rectangular"]
    if not (7 <= height <= 30 and 7 <= width <= 30):
        errors.append(f"grid dimensions must each be 7..30, got {height}x{width}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("cells must be literal integers from zero through nine")
    return height, width, errors


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    height, width, errors = _valid_grid(grid)
    info: dict[str, Any] = {}
    if errors:
        return info, errors

    row_walls = [row for row in range(height) if all(grid[row][col] == 9 for col in range(width))]
    col_walls = [col for col in range(width) if all(grid[row][col] == 9 for row in range(height))]
    if not row_walls or row_walls[0] != 0 or row_walls[-1] != height - 1:
        errors.append("top and bottom borders must be complete color-9 walls")
    if not col_walls or col_walls[0] != 0 or col_walls[-1] != width - 1:
        errors.append("left and right borders must be complete color-9 walls")
    if errors:
        return info, errors

    wall_rows, wall_cols = set(row_walls), set(col_walls)
    stray_walls = [
        (row, col) for row in range(height) for col in range(width)
        if grid[row][col] == 9 and row not in wall_rows and col not in wall_cols
    ]
    if stray_walls:
        errors.append("every color-9 cell must belong to a complete divider row or column")

    row_sizes = [row_walls[i + 1] - row_walls[i] - 1 for i in range(len(row_walls) - 1)]
    col_sizes = [col_walls[i + 1] - col_walls[i] - 1 for i in range(len(col_walls) - 1)]
    if any(size < 2 for size in row_sizes + col_sizes):
        errors.append("every chamber dimension must be at least two cells")
    n_rows, n_cols = len(row_sizes), len(col_sizes)
    layout = _DIMS_TO_LAYOUT.get((n_rows, n_cols))
    if layout is None:
        errors.append(f"unsupported chamber layout {n_rows}x{n_cols}")

    chambers = _chambers_from_walls(row_walls, col_walls)
    seeds: list[tuple[int, int, int, int]] = []
    seeded_indices: list[int] = []
    chamber_seeds: list[list[tuple[int, int, int]]] = []
    for index, (r0, r1, c0, c1) in enumerate(chambers):
        found = [
            (row, col, grid[row][col])
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if grid[row][col] not in (0, 9)
        ]
        chamber_seeds.append(found)
        if len(found) > 1:
            errors.append(f"chamber {index} contains {len(found)} seeds; at most one is allowed")
        elif found:
            row, col, color = found[0]
            seeds.append((index, row, col, color))
            seeded_indices.append(index)
    if len(seeds) < 2:
        errors.append(f"at least two chambers must be seeded, got {len(seeds)}")

    count = n_rows * n_cols
    if len(seeded_indices) == count:
        seed_pattern = "all_seeded"
    elif seeded_indices == list(range(count - 1)):
        seed_pattern = "last_unseeded"
    elif seeded_indices == _seeded_indices(n_rows, n_cols, "checker_unseeded"):
        seed_pattern = "checker_unseeded"
    else:
        seed_pattern = None
        errors.append("seeded chambers must match all_seeded, last_unseeded, or checker_unseeded")

    colors = [seed[3] for seed in seeds]
    counts = Counter(colors)
    repeats = sum(amount - 1 for amount in counts.values())
    if repeats == 0:
        color_relation = "all_distinct"
    elif repeats == 1 and max(counts.values()) == 2:
        color_relation = "one_repeat"
    else:
        color_relation = None
        errors.append("seed colors must be all distinct or contain exactly one repeated pair")

    size_relation = "uniform" if len(set(row_sizes)) == 1 and len(set(col_sizes)) == 1 else "varied"
    info.update({
        "height": height,
        "width": width,
        "row_walls": tuple(row_walls),
        "col_walls": tuple(col_walls),
        "row_sizes": tuple(row_sizes),
        "col_sizes": tuple(col_sizes),
        "chambers": tuple(chambers),
        "chamber_seeds": tuple(tuple(items) for items in chamber_seeds),
        "seeds": tuple(seeds),
        "seeded_indices": tuple(seeded_indices),
        "layout_profile": layout,
        "seed_pattern": seed_pattern,
        "color_relation": color_relation,
        "size_relation": size_relation,
    })
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    return _analyse(grid)[1]


def rule_mirror(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for chamber, seeds in zip(info["chambers"], info["chamber_seeds"]):
        if not seeds:
            continue
        color = seeds[0][2]
        r0, r1, c0, c1 = chamber
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = color
    return out


def _identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _fill_unseeded_with_modal(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    modal = Counter(seed[3] for seed in info["seeds"]).most_common(1)[0][0]
    for chamber, seeds in zip(info["chambers"], info["chamber_seeds"]):
        color = seeds[0][2] if seeds else modal
        r0, r1, c0, c1 = chamber
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = color
    return out


def _first_seed_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    index, _, _, color = info["seeds"][0]
    r0, r1, c0, c1 = info["chambers"][index]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            out[row][col] = color
    return out


def _first_chamber_per_color(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    seen: set[int] = set()
    for index, _, _, color in info["seeds"]:
        if color in seen:
            continue
        seen.add(color)
        r0, r1, c0, c1 = info["chambers"][index]
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = color
    return out


def _largest_chambers_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    areas = [(r1 - r0 + 1) * (c1 - c0 + 1) for r0, r1, c0, c1 in info["chambers"]]
    largest = max(areas)
    out = [list(row) for row in grid]
    for area, chamber, seeds in zip(areas, info["chambers"], info["chamber_seeds"]):
        if area != largest or not seeds:
            continue
        color = seeds[0][2]
        r0, r1, c0, c1 = chamber
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                out[row][col] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity_no_flood": _identity,
    "fill_unseeded_with_modal": _fill_unseeded_with_modal,
    "first_seed_only": _first_seed_only,
    "first_chamber_per_color": _first_chamber_per_color,
    "largest_chambers_only": _largest_chambers_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fill_unseeded_with_modal": _fill_unseeded_with_modal,
    "first_chamber_per_color": _first_chamber_per_color,
}


def _facts(grid: Any) -> tuple[dict[str, Any], bool]:
    info, errors = _analyse(grid)
    return info, not errors


def _witness_layout(name: str):
    return lambda grid: (_facts(grid)[1] and _facts(grid)[0]["layout_profile"] == name)


def _witness_unseeded(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and info["seed_pattern"] != "all_seeded"


def _witness_repeat(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and info["color_relation"] == "one_repeat"


def _witness_multiple_seeds(grid: Any) -> bool:
    info, ok = _facts(grid)
    return ok and len(info["seeds"]) >= 2


def _witness_unequal_seeded_nonmax(grid: Any) -> bool:
    info, ok = _facts(grid)
    if not ok or info["size_relation"] != "varied":
        return False
    areas = [(r1 - r0 + 1) * (c1 - c0 + 1) for r0, r1, c0, c1 in info["chambers"]]
    largest = max(areas)
    return any(areas[index] != largest for index in info["seeded_indices"])


SEMANTIC_WITNESSES = {
    "row_of_three_layout": _witness_layout("row_3"),
    "two_by_two_layout": _witness_layout("grid_2x2"),
    "two_by_three_layout": _witness_layout("grid_2x3"),
    "column_of_three_layout": _witness_layout("column_3"),
    "unseeded_chamber_preserved": _witness_unseeded,
    "repeated_seed_color_independent_chambers": _witness_repeat,
    "multiple_seeded_chambers": _witness_multiple_seeds,
    "unequal_chambers_with_seeded_nonmaximum": _witness_unequal_seeded_nonmax,
}
WITNESS_RIVALS = {
    "row_of_three_layout": ["identity_no_flood"],
    "two_by_two_layout": ["identity_no_flood"],
    "two_by_three_layout": ["identity_no_flood"],
    "column_of_three_layout": ["identity_no_flood"],
    "unseeded_chamber_preserved": ["fill_unseeded_with_modal"],
    "repeated_seed_color_independent_chambers": ["first_chamber_per_color"],
    "multiple_seeded_chambers": ["first_seed_only"],
    "unequal_chambers_with_seeded_nonmaximum": ["largest_chambers_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    observed: dict[str, set[Any]] = {name: set() for name in AXES}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output is not the chamber flood transform")
        for name in AXES:
            observed[name].add(info[name])
    if observed["layout_profile"] != set(LAYOUT_PROFILES):
        reasons.append(f"demonstrations do not cover all four layouts: {sorted(observed['layout_profile'])}")
    if observed["seed_pattern"] != set(SEED_PATTERNS):
        reasons.append(f"demonstrations do not cover all seed patterns: {sorted(observed['seed_pattern'])}")
    if observed["color_relation"] != set(COLOR_RELATIONS):
        reasons.append(f"demonstrations do not cover distinct and repeated seed colors: {sorted(observed['color_relation'])}")
    if observed["size_relation"] != set(SIZE_RELATIONS):
        reasons.append(f"demonstrations do not cover uniform and varied chamber sizes: {sorted(observed['size_relation'])}")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival survives every demonstration: {name}")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, query_errors = _analyse(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output is not the authoritative chamber flood")
    return reasons
