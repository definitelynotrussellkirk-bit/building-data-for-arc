"""Generator for cc07013acae1:H65 — infer a whole-panel transform.

Two full-height color-5 divider columns split the input into square panels
A, B, and C.  Infer the unique non-identity transform mapping A to B, then
return that transform applied to panel C.  The output is the transformed C
panel alone, not the original three-panel strip.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "63784d19dd2d"
TASK_ID = "63784d19dd2d"
VERSION = "3.0.0"  # honest boundaries/difficulty, visible query transform, structural checker
RULE_HASH = "7e42f2b65a1e"  # comment-stripped/whitespace-normalized canonical rule

SUMMARY = (
    "A 0-background N×(3N+2) input is split by two full-height color-5 "
    "divider columns into square N×N panels A, B, and C. A and B use the "
    "same non-{0,5} color, while C uses a different color. Exactly one "
    "non-identity transform in {rotate-cw, rotate-180, flip-ud, flip-lr} "
    "maps the complete panel A to panel B. Infer that transform and apply "
    "it to panel C. The oracle output is only the transformed N×N C panel."
)

INVARIANTS = [
    "background is 0 and the only divider color is 5",
    "two full-height color-5 columns split the input into three square N×N panels",
    "A and B are single-color connected shapes in the same color",
    "C is a non-empty connected single-color shape in a different color",
    "exactly one non-identity transform maps the complete A panel to B",
    "ordinary generated draws make the selected transform visibly change C",
    "the Racket output is transform(C) as an N×N panel, not the full input strip",
]

AXES = {
    "panel_n": {
        "type": "int",
        "default": "difficulty-linked draw over 3..7",
        "valid": "3..7",
    },
    "transform": {
        "type": "int",
        "default": "rng 2..5",
        "valid": "2..5",
    },
}

_TRANSFORMS = (1, 2, 3, 4, 5)
_NON_IDENTITY_TRANSFORMS = (2, 3, 4, 5)


def _xform(cells, code: int, n: int):
    """Transform a cell iterable inside an n×n panel."""
    cells = list(cells)
    if code == 1:
        return list(cells)
    if code == 2:
        return [(c, n - 1 - r) for r, c in cells]  # clockwise 90°
    if code == 3:
        return [(n - 1 - r, n - 1 - c) for r, c in cells]  # 180°
    if code == 4:
        return [(n - 1 - r, c) for r, c in cells]  # flip up/down
    if code == 5:
        return [(r, n - 1 - c) for r, c in cells]  # flip left/right
    raise ValueError(f"unknown transform code: {code}")


def _xform_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    """Apply the canonical whole-panel transform to a square grid."""
    n = len(grid)
    if not grid or any(len(row) != n for row in grid):
        raise ValueError("whole-panel transform requires a non-empty square grid")
    out = full_grid(n, n, 0)
    for r in range(n):
        for c in range(n):
            nr, nc = _xform([(r, c)], code, n)[0]
            out[nr][nc] = grid[r][c]
    return out


def _random_shape(rng, n: int, k: int) -> list[tuple[int, int]]:
    """Draw a connected k-cell polyomino inside an n×n panel."""
    if not (1 <= k <= n * n):
        raise ValueError(f"shape size {k} is invalid for {n}x{n}")
    first = (rng.randint(0, n - 1), rng.randint(0, n - 1))
    cells = [first]
    seen = {first}
    while len(cells) < k:
        boundary = []
        for r, c in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
                    boundary.append((nr, nc))
        if not boundary:
            raise ValueError("connected-shape frontier unexpectedly exhausted")
        cell = rng.choice(boundary)
        cells.append(cell)
        seen.add(cell)
    return cells


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    pending = deque([next(iter(cells))])
    seen = {pending[0]}
    while pending:
        r, c = pending.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (nr, nc) in cells and (nr, nc) not in seen:
                seen.add((nr, nc))
                pending.append((nr, nc))
    return seen == cells


def _panel(grid: list[list[int]], left: int, n: int) -> list[list[int]]:
    return [row[left:left + n] for row in grid]


def _support(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 5)
    }


def _panel_colors(panel: list[list[int]]) -> set[int]:
    return {value for row in panel for value in row if value not in (0, 5)}


def analyze_grid(grid: Any) -> dict[str, Any]:
    """Return task-linked observables and fail-closed structural diagnostics."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"]}
    if any(not isinstance(row, list) for row in grid):
        return {"errors": ["every grid row must be a list"]}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular with non-empty rows"]}
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")

    h = len(grid)
    seps = [c for c in range(width) if all(grid[r][c] == 5 for r in range(h))]
    if len(seps) != 2:
        errors.append(f"expected exactly two full-height color-5 dividers, got {seps}")
        return {"errors": errors, "height": h, "width": width, "separators": seps}

    n = seps[0]
    expected_seps = [n, 2 * n + 1]
    if not 3 <= n <= 7:
        errors.append(f"panel_n must be in 3..7, got {n}")
    if h != n or width != 3 * n + 2 or seps != expected_seps:
        errors.append(
            "dividers do not form three square panels: "
            f"h={h}, w={width}, separators={seps}, expected={expected_seps}"
        )
        return {
            "errors": errors,
            "height": h,
            "width": width,
            "panel_n": n,
            "separators": seps,
        }

    panels = (
        _panel(grid, 0, n),
        _panel(grid, n + 1, n),
        _panel(grid, 2 * n + 2, n),
    )
    names = ("A", "B", "C")
    for name, panel in zip(names, panels):
        if any(value == 5 for row in panel for value in row):
            errors.append(f"panel {name} contains divider color 5")

    supports = tuple(_support(panel) for panel in panels)
    colors = tuple(_panel_colors(panel) for panel in panels)
    for name, support, palette in zip(names, supports, colors):
        if len(support) < 3:
            errors.append(f"panel {name} must contain at least three shape cells")
        if len(palette) != 1:
            errors.append(f"panel {name} must use exactly one non-background color, got {sorted(palette)}")
        if support and not _connected(support):
            errors.append(f"panel {name} shape must be 4-connected")

    if len(colors[0]) == len(colors[1]) == 1 and colors[0] != colors[1]:
        errors.append("panels A and B must use the same color for full-grid equality")
    if len(colors[0]) == len(colors[2]) == 1 and colors[0] == colors[2]:
        errors.append("panel C must use a different color from A/B")

    matches = [
        code
        for code in _TRANSFORMS
        if _xform_grid(panels[0], code) == panels[1]
    ]
    if len(matches) != 1:
        errors.append(f"A->B transform is ambiguous or missing: {matches}")
    elif matches[0] == 1:
        errors.append("A->B identity transform hides the intended operation")

    transform = matches[0] if len(matches) == 1 else None
    transformed_c = _xform_grid(panels[2], transform) if transform is not None else None
    return {
        "errors": sorted(set(errors)),
        "height": h,
        "width": width,
        "panel_n": n,
        "separators": seps,
        "panels": panels,
        "supports": supports,
        "colors": tuple(next(iter(palette)) if len(palette) == 1 else None for palette in colors),
        "transform_matches": matches,
        "transform": transform,
        "shape_sizes": tuple(len(support) for support in supports),
        "query_transform_visible": transformed_c != panels[2] if transformed_c is not None else False,
        "output": transformed_c,
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = analyze_grid(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "panel_n": int(analysis["panel_n"]),
        "transform": int(analysis["transform"]),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python parity mirror; the canonical Racket program remains authoritative."""
    analysis = analyze_grid(grid)
    if analysis.get("errors"):
        raise ValueError("invalid lesson input: " + "; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n = ctx.draw_int_diff("panel_n", 3, 7)
    transform = ctx.draw_int("transform", 2, 5)
    color_a, color_c = ctx.draw_distinct_colors(
        "panel_colors", n=2, exclude={0, 5}
    )
    rng = ctx.draw_rng("layout")

    height = n
    width = 3 * n + 2
    d1, d2 = n, 2 * n + 1
    max_shape = min(n * n - 1, n + 3)

    for _ in range(240):
        cells_a = _random_shape(rng, n, rng.randint(3, max_shape))
        cells_b = _xform(cells_a, transform, n)
        matches = [
            code
            for code in _TRANSFORMS
            if set(_xform(cells_a, code, n)) == set(cells_b)
        ]
        if matches != [transform]:
            continue

        cells_c = _random_shape(rng, n, rng.randint(3, max_shape))
        cells_out = _xform(cells_c, transform, n)
        support_a, support_b = set(cells_a), set(cells_b)
        support_c, support_out = set(cells_c), set(cells_out)
        # The query must visibly exercise the selected transform and must not
        # collapse to copying A or B by position alone.
        if support_out == support_c:
            continue
        if support_c in (support_a, support_b) or support_out in (support_a, support_b):
            continue

        grid = full_grid(height, width, 0)
        for r in range(height):
            grid[r][d1] = 5
            grid[r][d2] = 5
        for r, c in cells_a:
            grid[r][c] = color_a
        for r, c in cells_b:
            grid[r][d1 + 1 + c] = color_a
        for r, c in cells_c:
            grid[r][d2 + 1 + c] = color_c

        analysis = analyze_grid(grid)
        if not analysis["errors"] and analysis["query_transform_visible"]:
            return grid

    raise ValueError(
        f"could not realize an unambiguous visible panel transform for n={n}, "
        f"transform={transform} in 240 attempts"
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(analyze_grid(grid).get("errors", ["grid analysis failed"]))
