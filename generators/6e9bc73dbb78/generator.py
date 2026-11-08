"""Generator for arc_puzzle_bank_21_set3:S3_E7.

The only non-background color that forms exactly one 4-connected component is
recolored yellow.  The curriculum deliberately varies color order, reading
order, component count, and cell-count relations so that color-, position-,
and size-based shortcuts disagree with the canonical rule.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6e9bc73dbb78"
TASK_ID = "6e9bc73dbb78"
VERSION = "2.0.0"
RULE_HASH = "9098234c66fa"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Recolor every cell of the sole color that forms exactly one "
    "4-connected component to yellow (4)."
)

INVARIANTS = [
    "background is 0 and input color 4 is absent",
    "exactly two nonzero colors are present",
    "one color forms exactly one 4-connected component",
    "the other color forms 2..4 disconnected 4-connected components",
    "color, reading-order, and object-size cues vary independently of the target",
]

SIZE_PROFILES = (
    "target_smaller_each",
    "target_equal_each",
    "target_larger_each_but_smaller_total",
    "target_equal_total",
    "target_larger_total",
)
COLOR_ORDERS = ("target_lower", "target_higher")
POSITION_ORDERS = ("target_first", "target_last")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors plus difficulty-aware 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors plus difficulty-aware 9..16",
        "valid": "9..16",
    },
    "n_repeat": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "2..4",
    },
    "size_profile": {
        "type": "str",
        "default": "scheduled shortcut-rebutting profile",
        "valid": "|".join(SIZE_PROFILES),
    },
    "color_order": {
        "type": "str",
        "default": "scheduled lower/higher target color",
        "valid": "|".join(COLOR_ORDERS),
    },
    "position_order": {
        "type": "str",
        "default": "scheduled first/last target component",
        "valid": "|".join(POSITION_ORDERS),
    },
}

# Every declared cross-product combination is intentionally supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_LEGAL_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
_CANONICAL_ANCHORS = (
    # (height, width, target color, repeated color, repeated components)
    (8, 9, 3, 1, 2),
    (9, 10, 6, 1, 3),
    (10, 10, 7, 2, 3),
)


def _components_by_color(grid: list[list[int]]) -> dict[int, list[set[tuple[int, int]]]]:
    """Return 4-connected non-background components grouped by color."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: dict[int, list[set[tuple[int, int]]]] = defaultdict(list)
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            component = {(sr, sc)}
            seen.add((sr, sc))
            stack = [(sr, sc)]
            while stack:
                r, c = stack.pop()
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        component.add((nr, nc))
                        stack.append((nr, nc))
            out[color].append(component)
    return dict(out)


def _component_counts_by_color(grid: list[list[int]]) -> dict[int, int]:
    return {color: len(parts) for color, parts in _components_by_color(grid).items()}


def _scene_facts(grid: list[list[int]]) -> dict[str, object]:
    components = _components_by_color(grid)
    counts = {color: len(parts) for color, parts in components.items()}
    singleton_colors = [color for color, count in counts.items() if count == 1]
    repeated_colors = [color for color, count in counts.items() if count >= 2]
    facts: dict[str, object] = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "components": components,
        "counts": counts,
        "singleton_colors": singleton_colors,
        "repeated_colors": repeated_colors,
    }
    if len(singleton_colors) != 1 or len(repeated_colors) != 1:
        return facts

    target_color = singleton_colors[0]
    repeat_color = repeated_colors[0]
    target_component = components[target_color][0]
    repeat_components = components[repeat_color]
    target_area = len(target_component)
    repeat_areas = sorted(len(part) for part in repeat_components)
    target_first = min(target_component)
    repeat_first = min(cell for part in repeat_components for cell in part)

    facts.update(
        {
            "target_color": target_color,
            "repeat_color": repeat_color,
            "target_component": target_component,
            "repeat_components": repeat_components,
            "target_area": target_area,
            "repeat_areas": repeat_areas,
            "repeat_total_area": sum(repeat_areas),
            "n_repeat": len(repeat_components),
            "color_order": (
                "target_lower" if target_color < repeat_color else "target_higher"
            ),
            "position_order": (
                "target_first" if target_first < repeat_first else "target_last"
            ),
        }
    )
    profile = _infer_size_profile(
        target_area=target_area,
        repeat_areas=repeat_areas,
        n_repeat=len(repeat_components),
    )
    if profile is not None:
        facts["size_profile"] = profile
    return facts


