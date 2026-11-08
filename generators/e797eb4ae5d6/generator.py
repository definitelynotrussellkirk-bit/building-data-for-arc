"""Generator for e5c44e8f / task e797eb4ae5d6.

The unique green (3) cell anchors a fixed relative stencil: a 49-cell spiral
path starting at the seed plus a disconnected 11-cell bar six rows below it.
With no red (2) blockers the oracle paints every in-bounds zero of the stencil.
If *any* blocker exists anywhere in the grid, the oracle instead paints only
the 4-connected stencil component reachable from the seed; blockers on the
spiral therefore cut it at their first path position, while even an off-stencil
blocker suppresses the disconnected bar.

Four consecutive sample indices deliberately expose: no-blocker full-mask
behavior, the global blocker switch with no path cut, an early path cut, and a
late path cut.  The cut profiles use shifted anchors so clipping and fixed-
position shortcuts are also rebutted in every four-demo lesson.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e797eb4ae5d6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Set atomically with the selected authority text; see source-sync evidence.
RULE_HASH = "865e9da6c30a"

SUMMARY = (
    "One green(3) seed anchors a fixed stencil made of a 49-cell spiral path "
    "and a disconnected 11-cell lower bar. With no color-2 blockers, every "
    "in-bounds zero stencil cell is painted green. If any color-2 blocker "
    "exists anywhere, only the blocker-free stencil component 4-connected to "
    "the seed is painted: an on-path blocker cuts the spiral, while even an "
    "off-stencil blocker suppresses the disconnected bar. Scheduled lessons "
    "cover the no-blocker mask, the global off-mask switch, early/late cuts, "
    "varied blocker counts, shifted anchors, clipping, and varied grid sizes."
)

INVARIANTS = [
    "background is 0 with exactly one green(3) seed; blockers, when present, are color 2",
    "with zero blockers every in-bounds zero in the fixed stencil is painted green",
    "with any blocker present only the blocker-free stencil component reachable from the seed is painted",
    "a blocker on the spiral path cuts all later path cells; off-stencil blockers are preserved and still trigger connected-component mode",
    "generated ordinary scenes are non-identity and use only colors 0, 2, and 3",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "strong 11x11 anchor on no-blocker schedule; otherwise difficulty-weighted 11..20",
        "valid": "11..20",
    },
    "grid_w": {
        "type": "int",
        "default": "strong 11x11 anchor on no-blocker schedule; otherwise difficulty-weighted 11..20",
        "valid": "11..20",
    },
    "blockers": {
        "type": "int",
        "default": "0 on no-blocker schedule; otherwise difficulty-weighted 1..12",
        "valid": "0..12",
    },
}

# Every exact cross-product value above is constructible.  Curriculum profiles
# are disabled whenever the caller supplies overrides, so no hidden profile
# constraint narrows the declared override domain.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Fixed expansion stencil relative to the green seed.  The first 49 cells form
# one simple path; the final row (dr=6) is a separate 11-cell component.
_RELS = (
    (-4, -4), (-4, -2), (-4, -1), (-4, 0), (-4, 1), (-4, 2), (-4, 3),
    (-4, 4), (-3, -4), (-3, -2), (-3, 4), (-2, -4), (-2, -2), (-2, 0),
    (-2, 1), (-2, 2), (-2, 4), (-1, -4), (-1, -2), (-1, 0), (-1, 2),
    (-1, 4), (0, -4), (0, -2), (0, 0), (0, 2), (0, 4), (1, -4),
    (1, -2), (1, 2), (1, 4), (2, -4), (2, -2), (2, -1), (2, 0),
    (2, 1), (2, 2), (2, 4), (3, -4), (3, 4), (4, -4), (4, -3),
    (4, -2), (4, -1), (4, 0), (4, 1), (4, 2), (4, 3), (4, 4),
    (6, -5), (6, -4), (6, -3), (6, -2), (6, -1), (6, 0), (6, 1),
    (6, 2), (6, 3), (6, 4), (6, 5),
)
_REL_SET = frozenset(_RELS)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _derive_core_path() -> tuple[tuple[int, int], ...]:
    """Walk the unique stencil component beginning at the seed endpoint."""
    path = [(0, 0)]
    previous = None
    current = (0, 0)
    while True:
        neighbors = [
            (current[0] + dr, current[1] + dc)
            for dr, dc in _CARDINAL
            if (current[0] + dr, current[1] + dc) in _REL_SET
            and (current[0] + dr, current[1] + dc) != previous
        ]
        # The seed component is a simple path.  The disconnected lower bar is
        # never adjacent and therefore never entered by this walk.
        unvisited = [cell for cell in neighbors if cell not in path]
        if not unvisited:
            break
        if len(unvisited) != 1:
            raise AssertionError(f"fixed stencil stopped being a simple path at {current}: {unvisited}")
        nxt = unvisited[0]
        path.append(nxt)
        previous, current = current, nxt
    if len(path) != 49:
        raise AssertionError(f"expected 49-cell seed component, derived {len(path)}")
    return tuple(path)


_CORE_PATH = _derive_core_path()
_CORE_DISTANCE = {rel: index for index, rel in enumerate(_CORE_PATH)}
_TAIL_RELS = tuple(rel for rel in _RELS if rel not in _CORE_DISTANCE)

_PROFILE_NAMES = (
    "no_blockers_full_mask",
    "off_mask_global_switch",
    "early_path_cut",
    "late_path_cut",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.12


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive sample indices expose every decisive branch."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 11, 20), ("grid_w", 11, 20), ("blockers", 0, 12)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _weighted_values(lo: int, hi: int, difficulty) -> tuple[int, ...]:
    """Full exact domain with a difficulty bias; boundaries remain overrideable."""
    values = list(range(lo, hi + 1))
    span = max(1, (hi - lo + 1) // 3)
    if difficulty == "easy":
        favored = list(range(lo, min(hi + 1, lo + span)))
    elif difficulty == "hard":
        favored = list(range(max(lo, hi - span + 1), hi + 1))
    else:
        mid = (lo + hi) // 2
        favored = list(range(max(lo, mid - 1), min(hi, mid + 1) + 1))
    return tuple(values + favored + favored)


def _seed_position(grid) -> tuple[int, int] | None:
    seeds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    return seeds[0] if len(seeds) == 1 else None


def _absolute(seed: tuple[int, int], rel: tuple[int, int]) -> tuple[int, int]:
    return seed[0] + rel[0], seed[1] + rel[1]


def _in_bounds(height: int, width: int, cell: tuple[int, int]) -> bool:
    return 0 <= cell[0] < height and 0 <= cell[1] < width


def _mask_cells(grid, seed: tuple[int, int]) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return {
        cell
        for rel in _RELS
        for cell in (_absolute(seed, rel),)
        if _in_bounds(height, width, cell) and grid[cell[0]][cell[1]] != 2
    }


def _reachable_cells(grid, seed: tuple[int, int]) -> set[tuple[int, int]]:
    mask = _mask_cells(grid, seed)
    if seed not in mask:
        return set()
    reached = {seed}
    queue = deque([seed])
    while queue:
        row, col = queue.popleft()
        for dr, dc in _CARDINAL:
            neighbor = (row + dr, col + dc)
            if neighbor in mask and neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return reached


def _paintable_count(grid, sr: int, sc: int) -> int:
    seed = (sr, sc)
    blockers = any(value == 2 for row in grid for value in row)
    targets = _reachable_cells(grid, seed) if blockers else _mask_cells(grid, seed)
    return sum(1 for row, col in targets if grid[row][col] == 0)


def _analyze(grid) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {}, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    height = len(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return {}, [f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"]

    seeds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    blockers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    palette = {value for row in grid for value in row}
    seed = seeds[0] if len(seeds) == 1 else None

    core_blocker_distances: list[int] = []
    in_bounds_rels = 0
    tail_in_bounds = 0
    if seed is not None:
        for rel in _RELS:
            if _in_bounds(height, width, _absolute(seed, rel)):
                in_bounds_rels += 1
                if rel in _TAIL_RELS:
                    tail_in_bounds += 1
        for row, col in blockers:
            rel = (row - seed[0], col - seed[1])
            if rel in _CORE_DISTANCE:
                core_blocker_distances.append(_CORE_DISTANCE[rel])

    features: dict[str, object] = {
        "grid_h": height,
        "grid_w": width,
        "seed_count": len(seeds),
        "seed": seed,
        "blockers": len(blockers),
        "blocker_cells": tuple(sorted(blockers)),
        "palette": tuple(sorted(palette)),
        "core_blocker_distances": tuple(sorted(core_blocker_distances)),
        "first_core_blocker_distance": min(core_blocker_distances) if core_blocker_distances else None,
        "tail_in_bounds": tail_in_bounds,
        "stencil_in_bounds": in_bounds_rels,
        "stencil_clipped": in_bounds_rels < len(_RELS),
    }
    return features, errors


def observe_overrides(grid) -> dict[str, int]:
    features, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe invalid spiral lesson: " + "; ".join(errors))
    return {
        "grid_h": int(features["grid_h"]),
        "grid_w": int(features["grid_w"]),
        "blockers": int(features["blockers"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar shared by generated and canonical inputs.

    Curriculum-only obligations (which semantic branch a lesson witnesses) stay
    out of this checker; they are enforced by generation assertions and the
    semantic hooks below.
    """
    del difficulty, meta
    features, errors = _analyze(grid)
    if errors:
        return errors
    height = int(features["grid_h"])
    width = int(features["grid_w"])
    if not 11 <= height <= 20:
        errors.append(f"height {height} outside generator/canonical grammar 11..20")
    if not 11 <= width <= 20:
        errors.append(f"width {width} outside generator/canonical grammar 11..20")
    palette = set(features["palette"])
    if not palette <= {0, 2, 3}:
        errors.append(f"palette must be a subset of {{0,2,3}}, found {sorted(palette)}")
    if int(features["seed_count"]) != 1:
        errors.append(f"expected exactly one green(3) seed, found {features['seed_count']}")
    blocker_count = int(features["blockers"])
    if not 0 <= blocker_count <= 12:
        errors.append(f"expected 0..12 blockers in the teaching grammar, found {blocker_count}")
    if errors:
        return errors
    seed = features["seed"]
    assert isinstance(seed, tuple)
    if _paintable_count(grid, seed[0], seed[1]) == 0:
        errors.append("no reachable paintable zero cell: authoritative rule would be identity")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Linked manifold covering all canonical geometry and an explicit anchor."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    features, _ = _analyze(grid)
    if (features["grid_h"], features["grid_w"]) != (11, 11):
        reasons.append(f"canonical dimensions are 11x11, found {features['grid_h']}x{features['grid_w']}")
    seed = features["seed"]
    if not (isinstance(seed, tuple) and seed[0] in {4, 5} and seed[1] in {4, 5, 6}):
        reasons.append(f"seed {seed} is outside the canonical anchor corridor")
    blocker_count = int(features["blockers"])
    if blocker_count not in {0, 9, 10}:
        reasons.append(f"canonical blocker counts are 0, 9, or 10; found {blocker_count}")
    if blocker_count and not features["core_blocker_distances"]:
        reasons.append("canonical blocker examples include at least one spiral-path blocker")
    return reasons


