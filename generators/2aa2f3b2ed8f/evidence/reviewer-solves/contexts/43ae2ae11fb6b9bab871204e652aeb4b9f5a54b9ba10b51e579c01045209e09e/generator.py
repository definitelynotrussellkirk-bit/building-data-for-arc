"""Generator for the tailed-rectangle slide task.

A non-rectangular creature consists of a solid rectangular body plus a
one-cell-thick tail.  The tail points toward a differently-coloured solid
rectangle and exactly bridges the gap to it.  The rule consumes the tail and
slides the body along that direction until the body is flush with the target.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "2aa2f3b2ed8f"
TASK_ID = GENERATOR_ID
RULE_HASH = "f1cfb51e6ad7"
VERSION = "3.0.0"
SUMMARY = "Consume a straight tail and slide its rectangular body until flush with the other rectangle."

INVARIANTS = [
    "the background is zero",
    "there are exactly two differently-coloured non-background objects",
    "one object is a solid rectangle",
    "the other object is a solid rectangular body plus a straight one-cell-thick tail",
    "the tail exactly bridges the positive gap from body to target",
    "the body is the unique largest filled rectangle inside the creature",
]

ORIENTATIONS = ("right", "left", "down", "up")
# Every advertised body shape remains the unique largest internal rectangle for
# every advertised tail length and orientation.  Canonical 3x3 inputs are still
# accepted by self_check, but 3x3 is not crossed with tail_length=6 in generation
# because that creates a largest-rectangle tie in the reference program.
BODY_SHAPES = ("3x4", "4x3", "4x4", "3x5", "5x3", "4x5", "5x4", "6x8")
TARGET_SHAPES = ("2x5", "5x2", "3x7", "7x3", "5x5", "7x7", "8x5", "5x8")
TAIL_LENGTHS = tuple(range(1, 7))

AXES = {
    "orientation": {
        "type": "str",
        "default": "scheduled canonical/broad draw",
        "valid": "|".join(ORIENTATIONS),
    },
    "body_shape": {
        "type": "str",
        "default": "scheduled canonical/broad draw",
        "valid": "|".join(BODY_SHAPES),
    },
    "target_shape": {
        "type": "str",
        "default": "scheduled canonical/broad draw",
        "valid": "|".join(TARGET_SHAPES),
    },
    "tail_length": {
        "type": "int",
        "default": "scheduled canonical/broad draw",
        "valid": "1..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# Four of every five samples use a canvas profile seen in the canonical task;
# the fifth broadens padding and independently varies the constructive axes.
_SCHEDULE_PERIOD = 5
EXAMPLES_NEEDED = 3
_CANONICAL_TEMPLATES = (
    {
        "canvas": (13, 18),
        "orientation": "right",
        "body_shape": "3x4",
        "target_shape": "7x7",
        "tail_length": 3,
    },
    {
        "canvas": (17, 14),
        "orientation": "up",
        "body_shape": "3x4",
        "target_shape": "3x7",
        "tail_length": 4,
    },
    {
        "canvas": (15, 19),
        "orientation": "up",
        "body_shape": "6x8",
        "target_shape": "2x5",
        "tail_length": 4,
    },
    {
        "canvas": (12, 17),
        "orientation": "left",
        "body_shape": "3x4",
        "target_shape": "8x5",
        "tail_length": 5,
    },
)


def _parse_shape(value: str) -> tuple[int, int]:
    height, width = value.split("x", 1)
    return int(height), int(width)


def _draw_scheduled_choice(ctx, name: str, domain: tuple[str, ...], default: str) -> str:
    """Use a deterministic scheduled default while retaining exact overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, domain)
    return ctx.draw_choice(name, (default,))


