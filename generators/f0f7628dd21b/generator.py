"""Independent generator family for ARC task 83b6b474.

Construction differs from the existing 9733a2d68593 family.  This module first
constructs one coherent square output frame, cuts that frame into the five
semantic roles, and only then scatters those pieces into the input grid.  The
existing family samples each role shape independently before scattering it.

The generator deliberately aliases the reviewed canonical rule owned by
``9733a2d68593``.  The runner records that alias in its bundle/receipts; it does
not duplicate or silently fork the rule.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f0f7628dd21b"
TASK_ID = GENERATOR_ID
SOURCE_TASK_ID = "83b6b474"
RULE_TASK_ID = "9733a2d68593"
RULE_HASH = "83938db8863a"
VERSION = "1.1.0"
CONSTRUCTION_ALGORITHM_ID = "assembled-frame-cut-and-scatter-v1"

SUMMARY = (
    "Construct a compact square border frame first, cut it into top-left, top, "
    "bottom-left, bottom-right, and side roles, then scatter the five distinctly "
    "coloured pieces on a nonzero modal-background grid. The canonical rule "
    "must recover role geometry and repack the pieces into the source frame."
)

INVARIANTS = [
    "the modal background is nonzero",
    "there are exactly five same-colour 4-connected foreground objects",
    "the five objects classify one-to-one as top-left, top, bottom-left, bottom-right, and side",
    "role shapes are cut from one coherent square output frame before scattering",
    "bottom-left and bottom-right anchors are scattered on opposite horizontal thirds",
]

ROLE_ORDER = ("top-left", "top", "bottom-left", "bottom-right", "side")

AXES = {
    "assembled_n": {"type": "int", "default": "6..10", "valid": "6..10"},
    "top_left_width": {"type": "int", "default": "2..4", "valid": "2..4"},
    "top_left_height": {"type": "int", "default": "2..5", "valid": "2..5"},
    "bottom_left_width": {"type": "int", "default": "2..n-2", "valid": "2..8"},
    "bottom_left_height": {"type": "int", "default": "2..5", "valid": "2..5"},
    "bottom_right_height": {"type": "int", "default": "2..5", "valid": "2..5"},
    "side_height": {"type": "int", "default": "2..4", "valid": "2..4"},
    "side_edge": {"type": "str", "default": "left|right", "valid": "left|right"},
    "grid_h": {"type": "int", "default": "14..18", "valid": "14..18"},
    "grid_w": {"type": "int", "default": "20..24", "valid": "20..24"},
    "colors": {"type": "tuple[int]", "default": "six distinct nonzero colors", "valid": "1..9 distinct"},
}


def _shape_from_output(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    points = list(cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return sorted((r - r0, c - c0) for r, c in points)


def _frame_decomposition(ctx) -> tuple[int, dict[str, list[tuple[int, int]]], str]:
    """Build one square frame and cut it into the five semantic pieces."""
    n = ctx.draw_int("assembled_n", 6, 10)
    tl_w = ctx.draw_int("top_left_width", 2, min(4, n - 2))
    bl_w = ctx.draw_int("bottom_left_width", 2, n - 2)
    br_w = n - bl_w

    # These pieces are claimed to be a CUT of one coherent frame, so they
    # must be pairwise disjoint in that frame. Reserve room on either vertical
    # edge for a top-left leg, the side segment, and a bottom-corner leg.  The
    # same bottom-height range is used on both sides so the chosen side is not
    # leaked by the draw distribution.
    side_h = ctx.draw_int("side_height", 2, min(4, n - 4))
    tl_h = ctx.draw_int("top_left_height", 2, min(5, n - side_h - 2))
    bottom_h_max = min(5, n - side_h - tl_h)
    bl_h = ctx.draw_int("bottom_left_height", 2, bottom_h_max)
    br_h = ctx.draw_int("bottom_right_height", 2, bottom_h_max)
    side_edge = ctx.draw_choice("side_edge", ("left", "right"))

    pieces: dict[str, list[tuple[int, int]]] = {
        "top-left": [(0, c) for c in range(tl_w)]
        + [(r, 0) for r in range(1, tl_h)],
        "top": [(0, c) for c in range(tl_w, n)],
        "bottom-left": [(n - 1, c) for c in range(bl_w)]
        + [(r, 0) for r in range(n - bl_h, n - 1)],
        "bottom-right": [(n - 1, c) for c in range(bl_w, n)]
        + [(r, n - 1) for r in range(n - br_h, n - 1)],
    }
    side_col = 0 if side_edge == "left" else n - 1
    bottom_h = bl_h if side_edge == "left" else br_h
    side_r0 = n - bottom_h - side_h
    assert side_r0 >= tl_h
    pieces["side"] = [(side_r0 + r, side_col) for r in range(side_h)]
    return n, {role: _shape_from_output(cells) for role, cells in pieces.items()}, side_edge


def _scatter(
    grid: list[list[int]],
    shape: list[tuple[int, int]],
    color: int,
    bg: int,
    rng,
    *,
    prefer: str | None = None,
) -> tuple[int, int]:
    """Scatter one shape with a one-cell halo from every prior object."""
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates: list[tuple[int, int]] = []
    for r0 in range(h - sh + 1):
        for c0 in range(w - sw + 1):
            if prefer == "left" and c0 > w // 3:
                continue
            if prefer == "right" and c0 < (2 * w) // 3 - sw:
                continue
            cells = {(r0 + r, c0 + c) for r, c in shape}
            halo = {
                (rr + dr, cc + dc)
                for rr, cc in cells
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
            }
            if any(
                grid[rr][cc] != bg
                for rr, cc in halo
                if 0 <= rr < h and 0 <= cc < w
            ):
                continue
            candidates.append((r0, c0))
    if not candidates:
        raise RuntimeError(f"cannot scatter {shape!r} in {h}x{w}")
    r0, c0 = rng.choice(candidates)
    for r, c in shape:
        grid[r0 + r][c0 + c] = color
    return r0, c0


def _modal(grid: list[list[int]]) -> int:
    return Counter(v for row in grid for v in row).most_common(1)[0][0]


def _objects(grid: list[list[int]], bg: int) -> list[dict[str, Any]]:
    """Same-colour, four-connected non-background objects."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            color = grid[r][c]
            queue: deque[tuple[int, int]] = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            out.append(
                {
                    "color": color,
                    "cells": sorted((rr - r0, cc - c0) for rr, cc in cells),
                    "hh": r1 - r0 + 1,
                    "ww": c1 - c0 + 1,
                }
            )
    return out


