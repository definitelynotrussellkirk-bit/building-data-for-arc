"""Generator for ARC task a64e4611.

The input is a 30x30 zero field with one clutter color.  Clearing linked long
row and column corridors creates several wide runs inside the largest
4-connected zero component.  The rule paints the trimmed interiors of every
qualifying row/column group green (3), taking the union where they cross.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "61d03db55894"
TASK_ID = GENERATOR_ID
VERSION = "4.0.3"
# Pinned to the selected Racket authority.  Updated atomically with the
# comment-preserving source synchronization in this candidate repair.
RULE_HASH = "dd04335d4f92"

GRID_SIZE = 30
TEXTURE_COLORS = (1, 2, 4, 8)
SCENE_PROFILES = (
    "right_arms_full_column",
    "split_arms_bottom_column",
    "left_band_full_column",
    "full_row_dual_columns",
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SUMMARY = (
    "A 30x30 zero field contains one nonzero clutter color and linked wide "
    "horizontal/vertical zero corridors.  In the largest 4-connected zero "
    "component, collect consecutive rows (or columns) whose longest run has "
    "length at least 17.  For each group of thickness at least 3, remove the "
    "two outer group lines, intersect the runs, trim non-boundary endpoints, "
    "and paint the remaining zero cells green (3).  Row and column fills are "
    "combined; a three-column group has the canonical extra bottom trim."
)

INVARIANTS = [
    "all ordinary inputs are 30x30 and use zero plus exactly one clutter color",
    "the largest 4-connected zero component contains both qualifying row and column groups",
    "row-only, column-only, and overlap output cells are all present",
    "the four scheduled profiles reproduce the four canonical corridor topologies",
]

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "texture_color": {
        "type": "int",
        "default": "seeded choice from canonical colors",
        "valid": "1|2|4|8",
    },
}

Grid = list[list[int]]
Cell = tuple[int, int]
Run = tuple[int, int, int]


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Cycle profiles so every four consecutive lesson examples cover all branches."""
    del difficulty
    return SCENE_PROFILES[(int(seed) + int(sample_index)) % len(SCENE_PROFILES)]


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(unknown)}")
    if "scene_profile" in overrides and overrides["scene_profile"] not in SCENE_PROFILES:
        raise ValueError(
            f"scene_profile must be one of {SCENE_PROFILES}, got {overrides['scene_profile']!r}"
        )
    if "texture_color" in overrides:
        value = overrides["texture_color"]
        if isinstance(value, bool) or value not in TEXTURE_COLORS:
            raise ValueError(
                f"texture_color must be one of {TEXTURE_COLORS}, got {value!r}"
            )


def _mark_rect(mask: list[list[bool]], rect: tuple[int, int, int, int]) -> None:
    r0, r1, c0, c1 = rect
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            mask[r][c] = True


def _choose_geometry(rng, profile: str) -> tuple[
    list[tuple[int, int, int, int]],
    list[tuple[int, int, int, int]],
]:
    """Return (horizontal corridors, vertical corridors), all inclusive."""
    h = w = GRID_SIZE
    if profile == "right_arms_full_column":
        width = rng.randint(7, 10)
        c0 = rng.randint(4, 10)
        c1 = c0 + width - 1
        first_h = rng.randint(3, 5)
        first_r0 = rng.randint(4, 8)
        second_h = rng.randint(4, 7)
        second_r0 = rng.randint(max(first_r0 + first_h + 4, 15), 24 - second_h + 1)
        horizontal = [
            (first_r0, first_r0 + first_h - 1, max(1, c0 - rng.randint(1, 3)), w - 1),
            (second_r0, second_r0 + second_h - 1, max(1, c0 - rng.randint(1, 4)), w - 1),
        ]
        vertical = [(0, h - 1, c0, c1)]
    elif profile == "split_arms_bottom_column":
        width = rng.randint(7, 10)
        c0 = rng.randint(7, 11)
        c1 = c0 + width - 1
        vtop = rng.randint(2, 5)
        first_h = rng.randint(3, 5)
        first_r0 = rng.randint(7, 10)
        second_h = rng.randint(3, 5)
        second_r0 = rng.randint(18, 23)
        horizontal = [
            (first_r0, first_r0 + first_h - 1, c0, w - 1),
            (second_r0, second_r0 + second_h - 1, 0, max(16, min(w - 2, c1 + rng.randint(0, 4)))),
        ]
        vertical = [(vtop, h - 1, c0, c1)]
    elif profile == "left_band_full_column":
        width = rng.randint(8, 10)
        c0 = rng.randint(7, 10)
        c1 = c0 + width - 1
        band_h = rng.randint(8, 12)
        r0 = rng.randint(7, 18 - band_h + 1)
        horizontal = [
            (r0, r0 + band_h - 1, 0, min(w - 2, c1 + rng.randint(2, 5)))
        ]
        vertical = [(0, h - 1, c0, c1)]
    elif profile == "full_row_dual_columns":
        band_h = rng.randint(5, 8)
        r0 = rng.randint(8, 15)
        first_width = rng.randint(4, 6)
        first_c0 = rng.randint(7, 11)
        first_c1 = first_c0 + first_width - 1
        second_c0 = rng.randint(max(first_c1 + 5, 19), 25)
        row_bottom = r0 + band_h - 1
        # Keep the width-three column's trimmed bottom witness strictly below
        # the horizontal fill. Otherwise the plausible no-extra-trim rival can
        # paint the same cell through the row branch and survive a full lesson.
        second_bottom = rng.randint(max(row_bottom + 3, 20), h - 2)
        horizontal = [(r0, row_bottom, 0, w - 1)]
        vertical = [
            (0, h - 1, first_c0, first_c1),
            (0, second_bottom, second_c0, second_c0 + 2),
        ]
    else:  # guarded by _validate_overrides / schedule_profile
        raise ValueError(f"unknown scene profile {profile!r}")
    return horizontal, vertical


