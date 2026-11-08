"""Generator for ARC task 65a142eb4d9b — expand 4-neighbor singletons.

The authoritative rule examines the original input.  Every nonzero cell with no
same-color cardinal neighbor paints a same-color plus (the center and every
in-bounds cardinal neighbor).  Cells belonging to a same-color cardinal
component are unchanged.

The six-slot default curriculum alternates three lesson roles:

* ``canonical``: sparse, distinct, interior dots like the public task;
* ``isolation``: a same-color domino plus a remote singleton of that color,
  proving that eligibility is local rather than global and that non-singletons
  do not expand;
* ``diagonal_edge``: a same-color diagonal pair plus a border singleton,
  proving 4-connectivity and clipped in-bounds arms.

Every three consecutive examples contain all three roles.  Exact overrides are
limited to four quantities that can be recovered from returned pixels.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "65a142eb4d9b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7224a7556e4b"

SUMMARY = (
    "On a black grid, expand every nonzero cell that has no same-color "
    "cardinal neighbor into a same-color plus, clipped at the grid boundary. "
    "Same-color cardinal components remain unchanged.  The linked three-demo "
    "curriculum distinguishes local 4-neighbor isolation, repeated colors, "
    "non-singletons, diagonal contact, and edge clipping."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "all cells are ARC colors 0..9 and background is 0",
    "there are 1..5 expandable 4-neighbor singletons",
    "there are 0..1 same-color cardinal domino distractors",
    "different colors do not touch cardinally",
    "expandable plus footprints do not conflict; a same-color diagonal pair may overlap",
    "every three scheduled examples contain canonical, isolation, and diagonal-edge roles",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-profile schedule spanning 7..10",
        "valid": "7..10",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "six-profile schedule spanning 7..10",
        "valid": "7..10",
        "doc": "Returned grid width.",
    },
    "n_expandable_cells": {
        "type": "int",
        "default": "six-profile schedule covers every count 1..5",
        "valid": "1..5",
        "doc": "Number of cells eligible to expand under the selected rule.",
    },
    "n_blocked_dominoes": {
        "type": "int",
        "default": "one in isolation profiles, otherwise zero",
        "valid": "0..1",
        "doc": "Number of unchanged same-color cardinal domino components.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_AXIS_BOUNDS = {
    "grid_h": (7, 10),
    "grid_w": (7, 10),
    "n_expandable_cells": (1, 5),
    "n_blocked_dominoes": (0, 1),
}
_CANONICAL_SHAPES = frozenset({(7, 7), (6, 8), (7, 6), (8, 8)})

SCHEDULE_PROFILES = (
    "canonical_one",
    "isolation_local_small",
    "diagonal_edge_small",
    "canonical_two",
    "isolation_local_large",
    "diagonal_edge_large",
)

# (height, width, expandable count, blocked-domino count).  The two canonical
# anchors stay exact in every band so medium/hard retain public-profile support.
_PROFILE_AXES = {
    "easy": {
        "canonical_one": (7, 7, 1, 0),
        "isolation_local_small": (7, 8, 2, 1),
        "diagonal_edge_small": (7, 7, 3, 0),
        "canonical_two": (8, 8, 2, 0),
        "isolation_local_large": (8, 8, 4, 1),
        "diagonal_edge_large": (8, 9, 5, 0),
    },
    "medium": {
        "canonical_one": (7, 7, 1, 0),
        "isolation_local_small": (8, 8, 2, 1),
        "diagonal_edge_small": (8, 9, 3, 0),
        "canonical_two": (8, 8, 2, 0),
        "isolation_local_large": (9, 9, 4, 1),
        "diagonal_edge_large": (9, 10, 5, 0),
    },
    "hard": {
        "canonical_one": (7, 7, 1, 0),
        "isolation_local_small": (9, 9, 2, 1),
        "diagonal_edge_small": (9, 10, 3, 0),
        "canonical_two": (8, 8, 2, 0),
        "isolation_local_large": (10, 10, 4, 1),
        "diagonal_edge_large": (10, 10, 5, 0),
    },
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic six-slot profile name for audit replay."""
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")


def _draw_axis(ctx, overrides, name: str, scheduled: int) -> int:
    lo, hi = _AXIS_BOUNDS[name]
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    # The schedule is an explicit curriculum, not an unrecorded post-draw edit.
    return ctx.draw_choice(name, (scheduled,))


