"""Generator for 3adf11522bf5 — mark selected all-zero square regions.

The selected Racket rule computes the largest all-zero square beginning at each
cell.  It paints the union of every globally largest square with color 1, then
also paints every all-zero square of side >= 2 that is completely disjoint from
that maximal union.  Nonzero obstacle cells are preserved.

This sampler deliberately alternates canonical-profile scenes (largest side 2)
with teaching scenes (largest side 3).  Teaching scenes contain concrete
counterexamples to four tempting shortcuts: largest-squares-only, paint every
square cell, use only the first largest square, and assume obstacle color 5.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3adf11522bf5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a18583a5c8f2"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find every globally largest all-zero square and paint their union color 1. "
    "Also paint cells belonging to any side>=2 all-zero square whose entire "
    "footprint is disjoint from that maximal union. Preserve the single "
    "nonzero obstacle color."
)

INVARIANTS = [
    "input is a 7..16 by 8..18 rectangular ARC grid",
    "background is 0 and all obstacles use exactly one color from 2..9",
    "obstacle density is 30%..50%",
    "the largest all-zero square has side 2 or 3",
    "scheduled teaching scenes refute all declared semantic rivals",
]

SCENE_PROFILES = ("canonical2", "teaching")
SCHEDULE_PROFILES = SCENE_PROFILES
_OBSTACLE_COLORS = tuple(range(2, 10))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "20-slot shape schedule; 10x10 every fourth slot",
        "valid": "7..16",
        "doc": "Observable input height. Every value is valid in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "20-slot shape schedule; 10x10 every fourth slot",
        "valid": "8..18",
        "doc": "Observable input width. Every value is valid in every difficulty band.",
    },
    "obstacle_color": {
        "type": "int",
        "default": "cyclic 2..9 schedule",
        "valid": "2..9",
        "doc": "The one nonzero input color.",
    },
    "scene_profile": {
        "type": "str",
        "default": "canonical2 once per four samples; teaching otherwise",
        "valid": "canonical2|teaching",
        "doc": "canonical2 has global maximum side 2; teaching has side 3 and rival witnesses.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Five canonical-profile slots plus fifteen distinct broad shapes.  A rotation
# per difficulty changes ordering, not support, so every band retains the full
# override domain and strong 10x10 support.
_SHAPE_SCHEDULE = (
    (10, 10), (7, 8), (8, 9), (9, 11),
    (10, 10), (11, 12), (12, 13), (13, 14),
    (10, 10), (14, 15), (15, 16), (16, 18),
    (10, 10), (7, 18), (16, 8), (8, 17),
    (10, 10), (15, 9), (9, 16), (12, 10),
)
_DIFFICULTY_ROTATION = {None: 0, "easy": 0, "medium": 5, "hard": 10}


@dataclass(frozen=True)
class _SquareFacts:
    max_side: int
    maximal_origins: tuple[tuple[int, int], ...]
    maximal_cells: frozenset[tuple[int, int]]
    disjoint_smaller_cells: frozenset[tuple[int, int]]
    all_square_cells: frozenset[tuple[int, int]]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose a cadence in which every four consecutive samples teach the rule."""
    del seed, difficulty
    return "canonical2" if int(sample_index) % 4 == 0 else "teaching"


def _scheduled_shape(sample_index: int, difficulty: Any) -> tuple[int, int]:
    offset = _DIFFICULTY_ROTATION[difficulty]
    return _SHAPE_SCHEDULE[(int(sample_index) + offset) % len(_SHAPE_SCHEDULE)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    for name in ("grid_h", "grid_w", "obstacle_color"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        if type(overrides["scene_profile"]) is not str:
            raise ValueError("scene_profile must be a string")

    ranges = {"grid_h": (7, 16), "grid_w": (8, 18), "obstacle_color": (2, 9)}
    for name, (lo, hi) in ranges.items():
        value = overrides.get(name)
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name} override {value!r} outside [{lo}, {hi}]")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")


def _resolved_int(ctx, overrides: dict[str, Any], name: str, scheduled: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, scheduled, scheduled))


def _resolved_choice(ctx, overrides: dict[str, Any], name: str, scheduled: Any, options: tuple[Any, ...]):
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _grid_shape_errors(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty sequences"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c})={value!r} is not an ARC integer color 0..9")
    return h, w, errors


def _square_table(grid) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    table = [[0] * w for _ in range(h)]
    for r in range(h - 1, -1, -1):
        for c in range(w - 1, -1, -1):
            if grid[r][c] != 0:
                continue
            table[r][c] = 1
            if r + 1 < h and c + 1 < w:
                table[r][c] += min(
                    table[r + 1][c], table[r][c + 1], table[r + 1][c + 1]
                )
    return table


def _square_cells(r: int, c: int, side: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for rr in range(r, r + side)
        for cc in range(c, c + side)
    }


def _square_facts(grid) -> _SquareFacts:
    table = _square_table(grid)
    h, w = len(table), len(table[0])
    max_side = max(max(row) for row in table)
    origins = tuple(
        (r, c)
        for r in range(h)
        for c in range(w)
        if table[r][c] == max_side
    )
    maximal: set[tuple[int, int]] = set()
    for r, c in origins:
        maximal.update(_square_cells(r, c, max_side))

    disjoint: set[tuple[int, int]] = set()
    all_square: set[tuple[int, int]] = set()
    for side in range(2, max_side + 1):
        for r in range(h - side + 1):
            for c in range(w - side + 1):
                if table[r][c] < side:
                    continue
                cells = _square_cells(r, c, side)
                all_square.update(cells)
                if cells.isdisjoint(maximal):
                    disjoint.update(cells)
    return _SquareFacts(
        max_side=max_side,
        maximal_origins=origins,
        maximal_cells=frozenset(maximal),
        disjoint_smaller_cells=frozenset(disjoint),
        all_square_cells=frozenset(all_square),
    )


def _paint(grid, cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    out = [list(row) for row in grid]
    for r, c in cells:
        out[r][c] = 1
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket authority for tests/contracts."""
    facts = _square_facts(grid)
    return _paint(grid, facts.maximal_cells | facts.disjoint_smaller_cells)


def _largest_only(grid) -> list[list[int]]:
    return _paint(grid, _square_facts(grid).maximal_cells)


def _mark_all_square_cells(grid) -> list[list[int]]:
    return _paint(grid, _square_facts(grid).all_square_cells)


def _first_largest_only(grid) -> list[list[int]]:
    facts = _square_facts(grid)
    cells: set[tuple[int, int]] = set()
    if facts.maximal_origins:
        r, c = facts.maximal_origins[0]
        cells = _square_cells(r, c, facts.max_side)
    return _paint(grid, cells)


def _obstacle_color(grid) -> int:
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"expected exactly one nonzero obstacle color, found {sorted(colors)}")
    return next(iter(colors))


def _color_five_only(grid) -> list[list[int]]:
    if _obstacle_color(grid) == 5:
        return rule_mirror(grid)
    return [list(row) for row in grid]


def _intended_cells(grid) -> frozenset[tuple[int, int]]:
    facts = _square_facts(grid)
    return facts.maximal_cells | facts.disjoint_smaller_cells


def _witness_disjoint_smaller(grid) -> bool:
    return bool(_square_facts(grid).disjoint_smaller_cells)


def _witness_overlap_exclusion(grid) -> bool:
    facts = _square_facts(grid)
    intended = facts.maximal_cells | facts.disjoint_smaller_cells
    return bool(facts.all_square_cells - intended)


def _witness_tied_largest(grid) -> bool:
    return len(_square_facts(grid).maximal_origins) >= 2


def _witness_non_five(grid) -> bool:
    try:
        return _obstacle_color(grid) != 5
    except ValueError:
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "largest_only": _largest_only,
    "mark_all_square_cells": _mark_all_square_cells,
    "first_largest_only": _first_largest_only,
    "color_five_only": _color_five_only,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "disjoint_smaller_square": _witness_disjoint_smaller,
    "overlap_exclusion": _witness_overlap_exclusion,
    "tied_largest_squares": _witness_tied_largest,
    "non_five_obstacle": _witness_non_five,
}
WITNESS_RIVALS = {
    "disjoint_smaller_square": ["largest_only"],
    "overlap_exclusion": ["mark_all_square_cells"],
    "tied_largest_squares": ["first_largest_only"],
    "non_five_obstacle": ["color_five_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# All canonical examples use obstacle color 5, so only generated color variation
# can disprove this otherwise-perfect canonical shortcut.
CANONICAL_SHORTCUTS = {"color_five_only": _color_five_only}


def _profile_matches(grid, profile: str) -> bool:
    facts = _square_facts(grid)
    if profile == "canonical2":
        return facts.max_side == 2 and len(facts.maximal_origins) >= 2
    if profile == "teaching":
        intended = facts.maximal_cells | facts.disjoint_smaller_cells
        return (
            facts.max_side == 3
            and len(facts.maximal_origins) >= 2
            and bool(facts.disjoint_smaller_cells)
            and bool(facts.all_square_cells - intended)
        )
    return False


def _target_density(profile: str, area: int, difficulty: Any, jitter: float) -> float:
    # Side-2 scenes need greater density as canvases grow; side-3 teaching
    # scenes need the opposite.  Difficulty only nudges within the same lawful
    # manifold and never changes an override's validity.
    if profile == "canonical2":
        base = 0.40 + min(0.08, max(0, area - 56) * 0.00035)
    else:
        base = 0.30 + min(0.05, max(0, area - 56) * 0.00022)
    shift = {None: 0.0, "easy": -0.008, "medium": 0.0, "hard": 0.008}[difficulty]
    return max(0.30, min(0.50, base + shift + jitter))


def _draw_scene(ctx, h: int, w: int, obstacle: int, profile: str, difficulty: Any):
    rng = ctx.draw_rng("layout")
    area = h * w
    cells = tuple(range(area))
    jitters = (-0.018, -0.012, -0.006, 0.0, 0.006, 0.012, 0.018)

    for attempt in range(4096):
        density = _target_density(profile, area, difficulty, jitters[attempt % len(jitters)])
        count = max(ceil(area * 0.30), min(floor(area * 0.50), round(area * density)))
        occupied = set(rng.sample(cells, count))
        grid = full_grid(h, w, 0)
        for index in occupied:
            grid[index // w][index % w] = obstacle
        if _profile_matches(grid, profile):
            return grid

    raise RuntimeError(
        f"could not construct {profile!r} scene for {h}x{w} after 4096 deterministic attempts"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal Python integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal Python integer (not bool)")
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w = _scheduled_shape(sample_index, difficulty)
    h = _resolved_int(ctx, overrides, "grid_h", scheduled_h, 7, 16)
    w = _resolved_int(ctx, overrides, "grid_w", scheduled_w, 8, 18)
    scheduled_color = _OBSTACLE_COLORS[(int(seed) + int(sample_index)) % len(_OBSTACLE_COLORS)]
    obstacle = int(
        _resolved_choice(ctx, overrides, "obstacle_color", scheduled_color, _OBSTACLE_COLORS)
    )
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile = str(
        _resolved_choice(ctx, overrides, "scene_profile", scheduled_profile, SCENE_PROFILES)
    )
    grid = _draw_scene(ctx, h, w, obstacle, profile, difficulty)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed grid failed self_check: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "obstacle_color": obstacle,
        "scene_profile": profile,
    }
    if observed != expected:
        raise RuntimeError(f"override observation mismatch: expected {expected}, observed {observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and off-manifold inputs, including minimal impostors."""
    del difficulty, meta
    h, w, errors = _grid_shape_errors(grid)
    if errors:
        return errors
    if not 7 <= h <= 16 or not 8 <= w <= 18:
        errors.append(f"dimensions {h}x{w} must lie in 7..16 by 8..18")

    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        errors.append(f"expected exactly one nonzero obstacle color, found {sorted(colors)}")
    elif not colors <= set(_OBSTACLE_COLORS):
        errors.append(f"obstacle color must be in 2..9, found {sorted(colors)}")

    obstacle_count = sum(value != 0 for row in grid for value in row)
    density = obstacle_count / (h * w)
    if not 0.30 <= density <= 0.50:
        errors.append(f"obstacle density {density:.3f} must lie in 0.30..0.50")

    if not errors:
        facts = _square_facts(grid)
        if facts.max_side not in (2, 3):
            errors.append(
                f"largest all-zero square side {facts.max_side} must be canonical side 2 or 3"
            )
        if len(facts.maximal_origins) < 1:
            errors.append("expected at least one maximal all-zero square")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict generated/canonical manifold is exactly the self-check contract."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    facts = _square_facts(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "obstacle_color": _obstacle_color(grid),
        "scene_profile": "canonical2" if facts.max_side == 2 else "teaching",
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared rivals that fit every demonstration but miss the query."""
    reasons: list[str] = []
    try:
        demo_pairs = [(item["input"], item["output"]) for item in demos]
        query_input, query_output = query["input"], query["output"]
    except (KeyError, TypeError) as exc:
        return [f"malformed lesson: {type(exc).__name__}: {exc}"]

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(grid) == output for grid, output in demo_pairs)
            if fits and rival(query_input) != query_output:
                reasons.append(f"declared rival {name!r} fits every demo but disagrees on query")
        except Exception as exc:  # fail loud through a returned contract reason
            reasons.append(f"declared rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
