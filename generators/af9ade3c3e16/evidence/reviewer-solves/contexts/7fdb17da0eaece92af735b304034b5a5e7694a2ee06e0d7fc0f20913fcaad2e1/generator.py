"""Generator for arc_additional_puzzle_bank_volume21:H143.

Count the red (2) marker cells.  The yellow (4) objects are strictly nested,
hollow rectangular frames.  Ordered by bounding-box area from largest to
smallest (equivalently outermost to innermost), recolor the k-th frame cyan
(8), where k is the red-cell count.

The generated distribution preserves the canonical nested-frame grammar and
includes an independent color-6 triomino distractor.  Exact dimensions, frame
count, and rank are observable and overrideable; incompatible combinations are
rejected rather than silently clamped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af9ade3c3e16"
TASK_ID = "af9ade3c3e16"
VERSION = "3.0.0"  # restore canonical nesting/palette; exact observable override contract
RULE_HASH = "b6731002573d"  # sha256[:12] of whitespace-normalized canonical program_solution

SUMMARY = (
    "A zero-background grid contains two to five strictly nested hollow "
    "yellow(4) rectangular frames and k red(2) marker cells outside the "
    "outer frame. A separate color-6 triomino is an irrelevant distractor. "
    "Order the frames by bounding-box area from largest/outermost to "
    "smallest/innermost and recolor the k-th frame border cyan(8)."
)

INVARIANTS = [
    "two to five hollow color-4 rectangular frames are strictly nested with distinct bounding-box areas",
    "the red-cell count k is in 1..#frames and is the only selector for the changed frame",
    "red markers lie outside the outermost frame and vary independently of k",
    "ordinary generated inputs contain exactly one independent connected color-6 triomino distractor",
    "the input palette is exactly {0,2,4,6}; only the selected color-4 border changes to 8",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "banded draw, enlarged when the selected frame count needs room",
        "valid": "12..24",
    },
    "grid_w": {
        "type": "int",
        "default": "banded draw, enlarged when the selected frame count needs room",
        "valid": "12..26",
    },
    "n_frames": {
        "type": "int",
        "default": "2..3 easy, 2..4 medium, 3..5 hard, subject to explicit canvas/rank feasibility",
        "valid": "2..5",
    },
    "rank": {
        "type": "int",
        "default": "sequential sample_index schedule over 1..n_frames",
        "valid": "1..5",
    },
}

_H_RANGE = (12, 24)
_W_RANGE = (12, 26)
_BAND_H = {
    "easy": (12, 16),
    "medium": (14, 20),
    "hard": (18, 24),
}
_BAND_W = {
    "easy": (12, 18),
    "medium": (14, 22),
    "hard": (18, 26),
}
_BAND_FRAMES = {
    "easy": (2, 3),
    "medium": (2, 4),
    "hard": (3, 5),
}


def _strict_override_int(overrides, name):
    value = overrides.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    return value


def _minimum_canvas(n_frames):
    # Tightest nested stack: 3x3 inner frame plus four cells per outer level,
    # with one empty row/column outside the outer frame on each side.
    return 4 * n_frames + 1


def _max_frames_for_dimension(size):
    return min(5, max(0, (size - 1) // 4))


def _frame(grid, r0, c0, r1, c1, color=4):
    for r in range(r0, r1 + 1):
        grid[r][c0] = color
        grid[r][c1] = color
    for c in range(c0, c1 + 1):
        grid[r0][c] = color
        grid[r1][c] = color


def _component_cells(grid, color):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _rect_border(r0, c0, r1, c1):
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _hollow_rect_bbox(cells):
    if not cells:
        return None
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None
    if set(cells) != _rect_border(r0, c0, r1, c1):
        return None
    return r0, c0, r1, c1


def _frame_bboxes(grid):
    boxes = []
    for cells in _component_cells(grid, 4):
        box = _hollow_rect_bbox(cells)
        if box is not None:
            boxes.append(box)
    return sorted(
        boxes,
        key=lambda box: -((box[2] - box[0] + 1) * (box[3] - box[1] + 1)),
    )


def _strictly_nested(boxes):
    return all(
        outer[0] < inner[0]
        and outer[1] < inner[1]
        and inner[2] < outer[2]
        and inner[3] < outer[3]
        for outer, inner in zip(boxes, boxes[1:])
    )


def _draw_n_frames(ctx, overrides, difficulty):
    h_override = _strict_override_int(overrides, "grid_h")
    w_override = _strict_override_int(overrides, "grid_w")
    rank_override = _strict_override_int(overrides, "rank")
    n_override = _strict_override_int(overrides, "n_frames")

    for name, value, bounds in (
        ("grid_h", h_override, _H_RANGE),
        ("grid_w", w_override, _W_RANGE),
        ("rank", rank_override, (1, 5)),
        ("n_frames", n_override, (2, 5)),
    ):
        if value is not None and not (bounds[0] <= value <= bounds[1]):
            raise ValueError(
                f"{name} override {value} outside [{bounds[0]}, {bounds[1]}]"
            )

    feasible_hi = 5
    if h_override is not None:
        feasible_hi = min(feasible_hi, _max_frames_for_dimension(h_override))
    if w_override is not None:
        feasible_hi = min(feasible_hi, _max_frames_for_dimension(w_override))

    band_lo, band_hi = _BAND_FRAMES.get(difficulty, (2, 5))
    lo = min(band_lo, feasible_hi)
    lo = max(2, lo)
    hi = min(band_hi, feasible_hi)
    if rank_override is not None:
        lo = max(lo, rank_override)
        hi = max(hi, min(rank_override, feasible_hi))
    if n_override is not None:
        lo = hi = n_override

    if hi < lo or feasible_hi < 2:
        detail = {
            key: overrides.get(key)
            for key in ("grid_h", "grid_w", "n_frames", "rank")
            if overrides.get(key) is not None
        }
        raise ValueError(f"incompatible frame/rank/canvas overrides: {detail}")

    n_frames = ctx.draw_int("n_frames", lo, hi)
    if rank_override is not None and rank_override > n_frames:
        raise ValueError(
            f"rank={rank_override} exceeds n_frames={n_frames}; selector is undefined"
        )
    return n_frames


def _draw_dimension(ctx, overrides, label, valid_range, band_range, n_frames):
    required = _minimum_canvas(n_frames)
    if overrides.get(label) is not None:
        value = ctx.draw_int(label, *valid_range)
        if value < required:
            raise ValueError(
                f"{label}={value} cannot fit {n_frames} nested frames; need >= {required}"
            )
        return value
    lo = max(band_range[0], required)
    hi = band_range[1]
    if lo > hi:
        lo, hi = required, valid_range[1]
    return ctx.draw_int(label, lo, hi)


def _draw_rank(ctx, overrides, sample_index, n_frames):
    if overrides.get("rank") is not None:
        return ctx.draw_int("rank", 1, n_frames)
    scheduled = 1 + (sample_index % n_frames)
    return ctx.draw_int("rank", scheduled, scheduled)


def _place_markers(grid, rank, outer_box, rng):
    r0, c0, r1, c1 = outer_box
    candidates = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0 and not (r0 <= r <= r1 and c0 <= c <= c1)
    ]
    rng.shuffle(candidates)
    if len(candidates) < rank:
        raise RuntimeError("not enough exterior cells for rank markers")
    for r, c in candidates[:rank]:
        grid[r][c] = 2


def _triomino_candidates(grid):
    h, w = len(grid), len(grid[0])
    shapes = (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    )
    candidates = []
    for shape in shapes:
        sh = max(dr for dr, _ in shape) + 1
        sw = max(dc for _, dc in shape) + 1
        for r0 in range(h - sh + 1):
            for c0 in range(w - sw + 1):
                cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
                if all(grid[r][c] == 0 for r, c in cells):
                    candidates.append(cells)
    return candidates


def _place_distractor(grid, rng):
    candidates = _triomino_candidates(grid)
    if not candidates:
        raise RuntimeError("no room for color-6 triomino distractor")
    for r, c in rng.choice(candidates):
        grid[r][c] = 6


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    n_frames = _draw_n_frames(ctx, overrides, difficulty)
    h = _draw_dimension(
        ctx,
        overrides,
        "grid_h",
        _H_RANGE,
        _BAND_H.get(difficulty, _H_RANGE),
        n_frames,
    )
    w = _draw_dimension(
        ctx,
        overrides,
        "grid_w",
        _W_RANGE,
        _BAND_W.get(difficulty, _W_RANGE),
        n_frames,
    )
    rank = _draw_rank(ctx, overrides, sample_index, n_frames)

    layout_rng = ctx.draw_rng("layout")
    marker_rng = ctx.draw_rng("markers")
    distractor_rng = ctx.draw_rng("distractor")

    min_outer = 4 * n_frames - 1
    outer_h = layout_rng.randint(min_outer, h - 2)
    outer_w = layout_rng.randint(min_outer, w - 2)
    top = layout_rng.randint(1, h - outer_h - 1)
    left = layout_rng.randint(1, w - outer_w - 1)

    grid = full_grid(h, w, 0)
    boxes = []
    for index in range(n_frames):
        inset = 2 * index
        box = (
            top + inset,
            left + inset,
            top + outer_h - 1 - inset,
            left + outer_w - 1 - inset,
        )
        boxes.append(box)
        _frame(grid, *box)

    _place_markers(grid, rank, boxes[0], marker_rng)
    _place_distractor(grid, distractor_rng)
    return grid


def observe_overrides(grid):
    """Recover every exact declared axis from the returned grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return {}
    boxes = _frame_bboxes(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(boxes),
        "rank": sum(value == 2 for row in grid for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Accept the canonical envelope and reject structural impostors."""
    if not grid or not grid[0]:
        return ["grid must be nonempty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    palette = {value for row in grid for value in row}
    if not palette <= {0, 2, 4, 6}:
        errors.append(f"input palette must be a subset of {{0,2,4,6}}, got {sorted(palette)}")

    boxes = _frame_bboxes(grid)
    all_four_components = _component_cells(grid, 4)
    if len(boxes) != len(all_four_components):
        errors.append("every color-4 component must be a complete hollow rectangle border")
    if not (2 <= len(boxes) <= 5):
        errors.append(f"expected 2..5 hollow color-4 frames, got {len(boxes)}")
    areas = [
        (r1 - r0 + 1) * (c1 - c0 + 1)
        for r0, c0, r1, c1 in boxes
    ]
    if len(areas) != len(set(areas)):
        errors.append("frame bounding-box areas must be distinct")
    if len(boxes) >= 2 and not _strictly_nested(boxes):
        errors.append("frames must be strictly nested from largest to smallest")

    rank = sum(value == 2 for row in grid for value in row)
    if not (1 <= rank <= len(boxes)):
        errors.append(f"red marker count rank={rank} must be in 1..#frames ({len(boxes)})")
    if boxes:
        r0, c0, r1, c1 = boxes[0]
        inside_markers = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 2 and r0 <= r <= r1 and c0 <= c <= c1
        ]
        if inside_markers:
            errors.append("red selector markers must lie outside the outermost frame")

    six_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    if six_cells:
        six_components = _component_cells(grid, 6)
        if len(six_cells) != 3 or len(six_components) != 1:
            errors.append("color-6 distractor, when present, must be one connected triomino")

    return errors