def _neighbors(
    point: tuple[int, int],
    h: int,
    w: int,
    deltas: Iterable[tuple[int, int]] = _CARDINALS,
) -> list[tuple[int, int]]:
    r, c = point
    return [
        (r + dr, c + dc)
        for dr, dc in deltas
        if 0 <= r + dr < h and 0 <= c + dc < w
    ]


def _footprint(point: tuple[int, int], h: int, w: int) -> set[tuple[int, int]]:
    return {point, *_neighbors(point, h, w)}


def _group_footprint(
    group: Sequence[tuple[int, int]], h: int, w: int
) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for point in group:
        cells.update(_footprint(point, h, w))
    return cells


def _candidate_groups(kind: str, h: int, w: int) -> list[tuple[tuple[int, int], ...]]:
    if kind == "interior":
        return [((r, c),) for r in range(1, h - 1) for c in range(1, w - 1)]
    if kind == "edge":
        points = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if r in (0, h - 1) or c in (0, w - 1)
        ]
        # Prefer a three-cell clipped plus to a corner's two-cell clipping.
        return [
            (point,)
            for point in points
            if point not in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
        ]
    if kind == "diagonal":
        groups = []
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                for dr, dc in ((1, 1), (1, -1)):
                    other = (r + dr, c + dc)
                    if 1 <= other[0] < h - 1 and 1 <= other[1] < w - 1:
                        groups.append(((r, c), other))
        return groups
    if kind == "any":
        return [((r, c),) for r in range(h) for c in range(w)]
    raise ValueError(f"unknown layout group kind: {kind}")


def _domino_candidates(
    reserved: set[tuple[int, int]], h: int, w: int
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    candidates = []
    for r in range(h):
        for c in range(w):
            for dr, dc in ((1, 0), (0, 1)):
                other = (r + dr, c + dc)
                if (
                    other[0] < h
                    and other[1] < w
                    and (r, c) not in reserved
                    and other not in reserved
                ):
                    candidates.append(((r, c), other))
    return candidates


def _layout(
    ctx,
    h: int,
    w: int,
    group_kinds: Sequence[str],
    n_blocked_dominoes: int,
    *,
    isolate_domino_from_first_group: bool = False,
) -> tuple[list[tuple[tuple[int, int], ...]], tuple[tuple[int, int], ...]]:
    """Construct a complete layout by finite backtracking, never by retry cap."""
    rng = ctx.draw_rng("layout")
    options: list[list[tuple[tuple[int, int], ...]]] = []
    for kind in group_kinds:
        groups = _candidate_groups(kind, h, w)
        rng.shuffle(groups)
        # Smaller clipped footprints are useful in tight exact-override cases;
        # stable sort preserves keyed random order within each footprint size.
        groups.sort(key=lambda group: len(_group_footprint(group, h, w)))
        options.append(groups)

    def search(
        index: int,
        reserved: set[tuple[int, int]],
        chosen: list[tuple[tuple[int, int], ...]],
    ):
        if index == len(options):
            if not n_blocked_dominoes:
                return chosen, ()
            dominoes = _domino_candidates(reserved, h, w)
            if isolate_domino_from_first_group and chosen:
                first_group = chosen[0]
                dominoes = [
                    domino
                    for domino in dominoes
                    if all(
                        max(abs(r - rr), abs(c - cc)) > 1
                        for r, c in domino
                        for rr, cc in first_group
                    )
                ]
            rng.shuffle(dominoes)
            if dominoes:
                return chosen, dominoes[0]
            return None
        for group in options[index]:
            footprint = _group_footprint(group, h, w)
            if footprint & reserved:
                continue
            result = search(index + 1, reserved | footprint, [*chosen, group])
            if result is not None:
                return result
        return None

    result = search(0, set(), [])
    if result is None:
        raise RuntimeError(
            "constructive placement failed for "
            f"{h}x{w}, groups={tuple(group_kinds)!r}, "
            f"dominoes={n_blocked_dominoes}"
        )
    return result


def _profile_group_kinds(profile: str, n_expandable: int) -> list[str]:
    if profile.startswith("diagonal_edge"):
        if n_expandable < 3:
            raise ValueError("diagonal-edge profiles require at least three expandables")
        return ["diagonal", "edge", *(["interior"] * (n_expandable - 3))]
    if profile.startswith(("canonical", "isolation")):
        return ["interior"] * n_expandable
    return ["any"] * n_expandable


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, difficulty=band)
    defaults = _PROFILE_AXES[band][profile]
    h = _draw_axis(ctx := gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    ), overrides, "grid_h", defaults[0])
    w = _draw_axis(ctx, overrides, "grid_w", defaults[1])
    n_expandable = _draw_axis(ctx, overrides, "n_expandable_cells", defaults[2])
    n_dominoes = _draw_axis(ctx, overrides, "n_blocked_dominoes", defaults[3])

    # Overrides request exact observable quantities, not a curriculum role.
    layout_profile = "general_override" if any(
        value is not None for value in overrides.values()
    ) else profile
    kinds = _profile_group_kinds(layout_profile, n_expandable)
    groups, domino = _layout(
        ctx,
        h,
        w,
        kinds,
        n_dominoes,
        isolate_domino_from_first_group=layout_profile.startswith("isolation"),
    )

    color_count = len(groups) + (
        1 if n_dominoes and not layout_profile.startswith("isolation") else 0
    )
    colors = list(ctx.draw_distinct_colors("palette", n=color_count, exclude=(0,)))
    grid = full_grid(h, w, 0)
    for color, group in zip(colors, groups):
        for r, c in group:
            grid[r][c] = color
    if domino:
        domino_color = colors[0] if layout_profile.startswith("isolation") else colors[-1]
        for r, c in domino:
            grid[r][c] = domino_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed an invalid grid: {errors}")
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    for index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return [f"row {index} is not rectangular width {width}"]
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["grid values must be integer ARC colors 0..9"]
    return []


def _same_color_components(
    grid, *, diagonal: bool = False
) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    deltas = (*_CARDINALS, *_DIAGONALS) if diagonal else _CARDINALS
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components: list[tuple[int, set[tuple[int, int]]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        cells = {start}
        while queue:
            point = queue.popleft()
            for neighbor in _neighbors(point, h, w, deltas):
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
                    cells.add(neighbor)
        components.append((color, cells))
    return components


def _expandable_cells(grid) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
        and all(
            grid[nr][nc] != value
            for nr, nc in _neighbors((r, c), h, w)
        )
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the deliberately narrow, conflict-free teaching grammar."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (5 <= h <= 12 and 5 <= w <= 12):
        errors.append(f"grid shape {h}x{w} outside accepted 5..12 range")

    components4 = _same_color_components(grid)
    components8 = _same_color_components(grid, diagonal=True)
    expandable = _expandable_cells(grid)
    dominoes = [cells for _, cells in components4 if len(cells) == 2]
    blocked_cells = set().union(*dominoes) if dominoes else set()

    if not 1 <= len(expandable) <= 5:
        errors.append(f"expandable cell count {len(expandable)} outside [1,5]")
    if any(len(cells) not in (1, 2) for _, cells in components4):
        errors.append("same-color cardinal components must be singletons or dominoes")
    if len(dominoes) > 1:
        errors.append(f"blocked domino count {len(dominoes)} exceeds 1")
    if any(len(cells) > 2 for _, cells in components8):
        errors.append("same-color 8-connected components may contain at most two cells")

    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            for nr, nc in _neighbors((r, c), h, w, ((1, 0), (0, 1))):
                if grid[nr][nc] != 0 and grid[nr][nc] != grid[r][c]:
                    errors.append("different colors may not touch cardinally")
                    break

    for index, (r, c, color) in enumerate(expandable):
        footprint = _footprint((r, c), h, w)
        if footprint & blocked_cells:
            errors.append("an expandable plus footprint intersects a blocked domino")
        for rr, cc, other_color in expandable[index + 1 :]:
            other_footprint = _footprint((rr, cc), h, w)
            if not footprint & other_footprint:
                continue
            lawful_diagonal_overlap = (
                color == other_color
                and abs(r - rr) == 1
                and abs(c - cc) == 1
            )
            if not lawful_diagonal_overlap:
                errors.append("expandable plus footprints conflict")

    nonzero_count = sum(value != 0 for row in grid for value in row)
    if nonzero_count > 7:
        errors.append(f"nonzero cell count {nonzero_count} exceeds 7")
    return list(dict.fromkeys(errors))


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors[0]}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_expandable_cells": len(_expandable_cells(grid)),
        "n_blocked_dominoes": sum(
            len(cells) == 2 for _, cells in _same_color_components(grid)
        ),
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the sparse distinct interior-dot public profile."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) not in _CANONICAL_SHAPES:
        errors.append(f"shape {(h, w)} is outside the four public profiles")
    expandable = _expandable_cells(grid)
    if len(expandable) not in (1, 2):
        errors.append("public profiles contain one or two expandable cells")
    if any(len(cells) == 2 for _, cells in _same_color_components(grid)):
        errors.append("public profiles contain no blocked domino")
    counts = Counter(value for row in grid for value in row if value != 0)
    if any(count != 1 for count in counts.values()):
        errors.append("public profiles use each nonzero color exactly once")
    if any(r in (0, h - 1) or c in (0, w - 1) for r, c, _ in expandable):
        errors.append("public-profile cells are interior")
    return errors


def _paint_plus(output, r: int, c: int, color: int) -> None:
    h, w = len(output), len(output[0])
    output[r][c] = color
    for nr, nc in _neighbors((r, c), h, w):
        output[nr][nc] = color


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket rule for testing."""
    if _grid_errors(grid):
        raise ValueError("rule_mirror requires a rectangular ARC-color grid")
    output = deepcopy(grid)
    for r, c, color in _expandable_cells(grid):
        _paint_plus(output, r, c, color)
    return output


def _rival_expand_all_nonzero(grid):
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                _paint_plus(output, r, c, color)
    return output


def _rival_globally_unique_colors(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0 and counts[color] == 1:
                _paint_plus(output, r, c, color)
    return output


def _rival_eight_connected_singletons(grid):
    singleton_points = {
        next(iter(cells))
        for _, cells in _same_color_components(grid, diagonal=True)
        if len(cells) == 1
    }
    output = deepcopy(grid)
    for r, c in sorted(singleton_points):
        _paint_plus(output, r, c, grid[r][c])
    return output


def _rival_interior_only(grid):
    h, w = len(grid), len(grid[0])
    output = deepcopy(grid)
    for r, c, color in _expandable_cells(grid):
        if 0 < r < h - 1 and 0 < c < w - 1:
            _paint_plus(output, r, c, color)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "expand_all_nonzero": _rival_expand_all_nonzero,
    "globally_unique_colors": _rival_globally_unique_colors,
    "eight_connected_singletons": _rival_eight_connected_singletons,
    "interior_only": _rival_interior_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_rival_difference(grid, rival_name: str) -> bool:
    return not self_check(grid) and (
        rule_mirror(grid) != SEMANTIC_RIVALS[rival_name](grid)
    )


def _witness_blocked_cells(grid) -> bool:
    return _valid_rival_difference(grid, "expand_all_nonzero")


def _witness_local_isolation(grid) -> bool:
    return _valid_rival_difference(grid, "globally_unique_colors")


def _witness_four_connectivity(grid) -> bool:
    return _valid_rival_difference(grid, "eight_connected_singletons")


def _witness_edge_clipping(grid) -> bool:
    return _valid_rival_difference(grid, "interior_only")


SEMANTIC_WITNESSES = {
    "blocked_cardinal_component_does_not_expand": _witness_blocked_cells,
    "isolation_is_local_not_global": _witness_local_isolation,
    "cardinal_not_eight_connectivity": _witness_four_connectivity,
    "border_pluses_are_clipped": _witness_edge_clipping,
}
WITNESS_RIVALS = {
    "blocked_cardinal_component_does_not_expand": ["expand_all_nonzero"],
    "isolation_is_local_not_global": ["globally_unique_colors"],
    "cardinal_not_eight_connectivity": ["eight_connected_singletons"],
    "border_pluses_are_clipped": ["interior_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to eliminate every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstration pairs"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is not an input/output pair")
            continue
        grammar_errors = self_check(pair["input"])
        if grammar_errors:
            reasons.append(f"{role} input is outside linked grammar: {grammar_errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with selected rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            if all(
                competitor(pair["input"]) == pair["output"]
                for pair in demos
                if isinstance(pair, dict) and "input" in pair and "output" in pair
            ):
                reasons.append(f"competitor {name!r} survives every demonstration")
        except Exception as exc:  # pragma: no cover - diagnostic boundary
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures():
    """Near-miss teaching scenes that the structural validator must reject."""
    blank = full_grid(7, 7, 0)

    solid = full_grid(7, 7, 1)

    triple = full_grid(7, 7, 0)
    triple[3][2:5] = [2, 2, 2]

    block = full_grid(7, 7, 0)
    for r in (2, 3):
        for c in (2, 3):
            block[r][c] = 3

    collision = full_grid(7, 7, 0)
    collision[3][2] = 4
    collision[3][4] = 7

    touching_colors = full_grid(7, 7, 0)
    touching_colors[3][3] = 5
    touching_colors[3][4] = 8

    return [
        ("blank", blank),
        ("solid_component", solid),
        ("three_cell_component", triple),
        ("two_by_two_component", block),
        ("conflicting_plus_footprints", collision),
        ("different_colors_touching", touching_colors),
    ]
