"""Generator for 4b6b68e5 / source id 7ef325b21961.

Rule: preserve every closed rectangular frame, replace its interior with the
majority color of the dots *inside that frame*, and erase outside distractors.
The ordinary distribution deliberately gives different frames different local
majorities so a global-color shortcut cannot solve multi-frame examples.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7ef325b21961"
VERSION = "2.1.0"
TASK_ID = "7ef325b21961"
RULE_HASH = "450273ee54ad"
SUMMARY = (
    "A 0-background grid contains 1-3 separated closed single-color "
    "rectangular frames.  Every frame contains isolated dots of exactly two "
    "non-frame colors, with a strict frame-local majority; different frames "
    "use different majority colors.  Preserve each border, fill its complete "
    "interior with that frame's local majority color, and erase all outside "
    "distractor dots."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 0",
    "each non-singleton object is a closed single-color rectangular frame",
    "each frame contains exactly two isolated non-frame dot colors",
    "each frame has a strict local majority and multi-frame winners differ",
]

HELPFUL_TEXTURES = ("sparse", "dense")
DEGENERATE_TEXTURES = ("no_frames", "no_dots", "full_grid")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 14..24", "valid": "14..24"},
    "grid_w": {"type": "int", "default": "difficulty-aware 14..24", "valid": "14..24"},
    "frame_count": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture": {
        "type": "str",
        "default": "rng sparse|dense",
        "valid": "sparse|dense|no_frames|no_dots|full_grid",
    },
}

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["empty grid"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC limit: {len(grid)}x{width}"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) is not an exact ARC color: {value!r}"]
    return []


def _components(grid) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                pr, pc = queue.popleft()
                cells.append((pr, pc))
                for dr, dc in _NEIGHBORS:
                    nr, nc = pr + dr, pc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, tuple(cells)))
    return result


def _frame_bbox(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    if r2 - r1 + 1 < 5 or c2 - c1 + 1 < 5:
        return None
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return (r1, c1, r2, c2) if set(cells) == border else None


def _frame_records(grid):
    records = []
    non_frames = []
    for color, cells in _components(grid):
        bbox = _frame_bbox(cells)
        if bbox is None:
            non_frames.append((color, cells))
            continue
        r1, c1, r2, c2 = bbox
        counts = Counter(
            grid[r][c]
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
            if grid[r][c] != 0
        )
        records.append((bbox, color, counts))
    return sorted(records), non_frames


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the ordinary local-majority teaching distribution."""
    errors = _validate_grid(grid)
    if errors:
        return errors

    frames, non_frames = _frame_records(grid)
    if not frames:
        return ["expected at least one closed rectangular frame"]

    for color, cells in non_frames:
        if len(cells) != 1:
            return [
                f"non-frame colored component of color {color} has {len(cells)} cells; "
                "only isolated dots are allowed"
            ]

    winners = []
    for bbox, frame_color, counts in frames:
        if frame_color in counts:
            return [f"frame {bbox} reuses its border color inside"]
        if len(counts) != 2:
            return [f"frame {bbox} must contain exactly two dot colors; found {dict(counts)}"]
        ordered = counts.most_common()
        if ordered[0][1] <= ordered[1][1] or ordered[1][1] < 1:
            return [f"frame {bbox} has no strict local majority: {dict(counts)}"]
        winners.append(ordered[0][0])

    if len(winners) != len(set(winners)):
        return [f"frame-local majority colors must differ; found {winners}"]
    return []


def _draw_frame(grid, r0: int, c0: int, rh: int, rw: int, color: int) -> None:
    for r in range(r0, r0 + rh):
        grid[r][c0] = color
        grid[r][c0 + rw - 1] = color
    for c in range(c0, c0 + rw):
        grid[r0][c] = color
        grid[r0 + rh - 1][c] = color


def _slot_specs(height: int, width: int, count: int):
    """Return separated layout slots that guarantee room for 5x5 frames."""
    if count == 1:
        rows, cols = 1, 1
    elif count == 2:
        rows, cols = ((1, 2) if width >= height else (2, 1))
    else:
        rows, cols = 2, 2
    slots = []
    for index in range(count):
        sr, sc = divmod(index, cols)
        r1, r2 = sr * height // rows, (sr + 1) * height // rows
        c1, c2 = sc * width // cols, (sc + 1) * width // cols
        slots.append((r1, c1, r2, c2))
    return slots