def _set_corridor_stoppers(
    grid: Grid,
    protected: list[list[bool]],
    horizontal: Iterable[tuple[int, int, int, int]],
    vertical: Iterable[tuple[int, int, int, int]],
    ink: int,
) -> None:
    """Bound intended runs so surrounding background cannot merge into them."""
    h, w = len(grid), len(grid[0])
    for r0, r1, c0, c1 in horizontal:
        for r in range(r0, r1 + 1):
            for c in (c0 - 1, c1 + 1):
                if 0 <= c < w and not protected[r][c]:
                    grid[r][c] = ink
    for r0, r1, c0, c1 in vertical:
        for c in range(c0, c1 + 1):
            for r in (r0 - 1, r1 + 1):
                if 0 <= r < h and not protected[r][c]:
                    grid[r][c] = ink


def _zero_runs(values: list[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index in range(len(values) + 1):
        is_zero = index < len(values) and values[index] == 0
        if is_zero and start is None:
            start = index
        elif not is_zero and start is not None:
            runs.append((start, index - 1))
            start = None
    return runs


def _break_unintended_line_runs(
    values: list[int],
    protected: list[bool],
    intended: list[tuple[int, int]],
    ink: int,
) -> None:
    """Ensure only declared corridor intervals can contain a run of 17 zeros."""
    while True:
        bad: tuple[int, int] | None = None
        for start, end in _zero_runs(values):
            if end - start + 1 < 17:
                continue
            if any(start <= left and right <= end for left, right in intended):
                continue
            bad = (start, end)
            break
        if bad is None:
            return
        start, end = bad
        preferred = min(end, start + 16)
        candidates = sorted(
            (index for index in range(start, end + 1) if not protected[index]),
            key=lambda index: (abs(index - preferred), index),
        )
        if not candidates:
            # A protected run is an intended corridor and should have matched.
            raise AssertionError("protected long run was not declared as intended")
        values[candidates[0]] = ink


def _break_accidental_long_runs(
    grid: Grid,
    protected: list[list[bool]],
    horizontal: list[tuple[int, int, int, int]],
    vertical: list[tuple[int, int, int, int]],
    ink: int,
) -> None:
    h, w = len(grid), len(grid[0])
    row_intervals: dict[int, list[tuple[int, int]]] = {r: [] for r in range(h)}
    col_intervals: dict[int, list[tuple[int, int]]] = {c: [] for c in range(w)}
    for r0, r1, c0, c1 in horizontal:
        for r in range(r0, r1 + 1):
            row_intervals[r].append((c0, c1))
    for r0, r1, c0, c1 in vertical:
        for c in range(c0, c1 + 1):
            col_intervals[c].append((r0, r1))

    for r in range(h):
        _break_unintended_line_runs(
            grid[r], protected[r], row_intervals[r], ink
        )
    for c in range(w):
        values = [grid[r][c] for r in range(h)]
        protected_values = [protected[r][c] for r in range(h)]
        _break_unintended_line_runs(
            values, protected_values, col_intervals[c], ink
        )
        for r, value in enumerate(values):
            grid[r][c] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile_options = (
        SCENE_PROFILES
        if overrides.get("scene_profile") is not None
        else (scheduled_profile,)
    )
    profile = str(ctx.draw_choice("scene_profile", profile_options))
    ink = int(ctx.draw_choice("texture_color", TEXTURE_COLORS))
    horizontal, vertical = _choose_geometry(rng, profile)

    protected = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    for rect in [*horizontal, *vertical]:
        _mark_rect(protected, rect)

    # Target the canonical clutter envelope after carving the protected zero
    # corridors.  Bernoulli-before-carving made wide profiles drift below the
    # official density floor even though the requested source density was
    # unchanged.  Exact-count placement is deterministic and keeps all bands
    # anchored to the four canonical examples (0.222..0.333 clutter).
    fraction_lo, fraction_hi = {
        "easy": (0.23, 0.25),
        "medium": (0.25, 0.27),
        "hard": (0.27, 0.29),
    }.get(difficulty, (0.24, 0.28))
    target_fraction = rng.uniform(fraction_lo, fraction_hi)
    target_ink = round(GRID_SIZE * GRID_SIZE * target_fraction)
    grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    _set_corridor_stoppers(grid, protected, horizontal, vertical, ink)
    existing_ink = sum(value == ink for row in grid for value in row)
    candidates = [
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if not protected[r][c] and grid[r][c] == 0
    ]
    rng.shuffle(candidates)
    for r, c in candidates[: max(0, target_ink - existing_ink)]:
        grid[r][c] = ink

    _break_accidental_long_runs(grid, protected, horizontal, vertical, ink)
    return grid


def _components4(grid: Grid, color: int) -> list[list[Cell]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[list[Cell]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue: deque[Cell] = deque([(r, c)])
            seen.add((r, c))
            cells: list[Cell] = []
            while queue:
                cell = queue.popleft()
                cells.append(cell)
                rr, cc = cell
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(cells)
    return components


def _max_run(length: int, predicate: Callable[[int], bool]) -> Run:
    best: Run = (0, -1, 0)
    start: int | None = None
    for index in range(length + 1):
        active = index < length and predicate(index)
        if active and start is None:
            start = index
        elif not active and start is not None:
            candidate = (start, index - 1, index - start)
            if candidate[2] > best[2]:
                best = candidate
            start = None
    return best


def _consecutive_groups(values: Iterable[int]) -> list[list[int]]:
    groups: list[list[int]] = []
    for value in values:
        if not groups or value != groups[-1][-1] + 1:
            groups.append([value])
        else:
            groups[-1].append(value)
    return groups


def _profile_from_details(
    row_details: list[dict[str, object]],
    col_details: list[dict[str, object]],
) -> str | None:
    if len(row_details) == 1 and len(col_details) == 2:
        row = row_details[0]
        if (
            row["touch_left"]
            and row["touch_right"]
            and any(detail["thickness"] == 3 for detail in col_details)
        ):
            return "full_row_dual_columns"
    if len(row_details) == 1 and len(col_details) == 1:
        row, col = row_details[0], col_details[0]
        if (
            row["touch_left"]
            and not row["touch_right"]
            and col["touch_top"]
            and col["touch_bottom"]
        ):
            return "left_band_full_column"
    if len(row_details) == 2 and len(col_details) == 1:
        left_only = any(
            detail["touch_left"] and not detail["touch_right"]
            for detail in row_details
        )
        right_only = any(
            detail["touch_right"] and not detail["touch_left"]
            for detail in row_details
        )
        col = col_details[0]
        if left_only and right_only and col["touch_bottom"]:
            return "split_arms_bottom_column"
        if (
            all(detail["touch_right"] for detail in row_details)
            and col["touch_top"]
            and col["touch_bottom"]
        ):
            return "right_arms_full_column"
    return None


def _analysis(grid: Grid) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["empty grid"]}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["grid rows must be nonempty lists"]}
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return {"errors": ["ragged grid"]}
    if h != GRID_SIZE or w != GRID_SIZE:
        errors.append(f"expected {GRID_SIZE}x{GRID_SIZE}, found {h}x{w}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid cell value at ({r},{c}): {value!r}")
                break
        if errors and errors[-1].startswith("invalid cell"):
            break

    counts = Counter(value for row in grid for value in row)
    nonzero = sorted(color for color in counts if color != 0)
    if not counts or counts.most_common(1)[0][0] != 0:
        errors.append("zero must be the modal background")
    if len(nonzero) != 1 or nonzero[0] == 3:
        errors.append(
            f"expected one non-green clutter color, found {nonzero}"
        )
    texture_color = nonzero[0] if len(nonzero) == 1 else None
    texture_fraction = (
        counts.get(texture_color, 0) / (h * w) if texture_color is not None else 0.0
    )
    if texture_color is not None and not 0.15 <= texture_fraction <= 0.42:
        errors.append(
            f"clutter fraction {texture_fraction:.3f} outside canonical range"
        )

    zero_components = _components4(grid, 0) if 0 in counts else []
    if not zero_components:
        errors.append("no zero component")
        return {
            "errors": errors,
            "texture_color": texture_color,
            "texture_fraction": texture_fraction,
        }
    largest = set(max(zero_components, key=len))
    # The largest component must carry the linked corridors, but it need not
    # exceed half the board: canonical-like clutter can split peripheral zero
    # pockets without changing the selected component or its run geometry.
    if len(largest) < (2 * h * w) // 5:
        errors.append("largest zero component is too small")

    row_runs = [
        _max_run(w, lambda c, r=r: (r, c) in largest) for r in range(h)
    ]
    col_runs = [
        _max_run(h, lambda r, c=c: (r, c) in largest) for c in range(w)
    ]
    row_groups = _consecutive_groups(
        r for r, run in enumerate(row_runs) if run[2] >= 17
    )
    col_groups = _consecutive_groups(
        c for c, run in enumerate(col_runs) if run[2] >= 17
    )

    row_fill: set[Cell] = set()
    col_fill: set[Cell] = set()
    row_details: list[dict[str, object]] = []
    col_details: list[dict[str, object]] = []

    for group in row_groups:
        if len(group) < 3:
            continue
        runs = [row_runs[r] for r in group]
        start = max(run[0] for run in runs)
        end = min(run[1] for run in runs)
        fill_start = start + 1 if start > 0 else start
        fill_end = end - 1 if end < w - 1 else end
        for r in group[1:-1]:
            for c in range(fill_start, fill_end + 1):
                if (r, c) in largest:
                    row_fill.add((r, c))
        row_details.append(
            {
                "group": tuple(group),
                "thickness": len(group),
                "common_start": start,
                "common_end": end,
                "touch_left": start == 0,
                "touch_right": end == w - 1,
            }
        )

    for group in col_groups:
        if len(group) < 3:
            continue
        runs = [col_runs[c] for c in group]
        start = max(run[0] for run in runs)
        end = min(run[1] for run in runs)
        fill_start = start + 1 if start > 0 else start
        fill_end = end - 1 if end < h - 1 else end
        if len(group) == 3 and fill_end < h - 1:
            fill_end -= 1
        for c in group[1:-1]:
            for r in range(fill_start, fill_end + 1):
                if (r, c) in largest:
                    col_fill.add((r, c))
        col_details.append(
            {
                "group": tuple(group),
                "thickness": len(group),
                "common_start": start,
                "common_end": end,
                "touch_top": start == 0,
                "touch_bottom": end == h - 1,
            }
        )

    if not row_fill:
        errors.append("no qualifying row-group fill")
    if not col_fill:
        errors.append("no qualifying column-group fill")
    if row_fill and col_fill:
        if not row_fill - col_fill:
            errors.append("no row-only output cells")
        if not col_fill - row_fill:
            errors.append("no column-only output cells")
        if not row_fill & col_fill:
            errors.append("row and column fills do not overlap")

    profile = _profile_from_details(row_details, col_details)
    if profile is None:
        errors.append(
            "qualifying row/column groups do not match a canonical topology"
        )

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "texture_color": texture_color,
        "texture_fraction": texture_fraction,
        "largest_zero": largest,
        "row_runs": row_runs,
        "col_runs": col_runs,
        "row_groups": row_groups,
        "col_groups": col_groups,
        "row_details": row_details,
        "col_details": col_details,
        "row_fill": row_fill,
        "col_fill": col_fill,
        "profile": profile,
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the selected Racket authority."""
    info = _analysis(grid)
    if "row_fill" not in info or "col_fill" not in info:
        raise ValueError("grid cannot be analyzed by the task rule")
    paint = set(info["row_fill"]) | set(info["col_fill"])
    return [
        [3 if value == 0 and (r, c) in paint else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    info = _analysis(grid)
    errors = list(info.get("errors", []))
    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis in AXES:
            if axis in requested and observed.get(axis) != requested[axis]:
                errors.append(
                    f"override {axis}={requested[axis]!r} realized as {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid):
    return list(_analysis(grid).get("errors", []))


def observe_overrides(grid):
    info = _analysis(grid)
    if info.get("errors"):
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(info["errors"]))
    return {
        "scene_profile": info["profile"],
        "texture_color": info["texture_color"],
    }


def _paint_rows_only(grid: Grid) -> Grid:
    info = _analysis(grid)
    paint = set(info.get("row_fill", set()))
    return [
        [3 if value == 0 and (r, c) in paint else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _paint_columns_only(grid: Grid) -> Grid:
    info = _analysis(grid)
    paint = set(info.get("col_fill", set()))
    return [
        [3 if value == 0 and (r, c) in paint else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _no_three_column_extra_trim(grid: Grid) -> Grid:
    """Plausible rival: omit the authority's extra bottom trim for width three."""
    info = _analysis(grid)
    if "largest_zero" not in info:
        return [row[:] for row in grid]
    h = len(grid)
    largest = set(info["largest_zero"])
    paint = set(info["row_fill"])
    col_runs = info["col_runs"]
    for group in info["col_groups"]:
        if len(group) < 3:
            continue
        runs = [col_runs[c] for c in group]
        start = max(run[0] for run in runs)
        end = min(run[1] for run in runs)
        fill_start = start + 1 if start > 0 else start
        fill_end = end - 1 if end < h - 1 else end
        for c in group[1:-1]:
            for r in range(fill_start, fill_end + 1):
                if (r, c) in largest:
                    paint.add((r, c))
    return [
        [3 if value == 0 and (r, c) in paint else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


def _first_row_group_only(grid: Grid) -> Grid:
    info = _analysis(grid)
    if "largest_zero" not in info:
        return [row[:] for row in grid]
    largest = set(info["largest_zero"])
    paint = set(info["col_fill"])
    row_runs = info["row_runs"]
    valid = [group for group in info["row_groups"] if len(group) >= 3]
    if valid:
        group = valid[0]
        runs = [row_runs[r] for r in group]
        start = max(run[0] for run in runs)
        end = min(run[1] for run in runs)
        start += 1 if start > 0 else 0
        end -= 1 if end < len(grid[0]) - 1 else 0
        for r in group[1:-1]:
            for c in range(start, end + 1):
                if (r, c) in largest:
                    paint.add((r, c))
    return [
        [3 if value == 0 and (r, c) in paint else value for c, value in enumerate(row)]
        for r, row in enumerate(grid)
    ]


SEMANTIC_WITNESSES = {
    "row_only_cells": lambda grid: bool(_analysis(grid).get("row_fill", set()) - _analysis(grid).get("col_fill", set())),
    "column_only_cells": lambda grid: bool(_analysis(grid).get("col_fill", set()) - _analysis(grid).get("row_fill", set())),
    "overlap_cells": lambda grid: bool(_analysis(grid).get("row_fill", set()) & _analysis(grid).get("col_fill", set())),
    "multiple_row_groups": lambda grid: len(_analysis(grid).get("row_details", [])) >= 2,
    "multiple_column_groups": lambda grid: len(_analysis(grid).get("col_details", [])) >= 2,
    "three_column_group": lambda grid: any(detail["thickness"] == 3 for detail in _analysis(grid).get("col_details", [])),
}

SEMANTIC_RIVALS = {
    "rows_only": _paint_rows_only,
    "columns_only": _paint_columns_only,
    "no_three_column_extra_trim": _no_three_column_extra_trim,
    "first_row_group_only": _first_row_group_only,
}
WITNESS_RIVALS = {
    "row_only_cells": ["columns_only"],
    "column_only_cells": ["rows_only"],
    "multiple_row_groups": ["first_row_group_only"],
    "three_column_group": ["no_three_column_extra_trim"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons: list[str] = []
    demo_profiles: set[str] = set()
    for index, pair in enumerate(demos):
        info = _analysis(pair["input"])
        if info.get("errors"):
            reasons.append(f"demo {index} is not canonical-like")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not follow the selected rule")
        demo_profiles.add(str(info["profile"]))
    missing = sorted(set(SCENE_PROFILES) - demo_profiles)
    if missing:
        reasons.append("demos omit profile(s): " + ", ".join(missing))
    query_info = _analysis(query["input"])
    if query_info.get("errors"):
        reasons.append("query is not canonical-like")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not follow the selected rule")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival survives demos: {name}")
    return reasons
