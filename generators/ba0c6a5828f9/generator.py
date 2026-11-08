"""Teaching generator for ARC task ba0c6a5828f9.

The selected rule is unchanged: find the unique red (2) pivot and, for every
blue (1) marker, paint every in-bounds member of its four-quarter-turn orbit.
Out-of-bounds orbit members are skipped.

The public examples leave two tempting shortcuts observationally equivalent to
the rule: rotating around the geometric canvas center instead of the red pivot,
and discarding a marker whenever any member of its orbit is out of bounds.  A
deterministic four-profile curriculum makes both hidden branches executable:

* ``canonical``: centered 7x7/9x9 public-like scenes with complete orbits;
* ``off_center``: the red pivot is not the geometric center, with no clipping;
* ``clipped``: a centered pivot plus an orbit that is partially out of bounds;
* ``mixed``: an off-center pivot and a partially clipped orbit.

Every consecutive four sample indices contain all four profiles.  Any three of
those four examples refute both named shortcuts, so a three-demo lesson plus a
query remains identifiable under every rotation of the query position.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "ba0c6a5828f9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e28fcc7b8767"
SUMMARY = (
    "Use the unique red cell as a rotation pivot. For every blue marker, paint "
    "all in-bounds 0°, 90°, 180°, and 270° rotation images; clipped images are "
    "skipped and the red pivot remains red."
)

INVARIANTS = [
    "exactly one color-2 pivot and two to five color-1 source markers",
    "the color-2 cell, not the canvas center, is the rotation pivot",
    "each marker contributes every in-bounds member of its quarter-turn orbit",
    "out-of-bounds orbit members are skipped rather than invalidating the orbit",
    "the selected canonical Racket program remains output authority",
]

PROFILES = ("canonical", "off_center", "clipped", "mixed")
SCHEDULE_PROFILES = PROFILES
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "profile": {
        "type": "str",
        "default": "sample_index plus mixed seed phase, mod 4",
        "valid": PROFILES,
        "probe": "diagnostic",
        "doc": (
            "Semantic lesson profile. Every consecutive four-pair window "
            "covers canonical, off-center-pivot, clipped-orbit, and mixed evidence."
        ),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[object, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]
Orbit = tuple[Cell, ...]
Rival = Callable[[Sequence[Sequence[int]]], Grid]
CANONICAL_DIMS = ((7, 7), (9, 9))
BAND_DIMS = {
    None: (7, 14),
    "easy": (7, 10),
    "medium": (8, 12),
    "hard": (10, 14),
}
MARKER_LIMITS = {
    None: (2, 5),
    "easy": (2, 3),
    "medium": (2, 4),
    "hard": (3, 5),
}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return a complete four-profile schedule with a deterministic seed phase."""
    del difficulty
    seed_value = int(seed)
    phase = (seed_value ^ (seed_value >> 1)) & 3
    return PROFILES[(int(sample_index) + phase) % len(PROFILES)]


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
            if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1, 2):
                return ["cells must be literal ARC integers 0, 1, or 2"]
    return []


def _pivot_cells(grid: Sequence[Sequence[int]]) -> list[Cell]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]


def _marker_cells(grid: Sequence[Sequence[int]]) -> list[Cell]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]


def _orbit_all(point: Cell, center: Cell) -> Orbit:
    r, c = point
    pr, pc = center
    dr, dc = r - pr, c - pc
    return (
        (pr + dr, pc + dc),
        (pr + dc, pc - dr),
        (pr - dr, pc - dc),
        (pr - dc, pc + dr),
    )


def _in_bounds(point: Cell, height: int, width: int) -> bool:
    return 0 <= point[0] < height and 0 <= point[1] < width


