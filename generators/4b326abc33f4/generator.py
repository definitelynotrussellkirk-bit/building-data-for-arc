"""Generator for ARC task 4b326abc33f4 — external-seed frame fill.

The input contains one or two hollow gray (5) rectangular frames.  Every frame
has exactly one colored seed immediately outside the midpoint of its left or
right side.  The canonical rule preserves the input and fills each frame's
interior with its own seed color.

The source generator deliberately exposes only controls it actually honors.
The separate task-local parametric family extends the same grammar to larger
multi-frame scenes; this production source remains close to the canonical task.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "4b326abc33f4"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b18855f77d40"

SUMMARY = (
    "Find each hollow gray frame, read its single colored side seed at the "
    "vertical midpoint, and fill that frame's interior with the seed color."
)

INVARIANTS = [
    "background is color 0 and all cells are exact ARC integers 0..9",
    "there are one or two disconnected rectangular color-5 frame borders",
    "each frame has exactly one nonzero non-5 seed immediately left or right of its midpoint",
    "each frame interior is empty in the generated input",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng", "valid": "12..20"},
    "n_frames": {"type": "int", "default": "difficulty-aware rng", "valid": "1..2"},
}


_PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_int(ctx, name: str, absolute: tuple[int, int], default: tuple[int, int], overrides: dict) -> int:
    bounds = absolute if overrides.get(name) is not None else default
    return ctx.draw_int_strict(name, *bounds)


def _seeded_frame(grid, bbox, side: str, color: int) -> None:
    r0, c0, r1, c1 = bbox
    draw_frame(grid, r0, c0, r1, c1, 5)
    mid = (r0 + r1) // 2
    if side == "left":
        grid[mid][c0 - 1] = color
    else:
        grid[mid][c1 + 1] = color


def _single_layout(h: int, w: int, rng, sample_index: int):
    fh = rng.randint(4, min(6, h))
    fw = rng.randint(4, min(6, w - 1))
    side = "left" if sample_index % 2 == 0 else "right"
    boundary = (sample_index // 2) % 3 == 0
    r0 = rng.randint(0, h - fh)
    if side == "left":
        if boundary:
            c0 = w - fw  # touch the opposite boundary; seed stays on the left
        else:
            c0 = rng.randint(1, w - fw)
    else:
        if boundary:
            c0 = 0
        else:
            c0 = rng.randint(0, w - fw - 1)
    return [(r0, c0, r0 + fh - 1, c0 + fw - 1, side)]


def _horizontal_layout(h: int, w: int, rng):
    split = w // 2
    slots = ((0, split - 1, "left"), (split, w - 1, "right"))
    result = []
    for start, end, side in slots:
        slot_w = end - start + 1
        fw = rng.randint(4, min(6, slot_w - 2))
        fh = rng.randint(4, min(6, h))
        r0 = rng.randint(0, h - fh)
        # Keep an inner blank column between the two frame components while
        # putting each seed on the outer side of its slot.
        if side == "left":
            c0 = rng.randint(start + 1, end - fw)
        else:
            c0 = rng.randint(start + 1, end - fw)
        result.append((r0, c0, r0 + fh - 1, c0 + fw - 1, side))
    return result


def _vertical_layout(h: int, w: int, rng, sample_index: int):
    split = h // 2
    slots = ((0, split - 1), (split, h - 1))
    result = []
    for index, (start, end) in enumerate(slots):
        slot_h = end - start + 1
        fh = rng.randint(4, min(6, slot_h - 1))
        fw = rng.randint(4, min(6, w - 2))
        r0 = start if index == 0 else start + 1
        r0 = min(r0, end - fh + 1)
        side = "left" if (sample_index + index) % 2 == 0 else "right"
        c0 = rng.randint(1, w - fw - 1)
        result.append((r0, c0, r0 + fh - 1, c0 + fw - 1, side))
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = {
        "easy": ((8, 10), (12, 15), (1, 1)),
        "medium": ((9, 12), (14, 18), (1, 2)),
        "hard": ((11, 14), (16, 20), (2, 2)),
    }[band]
    h = _draw_int(ctx, "grid_h", (8, 14), defaults[0], overrides)
    w = _draw_int(ctx, "grid_w", (12, 20), defaults[1], overrides)
    n_frames = _draw_int(ctx, "n_frames", (1, 2), defaults[2], overrides)

    rng = ctx.draw_rng("layout")
    if n_frames == 1:
        layouts = _single_layout(h, w, rng, int(sample_index))
    elif h >= 10 and int(sample_index) % 2:
        layouts = _vertical_layout(h, w, rng, int(sample_index))
    else:
        layouts = _horizontal_layout(h, w, rng)

    colors = list(_PALETTE)
    ctx.draw_rng("seed_colors").shuffle(colors)
    grid = full_grid(h, w, 0)
    for spec, color in zip(layouts, colors):
        r0, c0, r1, c1, side = spec
        _seeded_frame(grid, (r0, c0, r1, c1), side, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    return grid


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integers in 0..9")
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    return len(grid), width


def analyze_frames(grid) -> list[dict]:
    """Return canonical reading-order frame/seed records from an input grid."""
    h, w = _validate_grid(grid)
    fives = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    components = []
    seen = set()
    for start in sorted(fives):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = set()
        while stack:
            r, c = stack.pop()
            component.add((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in fives and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))
        components.append(component)

    records = []
    for component in components:
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if component != border or r1 - r0 < 3 or c1 - c0 < 3:
            raise ValueError(f"color-5 component at {(r0, c0, r1, c1)} is not a hollow rectangular frame")
        if any(grid[r][c] != 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
            raise ValueError(f"frame at {(r0, c0, r1, c1)} has a nonempty interior")
        mid = (r0 + r1) // 2
        candidates = []
        if c0 > 0 and grid[mid][c0 - 1] not in (0, 5):
            candidates.append(("left", grid[mid][c0 - 1], (mid, c0 - 1)))
        if c1 + 1 < w and grid[mid][c1 + 1] not in (0, 5):
            candidates.append(("right", grid[mid][c1 + 1], (mid, c1 + 1)))
        if len(candidates) != 1:
            raise ValueError(f"frame at {(r0, c0, r1, c1)} has {len(candidates)} side seeds, expected 1")
        side, color, position = candidates[0]
        records.append(
            {
                "bbox": (r0, r1, c0, c1),
                "seed_color": color,
                "seed_side": side,
                "seed_position": position,
                "boundary_contacts": tuple(
                    name
                    for name, hit in (
                        ("top", r0 == 0),
                        ("bottom", r1 == h - 1),
                        ("left", c0 == 0),
                        ("right", c1 == w - 1),
                    )
                    if hit
                ),
            }
        )
    return sorted(records, key=lambda record: record["bbox"])


def rule_mirror(grid):
    out = deepcopy(grid)
    for frame in analyze_frames(grid):
        r0, r1, c0, c1 = frame["bbox"]
        color = frame["seed_color"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = color
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        h, w = _validate_grid(grid)
        frames = analyze_frames(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors = []
    if not (8 <= h <= 14 and 12 <= w <= 20):
        # Canonical source examples are all inside this contract.  Parametric
        # large scenes use their own checker rather than widening the base.
        errors.append(f"generated grid shape {(h, w)} is outside 8..14 by 12..20")
    if not 1 <= len(frames) <= 2:
        errors.append(f"expected 1-2 frames, got {len(frames)}")
    return errors
