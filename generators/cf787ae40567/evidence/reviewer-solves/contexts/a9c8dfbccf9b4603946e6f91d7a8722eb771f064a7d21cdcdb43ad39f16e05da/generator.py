"""Task-linked generator for ARC task cf787ae40567: plus-growth union size.

Every nonzero input cell is a seed. Grow each seed by one orthogonal step,
clip growth at the canvas boundary, take the set union of all grown cells, and
emit a one-row bar of color 8 whose width is the union cardinality.

A deterministic four-profile curriculum makes the two operations hidden by the
public examples observable:

* ``canonical``: public-like square canvases, interior non-overlapping color-2
  seeds. These retain the canonical task profile.
* ``overlap``: interior plus masks overlap exactly once, teaching set union
  rather than summing per-seed areas.
* ``edge``: at least one seed is on the boundary and no masks overlap, teaching
  clipping rather than a fixed five cells per seed.
* ``mixed``: contains both boundary clipping and exactly one mask overlap.

Every consecutive four sample indices contain all four profiles. Seed-root
rotation prevents a fixed pinned census from starving any one profile. The
ordinary sampler deliberately covers every count-bar width from 5 through 28,
the complete 24-state output codomain of this teaching distribution.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "cf787ae40567"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "5d3366b26415"
SUMMARY = (
    "Treat every nonzero cell as a seed, grow its clipped orthogonal plus mask, "
    "count cells in the union of all masks, and output one row of that many 8s."
)

INVARIANTS = [
    "background is 0 and seed color 8 is reserved for the output",
    "each nonzero input cell contributes its clipped center-plus-cardinal mask",
    "overlapping grown cells are counted once because masks are unioned",
    "the output is a single row of 8s whose width is the union cardinality",
    "the selected canonical Racket program remains output authority",
]

PROFILES = ("canonical", "overlap", "edge", "mixed")
SCHEDULE_PROFILES = PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# The generator's finite output alphabet is one solid 1xN bar for every
# N in 5..28. This declaration is about the teaching distribution, not a claim
# that the underlying rule cannot execute on other lawful seed configurations.
EXPECTED_OUTPUT_WIDTHS = tuple(range(5, 29))
EXPECTED_OUTPUT_CODOMAIN = len(EXPECTED_OUTPUT_WIDTHS)
PROFILE_WIDTHS = {
    "canonical": (5, 10, 15),
    "overlap": (8, 9, 13, 14, 18, 19, 23, 24),
    "edge": (6, 7, 11, 12, 16, 17, 20, 21, 22),
    "mixed": (25, 26, 27, 28),
}
assert set().union(*(set(values) for values in PROFILE_WIDTHS.values())) == set(
    EXPECTED_OUTPUT_WIDTHS
)
assert sum(len(values) for values in PROFILE_WIDTHS.values()) == EXPECTED_OUTPUT_CODOMAIN

AXES = {
    "profile": {
        "type": "str",
        "default": "sample_index plus mixed seed phase, mod 4",
        "valid": PROFILES,
        "probe": "diagnostic",
        "doc": (
            "Semantic lesson profile; every consecutive four-demo window covers "
            "canonical, overlap, edge-clipping, and mixed evidence."
        ),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[object, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]
Rival = Callable[[Sequence[Sequence[int]]], Grid]
PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
LEGAL_SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
CANONICAL_DIMS = {(7, 7), (8, 8), (9, 9)}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Every length-four window is complete; seed roots rotate the phase."""
    del difficulty
    seed_value = int(seed)
    phase = (seed_value ^ (seed_value >> 1)) & 3
    return PROFILES[(int(sample_index) + phase) % len(PROFILES)]


def _target_width(ctx, profile: str) -> int:
    widths = PROFILE_WIDTHS[profile]
    return int(widths[int(ctx.seed) % len(widths)])


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _seed_cells(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if int(value) != 0
    ]


def _plus_cells(height: int, width: int, point: Cell) -> set[Cell]:
    r, c = point
    return {
        (r + dr, c + dc)
        for dr, dc in PLUS
        if 0 <= r + dr < height and 0 <= c + dc < width
    }


def _union_cells(grid: Sequence[Sequence[int]]) -> set[Cell]:
    height, width = len(grid), len(grid[0])
    result: set[Cell] = set()
    for r, c, _ in _seed_cells(grid):
        result.update(_plus_cells(height, width, (r, c)))
    return result