def _apply_rule(
    grid: Sequence[Sequence[int]],
    *,
    center: Cell | None = None,
    require_full_orbit: bool = False,
) -> Grid:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    pivots = _pivot_cells(grid)
    if len(pivots) != 1:
        raise ValueError(f"expected exactly one color-2 pivot, found {len(pivots)}")

    height, width = len(grid), len(grid[0])
    actual_center = pivots[0] if center is None else center
    result = [list(row) for row in grid]
    for marker in _marker_cells(grid):
        orbit = _orbit_all(marker, actual_center)
        if require_full_orbit and any(
            not _in_bounds(point, height, width) for point in orbit
        ):
            continue
        for r, c in orbit:
            if 0 <= r < height and 0 <= c < width:
                result[r][c] = 1
    return result


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Pure Python mirror for tests; selected Racket source is label authority."""
    return _apply_rule(grid)


def _geometric_center_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return _apply_rule(grid, center=(len(grid) // 2, len(grid[0]) // 2))


def _full_orbits_only_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return _apply_rule(grid, require_full_orbit=True)


def _has_clipped_marker(grid: Sequence[Sequence[int]]) -> bool:
    pivots = _pivot_cells(grid)
    if len(pivots) != 1:
        return False
    height, width = len(grid), len(grid[0])
    center = pivots[0]
    return any(
        any(not _in_bounds(point, height, width) for point in _orbit_all(marker, center))
        for marker in _marker_cells(grid)
    )


def _profile_name(grid: Sequence[Sequence[int]]) -> str | None:
    errors = _grid_errors(grid)
    if errors:
        return None
    pivots = _pivot_cells(grid)
    if len(pivots) != 1:
        return None
    height, width = len(grid), len(grid[0])
    marker_count = len(_marker_cells(grid))
    center = pivots[0]
    off_center = center != (height // 2, width // 2)
    clipped = _has_clipped_marker(grid)
    if off_center and clipped:
        return "mixed"
    if off_center:
        return "off_center"
    if clipped:
        return "clipped"
    if (height, width) in CANONICAL_DIMS and 2 <= marker_count <= 3:
        return "canonical"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate exactly the public grammar and four-profile teaching manifold."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not (7 <= height <= 14 and 7 <= width <= 14):
        errors.append(f"unsupported task canvas {(height, width)}")

    pivots = _pivot_cells(grid)
    markers = _marker_cells(grid)
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-2 pivot, found {len(pivots)}")
    if not (2 <= len(markers) <= 5):
        errors.append(f"expected two to five color-1 markers, found {len(markers)}")
    if errors:
        return errors

    profile = _profile_name(grid)
    if profile is None:
        errors.append(
            "input does not realize canonical, off_center, clipped, or mixed teaching grammar"
        )
        return errors
    if rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("selected rule would leave the input unchanged")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All public and generated inputs inhabit this declared task grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    if _grid_errors(grid):
        return {}
    return {"profile": _profile_name(grid)}


@lru_cache(maxsize=None)
def _orbit_groups(height: int, width: int, center: Cell) -> tuple[tuple[Orbit, ...], tuple[Orbit, ...]]:
    """Return complete and useful partial orbit groups as in-bounds members."""
    seen: set[tuple[Cell, ...]] = set()
    complete: list[Orbit] = []
    partial: list[Orbit] = []
    for r in range(height):
        for c in range(width):
            if (r, c) == center:
                continue
            full_key = tuple(sorted(_orbit_all((r, c), center)))
            if full_key in seen:
                continue
            seen.add(full_key)
            members = tuple(point for point in full_key if _in_bounds(point, height, width))
            if len(members) == 4:
                complete.append(members)
            elif 2 <= len(members) < 4:
                partial.append(members)
    return tuple(complete), tuple(partial)


def _shape_options(profile: str, difficulty) -> tuple[tuple[int, int], ...]:
    if profile == "canonical":
        return CANONICAL_DIMS
    low, high = BAND_DIMS[difficulty]
    return tuple((height, width) for height in range(low, high + 1) for width in range(low, high + 1))


@lru_cache(maxsize=None)
def _feasible_pivots(
    height: int,
    width: int,
    profile: str,
    marker_count: int,
) -> tuple[Cell, ...]:
    geometric_center = (height // 2, width // 2)
    if profile in ("canonical", "clipped"):
        candidates = (geometric_center,)
    else:
        candidates = tuple(
            (r, c)
            for r in range(1, height - 1)
            for c in range(1, width - 1)
            if (r, c) != geometric_center
        )

    feasible: list[Cell] = []
    for center in candidates:
        complete, partial = _orbit_groups(height, width, center)
        if profile in ("canonical", "off_center"):
            ok = len(complete) >= marker_count
        else:
            ok = bool(partial) and len(complete) >= marker_count - 1
        if ok:
            feasible.append(center)
    return tuple(feasible)


def _empty_grid(height: int, width: int) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint_scene(height: int, width: int, center: Cell, sources: Sequence[Cell]) -> Grid:
    grid = _empty_grid(height, width)
    grid[center[0]][center[1]] = 2
    for r, c in sources:
        if grid[r][c] != 0:
            raise AssertionError(f"duplicate source position {(r, c)}")
        grid[r][c] = 1
    return grid


def _profile_relationships_hold(profile: str, grid: Grid) -> bool:
    intended = rule_mirror(grid)
    center_rival = _geometric_center_rival(grid)
    clipping_rival = _full_orbits_only_rival(grid)
    if intended == grid:
        return False
    expected = {
        "canonical": (True, True),
        "off_center": (False, True),
        "clipped": (True, False),
        "mixed": (False, False),
    }[profile]
    return (center_rival == intended, clipping_rival == intended) == expected


def _construct_profile(ctx, profile: str, difficulty) -> Grid:
    rng = ctx.draw_rng(f"{profile}_layout_{difficulty or 'default'}")
    low_count, high_count = MARKER_LIMITS[difficulty]
    if profile == "canonical":
        high_count = min(high_count, 3)
    marker_count = rng.randint(low_count, high_count)

    shapes = list(_shape_options(profile, difficulty))
    rng.shuffle(shapes)
    for height, width in shapes:
        pivots = list(_feasible_pivots(height, width, profile, marker_count))
        rng.shuffle(pivots)
        for center in pivots:
            complete, partial = _orbit_groups(height, width, center)
            for _ in range(24):
                if profile in ("canonical", "off_center"):
                    chosen_groups = list(rng.sample(complete, marker_count))
                else:
                    chosen_groups = [rng.choice(partial)]
                    chosen_groups.extend(rng.sample(complete, marker_count - 1))
                sources = [rng.choice(group) for group in chosen_groups]
                grid = _paint_scene(height, width, center, sources)
                if _profile_name(grid) != profile:
                    continue
                if _profile_relationships_hold(profile, grid):
                    return grid
    raise AssertionError(
        f"could not construct profile={profile!r}, difficulty={difficulty!r}, "
        f"marker_count={marker_count}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    """Generate one deterministic task-linked input grid.

    ``profile`` is the only supported override. Unknown keys and non-exact
    profile values are rejected before any sampling occurs.
    """
    if difficulty not in BAND_DIMS:
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    if "profile" in overrides and overrides["profile"] not in PROFILES:
        raise ValueError(
            f"profile override must be one of {PROFILES}, got {overrides['profile']!r}"
        )

    effective_overrides = dict(overrides)
    effective_overrides.setdefault(
        "profile", schedule_profile(seed, sample_index, difficulty)
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("profile", PROFILES)
    grid = _construct_profile(ctx, profile, difficulty)
    findings = self_check(grid)
    if findings:
        raise AssertionError(f"constructed invalid {profile} scene: {findings}")
    if observe_overrides(grid) != {"profile": profile}:
        raise AssertionError(f"constructed scene does not expose requested profile {profile!r}")
    return grid


def _off_center_witness(grid: Sequence[Sequence[int]]) -> bool:
    return _profile_name(grid) in ("off_center", "mixed")


def _edge_clipping_witness(grid: Sequence[Sequence[int]]) -> bool:
    return _profile_name(grid) in ("clipped", "mixed")


CANONICAL_SHORTCUTS: dict[str, Rival] = {
    "geometric_center": _geometric_center_rival,
    "full_orbits_only": _full_orbits_only_rival,
}
SEMANTIC_RIVALS: dict[str, Rival] = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS: dict[str, Rival] = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "off_center_pivot": _off_center_witness,
    "edge_clipping": _edge_clipping_witness,
}
WITNESS_RIVALS = {
    "off_center_pivot": ["geometric_center"],
    "edge_clipping": ["full_orbits_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave either named shortcut alive."""
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence"]
    if len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, item in enumerate(demos):
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        findings = strict_canonical_like(item["input"])
        if findings:
            reasons.append(
                f"demo {index} input is outside the teaching grammar: {findings[0]}"
            )
        elif rule_mirror(item["input"]) != item["output"]:
            reasons.append(f"demo {index} output does not match the selected rule")

    query_findings = strict_canonical_like(query["input"])
    if query_findings:
        reasons.append(
            f"query input is outside the teaching grammar: {query_findings[0]}"
        )
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the selected rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(item["input"]) == item["output"] for item in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons
