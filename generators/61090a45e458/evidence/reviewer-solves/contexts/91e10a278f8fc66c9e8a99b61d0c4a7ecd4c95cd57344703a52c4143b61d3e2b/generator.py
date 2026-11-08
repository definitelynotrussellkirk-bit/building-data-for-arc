"""Curriculum generator for ARC task ``61090a45e458``.

Inside every monochrome rectangular frame, exactly one singleton seed and one
larger connected target object appear.  The selected Racket authority recolors
the target object to the seed color while preserving the frame and seed.

The canonical demonstrations always put the target through the interior
upper-left cell.  A three-example schedule therefore keeps one canonical anchor
and supplies two lawful counterexamples with the target elsewhere.  This blocks
the strongest position-only shortcut without changing the authority.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "61090a45e458"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "1041403d0f0a"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "One to three separated rectangular frames each contain one singleton "
    "seed and one connected 2..5-cell target. Recolor every target cell to "
    "its frame's seed color. Generated lessons move targets away from the "
    "canonical interior upper-left anchor."
)

INVARIANTS = [
    "all nonzero cells belong to one of 1..3 separated rectangular frames",
    "each frame interior has exactly one singleton seed and one connected target",
    "frame, seed, and target colors are globally distinct",
    "target size is shared across frames and lies in 2..5",
]

AXES = {
    "n_frames": {
        "type": "int",
        "default": "weighted 1..3; favors canonical two-frame scenes",
        "valid": "1..3",
    },
    "target_size": {
        "type": "int",
        "default": "weighted 2..5; favors canonical sizes 3..4",
        "valid": "2..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = (
    "canonical_top_left",
    "shifted_bottom_right",
    "shifted_vertical",
)

# Exact canonical (height, width, palette-size) profiles when two horizontal
# frames are drawn.  Every listed frame has at least six interior cells, enough
# for a five-cell target plus one seed.
_CANONICAL_TEMPLATES = (
    (10, 12, ((1, 1, 5, 4), (1, 7, 5, 10))),
    (10, 13, ((1, 1, 5, 5), (1, 8, 5, 11))),
    (11, 14, ((1, 1, 6, 5), (2, 9, 6, 12))),
)
_FRAME_SHAPES = (
    (4, 5),
    (5, 4),
    (5, 5),
    (5, 6),
    (6, 5),
    (6, 6),
    (5, 7),
    (7, 5),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive samples always contain all teaching roles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _strict_int_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _general_layout(ctx, n_frames: int, target_size: int, layout: str):
    shapes = [
        shape
        for shape in _FRAME_SHAPES
        if (shape[0] - 2) * (shape[1] - 2) >= target_size + 1
    ]
    rng = ctx.draw_rng("frame_geometry")
    selected = [rng.choice(shapes) for _ in range(n_frames)]
    leading = rng.randint(1, 2)
    trailing = rng.randint(1, 2)
    gap = rng.randint(1, 2)

    if layout == "horizontal":
        height = max(h for h, _ in selected) + leading + trailing
        width = sum(w for _, w in selected) + gap * (n_frames - 1) + 2
        boxes = []
        c = 1
        for i, (fh, fw) in enumerate(selected):
            row_rng = ctx.draw_rng(f"frame_row_{i}")
            r = row_rng.randint(1, height - fh - 1)
            boxes.append((r, c, r + fh - 1, c + fw - 1))
            c += fw + gap
    else:
        height = sum(h for h, _ in selected) + gap * (n_frames - 1) + 2
        width = max(w for _, w in selected) + leading + trailing
        boxes = []
        r = 1
        for i, (fh, fw) in enumerate(selected):
            col_rng = ctx.draw_rng(f"frame_col_{i}")
            c = col_rng.randint(1, width - fw - 1)
            boxes.append((r, c, r + fh - 1, c + fw - 1))
            r += fh + gap
    return height, width, tuple(boxes)


def _layout(ctx, n_frames: int, target_size: int, profile: str):
    if profile in {"canonical_top_left", "shifted_bottom_right"}:
        layout = "horizontal"
    else:
        layout = "vertical"

    if n_frames == 2 and layout == "horizontal":
        height, width, boxes = ctx.draw_rng("canonical_template").choice(
            _CANONICAL_TEMPLATES
        )
        return height, width, boxes
    return _general_layout(ctx, n_frames, target_size, layout)


def _neighbors(cell, height, width):
    r, c = cell
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _target_and_seed(height, width, size, mode, rng):
    if mode == "top_left":
        anchor = (0, 0)
        seed = (height - 1, width - 1)
    elif mode == "bottom_right":
        anchor = (height - 1, width - 1)
        seed = (0, 0)
    else:
        seed = (0, 0)
        anchor = (height // 2, width // 2)
        if anchor == seed:
            anchor = (height - 1, width - 1)

    allowed = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) != seed
    }
    if anchor not in allowed or len(allowed) < size:
        raise ValueError("frame interior cannot fit requested target and seed")

    chosen = {anchor}
    while len(chosen) < size:
        frontier = {
            neighbor
            for cell in chosen
            for neighbor in _neighbors(cell, height, width)
            if neighbor in allowed and neighbor not in chosen
        }
        if not frontier:
            raise RuntimeError("connected target growth exhausted unexpectedly")
        # Prefer compact growth while preserving keyed shape variation.
        distances = {
            cell: abs(cell[0] - anchor[0]) + abs(cell[1] - anchor[1])
            for cell in frontier
        }
        best = min(distances.values())
        compact = sorted(cell for cell in frontier if distances[cell] <= best + 1)
        chosen.add(rng.choice(compact))
    return tuple(sorted(chosen)), seed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_int_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_frames = ctx.draw_choice("n_frames", (1, 2, 2, 2, 3))
    if overrides.get("target_size") is not None:
        target_size_options = (2, 3, 4, 5)
    else:
        target_size_options = {
            "easy": (2, 2, 3, 3),
            "medium": (3, 3, 4, 4),
            "hard": (4, 4, 5, 5),
        }.get(difficulty, (2, 3, 3, 4, 4, 5))
    target_size = ctx.draw_choice("target_size", target_size_options)
    profile = schedule_profile(seed, sample_index, difficulty)
    height, width, boxes = _layout(ctx, n_frames, target_size, profile)
    grid = full_grid(height, width, 0)
    colors = ctx.draw_rng("palette").sample(range(1, 10), n_frames * 3)

    if profile == "canonical_top_left":
        mode = "top_left"
    elif profile == "shifted_bottom_right":
        mode = "bottom_right"
    else:
        mode = "center"

    for index, (r1, c1, r2, c2) in enumerate(boxes):
        frame_color, seed_color, target_color = colors[index * 3 : index * 3 + 3]
        draw_frame(grid, r1, c1, r2, c2, frame_color)
        interior_h, interior_w = r2 - r1 - 1, c2 - c1 - 1
        target, seed_cell = _target_and_seed(
            interior_h,
            interior_w,
            target_size,
            mode,
            ctx.draw_rng(f"target_shape_{index}"),
        )
        for rr, cc in target:
            grid[r1 + 1 + rr][c1 + 1 + cc] = target_color
        sr, sc = seed_cell
        grid[r1 + 1 + sr][c1 + 1 + sc] = seed_color
    return grid


def _rectangular_grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected nonempty rows"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer colors 0..9"
    if len(grid) > 30 or width > 30:
        return "grid exceeds ARC's 30x30 bound"
    return None


def _is_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for neighbor in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _frame_from_cells(color, cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if height < 3 or width < 3:
        return None
    expected = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if set(cells) != expected:
        return None
    return {
        "frame_color": color,
        "bbox": (r1, c1, r2, c2),
        "border": expected,
    }


def _analyze(grid):
    malformed = _rectangular_grid_error(grid)
    if malformed:
        return [malformed], []

    by_color = defaultdict(list)
    nonzero = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color[value].append((r, c))
                nonzero.add((r, c))

    frames = []
    for color, cells in by_color.items():
        frame = _frame_from_cells(color, cells)
        if frame is not None:
            frames.append(frame)
    frames.sort(key=lambda frame: frame["bbox"])

    errors = []
    if not 1 <= len(frames) <= 3:
        errors.append(f"expected 1..3 rectangular frames, found {len(frames)}")

    covered = set()
    details = []
    for frame in frames:
        r1, c1, r2, c2 = frame["bbox"]
        area = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        if covered & area:
            errors.append("frame rectangles overlap")
        covered |= area

        interior_by_color = defaultdict(list)
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                value = grid[r][c]
                if value:
                    interior_by_color[value].append((r, c))
        if len(interior_by_color) != 2:
            errors.append(
                f"frame {frame['bbox']} must contain exactly two interior colors"
            )
            continue
        seeds = [
            (color, cells)
            for color, cells in interior_by_color.items()
            if len(cells) == 1
        ]
        targets = [
            (color, cells)
            for color, cells in interior_by_color.items()
            if len(cells) > 1
        ]
        if len(seeds) != 1 or len(targets) != 1:
            errors.append(
                f"frame {frame['bbox']} needs one singleton seed and one larger target"
            )
            continue
        seed_color, seed_cells = seeds[0]
        target_color, target_cells = targets[0]
        if not 2 <= len(target_cells) <= 5:
            errors.append(
                f"frame {frame['bbox']} target size {len(target_cells)} outside 2..5"
            )
        if not _is_connected(target_cells):
            errors.append(f"frame {frame['bbox']} target must be 4-connected")
        details.append(
            {
                **frame,
                "seed_color": seed_color,
                "seed_cells": tuple(seed_cells),
                "target_color": target_color,
                "target_cells": tuple(target_cells),
            }
        )

    if nonzero - covered:
        errors.append("nonzero cells occur outside every frame rectangle")
    role_colors = []
    for detail in details:
        role_colors.extend(
            [
                detail["frame_color"],
                detail["seed_color"],
                detail["target_color"],
            ]
        )
    if len(role_colors) != len(set(role_colors)):
        errors.append("frame, seed, and target colors must be globally distinct")
    if details and len(details) != len(frames):
        errors.append("one or more frames could not be analyzed")
    return errors, details


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors, _ = _analyze(grid)
    return errors


def strict_canonical_like(grid):
    """Accept the intended task manifold, including all canonical inputs."""
    return self_check(grid)


def observe_overrides(grid):
    errors, frames = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    sizes = {len(frame["target_cells"]) for frame in frames}
    if len(sizes) != 1:
        raise ValueError("generated exact target_size is not recoverable")
    return {"n_frames": len(frames), "target_size": next(iter(sizes))}


def _top_left_target_only(grid):
    """Wrong rival: recolor only a target occupying the interior upper-left."""
    out = deepcopy(grid)
    errors, frames = _analyze(grid)
    if errors:
        return out
    for frame in frames:
        r1, c1, _, _ = frame["bbox"]
        if (r1 + 1, c1 + 1) not in set(frame["target_cells"]):
            continue
        for r, c in frame["target_cells"]:
            out[r][c] = frame["seed_color"]
    return out


def _target_not_top_left(grid):
    errors, frames = _analyze(grid)
    if errors:
        return False
    return any(
        (frame["bbox"][0] + 1, frame["bbox"][1] + 1)
        not in set(frame["target_cells"])
        for frame in frames
    )


def lesson_identifiable(demos, query):
    """A lesson must visibly refute the canonical top-left target shortcut."""
    del query
    for pair in demos:
        try:
            if _top_left_target_only(pair["input"]) != pair["output"]:
                return []
        except Exception:
            continue
    return ["no demonstration refutes the interior-top-left target shortcut"]


SEMANTIC_WITNESSES = {"target_not_top_left": _target_not_top_left}
SEMANTIC_RIVALS = {"top_left_target_only": _top_left_target_only}
WITNESS_RIVALS = {"target_not_top_left": ["top_left_target_only"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