def _draw_scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _scheduled_defaults(ctx, sample_index: int):
    slot = sample_index % _SCHEDULE_PERIOD
    if slot < len(_CANONICAL_TEMPLATES):
        return dict(_CANONICAL_TEMPLATES[slot]), True

    broad_index = sample_index // _SCHEDULE_PERIOD
    defaults = {
        # Cycling broad slots guarantees that a short consecutive sample window
        # includes all four directions, rather than relying on luck.
        "orientation": ORIENTATIONS[broad_index % len(ORIENTATIONS)],
        "body_shape": ctx.draw_rng("broad_body_default").choice(BODY_SHAPES),
        "target_shape": ctx.draw_rng("broad_target_default").choice(TARGET_SHAPES),
        "tail_length": ctx.draw_rng("broad_tail_default").choice(TAIL_LENGTHS),
        "canvas": None,
    }
    return defaults, False


def _minimum_canvas(
    orientation: str,
    body_shape: tuple[int, int],
    target_shape: tuple[int, int],
    tail_length: int,
) -> tuple[int, int]:
    body_h, body_w = body_shape
    target_h, target_w = target_shape
    if orientation in ("right", "left"):
        return max(body_h, target_h) + 2, body_w + tail_length + target_w + 2
    return body_h + tail_length + target_h + 2, max(body_w, target_w) + 2


def _canvas_for(ctx, minimum: tuple[int, int], scheduled_canvas, difficulty, canonical_slot):
    min_h, min_w = minimum
    if canonical_slot and scheduled_canvas is not None:
        return max(min_h, scheduled_canvas[0]), max(min_w, scheduled_canvas[1])

    pad_range = {
        None: (0, 4),
        "easy": (0, 1),
        "medium": (1, 3),
        "hard": (3, 5),
    }[difficulty]
    pad_h = ctx.draw_rng("canvas_padding_h").randint(*pad_range)
    pad_w = ctx.draw_rng("canvas_padding_w").randint(*pad_range)
    height, width = min_h + pad_h, min_w + pad_w
    if height > 30 or width > 30:
        raise ValueError(f"constructed canvas {(height, width)} exceeds ARC's 30x30 limit")
    return height, width


