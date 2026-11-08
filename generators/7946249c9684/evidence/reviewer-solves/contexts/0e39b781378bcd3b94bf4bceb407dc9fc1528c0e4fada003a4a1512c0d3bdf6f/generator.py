"""Input sampler for the vertical-run endcap task.

The selected Racket authority scans columns independently.  Every maximal
same-color non-background vertical run keeps its first and last cell; all
interior cells become background.  This generator deliberately includes
multi-run columns, touching differently colored runs, connected run systems,
and repeated colors so three tempting public-example shortcuts are falsified.

``_intended_output`` and the rival functions below are review/test helpers.
They never provide training labels; the Racket program remains the authority.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7946249c9684"
TASK_ID = GENERATOR_ID
RULE_HASH = "ab25d2969132"
VERSION = "3.2.0"
SUMMARY = (
    "Six- to twelve-row grids containing 3-8 same-color vertical runs in "
    "2-3 colors.  Scheduled profiles include canonical sparse bars, multiple "
    "runs in one column, touching colors, connected systems, and reused colors."
)

INVARIANTS = [
    "grid dimensions are 6..12 rows by 7..12 columns",
    "there are exactly 3..8 maximal same-color vertical runs in exactly 2 or 3 colors",
    "at least one run has length at least 3, so the authoritative output changes",
    "every three consecutive default examples include all semantic curriculum profiles",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical/band profile",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical/band profile",
        "valid": "7..12",
    },
    "n_runs": {
        "type": "int",
        "default": "scheduled 3..8",
        "valid": "3..8",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25
SCHEDULE_PROFILES = (
    "canonical",
    "boundary_contact",
    "separated_stacks",
)

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
_CANONICAL_PROFILES = ((7, 7), (8, 8), (6, 9), (7, 9))
_ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the cyclic semantic profile used for this sample index."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override axis: {sorted(unknown)}")
    bounds = {
        "grid_h": (6, 12),
        "grid_w": (7, 12),
        "n_runs": (3, 8),
        "palette_size": (2, 3),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}, got {value}")


def _profile_defaults(profile: str, sample_index: int, difficulty) -> dict[str, int]:
    cycle = sample_index // len(SCHEDULE_PROFILES)
    if profile == "canonical":
        h, w = _CANONICAL_PROFILES[cycle % len(_CANONICAL_PROFILES)]
        return {"grid_h": h, "grid_w": w, "n_runs": 3, "palette_size": 3}

    band = "medium" if difficulty is None else difficulty
    if profile == "boundary_contact":
        return {
            "easy": {"grid_h": 6, "grid_w": 8, "n_runs": 4, "palette_size": 3},
            "medium": {"grid_h": 9, "grid_w": 10, "n_runs": 6, "palette_size": 3},
            "hard": {"grid_h": 12, "grid_w": 12, "n_runs": 8, "palette_size": 3},
        }[band]
    if profile == "separated_stacks":
        return {
            "easy": {"grid_h": 7, "grid_w": 9, "n_runs": 5, "palette_size": 3},
            "medium": {"grid_h": 10, "grid_w": 11, "n_runs": 6, "palette_size": 3},
            "hard": {"grid_h": 12, "grid_w": 12, "n_runs": 8, "palette_size": 3},
        }[band]
    raise ValueError(f"unknown schedule profile: {profile!r}")


def _draw_profile_int(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    """Draw a scheduled singleton normally, but expose the full override domain."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _vertical_runs(grid):
    """Return ``(column, start_row, end_row, color)`` for every nonzero run."""
    h, w = len(grid), len(grid[0])
    runs = []
    for c in range(w):
        r = 0
        while r < h:
            color = grid[r][c]
            if color == 0:
                r += 1
                continue
            r0 = r
            while r + 1 < h and grid[r + 1][c] == color:
                r += 1
            runs.append((c, r0, r, color))
            r += 1
    return runs


def _paint_runs(h: int, w: int, runs) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    for column, start, end, color in runs:
        if not (0 <= column < w and 0 <= start <= end < h):
            raise RuntimeError(f"invalid constructed run {(column, start, end, color)}")
        for row in range(start, end + 1):
            if grid[row][column] != 0:
                raise RuntimeError(f"constructed runs overlap at {(row, column)}")
            grid[row][column] = color
    return grid


def _color_sequence(rng, palette, n_runs: int) -> list[int]:
    colors = list(palette)
    colors.extend(palette[index % len(palette)] for index in range(n_runs - len(colors)))
    rng.shuffle(colors)
    return colors


def _generic_sparse_runs(rng, h: int, w: int, n_runs: int, palette) -> list[tuple[int, int, int, int]]:
    """Construct exact counts for arbitrary legal override combinations."""
    columns = list(range(w))
    rng.shuffle(columns)
    chosen = columns[: min(n_runs, w)]
    if n_runs > w:  # only 8 runs on width 7 can reach this branch
        chosen.extend(columns[: n_runs - w])

    colors = _color_sequence(rng, palette, n_runs)
    occurrences = Counter(chosen)
    seen: Counter[int] = Counter()
    runs = []
    for index, column in enumerate(chosen):
        seen[column] += 1
        if occurrences[column] == 2:
            if seen[column] == 1:
                start, end = 0, 1
            else:
                start, end = 3, h - 1
        else:
            if index == 0:
                length = rng.randint(3, h)
            else:
                length = rng.randint(1, h)
            start = rng.randint(0, h - length)
            end = start + length - 1
        runs.append((column, start, end, colors[index]))
    return runs


def _canonical_runs(rng, h: int, w: int, palette) -> list[tuple[int, int, int, int]]:
    """Three isolated, unique-color runs at an exact public profile."""
    spaced_columns = list(range(0, w, 2))
    columns = sorted(rng.sample(spaced_columns, 3))
    colors = list(palette)
    rng.shuffle(colors)
    lengths = [1, 2, rng.randint(3, h)]
    rng.shuffle(lengths)
    runs = []
    for column, color, length in zip(columns, colors, lengths):
        start = rng.randint(0, h - length)
        runs.append((column, start, start + length - 1, color))
    return runs


def _extra_run(rng, h: int, column: int, color: int, *, force_long: bool = False):
    lo = 3 if force_long else 1
    length = rng.randint(lo, h)
    start = rng.randint(0, h - length)
    return (column, start, start + length - 1, color)


def _boundary_contact_runs(
    rng, h: int, w: int, n_runs: int, palette
) -> list[tuple[int, int, int, int]]:
    """Construct touching color/runs and a same-color horizontal branch."""
    primary = rng.randrange(w - 1)
    bridge = primary + 1
    unused = [column for column in range(w) if column not in (primary, bridge)]
    rng.shuffle(unused)
    split = h // 2

    if len(palette) == 3 and n_runs == 3:
        # Exact 3-run/3-color overrides cannot repeat a color.  Ordinary
        # scheduled profiles have >=4 runs and use the stronger branch below.
        top_color, bottom_color, bridge_color = palette
    else:
        top_color, bottom_color = palette[0], palette[1]
        bridge_color = top_color

    runs = [
        (primary, 0, split - 1, top_color),
        (primary, split, h - 1, bottom_color),
        (bridge, max(0, split - 2), min(h - 1, split + 1), bridge_color),
    ]
    next_unused = 0
    if len(palette) == 3 and n_runs >= 4:
        runs.append(_extra_run(rng, h, unused[next_unused], palette[2]))
        next_unused += 1

    remaining = n_runs - len(runs)
    for index in range(remaining):
        color = palette[index % len(palette)]
        runs.append(_extra_run(rng, h, unused[next_unused], color))
        next_unused += 1
    return runs


