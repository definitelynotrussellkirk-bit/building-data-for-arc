"""Generator for 926c6bd137d3 — fill each yellow frame from its marker.

A lawful input contains one to four disjoint hollow yellow rectangular frames.
Every frame has exactly one non-background, non-yellow marker in its interior.
The output fills the remaining zero cells of each frame interior with that
frame's marker color while preserving frame borders, marker cells, and all
cells outside the frame boxes.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "926c6bd137d3"
TASK_ID = "926c6bd137d3"
VERSION = "3.0.0"
RULE_HASH = "575c55ee70e4"

SUMMARY = (
    "A 10-18 by 10-18 zero-background grid contains one to four separated "
    "hollow yellow (4) rectangular frames, each 4-6 cells tall and wide. "
    "Every frame interior contains exactly one marker whose color is neither "
    "0 nor 4. One to four non-yellow distractor cells also lie outside all "
    "frame boxes. For each frame independently, fill only its zero-valued "
    "interior cells with that frame's marker color; preserve marker cells, "
    "yellow borders, and every exterior cell."
)

INVARIANTS = [
    "background is color 0",
    "every yellow component is exactly a hollow rectangular frame",
    "frames are pairwise disjoint and not nested",
    "each frame interior contains exactly one nonzero non-yellow marker",
    "ordinary generated inputs contain exterior non-yellow distractor cells",
    "the rule preserves all cells outside frame interiors",
]

MARKER_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {"type": "int", "default": "canonical schedule", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "canonical schedule", "valid": "10..18"},
    "n_frames": {"type": "int", "default": "schedule 1..4", "valid": "1..4"},
    "n_exterior_distractors": {
        "type": "int",
        "default": "schedule 1..4",
        "valid": "1..4",
    },
}

Grid = list[list[int]]
Frame = tuple[int, int, int, int]  # inclusive r0, c0, r1, c1

# Each residue is an exact canonical (height, width, palette-size) profile.
# The palette size follows from n_frames: 1 -> 4, 2 -> 5, 3 -> 5, 4 -> 6.
_DEFAULTS = (
    (12, 13, 1),
    (12, 11, 2),
    (13, 11, 3),
    (14, 12, 4),
)
SCHEDULE_PROFILES = (
    "one_frame",
    "two_distinct_markers",
    "three_frames_with_repetition",
    "four_frames_three_marker_colors",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 4


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-row teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _draw_int_axis(
    ctx, overrides: dict[str, Any], label: str, lo: int, hi: int, scheduled: int
) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _axis_halves(length: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Two inclusive spans of length >=4 separated by one unused coordinate."""
    first_size = (length - 1) // 2
    second_start = first_size + 1
    return (0, first_size - 1), (second_start, length - 1)


def _marker_palette(seed: int, sample_index: int, n_frames: int) -> tuple[list[int], int]:
    """Marker assignment plus a distinct exterior color.

    The first profile in each four-example block advances through all eight
    legal marker colors. Thus every eight blocks cover the full task palette,
    while each individual row has a canonical palette cardinality.
    """
    block = int(sample_index) // LESSON_SCHEDULE_PERIOD
    offset = (int(seed) + block) % len(MARKER_COLORS)
    ordered = MARKER_COLORS[offset:] + MARKER_COLORS[:offset]
    unique_needed = {1: 1, 2: 2, 3: 2, 4: 3}[n_frames]
    distinct = list(ordered[:unique_needed])
    markers = [distinct[index % unique_needed] for index in range(n_frames)]
    exterior_color = next(color for color in ordered if color not in distinct)
    return markers, exterior_color


