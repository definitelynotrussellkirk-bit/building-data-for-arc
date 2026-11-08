"""Generator for arc_puzzle_bank_21_set14_s:S14_H6.

The grid is split into equal vertical panels by full color-5 columns.  Each
panel contains one monochrome connected object.  A strict majority of panels
share the same per-row cell-count profile, while their normalized shapes are
deliberately different.  The answer is the majority profile rendered as a
left-justified color-8 histogram.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
from itertools import combinations, product
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "337ce626a05f"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "c75668610a13"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid is split into 3-5 equal vertical panels by full "
    "color-5 divider columns. Each panel contains one monochrome connected "
    "object. A strict majority of panel objects share the same row-profile "
    "(cell counts from top bbox row to bottom), but the agreeing objects have "
    "different normalized shapes. Ignore the outlier profiles and render the "
    "majority profile as a left-justified cyan(8) histogram."
)

INVARIANTS = [
    "background is 0 and full-height color-5 columns are the only dividers",
    "all panels have equal width and contain exactly one monochrome 4-connected object",
    "one row-profile occurs in strictly more than half of the panels",
    "at least one panel has a different profile, so consensus is necessary",
    "ordinary draws use distinct normalized shapes for all majority-profile panels",
]

# Coupled geometry is represented by one exact, observable layout axis instead
# of independent height/width/panel-count knobs with invalid Cartesian products.
AXES = {
    "layout": {
        "type": "str",
        "default": "weighted canonical3/compact3/compact4/compact5",
        "valid": "canonical3|compact3|compact4|compact5",
    },
    "grid_h": {"type": "int", "default": "weighted 8..12", "valid": "8..12"},
    "profile_height": {"type": "int", "default": "weighted 3..7", "valid": "3..7"},
    "profile_peak": {"type": "int", "default": "weighted 3..4", "valid": "3..4"},
    "profile_kind": {
        "type": "str",
        "default": "weighted canonical families",
        "valid": "ramp_up|ramp_down|bowl|valley|left_plateau|right_plateau|center_peak|zig_up|zig_down",
    },
    "color_mode": {
        "type": "str",
        "default": "weighted all_distinct/majority_shared",
        "valid": "all_distinct|majority_shared",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_LAYOUTS = {
    "canonical3": (3, 7),   # canonical 23-column envelope
    "compact3": (3, 6),
    "compact4": (4, 6),
    "compact5": (5, 5),
}
_OBJECT_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_PROFILE_KINDS = (
    "ramp_up", "ramp_down", "bowl", "valley",
    "left_plateau", "right_plateau", "center_peak", "zig_up", "zig_down",
)
_COLOR_MODES = ("all_distinct", "majority_shared")
SCHEDULE_PROFILES = ("anchor", "first_outlier", "large_outlier", "color_trap")

Grid = list[list[int]]
Cell = tuple[int, int]
Profile = tuple[int, ...]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Four-slot schedule; every four-example sliding window sees all slots."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _profile(kind: str, height: int, peak: int) -> Profile:
    if kind == "ramp_up":
        return tuple(1 + ((peak - 1) * r) // (height - 1) for r in range(height))
    if kind == "ramp_down":
        return tuple(reversed(_profile("ramp_up", height, peak)))
    if kind == "bowl":
        return (peak, *([1] * (height - 2)), peak)
    if kind == "valley":
        return tuple(max(1, peak - min(r, height - 1 - r)) for r in range(height))
    if kind == "left_plateau":
        return (*([peak] * (height - 1)), 1)
    if kind == "right_plateau":
        return (1, *([peak] * (height - 1)))
    if kind == "center_peak":
        middle = {(height - 1) // 2, height // 2}
        return tuple(peak if r in middle else 1 for r in range(height))
    if kind == "zig_up":
        motif = (1, peak, peak - 1)
        return tuple(motif[r % len(motif)] for r in range(height))
    if kind == "zig_down":
        return tuple(reversed(_profile("zig_up", height, peak)))
    raise ValueError(f"unknown profile kind {kind!r}")


def _profile_kind(profile: Profile) -> str:
    height = len(profile)
    peak = max(profile)
    matches = [kind for kind in _PROFILE_KINDS if _profile(kind, height, peak) == profile]
    if len(matches) != 1:
        raise ValueError(f"profile is not uniquely classified: {profile!r} -> {matches!r}")
    return matches[0]


def _connected(cells: set[Cell]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == len(cells)


@lru_cache(maxsize=None)
def _shapes_for_profile(profile: Profile) -> tuple[tuple[Cell, ...], ...]:
    """Enumerate connected normalized shapes with exactly this row-profile."""
    width = max(profile)
    row_options = [tuple(combinations(range(width), count)) for count in profile]
    shapes: list[tuple[Cell, ...]] = []
    for rows in product(*row_options):
        cells = {(r, c) for r, columns in enumerate(rows) for c in columns}
        if _connected(cells):
            shapes.append(tuple(sorted(cells)))
    return tuple(shapes)


def _simple_shape(profile: Profile, variant: int) -> tuple[Cell, ...]:
    """Construct a connected outlier shape; profile uniqueness carries semantics."""
    width = max(profile)
    starts: list[int] = []
    previous_start = 0
    previous_width = profile[0]
    for r, row_width in enumerate(profile):
        candidates = list(range(width - row_width + 1))
        if variant % 2:
            candidates.reverse()
        legal = [
            start
            for start in candidates
            if r == 0
            or max(start, previous_start)
            <= min(start + row_width - 1, previous_start + previous_width - 1)
        ]
        start = legal[(variant + r) % len(legal)]
        starts.append(start)
        previous_start = start
        previous_width = row_width
    return tuple(
        (r, c)
        for r, (start, row_width) in enumerate(zip(starts, profile))
        for c in range(start, start + row_width)
    )


def _components(panel: Grid) -> list[set[Cell]]:
    cells = {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}
    components: list[set[Cell]] = []
    while cells:
        start = next(iter(cells))
        component = {start}
        queue = deque([start])
        cells.remove(start)
        while queue:
            r, c = queue.popleft()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in cells:
                    cells.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _object_record(panel: Grid, panel_index: int) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    components = _components(panel)
    if len(components) != 1:
        return None, [f"panel {panel_index} must contain exactly one object, found {len(components)}"]
    cells = components[0]
    colors = {panel[r][c] for r, c in cells}
    if len(colors) != 1:
        errors.append(f"panel {panel_index} object is not monochrome: {sorted(colors)}")
    color = next(iter(colors))
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    profile = tuple(sum((r, c) in cells for c in range(len(panel[0]))) for r in range(r1, r2 + 1))
    if any(count == 0 for count in profile):
        errors.append(f"panel {panel_index} object has an empty row inside its bbox")
    shape = tuple(sorted((r - r1, c - c1) for r, c in cells))
    return {
        "panel_index": panel_index,
        "color": color,
        "cells": tuple(sorted(cells)),
        "size": len(cells),
        "bbox": (r1, c1, r2, c2),
        "profile": profile,
        "shape": shape,
    }, errors


def _analyze(grid: Grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty rectangular list of rows"]}
    height = len(grid)
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid is ragged"]}
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC bounds: {height}x{width}")
    if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid contains a non-integer or a color outside 0..9")

    divider_columns = [c for c in range(width) if all(grid[r][c] == 5 for r in range(height))]
    if not 2 <= len(divider_columns) <= 4:
        errors.append(f"expected 2..4 full color-5 dividers, found {len(divider_columns)}")
    if any(grid[r][c] == 5 for r in range(height) for c in range(width) if c not in divider_columns):
        errors.append("color 5 occurs outside a full-height divider column")

    bounds = (-1, *divider_columns, width)
    panel_ranges = [(bounds[i] + 1, bounds[i + 1]) for i in range(len(bounds) - 1)]
    panel_widths = [right - left for left, right in panel_ranges]
    if any(panel_width <= 0 for panel_width in panel_widths):
        errors.append("adjacent or edge dividers create an empty panel")
    if panel_widths and len(set(panel_widths)) != 1:
        errors.append(f"panel widths are not equal: {panel_widths}")

    records: list[dict[str, Any]] = []
    if not errors:
        for index, (left, right) in enumerate(panel_ranges):
            panel = [row[left:right] for row in grid]
            record, panel_errors = _object_record(panel, index)
            errors.extend(panel_errors)
            if record is not None:
                record["left"] = left
                records.append(record)

    majority_profile: Profile | None = None
    majority_indices: list[int] = []
    outlier_indices: list[int] = []
    if records and len(records) == len(panel_ranges):
        counts = Counter(record["profile"] for record in records)
        winners = [profile for profile, count in counts.items() if count > len(records) // 2]
        if len(winners) != 1:
            errors.append(f"expected one strict-majority row-profile, found {counts}")
        else:
            majority_profile = winners[0]
            majority_indices = [i for i, record in enumerate(records) if record["profile"] == majority_profile]
            outlier_indices = [i for i in range(len(records)) if i not in majority_indices]
            if not outlier_indices:
                errors.append("all panels share the profile; the majority operation is hidden")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "divider_columns": divider_columns,
        "panel_ranges": panel_ranges,
        "panel_widths": panel_widths,
        "records": records,
        "majority_profile": majority_profile,
        "majority_indices": majority_indices,
        "outlier_indices": outlier_indices,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _color_mode(info: dict[str, Any]) -> str:
    records = info["records"]
    majority = info["majority_indices"]
    outliers = info["outlier_indices"]
    colors = [record["color"] for record in records]
    if len(set(colors)) == len(colors):
        return "all_distinct"
    majority_colors = {colors[index] for index in majority}
    outlier_colors = [colors[index] for index in outliers]
    if (
        len(majority_colors) == 1
        and all(color not in majority_colors for color in outlier_colors)
        and len(set(outlier_colors)) == len(outlier_colors)
    ):
        return "majority_shared"
    raise ValueError(f"color assignment does not match a declared mode: {colors}")


def observe_overrides(grid) -> dict[str, int | str]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    panel_width = info["panel_widths"][0]
    layout_matches = [name for name, value in _LAYOUTS.items() if value == (len(info["records"]), panel_width)]
    if len(layout_matches) != 1:
        raise ValueError(f"unrecognized layout: panels={len(info['records'])}, panel_width={panel_width}")
    profile = info["majority_profile"]
    return {
        "layout": layout_matches[0],
        "grid_h": info["height"],
        "profile_height": len(profile),
        "profile_peak": max(profile),
        "profile_kind": _profile_kind(profile),
        "color_mode": _color_mode(info),
    }


def semantic_observables(grid) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        return {"valid": False, "errors": info["errors"]}
    return {
        "valid": True,
        **observe_overrides(grid),
        "majority_profile": info["majority_profile"],
        "panel_profiles": [record["profile"] for record in info["records"]],
        "panel_shapes": [record["shape"] for record in info["records"]],
        "panel_sizes": [record["size"] for record in info["records"]],
        "panel_colors": [record["color"] for record in info["records"]],
        "majority_indices": info["majority_indices"],
        "outlier_indices": info["outlier_indices"],
    }


def _histogram(profile: Iterable[int]) -> Grid:
    profile = tuple(profile)
    return [[8 if c < count else 0 for c in range(max(profile))] for count in profile]


def rule_mirror(grid) -> Grid:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return _histogram(info["majority_profile"])


def _rival_first_panel(grid) -> Grid:
    info = _analyze(grid)
    return _histogram(info["records"][0]["profile"])


def _rival_largest_object(grid) -> Grid:
    info = _analyze(grid)
    record = max(info["records"], key=lambda row: row["size"])
    return _histogram(record["profile"])


def _rival_modal_exact_shape(grid) -> Grid:
    info = _analyze(grid)
    counts = Counter(record["shape"] for record in info["records"])
    best_count = max(counts.values())
    record = next(record for record in info["records"] if counts[record["shape"]] == best_count)
    return _histogram(record["profile"])


def _rival_lowest_color(grid) -> Grid:
    info = _analyze(grid)
    record = min(info["records"], key=lambda row: row["color"])
    return _histogram(record["profile"])


def _rival_largest_profile_total(grid) -> Grid:
    info = _analyze(grid)
    record = max(info["records"], key=lambda row: sum(row["profile"]))
    return _histogram(record["profile"])


SEMANTIC_RIVALS = {
    "first_panel_profile": _rival_first_panel,
    "largest_object_profile": _rival_largest_object,
    "modal_exact_shape": _rival_modal_exact_shape,
    "lowest_color_profile": _rival_lowest_color,
    "largest_profile_total": _rival_largest_profile_total,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _rival_differs(name: str, grid: Grid) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


def _distinct_majority_shapes(grid: Grid) -> bool:
    obs = semantic_observables(grid)
    if not obs.get("valid"):
        return False
    shapes = [obs["panel_shapes"][index] for index in obs["majority_indices"]]
    return len(set(shapes)) == len(shapes)


SEMANTIC_WITNESSES = {
    "first_panel_shortcut_counterexample": lambda grid: _rival_differs("first_panel_profile", grid),
    "largest_object_shortcut_counterexample": lambda grid: _rival_differs("largest_object_profile", grid),
    "exact_shape_shortcut_counterexample": lambda grid: (
        _distinct_majority_shapes(grid) and _rival_differs("modal_exact_shape", grid)
    ),
    "lowest_color_shortcut_counterexample": lambda grid: _rival_differs("lowest_color_profile", grid),
    "largest_total_shortcut_counterexample": lambda grid: _rival_differs("largest_profile_total", grid),
}
WITNESS_RIVALS = {
    "first_panel_shortcut_counterexample": ["first_panel_profile"],
    "largest_object_shortcut_counterexample": ["largest_object_profile"],
    "exact_shape_shortcut_counterexample": ["modal_exact_shape"],
    "lowest_color_shortcut_counterexample": ["lowest_color_profile"],
    "largest_total_shortcut_counterexample": ["largest_profile_total"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives every demo."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    query_input = query.get("input") if isinstance(query, dict) else None
    if query_input is None or self_check(query_input):
        return ["query input is not a lawful majority-profile scene"]
    query_truth = rule_mirror(query_input)

    checked: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is malformed")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the rule mirror")
            continue
        checked.append(demo)
    if reasons:
        return sorted(set(reasons))

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(demo["input"]) == demo["output"] for demo in checked)
        if survives and rival(query_input) != query_truth:
            reasons.append(f"competing rule {name!r} matches every demo but changes the query")
    return sorted(set(reasons))


def _weighted_axis_options(difficulty: str | None) -> dict[str, list[Any]]:
    # Every legal value remains available in every band; repetition only changes
    # ordinary-draw frequency and keeps canonical scale well represented.
    if difficulty == "easy":
        return {
            "layout": ["canonical3"] * 7 + ["compact3", "compact4", "compact5"],
            "grid_h": [8, 8, 8, 8, 9, 9, 9, 10, 11, 12],
            "profile_height": [3, 3, 3, 4, 4, 5, 6, 7],
            "profile_peak": [3, 3, 3, 4],
            "profile_kind": list(_PROFILE_KINDS),
            "color_mode": ["all_distinct", "all_distinct", "all_distinct", "majority_shared"],
        }
    if difficulty == "hard":
        return {
            "layout": ["canonical3"] * 6 + ["compact3", "compact4", "compact5"],
            "grid_h": [8, 8, 8, 9, 9, 9, 10, 11, 12],
            "profile_height": [3, 4, 5, 6, 7, 7],
            "profile_peak": [3, 4, 4],
            "profile_kind": list(_PROFILE_KINDS),
            "color_mode": ["all_distinct", "all_distinct", "all_distinct", "majority_shared", "majority_shared"],
        }
    return {
        "layout": ["canonical3"] * 6 + ["compact3", "compact4", "compact5"],
        "grid_h": [8, 8, 8, 9, 9, 9, 10, 11, 12],
        "profile_height": [3, 3, 4, 4, 5, 6, 7],
        "profile_peak": [3, 3, 3, 4],
        "profile_kind": list(_PROFILE_KINDS),
        "color_mode": ["all_distinct", "all_distinct", "all_distinct", "majority_shared"],
    }


@lru_cache(maxsize=None)
def _outlier_profiles_by_total(max_count: int) -> dict[int, tuple[Profile, ...]]:
    """Enumerate the small legal profile universe once per panel width."""
    buckets: dict[int, list[Profile]] = {}
    for height in range(2, 8):
        for values in product(range(1, max_count + 1), repeat=height):
            profile = tuple(values)
            buckets.setdefault(sum(profile), []).append(profile)
    return {total: tuple(rows) for total, rows in buckets.items()}


def _outlier_profile(
    rng,
    *,
    relation: str,
    majority: Profile,
    max_count: int,
    used: set[Profile],
) -> Profile:
    buckets = _outlier_profiles_by_total(max_count)
    majority_total = sum(majority)
    if relation == "smaller":
        totals = [total for total in buckets if total < majority_total]
    elif relation == "same":
        totals = [majority_total] if majority_total in buckets else []
    elif relation == "larger":
        totals = [total for total in buckets if total > majority_total]
    else:
        raise ValueError(f"unknown outlier relation {relation!r}")
    rng.shuffle(totals)
    for total in totals:
        pool = buckets[total]
        start = rng.randrange(len(pool))
        for offset in range(len(pool)):
            candidate = pool[(start + offset) % len(pool)]
            if candidate != majority and candidate not in used:
                return candidate
    raise ValueError(f"no {relation} outlier profile for majority {majority}")


def _outlier_positions(n_panels: int, slot: str, rng) -> list[int]:
    outlier_count = n_panels - (n_panels // 2 + 1)
    if slot in {"first_outlier", "color_trap"}:
        required = 0
    elif slot == "large_outlier":
        required = n_panels // 2
    else:
        required = n_panels - 1
    positions = [required]
    remaining = [index for index in range(n_panels) if index != required]
    rng.shuffle(remaining)
    positions.extend(remaining[: outlier_count - 1])
    return sorted(positions)


def _assign_colors(
    rng,
    *,
    n_panels: int,
    majority_indices: list[int],
    outlier_indices: list[int],
    color_mode: str,
    slot: str,
) -> list[int]:
    colors = [0] * n_panels
    pool = list(_OBJECT_COLORS)
    rng.shuffle(pool)
    low_outlier = outlier_indices[0] if slot == "color_trap" else None
    if low_outlier is not None:
        colors[low_outlier] = 1
        pool.remove(1)

    if color_mode == "all_distinct":
        for index in range(n_panels):
            if colors[index] == 0:
                colors[index] = pool.pop()
        return colors

    majority_color = next(color for color in pool if color != 1)
    pool.remove(majority_color)
    for index in majority_indices:
        colors[index] = majority_color
    for index in outlier_indices:
        if colors[index] == 0:
            colors[index] = pool.pop()
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    options = _weighted_axis_options(difficulty)
    layout = ctx.draw_choice("layout", options["layout"])
    grid_h = ctx.draw_choice("grid_h", options["grid_h"])
    profile_height = ctx.draw_choice("profile_height", options["profile_height"])
    profile_peak = ctx.draw_choice("profile_peak", options["profile_peak"])
    profile_kind = ctx.draw_choice("profile_kind", options["profile_kind"])
    color_mode = ctx.draw_choice("color_mode", options["color_mode"])

    n_panels, panel_width = _LAYOUTS[layout]
    majority_profile = _profile(profile_kind, profile_height, profile_peak)
    majority_count = n_panels // 2 + 1
    shape_pool = list(_shapes_for_profile(majority_profile))
    if len(shape_pool) < majority_count:
        raise AssertionError(
            f"profile {majority_profile} has only {len(shape_pool)} distinct shapes, "
            f"need {majority_count}"
        )
    shape_rng = ctx.draw_rng("majority_shapes")
    shape_rng.shuffle(shape_pool)
    majority_shapes = shape_pool[:majority_count]

    slot = schedule_profile(seed, sample_index, difficulty)
    layout_rng = ctx.draw_rng("panel_roles")
    outlier_indices = _outlier_positions(n_panels, slot, layout_rng)
    majority_indices = [index for index in range(n_panels) if index not in outlier_indices]

    relation_by_slot = {
        "anchor": "smaller",
        "first_outlier": "same",
        "large_outlier": "larger",
        "color_trap": "smaller",
    }
    relation_cycle = (relation_by_slot[slot], "larger", "same", "smaller")
    outlier_rng = ctx.draw_rng("outlier_profiles")
    used_profiles = {majority_profile}
    outlier_profiles: dict[int, Profile] = {}
    for rank, panel_index in enumerate(outlier_indices):
        relation = relation_cycle[rank % len(relation_cycle)]
        profile = _outlier_profile(
            outlier_rng,
            relation=relation,
            majority=majority_profile,
            max_count=min(4, panel_width - 1),
            used=used_profiles,
        )
        used_profiles.add(profile)
        outlier_profiles[panel_index] = profile

    colors = _assign_colors(
        ctx.draw_rng("colors"),
        n_panels=n_panels,
        majority_indices=majority_indices,
        outlier_indices=outlier_indices,
        color_mode=color_mode,
        slot=slot,
    )

    width = n_panels * panel_width + (n_panels - 1)
    grid = full_grid(grid_h, width, 0)
    for divider_rank in range(n_panels - 1):
        column = divider_rank * (panel_width + 1) + panel_width
        for row in range(grid_h):
            grid[row][column] = 5

    placement_rng = ctx.draw_rng("placements")
    majority_shape_by_panel = dict(zip(majority_indices, majority_shapes))
    for panel_index in range(n_panels):
        if panel_index in majority_shape_by_panel:
            shape = majority_shape_by_panel[panel_index]
        else:
            shape = _simple_shape(outlier_profiles[panel_index], panel_index + sample_index)
        shape_height = max(r for r, _ in shape) + 1
        shape_width = max(c for _, c in shape) + 1
        row_offset = placement_rng.randint(0, grid_h - shape_height)
        col_offset = placement_rng.randint(0, panel_width - shape_width)
        panel_left = panel_index * (panel_width + 1)
        for r, c in shape:
            grid[row_offset + r][panel_left + col_offset + c] = colors[panel_index]

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "layout": layout,
        "grid_h": grid_h,
        "profile_height": profile_height,
        "profile_peak": profile_peak,
        "profile_kind": profile_kind,
        "color_mode": color_mode,
    }
    if observed != requested:
        raise AssertionError(f"axis observation mismatch: requested={requested}, observed={observed}")
    if not _distinct_majority_shapes(grid):
        raise AssertionError("ordinary draw failed to use distinct majority shapes")
    return grid