def _choose_overlapping_offsets(rng, extent: int, first_size: int, second_size: int):
    """Choose two in-bounds spans and one coordinate in their intersection."""
    pairs = []
    for first in range(1, extent - first_size):
        for second in range(1, extent - second_size):
            lo = max(first, second)
            hi = min(first + first_size - 1, second + second_size - 1)
            if lo <= hi:
                pairs.append((first, second, lo, hi))
    if not pairs:
        raise ValueError(
            f"no overlapping placements for sizes {first_size} and {second_size} in extent {extent}"
        )
    first, second, lo, hi = rng.choice(pairs)
    return first, second, rng.randint(lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a plain integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults, canonical_slot = _scheduled_defaults(ctx, sample_index)
    orientation = _draw_scheduled_choice(
        ctx, "orientation", ORIENTATIONS, defaults["orientation"]
    )
    body_name = _draw_scheduled_choice(
        ctx, "body_shape", BODY_SHAPES, defaults["body_shape"]
    )
    target_name = _draw_scheduled_choice(
        ctx, "target_shape", TARGET_SHAPES, defaults["target_shape"]
    )
    tail_length = _draw_scheduled_int(
        ctx, "tail_length", min(TAIL_LENGTHS), max(TAIL_LENGTHS), defaults["tail_length"]
    )

    body_h, body_w = _parse_shape(body_name)
    target_h, target_w = _parse_shape(target_name)
    minimum = _minimum_canvas(
        orientation, (body_h, body_w), (target_h, target_w), tail_length
    )
    height, width = _canvas_for(
        ctx, minimum, defaults.get("canvas"), difficulty, canonical_slot
    )
    moving_color, target_color = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    grid = full_grid(height, width, 0)
    placement_rng = ctx.draw_rng("placement")

    if orientation in ("right", "left"):
        body_top, target_top, tail_row = _choose_overlapping_offsets(
            placement_rng, height, body_h, target_h
        )
        occupied_width = body_w + tail_length + target_w
        start_col = placement_rng.randint(1, width - occupied_width - 1)
        if orientation == "right":
            body_left = start_col
            target_left = body_left + body_w + tail_length
        else:
            target_left = start_col
            body_left = target_left + target_w + tail_length

        draw_rect(grid, body_top, body_left, body_h, body_w, moving_color)
        draw_rect(grid, target_top, target_left, target_h, target_w, target_color)
        if orientation == "right":
            for col in range(body_left + body_w, target_left):
                grid[tail_row][col] = moving_color
        else:
            for col in range(target_left + target_w, body_left):
                grid[tail_row][col] = moving_color
    else:
        body_left, target_left, tail_col = _choose_overlapping_offsets(
            placement_rng, width, body_w, target_w
        )
        occupied_height = body_h + tail_length + target_h
        start_row = placement_rng.randint(1, height - occupied_height - 1)
        if orientation == "down":
            body_top = start_row
            target_top = body_top + body_h + tail_length
        else:
            target_top = start_row
            body_top = target_top + target_h + tail_length

        draw_rect(grid, body_top, body_left, body_h, body_w, moving_color)
        draw_rect(grid, target_top, target_left, target_h, target_w, target_color)
        if orientation == "down":
            for row in range(body_top + body_h, target_top):
                grid[row][tail_col] = moving_color
        else:
            for row in range(target_top + target_h, body_top):
                grid[row][tail_col] = moving_color

    return grid


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_rectangle(cells) -> bool:
    r1, c1, r2, c2 = _bbox(cells)
    return len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1)


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                r, c = current
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _largest_filled_rectangle(cells):
    """Match the reference program's first-maximum enumeration order."""
    r1, c1, r2, c2 = _bbox(cells)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    prefix = [[0] * (width + 1) for _ in range(height + 1)]
    for row, col in cells:
        rr, cc = row - r1 + 1, col - c1 + 1
        prefix[rr][cc] = 1
    for rr in range(1, height + 1):
        running = 0
        for cc in range(1, width + 1):
            running += prefix[rr][cc]
            prefix[rr][cc] = prefix[rr - 1][cc] + running

    def count(top, left, bottom, right):
        a, b = top - r1, left - c1
        c, d = bottom - r1 + 1, right - c1 + 1
        return prefix[c][d] - prefix[a][d] - prefix[c][b] + prefix[a][b]

    best_area = 0
    best_box = None
    for top in range(r1, r2 + 1):
        for bottom in range(top, r2 + 1):
            for left in range(c1, c2 + 1):
                for right in range(left, c2 + 1):
                    area = (bottom - top + 1) * (right - left + 1)
                    if area > best_area and count(top, left, bottom, right) == area:
                        best_area = area
                        best_box = (top, left, bottom, right)
    if best_box is None:
        raise ValueError("creature has no filled rectangular body")
    top, left, bottom, right = best_box
    body = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    return body, best_box


