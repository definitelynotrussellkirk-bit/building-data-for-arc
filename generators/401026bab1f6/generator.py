"""Generator for arc_additional_puzzles_21_set3:M17.

Inside every complete color-1 rectangular frame, reflect each color-4 cell
vertically across that frame's own horizontal mid-line.  Paint color 7 at the
mirror only when that cell is empty; preserve the frame and all original 4s.

The four-slot schedule is deliberate: every four consecutive examples include
a top-only source pattern, a bottom-only pattern, a mixed pattern, and a
blocked mirror pair.  Frame count is scheduled 1/2/3/2, so every lesson also
contains multi-frame evidence that separates the object-local axis from the
grid-wide axis and from a first-frame-only shortcut.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "401026bab1f6"
TASK_ID = GENERATOR_ID
RULE_HASH = "5539aa3ad4f4"
VERSION = "4.0.0"

SUMMARY = (
    "A 0-background grid contains one to three separate complete blue(1) "
    "rectangular frames.  Within each frame, yellow(4) cells may occur above "
    "or below the frame-local horizontal mid-line.  Reflect every yellow cell "
    "through that frame's own mid-line and add orange(7) only when the mirror "
    "cell is empty.  Preserve blue frames and original yellow cells."
)

INVARIANTS = [
    "the input palette is exactly a subset of {0,1,4}, with background 0",
    "one to three separate color-1 components are complete rectangular outlines",
    "every color-4 cell lies strictly inside exactly one frame",
    "every frame has at least one color-4 cell whose mirror is empty, so the rule fires",
    "frame-local reflection, not the full-grid axis, determines every mirror row",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "canonical/expanded schedule", "valid": "10..24"},
    "grid_w": {"type": "int", "default": "canonical/expanded schedule", "valid": "10..26"},
    "n_frames": {"type": "int", "default": "1/2/3/2 schedule", "valid": "1..3"},
    "pattern_mode": {
        "type": "str",
        "default": "four-slot teaching schedule",
        "valid": "top_only|bottom_only|mixed|blocked",
    },
}

_SCHEDULE = (
    ("top_only", 1),
    ("bottom_only", 2),
    ("mixed", 3),
    ("blocked", 2),
)
SCHEDULE_PROFILES = (
    "top_only_single",
    "bottom_only_double",
    "mixed_triple",
    "blocked_double",
)
_CANONICAL_SHAPES = ((10, 10), (11, 12), (12, 11), (12, 12))
_EXPANDED_SHAPES = {
    "easy": ((13, 14), (14, 13), (14, 15), (15, 14)),
    "medium": ((16, 18), (17, 17), (18, 16), (18, 20)),
    "hard": ((20, 22), (22, 20), (23, 24), (24, 26)),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    mode, count = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    names = {1: "single", 2: "double", 3: "triple"}
    return f"{mode}_{names[count]}"


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        comp = {start}
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    comp.add((nr, nc))
                    queue.append((nr, nc))
        components.append(comp)
    return components


def _outline_cells(r0: int, c0: int, r1: int, c1: int) -> set[tuple[int, int]]:
    cells = {(r0, c) for c in range(c0, c1 + 1)}
    cells.update((r1, c) for c in range(c0, c1 + 1))
    cells.update((r, c0) for r in range(r0, r1 + 1))
    cells.update((r, c1) for r in range(r0, r1 + 1))
    return cells


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if any(not isinstance(value, int) or isinstance(value, bool) for row in grid for value in row):
        return {"errors": ["grid cells must be integers"]}

    h, w = len(grid), width
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    palette = {value for row in grid for value in row}
    illegal = sorted(palette - {0, 1, 4})
    if illegal:
        errors.append(f"input contains colors outside {{0,1,4}}: {illegal}")

    frames: list[dict[str, Any]] = []
    for comp in _components(grid, 1):
        rows = [r for r, _ in comp]
        cols = [c for _, c in comp]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        expected = _outline_cells(r0, c0, r1, c1)
        if fh < 3 or fw < 3 or comp != expected:
            errors.append(
                f"color-1 component at {(r0, c0, r1, c1)} is not a complete rectangular frame"
            )
            continue
        frames.append({"bbox": (r0, c0, r1, c1), "cells": comp, "marks": set()})

    if not 1 <= len(frames) <= 3:
        errors.append(f"expected 1..3 complete frames, found {len(frames)}")

    marks = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4}
    for mark in sorted(marks):
        owners = []
        r, c = mark
        for index, frame in enumerate(frames):
            r0, c0, r1, c1 = frame["bbox"]
            if r0 < r < r1 and c0 < c < c1:
                owners.append(index)
        if len(owners) != 1:
            errors.append(f"color-4 cell {mark} lies inside {len(owners)} frames, expected exactly one")
        else:
            frames[owners[0]]["marks"].add(mark)

    top_unpaired = bottom_unpaired = paired_pairs = centerline = 0
    per_frame: list[dict[str, Any]] = []
    for frame in frames:
        r0, c0, r1, c1 = frame["bbox"]
        frame_marks = frame["marks"]
        if not frame_marks:
            errors.append(f"frame {(r0, c0, r1, c1)} has no interior color-4 cells")
        ft = fb = fp = fc = 0
        for r, c in sorted(frame_marks):
            mr = r0 + r1 - r
            if mr == r:
                fc += 1
            elif (mr, c) in frame_marks:
                if r < mr:
                    fp += 1
            elif r < mr:
                ft += 1
            else:
                fb += 1
        if ft + fb == 0:
            errors.append(f"frame {(r0, c0, r1, c1)} has no empty-mirror source cell")
        top_unpaired += ft
        bottom_unpaired += fb
        paired_pairs += fp
        centerline += fc
        per_frame.append(
            {
                "bbox": frame["bbox"],
                "marks": set(frame_marks),
                "top_unpaired": ft,
                "bottom_unpaired": fb,
                "paired_pairs": fp,
                "centerline": fc,
            }
        )

    pattern_mode = None
    if paired_pairs > 0 and top_unpaired + bottom_unpaired > 0:
        pattern_mode = "blocked"
    elif paired_pairs == 0 and top_unpaired > 0 and bottom_unpaired > 0:
        pattern_mode = "mixed"
    elif paired_pairs == 0 and top_unpaired > 0 and bottom_unpaired == 0:
        pattern_mode = "top_only"
    elif paired_pairs == 0 and bottom_unpaired > 0 and top_unpaired == 0:
        pattern_mode = "bottom_only"
    else:
        errors.append("interior mark pattern is not one of the declared teaching modes")

    return {
        "errors": list(dict.fromkeys(errors)),
        "grid": [list(row) for row in grid],
        "grid_h": h,
        "grid_w": w,
        "palette": palette,
        "frames": sorted(per_frame, key=lambda frame: frame["bbox"]),
        "n_frames": len(frames),
        "pattern_mode": pattern_mode,
        "top_unpaired": top_unpaired,
        "bottom_unpaired": bottom_unpaired,
        "paired_pairs": paired_pairs,
        "centerline": centerline,
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if not errors:
        for axis in AXES:
            if axis in requested and requested[axis] is not None:
                observed = analysis[axis]
                if observed != requested[axis]:
                    errors.append(f"{axis} requested {requested[axis]!r}, observed {observed!r}")
    return list(dict.fromkeys(errors))


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {axis: analysis[axis] for axis in AXES}


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-linked manifold: well-formed framed local-reflection scenes."""
    return self_check(grid)


