"""Generate identifiable lessons for ARC task cdecee7f.

The rule treats every non-black cell as an individual pixel, orders the pixels
by column and then row, and writes their colors into a 3x3 boustrophedon
(snake) output.  Canonical examples contain 6, 7, or 9 isolated pixels on a
10x10 canvas.  They do not contain two pixels in one column and therefore do
not identify the row tie-breaker; they also leave an object-deduplication rule
plausible because every same-color component is a singleton.

Ordinary draws alternate canonical-linked profiles with a linked
``tie_and_domino_9`` profile.  That profile simultaneously contains a
same-column pair with different colors and a separate same-color domino, so it
refutes both canonical-ambiguous shortcuts without displacing the public
manifold.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette


GENERATOR_ID = "9b028298192f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "36a01f0aa9d2"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "Collect every non-black cell, sort the cells by column ascending and then "
    "row ascending, and place the ordered colors into a 3x3 output whose middle "
    "row runs right-to-left. Missing entries are black."
)
INVARIANTS = [
    "background is black (0)",
    "every non-black cell is an answer-bearing pixel, including touching cells",
    "pixels are ordered by (column, row)",
    "the 3x3 output uses left-right, right-left, left-right snake order",
    "lawful lessons contain 6, 7, or 9 pixels and never more than nine",
]

_CANONICAL_PROFILES = (
    "canonical_6_distinct",
    "canonical_7_distinct",
    "canonical_9_two_pairs",
    "canonical_9_three_pairs",
)
SCENE_PROFILES = _CANONICAL_PROFILES + ("tie_and_domino_9",)
SCHEDULE_PROFILES = SCENE_PROFILES
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10 for canonical-linked draws; 10|12|14 for tie witnesses",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "10 for canonical-linked draws; 10|12|14 for tie witnesses",
        "valid": "10..14",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule preserving 50% canonical-linked draws",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# Every declared combination is constructible; keeping the declaration explicit
# makes any future rejection a contract failure rather than a legacy warning.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic profile scheduled for one draw."""
    del seed, difficulty
    cycle = (
        "canonical_6_distinct",
        "tie_and_domino_9",
        "canonical_7_distinct",
        "tie_and_domino_9",
        "canonical_9_two_pairs",
        "tie_and_domino_9",
        "canonical_9_three_pairs",
        "tie_and_domino_9",
    )
    return cycle[int(sample_index) % len(cycle)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    scheduled = schedule_profile(seed, sample_index, band)
    if overrides.get("scene_profile") is None:
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)

    if profile in _CANONICAL_PROFILES:
        default_h = default_w = 10
    else:
        default_h = default_w = {"easy": 10, "medium": 12, "hard": 14}[band]
    h = _draw_scheduled_int(ctx, "grid_h", default_h, overrides)
    w = _draw_scheduled_int(ctx, "grid_w", default_w, overrides)

    rng = ctx.draw_rng(f"scene:{profile}:{h}x{w}")
    if profile == "tie_and_domino_9":
        positions, domino = _pick_tie_and_domino_positions(h, w, rng)
        colors = _tie_and_domino_colors(positions, domino, rng)
    else:
        n_cells, pair_count = _canonical_profile_spec(profile)
        positions = _pick_isolated_unique_columns(n_cells, h, w, rng)
        colors = _canonical_profile_colors(n_cells, pair_count, positions, rng)

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color

    errors = self_check(
        grid,
        difficulty=band,
        meta={"scene_profile": profile, "overrides": dict(overrides)},
    )
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _draw_scheduled_int(ctx, label: str, default: int, overrides: dict) -> int:
    if overrides.get(label) is None:
        return int(ctx.draw_choice(label, (default,)))
    return ctx.draw_int(label, 10, 14)


def _canonical_profile_spec(profile: str) -> tuple[int, int]:
    return {
        "canonical_6_distinct": (6, 0),
        "canonical_7_distinct": (7, 0),
        "canonical_9_two_pairs": (9, 2),
        "canonical_9_three_pairs": (9, 3),
    }[profile]