def _analyze_geometry(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a non-empty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a non-empty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        raise ValueError("grid dimensions must be within 1..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")

    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) != 2:
        raise ValueError(f"expected exactly two nonzero colors, found {colors}")
    colored_components = []
    for color in colors:
        for cells in _components(grid, color):
            colored_components.append((color, cells))
    if len(colored_components) != 2:
        raise ValueError(
            f"expected exactly two connected colored objects, found {len(colored_components)}"
        )

    rectangles = [
        (color, cells) for color, cells in colored_components if _is_rectangle(cells)
    ]
    creatures = [
        (color, cells) for color, cells in colored_components if not _is_rectangle(cells)
    ]
    if len(rectangles) != 1 or len(creatures) != 1:
        raise ValueError("expected one solid rectangle and one non-rectangular creature")

    target_color, target_cells = rectangles[0]
    moving_color, moving_cells = creatures[0]
    body_cells, body_box = _largest_filled_rectangle(moving_cells)
    tail_cells = moving_cells - body_cells
    if not tail_cells:
        raise ValueError("creature must have a non-empty tail")

    br1, bc1, br2, bc2 = body_box
    tr1, tc1, tr2, tc2 = _bbox(target_cells)
    direction = None
    anchor = None
    expected_tail = None
    if all(row < br1 for row, _ in tail_cells):
        direction = "up"
        cols = {col for _, col in tail_cells}
        if len(cols) == 1:
            anchor = next(iter(cols))
            length = len(tail_cells)
            expected_tail = {(row, anchor) for row in range(br1 - length, br1)}
            target_flush = tr2 == br1 - length - 1 and tc1 <= anchor <= tc2
    elif all(row > br2 for row, _ in tail_cells):
        direction = "down"
        cols = {col for _, col in tail_cells}
        if len(cols) == 1:
            anchor = next(iter(cols))
            length = len(tail_cells)
            expected_tail = {(row, anchor) for row in range(br2 + 1, br2 + length + 1)}
            target_flush = tr1 == br2 + length + 1 and tc1 <= anchor <= tc2
    elif all(col < bc1 for _, col in tail_cells):
        direction = "left"
        rows = {row for row, _ in tail_cells}
        if len(rows) == 1:
            anchor = next(iter(rows))
            length = len(tail_cells)
            expected_tail = {(anchor, col) for col in range(bc1 - length, bc1)}
            target_flush = tc2 == bc1 - length - 1 and tr1 <= anchor <= tr2
    elif all(col > bc2 for _, col in tail_cells):
        direction = "right"
        rows = {row for row, _ in tail_cells}
        if len(rows) == 1:
            anchor = next(iter(rows))
            length = len(tail_cells)
            expected_tail = {(anchor, col) for col in range(bc2 + 1, bc2 + length + 1)}
            target_flush = tc1 == bc2 + length + 1 and tr1 <= anchor <= tr2

    if direction is None or anchor is None or expected_tail is None:
        raise ValueError("tail must be a straight one-cell-thick line outside one body side")
    if tail_cells != expected_tail:
        raise ValueError("tail must be contiguous, gap-free, and attached to the body")
    if not target_flush:
        raise ValueError("tail must exactly bridge the gap from body to target rectangle")

    body_h, body_w = br2 - br1 + 1, bc2 - bc1 + 1
    target_h, target_w = tr2 - tr1 + 1, tc2 - tc1 + 1
    # A strict area advantage makes the rule's largest-rectangle parse stable.
    runner_up_line = max(body_h, body_w) + len(tail_cells)
    if len(body_cells) <= runner_up_line:
        # Canonical 3x3 + length-3 is safe (9 > 6); this primarily protects
        # future externally supplied grids from tie/line ambiguities.
        raise ValueError("rectangular body is not uniquely larger than the extended tail line")

    vectors = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    return {
        "orientation": direction,
        "body_shape": f"{body_h}x{body_w}",
        "target_shape": f"{target_h}x{target_w}",
        "tail_length": len(tail_cells),
        "body_cells": body_cells,
        "body_box": body_box,
        "tail_cells": tail_cells,
        "moving_cells": moving_cells,
        "moving_color": moving_color,
        "target_cells": target_cells,
        "target_color": target_color,
        "vector": vectors[direction],
    }


def self_check(grid, *, difficulty=None, meta=None):
    try:
        _analyze_geometry(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    analysis = _analyze_geometry(grid)
    return {
        "orientation": analysis["orientation"],
        "body_shape": analysis["body_shape"],
        "target_shape": analysis["target_shape"],
        "tail_length": analysis["tail_length"],
    }


def _move_body(grid, steps):
    analysis = _analyze_geometry(grid)
    dr, dc = analysis["vector"]
    output = deepcopy(grid)
    for row, col in analysis["moving_cells"]:
        output[row][col] = 0
    for row, col in analysis["body_cells"]:
        output[row + dr * steps][col + dc * steps] = analysis["moving_color"]
    return output


def _slide_one_cell(grid):
    """Named rival: erase the tail but move the body only one cell."""
    return _move_body(grid, 1)


def _long_tail_requires_full_slide(grid):
    try:
        return _analyze_geometry(grid)["tail_length"] > 1
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {"long_tail_requires_full_slide": _long_tail_requires_full_slide}
SEMANTIC_RIVALS = {"slide_one_cell": _slide_one_cell}
WITNESS_RIVALS = {"long_tail_requires_full_slide": ["slide_one_cell"]}
CANONICAL_SHORTCUTS = {"slide_one_cell": _slide_one_cell}
LESSON_COMPETITORS = {"slide_one_cell": _slide_one_cell}
