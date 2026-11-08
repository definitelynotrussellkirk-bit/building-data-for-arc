"""Generator for ARC task 7bb29440 / content hash 97bcb3b9194e.

The input contains separated solid blue rectangles.  Each rectangle has blue
body cells and one or more non-blue mark cells.  Exactly one rectangle has the
fewest marks; the Racket oracle returns that rectangle cropped to its bounding
box.
"""
from __future__ import annotations

from math import ceil, sqrt

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "97bcb3b9194e"
TASK_ID = "97bcb3b9194e"
VERSION = "4.0.0"
RULE_HASH = "d21a7bae9946"
SUMMARY = (
    "A 0-background grid contains 2-7 separated solid rectangular objects. "
    "Every object has a blue (1) body plus one or more non-blue marks. Exactly "
    "one rectangle has the fewest marks. Select that rectangle and return its "
    "bounding-box crop unchanged."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0 and every nonzero component is a filled rectangle",
    "there are 2-7 rectangles, each 3-10 cells tall and wide",
    "every rectangle contains blue body cells and at least one non-blue mark",
    "the minimum non-blue mark count is unique",
    "rectangle bounding boxes have at least one background row or column between them",
]

MARK_PALETTES = {
    "canonical": (4, 6),
    "four_only": (4,),
    "six_only": (6,),
}
WINNER_POSITIONS = ("first", "middle", "last")

# Public axes are exact scene properties, not loose placement hints.  Each is
# recoverable from observe_overrides(), and explicit values use the same global
# validity range in every difficulty band.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "12..28"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "11..28"},
    "n_boxes": {"type": "int", "default": "scheduled by band", "valid": "2..7"},
    "winner_marks": {"type": "int", "default": "sample_index cycle", "valid": "1..3"},
    "mark_palette": {
        "type": "str",
        "default": "sample_index cycle",
        "valid": "canonical|four_only|six_only",
    },
    "winner_position": {
        "type": "str",
        "default": "sample_index alternation",
        "valid": "first|middle|last",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic, fresh input grid for the canonical Racket rule."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    box_schedule = _band_box_schedule(difficulty)
    if (
        overrides.get("winner_position") == "middle"
        and overrides.get("n_boxes") is None
    ):
        box_schedule = tuple(value for value in box_schedule if value >= 3)
    n_boxes = _scheduled_int(
        ctx,
        "n_boxes",
        box_schedule,
        sample_index // 3,
        global_lo=2,
        global_hi=7,
    )
    winner_marks = _scheduled_int(
        ctx,
        "winner_marks",
        (1, 2, 3),
        sample_index,
        global_lo=1,
        global_hi=3,
    )
    palette_name = _scheduled_choice(
        ctx,
        "mark_palette",
        tuple(MARK_PALETTES),
        sample_index // 2,
    )
    winner_position = _scheduled_winner_position(ctx, n_boxes, sample_index)

    preferred_rows = max(1, min(n_boxes, round(sqrt(n_boxes))))
    preferred_cols = ceil(n_boxes / preferred_rows)
    preferred_h = max(12, preferred_rows * 5 + preferred_rows - 1)
    preferred_w = max(11, preferred_cols * 5 + preferred_cols - 1)
    h = _draw_dimension(
        ctx, "grid_h", preferred_h, 12, 28, sample_index, canonical_hi=22
    )
    w = _draw_dimension(
        ctx, "grid_w", preferred_w, 11, 28, sample_index, canonical_hi=25
    )

    placement_rng = ctx.draw_rng("placement")
    slots = _make_slots(h, w, n_boxes, placement_rng)
    if winner_position == "first":
        winner_index = 0
    elif winner_position == "last":
        winner_index = len(slots) - 1
    else:
        winner_index = len(slots) // 2
    boxes = _size_and_place_boxes(
        slots, winner_index, sample_index, placement_rng
    )
    boxes.sort(key=lambda box: (box[0], box[1]))
    mark_counts = _mark_counts(n_boxes, winner_index, winner_marks, placement_rng)
    total_marks = sum(mark_counts)
    mark_colors = _mark_color_stream(
        MARK_PALETTES[palette_name], total_marks, placement_rng
    )

    grid = full_grid(h, w, 0)
    color_cursor = 0
    for index, (r1, c1, r2, c2) in enumerate(boxes):
        bh = r2 - r1 + 1
        bw = c2 - c1 + 1
        draw_rect(grid, r1, c1, bh, bw, 1)
        cells = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
        cell_rng = ctx.draw_rng(f"marks:{index}")
        cell_rng.shuffle(cells)
        count = mark_counts[index]
        if count >= len(cells):
            raise ValueError("mark count would erase the blue body")
        for r, c in cells[:count]:
            grid[r][c] = mark_colors[color_cursor]
            color_cursor += 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("internal generation invariant failed: " + "; ".join(errors))
    return grid


def rule_mirror(grid):
    """Independent Python mirror used only by tests and evidence tooling."""
    records, structural_errors = _component_records(grid)
    if structural_errors or not records:
        raise ValueError("cannot apply rule mirror to malformed scene")
    mark_counts = [record["marks"] for record in records]
    best = records[mark_counts.index(min(mark_counts))]
    r1, c1, r2, c2 = best["bbox"]
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def observe_overrides(grid):
    """Recover every exact public axis from a returned valid scene."""
    records, structural_errors = _component_records(grid)
    if structural_errors:
        raise ValueError("cannot observe malformed scene: " + "; ".join(structural_errors))
    mark_counts = [record["marks"] for record in records]
    if not mark_counts or mark_counts.count(min(mark_counts)) != 1:
        raise ValueError("scene lacks a unique fewest-mark rectangle")
    winner_index = mark_counts.index(min(mark_counts))
    mark_colors = {
        grid[r][c]
        for record in records
        for r, c in record["cells"]
        if grid[r][c] not in (0, 1)
    }
    reverse_palettes = {frozenset(colors): name for name, colors in MARK_PALETTES.items()}
    palette_name = reverse_palettes.get(frozenset(mark_colors), "other")
    if winner_index == 0:
        winner_position = "first"
    elif winner_index == len(records) - 1:
        winner_position = "last"
    else:
        winner_position = "middle"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_boxes": len(records),
        "winner_marks": min(mark_counts),
        "mark_palette": palette_name,
        "winner_position": winner_position,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete teaching grammar, including malformed components."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC bounds: {len(grid)}x{width}"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid contains a non-integer or color outside 0..9"]
    if not any(value == 0 for row in grid for value in row):
        return ["background color 0 is absent"]

    records, errors = _component_records(grid)
    if not 2 <= len(records) <= 7:
        errors.append(f"expected 2-7 rectangular components, found {len(records)}")

    mark_counts = []
    for record in records:
        bh, bw = record["dims"]
        if not (3 <= bh <= 10 and 3 <= bw <= 10):
            errors.append(f"rectangle dimensions must be 3..10, got {bh}x{bw}")
        if record["blue"] == 0:
            errors.append("every rectangle must retain at least one blue body cell")
        if record["marks"] == 0:
            errors.append("every rectangle must contain at least one non-blue mark")
        mark_counts.append(record["marks"])

    if mark_counts and mark_counts.count(min(mark_counts)) != 1:
        errors.append(f"fewest mark count must be unique, got {mark_counts}")

    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            if _boxes_touch_or_overlap(left["bbox"], right["bbox"]):
                errors.append("rectangle bounding boxes need a one-cell background gap")
                break
    return errors


def _scheduled_int(ctx, label, values, sample_index, *, global_lo, global_hi):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, global_lo, global_hi)
    value = values[sample_index % len(values)]
    return ctx.draw_int(label, value, value)



def _scheduled_winner_position(ctx, n_boxes, sample_index):
    if "winner_position" in ctx.overrides and ctx.overrides["winner_position"] is not None:
        value = ctx.draw_choice("winner_position", WINNER_POSITIONS)
        if value == "middle" and n_boxes < 3:
            raise ValueError("winner_position=middle requires n_boxes >= 3")
        return value
    values = WINNER_POSITIONS if n_boxes >= 3 else ("first", "last")
    value = values[sample_index % len(values)]
    return ctx.draw_choice("winner_position", (value,))

def _scheduled_choice(ctx, label, values, sample_index):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, values)
    value = values[sample_index % len(values)]
    return ctx.draw_choice(label, (value,))


def _draw_dimension(
    ctx, label, preferred_lo, global_lo, global_hi, sample_index, *, canonical_hi
):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, global_lo, global_hi)
    preferred_lo = max(global_lo, min(preferred_lo, global_hi))
    if sample_index % 3 == 0:
        return ctx.draw_int(label, min(preferred_lo, canonical_hi), canonical_hi)
    return ctx.draw_int_diff(label, preferred_lo, global_hi)


def _band_box_schedule(difficulty):
    if difficulty == "easy":
        return (2, 3, 4)
    if difficulty == "hard":
        return (5, 6, 7)
    if difficulty == "medium":
        return (3, 4, 5, 6)
    return (2, 3, 4, 5, 6, 7)


def _make_slots(h, w, n_boxes, rng):
    candidates = []
    for rows in range(1, n_boxes + 1):
        cols = ceil(n_boxes / rows)
        if rows * 3 + rows - 1 > h or cols * 3 + cols - 1 > w:
            continue
        unused = rows * cols - n_boxes
        cell_aspect = (h - rows + 1) / rows / ((w - cols + 1) / cols)
        score = (unused, abs(cell_aspect - 1.0), abs(rows - cols), rng.random())
        candidates.append((score, rows, cols))
    if not candidates:
        raise ValueError(f"cannot place {n_boxes} separated 3x3 rectangles in {h}x{w}")
    _, rows, cols = min(candidates, key=lambda item: item[0])

    row_sizes = _partition(h - (rows - 1), rows, 3, rng)
    col_sizes = _partition(w - (cols - 1), cols, 3, rng)
    row_starts = []
    cursor = 0
    for size in row_sizes:
        row_starts.append(cursor)
        cursor += size + 1
    col_starts = []
    cursor = 0
    for size in col_sizes:
        col_starts.append(cursor)
        cursor += size + 1

    all_slots = [
        (row_starts[r], col_starts[c], row_sizes[r], col_sizes[c])
        for r in range(rows)
        for c in range(cols)
    ]
    selected = sorted(rng.sample(all_slots, n_boxes), key=lambda slot: (slot[0], slot[1]))
    return selected


def _partition(total, parts, minimum, rng):
    if total < parts * minimum:
        raise ValueError("partition cannot satisfy minimum slot size")
    sizes = [minimum] * parts
    for _ in range(total - parts * minimum):
        sizes[rng.randrange(parts)] += 1
    return sizes


def _size_and_place_boxes(slots, winner_slot_index, sample_index, rng):
    limits = [(min(10, sh), min(10, sw)) for _, _, sh, sw in slots]
    dims = [(rng.randint(3, mh), rng.randint(3, mw)) for mh, mw in limits]
    # Within ordinary lessons, size is deliberately not a stable selector.
    # For n>=3 the winner shares its dimensions with one distractor, while a
    # second distractor lies on the opposite side of the size range.  The role
    # alternates across sample_index, rebutting both smallest- and largest-box
    # shortcuts at episode level.
    if len(slots) >= 3:
        other_indices = [i for i in range(len(slots)) if i != winner_slot_index]
        twin = other_indices[0]
        opposite = other_indices[-1]
        if sample_index % 2 == 0:
            common_h = min(limits[winner_slot_index][0], limits[twin][0])
            common_w = min(limits[winner_slot_index][1], limits[twin][1])
            dims[winner_slot_index] = (common_h, common_w)
            dims[twin] = (common_h, common_w)
            dims[opposite] = (3, 3)
        else:
            dims[winner_slot_index] = (3, 3)
            dims[twin] = (3, 3)
            dims[opposite] = limits[opposite]
    elif len(slots) == 2:
        other = 1 - winner_slot_index
        if sample_index % 2 == 0:
            dims[winner_slot_index] = limits[winner_slot_index]
            dims[other] = (3, 3)
        else:
            dims[winner_slot_index] = (3, 3)
            dims[other] = limits[other]

    boxes = []
    for (sr, sc, sh, sw), (bh, bw) in zip(slots, dims):
        rr = sr + rng.randint(0, sh - bh)
        rc = sc + rng.randint(0, sw - bw)
        boxes.append((rr, rc, rr + bh - 1, rc + bw - 1))
    return boxes


def _mark_counts(n_boxes, winner_index, winner_marks, rng):
    upper = 6
    distractor_count = rng.randint(winner_marks + 1, upper)
    counts = []
    for index in range(n_boxes):
        if index == winner_index:
            counts.append(winner_marks)
        elif n_boxes >= 3 and len([c for c in counts if c == distractor_count]) < 2:
            counts.append(distractor_count)
        else:
            counts.append(rng.randint(winner_marks + 1, upper))
    return counts


def _mark_color_stream(palette, total, rng):
    if total <= 0:
        return []
    colors = list(palette[: min(len(palette), total)])
    while len(colors) < total:
        colors.append(rng.choice(palette))
    rng.shuffle(colors)
    return colors


def _component_records(grid):
    h = len(grid)
    w = len(grid[0])
    seen = set()
    records = []
    errors = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            bbox_cells = {
                (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            }
            if cells != bbox_cells or any(grid[r][c] == 0 for r, c in bbox_cells):
                errors.append(
                    f"nonzero component at ({r1},{c1}) is not a filled rectangle"
                )
            records.append(
                {
                    "bbox": (r1, c1, r2, c2),
                    "dims": (r2 - r1 + 1, c2 - c1 + 1),
                    "cells": cells,
                    "marks": sum(grid[r][c] not in (0, 1) for r, c in cells),
                    "blue": sum(grid[r][c] == 1 for r, c in cells),
                }
            )
    records.sort(key=lambda record: (record["bbox"][0], record["bbox"][1]))
    return records, errors


def _boxes_touch_or_overlap(left, right):
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    return not (
        lr2 + 1 < rr1
        or rr2 + 1 < lr1
        or lc2 + 1 < rc1
        or rc2 + 1 < lc1
    )