def _quadrants(h: int, w: int) -> list[tuple[int, int, int, int]]:
    top_h = (h - 1) // 2
    bottom_h = h - 1 - top_h
    left_w = (w - 1) // 2
    right_w = w - 1 - left_w
    return [
        (0, 0, top_h, left_w),
        (0, left_w + 1, top_h, right_w),
        (top_h + 1, 0, bottom_h, left_w),
        (top_h + 1, left_w + 1, bottom_h, right_w),
    ]


def _frame_boxes(h: int, w: int, count: int, rng) -> list[tuple[int, int, int, int]]:
    if count == 1:
        min_h = 6 if h >= 8 else 4
        min_w = 6 if w >= 8 else 4
        fh = rng.randint(min_h, min(9, h - 1))
        fw = rng.randint(min_w, min(9, w - 1))
        candidates = [
            (top, left)
            for top in range(h - fh + 1)
            for left in range(w - fw + 1)
            if (2 * top + fh - 1 != h - 1) or (2 * left + fw - 1 != w - 1)
        ]
        if not candidates:
            candidates = [(top, left) for top in range(h - fh + 1) for left in range(w - fw + 1)]
        top, left = rng.choice(candidates)
        return [(top, left, top + fh - 1, left + fw - 1)]

    regions = _quadrants(h, w)
    if any(rh < 4 or rw < 4 for _, _, rh, rw in regions):
        raise ValueError(f"grid {h}x{w} cannot fit {count} separated frames")
    if count == 2:
        choices = ((0, 3), (1, 2), (0, 1), (2, 3), (0, 2), (1, 3))
        selected = rng.choice(choices)
    else:
        omitted = rng.randrange(4)
        selected = tuple(index for index in range(4) if index != omitted)

    boxes = []
    for index in selected:
        base_r, base_c, rh, rw = regions[index]
        fh = rng.randint(4, min(9, rh))
        fw = rng.randint(4, min(9, rw))
        top = base_r + rng.randint(0, rh - fh)
        left = base_c + rng.randint(0, rw - fw)
        boxes.append((top, left, top + fh - 1, left + fw - 1))
    return sorted(boxes)


