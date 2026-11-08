"""Generator for ``Area Rank Recolor`` (task ``fae242ae157d``).

The input is a 0-background grid containing exactly three separated,
monochrome, 4-connected objects with distinct areas.  Sort the objects by
ascending cell count and repaint their unchanged cells 2, 3, and 4.

The official examples all use areas 4/5/6 and place those areas in ascending
scan order.  The generated curriculum deliberately includes different area
triples, reversed/mixed scan orders, monochrome inputs, and permuted 2/3/4
input colours.  A six-slot cue schedule also reuses canonical dimensions and
palette modes across different scan orders, so exposed metadata cannot stand
in for comparing object areas.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fae242ae157d"
TASK_ID = "fae242ae157d"
VERSION = "4.1.0"
RULE_HASH = "ce7e86577c99"

SUMMARY = (
    "A 0-background grid contains exactly three separated monochrome "
    "4-connected objects with strictly distinct cell counts. Sort the objects "
    "by ascending area and repaint their unchanged cells on a blank grid: the "
    "smallest object becomes 2, the middle object 3, and the largest object 4. "
    "Input colour, top-left scan order, shape, and absolute area are distractors."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "background is 0",
    "there are exactly three separated 4-connected nonzero objects",
    "each object is monochrome and has between 3 and 12 cells",
    "the three cell counts are strictly distinct, so ascending-area rank is unique",
    "input colours may overlap 2/3/4 but never determine the output rank",
    "the output preserves all object cells and recolours ranks to 2, 3, and 4",
]

CANONICAL_PROFILES = (
    "canonical_9x12",
    "canonical_10x13",
    "canonical_9x11",
    "canonical_10x12",
)
GENERAL_PROFILES = ("general_11x14", "general_13x16")
SCENE_PROFILES = CANONICAL_PROFILES + GENERAL_PROFILES
COLOR_MODES = ("distinct", "rank_permuted", "monochrome")
SCAN_ORDERS = ("ascending", "descending", "mixed")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled canonical/general profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "color_mode": {
        "type": "str",
        "default": "scheduled distinct/rank-permuted/monochrome input colours",
        "valid": "|".join(COLOR_MODES),
    },
    "scan_order": {
        "type": "str",
        "default": "scheduled ascending/descending/mixed top-left order",
        "valid": "|".join(SCAN_ORDERS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PROFILE_DIMS = {
    "canonical_9x12": (9, 12),
    "canonical_10x13": (10, 13),
    "canonical_9x11": (9, 11),
    "canonical_10x12": (10, 12),
    "general_11x14": (11, 14),
    "general_13x16": (13, 16),
}
_DIMS_TO_PROFILE = {dims: name for name, dims in _PROFILE_DIMS.items()}
_CANONICAL_SIZES = (4, 5, 6)
_GENERAL_SIZE_TRIPLES = {
    "general_11x14": ((3, 7, 10), (3, 8, 11), (7, 9, 12)),
    "general_13x16": ((3, 8, 12), (7, 10, 12), (8, 11, 12)),
}
_GENERALIZED_SIZE_TRIPLES = tuple(
    dict.fromkeys(
        triple
        for triples in _GENERAL_SIZE_TRIPLES.values()
        for triple in triples
    )
)
_DISTINCT_COLOR_TRIPLES = (
    (7, 5, 3),
    (8, 6, 4),
    (9, 7, 2),
    (5, 4, 7),
    (1, 6, 8),
)
_RANK_PERMUTATIONS = (
    (2, 4, 3),
    (3, 2, 4),
    (3, 4, 2),
    (4, 2, 3),
    (4, 3, 2),
)
_MONOCHROME_COLORS = (1, 2, 5, 6, 7, 8, 9)
_SCAN_RANKS_AT_ZONE = {
    "ascending": (0, 1, 2),
    "descending": (2, 1, 0),
    "mixed": (1, 2, 0),
}

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "scan_and_absolute_size_counterexample",
    "color_and_scan_counterexample",
)
_SCHEDULE_PERIOD = 6
_PROFILE_FAMILY_SCHEDULE = (
    "canonical",
    "canonical",
    "general_11x14",
    "canonical",
    "general_13x16",
    "canonical",
)
_COLOR_MODE_SCHEDULE = (
    "distinct",
    "rank_permuted",
    "monochrome",
    "distinct",
    "distinct",
    "rank_permuted",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the three-slot lesson schedule; every length-three window covers it."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if (len(grid), width) not in _DIMS_TO_PROFILE:
        return [
            "grid dimensions must match a declared scene profile; found "
            f"{len(grid)}x{width}"
        ]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colours 0..9"]
    return []


def _components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            result.append(tuple(sorted(cells)))
    return result


def _component_color(grid: list[list[int]], cells: Iterable[tuple[int, int]]):
    colors = {grid[row][col] for row, col in cells}
    return next(iter(colors)) if len(colors) == 1 else None


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {
            "errors": errors,
            "components": [],
            "sizes": [],
            "colors_by_rank": [],
            "scene_profile": None,
            "color_mode": None,
            "scan_order": None,
        }

    assert isinstance(grid, list)
    components = _components(grid)
    if 0 not in {value for row in grid for value in row}:
        errors.append("background colour 0 must be present")
    if len(components) != 3:
        errors.append(f"expected exactly three nonzero objects; found {len(components)}")

    sizes = [len(cells) for cells in components]
    if any(not 3 <= size <= 12 for size in sizes):
        errors.append(f"object areas must be in 3..12; found {sorted(sizes)}")
    if len(set(sizes)) != len(sizes):
        errors.append(f"object areas must be strictly distinct; found {sorted(sizes)}")

    component_colors: list[int] = []
    for index, cells in enumerate(components):
        color = _component_color(grid, cells)
        if color is None:
            found = sorted({grid[row][col] for row, col in cells})
            errors.append(f"object {index} must be monochrome; found {found}")
        else:
            component_colors.append(color)

    scene_profile = _DIMS_TO_PROFILE[(len(grid), len(grid[0]))]
    color_mode = None
    scan_order = None
    colors_by_rank: list[int] = []
    rank_by_component: dict[tuple[tuple[int, int], ...], int] = {}
    if len(components) == 3 and len(set(sizes)) == 3 and len(component_colors) == 3:
        ranked = sorted(components, key=lambda cells: (len(cells), min(cells)))
        rank_by_component = {cells: rank for rank, cells in enumerate(ranked)}
        colors_by_rank = [grid[cells[0][0]][cells[0][1]] for cells in ranked]
        if len(set(colors_by_rank)) == 1:
            color_mode = "monochrome"
        elif len(set(colors_by_rank)) == 3 and set(colors_by_rank) == {2, 3, 4}:
            if tuple(colors_by_rank) == (2, 3, 4):
                errors.append(
                    "input colours already equal the official area-rank output; "
                    "the scene would hide the transformation"
                )
            else:
                color_mode = "rank_permuted"
        elif len(set(colors_by_rank)) == 3:
            color_mode = "distinct"
        else:
            errors.append(
                "input colours must be all distinct, all equal, or a non-identity "
                "permutation of 2/3/4"
            )

        scan_components = sorted(components, key=min)
        scan_ranks = tuple(rank_by_component[cells] for cells in scan_components)
        if scan_ranks == (0, 1, 2):
            scan_order = "ascending"
        elif scan_ranks == (2, 1, 0):
            scan_order = "descending"
        else:
            scan_order = "mixed"

    return {
        "errors": errors,
        "components": components,
        "sizes": sizes,
        "component_colors": component_colors,
        "colors_by_rank": colors_by_rank,
        "rank_by_component": rank_by_component,
        "scene_profile": scene_profile,
        "color_mode": color_mode,
        "scan_order": scan_order,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or transformation-hiding lesson inputs."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "color_mode": analysis["color_mode"],
        "scan_order": analysis["scan_order"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if analysis["scene_profile"] not in CANONICAL_PROFILES:
        reasons.append("dimensions are not one of the four canonical profiles")
    if sorted(analysis["sizes"]) != list(_CANONICAL_SIZES):
        reasons.append("canonical object areas are exactly 4, 5, and 6")
    if analysis["color_mode"] != "distinct":
        reasons.append("canonical inputs use three distinct object colours")
    if analysis["scan_order"] != "ascending":
        reasons.append("canonical inputs place ascending areas in top-left scan order")
    return reasons


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    if strict_canonical_like(grid):
        return None
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
        tuple(sorted(analysis["sizes"])),
    )


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Exact Python mirror used only for tests and semantic diagnostics."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(len(grid), len(grid[0]), 0)
    for rank, cells in enumerate(sorted(analysis["components"], key=len)):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _random_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    for _ in range(512):
        cells = {(0, 0)}
        while len(cells) < size:
            row, col = rng.choice(sorted(cells))
            drow, dcol = rng.choice(_DIR4)
            cells.add((row + drow, col + dcol))
        normalized = _normalize(cells)
        height = max(row for row, _ in normalized) + 1
        width = max(col for _, col in normalized) + 1
        if height <= 4 and width <= 5:
            return normalized
    raise AssertionError(f"could not grow a compact connected shape of area {size}")


def _place_shape(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    *,
    top: int,
    left0: int,
    box_width: int,
    color: int,
    rng,
) -> None:
    shape_width = max(col for _, col in shape) + 1
    left = left0 + rng.randint(0, box_width - shape_width)
    for row, col in shape:
        grid[top + row][left + col] = color


def _canonical_profile_options(difficulty):
    if difficulty == "easy":
        return ("canonical_9x11", "canonical_9x12")
    if difficulty == "hard":
        return ("canonical_10x12", "canonical_10x13")
    return CANONICAL_PROFILES


def _choose_profile_options(difficulty, schedule_index: int):
    family = _PROFILE_FAMILY_SCHEDULE[schedule_index]
    if family == "canonical":
        return _canonical_profile_options(difficulty)
    return (family,)


def _profile_sizes(profile: str, slot: int, rng) -> tuple[int, int, int]:
    if slot == 0:
        return _CANONICAL_SIZES
    if profile in _GENERAL_SIZE_TRIPLES:
        return rng.choice(_GENERAL_SIZE_TRIPLES[profile])
    return rng.choice(_GENERALIZED_SIZE_TRIPLES)


def _colors_for_mode(mode: str, rng) -> tuple[int, int, int]:
    if mode == "distinct":
        colors = list(rng.choice(_DISTINCT_COLOR_TRIPLES))
        rng.shuffle(colors)
        return tuple(colors)
    if mode == "rank_permuted":
        return rng.choice(_RANK_PERMUTATIONS)
    color = rng.choice(_MONOCHROME_COLORS)
    return (color, color, color)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % 3
    schedule_index = sample_index % _SCHEDULE_PERIOD

    profile_options = (
        SCENE_PROFILES if "scene_profile" in overrides
        else _choose_profile_options(difficulty, schedule_index)
    )
    color_options = (
        COLOR_MODES if "color_mode" in overrides
        else (_COLOR_MODE_SCHEDULE[schedule_index],)
    )
    scan_options = (
        SCAN_ORDERS if "scan_order" in overrides
        else (("ascending",), ("descending",), ("mixed",))[slot]
    )

    profile = ctx.draw_choice("scene_profile", profile_options)
    color_mode = ctx.draw_choice("color_mode", color_options)
    scan_order = ctx.draw_choice("scan_order", scan_options)
    rng = ctx.draw_rng("scene")

    height, width = _PROFILE_DIMS[profile]
    sizes = _profile_sizes(profile, slot, rng)
    shapes = [_random_shape(rng, size) for size in sizes]
    colors_by_rank = _colors_for_mode(color_mode, ctx.draw_rng("colors"))
    ranks_at_zone = _SCAN_RANKS_AT_ZONE[scan_order]

    # Three spatial zones have fixed top rows 0, 2, and h-4.  The left zones
    # occupy columns 0..4 and the middle zone occupies the rightmost 5 columns,
    # leaving a cardinal gap even in the smallest 9x11 profile.
    zones = ((0, 0), (2, width - 5), (height - 4, 0))
    grid = full_grid(height, width, 0)
    for (top, left0), rank in zip(zones, ranks_at_zone):
        _place_shape(
            grid,
            shapes[rank],
            top=top,
            left0=left0,
            box_width=5,
            color=colors_by_rank[rank],
            rng=rng,
        )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "scene_profile": profile,
        "color_mode": color_mode,
        "scan_order": scan_order,
    }
    if observed != requested:
        raise AssertionError(f"observable override drift: requested={requested}, observed={observed}")
    return grid


def _valid(grid) -> bool:
    return not _analysis(grid)["errors"]


def _witness_canonical_anchor(grid) -> bool:
    return not strict_canonical_like(grid)


def _witness_generalized_size_triplet(grid) -> bool:
    analysis = _analysis(grid)
    return _valid(grid) and sorted(analysis["sizes"]) != list(_CANONICAL_SIZES)


def _witness_scan_order_conflict(grid) -> bool:
    analysis = _analysis(grid)
    return _valid(grid) and analysis["scan_order"] != "ascending"


def _witness_descending_scan_order(grid) -> bool:
    analysis = _analysis(grid)
    return _valid(grid) and analysis["scan_order"] == "descending"


def _witness_mixed_scan_order(grid) -> bool:
    analysis = _analysis(grid)
    return _valid(grid) and analysis["scan_order"] == "mixed"


def _witness_distinct_colors(grid) -> bool:
    analysis = _analysis(grid)
    return _valid(grid) and analysis["color_mode"] == "distinct"


def _witness_rank_palette_permuted(grid) -> bool:
    analysis = _analysis(grid)
    return _valid(grid) and analysis["color_mode"] == "rank_permuted"


def _witness_monochrome_input(grid) -> bool:
    analysis = _analysis(grid)
    return _valid(grid) and analysis["color_mode"] == "monochrome"


def _witness_ascending_differs_from_descending(grid) -> bool:
    return _valid(grid)


def _witness_schedule_cue_decoupled(grid) -> bool:
    """A generated case where the legacy scene-cue shortcut is wrong."""
    return _valid(grid) and _competitor_scene_cues(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "canonical_anchor": _witness_canonical_anchor,
    "generalized_size_triplet": _witness_generalized_size_triplet,
    "scan_order_conflict": _witness_scan_order_conflict,
    "descending_scan_order": _witness_descending_scan_order,
    "mixed_scan_order": _witness_mixed_scan_order,
    "distinct_input_colours": _witness_distinct_colors,
    "rank_palette_permuted": _witness_rank_palette_permuted,
    "monochrome_input": _witness_monochrome_input,
    "ascending_differs_from_descending": _witness_ascending_differs_from_descending,
    "schedule_cue_decoupled": _witness_schedule_cue_decoupled,
}

# These predicates measure positive branch coverage.  They do not claim a
# specific competing rule is refuted on every firing; rival-bearing witnesses
# are declared separately in WITNESS_RIVALS below.
BRANCH_WITNESSES = {
    "canonical_anchor",
    "descending_scan_order",
    "mixed_scan_order",
    "distinct_input_colours",
    "monochrome_input",
}


def _blank_output(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _competitor_scan_order(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _blank_output(grid)
    output = _blank_output(grid)
    for rank, cells in enumerate(sorted(analysis["components"], key=min)):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _competitor_descending_area(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _blank_output(grid)
    output = _blank_output(grid)
    for rank, cells in enumerate(sorted(analysis["components"], key=len, reverse=True)):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _competitor_numeric_color(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _blank_output(grid)
    output = _blank_output(grid)
    ordered = sorted(
        analysis["components"],
        key=lambda cells: (grid[cells[0][0]][cells[0][1]], min(cells)),
    )
    for rank, cells in enumerate(ordered):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


def _competitor_fixed_456(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _blank_output(grid)
    output = _blank_output(grid)
    fixed = {4: 2, 5: 3, 6: 4}
    for cells in analysis["components"]:
        color = fixed.get(len(cells), 1)
        for row, col in cells:
            output[row][col] = color
    return output


def _competitor_identity(grid):
    return [row[:] for row in grid]


def _competitor_scene_cues(grid):
    """Legacy shortcut: infer rank from dimensions plus scan position."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _blank_output(grid)
    if analysis["scene_profile"] in CANONICAL_PROFILES:
        ranks_at_scan_position = (0, 1, 2)
    elif analysis["scene_profile"] == "general_11x14":
        ranks_at_scan_position = (2, 1, 0)
    else:
        ranks_at_scan_position = (1, 2, 0)
    output = _blank_output(grid)
    for cells, rank in zip(
        sorted(analysis["components"], key=min),
        ranks_at_scan_position,
    ):
        for row, col in cells:
            output[row][col] = 2 + rank
    return output


SEMANTIC_RIVALS = {
    "rank by top-left scan order": _competitor_scan_order,
    "rank by descending area": _competitor_descending_area,
    "rank by numeric input colour": _competitor_numeric_color,
    "map absolute areas 4/5/6 to 2/3/4": _competitor_fixed_456,
    "leave the input unchanged": _competitor_identity,
    "rank from scene dimensions and top-left position": _competitor_scene_cues,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "rank by top-left scan order": _competitor_scan_order,
    "map absolute areas 4/5/6 to 2/3/4": _competitor_fixed_456,
    "rank from scene dimensions and top-left position": _competitor_scene_cues,
}
WITNESS_RIVALS = {
    "generalized_size_triplet": ["map absolute areas 4/5/6 to 2/3/4"],
    "scan_order_conflict": ["rank by top-left scan order"],
    "rank_palette_permuted": [
        "rank by numeric input colour",
        "leave the input unchanged",
    ],
    "ascending_differs_from_descending": ["rank by descending area"],
    "schedule_cue_decoupled": [
        "rank from scene dimensions and top-left position"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} is outside the teaching grammar: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match ascending-area recolouring")
    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is outside the teaching grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match ascending-area recolouring")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query_answer:
                reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
