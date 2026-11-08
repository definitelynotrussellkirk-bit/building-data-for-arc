"""Generator for ARC task 69889d6e.

A single red cell (2) on the bottom row seeds a two-cell-wide staircase that
climbs one row at a time while drifting right.  On each row, blue blockers (1)
occupying either prospective staircase cell push the staircase to the first
column immediately to their right.  The displaced row is connected to the
previous row by a horizontal red bridge.  Blue cells that are not in the two
prospective staircase columns are irrelevant and remain unchanged.

Default lessons use a four-slot schedule: clear baseline, one-cell deflection,
adjacent-blocker multi-cell deflection, and an off-path decoy.  Every four
consecutive demonstrations therefore expose both the positive mechanism and
the key negative control.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4b1c57a69862"
TASK_ID = "4b1c57a69862"
VERSION = "3.0.0"
RULE_HASH = "a731b6ee66cd"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "One bottom-row red seed grows a two-cell-wide up-right staircase. "
    "Blue blockers in either prospective path cell shift that row to the "
    "first free column on their right and create a horizontal red bridge; "
    "off-path blue cells are preserved and do not affect the path."
)

INVARIANTS = [
    "background is 0, with exactly one red seed (2) on the bottom row",
    "zero to four blue blockers (1) lie above the seed",
    "the staircase has at least four in-bounds rows and changes every lawful input",
    "at most one blue blocker is deliberately off-path, and it coexists with a real deflection",
    "blocker runs cause one-, two-, or three-column right shifts; at most two rows shift",
]

SCENE_PROFILES = (
    "canonical_clear_left",
    "canonical_clear_right",
    "canonical_single",
    "canonical_single_then_double",
    "canonical_double_then_single",
    "generalized_clear",
    "generalized_single",
    "generalized_double",
    "generalized_chain",
    "generalized_mixed",
    "generalized_decoy",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot semantic schedule with keyed variation",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Exact observable profile: canonical clear/single/mixed scenes or "
            "generalized clear, one-, two-, three-cell, mixed, and off-path-decoy scenes."
        ),
    }
}

SCHEDULE_PROFILES = ("clear", "single", "multi", "decoy")
_SLOT_OPTIONS = {
    "clear": (
        "canonical_clear_left",
        "canonical_clear_right",
        "generalized_clear",
    ),
    "single": ("canonical_single", "generalized_single"),
    "multi": (
        "canonical_single_then_double",
        "canonical_double_then_single",
        "generalized_double",
        "generalized_chain",
        "generalized_mixed",
    ),
    "decoy": ("generalized_decoy",),
}

Grid = list[list[int]]
Cell = tuple[int, int]

_CANONICAL_SPECS: dict[str, tuple[int, int, int, tuple[Cell, ...]]] = {
    "canonical_clear_left": (10, 10, 1, ()),
    "canonical_clear_right": (10, 10, 3, ()),
    "canonical_single": (10, 10, 1, ((6, 3),)),
    "canonical_single_then_double": (10, 10, 0, ((7, 1), (5, 4), (5, 5))),
    "canonical_double_then_single": (10, 10, 1, ((6, 3), (6, 4), (4, 7))),
}


def _canonical_signature(grid: Grid) -> tuple[Any, ...] | None:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(seeds) != 1:
        return None
    seed_r, seed_c = seeds[0]
    blockers = tuple(
        sorted(
            (r - seed_r, c - seed_c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 1
        )
    )
    return len(grid), len(grid[0]), seed_r, seed_c, blockers


_CANONICAL_SIGNATURE_TO_PROFILE = {
    (
        h,
        w,
        h - 1,
        seed_col,
        tuple(sorted((r - (h - 1), c - seed_col) for r, c in blockers)),
    ): profile
    for profile, (h, w, seed_col, blockers) in _CANONICAL_SPECS.items()
}


def canonical_profile_signature(grid: Grid) -> tuple[Any, ...] | None:
    """Stable strict-profile signature shared by tests and review censuses."""
    signature = _canonical_signature(grid)
    return signature if signature in _CANONICAL_SIGNATURE_TO_PROFILE else None


def _trace(grid: Grid) -> dict[str, Any]:
    """Trace the canonical path and identify blockers that actually cause shifts."""
    h, w = len(grid), len(grid[0])
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(seeds) != 1:
        return {
            "seed": None,
            "left_cols": {},
            "shifts": [],
            "used_blockers": set(),
            "off_path_blockers": set(),
            "in_bounds_rows": 0,
            "reaches_top": False,
        }
    seed_r, seed_c = seeds[0]
    blue_by_row: dict[int, list[int]] = {}
    all_blockers: set[Cell] = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1:
                blue_by_row.setdefault(r, []).append(c)
                all_blockers.add((r, c))

    left_cols: dict[int, int] = {}
    shifts: list[dict[str, Any]] = []
    used: set[Cell] = set()
    cl = seed_c
    row = seed_r - 1
    while row >= 0 and cl < w:
        before = cl
        blues = sorted(blue_by_row.get(row, ()))
        while cl in blues or cl + 1 in blues:
            hits = [bc for bc in blues if bc == cl or bc == cl + 1]
            used.update((row, bc) for bc in hits)
            cl = max(hits) + 1
        left_cols[row] = cl
        if cl > before:
            shifts.append(
                {
                    "row": row,
                    "before": before,
                    "after": cl,
                    "distance": cl - before,
                    "blockers": tuple(blues),
                }
            )
        cl += 1
        row -= 1

    in_bounds_rows = sum(left < w for left in left_cols.values())
    return {
        "seed": (seed_r, seed_c),
        "left_cols": left_cols,
        "shifts": shifts,
        "used_blockers": used,
        "off_path_blockers": all_blockers - used,
        "in_bounds_rows": in_bounds_rows,
        "reaches_top": 0 in left_cols and left_cols[0] < w,
    }


def _climb(grid: Grid) -> Grid:
    """Faithful Python transcription used only for validation and rivals."""
    h, w = len(grid), len(grid[0])
    red_r = red_c = None
    blue_map: dict[int, list[int]] = {}
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 2:
                red_r, red_c = r, c
            elif grid[r][c] == 1:
                blue_map.setdefault(r, []).append(c)
    if red_r is None or red_c is None:
        return [row[:] for row in grid]

    result = [row[:] for row in grid]
    left_cols: dict[int, int] = {}
    cl = red_c
    row = red_r - 1
    while not (row < 0 or cl >= w):
        blues = blue_map.get(row, [])
        while cl in blues or cl + 1 in blues:
            cl = 1 + max(bc for bc in blues if bc == cl or bc == cl + 1)
        left_cols[row] = cl
        cl += 1
        row -= 1

    prev_cl = red_c
    row = red_r - 1
    while row >= 0 and row in left_cols:
        cl_here = left_cols[row]
        if cl_here > prev_cl + 1:
            bridge_row = row + 1
            for c in range(prev_cl + 1, cl_here + 1):
                if 0 <= c < w and result[bridge_row][c] == 0:
                    result[bridge_row][c] = 2
        if cl_here < w:
            result[row][cl_here] = 2
        if cl_here + 1 < w:
            result[row][cl_here + 1] = 2
        prev_cl = cl_here
        row -= 1
    return result


def _climb_rival(
    grid: Grid,
    *,
    shift_policy: str = "canonical",
    bridge: bool = True,
) -> Grid:
    """Parameterized rival family; never used as the output authority."""
    h, w = len(grid), len(grid[0])
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not seeds:
        return [row[:] for row in grid]
    red_r, red_c = seeds[-1]
    blue_map: dict[int, list[int]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1:
                blue_map.setdefault(r, []).append(c)

    result = [row[:] for row in grid]
    left_cols: dict[int, int] = {}
    cl = red_c
    for row in range(red_r - 1, -1, -1):
        if cl >= w:
            break
        blues = sorted(blue_map.get(row, ()))
        if shift_policy == "ignore":
            pass
        elif shift_policy == "single":
            if cl in blues or cl + 1 in blues:
                cl += 1
        elif shift_policy == "any_row":
            if blues:
                cl = max(blues) + 1
        elif shift_policy == "always":
            cl += 1
        else:
            while cl in blues or cl + 1 in blues:
                cl = max(bc for bc in blues if bc == cl or bc == cl + 1) + 1
        left_cols[row] = cl
        cl += 1

    prev_cl = red_c
    for row in range(red_r - 1, -1, -1):
        if row not in left_cols:
            break
        cl_here = left_cols[row]
        if bridge and cl_here > prev_cl + 1:
            for c in range(prev_cl + 1, cl_here + 1):
                if 0 <= c < w and result[row + 1][c] == 0:
                    result[row + 1][c] = 2
        if cl_here < w:
            result[row][cl_here] = 2
        if cl_here + 1 < w:
            result[row][cl_here + 1] = 2
        prev_cl = cl_here
    return result


def _rival_ignore_blockers(grid: Grid) -> Grid:
    return _climb_rival(grid, shift_policy="ignore")


def _rival_single_step(grid: Grid) -> Grid:
    return _climb_rival(grid, shift_policy="single")


def _rival_no_bridge(grid: Grid) -> Grid:
    return _climb_rival(grid, bridge=False)


def _rival_shift_on_any_blue_row(grid: Grid) -> Grid:
    return _climb_rival(grid, shift_policy="any_row")


def _rival_always_shift(grid: Grid) -> Grid:
    return _climb_rival(grid, shift_policy="always")


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "ignore_blockers": _rival_ignore_blockers,
    "single_step_per_blocked_row": _rival_single_step,
    "shift_without_bridge": _rival_no_bridge,
    "shift_on_any_blue_row": _rival_shift_on_any_blue_row,
    "always_extra_shift": _rival_always_shift,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _canonical_grid(profile: str) -> Grid:
    h, w, seed_col, blockers = _CANONICAL_SPECS[profile]
    grid = full_grid(h, w, 0)
    grid[h - 1][seed_col] = 2
    for r, c in blockers:
        grid[r][c] = 1
    return grid


def _generalized_dimensions(ctx, band: str) -> tuple[int, int, int]:
    if band == "easy":
        h = ctx.draw_rng("height_easy").randint(11, 13)
    elif band == "hard":
        h = ctx.draw_rng("height_hard").randint(18, 22)
    else:
        h = ctx.draw_rng("height_medium").randint(14, 17)
    extra = ctx.draw_rng(f"width_extra_{band}").randint(6, 8)
    w = min(30, h + extra)
    seed_col = ctx.draw_rng(f"seed_col_{band}").randint(0, 2)
    return h, w, seed_col


def _generalized_grid(profile: str, ctx, band: str) -> Grid:
    h, w, seed_col = _generalized_dimensions(ctx, band)
    seed_r = h - 1
    grid = full_grid(h, w, 0)
    grid[seed_r][seed_col] = 2

    if profile == "generalized_clear":
        event_runs: dict[int, int] = {}
    elif profile == "generalized_single":
        event_runs = {ctx.draw_rng("single_step").randint(3, 5): 1}
    elif profile == "generalized_double":
        event_runs = {ctx.draw_rng("double_step").randint(3, 5): 2}
    elif profile == "generalized_chain":
        event_runs = {ctx.draw_rng("chain_step").randint(3, 5): 3}
    elif profile == "generalized_mixed":
        event_runs = {2: 1, 5: 2}
    elif profile == "generalized_decoy":
        event_runs = {4: 1}
    else:
        raise ValueError(f"unknown generalized profile {profile!r}")

    cl = seed_col
    for step in range(1, seed_r + 1):
        row = seed_r - step
        run_length = event_runs.get(step, 0)
        if run_length:
            if cl + run_length - 1 >= w:
                raise ValueError(
                    f"profile {profile} cannot place blocker run length {run_length} "
                    f"at row {row}, column {cl}, width {w}"
                )
            for c in range(cl, cl + run_length):
                grid[row][c] = 1
            cl += run_length
        cl += 1
        if cl >= w:
            break

    if profile == "generalized_decoy":
        decoy_row = seed_r - 2
        decoy_col = w - 1
        if grid[decoy_row][decoy_col] != 0:
            raise ValueError("decoy placement collided with a blocker")
        grid[decoy_row][decoy_col] = 1
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    if "scene_profile" in overrides:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        slot = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", _SLOT_OPTIONS[slot])

    if profile in _CANONICAL_SPECS:
        grid = _canonical_grid(profile)
    else:
        band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
        grid = _generalized_grid(profile, ctx, band)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid {profile} scene: {errors}")
    observed = observe_overrides(grid)
    if observed.get("scene_profile") != profile:
        raise ValueError(
            f"constructed profile {profile!r} observed as {observed.get('scene_profile')!r}"
        )
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]

    height = len(grid)
    errors: list[str] = []
    if not (10 <= height <= 30 and 10 <= width <= 30):
        errors.append(f"dims {height}x{width} outside supported 10..30 range")
    invalid = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or value not in {0, 1, 2}
    ]
    if invalid:
        errors.append("grid contains a non-integer or a color outside {0,1,2}")

    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(seeds) != 1:
        errors.append(f"expected exactly one red seed, found {len(seeds)}")
        return errors
    seed_r, seed_c = seeds[0]
    if seed_r != height - 1:
        errors.append("red seed must lie on the bottom row")
    if not 0 <= seed_c <= 3:
        errors.append(f"red seed column {seed_c} is outside the lower-left 0..3 band")

    blockers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if len(blockers) > 4:
        errors.append(f"expected at most four blue blockers, found {len(blockers)}")
    if any(r >= seed_r for r, _ in blockers):
        errors.append("all blue blockers must lie strictly above the seed")

    trace = _trace(grid)
    shifts = trace["shifts"]
    off_path = trace["off_path_blockers"]
    if trace["in_bounds_rows"] < 4:
        errors.append(
            f"staircase has only {trace['in_bounds_rows']} in-bounds rows; need at least four"
        )
    if len(shifts) > 2:
        errors.append(f"expected at most two shifting rows, found {len(shifts)}")
    if any(not 1 <= shift["distance"] <= 3 for shift in shifts):
        errors.append("blocker run causes a shift outside the supported one-to-three columns")
    if len(off_path) > 1:
        errors.append(
            f"at most one blocker may be off-path, found {len(off_path)}: {sorted(off_path)}"
        )
    if off_path and not shifts:
        errors.append("an off-path decoy requires at least one real path deflection")
    if _climb(grid) == grid:
        errors.append("canonical rule is identity on this scene")
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    signature = _canonical_signature(grid)
    if signature in _CANONICAL_SIGNATURE_TO_PROFILE:
        return {"scene_profile": _CANONICAL_SIGNATURE_TO_PROFILE[signature]}
    if self_check(grid):
        return {"scene_profile": None}

    trace = _trace(grid)
    distances = [shift["distance"] for shift in trace["shifts"]]
    blocker_count = sum(value == 1 for row in grid for value in row)
    off_path_count = len(trace["off_path_blockers"])
    if blocker_count == 0 and not distances:
        profile = "generalized_clear"
    elif distances == [1] and blocker_count == 1 and off_path_count == 0:
        profile = "generalized_single"
    elif distances == [2] and blocker_count == 2 and off_path_count == 0:
        profile = "generalized_double"
    elif distances == [3] and blocker_count == 3 and off_path_count == 0:
        profile = "generalized_chain"
    elif distances == [1, 2] and blocker_count == 3 and off_path_count == 0:
        profile = "generalized_mixed"
    elif distances == [1] and blocker_count == 2 and off_path_count == 1:
        profile = "generalized_decoy"
    else:
        profile = None
    return {"scene_profile": profile}


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature is None:
        return ["scene does not match one of the five exact canonical input signatures"]
    return []


def _is_clear(grid: Grid) -> bool:
    trace = _trace(grid)
    return not trace["shifts"] and not any(value == 1 for row in grid for value in row)


def _has_shift(grid: Grid) -> bool:
    return bool(_trace(grid)["shifts"])


def _has_multi_shift(grid: Grid) -> bool:
    return any(shift["distance"] >= 2 for shift in _trace(grid)["shifts"])


def _has_bridge(grid: Grid) -> bool:
    return _has_shift(grid) and _climb(grid) != _rival_no_bridge(grid)


def _has_decoy(grid: Grid) -> bool:
    return len(_trace(grid)["off_path_blockers"]) == 1


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "clear_baseline": _is_clear,
    "blocker_changes_path": _has_shift,
    "adjacent_blockers_force_multi_shift": _has_multi_shift,
    "bridge_cells_are_required": _has_bridge,
    "off_path_blocker_is_irrelevant": _has_decoy,
}
WITNESS_RIVALS = {
    "clear_baseline": ["always_extra_shift"],
    "blocker_changes_path": ["ignore_blockers"],
    "adjacent_blockers_force_multi_shift": ["single_step_per_blocked_row"],
    "bridge_cells_are_required": ["shift_without_bridge"],
    "off_path_blocker_is_irrelevant": ["shift_on_any_blue_row"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    inputs: list[Grid] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict):
            reasons.append(f"demo {index} is not a pair mapping")
            continue
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        if output != _climb(grid):
            reasons.append(f"demo {index} output does not match the canonical rule")
            continue
        inputs.append(grid)

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query input is unlawful: {query_errors[0]}")

    if inputs:
        requirements = (
            ("clear no-blocker baseline", _is_clear),
            ("one blocker-driven deflection", _has_shift),
            ("adjacent-blocker multi-column deflection", _has_multi_shift),
            ("off-path blue decoy", _has_decoy),
        )
        for label, predicate in requirements:
            if not any(predicate(grid) for grid in inputs):
                reasons.append(f"demonstrations omit {label}")
    return reasons
