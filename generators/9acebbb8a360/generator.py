"""Generate two gray rooms whose distinct seeds flood their own interiors.

Rule: each non-0/non-5 marker triggers a BFS over its 4-connected
0-cells through the open part of its 5-room. The visited 0-cells are
repainted with that marker's color.

Ordinary axes: grid_h and grid_w. Explicit malformed fixtures remain
available through ``texture`` names in ``DEGENERATE_TEXTURES`` but are not part
of the ordinary valid override domain.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import bbox_overlaps
from puzzle_generators.helpers.grid import draw_frame, full_grid
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.selfcheck import (
    components,
    components_have_clearance,
    interior_cells,
    is_full_frame_component,
)

GENERATOR_ID = "9acebbb8a360"
VERSION = "1.3.0"
TASK_ID = "9acebbb8a360"
RULE_HASH = "d6506ab5c894"
SUMMARY = (
    "Two separated gray rectangle rooms, each with one distinct-color seed "
    "in its strict interior."
)

INVARIANTS = [
    "background is 0",
    "exactly 2 full-perimeter 5-color rectangle frames (each ≥3×3)",
    "each frame's interior holds exactly one non-0/non-5 marker",
    "the two markers have distinct colors",
    "frames don't touch each other",
]

DEGENERATE_TEXTURES = ("no_frames", "no_markers", "multi_markers")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 8..13",
        "valid": "8..13",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 10..16",
        "valid": "10..16",
    },
}


def _validate_call(seed, sample_index, difficulty, overrides) -> str | None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a non-negative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")

    texture = overrides.get("texture")
    ordinary = set(AXES)
    unknown = sorted(set(overrides) - ordinary - {"texture"})
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(
            f"unsupported texture {texture!r}; expected one of {DEGENERATE_TEXTURES}"
        )
    if texture is not None:
        combined = sorted(
            name
            for name, value in overrides.items()
            if name != "texture" and value is not None
        )
        if combined:
            raise ValueError(
                "degenerate texture cannot be combined with ordinary override(s): "
                + ", ".join(combined)
            )

    for name in ordinary:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    return texture


def generate(seed, sample_index, *, difficulty=None, **overrides):
    texture = _validate_call(seed, sample_index, difficulty, overrides)
    if texture is not None:
        return _draw_from_degenerate(texture)

    ordinary_overrides = {name: overrides[name] for name in AXES if name in overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=ordinary_overrides,
    )
    h = ctx.draw_int_diff("grid_h", 8, 13)
    w = ctx.draw_int_diff("grid_w", 10, 16)
    n_frames = 2

    layout_rng = ctx.draw_rng("layout")
    marker_rng = ctx.draw_rng("markers")
    placed = _place_exactly_two_frames(h, w, layout_rng)
    marker_colors = random_palette(marker_rng, n_frames, exclude={5})

    grid = full_grid(h, w, 0)
    for (r1, c1, r2, c2), marker in zip(placed, marker_colors, strict=True):
        draw_frame(grid, r1, c1, r2, c2, 5)
        sr = layout_rng.randint(r1 + 1, r2 - 1)
        sc = layout_rng.randint(c1 + 1, c2 - 1)
        grid[sr][sc] = marker
    return grid


def _fallback_two_frames(h: int, w: int) -> list[tuple[int, int, int, int]]:
    """Deterministic separated two-frame layout for small legal canvases."""
    # Two 4-wide rooms plus a two-column moat fit exactly in width 10:
    # [0..3] and [6..9].
    if w >= 10 and h >= 4:
        rh = min(5, h)
        rw = max(4, min(5, (w - 3) // 2))
        return [
            (0, 0, rh - 1, rw - 1),
            (0, rw + 2, rh - 1, 2 * rw + 1),
        ]
    # Retained for direct helper use on unusually narrow canvases.
    if h >= 10 and w >= 4:
        rw = min(5, w)
        rh = max(4, min(5, (h - 3) // 2))
        return [
            (0, 0, rh - 1, rw - 1),
            (rh + 2, 0, 2 * rh + 1, rw - 1),
        ]
    raise ValueError(f"canvas {h}x{w} is too small for two separated 4x4 frames")


def _place_exactly_two_frames(
    h: int, w: int, rng
) -> list[tuple[int, int, int, int]]:
    """Randomly place two non-touching frames; never silently emit one frame."""
    n_frames = 2
    for _layout in range(80):
        placed: list[tuple[int, int, int, int]] = []
        for _ in range(160):
            if len(placed) >= n_frames:
                break
            rh = rng.randint(4, min(5, h))
            rw = rng.randint(4, min(5, w))
            r1 = rng.randint(0, h - rh)
            c1 = rng.randint(0, w - rw)
            r2 = r1 + rh - 1
            c2 = c1 + rw - 1
            bb_pad = (r1 - 1, c1 - 1, r2 + 1, c2 + 1)
            if any(
                bbox_overlaps(
                    bb_pad,
                    (p[0] - 1, p[1] - 1, p[2] + 1, p[3] + 1),
                )
                for p in placed
            ):
                continue
            placed.append((r1, c1, r2, c2))
        if len(placed) == n_frames:
            return placed
    return _fallback_two_frames(h, w)


def _draw_from_degenerate(name: str) -> list[list[int]]:
    h, w = 9, 12
    grid = full_grid(h, w, 0)
    if name == "no_frames":
        # Loose markers, no frames — rule has no rooms to flood.
        grid[3][3] = 4
        grid[5][8] = 6
        return grid
    if name == "no_markers":
        # Frames present but no markers — rule has no color to flood with.
        draw_frame(grid, 1, 1, 4, 5, 5)
        draw_frame(grid, 1, 7, 4, 11, 5)
        return grid
    if name == "multi_markers":
        # Multiple markers in one frame — flood color is ambiguous.
        draw_frame(grid, 1, 1, 5, 6, 5)
        grid[2][2] = 4
        grid[3][4] = 6
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    frames = [
        comp
        for comp in components(grid, colors={5})
        if is_full_frame_component(comp, color=5, min_size=3)
    ]
    if len(frames) != 2:
        errs.append(f"expected exactly two full 5-frames, got {len(frames)}")

    marker_colors: list[int] = []
    for frame in frames:
        markers = [
            (r, c, grid[r][c])
            for r, c in interior_cells(frame["bbox"])
            if grid[r][c] not in (0, 5)
        ]
        if len(markers) != 1:
            errs.append("each frame interior should contain exactly one marker")
        else:
            marker_colors.append(markers[0][2])

    if len(marker_colors) == 2 and len(set(marker_colors)) != 2:
        errs.append("the two room markers should use distinct colors")
    if len(frames) == 2 and not components_have_clearance(grid, frames):
        errs.append("frames should not touch")
    return errs

def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical room-fill Racket rule."""
    if not grid:
        return []
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    for sr in range(h):
        for sc in range(w):
            marker = source[sr][sc]
            if marker in (0, 5):
                continue
            queue = [(sr, sc)]
            seen: set[tuple[int, int]] = set()
            cursor = 0
            while cursor < len(queue):
                r, c = queue[cursor]
                cursor += 1
                if (r, c) in seen or not (0 <= r < h and 0 <= c < w):
                    continue
                if (r, c) != (sr, sc) and source[r][c] != 0:
                    continue
                seen.add((r, c))
                if source[r][c] == 0:
                    out[r][c] = marker
                queue.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    return out


