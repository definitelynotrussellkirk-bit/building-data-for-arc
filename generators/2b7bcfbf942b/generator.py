"""Source-bound generator for checkerboard bounding-box completion.

The selected executable rule treats every same-color 4-connected object as a
bounding-box cue: it paints that object's full bounding-box border and fills
its interior with a local checkerboard that starts in the object's color at
the interior top-left cell.  Canonical examples happen to contain only closed
frames, so this generator also emits open frames and crosses to rule out the
plausible but narrower "complete frames only" interpretation.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2b7bcfbf942b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "de72b7a33ad3"

SUMMARY = (
    "A 0-background grid contains one to three distinct-color, same-style "
    "4-connected objects. Objects vary among complete frames, gapped/open "
    "frames, and crosses, with independently variable canvas size, bounding "
    "boxes, positions, colors, and count. The selected rule replaces each "
    "object by its full bounding-box border plus a local same-color/zero "
    "checkerboard interior beginning with color at the interior top-left."
)

INVARIANTS = [
    "background is color 0 and every object has its own nonzero color",
    "each object is 4-connected, spans a bbox at least 3x3, and bboxes do not overlap",
    "all objects in one grid use the same observable style: frame, open, or cross",
    "three consecutive default sample indices cover all three object styles",
]

STYLES = ("frame", "open", "cross")
CANONICAL_PROFILES = (
    (8, 10, 1),   # palette size 2
    (9, 12, 2),   # palette size 3
    (10, 10, 1),
    (8, 13, 2),
    (9, 11, 1),
)
CANONICAL_BBOXES = frozenset({(5, 5), (6, 4), (6, 6), (6, 7)})
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile cycle plus broad draws", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "canonical-profile cycle plus broad draws", "valid": "9..18"},
    "n_objects": {"type": "int", "default": "profile-linked 1..3", "valid": "1..3"},
    "object_style": {"type": "str", "default": "sample_index cycle", "valid": "frame|open|cross"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (("grid_h", 8, 16), ("grid_w", 9, 18), ("n_objects", 1, 3)):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:  # bool is intentionally rejected
            raise ValueError(f"{name} must be an int in [{lo}, {hi}], got {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

    if "object_style" in overrides:
        value = overrides["object_style"]
        if type(value) is not str or value not in STYLES:
            raise ValueError(f"object_style must be one of {STYLES}, got {value!r}")


def _draw_preferred_choice(ctx, label: str, options: Iterable, preferred=None):
    """Draw from the full exact-axis domain while enforcing a curriculum default.

    The option set always contains the complete declared domain, so every exact
    override remains legal in every difficulty band.  When a curriculum value
    is requested, the option order is deterministically permuted so the keyed
    RNG selects that value; no global RNG or hidden override is used.
    """
    options = list(options)
    if label in ctx.overrides:
        return ctx.draw_choice(label, options)
    if preferred is None:
        return ctx.draw_choice(label, options)
    if preferred not in options:
        raise ValueError(f"preferred {label}={preferred!r} outside {options!r}")
    chosen_index = ctx.draw_rng(label).randrange(len(options))
    preferred_index = options.index(preferred)
    options[chosen_index], options[preferred_index] = options[preferred_index], options[chosen_index]
    return ctx.draw_choice(label, options)


def _partition(length: int, count: int) -> list[tuple[int, int]]:
    """Partition [0,length) into count contiguous intervals, each at least 3."""
    if length < 3 * count:
        raise ValueError(f"cannot partition length {length} into {count} 3-cell slots")
    base, extra = divmod(length, count)
    intervals = []
    start = 0
    for i in range(count):
        size = base + (1 if i < extra else 0)
        intervals.append((start, start + size - 1))
        start += size
    return intervals


def _shape_cells(box: tuple[int, int, int, int], style: str, open_side: str = "top") -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    perimeter = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if style == "frame":
        return perimeter
    if style == "open":
        gaps = {
            "top": {(r1, c) for c in range(c1 + 1, c2)},
            "bottom": {(r2, c) for c in range(c1 + 1, c2)},
            "left": {(r, c1) for r in range(r1 + 1, r2)},
            "right": {(r, c2) for r in range(r1 + 1, r2)},
        }
        return perimeter - gaps[open_side]
    if style == "cross":
        mr, mc = (r1 + r2) // 2, (c1 + c2) // 2
        return {(mr, c) for c in range(c1, c2 + 1)} | {(r, mc) for r in range(r1, r2 + 1)}
    raise ValueError(f"unknown style {style!r}")


def _choose_box(ctx, slot: tuple[int, int, int, int], index: int, difficulty) -> tuple[int, int, int, int]:
    sr1, sc1, sr2, sc2 = slot
    max_h, max_w = sr2 - sr1 + 1, sc2 - sc1 + 1
    rng = ctx.draw_rng(f"object_{index}_box")

    if difficulty == "easy":
        min_h = max(3, max_h - 2)
        min_w = max(3, max_w - 2)
    elif difficulty == "hard":
        min_h = 3
        min_w = 3
    else:
        min_h = max(3, max_h // 2)
        min_w = max(3, max_w // 2)

    bh = rng.randint(min_h, max_h)
    bw = rng.randint(min_w, max_w)
    r1 = rng.randint(sr1, sr2 - bh + 1)
    c1 = rng.randint(sc1, sc2 - bw + 1)
    return r1, c1, r1 + bh - 1, c1 + bw - 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    cycle = sample_index % 6
    preferred = CANONICAL_PROFILES[cycle] if cycle < len(CANONICAL_PROFILES) else None
    preferred_h = preferred[0] if preferred else None
    preferred_w = preferred[1] if preferred else None
    preferred_n = preferred[2] if preferred else 3

    h = _draw_preferred_choice(ctx, "grid_h", range(8, 17), preferred_h)
    w = _draw_preferred_choice(ctx, "grid_w", range(9, 19), preferred_w)
    n_objects = _draw_preferred_choice(ctx, "n_objects", range(1, 4), preferred_n)
    style = _draw_preferred_choice(ctx, "object_style", STYLES, STYLES[sample_index % 3])
    colors = ctx.draw_distinct_colors("colors", n=n_objects, exclude=[0])

    horizontal_ok = w >= 3 * n_objects
    vertical_ok = h >= 3 * n_objects
    if horizontal_ok and vertical_ok:
        layout = ctx.draw_choice("layout_axis", ("horizontal", "vertical"))
    elif horizontal_ok:
        layout = "horizontal"
    elif vertical_ok:
        layout = "vertical"
    else:  # declared domains make this unreachable, but keep failure explicit
        raise ValueError(f"{h}x{w} cannot fit {n_objects} objects")

    if layout == "horizontal":
        slots = [(0, c1, h - 1, c2) for c1, c2 in _partition(w, n_objects)]
    else:
        slots = [(r1, 0, r2, w - 1) for r1, r2 in _partition(h, n_objects)]

    grid = full_grid(h, w, 0)
    for index, (slot, color) in enumerate(zip(slots, colors)):
        box = _choose_box(ctx, slot, index, difficulty)
        side = ctx.draw_choice(f"open_side_{index}", ("top", "bottom", "left", "right"))
        for r, c in _shape_cells(box, style, side):
            grid[r][c] = color
    return grid


def _components(grid) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, frozenset(cells)))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _classify(cells: Iterable[tuple[int, int]]) -> str | None:
    cells = set(cells)
    box = _bbox(cells)
    r1, c1, r2, c2 = box
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return None
    for style in STYLES:
        if style == "open":
            for side in ("top", "bottom", "left", "right"):
                if cells == _shape_cells(box, style, side):
                    return style
        elif cells == _shape_cells(box, style):
            return style
    return None


def _boxes_overlap(a, b) -> bool:
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return not (ar2 < br1 or br2 < ar1 or ac2 < bc1 or bc2 < ac1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    h, w = len(grid), width
    if not (8 <= h <= 16 and 9 <= w <= 18):
        return [f"grid shape {h}x{w} outside 8..16 by 9..18"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an int color 0..9, got {value!r}"]

    comps = _components(grid)
    if not 1 <= len(comps) <= 3:
        return [f"expected 1..3 nonzero objects, got {len(comps)}"]
    colors = [color for color, _ in comps]
    if len(set(colors)) != len(colors):
        return ["each color must form exactly one 4-connected object"]

    boxes = []
    styles = []
    for index, (_, cells) in enumerate(comps):
        style = _classify(cells)
        if style is None:
            return [f"object {index} is not a frame, open frame, or cross spanning a >=3x3 bbox"]
        boxes.append(_bbox(cells))
        styles.append(style)
    if len(set(styles)) != 1:
        return [f"all objects must share one style, got {sorted(set(styles))}"]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if _boxes_overlap(a, b):
                return [f"object bounding boxes overlap: {a} and {b}"]
    return []


def observe_overrides(grid) -> dict:
    issues = self_check(grid)
    if issues:
        raise ValueError("cannot observe invalid grid: " + "; ".join(issues))
    comps = _components(grid)
    style = _classify(comps[0][1])
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(comps),
        "object_style": style,
    }


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _bbox_rule(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for color, cells in _components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                border = r in (r1, r2) or c in (c1, c2)
                local_even = ((r - r1 - 1) + (c - c1 - 1)) % 2 == 0
                out[r][c] = color if border or local_even else 0
    return out


def _complete_frames_only(grid):
    out = deepcopy(grid)
    for color, cells in _components(grid):
        box = _bbox(cells)
        if set(cells) != _shape_cells(box, "frame"):
            continue
        r1, c1, r2, c2 = box
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                out[r][c] = color if ((r - r1 - 1) + (c - c1 - 1)) % 2 == 0 else 0
    return out


def _canonical_bbox_sizes_only(grid):
    out = deepcopy(grid)
    authority = _bbox_rule(grid)
    for _, cells in _components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        if (r2 - r1 + 1, c2 - c1 + 1) not in CANONICAL_BBOXES:
            continue
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] = authority[r][c]
    return out


def _has_non_frame(grid) -> bool:
    return any(_classify(cells) != "frame" for _, cells in _components(grid))


def _has_novel_bbox_size(grid) -> bool:
    return any(
        (r2 - r1 + 1, c2 - c1 + 1) not in CANONICAL_BBOXES
        for _, cells in _components(grid)
        for r1, c1, r2, c2 in [_bbox(cells)]
    )


SEMANTIC_RIVALS = {
    "complete_frames_only": _complete_frames_only,
    "canonical_bbox_sizes_only": _canonical_bbox_sizes_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "non_frame_object": _has_non_frame,
    "novel_bbox_size": _has_novel_bbox_size,
}
WITNESS_RIVALS = {
    "non_frame_object": ["complete_frames_only"],
    "novel_bbox_size": ["canonical_bbox_sizes_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"{name} fits every demonstration")
    return reasons
