"""Input sampler for 90-degree clockwise rotation about a color-9 anchor.

The selected rule keeps the unique 9-cell fixed and rotates every other nonzero
cell independently around that *actual* anchor.  The public examples are all
monochrome and 4-connected, and two of three place the anchor at the integer
center, so those examples alone under-specify three plausible shortcuts.  The
four-profile curriculum below deliberately varies color and connectivity while
placing every generated anchor off the integer center.  Any consecutive
four-demo lesson, including any one-pair query rotation from a five-pair window,
retains evidence against all declared competitors.

The selected Racket authority is unchanged.  This module samples only inputs;
its Python transformation helpers are analysis rivals, not label authority.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1e07c169ac61"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b7275e98009a"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Keep the unique color-9 anchor fixed and rotate every other nonzero cell "
    "90 degrees clockwise around that anchor, preserving each cell's color."
)

INVARIANTS = [
    "the input is a 6..10 by 6..10 integer ARC grid with background color 0",
    "exactly one color-9 anchor is present and generated anchors are off the integer center",
    "exactly 3..8 nonzero non-9 foreground cells are present",
    "every foreground destination under the anchor-centered clockwise rotation stays in bounds",
    "the sampled foreground is not invariant under the selected rotation",
    "the curriculum spans mono/multicolor and connected/disconnected foregrounds",
]

PROFILES = (
    "mono_connected",
    "multicolor_connected",
    "mono_disconnected",
    "multicolor_disconnected",
)
SCHEDULE_PROFILES = PROFILES
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile schedule; broad profiles vary across 6..10",
        "valid": "6..10",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "profile schedule; broad profiles vary across 6..10",
        "valid": "6..10",
        "doc": "Exact returned grid width.",
    },
    "foreground_size": {
        "type": "int",
        "default": "difficulty-weighted 3..8",
        "valid": "3..8",
        "doc": "Exact count of nonzero, non-9 source cells.",
    },
    "profile": {
        "type": "str",
        "default": "four-slot teaching schedule",
        "valid": "|".join(PROFILES),
        "doc": "Exact mono/multicolor and 4-connectivity profile.",
    },
}

# Every advertised cross-product is constructive, including 6x10 / 10x6 with
# eight isolated cells.  Keep this explicit so a future rejection is a defect,
# not an implicitly accepted incompatibility.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_SIDES = (
    lambda r, c, ar, ac: r < ar,
    lambda r, c, ar, ac: r > ar,
    lambda r, c, ar, ac: c < ac,
    lambda r, c, ar, ac: c > ac,
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(
        f"unknown difficulty {difficulty!r}; expected None, 'easy', 'medium', or 'hard'"
    )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic four-slot curriculum; seed and band do not alter the slot."""
    del seed
    _band(difficulty)
    return PROFILES[int(sample_index) % len(PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name in ("grid_h", "grid_w", "foreground_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    profile = overrides.get("profile")
    if profile is not None and type(profile) is not str:
        raise TypeError(f"profile must be a string, not {type(profile).__name__}")
    return band


def _draw_profile(ctx, overrides: dict[str, Any], default: str) -> str:
    if overrides.get("profile") is not None:
        return ctx.draw_choice("profile", PROFILES)
    # A singleton keyed draw records the exact scheduled semantic branch while
    # explicit overrides still use the complete declared domain above.
    return ctx.draw_choice("profile", (default,))


def _draw_dimension(
    ctx,
    overrides: dict[str, Any],
    name: str,
    *,
    profile: str,
    band: str,
) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, 6, 10)
    # Half the ordinary stream anchors an exact canonical profile in every
    # difficulty band.  The two broad profiles retain the full size domain.
    if profile == "mono_connected":
        return ctx.draw_int_strict(name, 7, 7)
    if profile == "mono_disconnected":
        return ctx.draw_int_strict(name, 6, 6)
    options = list(range(6, 11))
    favored = {
        "easy": (6, 7),
        "medium": (7, 8, 9),
        "hard": (9, 10),
    }[band]
    options.extend(favored * 4)
    return int(ctx.draw_choice(name, options))


def _draw_foreground_size(ctx, overrides: dict[str, Any], band: str) -> int:
    if overrides.get("foreground_size") is not None:
        return ctx.draw_int_strict("foreground_size", 3, 8)
    options = list(range(3, 9))
    favored = {
        "easy": (3, 4),
        "medium": (4, 5, 6),
        "hard": (6, 7, 8),
    }[band]
    options.extend(favored * 4)
    return int(ctx.draw_choice("foreground_size", options))


def _rotated_point(anchor: tuple[int, int], point: tuple[int, int]) -> tuple[int, int]:
    ar, ac = anchor
    r, c = point
    return ar + (c - ac), ac - (r - ar)


def _valid_sites(h: int, w: int, anchor: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) != anchor
        and 0 <= _rotated_point(anchor, (r, c))[0] < h
        and 0 <= _rotated_point(anchor, (r, c))[1] < w
    )


def _components4(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _connected_regions(
    sites: Sequence[tuple[int, int]], anchor: tuple[int, int], count: int
) -> tuple[tuple[tuple[int, int], ...], ...]:
    ar, ac = anchor
    regions: list[tuple[tuple[int, int], ...]] = []
    for predicate in _SIDES:
        side = [point for point in sites if predicate(*point, ar, ac)]
        for component in _components4(side):
            if len(component) >= count:
                regions.append(tuple(sorted(component)))
    return tuple(regions)


def _sector(point: tuple[int, int], anchor: tuple[int, int]) -> tuple[int, int]:
    dr = point[0] - anchor[0]
    dc = point[1] - anchor[1]
    return ((dr > 0) - (dr < 0), (dc > 0) - (dc < 0))


def _disconnected_plans(
    sites: Sequence[tuple[int, int]], anchor: tuple[int, int], count: int
) -> tuple[tuple[int, tuple[int, int], tuple[tuple[int, int], ...]], ...]:
    """Return parity/seed pools that guarantee isolation and non-identity.

    Same-parity cells are never 4-neighbors.  A distinguished seed is chosen
    whose rotated destination is explicitly excluded from the source pool, so
    the selected set cannot be invariant under the intended rotation.
    """
    plans: list[tuple[int, tuple[int, int], tuple[tuple[int, int], ...]]] = []
    for parity in (0, 1):
        pool = tuple(sorted(point for point in sites if sum(point) % 2 == parity))
        if len(pool) < count:
            continue
        pool_set = set(pool)
        for seed in pool:
            rotated = _rotated_point(anchor, seed)
            available = tuple(point for point in pool if point != seed and point != rotated)
            if len(available) < count - 1:
                continue
            if count > 1 and not any(
                _sector(point, anchor) != _sector(seed, anchor) for point in available
            ):
                continue
            # If the rotated seed is not in the chosen source set, rotation
            # necessarily changes the finite set.  Retain the full legal pool;
            # construction below reserves one different-sector marker first.
            if rotated in pool_set or rotated not in pool_set:
                plans.append((parity, seed, available))
    return tuple(plans)


@lru_cache(maxsize=600)
def _anchor_plans(
    h: int, w: int, count: int, connected: bool
) -> tuple[tuple[tuple[int, int], tuple[Any, ...]], ...]:
    plans: list[tuple[tuple[int, int], tuple[Any, ...]]] = []
    integer_center = (h // 2, w // 2)
    for ar in range(h):
        for ac in range(w):
            anchor = (ar, ac)
            if anchor == integer_center:
                continue
            sites = _valid_sites(h, w, anchor)
            if connected:
                regions = _connected_regions(sites, anchor, count)
                if regions:
                    plans.append((anchor, regions))
            else:
                disconnected = _disconnected_plans(sites, anchor, count)
                if disconnected:
                    plans.append((anchor, disconnected))
    return tuple(plans)


def _grow_connected(
    region: Sequence[tuple[int, int]], count: int, rng
) -> list[tuple[int, int]]:
    allowed = set(region)
    cells = {rng.choice(list(region))}
    while len(cells) < count:
        frontier = sorted(
            neighbor
            for r, c in cells
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if neighbor in allowed and neighbor not in cells
        )
        if not frontier:
            raise RuntimeError("connected-region construction lost its frontier")
        cells.add(rng.choice(frontier))
    return sorted(cells)


def _draw_disconnected(
    plan: tuple[int, tuple[int, int], tuple[tuple[int, int], ...]],
    anchor: tuple[int, int],
    count: int,
    rng,
) -> list[tuple[int, int]]:
    _parity, seed, available = plan
    chosen = [seed]
    remaining = list(available)
    if count > 1:
        different = [point for point in remaining if _sector(point, anchor) != _sector(seed, anchor)]
        second = rng.choice(different)
        chosen.append(second)
        remaining.remove(second)
    if count > len(chosen):
        chosen.extend(rng.sample(remaining, count - len(chosen)))
    return sorted(chosen)


def _draw_layout(
    ctx,
    h: int,
    w: int,
    count: int,
    profile: str,
) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    connected = profile.endswith("connected") and not profile.endswith("disconnected")
    plans = _anchor_plans(h, w, count, connected)
    if not plans:
        raise RuntimeError(
            f"no constructive anchor plan for {h}x{w}, count={count}, profile={profile}"
        )
    anchor, choices = ctx.draw_rng("anchor_position").choice(plans)
    layout_rng = ctx.draw_rng("foreground_layout")
    if connected:
        region = layout_rng.choice(list(choices))
        cells = _grow_connected(region, count, layout_rng)
    else:
        plan = layout_rng.choice(list(choices))
        cells = _draw_disconnected(plan, anchor, count, layout_rng)
    rotated = {_rotated_point(anchor, point) for point in cells}
    if rotated == set(cells):
        raise RuntimeError("constructive layout unexpectedly invariant under rotation")
    return anchor, cells


def _paint_foreground(
    grid: list[list[int]],
    cells: Sequence[tuple[int, int]],
    profile: str,
    rng,
) -> None:
    color_count = 1 if profile.startswith("mono_") else (3 if len(cells) >= 6 else 2)
    colors = rng.sample(list(range(1, 9)), color_count)
    shuffled = list(cells)
    rng.shuffle(shuffled)
    for index, (r, c) in enumerate(shuffled):
        grid[r][c] = colors[index % len(colors)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile = _draw_profile(ctx, overrides, scheduled)
    h = _draw_dimension(ctx, overrides, "grid_h", profile=profile, band=band)
    w = _draw_dimension(ctx, overrides, "grid_w", profile=profile, band=band)
    foreground_size = _draw_foreground_size(ctx, overrides, band)

    anchor, cells = _draw_layout(ctx, h, w, foreground_size, profile)
    grid = full_grid(h, w, 0)
    grid[anchor[0]][anchor[1]] = 9
    _paint_foreground(grid, cells, profile, ctx.draw_rng("foreground_palette"))
    return grid


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        return []
    rows: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)):
            return []
        rows.append(list(row))
    return rows


def _anchor(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    hits = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one color-9 anchor, found {hits}")
    return hits[0]


def observe_overrides(grid) -> dict[str, object]:
    """Recover every advertised exact control from returned pixels."""
    rows = _coerce_grid(grid)
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("cannot observe a malformed grid")
    foreground = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    colors = {rows[r][c] for r, c in foreground}
    connected = len(_components4(foreground)) == 1
    profile = (
        ("mono_" if len(colors) == 1 else "multicolor_")
        + ("connected" if connected else "disconnected")
    )
    return {
        "grid_h": len(rows),
        "grid_w": len(rows[0]),
        "foreground_size": len(foreground),
        "profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked bounded teaching manifold."""
    del difficulty, meta
    rows = _coerce_grid(grid)
    if not rows or not rows[0]:
        return ["grid must be a nonempty rectangular list of rows"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return ["ragged grid: every row must have the same width"]

    h, w = len(rows), width
    errors: list[str] = []
    if not 6 <= h <= 10 or not 6 <= w <= 10:
        errors.append(f"grid dimensions must each be 6..10, got {h}x{w}")

    invalid = [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(
            f"cells must be integer ARC colors 0..9; first invalid {invalid[0]}"
        )
        return errors

    anchors = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-9 anchor, found {anchors}")

    foreground = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not 3 <= len(foreground) <= 8:
        errors.append(f"expected 3..8 foreground cells, got {len(foreground)}")

    if len(anchors) == 1 and foreground:
        anchor = anchors[0]
        rotated = [_rotated_point(anchor, point) for point in foreground]
        out_of_bounds = [
            point for point in rotated if not (0 <= point[0] < h and 0 <= point[1] < w)
        ]
        if out_of_bounds:
            errors.append(
                f"{len(out_of_bounds)} rotated foreground destination(s) leave the grid"
            )
        if set(rotated) == set(foreground):
            errors.append("foreground is invariant under the 90-degree rotation")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _rotate_selected(
    grid,
    *,
    pivot: tuple[int, int] | None = None,
    selected: Callable[[int, int, int], bool] | None = None,
) -> list[list[int]]:
    rows = _coerce_grid(grid)
    if not rows or not rows[0]:
        raise ValueError("expected a nonempty grid")
    h, w = len(rows), len(rows[0])
    actual_anchor = _anchor(rows)
    ar, ac = actual_anchor if pivot is None else pivot
    out = full_grid(h, w, 0)
    out[actual_anchor[0]][actual_anchor[1]] = 9
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            if selected is not None and not selected(r, c, value):
                continue
            rr, cc = ar + (c - ac), ac - (r - ar)
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def _center_pivot(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    return _rotate_selected(grid, pivot=(len(rows) // 2, len(rows[0]) // 2))


def _first_color_only(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    first = next(value for row in rows for value in row if value not in (0, 9))
    return _rotate_selected(rows, selected=lambda _r, _c, value: value == first)


def _largest_component_only(grid) -> list[list[int]]:
    rows = _coerce_grid(grid)
    foreground = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    component = min(_components4(foreground), key=lambda item: (-len(item), min(item)))
    return _rotate_selected(
        rows, selected=lambda r, c, _value: (r, c) in component
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "center_pivot": _center_pivot,
    "first_color_only": _first_color_only,
    "largest_component_only": _largest_component_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "first_color_only": _first_color_only,
    "largest_component_only": _largest_component_only,
}


def _lawful(grid) -> bool:
    return self_check(grid) == []


def _off_center_anchor(grid) -> bool:
    rows = _coerce_grid(grid)
    return bool(rows and rows[0] and _lawful(rows)) and _anchor(rows) != (
        len(rows) // 2,
        len(rows[0]) // 2,
    )


def _multicolor(grid) -> bool:
    rows = _coerce_grid(grid)
    if not rows or not rows[0] or not _lawful(rows):
        return False
    return len({value for row in rows for value in row if value not in (0, 9)}) > 1


def _disconnected(grid) -> bool:
    rows = _coerce_grid(grid)
    if not rows or not rows[0] or not _lawful(rows):
        return False
    foreground = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    return len(_components4(foreground)) > 1


SEMANTIC_WITNESSES = {
    "off_center_anchor": _off_center_anchor,
    "multicolor": _multicolor,
    "disconnected": _disconnected,
}
WITNESS_RIVALS = {
    "off_center_anchor": ["center_pivot"],
    "multicolor": ["first_color_only"],
    "disconnected": ["largest_component_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a labeled lesson when a declared wrong rule survives the demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            differs = rival(query["input"]) != query["output"]
        except Exception as exc:  # diagnostic contract: never hide a broken rival
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and differs:
            reasons.append(
                f"competitor {name} fits every demonstration but changes the query"
            )
    return reasons