def _room_marker_colors(grid: list[list[int]]) -> list[int]:
    frames = sorted(
        (
            comp
            for comp in components(grid, colors={5})
            if is_full_frame_component(comp, color=5, min_size=3)
        ),
        key=lambda comp: comp["bbox"],
    )
    colors: list[int] = []
    for frame in frames:
        markers = [
            grid[r][c]
            for r, c in interior_cells(frame["bbox"])
            if grid[r][c] not in (0, 5)
        ]
        if len(markers) == 1:
            colors.append(markers[0])
    return colors


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_single_global_seed_color(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: use the first seed's color for every room's newly filled cells."""
    truth = rule_mirror(grid)
    markers = [
        grid[r][c]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] not in (0, 5)
    ]
    if not markers:
        return truth
    first = markers[0]
    out = [row[:] for row in truth]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and truth[r][c] not in (0, 5):
                out[r][c] = first
    return out


def strict_canonical_like(grid) -> list[str]:
    """Accept the full canonical two-room manifold, including 3-cell widths."""
    return self_check(grid)


def _witness_nontrivial_room_fill(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != grid


def _witness_distinct_room_colors(grid) -> bool:
    markers = _room_marker_colors(grid)
    return not self_check(grid) and len(markers) == 2 and len(set(markers)) == 2


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "single_global_seed_color": _rival_single_global_seed_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "nontrivial_room_fill": _witness_nontrivial_room_fill,
    "distinct_room_colors": _witness_distinct_room_colors,
}
WITNESS_RIVALS = {
    "nontrivial_room_fill": ["identity"],
    "distinct_room_colors": ["single_global_seed_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared plausible wrong rule survives the demos."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["lesson has no demonstrations"]

    reasons: list[str] = []
    prepared: list[tuple[list[list[int]], list[list[int]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the room-fill rule")
            continue
        prepared.append((pair["input"], pair["output"]))

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is malformed")
        return sorted(set(reasons))
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input invalid: " + "; ".join(query_errors))
        return sorted(set(reasons))
    query_truth = rule_mirror(query["input"])
    if "output" in query and query["output"] != query_truth:
        reasons.append("query output disagrees with the room-fill rule")

    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(inp) == gold for inp, gold in prepared)
        if survives and rival(query["input"]) != query_truth:
            reasons.append(
                f"competing rule {name!r} matches every demo but changes the query"
            )
    return reasons