def _draw_scene(
    *,
    h: int,
    w: int,
    n_frames: int,
    n_exterior_distractors: int,
    marker_colors: list[int],
    exterior_color: int,
    max_frame_size: int,
    rng,
) -> Grid:
    grid = full_grid(h, w, 0)
    row_spans = _axis_halves(h)
    col_spans = _axis_halves(w)
    slots = [
        (row_span[0], col_span[0], row_span[1], col_span[1])
        for row_span in row_spans
        for col_span in col_spans
    ]
    rng.shuffle(slots)
    selected = slots[:n_frames]
    rng.shuffle(marker_colors)

    frames: list[Frame] = []
    for slot, marker_color in zip(selected, marker_colors):
        sr0, sc0, sr1, sc1 = slot
        slot_h = sr1 - sr0 + 1
        slot_w = sc1 - sc0 + 1
        frame_h = rng.randint(4, min(max_frame_size, slot_h))
        frame_w = rng.randint(4, min(max_frame_size, slot_w))
        r0 = rng.randint(sr0, sr1 - frame_h + 1)
        c0 = rng.randint(sc0, sc1 - frame_w + 1)
        draw_rect_outline(grid, r0, c0, frame_h, frame_w, 4)
        r1, c1 = r0 + frame_h - 1, c0 + frame_w - 1
        mr = rng.randint(r0 + 1, r1 - 1)
        mc = rng.randint(c0 + 1, c1 - 1)
        grid[mr][mc] = marker_color
        frames.append((r0, c0, r1, c1))

    exterior_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0
        and all(not (r0 <= r <= r1 and c0 <= c <= c1)
                for r0, c0, r1, c1 in frames)
    ]
    if len(exterior_candidates) < n_exterior_distractors:
        raise RuntimeError(
            "constructive layout left too few exterior cells: "
            f"need {n_exterior_distractors}, have {len(exterior_candidates)}"
        )
    for r, c in rng.sample(exterior_candidates, n_exterior_distractors):
        grid[r][c] = exterior_color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
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
    scheduled_h, scheduled_w, scheduled_frames = _DEFAULTS[
        sample_index % LESSON_SCHEDULE_PERIOD
    ]
    # Deliberately independent of the frame-count residue. Across blocks, each
    # n_frames value co-occurs with every exterior count instead of forming a
    # misleading one-to-one proxy axis.
    scheduled_exterior = 1 + (
        seed + sample_index // LESSON_SCHEDULE_PERIOD
        + 2 * (sample_index % LESSON_SCHEDULE_PERIOD)
    ) % 4
    h = _draw_int_axis(ctx, overrides, "grid_h", 10, 18, scheduled_h)
    w = _draw_int_axis(ctx, overrides, "grid_w", 10, 18, scheduled_w)
    n_frames = _draw_int_axis(ctx, overrides, "n_frames", 1, 4, scheduled_frames)
    n_exterior = _draw_int_axis(
        ctx,
        overrides,
        "n_exterior_distractors",
        1,
        4,
        scheduled_exterior,
    )

    marker_colors, exterior_color = _marker_palette(seed, sample_index, n_frames)
    return _draw_scene(
        h=h,
        w=w,
        n_frames=n_frames,
        n_exterior_distractors=n_exterior,
        marker_colors=marker_colors,
        exterior_color=exterior_color,
        max_frame_size={None: 5, "easy": 4, "medium": 5, "hard": 6}[difficulty],
        rng=ctx.draw_rng(f"placement:{difficulty or 'default'}"),
    )


def _components_of(grid: Grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    cells.append(neighbor)
        components.append(sorted(cells))
    return components


def _bbox(cells: list[tuple[int, int]]) -> Frame:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _border(frame: Frame) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = frame
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _boxes_overlap(a: Frame, b: Frame) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _inside(frame: Frame, r: int, c: int) -> bool:
    r0, c0, r1, c1 = frame
    return r0 < r < r1 and c0 < c < c1


def _in_box(frame: Frame, r: int, c: int) -> bool:
    r0, c0, r1, c1 = frame
    return r0 <= r <= r1 and c0 <= c <= c1


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list"]
    if not all(isinstance(row, list) for row in grid):
        return {}, ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {}, ["grid must be nonempty and rectangular"]

    h, w = len(grid), width
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell {(r, c)} must be an integer color in 0..9")
    if errors:
        return {"grid_h": h, "grid_w": w}, errors

    frames: list[Frame] = []
    for component in _components_of(grid, 4):
        frame = _bbox(component)
        frame_h = frame[2] - frame[0] + 1
        frame_w = frame[3] - frame[1] + 1
        if set(component) != _border(frame):
            errors.append(
                f"yellow component at {frame} is not exactly a hollow rectangular frame"
            )
            continue
        if not (4 <= frame_h <= 6 and 4 <= frame_w <= 6):
            errors.append(
                f"yellow frame at {frame} must be 4..6 cells tall and wide"
            )
            continue
        frames.append(frame)
    frames.sort()

    if not 1 <= len(frames) <= 4:
        errors.append(f"expected 1..4 hollow yellow frames, got {len(frames)}")
    for index, frame in enumerate(frames):
        for other in frames[index + 1:]:
            if _boxes_overlap(frame, other):
                errors.append(f"frame boxes overlap or nest: {frame} and {other}")

    markers: list[tuple[int, int]] = []
    marker_colors: list[int] = []
    for frame in frames:
        r0, c0, r1, c1 = frame
        local = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 4)
        ]
        if len(local) != 1:
            errors.append(
                f"frame {frame} must contain exactly one nonzero non-yellow marker; "
                f"got {len(local)}"
            )
        else:
            markers.append(local[0])
            marker_colors.append(grid[local[0][0]][local[0][1]])

    exterior_cells = tuple(
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 4)
        and all(not _in_box(frame, r, c) for frame in frames)
    )
    info = {
        "grid_h": h,
        "grid_w": w,
        "frames": tuple(frames),
        "markers": tuple(markers),
        "marker_colors": tuple(marker_colors),
        "exterior_cells": exterior_cells,
        "n_exterior_distractors": len(exterior_cells),
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the complete authority grammar, including canonical inputs."""
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def generation_check(grid) -> list[str]:
    """Validate the stricter ordinary-generation envelope."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    if not 10 <= info["grid_h"] <= 18:
        errors.append(f"generated grid_h outside 10..18: {info['grid_h']}")
    if not 10 <= info["grid_w"] <= 18:
        errors.append(f"generated grid_w outside 10..18: {info['grid_w']}")
    if not 1 <= len(info["frames"]) <= 4:
        errors.append(f"generated n_frames outside 1..4: {len(info['frames'])}")
    if not 1 <= info["n_exterior_distractors"] <= 4:
        errors.append(
            "generated n_exterior_distractors outside 1..4: "
            f"{info['n_exterior_distractors']}"
        )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "n_frames": len(info["frames"]),
        "n_exterior_distractors": info["n_exterior_distractors"],
    }