def _infer_size_profile(
    *, target_area: int, repeat_areas: list[int], n_repeat: int
) -> str | None:
    if not repeat_areas or len(set(repeat_areas)) != 1:
        return None
    repeat_area = repeat_areas[0]
    if target_area == 2 and repeat_area == 3:
        return "target_smaller_each"
    if target_area == 3 and repeat_area == 3:
        return "target_equal_each"
    if target_area == n_repeat + 2 and repeat_area == 3:
        return "target_larger_each_but_smaller_total"
    if target_area == 2 * n_repeat and repeat_area == 2:
        return "target_equal_total"
    if target_area == n_repeat + 2 and repeat_area == 1:
        return "target_larger_total"
    return None


def _areas_for_profile(profile: str, n_repeat: int) -> tuple[int, int]:
    if profile == "target_smaller_each":
        return 2, 3
    if profile == "target_equal_each":
        return 3, 3
    if profile == "target_larger_each_but_smaller_total":
        return n_repeat + 2, 3
    if profile == "target_equal_total":
        return 2 * n_repeat, 2
    if profile == "target_larger_total":
        return n_repeat + 2, 1
    raise ValueError(f"unknown size_profile {profile!r}")


def _record_scheduled_int(ctx, label: str, lo: int, hi: int, value: int) -> int:
    """Record a deterministic schedule value while preserving override semantics."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if not lo <= value <= hi:
        raise ValueError(f"scheduled {label}={value} outside [{lo}, {hi}]")
    ctx.draw_bounds_store[label] = (lo, hi)
    return int(ctx._record(label, int(value), from_override=False))


def _record_scheduled_choice(ctx, label: str, options: tuple[str, ...], value: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    if value not in options:
        raise ValueError(f"scheduled {label}={value!r} not in {options!r}")
    ctx.draw_options_store[label] = tuple(options)
    return str(ctx._record(label, value, from_override=False))


def _shape_for_area(area: int, variant: int) -> list[tuple[int, int]]:
    """Connected polyomino of exactly ``area`` cells with varied aspect ratio."""
    if area < 1:
        raise ValueError("shape area must be positive")
    widths = (1, min(2, area), min(3, area), min(4, area))
    width = widths[variant % len(widths)]
    cells: list[tuple[int, int]] = []
    row = 0
    remaining = area
    while remaining:
        take = min(width, remaining)
        cols = list(range(take))
        if row % 2:
            cols = list(reversed(cols))
        cells.extend((row, col) for col in cols)
        remaining -= take
        row += 1
    # Normalize after optional transpose so every shape contains (0, 0).
    if (variant // len(widths)) % 2:
        cells = [(c, r) for r, c in cells]
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _can_place(
    grid: list[list[int]],
    shape: list[tuple[int, int]],
    offset: tuple[int, int],
    color: int,
) -> bool:
    h, w = len(grid), len(grid[0])
    rr, cc = offset
    cells = {(rr + dr, cc + dc) for dr, dc in shape}
    if any(r < 0 or r >= h or c < 0 or c >= w for r, c in cells):
        return False
    if any(grid[r][c] != 0 for r, c in cells):
        return False
    # Same-color components must remain 4-disconnected.  Adjacent cells within
    # the new shape are allowed; only neighbors outside the shape matter.
    for r, c in cells:
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            if (nr, nc) not in cells and 0 <= nr < h and 0 <= nc < w:
                if grid[nr][nc] == color:
                    return False
    return True


def _place_shape(
    rng,
    grid: list[list[int]],
    shape: list[tuple[int, int]],
    color: int,
    *,
    key_relation: Callable[[tuple[int, int]], bool] | None = None,
) -> tuple[int, int] | None:
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = [
        (r, c)
        for r in range(h - sh + 1)
        for c in range(w - sw + 1)
        if key_relation is None or key_relation((r, c))
    ]
    rng.shuffle(candidates)
    for offset in candidates:
        if _can_place(grid, shape, offset, color):
            rr, cc = offset
            for dr, dc in shape:
                grid[rr + dr][cc + dc] = color
            return offset
    return None


def _choose_colors(ctx, *, color_order: str, anchor_index: int | None) -> tuple[int, int]:
    rng = ctx.draw_rng("palette")
    if anchor_index is not None and color_order == "target_higher":
        _, _, target, repeated, _ = _CANONICAL_ANCHORS[anchor_index]
        return target, repeated
    low, high = sorted(rng.sample(_LEGAL_COLORS, 2))
    if color_order == "target_lower":
        return low, high
    return high, low


def _draw_grid(
    *,
    h: int,
    w: int,
    target_color: int,
    repeat_color: int,
    n_repeat: int,
    size_profile: str,
    position_order: str,
    rng,
    sample_index: int,
) -> list[list[int]]:
    target_area, repeat_area = _areas_for_profile(size_profile, n_repeat)
    for attempt in range(160):
        grid = full_grid(h, w, 0)
        target_shape = _shape_for_area(target_area, sample_index + attempt)
        target_candidates = [
            (r, c)
            for r in range(h - max(x for x, _ in target_shape))
            for c in range(w - max(y for _, y in target_shape))
        ]
        # Pick target near one end of reading order, then constrain every
        # repeated component to the opposite side of its top-left key.
        target_candidates.sort()
        span = max(1, len(target_candidates) // 3)
        pool = (
            target_candidates[:span]
            if position_order == "target_first"
            else target_candidates[-span:]
        )
        rng.shuffle(pool)
        target_offset = next(
            (
                offset
                for offset in pool
                if _can_place(grid, target_shape, offset, target_color)
            ),
            None,
        )
        if target_offset is None:
            continue
        rr, cc = target_offset
        for dr, dc in target_shape:
            grid[rr + dr][cc + dc] = target_color

        if position_order == "target_first":
            relation = lambda key, bound=target_offset: key > bound
        else:
            relation = lambda key, bound=target_offset: key < bound

        ok = True
        for index in range(n_repeat):
            repeat_shape = _shape_for_area(
                repeat_area, sample_index * 7 + attempt * 3 + index
            )
            if _place_shape(
                rng,
                grid,
                repeat_shape,
                repeat_color,
                key_relation=relation,
            ) is None:
                ok = False
                break
        if not ok:
            continue

        facts = _scene_facts(grid)
        if (
            facts.get("n_repeat") == n_repeat
            and facts.get("size_profile") == size_profile
            and facts.get("position_order") == position_order
        ):
            return grid
    raise ValueError(
        "could not place the requested unique/repeated component scene "
        f"on {h}x{w} after 160 deterministic attempts"
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the task's complete input grammar and reject impostors."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]
    h = len(grid)
    errors: list[str] = []
    if not (8 <= h <= 14 and 9 <= w <= 16):
        errors.append(f"grid dimensions must be within 8..14 by 9..16, got {h}x{w}")
    invalid = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"invalid ARC colors present: {sorted(set(map(repr, invalid)))}")
        return errors
    if 0 not in {value for row in grid for value in row}:
        errors.append("background color 0 must be present")
    if any(value == 4 for row in grid for value in row):
        errors.append("input color 4 is reserved for the output and must be absent")

    facts = _scene_facts(grid)
    counts = facts["counts"]
    if len(counts) != 2:
        errors.append(f"expected exactly two nonzero colors, found {sorted(counts)}")
    singleton_colors = facts["singleton_colors"]
    repeated_colors = facts["repeated_colors"]
    if len(singleton_colors) != 1:
        errors.append(
            "expected exactly one color with one connected component, "
            f"found {sorted(singleton_colors)}"
        )
    if len(repeated_colors) != 1:
        errors.append(
            "expected exactly one repeated color with multiple components, "
            f"found {sorted(repeated_colors)}"
        )
    if len(repeated_colors) == 1:
        n_repeat = int(counts[repeated_colors[0]])
        if not 2 <= n_repeat <= 4:
            errors.append(f"repeated color must form 2..4 components, got {n_repeat}")
    nonzero = sum(value != 0 for row in grid for value in row)
    if nonzero >= h * w // 2:
        errors.append("non-background cells must occupy less than half the grid")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws and every canonical input lie on this manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned grid."""
    if self_check(grid):
        return {}
    facts = _scene_facts(grid)
    profile = facts.get("size_profile")
    if profile is None:
        return {}
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "n_repeat": int(facts["n_repeat"]),
        "size_profile": str(profile),
        "color_order": str(facts["color_order"]),
        "position_order": str(facts["position_order"]),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror for diagnostics; Racket remains authority."""
    facts = _scene_facts(grid)
    singleton_colors = facts["singleton_colors"]
    if not singleton_colors:
        raise ValueError("no single-component color")
    target_color = min(int(color) for color in singleton_colors)
    return [
        [4 if value == target_color else value for value in row]
        for row in grid
    ]


def _recolor_candidate(grid: list[list[int]], chooser: Callable[[dict[str, object]], int]) -> list[list[int]]:
    facts = _scene_facts(grid)
    chosen = chooser(facts)
    return [[4 if value == chosen else value for value in row] for row in grid]


def _total_cells_by_color(facts: dict[str, object]) -> dict[int, int]:
    components = facts["components"]
    return {
        int(color): sum(len(part) for part in parts)
        for color, parts in components.items()
    }


def _first_seen_colors(grid: list[list[int]]) -> list[int]:
    seen: list[int] = []
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.append(value)
    return seen


def _candidate_fewest_cells(grid):
    return _recolor_candidate(
        grid,
        lambda facts: min(
            _total_cells_by_color(facts),
            key=lambda color: (_total_cells_by_color(facts)[color], color),
        ),
    )


def _candidate_most_cells(grid):
    return _recolor_candidate(
        grid,
        lambda facts: max(
            _total_cells_by_color(facts),
            key=lambda color: (_total_cells_by_color(facts)[color], -color),
        ),
    )


def _candidate_lowest_color(grid):
    return _recolor_candidate(grid, lambda facts: min(facts["components"]))


def _candidate_highest_color(grid):
    return _recolor_candidate(grid, lambda facts: max(facts["components"]))


def _candidate_first_seen(grid):
    color = _first_seen_colors(grid)[0]
    return [[4 if value == color else value for value in row] for row in grid]


def _candidate_last_seen(grid):
    color = _first_seen_colors(grid)[-1]
    return [[4 if value == color else value for value in row] for row in grid]


def _candidate_smallest_object(grid):
    return _recolor_candidate(
        grid,
        lambda facts: min(
            (
                (len(part), min(part), int(color))
                for color, parts in facts["components"].items()
                for part in parts
            )
        )[2],
    )


def _candidate_largest_object(grid):
    return _recolor_candidate(
        grid,
        lambda facts: max(
            (
                (len(part), tuple(-x for x in min(part)), -int(color), int(color))
                for color, parts in facts["components"].items()
                for part in parts
            )
        )[3],
    )


SEMANTIC_RIVALS = {
    "fewest_cells": _candidate_fewest_cells,
    "most_cells": _candidate_most_cells,
    "lowest_color": _candidate_lowest_color,
    "highest_color": _candidate_highest_color,
    "first_seen": _candidate_first_seen,
    "last_seen": _candidate_last_seen,
    "smallest_object": _candidate_smallest_object,
    "largest_object": _candidate_largest_object,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "highest_color": _candidate_highest_color,
}


def _target_and_repeat_areas(grid) -> tuple[int, list[int]]:
    facts = _scene_facts(grid)
    return int(facts["target_area"]), list(facts["repeat_areas"])


def _witness_target_fewer_cells(grid) -> bool:
    facts = _scene_facts(grid)
    return int(facts["target_area"]) < int(facts["repeat_total_area"])


def _witness_target_more_cells(grid) -> bool:
    facts = _scene_facts(grid)
    return int(facts["target_area"]) > int(facts["repeat_total_area"])


def _witness_target_smaller_each(grid) -> bool:
    target, repeats = _target_and_repeat_areas(grid)
    return bool(repeats) and target < min(repeats)


def _witness_target_larger_each(grid) -> bool:
    target, repeats = _target_and_repeat_areas(grid)
    return bool(repeats) and target > max(repeats)


def _witness_target_lower_color(grid) -> bool:
    return _scene_facts(grid).get("color_order") == "target_lower"


def _witness_target_higher_color(grid) -> bool:
    return _scene_facts(grid).get("color_order") == "target_higher"


def _witness_target_first(grid) -> bool:
    return _scene_facts(grid).get("position_order") == "target_first"


def _witness_target_last(grid) -> bool:
    return _scene_facts(grid).get("position_order") == "target_last"


def _witness_two_repeats(grid) -> bool:
    return _scene_facts(grid).get("n_repeat") == 2


def _witness_four_repeats(grid) -> bool:
    return _scene_facts(grid).get("n_repeat") == 4


SEMANTIC_WITNESSES = {
    "target_has_fewer_cells_than_repeated_color": _witness_target_fewer_cells,
    "target_has_more_cells_than_repeated_color": _witness_target_more_cells,
    "target_object_smaller_than_every_repeat_object": _witness_target_smaller_each,
    "target_object_larger_than_every_repeat_object": _witness_target_larger_each,
    "target_numeric_color_is_lower": _witness_target_lower_color,
    "target_numeric_color_is_higher": _witness_target_higher_color,
    "target_is_first_in_reading_order": _witness_target_first,
    "target_is_last_in_reading_order": _witness_target_last,
}

WITNESS_RIVALS = {
    "target_has_fewer_cells_than_repeated_color": ["most_cells"],
    "target_has_more_cells_than_repeated_color": ["fewest_cells"],
    "target_object_smaller_than_every_repeat_object": ["largest_object"],
    "target_object_larger_than_every_repeat_object": ["smallest_object"],
    "target_numeric_color_is_lower": ["highest_color"],
    "target_numeric_color_is_higher": ["lowest_color"],
    "target_is_first_in_reading_order": ["last_seen"],
    "target_is_last_in_reading_order": ["first_seen"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a named rival fits demos but changes query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if not all(rival(pair["input"]) == pair["output"] for pair in demos):
                continue
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name} matches every demonstration but predicts a different query"
                )
        except Exception as exc:
            reasons.append(f"rival {name} raised {type(exc).__name__}: {exc}")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return sample_index % 20


SCHEDULE_PROFILES = tuple(range(20))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis: {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor_index = {1: 0, 5: 1, 9: 2}.get(sample_index % 12)
    if anchor_index is not None:
        anchor_h, anchor_w, _, _, anchor_repeat = _CANONICAL_ANCHORS[anchor_index]
        h = _record_scheduled_int(ctx, "grid_h", 8, 14, anchor_h)
        w = _record_scheduled_int(ctx, "grid_w", 9, 16, anchor_w)
        n_repeat = _record_scheduled_int(ctx, "n_repeat", 2, 4, anchor_repeat)
        default_color_order = "target_higher"
    else:
        h = ctx.draw_int_diff("grid_h", 8, 14)
        w = ctx.draw_int_diff("grid_w", 9, 16)
        n_repeat = _record_scheduled_int(ctx, "n_repeat", 2, 4, 2 + sample_index % 3)
        default_color_order = COLOR_ORDERS[sample_index % len(COLOR_ORDERS)]

    size_profile = _record_scheduled_choice(
        ctx,
        "size_profile",
        SIZE_PROFILES,
        SIZE_PROFILES[sample_index % len(SIZE_PROFILES)],
    )
    color_order = _record_scheduled_choice(
        ctx, "color_order", COLOR_ORDERS, default_color_order
    )
    position_order = _record_scheduled_choice(
        ctx,
        "position_order",
        POSITION_ORDERS,
        POSITION_ORDERS[(sample_index // 2) % len(POSITION_ORDERS)],
    )

    target_color, repeat_color = _choose_colors(
        ctx, color_order=color_order, anchor_index=anchor_index
    )
    grid = _draw_grid(
        h=h,
        w=w,
        target_color=target_color,
        repeat_color=repeat_color,
        n_repeat=n_repeat,
        size_profile=size_profile,
        position_order=position_order,
        rng=ctx.draw_rng("layout"),
        sample_index=sample_index,
    )
    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_repeat": n_repeat,
        "size_profile": size_profile,
        "color_order": color_order,
        "position_order": position_order,
    }
    if observed != expected:
        raise ValueError(f"axis observation mismatch: expected {expected}, got {observed}")
    return grid