def _overlap_pair_count(grid: Sequence[Sequence[int]]) -> int:
    height, width = len(grid), len(grid[0])
    points = [(r, c) for r, c, _ in _seed_cells(grid)]
    count = 0
    for index, first in enumerate(points):
        first_mask = _plus_cells(height, width, first)
        for second in points[index + 1 :]:
            count += bool(first_mask & _plus_cells(height, width, second))
    return count


def _edge_seed_count(grid: Sequence[Sequence[int]]) -> int:
    height, width = len(grid), len(grid[0])
    return sum(
        r in (0, height - 1) or c in (0, width - 1)
        for r, c, _ in _seed_cells(grid)
    )


def _profile_name(grid: Sequence[Sequence[int]]) -> str | None:
    seeds = _seed_cells(grid)
    if not seeds:
        return None
    height, width = len(grid), len(grid[0])
    count = len(seeds)
    colors = [value for _, _, value in seeds]
    edge_count = _edge_seed_count(grid)
    overlap_count = _overlap_pair_count(grid)

    if (
        (height, width) in CANONICAL_DIMS
        and 1 <= count <= 3
        and edge_count == 0
        and overlap_count == 0
        and set(colors) == {2}
    ):
        return "canonical"
    if (
        2 <= count <= 5
        and edge_count == 0
        and overlap_count == 1
        and len(set(colors)) == count
    ):
        return "overlap"
    if (
        2 <= count <= 5
        and edge_count >= 1
        and overlap_count == 0
        and len(set(colors)) == 1
    ):
        return "edge"
    if (
        3 <= count <= 6
        and edge_count >= 1
        and overlap_count == 1
        and len(set(colors)) == count
    ):
        return "mixed"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate exactly the canonical and four-profile teaching grammar."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not (5 <= height <= 14 and 5 <= width <= 14):
        errors.append(f"unsupported task canvas {(height, width)}")

    seeds = _seed_cells(grid)
    if not seeds:
        errors.append("expected at least one nonzero seed")
        return errors
    if len(seeds) > 6:
        errors.append(f"expected at most six seeds, found {len(seeds)}")
    if any(value == 8 for _, _, value in seeds):
        errors.append("input color 8 is reserved for the output bar")
    if len(_union_cells(grid)) > 30:
        errors.append("plus-mask union exceeds ARC output width 30")
    if _profile_name(grid) is None:
        errors.append(
            "input does not realize canonical, overlap, edge, or mixed teaching grammar"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All public inputs and ordinary generated inputs inhabit this grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    errors = _grid_errors(grid)
    if errors:
        return {}
    return {"profile": _profile_name(grid)}


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Python mirror for tests; the selected Racket rule is label authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [[8] * len(_union_cells(grid))]


def _empty_grid(height: int, width: int) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint_seeds(
    height: int,
    width: int,
    points: Sequence[Cell],
    colors: Sequence[int],
) -> Grid:
    if len(points) != len(colors):
        raise ValueError("points and colors must have equal length")
    grid = _empty_grid(height, width)
    for (r, c), color in zip(points, colors):
        if grid[r][c] != 0:
            raise AssertionError(f"duplicate seed position {(r, c)}")
        grid[r][c] = int(color)
    return grid


def _nonoverlapping(point: Cell, existing: Sequence[Cell]) -> bool:
    """Plus masks intersect exactly when distinct centers are within L1 distance 2."""
    return all(abs(point[0] - r) + abs(point[1] - c) > 2 for r, c in existing)


def _choose_separated(
    candidates: Sequence[Cell],
    count: int,
    rng,
    *,
    existing: Sequence[Cell] = (),
) -> list[Cell]:
    if count == 0:
        return []
    options = list(candidates)
    rng.shuffle(options)
    fixed = list(existing)

    def search(start: int, added: list[Cell]) -> list[Cell] | None:
        if len(added) == count:
            return list(added)
        for index in range(start, len(options)):
            point = options[index]
            if point in fixed or point in added:
                continue
            if not _nonoverlapping(point, [*fixed, *added]):
                continue
            added.append(point)
            result = search(index + 1, added)
            if result is not None:
                return result
            added.pop()
        return None

    result = search(0, [])
    if result is None:
        raise AssertionError(
            f"could not place {count} separated seeds with {len(existing)} fixed seeds"
        )
    return result


def _roomy_dims(ctx, profile: str, minimum: int, difficulty) -> tuple[int, int]:
    rng = ctx.draw_rng(f"{profile}_dims_{difficulty}")
    low = max(7, minimum)
    height = rng.randint(low, 14)
    width = rng.randint(low, 14)
    if height == width and rng.randrange(2):
        width = low if width != low else 14
    return height, width


def _contribution_candidates(height: int, width: int, contribution: int) -> list[Cell]:
    if contribution == 3:
        return [(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)]
    if contribution == 4:
        return [
            (r, c)
            for r in range(height)
            for c in range(width)
            if (r in (0, height - 1) or c in (0, width - 1))
            and (r, c)
            not in {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
        ]
    if contribution == 5:
        return [
            (r, c)
            for r in range(1, height - 1)
            for c in range(1, width - 1)
        ]
    raise ValueError(f"unsupported isolated-mask contribution: {contribution}")


def _place_by_contributions(
    height: int,
    width: int,
    contributions: Sequence[int],
    rng,
    *,
    existing: Sequence[Cell] = (),
) -> list[Cell]:
    requirements = sorted(contributions, key=lambda value: {3: 0, 4: 1, 5: 2}[value])
    option_rows: list[list[Cell]] = []
    for contribution in requirements:
        options = _contribution_candidates(height, width, contribution)
        rng.shuffle(options)
        option_rows.append(options)
    fixed = list(existing)

    def search(index: int, chosen: list[Cell]) -> list[Cell] | None:
        if index == len(requirements):
            return list(chosen)
        for point in option_rows[index]:
            if point in fixed or point in chosen:
                continue
            if not _nonoverlapping(point, [*fixed, *chosen]):
                continue
            chosen.append(point)
            result = search(index + 1, chosen)
            if result is not None:
                return result
            chosen.pop()
        return None

    result = search(0, [])
    if result is None:
        raise AssertionError(
            f"could not place isolated contributions {tuple(contributions)} "
            f"with {len(existing)} fixed seeds"
        )
    return result


def _canonical_grid(ctx, difficulty) -> Grid:
    target = _target_width(ctx, "canonical")
    count = target // 5
    rng = ctx.draw_rng(f"canonical_layout_{difficulty}_{target}")
    size = rng.choice((7, 8, 9))
    interior = [(r, c) for r in range(1, size - 1) for c in range(1, size - 1)]
    points = _choose_separated(interior, count, rng)
    return _paint_seeds(size, size, points, [2] * count)


def _overlap_grid(ctx, difficulty) -> Grid:
    target = _target_width(ctx, "overlap")
    if target % 5 == 3:
        overlap_loss = 2
        count = (target + 2) // 5
        distance = 1
    elif target % 5 == 4:
        overlap_loss = 1
        count = (target + 1) // 5
        distance = 2
    else:  # pragma: no cover - protected by PROFILE_WIDTHS
        raise AssertionError(f"unsupported overlap target {target}")

    height, width = _roomy_dims(ctx, "overlap", count + 6, difficulty)
    rng = ctx.draw_rng(f"overlap_layout_{difficulty}_{target}")
    interior = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)]
    pairs: list[tuple[Cell, Cell]] = []
    for r, c in interior:
        for dr, dc in ((0, distance), (distance, 0)):
            second = (r + dr, c + dc)
            if second in interior:
                pairs.append(((r, c), second))
    rng.shuffle(pairs)
    for first, second in pairs:
        try:
            extra = _choose_separated(
                interior,
                count - 2,
                rng,
                existing=(first, second),
            )
        except AssertionError:
            continue
        points = [first, second, *extra]
        colors = rng.sample(LEGAL_SEED_COLORS, count)
        grid = _paint_seeds(height, width, points, colors)
        if len(_union_cells(grid)) != target:
            continue
        if 5 * count - target != overlap_loss:
            continue
        return grid
    raise AssertionError(f"could not construct overlap profile of width {target}")