def _paint_positions(grid, positions) -> list[list[int]]:
    out = [list(row) for row in grid]
    for row, col in positions:
        if out[row][col] == 0:
            out[row][col] = 3
    return out


def _rule_mirror(grid) -> list[list[int]]:
    """Test/semantic mirror only; canonical Racket remains output authority."""
    seed = _seed_position(grid)
    if seed is None:
        return [list(row) for row in grid]
    has_blockers = any(value == 2 for row in grid for value in row)
    targets = _reachable_cells(grid, seed) if has_blockers else _mask_cells(grid, seed)
    return _paint_positions(grid, targets)


def _rival_ignore_blockers(grid) -> list[list[int]]:
    """Shortcut: blockers are preserved but never truncate/switch the stencil."""
    seed = _seed_position(grid)
    if seed is None:
        return [list(row) for row in grid]
    return _paint_positions(grid, _mask_cells(grid, seed))


def _rival_always_connected(grid) -> list[list[int]]:
    """Shortcut: always use only the seed-connected spiral, even with no blockers."""
    seed = _seed_position(grid)
    if seed is None:
        return [list(row) for row in grid]
    return _paint_positions(grid, _reachable_cells(grid, seed))


def _rival_local_blockers_only(grid) -> list[list[int]]:
    """Plausible canonical-fitting shortcut: switch mode only for a stencil blocker."""
    seed = _seed_position(grid)
    if seed is None:
        return [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    stencil = {
        _absolute(seed, rel)
        for rel in _RELS
        if _in_bounds(height, width, _absolute(seed, rel))
    }
    has_stencil_blocker = any(grid[row][col] == 2 for row, col in stencil)
    targets = _reachable_cells(grid, seed) if has_stencil_blocker else _mask_cells(grid, seed)
    return _paint_positions(grid, targets)


def _rival_fixed_center_anchor(grid) -> list[list[int]]:
    """Shortcut: ignore the observed seed and always anchor at canonical (4,5)."""
    if len(grid) <= 4 or len(grid[0]) <= 5:
        return [list(row) for row in grid]
    anchor = (4, 5)
    has_blockers = any(value == 2 for row in grid for value in row)
    targets = _reachable_cells(grid, anchor) if has_blockers else _mask_cells(grid, anchor)
    return _paint_positions(grid, targets)


def _witness_no_blockers_full_mask(grid) -> bool:
    features, errors = _analyze(grid)
    return not errors and features["blockers"] == 0 and features["tail_in_bounds"] > 0


def _witness_off_mask_global_switch(grid) -> bool:
    features, errors = _analyze(grid)
    return (
        not errors
        and int(features["blockers"]) > 0
        and not features["core_blocker_distances"]
        and int(features["tail_in_bounds"]) > 0
    )


def _witness_early_path_cut(grid) -> bool:
    features, errors = _analyze(grid)
    distance = features.get("first_core_blocker_distance")
    return not errors and isinstance(distance, int) and 2 <= distance <= 18


def _witness_late_path_cut(grid) -> bool:
    features, errors = _analyze(grid)
    distance = features.get("first_core_blocker_distance")
    return not errors and isinstance(distance, int) and 30 <= distance <= 47


def _witness_shifted_clipped_anchor(grid) -> bool:
    features, errors = _analyze(grid)
    return (
        not errors
        and bool(features["stencil_clipped"])
        and features["seed"] != (4, 5)
    )


SEMANTIC_WITNESSES = {
    "no_blockers_full_mask": _witness_no_blockers_full_mask,
    "off_mask_global_switch": _witness_off_mask_global_switch,
    "early_path_cut": _witness_early_path_cut,
    "late_path_cut": _witness_late_path_cut,
    "shifted_clipped_anchor": _witness_shifted_clipped_anchor,
}

SEMANTIC_RIVALS = {
    "ignore_blockers": _rival_ignore_blockers,
    "always_connected": _rival_always_connected,
    "local_blockers_only": _rival_local_blockers_only,
    "fixed_center_anchor": _rival_fixed_center_anchor,
}

WITNESS_RIVALS = {
    "no_blockers_full_mask": ["always_connected"],
    "off_mask_global_switch": ["local_blockers_only"],
    "early_path_cut": ["ignore_blockers"],
    "late_path_cut": ["ignore_blockers"],
    "shifted_clipped_anchor": ["fixed_center_anchor"],
}

# This shortcut fits every canonical pair: all canonical blocker-bearing inputs
# happen to contain at least one blocker on the stencil.  Only generated
# off-stencil-blocker scenes can show that *any* blocker globally switches mode.
CANONICAL_SHORTCUTS = {
    "local_blockers_only": _rival_local_blockers_only,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to kill the named canonical/shape rivals."""
    del query
    reasons: list[str] = []
    inputs = [demo["input"] for demo in demos]
    required = {
        "no-blocker full mask": _witness_no_blockers_full_mask,
        "off-mask global blocker switch": _witness_off_mask_global_switch,
        "early path cut": _witness_early_path_cut,
        "late path cut": _witness_late_path_cut,
        "shifted/clipped anchor": _witness_shifted_clipped_anchor,
    }
    for name, predicate in required.items():
        if not any(predicate(grid) for grid in inputs):
            reasons.append(f"demos lack {name} witness")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"named rival {name!r} survives every demo")
    return reasons


def _choose_dimensions(ctx, profile: str | None, difficulty) -> tuple[int, int]:
    # One of every four ordinary draws is the exact canonical 11x11 no-blocker
    # anchor in every difficulty band.  Override calls bypass profile scheduling
    # and retain the entire declared 11..20 domain.
    if profile == "no_blockers_full_mask":
        # Every four-example lesson gets one exact 11x11 canonical-profile
        # anchor.  Seed position still varies over six placements, so the
        # canonical anchor does not collapse the generator to a fixed grid.
        return ctx.draw_choice("grid_h", (11,)), ctx.draw_choice("grid_w", (11,))
    return (
        ctx.draw_choice("grid_h", _weighted_values(11, 20, difficulty)),
        ctx.draw_choice("grid_w", _weighted_values(11, 20, difficulty)),
    )


def _place_blockers(
    grid,
    seed: tuple[int, int],
    count: int,
    rng,
    *,
    profile: str | None,
) -> None:
    if count == 0:
        return
    height, width = len(grid), len(grid[0])
    stencil_cells = {
        _absolute(seed, rel)
        for rel in _RELS
        if _in_bounds(height, width, _absolute(seed, rel))
    }
    off_mask = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) != seed and (row, col) not in stencil_cells
    ]

    chosen: list[tuple[int, int]] = []
    if profile == "off_mask_global_switch":
        if len(off_mask) < count:
            raise ValueError("not enough off-stencil cells for blocker profile")
        chosen = rng.sample(off_mask, count)
    elif profile in {"early_path_cut", "late_path_cut"}:
        distances = range(4, 17) if profile == "early_path_cut" else range(32, 45)
        legal_distances = [
            distance
            for distance in distances
            if _in_bounds(height, width, _absolute(seed, _CORE_PATH[distance]))
        ]
        if not legal_distances:
            raise ValueError(f"no legal {profile} blocker distance")
        distance = rng.choice(legal_distances)
        chosen.append(_absolute(seed, _CORE_PATH[distance]))
        if count > 1:
            pool = [cell for cell in off_mask if cell not in chosen]
            if len(pool) < count - 1:
                raise ValueError("not enough decoy cells for blocker profile")
            chosen.extend(rng.sample(pool, count - 1))
    else:
        # Override mode: all exact blocker counts 0..12 are legal.  Excluding
        # path-distance 1 guarantees at least one paintable zero even if the
        # remaining blockers happen to hit the spiral.
        forbidden = {seed}
        if _in_bounds(height, width, _absolute(seed, _CORE_PATH[1])):
            forbidden.add(_absolute(seed, _CORE_PATH[1]))
        pool = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if (row, col) not in forbidden
        ]
        chosen = rng.sample(pool, count)

    if len(chosen) != count or len(set(chosen)) != count:
        raise AssertionError("blocker placement did not realize exact requested count")
    for row, col in chosen:
        if grid[row][col] != 0:
            raise AssertionError(f"blocker placement collided at {(row, col)}")
        grid[row][col] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")

    profile = None if overrides else schedule_profile(seed, sample_index, difficulty)
    height, width = _choose_dimensions(ctx, profile, difficulty)

    if profile == "no_blockers_full_mask":
        blocker_count = ctx.draw_choice("blockers", (0,))
        # Six positions preserve output variation while staying at canonical
        # dimensions. Row 3 also teaches top-edge clipping of the same stencil.
        seed_cell = (rng.choice((3, 4)), rng.choice((4, 5, 6)))
    elif profile == "off_mask_global_switch":
        blocker_count = ctx.draw_choice("blockers", _weighted_values(1, 12, difficulty))
        seed_cell = (4, 5)  # disconnected lower bar is fully in bounds
    elif profile == "early_path_cut":
        blocker_count = ctx.draw_choice("blockers", _weighted_values(1, 12, difficulty))
        seed_cell = (4, 4)  # leftmost lower-bar cell clips; core spiral remains in bounds
    elif profile == "late_path_cut":
        blocker_count = ctx.draw_choice("blockers", _weighted_values(1, 12, difficulty))
        seed_cell = (4, width - 5)  # symmetric right clipping with core still in bounds
    else:
        blocker_count = ctx.draw_choice("blockers", _weighted_values(0, 12, difficulty))
        # Full stencil fits, making every exact override combination constructive.
        seed_cell = (
            rng.randint(4, height - 7),
            rng.randint(5, width - 6),
        )

    grid = full_grid(height, width, 0)
    grid[seed_cell[0]][seed_cell[1]] = 3
    _place_blockers(grid, seed_cell, blocker_count, rng, profile=profile)

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid spiral lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "blockers": blocker_count}
    if observed != expected:
        raise AssertionError(f"axis provenance mismatch: expected {expected}, observed {observed}")
    if _rule_mirror(grid) == grid:
        raise AssertionError("constructed an identity/no-op spiral lesson")

    # Turn the schedule from an aspiration into a generation invariant.
    if profile is not None:
        expected_witness = {
            "no_blockers_full_mask": _witness_no_blockers_full_mask,
            "off_mask_global_switch": _witness_off_mask_global_switch,
            "early_path_cut": _witness_early_path_cut,
            "late_path_cut": _witness_late_path_cut,
        }[profile]
        if not expected_witness(grid):
            raise AssertionError(f"scheduled profile {profile!r} lost its semantic witness")
        if profile in {"early_path_cut", "late_path_cut"} and not _witness_shifted_clipped_anchor(grid):
            raise AssertionError(f"scheduled profile {profile!r} lost shifted/clipped-anchor witness")
    return grid