def _pick_isolated_unique_columns(n: int, h: int, w: int, rng) -> list[Cell]:
    """Pick canonical-linked singleton pixels with one pixel per column."""
    for _ in range(2000):
        columns = sorted(rng.sample(range(w), n))
        rows = [rng.randrange(h) for _ in range(n)]
        positions = list(zip(rows, columns))
        if _has_cardinal_contact(positions):
            continue
        if _order_permutation(positions) == list(range(n)):
            continue
        return positions
    raise RuntimeError("could not place isolated unique-column pixels")


def _pick_tie_and_domino_positions(h: int, w: int, rng) -> tuple[list[Cell], set[Cell]]:
    """Place one different-color column tie and one same-color horizontal domino."""
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    for _ in range(4000):
        tie_col = rng.randrange(w)
        tie_rows = sorted(rng.sample(range(h), 2))
        if tie_rows[1] - tie_rows[0] < 2:
            continue
        tie = {(tie_rows[0], tie_col), (tie_rows[1], tie_col)}

        domino_row = rng.randrange(h)
        domino_col = rng.randrange(w - 1)
        domino = {(domino_row, domino_col), (domino_row, domino_col + 1)}
        if tie & domino:
            continue
        if any(_manhattan(a, b) == 1 for a in tie for b in domino):
            continue
        if tie_col in {domino_col, domino_col + 1}:
            continue

        positions = list(tie | domino)
        occupied_columns = {c for _, c in positions}
        candidates = all_cells[:]
        rng.shuffle(candidates)
        for cell in candidates:
            if len(positions) == 9:
                break
            r, c = cell
            if c == tie_col or c in occupied_columns:
                continue
            if any(_manhattan(cell, other) == 1 for other in positions):
                continue
            positions.append(cell)
            occupied_columns.add(c)
        if len(positions) != 9:
            continue
        if len({c for _, c in positions}) != 8:
            continue
        if _order_permutation(positions) == list(range(9)):
            continue
        return positions, domino
    raise RuntimeError("could not place tie-and-domino witness")


def _canonical_profile_colors(
    n: int, pair_count: int, positions: list[Cell], rng
) -> list[int]:
    distinct_count = n - pair_count
    palette = list(random_palette(rng, distinct_count))
    multiset = palette + palette[:pair_count]
    for _ in range(1000):
        rng.shuffle(multiset)
        colors = list(multiset)
        grid = _grid_from_assignments(positions, colors)
        if _base_rivals_refuted(grid):
            return colors
    raise RuntimeError("could not assign discriminator colors")


def _tie_and_domino_colors(
    positions: list[Cell], domino: set[Cell], rng
) -> list[int]:
    palette = list(random_palette(rng, 8))
    domino_color = palette[0]
    other_colors = palette[1:]
    domino_indices = [i for i, cell in enumerate(positions) if cell in domino]
    other_indices = [i for i, cell in enumerate(positions) if cell not in domino]
    for _ in range(1000):
        rng.shuffle(other_colors)
        colors = [0] * len(positions)
        for index in domino_indices:
            colors[index] = domino_color
        for index, color in zip(other_indices, other_colors):
            colors[index] = color
        grid = _grid_from_assignments(positions, colors)
        if _all_rivals_refuted(grid):
            return colors
    raise RuntimeError("could not assign tie-and-domino discriminator colors")


def _grid_from_assignments(positions: list[Cell], colors: list[int]) -> Grid:
    h = max(r for r, _ in positions) + 1
    w = max(c for _, c in positions) + 1
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    return grid


def _manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _has_cardinal_contact(positions: list[Cell]) -> bool:
    cells = set(positions)
    return any((r + dr, c + dc) in cells for r, c in cells for dr, dc in ((1, 0), (0, 1)))


def _order_permutation(positions: list[Cell]) -> list[int]:
    true_order = sorted(range(len(positions)), key=lambda i: (positions[i][1], positions[i][0]))
    row_order = sorted(range(len(positions)), key=lambda i: (positions[i][0], positions[i][1]))
    rank = {index: place for place, index in enumerate(true_order)}
    return [rank[index] for index in row_order]