def _fill_interior(output: Grid, frame: Frame, color: int) -> None:
    r0, c0, r1, c1 = frame
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if output[r][c] == 0:
                output[r][c] = color


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the pinned per-frame Racket authority."""
    output = [list(row) for row in grid]
    info, errors = _analyse(grid)
    if errors:
        return output
    for frame, color in zip(info["frames"], info["marker_colors"]):
        _fill_interior(output, frame, color)
    return output


def _rival_erase_exterior(grid: Grid) -> Grid:
    output = rule_mirror(grid)
    info, errors = _analyse(grid)
    if errors:
        return output
    for r, c, _color in info["exterior_cells"]:
        output[r][c] = 0
    return output


def _rival_single_marker_color(grid: Grid) -> Grid:
    output = [list(row) for row in grid]
    info, errors = _analyse(grid)
    if errors or not info["marker_colors"]:
        return output
    color = info["marker_colors"][0]
    for frame in info["frames"]:
        _fill_interior(output, frame, color)
    return output


def _rival_leave_interiors_blank(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _rival_fixed_blue_fill(grid: Grid) -> Grid:
    output = [list(row) for row in grid]
    info, errors = _analyse(grid)
    if errors:
        return output
    for frame in info["frames"]:
        _fill_interior(output, frame, 2)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "erase_exterior": _rival_erase_exterior,
    "single_marker_color": _rival_single_marker_color,
    "leave_interiors_blank": _rival_leave_interiors_blank,
    "fixed_blue_fill": _rival_fixed_blue_fill,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# None of the named rivals fits every canonical pair. They are lesson-level
# competitors, not canonical-equivalent shortcuts.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {}


def _valid_info(grid: Grid) -> dict[str, Any] | None:
    info, errors = _analyse(grid)
    return None if errors else info


def _witness_preserve_exterior(grid: Grid) -> bool:
    info = _valid_info(grid)
    return bool(info and info["exterior_cells"])


def _witness_multiple_marker_colors(grid: Grid) -> bool:
    info = _valid_info(grid)
    return bool(info and len(set(info["marker_colors"])) > 1)


def _witness_fill_entire_interior(grid: Grid) -> bool:
    info = _valid_info(grid)
    if not info:
        return False
    return any(
        any(
            grid[r][c] == 0
            for r in range(frame[0] + 1, frame[2])
            for c in range(frame[1] + 1, frame[3])
        )
        for frame in info["frames"]
    )


def _witness_marker_not_blue(grid: Grid) -> bool:
    info = _valid_info(grid)
    return bool(info and any(color != 2 for color in info["marker_colors"]))


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "preserve_exterior": _witness_preserve_exterior,
    "multiple_marker_colors": _witness_multiple_marker_colors,
    "fill_entire_interior": _witness_fill_entire_interior,
    "marker_not_blue": _witness_marker_not_blue,
}
WITNESS_RIVALS = {
    "preserve_exterior": ["erase_exterior"],
    "multiple_marker_colors": ["single_marker_color"],
    "fill_entire_interior": ["leave_interiors_blank"],
    "marker_not_blue": ["fixed_blue_fill"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-row lesson to refute each declared rival."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    errors: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output")
            continue
        structural = self_check(pair["input"])
        if structural:
            errors.append(f"pair {index} is not authority-valid: {structural}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} output does not match the authority")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"demonstrations do not refute rival {name!r}")
    return errors