def _difficulty_bounds(difficulty):
    if difficulty == "easy":
        return (14, 17)
    if difficulty == "hard":
        return (20, 24)
    return (16, 24)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size_lo, size_hi = _difficulty_bounds(difficulty)
    height = ctx.draw_int_strict("grid_h", size_lo, size_hi)
    width = ctx.draw_int_strict("grid_w", size_lo, size_hi)
    frame_count = ctx.draw_int_strict("frame_count", 1, 3)
    if "texture" in overrides:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
    else:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx.draw_rng("degenerate"), height, width)

    colors = ctx.draw_distinct_colors("colors", n=3 * frame_count, exclude={0})
    frame_colors = colors[:frame_count]
    majority_colors = colors[frame_count:2 * frame_count]
    minority_colors = colors[2 * frame_count:]

    grid = full_grid(height, width, 0)
    frames = []
    for index, (slot_r1, slot_c1, slot_r2, slot_c2) in enumerate(
            _slot_specs(height, width, frame_count)):
        rng = ctx.draw_rng(f"frame_{index}")
        slot_h, slot_w = slot_r2 - slot_r1, slot_c2 - slot_c1
        max_h, max_w = min(8, slot_h - 2), min(8, slot_w - 2)
        if max_h < 5 or max_w < 5:
            raise ValueError(
                f"grid {height}x{width} cannot place {frame_count} separated 5x5 frames"
            )
        rh = rng.randint(5, max_h)
        rw = rng.randint(5, max_w)
        r0 = rng.randint(slot_r1 + 1, slot_r2 - rh - 1)
        c0 = rng.randint(slot_c1 + 1, slot_c2 - rw - 1)
        _draw_frame(grid, r0, c0, rh, rw, frame_colors[index])
        frames.append((r0, c0, r0 + rh - 1, c0 + rw - 1))

        interior = [
            (r, c)
            for r in range(r0 + 1, r0 + rh - 1)
            for c in range(c0 + 1, c0 + rw - 1)
        ]
        parity = {
            0: [point for point in interior if sum(point) % 2 == 0],
            1: [point for point in interior if sum(point) % 2 == 1],
        }
        major_parity = max(parity, key=lambda value: len(parity[value]))
        major_slots = parity[major_parity]
        minor_slots = parity[1 - major_parity]
        rng.shuffle(major_slots)
        rng.shuffle(minor_slots)

        if texture == "sparse":
            n_major = rng.randint(2, min(3, len(major_slots)))
            n_minor = 1
        else:
            n_major = rng.randint(3, min(5, len(major_slots)))
            n_minor = rng.randint(1, min(2, n_major - 1, len(minor_slots)))
        for r, c in major_slots[:n_major]:
            grid[r][c] = majority_colors[index]
        for r, c in minor_slots[:n_minor]:
            grid[r][c] = minority_colors[index]

    # Optional isolated outside distractors.  They are never adjacent to any
    # nonzero cell, so no dot component can masquerade as a frame object.
    unused_colors = [color for color in range(1, 10) if color not in colors]
    if unused_colors:
        noise_rng = ctx.draw_rng("outside_noise")
        candidates = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == 0
            and not any(
                r1 - 1 <= r <= r2 + 1 and c1 - 1 <= c <= c2 + 1
                for r1, c1, r2, c2 in frames
            )
        ]
        noise_rng.shuffle(candidates)
        remaining = noise_rng.randint(0, min(6, len(candidates)))
        for r, c in candidates:
            if remaining == 0:
                break
            if any(
                0 <= r + dr < height and 0 <= c + dc < width
                and grid[r + dr][c + dc] != 0
                for dr, dc in _NEIGHBORS
            ):
                continue
            grid[r][c] = noise_rng.choice(unused_colors)
            remaining -= 1

    return grid


def _draw_from_degenerate(name, rng, height: int, width: int):
    grid = full_grid(height, width, 0)
    if name == "no_frames":
        grid[height // 2][width // 2] = 2
        return grid
    if name == "no_dots":
        _draw_frame(grid, 2, 2, min(7, height - 4), min(8, width - 4), 1)
        return grid
    if name == "full_grid":
        return full_grid(height, width, 2)
    return grid