def _edge_contributions(target: int, rng) -> tuple[int, ...]:
    options = [
        values
        for count in range(2, 6)
        for values in product((3, 4, 5), repeat=count)
        if sum(values) == target and any(value < 5 for value in values)
    ]
    if not options:
        raise AssertionError(f"edge target {target} has no clipped-mask decomposition")
    return tuple(rng.choice(options))


def _edge_grid(ctx, difficulty) -> Grid:
    target = _target_width(ctx, "edge")
    rng = ctx.draw_rng(f"edge_layout_{difficulty}_{target}")
    contributions = _edge_contributions(target, rng)
    height, width = _roomy_dims(ctx, "edge", 11, difficulty)
    points = _place_by_contributions(height, width, contributions, rng)
    color = rng.choice(LEGAL_SEED_COLORS)
    grid = _paint_seeds(height, width, points, [color] * len(points))
    if len(_union_cells(grid)) != target:
        raise AssertionError(f"edge target {target} realized as {len(_union_cells(grid))}")
    return grid


def _mixed_grid(ctx, difficulty) -> Grid:
    target = _target_width(ctx, "mixed")
    distance, contributions = {
        25: (1, (3, 5, 5, 5)),
        26: (1, (4, 5, 5, 5)),
        27: (1, (5, 5, 5, 5)),
        28: (2, (5, 5, 5, 5)),
    }[target]
    height, width = _roomy_dims(ctx, "mixed", 12, difficulty)
    rng = ctx.draw_rng(f"mixed_layout_{difficulty}_{target}")

    pairs: list[tuple[Cell, Cell]] = []
    for c in range(2, width - 2):
        pairs.append(((0, c), (distance, c)))
        pairs.append(((height - 1, c), (height - 1 - distance, c)))
    for r in range(2, height - 2):
        pairs.append(((r, 0), (r, distance)))
        pairs.append(((r, width - 1), (r, width - 1 - distance)))
    rng.shuffle(pairs)

    for edge_point, partner in pairs:
        try:
            extra = _place_by_contributions(
                height,
                width,
                contributions,
                rng,
                existing=(edge_point, partner),
            )
        except AssertionError:
            continue
        points = [edge_point, partner, *extra]
        colors = rng.sample(LEGAL_SEED_COLORS, len(points))
        grid = _paint_seeds(height, width, points, colors)
        if len(_union_cells(grid)) == target:
            return grid
    raise AssertionError(f"could not construct mixed profile of width {target}")


