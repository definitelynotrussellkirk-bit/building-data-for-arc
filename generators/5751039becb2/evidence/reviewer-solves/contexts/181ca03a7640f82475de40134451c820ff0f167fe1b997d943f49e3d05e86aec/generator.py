"""Input sampler for ARC task 5751039becb2: diagonal-neighbour selection.

The selected Racket rule keeps a nonzero cell exactly when one of its four
DIAGONAL neighbours has the same color.  This sampler deliberately alternates
canonical-style examples with two minimal counterexample families:

* a remote singleton reusing a surviving color, which refutes global color-
  frequency and "keep the whole color if any pair exists" shortcuts;
* a same-color cardinal pair, which refutes "any 8-neighbour" and global
  repetition shortcuts.

Outputs are never generated here; ``rule_mirror`` is an executable review
oracle and the canonical Racket program remains authoritative.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5751039becb2"
TASK_ID = GENERATOR_ID
RULE_HASH = "8626f391dcea"
VERSION = "3.0.0"

SUMMARY = (
    "Sparse 0-background grids teach a local diagonal relation.  Every lawful "
    "input has at least one three-cell diagonal chain and remaining two- or "
    "three-cell diagonal components in distinct colors, with a contrastive "
    "erased pattern.  A four-slot schedule "
    "cycles canonical singleton, remote same-color singleton, cardinal same-"
    "color pair, and their combination; every three-demo window refutes the "
    "declared global-frequency and 8-neighbour shortcuts."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

PROFILES = (
    "canonical",
    "shared_color_singleton",
    "orthogonal_repeat",
    "combined",
)
SCHEDULE_PROFILES = PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical/rich value",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical/rich value",
        "valid": "7..12",
    },
    "n_survivor_groups": {
        "type": "int",
        "default": "3; combined slot scales 2..4 by difficulty",
        "valid": "2..4",
    },
    "profile": {
        "type": "str",
        "default": "four-slot teaching schedule",
        "valid": "|".join(PROFILES),
    },
}

# The full Cartesian product is constructive, including 6x7 / four groups /
# combined decoys.  Keep this declaration explicit so the override checker uses
# strict incompatibility accounting rather than the legacy compatibility mode.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "background is 0 and colors are ARC integers 0..9",
    "survivor components are same-color diagonal chains of length 2 or 3, with at least one length-3 chain",
    "at least one nonzero cell is erased by the selected rule",
    "profile schedule supplies global-color and cardinal-neighbour counterexamples",
]

_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = _DIAGONALS + _CARDINALS
_VALID_BANDS = {None, "easy", "medium", "hard"}
_CANONICAL_DIMS = ((6, 7), (7, 8))

Grid = list[list[int]]
Point = tuple[int, int]


def _band(difficulty: Any) -> str:
    if difficulty not in _VALID_BANDS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return "medium" if difficulty is None else difficulty


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "n_survivor_groups"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if "profile" in overrides and overrides["profile"] is not None:
        value = overrides["profile"]
        if type(value) is not str:
            raise ValueError(f"profile must be a string, not {type(value).__name__}")
    return band


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the exact four-position curriculum to source-bound gates."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    """Record a deterministic default while retaining the full override range."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(
    ctx, label: str, options: Sequence[str], scheduled: str
) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(ctx, profile: str, band: str) -> tuple[int, int, int]:
    sample_index = int(ctx.sample_index)
    if profile == "canonical":
        h, w = _CANONICAL_DIMS[(sample_index // len(PROFILES)) % 2]
        return h, w, 3
    if profile == "shared_color_singleton":
        return 7, 8, 3
    if profile == "orthogonal_repeat":
        return 6, 7, 3

    # The combined slot carries scale breadth while the other three slots keep
    # exact canonical profiles in every band.  Values are chosen before the
    # exact-axis draws, so there is no post-draw clipping or silent fallback.
    ranges = {
        "easy": ((6, 8), (7, 9), 2),
        "medium": ((7, 9), (8, 10), 3),
        "hard": ((8, 10), (10, 12), 4),
    }
    (h_lo, h_hi), (w_lo, w_hi), groups = ranges[band]
    h = ctx.draw_rng("combined_default_h").randint(h_lo, h_hi)
    w = ctx.draw_rng("combined_default_w").randint(w_lo, w_hi)
    return h, w, groups


def _chain_candidates(h: int, w: int) -> list[tuple[Point, Point, Point]]:
    candidates: list[tuple[Point, Point, Point]] = []
    for r in range(h - 2):
        for c in range(w):
            for dc in (-1, 1):
                c1, c2 = c + dc, c + 2 * dc
                if 0 <= c1 < w and 0 <= c2 < w:
                    candidates.append(((r, c), (r + 1, c1), (r + 2, c2)))
    return candidates


def _pair_candidates(h: int, w: int) -> list[tuple[Point, Point]]:
    return [
        ((r, c), (r + 1, c + dc))
        for r in range(h - 1)
        for c in range(w)
        for dc in (-1, 1)
        if 0 <= c + dc < w
    ]


def _choose_disjoint_pairs(
    candidates: Sequence[tuple[Point, Point]],
    occupied: set[Point],
    needed: int,
    start: int = 0,
) -> list[tuple[Point, Point]] | None:
    if needed == 0:
        return []
    for index in range(start, len(candidates)):
        pair = candidates[index]
        cells = set(pair)
        if cells & occupied:
            continue
        rest = _choose_disjoint_pairs(
            candidates, occupied | cells, needed - 1, index + 1
        )
        if rest is not None:
            return [pair, *rest]
    return None


def _survivor_groups(h: int, w: int, count: int, rng) -> list[tuple[Point, ...]]:
    chains = _chain_candidates(h, w)
    pairs = _pair_candidates(h, w)
    rng.shuffle(chains)
    rng.shuffle(pairs)
    for chain in chains:
        selected = _choose_disjoint_pairs(pairs, set(chain), count - 1)
        if selected is not None:
            return [tuple(chain), *(tuple(pair) for pair in selected)]
    raise RuntimeError(
        f"no constructive survivor layout for {h}x{w} with {count} groups"
    )


def _empty_cells(grid: Grid) -> list[Point]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    ]


def _choose_empty(grid: Grid, rng, *, allowed: Callable[[Point], bool] | None = None) -> Point:
    candidates = _empty_cells(grid)
    if allowed is not None:
        candidates = [point for point in candidates if allowed(point)]
    if not candidates:
        raise RuntimeError("constructive scene has no eligible empty cell")
    return rng.choice(candidates)


def _choose_cardinal_pair(grid: Grid, rng) -> tuple[Point, Point]:
    h, w = len(grid), len(grid[0])
    pairs: list[tuple[Point, Point]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0:
                    pairs.append(((r, c), (rr, cc)))
    if not pairs:
        raise RuntimeError("constructive scene has no empty cardinal pair")
    return rng.choice(pairs)


def _build_grid(
    h: int,
    w: int,
    n_survivor_groups: int,
    profile: str,
    ctx,
) -> Grid:
    grid = full_grid(h, w, 0)
    layout_rng = ctx.draw_rng("survivor_layout")
    groups = _survivor_groups(h, w, n_survivor_groups, layout_rng)
    colors = ctx.draw_rng("palette").sample(range(1, 10), n_survivor_groups + 1)
    survivor_colors, decoy_color = colors[:-1], colors[-1]
    for cells, color in zip(groups, survivor_colors):
        for r, c in cells:
            grid[r][c] = color

    decoy_rng = ctx.draw_rng("decoy_layout")
    if profile in ("orthogonal_repeat", "combined"):
        for r, c in _choose_cardinal_pair(grid, decoy_rng):
            grid[r][c] = decoy_color

    if profile in ("shared_color_singleton", "combined"):
        group_index = ctx.draw_rng("shared_color_group").randrange(n_survivor_groups)
        shared_color = survivor_colors[group_index]
        same_color_cells = groups[group_index]

        def remote(point: Point) -> bool:
            # Deliberately exclude all 8-neighbour contact.  The decoy therefore
            # isolates global-color evidence from the separate 8-neighbour trap.
            return all(
                max(abs(point[0] - r), abs(point[1] - c)) > 1
                for r, c in same_color_cells
            )

        r, c = _choose_empty(grid, decoy_rng, allowed=remote)
        grid[r][c] = shared_color

    if profile in ("canonical", "shared_color_singleton"):
        r, c = _choose_empty(grid, decoy_rng)
        grid[r][c] = decoy_color

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _draw_scheduled_choice(
        ctx,
        "profile",
        PROFILES,
        schedule_profile(seed, sample_index, band),
    )
    default_h, default_w, default_groups = _scheduled_defaults(ctx, profile, band)
    h = _draw_scheduled_int(ctx, "grid_h", 6, 10, default_h)
    w = _draw_scheduled_int(ctx, "grid_w", 7, 12, default_w)
    n_groups = _draw_scheduled_int(
        ctx, "n_survivor_groups", 2, 4, default_groups
    )
    grid = _build_grid(h, w, n_groups, profile, ctx)

    # Assert the exact contract at the source boundary.  This is not a fallback:
    # any mismatch is a loud implementation defect rather than a clamped axis.
    observed = observe_overrides(grid)
    for name in AXES:
        if observed[name] != ctx.axis_value(name):
            raise RuntimeError(
                f"axis {name!r} recorded {ctx.axis_value(name)!r} but grid "
                f"realizes {observed[name]!r}"
            )
    return grid


def _rectangular_grid(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python transcription of the selected local rule."""
    shape = _rectangular_grid(grid)
    if shape is None:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = shape
    output = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] == value
                for dr, dc in _DIAGONALS
            ):
                output[r][c] = value
    return output


def _diagonal_components(grid: Sequence[Sequence[int]], points: set[Point]) -> list[set[Point]]:
    unseen = set(points)
    components: list[set[Point]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = [start]
        while queue:
            r, c = queue.pop()
            value = grid[r][c]
            for dr, dc in _DIAGONALS:
                neighbour = (r + dr, c + dc)
                if neighbour in unseen and grid[neighbour[0]][neighbour[1]] == value:
                    unseen.remove(neighbour)
                    component.add(neighbour)
                    queue.append(neighbour)
        components.append(component)
    return components


def _classify_profile(
    grid: Sequence[Sequence[int]],
    survivors: set[Point],
    decoys: set[Point],
) -> str | None:
    survivor_colors = {grid[r][c] for r, c in survivors}
    shared = {(r, c) for r, c in decoys if grid[r][c] in survivor_colors}
    new = decoys - shared
    orthogonal_pairs = {
        frozenset(((r, c), (r + dr, c + dc)))
        for r, c in new
        for dr, dc in _CARDINALS
        if (r + dr, c + dc) in new
        and grid[r + dr][c + dc] == grid[r][c]
    }
    if len(decoys) == 1 and not shared and not orthogonal_pairs:
        return "canonical"
    if len(decoys) == 2 and len(shared) == 1 and len(new) == 1 and not orthogonal_pairs:
        return "shared_color_singleton"
    if (
        len(decoys) == 2
        and not shared
        and len(new) == 2
        and len(orthogonal_pairs) == 1
        and len({grid[r][c] for r, c in new}) == 1
    ):
        return "orthogonal_repeat"
    if (
        len(decoys) == 3
        and len(shared) == 1
        and len(new) == 2
        and len(orthogonal_pairs) == 1
        and len({grid[r][c] for r, c in new}) == 1
    ):
        return "combined"
    return None


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    shape = _rectangular_grid(grid)
    if shape is None:
        return {}, ["expected a nonempty rectangular grid"]
    h, w = shape
    errors: list[str] = []
    if not (6 <= h <= 10 and 7 <= w <= 12):
        errors.append(f"grid dimensions {h}x{w} outside 6..10 by 7..12")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (booleans are invalid)")
        return {}, errors

    output = rule_mirror(grid)
    nonzero = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    survivors = {(r, c) for r, c in nonzero if output[r][c] != 0}
    decoys = nonzero - survivors
    if not survivors:
        errors.append("rule output is empty; at least two survivor groups are required")
    if not decoys:
        errors.append("input has no erased contrast cell")

    components = _diagonal_components(grid, survivors)
    component_sizes = sorted(len(component) for component in components)
    n_groups = len(components)
    if not 2 <= n_groups <= 4:
        errors.append(f"survivor group count {n_groups} outside 2..4")
    if not component_sizes or any(size not in (2, 3) for size in component_sizes) or 3 not in component_sizes:
        errors.append(
            "survivors must be same-color diagonal components of length 2 or 3 "
            f"with at least one length-3 chain; observed {component_sizes}"
        )
    survivor_component_colors = [
        {grid[r][c] for r, c in component} for component in components
    ]
    if any(len(colors) != 1 for colors in survivor_component_colors):
        errors.append("every survivor component must use one color")
    flat_survivor_colors = [next(iter(colors)) for colors in survivor_component_colors if colors]
    if len(flat_survivor_colors) != len(set(flat_survivor_colors)):
        errors.append("survivor groups must use distinct colors")

    profile = _classify_profile(grid, survivors, decoys)
    if profile is None:
        errors.append("erased cells do not realize one declared teaching profile")

    info = {
        "grid_h": h,
        "grid_w": w,
        "n_survivor_groups": n_groups,
        "profile": profile,
        "output": output,
        "survivors": survivors,
        "decoys": decoys,
        "component_sizes": component_sizes,
    }
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every advertised exact control from returned pixels."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected teaching grammar without consulting RNG metadata."""
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid):
    """All generated inputs and canonical examples belong to this strict grammar."""
    return self_check(grid)


# ---- executable shortcut and teaching contracts ---------------------------

def _color_counts(grid: Sequence[Sequence[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value != 0)


def _rival_keep_repeated_colors(grid: Sequence[Sequence[int]]) -> Grid:
    counts = _color_counts(grid)
    return [
        [value if value != 0 and counts[value] >= 2 else 0 for value in row]
        for row in grid
    ]


def _rival_keep_color_if_any_diagonal_pair(grid: Sequence[Sequence[int]]) -> Grid:
    true = rule_mirror(grid)
    qualifying = {
        grid[r][c]
        for r, row in enumerate(true)
        for c, value in enumerate(row)
        if value != 0
    }
    return [
        [value if value != 0 and value in qualifying else 0 for value in row]
        for row in grid
    ]


def _rival_any_eight_neighbor(grid: Sequence[Sequence[int]]) -> Grid:
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value != 0 and any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] == value
                for dr, dc in _EIGHT
            ):
                output[r][c] = value
    return output


def _rival_exactly_two_occurrences(grid: Sequence[Sequence[int]]) -> Grid:
    counts = _color_counts(grid)
    return [
        [value if value != 0 and counts[value] == 2 else 0 for value in row]
        for row in grid
    ]


SEMANTIC_RIVALS = {
    "keep_repeated_colors": _rival_keep_repeated_colors,
    "keep_whole_color_if_any_diagonal_pair": _rival_keep_color_if_any_diagonal_pair,
    "keep_any_same_color_8_neighbor": _rival_any_eight_neighbor,
    "keep_exactly_two_occurrences": _rival_exactly_two_occurrences,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "keep_repeated_colors",
        "keep_whole_color_if_any_diagonal_pair",
        "keep_any_same_color_8_neighbor",
    )
}


def _has_profile(grid: Any, *profiles: str) -> bool:
    try:
        return observe_overrides(grid)["profile"] in profiles
    except (TypeError, ValueError):
        return False


def _has_three_cell_chain(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and 3 in info["component_sizes"]


SEMANTIC_WITNESSES = {
    "same_color_isolated_decoy": lambda grid: _has_profile(
        grid, "shared_color_singleton", "combined"
    ),
    "orthogonal_same_color_decoy": lambda grid: _has_profile(
        grid, "orthogonal_repeat", "combined"
    ),
    "three_cell_diagonal_chain": _has_three_cell_chain,
}
WITNESS_RIVALS = {
    "same_color_isolated_decoy": [
        "keep_repeated_colors",
        "keep_whole_color_if_any_diagonal_pair",
    ],
    "orthogonal_same_color_decoy": [
        "keep_repeated_colors",
        "keep_any_same_color_8_neighbor",
    ],
    "three_cell_diagonal_chain": ["keep_exactly_two_occurrences"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named competitor to be refuted by three demonstrations."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demos, got {len(demos)}")
        return reasons
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} lacks input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} outside teaching grammar: {errors}")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with selected rule")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query lacks input")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query outside teaching grammar: {errors}")
        if "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with selected rule")

    for name, rival in LESSON_COMPETITORS.items():
        if not any(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) != pair["output"]
            for pair in demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
