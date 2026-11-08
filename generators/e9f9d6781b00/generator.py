"""Generator for ARC task e9f9d6781b00 (legacy slug d13f3404).

Each non-zero input cell keeps its color and emits a southeast (+1,+1)
diagonal in an output whose height and width are doubled.  The teaching
grammar keeps source cells on distinct diagonals so no source is hidden by the
canonical rule's first-hit behavior.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e9f9d6781b00"
TASK_ID = "e9f9d6781b00"
VERSION = "4.0.0"
RULE_HASH = "0db50ef6e527"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 3..6 by 3..6 zero-background grid contains 2..4 distinct-colored "
    "source cells on distinct southeast diagonals.  The output is 2h by 2w. "
    "Every source at (r,c) retains its color and paints that color at "
    "(r+k,c+k) for every in-bounds k>=0."
)

INVARIANTS = [
    "background is color 0",
    "there are 2..4 non-zero source cells with pairwise-distinct colors",
    "source cells occupy distinct r-c diagonals, so no trail overwrites another",
    "sources are not all confined to one row or one column",
    "every ordinary draw is either mixed top/left-edge evidence or includes a non-top/left source",
    "input dimensions are 3..6, so the doubled output remains within ARC limits",
]

LAYOUTS = ("mixed_edges", "interior_mix")
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 3..6", "valid": "3..6"},
    "grid_w": {"type": "int", "default": "scheduled 3..6", "valid": "3..6"},
    "n_dots": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "layout": {
        "type": "str",
        "default": "scheduled canonical/broad alternation",
        "valid": "|".join(LAYOUTS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Negative fixtures are intentionally outside AXES.  They exist so defect-lint
# and focused tests can prove that self_check rejects rule-hiding scenes.
DEGENERATE_TEXTURES = (
    "no_dots",
    "singleton",
    "same_diagonal",
    "duplicate_color",
    "short_line",
    "solid_block",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_mixed_edges",
    "canonical_interior",
    "broad_interior",
    "broad_mixed_edges",
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the four-slot curriculum schedule used by every lesson window."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty in (None, "easy", "medium", "hard"):
        return
    if (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and 0.0 <= float(difficulty) <= 1.0
    ):
        return
    raise ValueError(
        "difficulty must be easy, medium, hard, None, or a number in [0,1]"
    )


def _draw_int_with_default(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_with_default(
    ctx, label: str, options: Sequence[str], default: str
) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _broad_dimensions(ctx, difficulty: Any, profile_index: int) -> tuple[int, int]:
    if difficulty == "easy" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) < 0.34
    ):
        lo, hi = 3, 4
    elif difficulty == "hard" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) >= 0.67
    ):
        lo, hi = 5, 6
    else:
        lo, hi = 4, 5
    rng = ctx.draw_rng("scheduled_dimensions")
    first = rng.randint(lo, hi)
    second = rng.randint(lo, hi)
    if first == second:
        second = lo if first != lo else hi
    return (first, second) if profile_index == 2 else (second, first)


def _layout_positions(
    layout: str, h: int, w: int, n_dots: int, rng
) -> list[tuple[int, int]]:
    if layout == "mixed_edges":
        top = [(0, c) for c in range(1, w)]
        left = [(r, 0) for r in range(1, h)]
        chosen = [rng.choice(top), rng.choice(left)]
        remaining = [
            p
            for p in [(0, 0), *top, *left]
            if p not in chosen and (p[0] - p[1]) not in {r - c for r, c in chosen}
        ]
        if n_dots > 2:
            chosen.extend(rng.sample(remaining, n_dots - 2))
        return chosen

    if layout != "interior_mix":
        raise ValueError(f"unknown layout {layout!r}")

    positions = [(r, c) for r in range(h) for c in range(w)]
    for _ in range(1024):
        chosen = rng.sample(positions, n_dots)
        if not any(r > 0 and c > 0 for r, c in chosen):
            continue
        if len({r - c for r, c in chosen}) != n_dots:
            continue
        if len({r for r, _ in chosen}) == 1 or len({c for _, c in chosen}) == 1:
            continue
        return chosen

    # Deterministic exhaustive fallback for completeness at the smallest grid.
    valid = [
        list(combo)
        for combo in combinations(positions, n_dots)
        if any(r > 0 and c > 0 for r, c in combo)
        and len({r - c for r, c in combo}) == n_dots
        and len({r for r, _ in combo}) > 1
        and len({c for _, c in combo}) > 1
    ]
    if not valid:
        raise ValueError(
            f"grid_h={h}, grid_w={w}, n_dots={n_dots}, layout={layout} "
            "has no lawful placement"
        )
    return rng.choice(valid)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture {texture!r}")
        return _draw_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_index = sample_index % len(SCHEDULE_PROFILES)
    if profile_index < 2:
        default_h, default_w = 3, 3
        default_n = 3
        default_layout = LAYOUTS[profile_index]
    else:
        default_h, default_w = _broad_dimensions(ctx, difficulty, profile_index)
        default_n = 4 if profile_index == 2 else 2
        default_layout = "interior_mix" if profile_index == 2 else "mixed_edges"

    h = _draw_int_with_default(ctx, "grid_h", 3, 6, default_h)
    w = _draw_int_with_default(ctx, "grid_w", 3, 6, default_w)
    n_dots = _draw_int_with_default(ctx, "n_dots", 2, 4, default_n)
    layout = _draw_choice_with_default(ctx, "layout", LAYOUTS, default_layout)

    rng = ctx.draw_rng("placement_and_colors")
    positions = _layout_positions(layout, h, w, n_dots, rng)
    colors = rng.sample(list(range(1, 10)), n_dots)
    rng.shuffle(colors)

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    return grid


def _draw_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(3, 3, 0)
    if name == "no_dots":
        return grid
    if name == "singleton":
        grid[1][1] = 2
        return grid
    if name == "same_diagonal":
        grid[0][0], grid[1][1] = 2, 3
        return grid
    if name == "duplicate_color":
        grid[0][1], grid[1][0], grid[2][2] = 4, 4, 7
        return grid
    if name == "short_line":
        grid[1] = [2, 3, 4]
        return grid
    if name == "solid_block":
        grid[0][0] = grid[0][1] = grid[1][0] = grid[1][1] = 6
        return grid
    raise ValueError(f"unknown texture {name!r}")


def _dot_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _classify_layout(grid: list[list[int]]) -> str | None:
    dots = _dot_cells(grid)
    if not dots:
        return None
    if all(r == 0 or c == 0 for r, c, _ in dots):
        has_top = any(r == 0 and c > 0 for r, c, _ in dots)
        has_left = any(c == 0 and r > 0 for r, c, _ in dots)
        return "mixed_edges" if has_top and has_left else None
    return "interior_mix" if any(r > 0 and c > 0 for r, c, _ in dots) else None


def observe_overrides(grid) -> dict[str, int | str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}
    h = len(grid)
    w = len(grid[0]) if grid else 0
    return {
        "grid_h": h,
        "grid_w": w,
        "n_dots": len(_dot_cells(grid)),
        "layout": _classify_layout(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the task-linked input grammar and exact realized overrides."""
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return ["grid must be rectangular and non-empty"]

    h, w = len(grid), len(grid[0])
    if not (3 <= h <= 6 and 3 <= w <= 6):
        errors.append(f"input dimensions {h}x{w} are outside 3..6")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return errors

    dots = _dot_cells(grid)
    if not 2 <= len(dots) <= 4:
        errors.append(f"expected 2..4 non-zero source cells; got {len(dots)}")
    colors = [value for _, _, value in dots]
    if len(set(colors)) != len(colors):
        errors.append("source colors must be pairwise distinct")
    diagonals = [r - c for r, c, _ in dots]
    if len(set(diagonals)) != len(diagonals):
        errors.append("source cells must occupy distinct southeast diagonals")
    if dots and len({r for r, _, _ in dots}) == 1:
        errors.append("all source cells lie on one row")
    if dots and len({c for _, c, _ in dots}) == 1:
        errors.append("all source cells lie on one column")
    layout = _classify_layout(grid)
    if layout not in LAYOUTS:
        errors.append("source placement is neither mixed_edges nor interior_mix")

    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    observed = observe_overrides(grid)
    if isinstance(overrides, dict):
        for axis, requested in overrides.items():
            if axis in AXES and observed.get(axis) != requested:
                errors.append(
                    f"override {axis} requested {requested!r}, observed "
                    f"{observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws lie on the defended canonical teaching manifold."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python test mirror; the canonical Racket program remains authority."""
    h, w = len(grid), len(grid[0])
    output = full_grid(2 * h, 2 * w, 0)
    for r, c, color in _dot_cells(grid):
        k = 0
        while r + k < 2 * h and c + k < 2 * w:
            output[r + k][c + k] = color
            k += 1
    return output


def _restricted_rule(
    grid: list[list[int]],
    keep: Callable[[int, int, int], bool] = lambda r, c, v: True,
    *,
    max_step: int | None = None,
    force_color: int | None = None,
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    output = full_grid(2 * h, 2 * w, 0)
    for r, c, color in _dot_cells(grid):
        if not keep(r, c, color):
            continue
        painted = force_color if force_color is not None else color
        k = 0
        while r + k < 2 * h and c + k < 2 * w:
            if max_step is not None and k > max_step:
                break
            output[r + k][c + k] = painted
            k += 1
    return output


def _copy_only(grid):
    return _restricted_rule(grid, max_step=0)


def _one_step(grid):
    return _restricted_rule(grid, max_step=1)


def _top_row_only(grid):
    return _restricted_rule(grid, keep=lambda r, c, v: r == 0)


def _edge_only(grid):
    return _restricted_rule(grid, keep=lambda r, c, v: r == 0 or c == 0)


def _monochrome(grid):
    dots = _dot_cells(grid)
    color = dots[0][2] if dots else 1
    return _restricted_rule(grid, force_color=color)


SEMANTIC_RIVALS = {
    "copy_sources_without_extension": _copy_only,
    "extend_only_one_step": _one_step,
    "use_only_top_row_sources": _top_row_only,
    "use_only_top_or_left_edge_sources": _edge_only,
    "recolor_every_trail_with_first_source": _monochrome,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _layout_witness(name: str):
    return lambda grid: not self_check(grid) and _classify_layout(grid) == name


def _has_interior_source(grid) -> bool:
    return not self_check(grid) and any(
        r > 0 and c > 0 for r, c, _ in _dot_cells(grid)
    )


def _has_non_top_source(grid) -> bool:
    return not self_check(grid) and any(r > 0 for r, _, _ in _dot_cells(grid))


def _has_three_or_more_colors(grid) -> bool:
    return not self_check(grid) and len(_dot_cells(grid)) >= 3


def _has_long_extension(grid) -> bool:
    return not self_check(grid) and bool(_dot_cells(grid))


SEMANTIC_WITNESSES = {
    "mixed_edges_layout": _layout_witness("mixed_edges"),
    "interior_mix_layout": _layout_witness("interior_mix"),
    "interior_source": _has_interior_source,
    "non_top_source": _has_non_top_source,
    "three_or_more_distinct_colors": _has_three_or_more_colors,
    "long_extension": _has_long_extension,
    "rectangular_input": lambda grid: not self_check(grid) and len(grid) != len(grid[0]),
}
WITNESS_RIVALS = {
    "interior_source": ["use_only_top_or_left_edge_sources"],
    "non_top_source": ["use_only_top_row_sources"],
    "three_or_more_distinct_colors": ["recolor_every_trail_with_first_source"],
    "long_extension": ["copy_sources_without_extension", "extend_only_one_step"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival fits demos but changes query."""
    reasons: list[str] = []
    profiles: set[str] = set()
    dot_counts: set[int] = set()
    sizes: set[tuple[int, int]] = set()
    for index, demo in enumerate(demos):
        grid = demo.get("input") if isinstance(demo, dict) else None
        if self_check(grid):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo.get("output") != rule_mirror(grid):
            reasons.append(f"demo {index} output disagrees with the diagonal-extension rule")
        profiles.add(_classify_layout(grid) or "invalid")
        dot_counts.add(len(_dot_cells(grid)))
        sizes.add((len(grid), len(grid[0])))

    if profiles != set(LAYOUTS):
        reasons.append(f"demonstrations omit layout evidence: saw {sorted(profiles)}")
    if not {2, 3, 4}.issubset(dot_counts):
        reasons.append(f"demonstrations omit source-count evidence: saw {sorted(dot_counts)}")
    if (3, 3) not in sizes or len(sizes) < 2:
        reasons.append(f"demonstrations do not separate canonical 3x3 from broader sizes: {sorted(sizes)}")

    query_grid = query.get("input") if isinstance(query, dict) else None
    if self_check(query_grid):
        reasons.append("query input is outside the teaching grammar")
    elif isinstance(query, dict) and query.get("output") != rule_mirror(query_grid):
        reasons.append("query output disagrees with the diagonal-extension rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if demos and all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        ):
            if competitor(query_grid) != query.get("output"):
                reasons.append(
                    f"named competitor {name!r} fits every demo but changes the query"
                )
    return reasons