_BUILDERS = {
    "canonical": _canonical_grid,
    "overlap": _overlap_grid,
    "edge": _edge_grid,
    "mixed": _mixed_grid,
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    choices = PROFILES if overrides.get("profile") is not None else (scheduled,)
    profile = str(ctx.draw_choice("profile", choices))
    grid = _BUILDERS[profile](ctx, difficulty)
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"constructed invalid {profile} scene: {errors}")
    observed = observe_overrides(grid).get("profile")
    if observed != profile:
        raise AssertionError(f"profile {profile!r} realized as {observed!r}")
    target = _target_width(ctx, profile)
    realized = len(_union_cells(grid))
    if realized != target:
        raise AssertionError(f"profile {profile!r} target {target} realized as {realized}")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Executable rivals and semantic contract.
# ---------------------------------------------------------------------------


def _five_per_seed(grid: Sequence[Sequence[int]]) -> Grid:
    return [[8] * (5 * len(_seed_cells(grid)))]


def _clipped_sum_without_union(grid: Sequence[Sequence[int]]) -> Grid:
    height, width = len(grid), len(grid[0])
    count = sum(
        len(_plus_cells(height, width, (r, c)))
        for r, c, _ in _seed_cells(grid)
    )
    return [[8] * count]


CANONICAL_SHORTCUTS: dict[str, Rival] = {
    "five_per_seed": _five_per_seed,
    "clipped_sum_without_union": _clipped_sum_without_union,
}
SEMANTIC_RIVALS: dict[str, Rival] = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS: dict[str, Rival] = dict(SEMANTIC_RIVALS)


def _disagrees(grid: Sequence[Sequence[int]], rival_name: str) -> bool:
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "edge_clipping": lambda grid: (
        not self_check(grid)
        and observe_overrides(grid).get("profile") in {"edge", "mixed"}
        and _disagrees(grid, "five_per_seed")
    ),
    "overlap_deduplication": lambda grid: (
        not self_check(grid)
        and observe_overrides(grid).get("profile") in {"overlap", "mixed"}
        and _disagrees(grid, "five_per_seed")
        and _disagrees(grid, "clipped_sum_without_union")
    ),
}

WITNESS_RIVALS = {
    "edge_clipping": ["five_per_seed"],
    "overlap_deduplication": ["five_per_seed", "clipped_sum_without_union"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check the finite named rival registry; this is not universal induction."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, item in enumerate(demos):
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(item["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
        elif rule_mirror(item["input"]) != item["output"]:
            reasons.append(f"demo {index} output does not match the selected rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the selected rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(item["input"]) == item["output"] for item in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons
