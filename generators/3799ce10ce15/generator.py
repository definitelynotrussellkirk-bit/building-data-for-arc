"""Generator for 3799ce10ce15 — frame-by-color presence matrix.

The first row is an ordered legend of distinct colors.  Every exact hollow
color-9 rectangle contributes one output row, ordered by the frame's top-left
corner.  A row contains each legend color when that color occurs anywhere in
the corresponding frame interior, and 0 otherwise.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3799ce10ce15"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "7962236ae928"

SUMMARY = (
    "Read the nonzero, non-9 colors in row 0 from left to right. For each "
    "hollow 9-frame in top-left order, emit that legend color when it is "
    "present in the frame interior, otherwise 0."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and the frame color is 9",
    "row 0 contains 2..4 distinct legend colors in left-to-right order",
    "the body contains 2..4 separate exact hollow rectangular 9-frames",
    "every non-background body color belongs to the legend and lies inside one frame",
    "every frame interior is non-empty and at least two frame-presence rows differ",
]

# Every declared axis is exact, strict, and recoverable from the returned grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled across 13..18",
        "valid": "13..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled across 18..25",
        "valid": "18..25",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled across 2..4",
        "valid": "2..4",
    },
    "n_frames": {
        "type": "int",
        "default": "scheduled across 2..4",
        "valid": "2..4",
    },
    "copies_per_present": {
        "type": "int",
        "default": "scheduled across 1..3",
        "valid": "1..3",
    },
}

# Residues 0, 4 and 8 deliberately anchor the exact canonical input profile
# (13x18 with colors {0,9}+three legend colors) in every difficulty band.
_PROFILES = (
    (13, 18, 3, 3, 1),
    (14, 19, 2, 2, 2),
    (15, 20, 4, 4, 3),
    (16, 21, 3, 4, 1),
    (13, 18, 3, 3, 2),
    (17, 22, 4, 2, 3),
    (18, 23, 2, 3, 1),
    (14, 24, 3, 4, 2),
    (13, 18, 3, 3, 3),
    (15, 25, 4, 2, 1),
    (16, 20, 2, 4, 2),
    (18, 18, 4, 3, 3),
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 4, "hard": 8}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared deterministic curriculum residue."""
    del seed
    if difficulty not in _BAND_OFFSETS:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    return (int(sample_index) + _BAND_OFFSETS[difficulty]) % len(_PROFILES)


def _is_rectangular_int_grid(grid) -> tuple[bool, str]:
    if not isinstance(grid, list) or not grid:
        return False, "grid must be a non-empty list"
    if not isinstance(grid[0], list) or not grid[0]:
        return False, "grid rows must be non-empty lists"
    width = len(grid[0])
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != width:
            return False, f"row {r} is ragged or not a list"
        for c, value in enumerate(row):
            if type(value) is not int:
                return False, f"cell ({r},{c}) is not an integer"
            if not 0 <= value <= 9:
                return False, f"cell ({r},{c})={value} is outside 0..9"
    return True, ""


def _nine_components(grid) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        todo = deque([start])
        cells = {start}
        while todo:
            r, c = todo.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    cells.add((rr, cc))
                    todo.append((rr, cc))
        components.append(cells)
    return components


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _border(r0: int, c0: int, r1: int, c1: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _frame_boxes(grid) -> tuple[list[tuple[int, int, int, int]], list[str]]:
    boxes: list[tuple[int, int, int, int]] = []
    errors: list[str] = []
    for index, cells in enumerate(_nine_components(grid)):
        r0, c0, r1, c1 = _bbox(cells)
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            errors.append(f"9-component {index} is too small to be a frame")
            continue
        expected = _border(r0, c0, r1, c1)
        if cells != expected:
            errors.append(f"9-component {index} is not an exact hollow rectangle")
            continue
        boxes.append((r0, c0, r1, c1))
    return sorted(boxes), errors


def _legend(grid) -> list[int]:
    return [value for value in grid[0] if value not in (0, 9)]


def _presence_counts(grid, box, palette) -> Counter:
    r0, c0, r1, c1 = box
    return Counter(
        grid[r][c]
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] in palette
    )


def _apply(grid) -> list[list[int]]:
    palette = _legend(grid)
    boxes, _ = _frame_boxes(grid)
    output = []
    for box in boxes:
        present = set(_presence_counts(grid, box, palette))
        output.append([color if color in present else 0 for color in palette])
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task grammar while accepting every canonical input."""
    del difficulty, meta
    valid, message = _is_rectangular_int_grid(grid)
    if not valid:
        return [message]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if h > 30 or w > 30:
        errors.append("grid exceeds the ARC 30x30 canvas")

    if any(value == 9 for value in grid[0]):
        errors.append("legend row may not contain frame color 9")
    palette = _legend(grid)
    if not 2 <= len(palette) <= 4:
        errors.append(f"legend must contain 2..4 colors, found {len(palette)}")
    if len(set(palette)) != len(palette):
        errors.append("legend colors must be distinct")

    boxes, frame_errors = _frame_boxes(grid)
    errors.extend(frame_errors)
    if not 2 <= len(boxes) <= 4:
        errors.append(f"body must contain 2..4 exact frames, found {len(boxes)}")

    interior_owner: dict[tuple[int, int], int] = {}
    for index, (r0, c0, r1, c1) in enumerate(boxes):
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                interior_owner[(r, c)] = index

    patterns: list[tuple[bool, ...]] = []
    union_present: set[int] = set()
    for index, box in enumerate(boxes):
        counts = _presence_counts(grid, box, palette)
        present = set(counts)
        if not present:
            errors.append(f"frame {index} has an empty interior")
        union_present.update(present)
        patterns.append(tuple(color in present for color in palette))

    for r in range(1, h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 9):
                continue
            if value not in palette:
                errors.append(f"body color {value} at ({r},{c}) is absent from the legend")
            if (r, c) not in interior_owner:
                errors.append(f"colored body cell ({r},{c}) lies outside every frame interior")

    # Canonical demonstrations may include a legend color absent from every
    # frame; that is a lawful all-zero output column. Generated lessons still
    # cover every legend color by construction, but acceptance must follow the
    # authority rather than that curriculum preference.
    if len(patterns) >= 2 and len(set(patterns)) < 2:
        errors.append("all frames have the same presence row")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The lawful manifold is exactly the validated frame/legend grammar."""
    return self_check(grid)


def _fixed_canonical_windows(grid):
    """Canonical-fitting shortcut: hard-code public legend and frame windows."""
    valid, _ = _is_rectangular_int_grid(grid)
    if not valid:
        return []
    h, w = len(grid), len(grid[0])
    palette = [grid[0][c] if c < w else 0 for c in (2, 5, 8)]
    output = []
    for r0, c0, r1, c1 in ((3, 1, 9, 5), (3, 7, 9, 11), (3, 13, 9, 17)):
        present = {
            grid[r][c]
            for r in range(r0 + 1, min(r1, h))
            for c in range(c0 + 1, min(c1, w))
        }
        output.append(
            [color if color not in (0, 9) and color in present else 0 for color in palette]
        )
    return output


def _exactly_once_presence(grid):
    palette = _legend(grid)
    boxes, _ = _frame_boxes(grid)
    output = []
    for box in boxes:
        counts = _presence_counts(grid, box, palette)
        output.append([color if counts[color] == 1 else 0 for color in palette])
    return output


def _witness_fixed_windows(grid) -> bool:
    try:
        return _fixed_canonical_windows(grid) != _apply(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _witness_repeated_presence(grid) -> bool:
    try:
        palette = _legend(grid)
        boxes, errors = _frame_boxes(grid)
        return not errors and any(
            count > 1
            for box in boxes
            for count in _presence_counts(grid, box, palette).values()
        )
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "fixed_canonical_windows_break": _witness_fixed_windows,
    "repeated_presence_cells": _witness_repeated_presence,
}
SEMANTIC_RIVALS = {
    "fixed_canonical_windows": _fixed_canonical_windows,
    "exactly_once_presence": _exactly_once_presence,
}
WITNESS_RIVALS = {
    "fixed_canonical_windows_break": ["fixed_canonical_windows"],
    "repeated_presence_cells": ["exactly_once_presence"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_canonical_windows": _fixed_canonical_windows,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose pairs are invalid or whose demos leave a rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        grammar = self_check(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the grammar: {grammar[0]}")
            continue
        if _apply(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the presence rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            if survives and competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not falsify rival: {name}")
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from pixels alone."""
    findings = self_check(grid)
    if findings:
        raise ValueError(f"cannot observe invalid grid: {findings[0]}")
    palette = _legend(grid)
    boxes, _ = _frame_boxes(grid)
    counts = [
        count
        for box in boxes
        for count in _presence_counts(grid, box, palette).values()
        if count
    ]
    if not counts or len(set(counts)) != 1:
        raise ValueError("copies_per_present is not uniform on this grid")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len(palette),
        "n_frames": len(boxes),
        "copies_per_present": counts[0],
    }


def _presence_codes(rng, palette_size: int, n_frames: int) -> list[int]:
    full = (1 << palette_size) - 1
    first = rng.randint(1, full - 1)
    codes = [first, full ^ first]
    while len(codes) < n_frames:
        codes.append(rng.randint(1, full))
    rng.shuffle(codes)
    return codes


def _frame_size(rng, occupied_cells: int) -> tuple[int, int]:
    candidates = [
        (height, width)
        for height in (4, 5)
        for width in (4, 5, 6)
        if (height - 2) * (width - 2) >= occupied_cells
    ]
    if not candidates:
        raise ValueError(f"no frame can hold {occupied_cells} interior cells")
    return rng.choice(candidates)


def _distribute_extra(rng, amount: int, buckets: int) -> list[int]:
    result = [0] * buckets
    for _ in range(amount):
        result[rng.randrange(buckets)] += 1
    return result


def _pack_frames(
    rng,
    grid_h: int,
    grid_w: int,
    sizes: list[tuple[int, int]],
) -> list[tuple[int, int, int, int]]:
    slots = [(0, 0), (0, 1), (1, 0), (1, 1)]
    chosen = rng.sample(slots, len(sizes)) if len(sizes) < 4 else slots[:]
    rng.shuffle(chosen)

    active_rows = sorted({row for row, _ in chosen})
    active_cols = sorted({col for _, col in chosen})
    row_size = {
        row: max(size[0] for size, slot in zip(sizes, chosen) if slot[0] == row)
        for row in active_rows
    }
    col_size = {
        col: max(size[1] for size, slot in zip(sizes, chosen) if slot[1] == col)
        for col in active_cols
    }

    body_start = 2
    body_height = grid_h - body_start
    min_row_total = sum(row_size.values()) + max(0, len(active_rows) - 1)
    min_col_total = sum(col_size.values()) + max(0, len(active_cols) - 1)
    if min_row_total > body_height or min_col_total > grid_w:
        raise ValueError("frame pack does not fit the requested grid")

    row_gaps = _distribute_extra(rng, body_height - min_row_total, len(active_rows) + 1)
    col_gaps = _distribute_extra(rng, grid_w - min_col_total, len(active_cols) + 1)

    row_origin: dict[int, int] = {}
    cursor = body_start + row_gaps[0]
    for index, row in enumerate(active_rows):
        row_origin[row] = cursor
        cursor += row_size[row]
        if index + 1 < len(active_rows):
            cursor += 1 + row_gaps[index + 1]

    col_origin: dict[int, int] = {}
    cursor = col_gaps[0]
    for index, col in enumerate(active_cols):
        col_origin[col] = cursor
        cursor += col_size[col]
        if index + 1 < len(active_cols):
            cursor += 1 + col_gaps[index + 1]

    boxes = []
    for (height, width), (slot_row, slot_col) in zip(sizes, chosen):
        top = row_origin[slot_row] + rng.randint(0, row_size[slot_row] - height)
        left = col_origin[slot_col] + rng.randint(0, col_size[slot_col] - width)
        boxes.append((top, left, top + height - 1, left + width - 1))
    return boxes


def _draw_frame(grid, box) -> None:
    r0, c0, r1, c1 = box
    for r, c in _border(r0, c0, r1, c1):
        grid[r][c] = 9


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_OFFSETS:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    profile_index = schedule_profile(seed, sample_index, difficulty)
    defaults = dict(zip(AXES, _PROFILES[profile_index]))
    effective = {
        key: value for key, value in overrides.items() if value is not None
    }
    for key, value in defaults.items():
        effective.setdefault(key, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    grid_h = ctx.draw_int_strict("grid_h", 13, 18)
    grid_w = ctx.draw_int_strict("grid_w", 18, 25)
    palette_size = ctx.draw_int_strict("palette_size", 2, 4)
    n_frames = ctx.draw_int_strict("n_frames", 2, 4)
    copies = ctx.draw_int_strict("copies_per_present", 1, 3)

    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(range(1, 9), palette_size)

    legend_rng = ctx.draw_rng("legend_positions")
    for _ in range(64):
        legend_columns = tuple(sorted(legend_rng.sample(range(grid_w), palette_size)))
        if palette_size != 3 or legend_columns != (2, 5, 8):
            break
    else:
        raise ValueError("could not choose non-canonical legend columns")

    pattern_rng = ctx.draw_rng("presence_patterns")
    codes = _presence_codes(pattern_rng, palette_size, n_frames)
    sizes = [
        _frame_size(
            ctx.draw_rng(f"frame_size_{index}"),
            code.bit_count() * copies,
        )
        for index, code in enumerate(codes)
    ]
    boxes = _pack_frames(ctx.draw_rng("frame_layout"), grid_h, grid_w, sizes)

    grid = full_grid(grid_h, grid_w, 0)
    for column, color in zip(legend_columns, palette):
        grid[0][column] = color

    for frame_index, (box, code) in enumerate(zip(boxes, codes)):
        _draw_frame(grid, box)
        r0, c0, r1, c1 = box
        interior = [
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        ]
        fill_rng = ctx.draw_rng(f"frame_fill_{frame_index}")
        fill_rng.shuffle(interior)
        values = [
            palette[color_index]
            for color_index in range(palette_size)
            if code & (1 << color_index)
            for _ in range(copies)
        ]
        fill_rng.shuffle(values)
        for (r, c), value in zip(interior, values):
            grid[r][c] = value

    findings = self_check(grid)
    if findings:
        raise AssertionError(f"generated invalid grid: {findings[:3]}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "palette_size": palette_size,
        "n_frames": n_frames,
        "copies_per_present": copies,
    }
    if observed != expected:
        raise AssertionError(f"axis observability mismatch: {observed} != {expected}")
    return grid