def _separated_stack_runs(
    rng, h: int, w: int, n_runs: int, palette
) -> list[tuple[int, int, int, int]]:
    """Separated same-column runs plus a same-color adjacent bridge."""
    stack = rng.randrange(w - 1)
    bridge = stack + 1
    unused = [column for column in range(w) if column not in (stack, bridge)]
    rng.shuffle(unused)

    if len(palette) == 3 and n_runs == 3:
        # Three runs cannot both use three colors and repeat one.  This is an
        # honest exact-override edge; scheduled profiles use at least five.
        top_color, bottom_color, bridge_color = palette
    else:
        top_color = palette[0]
        bottom_color = palette[1]
        bridge_color = top_color

    runs = [
        (stack, 0, 1, top_color),
        (stack, 3, h - 1, bottom_color),
        (bridge, 1, 3, bridge_color),
    ]
    next_unused = 0
    if len(palette) == 3 and n_runs >= 4:
        runs.append(_extra_run(rng, h, unused[next_unused], palette[2]))
        next_unused += 1

    remaining = n_runs - len(runs)
    for index in range(remaining):
        color = palette[index % len(palette)]
        runs.append(_extra_run(rng, h, unused[next_unused], color))
        next_unused += 1
    return runs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty=difficulty)
    defaults = _profile_defaults(profile, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", defaults["grid_h"], 6, 12)
    w = _draw_profile_int(ctx, overrides, "grid_w", defaults["grid_w"], 7, 12)
    n_runs = _draw_profile_int(ctx, overrides, "n_runs", defaults["n_runs"], 3, 8)
    palette_size = _draw_profile_int(
        ctx, overrides, "palette_size", defaults["palette_size"], 2, 3
    )
    palette = ctx.draw_distinct_colors("palette", n=palette_size, exclude=(0,))
    layout_rng = ctx.draw_rng("layout")

    default_contract = all(
        name not in overrides or overrides[name] is None for name in AXES
    )
    if profile == "canonical" and default_contract:
        runs = _canonical_runs(layout_rng, h, w, palette)
    elif profile == "boundary_contact":
        runs = _boundary_contact_runs(layout_rng, h, w, n_runs, palette)
    elif profile == "separated_stacks":
        runs = _separated_stack_runs(layout_rng, h, w, n_runs, palette)
    else:
        runs = _generic_sparse_runs(layout_rng, h, w, n_runs, palette)

    grid = _paint_runs(h, w, runs)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid vertical-run lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_runs": n_runs,
        "palette_size": palette_size,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axis mismatch: expected {expected}, got {observed}")
    return grid


def _intended_output(grid):
    """Independent Python semantic mirror used only by review/tests."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for column, start, end, color in _vertical_runs(grid):
        out[start][column] = color
        out[end][column] = color
    return out


def observe_overrides(grid) -> dict[str, int]:
    runs = _vertical_runs(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_runs": len(runs),
        "palette_size": len({color for _, _, _, color in runs}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    errors: list[str] = []
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append(f"unknown difficulty: {difficulty!r}")
    if not isinstance(grid, list) or not grid:
        return errors + ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return errors + ["every row must be a nonempty list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return errors + ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return errors + ["cells must be integer colors 0..9"]

    h, w = len(grid), len(grid[0])
    if not 6 <= h <= 12:
        errors.append(f"grid height must be 6..12, got {h}")
    if not 7 <= w <= 12:
        errors.append(f"grid width must be 7..12, got {w}")

    runs = _vertical_runs(grid)
    if not 3 <= len(runs) <= 8:
        errors.append(f"expected 3..8 vertical runs, got {len(runs)}")
    palette_size = len({color for _, _, _, color in runs})
    if not 2 <= palette_size <= 3:
        errors.append(f"expected 2 or 3 foreground colors, got {palette_size}")
    if not any(end - start + 1 >= 3 for _, start, end, _ in runs):
        errors.append("expected at least one run of length at least 3")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical sparse three-run manifold, not all lawful lessons."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    if (h, w) not in _CANONICAL_PROFILES:
        reasons.append(f"shape {(h, w)} is not one of the canonical profiles")
    runs = _vertical_runs(grid)
    if len(runs) != 3:
        reasons.append(f"canonical profile requires exactly 3 runs, got {len(runs)}")
    if len({color for _, _, _, color in runs}) != 3:
        reasons.append("canonical profile requires one distinct color per run")
    if len({column for column, _, _, _ in runs}) != len(runs):
        reasons.append("canonical profile has at most one run per column")
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    if any((r, c + 1) in nonzero for r, c in nonzero):
        reasons.append("canonical profile has no horizontally adjacent foreground cells")
    return reasons


def _column_extremes_rival(grid):
    """Wrong shortcut: retain only the first/last nonzero cell per column."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] != 0]
        if rows:
            out[rows[0]][c] = grid[rows[0]][c]
            out[rows[-1]][c] = grid[rows[-1]][c]
    return out


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _ORTHOGONALS:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _nonzero_component_leaves_rival(grid):
    """Wrong shortcut: keep graph leaves of each color-blind foreground component."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for component in _nonzero_components(grid):
        for r, c in component:
            degree = sum((r + dr, c + dc) in component for dr, dc in _ORTHOGONALS)
            if degree <= 1:
                out[r][c] = grid[r][c]
    return out


def _same_color_components(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _ORTHOGONALS:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _same_color_component_leaves_rival(grid):
    """Wrong shortcut: keep leaves of each same-color 4-connected component."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for component in _same_color_components(grid):
        for r, c in component:
            degree = sum((r + dr, c + dc) in component for dr, dc in _ORTHOGONALS)
            if degree <= 1:
                out[r][c] = grid[r][c]
    return out


def _global_color_extremes_rival(grid):
    """Wrong shortcut: keep globally top/bottom cells of each foreground color."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                by_color[color].append((r, c))
    for color, cells in by_color.items():
        lo = min(r for r, _ in cells)
        hi = max(r for r, _ in cells)
        for r, c in cells:
            if r in (lo, hi):
                out[r][c] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "column_extremes": _column_extremes_rival,
    "nonzero_component_leaves": _nonzero_component_leaves_rival,
    "same_color_component_leaves": _same_color_component_leaves_rival,
    "global_color_extremes": _global_color_extremes_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _multiple_runs_per_column(grid) -> bool:
    counts = Counter(column for column, _, _, _ in _vertical_runs(grid))
    return any(count > 1 for count in counts.values()) and (
        _column_extremes_rival(grid) != _intended_output(grid)
    )


def _connected_nonzero_runs(grid) -> bool:
    return _nonzero_component_leaves_rival(grid) != _intended_output(grid)


def _same_color_connected_runs(grid) -> bool:
    return _same_color_component_leaves_rival(grid) != _intended_output(grid)


def _reused_color_runs(grid) -> bool:
    counts = Counter(color for _, _, _, color in _vertical_runs(grid))
    return any(count > 1 for count in counts.values()) and (
        _global_color_extremes_rival(grid) != _intended_output(grid)
    )


SEMANTIC_WITNESSES = {
    "multiple_runs_per_column": _multiple_runs_per_column,
    "connected_nonzero_runs": _connected_nonzero_runs,
    "same_color_connected_runs": _same_color_connected_runs,
    "reused_color_runs": _reused_color_runs,
}
WITNESS_RIVALS = {
    "multiple_runs_per_column": ["column_extremes"],
    "connected_nonzero_runs": ["nonzero_component_leaves"],
    "same_color_connected_runs": ["same_color_component_leaves"],
    "reused_color_runs": ["global_color_extremes"],
}


def semantic_observables(grid) -> dict[str, Any]:
    runs = _vertical_runs(grid)
    return {
        **observe_overrides(grid),
        "profile_reasons": strict_canonical_like(grid),
        "columns_with_multiple_runs": sum(
            count > 1 for count in Counter(c for c, _, _, _ in runs).values()
        ),
        "colors_reused_across_runs": sum(
            count > 1 for count in Counter(color for _, _, _, color in runs).values()
        ),
        "nonzero_components": len(_nonzero_components(grid)),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demos leave a declared canonical-fitting rival alive."""
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful run lesson: " + "; ".join(query_errors)]
    query_truth = _intended_output(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != _intended_output(demo_input):
            reasons.append(f"demo {index} output disagrees with vertical-run endcaps")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
    return reasons