def _cells(grid: Grid) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _pack_snake(colors: list[int]) -> Grid:
    output = full_grid(3, 3, 0)
    for index, color in enumerate(colors[:9]):
        r, offset = divmod(index, 3)
        c = offset if r % 2 == 0 else 2 - offset
        output[r][c] = color
    return output


def _pack_straight(colors: list[int]) -> Grid:
    output = full_grid(3, 3, 0)
    for index, color in enumerate(colors[:9]):
        r, c = divmod(index, 3)
        output[r][c] = color
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror; the canonical Racket program remains authoritative."""
    ordered = sorted(_cells(grid), key=lambda cell: (cell[1], cell[0]))
    return _pack_snake([value for _, _, value in ordered])


def _rival_row_major_scan(grid: Grid) -> Grid:
    ordered = sorted(_cells(grid), key=lambda cell: (cell[0], cell[1]))
    return _pack_snake([value for _, _, value in ordered])


def _rival_straight_pack(grid: Grid) -> Grid:
    ordered = sorted(_cells(grid), key=lambda cell: (cell[1], cell[0]))
    return _pack_straight([value for _, _, value in ordered])


def _rival_value_sort(grid: Grid) -> Grid:
    return _pack_snake(sorted(value for _, _, value in _cells(grid)))


def _rival_row_desc_within_column(grid: Grid) -> Grid:
    ordered = sorted(_cells(grid), key=lambda cell: (cell[1], -cell[0]))
    return _pack_snake([value for _, _, value in ordered])


def _same_color_components(grid: Grid) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for r, c, color in _cells(grid):
        if (r, c) in seen:
            continue
        queue = deque([(r, c)])
        seen.add((r, c))
        cells: list[Cell] = []
        while queue:
            cr, cc = queue.popleft()
            cells.append((cr, cc))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = cr + dr, cc + dc
                if (
                    0 <= nr < h
                    and 0 <= nc < w
                    and (nr, nc) not in seen
                    and grid[nr][nc] == color
                ):
                    seen.add((nr, nc))
                    queue.append((nr, nc))
        components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _rival_one_per_same_color_component(grid: Grid) -> Grid:
    components = _same_color_components(grid)
    components.sort(
        key=lambda obj: (
            min(c for _, c in obj["cells"]),
            min(r for r, _ in obj["cells"]),
        )
    )
    return _pack_snake([obj["color"] for obj in components])


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "row_major_scan": _rival_row_major_scan,
    "straight_row_major_pack": _rival_straight_pack,
    "sort_colors_by_value": _rival_value_sort,
    "row_descending_within_column": _rival_row_desc_within_column,
    "one_entry_per_same_color_component": _rival_one_per_same_color_component,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "row_descending_within_column": _rival_row_desc_within_column,
    "one_entry_per_same_color_component": _rival_one_per_same_color_component,
}


def _base_rivals_refuted(grid: Grid) -> bool:
    answer = rule_mirror(grid)
    return all(
        rival(grid) != answer
        for rival in (
            _rival_row_major_scan,
            _rival_straight_pack,
            _rival_value_sort,
        )
    )


def _all_rivals_refuted(grid: Grid) -> bool:
    answer = rule_mirror(grid)
    return all(rival(grid) != answer for rival in SEMANTIC_RIVALS.values())


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if not (10 <= h <= 14 and 10 <= w <= 14):
        errors.append(f"grid dimensions must each be in 10..14, got {h}x{w}")
    bad_values = [value for row in grid for value in row if not isinstance(value, int) or not 0 <= value <= 9]
    if bad_values:
        errors.append(f"grid contains non-ARC values: {bad_values[:3]!r}")
        return {"errors": errors}

    cells = _cells(grid)
    positions = [(r, c) for r, c, _ in cells]
    colors = [value for _, _, value in cells]
    components = _same_color_components(grid)
    occupied_by_column: dict[int, list[tuple[int, int]]] = {}
    for r, c, value in cells:
        occupied_by_column.setdefault(c, []).append((r, value))
    adjacent_pairs = {
        tuple(sorted(((r, c), (nr, nc))))
        for r, c in positions
        for nr, nc in ((r + 1, c), (r, c + 1))
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
    }
    same_color_adjacent = {
        pair
        for pair in adjacent_pairs
        if grid[pair[0][0]][pair[0][1]] == grid[pair[1][0]][pair[1][1]]
    }
    facts = {
        "height": h,
        "width": w,
        "cells": cells,
        "positions": positions,
        "colors": colors,
        "color_counts": Counter(colors),
        "components": components,
        "component_sizes": tuple(sorted(len(obj["cells"]) for obj in components)),
        "occupied_by_column": occupied_by_column,
        "occupied_columns": len(occupied_by_column),
        "adjacent_pairs": adjacent_pairs,
        "same_color_adjacent_pairs": same_color_adjacent,
    }
    return {"errors": errors, "facts": facts}


def _classify_profile(facts: dict[str, Any]) -> str | None:
    n = len(facts["cells"])
    frequencies = tuple(sorted(facts["color_counts"].values(), reverse=True))
    isolated = not facts["adjacent_pairs"]
    unique_columns = facts["occupied_columns"] == n

    if isolated and unique_columns:
        if n == 6 and frequencies == (1, 1, 1, 1, 1, 1):
            return "canonical_6_distinct"
        if n == 7 and frequencies == (1, 1, 1, 1, 1, 1, 1):
            return "canonical_7_distinct"
        if n == 9 and frequencies == (2, 2, 1, 1, 1, 1, 1):
            return "canonical_9_two_pairs"
        if n == 9 and frequencies == (2, 2, 2, 1, 1, 1):
            return "canonical_9_three_pairs"

    if n != 9 or frequencies != (2, 1, 1, 1, 1, 1, 1, 1):
        return None
    if facts["occupied_columns"] != 8:
        return None
    if len(facts["adjacent_pairs"]) != 1 or len(facts["same_color_adjacent_pairs"]) != 1:
        return None
    if facts["component_sizes"] != (1, 1, 1, 1, 1, 1, 1, 2):
        return None
    repeated_columns = [rows for rows in facts["occupied_by_column"].values() if len(rows) == 2]
    if len(repeated_columns) != 1:
        return None
    tied = sorted(repeated_columns[0])
    if tied[0][1] == tied[1][1] or tied[1][0] - tied[0][0] < 2:
        return None
    return "tie_and_domino_9"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete linked teaching grammar and reject impostors."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if profile is None:
        return [
            "scene must match a canonical 6/7/9 isolated profile or the linked "
            "nine-pixel tie-and-domino counterexample profile"
        ]

    if not _base_rivals_refuted(grid):
        errors.append("scene does not expose column order, snake order, and value-order distinctions")
    if profile == "tie_and_domino_9":
        if _rival_row_desc_within_column(grid) == rule_mirror(grid):
            errors.append("same-column pair does not expose ascending row tie-breaking")
        if _rival_one_per_same_color_component(grid) == rule_mirror(grid):
            errors.append("same-color domino does not expose per-cell rather than per-object handling")

    requested = None
    if isinstance(meta, dict):
        requested = meta.get("scene_profile")
        if requested is None and isinstance(meta.get("overrides"), dict):
            requested = meta["overrides"].get("scene_profile")
    if requested is not None and requested != profile:
        errors.append(f"scene_profile requested {requested!r}, observed {profile!r}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if profile is None:
        return {}
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "scene_profile": profile,
    }


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid is outside the exact public joint manifold."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if (facts["height"], facts["width"]) != (10, 10):
        return [f"canonical canvas is 10x10, got {facts['height']}x{facts['width']}"]
    if profile not in _CANONICAL_PROFILES:
        return [f"canonical linked morphology not observed: {profile!r}"]
    return []


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (facts["height"], facts["width"], _classify_profile(facts))


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "scene_profile": _classify_profile(facts),
        "height": facts["height"],
        "width": facts["width"],
        "pixel_count": len(facts["cells"]),
        "occupied_columns": facts["occupied_columns"],
        "color_multiplicities": tuple(sorted(facts["color_counts"].values(), reverse=True)),
        "component_sizes": facts["component_sizes"],
        "strict_canonical_like": not strict_canonical_like(grid),
        "rival_disagreements": {
            name: rival(grid) != rule_mirror(grid)
            for name, rival in SEMANTIC_RIVALS.items()
        },
    }


def _witness_rival(name: str) -> Callable[[Grid], bool]:
    return lambda grid: SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "canonical_6_distinct": lambda grid: observe_overrides(grid).get("scene_profile") == "canonical_6_distinct",
    "canonical_7_distinct": lambda grid: observe_overrides(grid).get("scene_profile") == "canonical_7_distinct",
    "canonical_9_two_pairs": lambda grid: observe_overrides(grid).get("scene_profile") == "canonical_9_two_pairs",
    "canonical_9_three_pairs": lambda grid: observe_overrides(grid).get("scene_profile") == "canonical_9_three_pairs",
    "row_scan_disagrees": _witness_rival("row_major_scan"),
    "straight_pack_disagrees": _witness_rival("straight_row_major_pack"),
    "value_sort_disagrees": _witness_rival("sort_colors_by_value"),
    "tie_and_domino_refutes_canonical_shortcuts": lambda grid: (
        observe_overrides(grid).get("scene_profile") == "tie_and_domino_9"
        and _rival_row_desc_within_column(grid) != rule_mirror(grid)
        and _rival_one_per_same_color_component(grid) != rule_mirror(grid)
    ),
}
WITNESS_RIVALS = {
    "row_scan_disagrees": ["row_major_scan"],
    "straight_pack_disagrees": ["straight_row_major_pack"],
    "value_sort_disagrees": ["sort_colors_by_value"],
    "tie_and_domino_refutes_canonical_shortcuts": [
        "row_descending_within_column",
        "one_entry_per_same_color_component",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which a named wrong rule still determines the query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(f"demo {index} output does not match the column-sort snake rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo.get("output") for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query answer")
    return reasons


def mutation_fixtures():
    """Named structural near-misses that self_check must reject."""
    valid_small = generate(7001, 0, difficulty="easy", scene_profile="canonical_6_distinct")
    valid_tie = generate(7002, 1, difficulty="easy", scene_profile="tie_and_domino_9")
    fixtures: list[tuple[str, Grid]] = []

    all_background = full_grid(10, 10, 0)
    fixtures.append(("all_background", all_background))

    five_pixels = deepcopy(valid_small)
    r, c, _ = _cells(five_pixels)[0]
    five_pixels[r][c] = 0
    fixtures.append(("five_pixels", five_pixels))

    invalid_color = deepcopy(valid_small)
    r, c, _ = _cells(invalid_color)[0]
    invalid_color[r][c] = 10
    fixtures.append(("invalid_arc_color", invalid_color))

    broken_domino = deepcopy(valid_tie)
    pair = next(iter(_analyze(broken_domino)["facts"]["same_color_adjacent_pairs"]))
    (r1, c1), (r2, c2) = pair
    broken_domino[r2][c2] = next(color for color in range(1, 10) if color not in {broken_domino[r1][c1]} and color not in [v for _, _, v in _cells(broken_domino)])
    fixtures.append(("domino_loses_duplicate_color", broken_domino))

    triple_color = deepcopy(valid_tie)
    repeated = next(color for color, count in Counter(v for _, _, v in _cells(triple_color)).items() if count == 2)
    r, c, _ = next(cell for cell in _cells(triple_color) if cell[2] != repeated)
    triple_color[r][c] = repeated
    fixtures.append(("triple_repeated_color", triple_color))

    adjacent_canonical = deepcopy(valid_small)
    cells = _cells(adjacent_canonical)
    r, c, color = cells[0]
    adjacent_canonical[r][c] = 0
    target = next(
        (nr, nc)
        for _, _, _ in [cells[1]]
        for nr, nc in ((cells[1][0] + 1, cells[1][1]), (cells[1][0] - 1, cells[1][1]), (cells[1][0], cells[1][1] + 1), (cells[1][0], cells[1][1] - 1))
        if 0 <= nr < len(adjacent_canonical)
        and 0 <= nc < len(adjacent_canonical[0])
        and adjacent_canonical[nr][nc] == 0
    )
    adjacent_canonical[target[0]][target[1]] = color
    fixtures.append(("unsupported_adjacent_canonical_profile", adjacent_canonical))
    return fixtures