def _mirror_pairs(box: tuple[int, int, int, int]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    r0, c0, r1, c1 = box
    pairs = []
    for r in range(r0 + 1, r1):
        mr = r0 + r1 - r
        if r >= mr:
            continue
        for c in range(c0 + 1, c1):
            pairs.append(((r, c), (mr, c)))
    return pairs


def _paint_pattern(grid: list[list[int]], box, mode: str, rng) -> None:
    pairs = _mirror_pairs(box)
    rng.shuffle(pairs)
    if len(pairs) < 2:
        raise ValueError(f"frame {box} has too few mirror pairs for mode {mode}")

    max_unpaired = min(len(pairs), rng.randint(2, min(5, len(pairs))))
    if mode == "top_only":
        for top, _ in pairs[:max_unpaired]:
            grid[top[0]][top[1]] = 4
    elif mode == "bottom_only":
        for _, bottom in pairs[:max_unpaired]:
            grid[bottom[0]][bottom[1]] = 4
    elif mode == "mixed":
        top, _ = pairs[0]
        _, bottom = pairs[1]
        grid[top[0]][top[1]] = 4
        grid[bottom[0]][bottom[1]] = 4
        for pair in pairs[2:max_unpaired]:
            cell = pair[rng.randrange(2)]
            grid[cell[0]][cell[1]] = 4
    elif mode == "blocked":
        top, bottom = pairs[0]
        grid[top[0]][top[1]] = 4
        grid[bottom[0]][bottom[1]] = 4
        cell = pairs[1][rng.randrange(2)]
        grid[cell[0]][cell[1]] = 4
        for pair in pairs[2:max_unpaired]:
            cell = pair[rng.randrange(2)]
            grid[cell[0]][cell[1]] = 4
    else:
        raise ValueError(f"unknown pattern mode: {mode!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    band = difficulty or "medium"
    slot = int(sample_index) % len(_SCHEDULE)
    scheduled_mode, scheduled_frames = _SCHEDULE[slot]
    if (int(sample_index) // len(_SCHEDULE)) % 2 == 0:
        scheduled_h, scheduled_w = _CANONICAL_SHAPES[slot]
    else:
        scheduled_h, scheduled_w = _EXPANDED_SHAPES[band][slot]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, "grid_h", scheduled_h, 10, 24)
    w = _draw_scheduled_int(ctx, "grid_w", scheduled_w, 10, 26)
    n_frames = _draw_scheduled_int(ctx, "n_frames", scheduled_frames, 1, 3)
    pattern_mode = _draw_scheduled_choice(
        ctx,
        "pattern_mode",
        scheduled_mode,
        ("top_only", "bottom_only", "mixed", "blocked"),
    )
    rng = ctx.draw_rng(f"construction:{band}")

    grid = full_grid(h, w, 0)
    boxes = _frame_boxes(h, w, n_frames, rng)
    for box in boxes:
        r0, c0, r1, c1 = box
        draw_rect_outline(grid, r0, c0, r1 - r0 + 1, c1 - c0 + 1, 1)
        _paint_pattern(grid, box, pattern_mode, rng)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": ctx.recorded_draws()})
    if errors:
        raise AssertionError("generator emitted invalid grid: " + "; ".join(errors))
    return grid


def rule_mirror(grid: Any) -> list[list[int]]:
    """Test-only Python mirror; the canonical Racket program remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    source = analysis["grid"]
    out = [row[:] for row in source]
    for frame in analysis["frames"]:
        r0, c0, r1, c1 = frame["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if source[r][c] != 4:
                    continue
                mr = r0 + r1 - r
                if out[mr][c] == 0:
                    out[mr][c] = 7
    return out


def _apply_subset(grid: Any, frame_indices: set[int] | None, direction: str | None, overwrite: bool) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    source = analysis["grid"]
    out = [row[:] for row in source]
    frames = analysis["frames"]
    for index, frame in enumerate(frames):
        if frame_indices is not None and index not in frame_indices:
            continue
        r0, c0, r1, c1 = frame["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if source[r][c] != 4:
                    continue
                mr = r0 + r1 - r
                if direction == "top" and r >= mr:
                    continue
                if direction == "bottom" and r <= mr:
                    continue
                if overwrite or out[mr][c] == 0:
                    out[mr][c] = 7
    return out


def _rival_top_down_only(grid: Any) -> list[list[int]]:
    return _apply_subset(grid, None, "top", False)


def _rival_bottom_up_only(grid: Any) -> list[list[int]]:
    return _apply_subset(grid, None, "bottom", False)


def _rival_overwrite_occupied(grid: Any) -> list[list[int]]:
    return _apply_subset(grid, None, None, True)


def _rival_first_frame_only(grid: Any) -> list[list[int]]:
    return _apply_subset(grid, {0}, None, False)


def _rival_grid_axis(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    source = analysis["grid"]
    out = [row[:] for row in source]
    h = len(source)
    for r, row in enumerate(source):
        for c, value in enumerate(row):
            if value != 4:
                continue
            mr = h - 1 - r
            if out[mr][c] == 0:
                out[mr][c] = 7
    return out


SEMANTIC_RIVALS = {
    "top_down_only": _rival_top_down_only,
    "bottom_up_only": _rival_bottom_up_only,
    "overwrite_occupied_mirror": _rival_overwrite_occupied,
    "grid_axis_reflection": _rival_grid_axis,
    "first_frame_only": _rival_first_frame_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "grid_axis_reflection": _rival_grid_axis,
    "first_frame_only": _rival_first_frame_only,
}


def _witness(grid: Any, predicate: Callable[[dict[str, Any]], bool], rival: Callable[[Any], Any]) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(predicate(analysis)) and rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "top_source_refutes_bottom_only": lambda grid: _witness(
        grid, lambda a: a["top_unpaired"] > 0, _rival_bottom_up_only
    ),
    "bottom_source_refutes_top_only": lambda grid: _witness(
        grid, lambda a: a["bottom_unpaired"] > 0, _rival_top_down_only
    ),
    "occupied_mirror_refutes_overwrite": lambda grid: _witness(
        grid, lambda a: a["paired_pairs"] > 0, _rival_overwrite_occupied
    ),
    "local_axis_refutes_grid_axis": lambda grid: _witness(
        grid,
        lambda a: any(
            frame["bbox"][0] + frame["bbox"][2] != a["grid_h"] - 1
            for frame in a["frames"]
        ),
        _rival_grid_axis,
    ),
    "multiple_frames_refute_first_only": lambda grid: _witness(
        grid, lambda a: a["n_frames"] > 1, _rival_first_frame_only
    ),
}
WITNESS_RIVALS = {
    "top_source_refutes_bottom_only": ["bottom_up_only"],
    "bottom_source_refutes_top_only": ["top_down_only"],
    "occupied_mirror_refutes_overwrite": ["overwrite_occupied_mirror"],
    "local_axis_refutes_grid_axis": ["grid_axis_reflection"],
    "multiple_frames_refute_first_only": ["first_frame_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [(f"demo {index}", pair) for index, pair in enumerate(demos)] + [("query", query)]
    for label, pair in pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} input is unlawful: {'; '.join(errors)}")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{label} output disagrees with frame-local reflection")
    if reasons:
        return reasons

    truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != truth:
                reasons.append(f"named competitor {name!r} survives demos but changes the query")
    return reasons


def mutation_fixtures():
    base = generate(73, 2, difficulty="medium")
    analysis = _analyze(base)
    frame = analysis["frames"][0]
    r0, c0, r1, c1 = frame["bbox"]

    broken_frame = [row[:] for row in base]
    broken_frame[r0][c0 + 1] = 0

    exterior_mark = [row[:] for row in base]
    exterior = next(
        (r, c)
        for r in range(len(base))
        for c in range(len(base[0]))
        if exterior_mark[r][c] == 0
        and not any(fr["bbox"][0] < r < fr["bbox"][2] and fr["bbox"][1] < c < fr["bbox"][3] for fr in analysis["frames"])
    )
    exterior_mark[exterior[0]][exterior[1]] = 4

    palette_intruder = [row[:] for row in base]
    bg = next((r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value == 0)
    palette_intruder[bg[0]][bg[1]] = 2

    all_marks_paired = generate(79, 0, difficulty="medium", pattern_mode="top_only")
    paired_analysis = _analyze(all_marks_paired)
    for fr in paired_analysis["frames"]:
        r0, _, r1, _ = fr["bbox"]
        for r, c in list(fr["marks"]):
            mr = r0 + r1 - r
            all_marks_paired[mr][c] = 4

    return [
        ("broken_frame_outline", broken_frame),
        ("yellow_mark_outside_frames", exterior_mark),
        ("unseen_replacement_color", palette_intruder),
        ("all_mirrors_occupied_no_effect", all_marks_paired),
    ]