def _classify(obj: dict[str, Any]) -> str:
    cells = set(obj["cells"])
    hh, ww = int(obj["hh"]), int(obj["ww"])

    def full_row(r: int) -> bool:
        return all((r, c) in cells for c in range(ww))

    def full_col(c: int) -> bool:
        return all((r, c) in cells for r in range(hh))

    if hh == 1 and ww > 1:
        return "top"
    if hh > 1 and ww > 1 and full_row(0) and full_col(0):
        return "top-left"
    if hh > 1 and ww > 1 and full_row(hh - 1) and full_col(0):
        return "bottom-left"
    if hh > 1 and ww > 1 and full_row(hh - 1) and full_col(ww - 1):
        return "bottom-right"
    return "side"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    bg = _modal(grid)
    if bg == 0:
        return ["expected nonzero modal background"]
    objects = _objects(grid, bg)
    if len(objects) != 5:
        return [f"expected exactly 5 foreground objects; found {len(objects)}"]
    roles = Counter(_classify(obj) for obj in objects)
    expected = Counter({role: 1 for role in ROLE_ORDER})
    if roles != expected:
        return [f"expected role counts {dict(expected)}; found {dict(roles)}"]
    if len({obj["color"] for obj in objects}) != 5:
        return ["expected five distinct foreground colors"]
    return []


def generate_with_metadata(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n, shapes, side_edge = _frame_decomposition(ctx)
    if difficulty == "easy":
        h, w = 14, 20
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", max(16, n + 6), 18)
        w = ctx.draw_int("grid_w", max(22, n + 10), 24)
    else:
        h = ctx.draw_int("grid_h", max(14, n + 5), 18)
        w = ctx.draw_int("grid_w", max(20, n + 8), 24)
    palette = ctx.draw_distinct_colors("colors", n=6, exclude={0})
    bg, colors = palette[0], palette[1:]

    last_error: Exception | None = None
    for attempt in range(32):
        grid = full_grid(h, w, bg)
        rng = ctx.draw_rng(f"scatter-{attempt}")
        placements: dict[str, tuple[int, int]] = {}
        try:
            for role, color in zip(ROLE_ORDER, colors):
                prefer = (
                    "left"
                    if role == "bottom-left"
                    or (role == "side" and side_edge == "left")
                    else "right"
                    if role == "bottom-right"
                    or (role == "side" and side_edge == "right")
                    else None
                )
                placements[role] = _scatter(
                    grid, shapes[role], color, bg, rng, prefer=prefer
                )
        except RuntimeError as exc:
            last_error = exc
            continue
        findings = self_check(grid)
        if findings:
            last_error = ValueError("; ".join(findings))
            continue

        # The construction claim is only useful supervision if it survives
        # scattering into the model-visible task.  The canonical rule decides
        # which wall receives the side piece from its horizontal proximity to
        # the two bottom corners.  Reject placements where that visible signal
        # contradicts the hidden frame edge chosen above; otherwise the emitted
        # (input, output) pair would no longer reconstruct the frame that was
        # supposedly built first.
        def center2(role: str) -> int:
            _r0, c0 = placements[role]
            width = max(c for _r, c in shapes[role]) + 1
            return 2 * c0 + width - 1

        semantic_side_edge = (
            "left"
            if abs(center2("side") - center2("bottom-left"))
            <= abs(center2("side") - center2("bottom-right"))
            else "right"
        )
        if semantic_side_edge != side_edge:
            last_error = ValueError(
                "scattering erased frame-side semantics: "
                f"constructed={side_edge}, visible={semantic_side_edge}"
            )
            continue

        return {
            "grid": grid,
            "metadata": {
                "assembled_n": n,
                "side_edge": side_edge,
                "semantic_side_edge": semantic_side_edge,
                "background": bg,
                "role_shapes": {
                    role: [list(cell) for cell in shape]
                    for role, shape in shapes.items()
                },
                "scatter_placements": {
                    role: list(position) for role, position in placements.items()
                },
                "construction_algorithm_id": CONSTRUCTION_ALGORITHM_ID,
                "rule_task_id": RULE_TASK_ID,
                "draws": ctx.recorded_draws(),
            },
        }
    raise RuntimeError(f"failed to scatter a valid instance after 32 attempts: {last_error}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    return generate_with_metadata(
        seed, sample_index, difficulty=difficulty, **overrides
    )["grid"]
