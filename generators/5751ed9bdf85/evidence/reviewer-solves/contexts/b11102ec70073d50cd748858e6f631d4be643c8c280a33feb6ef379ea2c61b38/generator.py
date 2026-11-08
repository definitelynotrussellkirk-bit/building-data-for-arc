"""Generator for arc_additional_puzzle_bank_volume12:M79.

The selected gray (5) rectangular frame is the unique frame whose interior
contains exactly one non-zero, non-gray marker cell.  Fill only that frame's
zero interior cells with the marker color; leave every other frame unchanged.

Canonical lessons contain three roles: an empty frame, the one-marker target,
and a two-marker decoy.  Generated lessons preserve those roles while varying
target slot, target size rank, decoy multiplicity, and whether the decoy shares
the target color.  Shared-color decoys refute global marker-color uniqueness;
three-marker decoys refute the canonical-fitting shortcut "fill odd counts".
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

Grid = list[list[int]]

GENERATOR_ID = "5751ed9bdf85"
TASK_ID = GENERATOR_ID
VERSION = "3.1.1"
RULE_HASH = "7819ac1160c7"

SUMMARY = (
    "Several hollow gray (5) rectangular frames appear. Exactly one frame "
    "contains exactly one colored marker cell; fill only that frame's zero "
    "interior cells with that marker color. Frames with zero or multiple "
    "marker cells remain unchanged."
)
INVARIANTS = [
    "literal color 0 is the background and literal color 5 forms every frame perimeter",
    "each gray component is exactly one hollow rectangular perimeter",
    "exactly one frame contains exactly one non-zero non-gray interior marker cell",
    "all non-zero non-gray cells lie strictly inside a gray frame",
    "generated lessons include one empty frame and one two- or three-marker decoy in addition to the target",
    "the Racket rule is the sole output authority; rule_mirror is test-only parity logic",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

TARGET_SLOTS = ("top_left", "top_right", "bottom")
TARGET_SIZE_RANKS = ("smallest", "middle", "largest")
DECOY_COLOR_RELATIONS = ("distinct", "same_as_target")
DECOY_MARKER_COUNTS = (2, 3)
MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Every ordinary draw uses one canonical (height, width) profile.  Explicit
# dimension overrides may broaden the grid while preserving the same scene
# grammar; this keeps training anchored to all five canonical geometries.
_CANONICAL_DIMENSIONS = (
    (12, 14),
    (11, 13),
    (13, 12),
    (10, 15),
    (12, 12),
)
_CANONICAL_DIMENSION_SET = set(_CANONICAL_DIMENSIONS)

# Unique interior areas 3, 4, and 6 make target-size rank exactly observable.
_COMPACT_SIZE_BY_RANK = {
    "smallest": (3, 5),   # 1 x 3 interior
    "middle": (4, 4),     # 2 x 2 interior
    "largest": (4, 5),    # 2 x 3 interior
}
_EXPANDED_SIZE_BY_RANK = {
    "smallest": (3, 5),   # 1 x 3 interior
    "middle": (4, 4),     # 2 x 2 interior
    "largest": (6, 6),    # 4 x 4 interior, perimeter 20 (canonical maximum scale)
}

# Four consecutive sample indexes contain every profile once.  Therefore every
# EXAMPLES_NEEDED=4 sliding lesson window contains: a shared-color counterexample,
# a target that is not first, and a target that is not largest.
SCHEDULE_PROFILES = (
    "first_small_two_distinct",
    "right_large_three_shared",
    "bottom_middle_two_distinct",
    "right_small_three_shared",
)
_SCHEDULE = (
    {
        "target_slot": "top_left",
        "target_size_rank": "smallest",
        "decoy_color_relation": "distinct",
        "decoy_marker_count": 2,
    },
    {
        "target_slot": "top_right",
        "target_size_rank": "largest",
        "decoy_color_relation": "same_as_target",
        "decoy_marker_count": 3,
    },
    {
        "target_slot": "bottom",
        "target_size_rank": "middle",
        "decoy_color_relation": "distinct",
        "decoy_marker_count": 2,
    },
    {
        "target_slot": "top_right",
        "target_size_rank": "smallest",
        "decoy_color_relation": "same_as_target",
        "decoy_marker_count": 3,
    },
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-way canonical dimension schedule",
        "valid": "10..18",
    },
    "grid_w": {
        "type": "int",
        "default": "five-way canonical dimension schedule",
        "valid": "12..22",
    },
    "target_slot": {
        "type": "enum",
        "default": "four-way lesson schedule",
        "valid": "top_left|top_right|bottom",
    },
    "target_size_rank": {
        "type": "enum",
        "default": "four-way lesson schedule",
        "valid": "smallest|middle|largest",
    },
    "decoy_color_relation": {
        "type": "enum",
        "default": "four-way lesson schedule",
        "valid": "distinct|same_as_target",
    },
    "decoy_marker_count": {
        "type": "int",
        "default": "four-way lesson schedule",
        "valid": "2..3",
    },
    "target_color": {
        "type": "color",
        "default": "keyed draw from ARC colors except 0 and 5",
        "valid": "1..9 (≠5)",
    },
}

# Every Cartesian combination of declared exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the exact four-slot semantic schedule profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(cleaned) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    return cleaned


def _draw_dimension(ctx: Any, overrides: dict[str, Any], label: str, scheduled: int) -> int:
    lo, hi = (10, 18) if label == "grid_h" else (12, 22)
    if label in overrides:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, scheduled, scheduled))


def _draw_scheduled_choice(
    ctx: Any,
    overrides: dict[str, Any],
    label: str,
    scheduled: str,
    options: Sequence[str],
) -> str:
    choices = options if label in overrides else (scheduled,)
    return str(ctx.draw_choice(label, choices))


def _draw_scheduled_int(
    ctx: Any,
    overrides: dict[str, Any],
    label: str,
    scheduled: int,
    lo: int,
    hi: int,
) -> int:
    if label in overrides:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, scheduled, scheduled))


def _slot_bboxes(
    height: int,
    width: int,
    size_by_slot: dict[str, tuple[int, int]],
) -> dict[str, tuple[int, int, int, int]]:
    """Construct three separated frame boxes for every declared dimension."""
    boxes: dict[str, tuple[int, int, int, int]] = {}
    for slot in TARGET_SLOTS:
        frame_h, frame_w = size_by_slot[slot]
        if slot == "top_left":
            row0, col0 = 1, 0
        elif slot == "top_right":
            row0, col0 = 1, width - frame_w
        else:
            row0, col0 = height - frame_h, (width - frame_w) // 2
        boxes[slot] = (row0, col0, row0 + frame_h - 1, col0 + frame_w - 1)

    # These are construction assertions, not fallbacks: every declared boundary
    # must fit without overlap or connected gray borders.
    values = list(boxes.values())
    for row0, col0, row1, col1 in values:
        if not (0 <= row0 < row1 < height and 0 <= col0 < col1 < width):
            raise ValueError("declared grid dimensions cannot contain the scheduled frame geometry")
    for index, first in enumerate(values):
        for second in values[index + 1 :]:
            r0, c0, r1, c1 = first
            or0, oc0, or1, oc1 = second
            separated = r1 + 1 < or0 or or1 + 1 < r0 or c1 + 1 < oc0 or oc1 + 1 < c0
            if not separated:
                raise ValueError("declared grid dimensions make frame components touch or overlap")
    return boxes


def _interior_positions(box: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    row0, col0, row1, col1 = box
    return [
        (row, col)
        for row in range(row0 + 1, row1)
        for col in range(col0 + 1, col1)
    ]


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> Grid:
    """Return one deterministic lesson input with explicit shortcut controls."""
    _validate_difficulty(difficulty)
    overrides = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    dimension_offset = {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    dimension_index = (int(sample_index) + dimension_offset) % len(_CANONICAL_DIMENSIONS)
    scheduled_h, scheduled_w = _CANONICAL_DIMENSIONS[dimension_index]
    height = _draw_dimension(ctx, overrides, "grid_h", scheduled_h)
    width = _draw_dimension(ctx, overrides, "grid_w", scheduled_w)
    target_slot = _draw_scheduled_choice(
        ctx, overrides, "target_slot", scheduled["target_slot"], TARGET_SLOTS
    )
    target_size_rank = _draw_scheduled_choice(
        ctx,
        overrides,
        "target_size_rank",
        scheduled["target_size_rank"],
        TARGET_SIZE_RANKS,
    )
    color_relation = _draw_scheduled_choice(
        ctx,
        overrides,
        "decoy_color_relation",
        scheduled["decoy_color_relation"],
        DECOY_COLOR_RELATIONS,
    )
    decoy_marker_count = _draw_scheduled_int(
        ctx,
        overrides,
        "decoy_marker_count",
        scheduled["decoy_marker_count"],
        min(DECOY_MARKER_COUNTS),
        max(DECOY_MARKER_COUNTS),
    )
    target_color = int(ctx.draw_color("target_color", exclude={0, 5}))

    # Assign the requested target size exactly; shuffle the remaining two ranks
    # between the non-target slots so slot does not leak size or role.  A
    # three-marker decoy must retain at least one zero interior cell, otherwise
    # the odd-marker rival makes no observable change on that frame.
    remaining_slots = [slot for slot in TARGET_SLOTS if slot != target_slot]
    decoy_slot = remaining_slots[0]
    remaining_ranks = [rank for rank in TARGET_SIZE_RANKS if rank != target_size_rank]
    ctx.draw_rng("size_assignment").shuffle(remaining_ranks)
    if decoy_marker_count == 3 and remaining_ranks[0] == "smallest":
        remaining_ranks.reverse()
    rank_by_slot = {target_slot: target_size_rank}
    rank_by_slot.update(zip(remaining_slots, remaining_ranks))
    size_catalog = (
        _EXPANDED_SIZE_BY_RANK
        if difficulty == "hard" and height >= 12
        else _COMPACT_SIZE_BY_RANK
    )
    size_by_slot = {slot: size_catalog[rank] for slot, rank in rank_by_slot.items()}
    boxes = _slot_bboxes(height, width, size_by_slot)

    grid = full_grid(height, width, 0)
    for box in boxes.values():
        draw_frame(grid, *box, 5)

    # The earliest non-target slot is always the multi-marker decoy.  This makes
    # target_slot != top_left a direct counterexample to a row-major-first rule.
    target_cells = _interior_positions(boxes[target_slot])
    decoy_cells = _interior_positions(boxes[decoy_slot])
    target_rng = ctx.draw_rng("target_marker_position")
    decoy_rng = ctx.draw_rng("decoy_marker_positions")
    target_rng.shuffle(target_cells)
    decoy_rng.shuffle(decoy_cells)
    grid[target_cells[0][0]][target_cells[0][1]] = target_color

    if color_relation == "same_as_target":
        decoy_color = target_color
    else:
        decoy_color = ctx.draw_rng("decoy_color").choice(
            [color for color in MARKER_COLORS if color != target_color]
        )
    for row, col in decoy_cells[:decoy_marker_count]:
        grid[row][col] = decoy_color
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list or tuple of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty lists or tuples"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed the ARC 30x30 limit"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9 (not booleans)"]
    return []


def _gray_components(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for drow, dcol in _NEIGHBORS4:
                    nxt = (current[0] + drow, current[1] + dcol)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == 5
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(cells)
    return components


def _frame_record(
    grid: Sequence[Sequence[int]], component: Sequence[tuple[int, int]]
) -> tuple[dict[str, Any] | None, str | None]:
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    row0, row1 = min(rows), max(rows)
    col0, col1 = min(cols), max(cols)
    if row1 - row0 < 2 or col1 - col0 < 2:
        return None, "gray component is too small to be a hollow rectangular frame"
    perimeter = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    }
    if set(component) != perimeter:
        return None, "gray component is not exactly one rectangular perimeter"
    marker_cells = [
        (row, col, int(grid[row][col]))
        for row in range(row0 + 1, row1)
        for col in range(col0 + 1, col1)
        if grid[row][col] not in (0, 5)
    ]
    return {
        "bbox": (row0, col0, row1, col1),
        "marker_cells": marker_cells,
        "marker_count": len(marker_cells),
        "interior_area": (row1 - row0 - 1) * (col1 - col0 - 1),
    }, None


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "frames": []}
    height, width = len(grid), len(grid[0])
    components = _gray_components(grid)
    if not components:
        errors.append("no gray rectangular frame found")

    frames: list[dict[str, Any]] = []
    for component in components:
        record, error = _frame_record(grid, component)
        if error:
            errors.append(error)
        elif record is not None:
            frames.append(record)

    # Distinct frame rectangles may not geometrically overlap; otherwise a
    # non-gray cell could belong to two interiors and the target is ambiguous.
    for index, first in enumerate(frames):
        r0, c0, r1, c1 = first["bbox"]
        for second in frames[index + 1 :]:
            or0, oc0, or1, oc1 = second["bbox"]
            overlap = not (r1 < or0 or or1 < r0 or c1 < oc0 or oc1 < c0)
            if overlap:
                errors.append("gray frame rectangles overlap")
                break

    interior_cells: set[tuple[int, int]] = set()
    for frame in frames:
        row0, col0, row1, col1 = frame["bbox"]
        interior_cells.update(
            (row, col)
            for row in range(row0 + 1, row1)
            for col in range(col0 + 1, col1)
        )
    stray = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5) and (row, col) not in interior_cells
    ]
    if stray:
        errors.append("non-zero non-gray cells must lie strictly inside a gray frame")

    targets = [frame for frame in frames if frame["marker_count"] == 1]
    if len(targets) != 1:
        errors.append(f"expected exactly one one-marker frame, found {len(targets)}")
    frames.sort(key=lambda frame: (frame["bbox"][0], frame["bbox"][1]))
    return {
        "errors": errors,
        "frames": frames,
        "target": targets[0] if len(targets) == 1 else None,
        "height": height,
        "width": width,
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the authority-level frame grammar, including canonical inputs."""
    errors = list(_analyze_scene(grid).get("errors", ()))
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append("unknown difficulty band")
    if errors:
        return errors

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for key, value in requested.items():
                if key in AXES and value is not None and observed.get(key) != value:
                    errors.append(
                        f"override {key!r} observed {observed.get(key)!r}, requested {value!r}"
                    )
    return errors


def _generated_role_facts(grid: Any) -> dict[str, Any] | None:
    info = _analyze_scene(grid)
    if info.get("errors"):
        return None
    frames = info["frames"]
    if len(frames) != 3:
        return None
    counts = sorted(frame["marker_count"] for frame in frames)
    if (
        len(counts) != 3
        or counts[:2] != [0, 1]
        or counts[2] not in DECOY_MARKER_COUNTS
    ):
        return None
    target = info["target"]
    decoy = next(frame for frame in frames if frame["marker_count"] > 1)
    empty = next(frame for frame in frames if frame["marker_count"] == 0)
    del empty

    first_row = min(frame["bbox"][0] for frame in frames)
    top = sorted(
        [frame for frame in frames if frame["bbox"][0] == first_row],
        key=lambda frame: frame["bbox"][1],
    )
    bottom = max(frames, key=lambda frame: frame["bbox"][0])
    if len(top) != 2 or bottom in top:
        return None
    slot_by_id = {id(top[0]): "top_left", id(top[1]): "top_right", id(bottom): "bottom"}
    target_slot = slot_by_id.get(id(target))
    if target_slot is None:
        return None

    ranked = sorted(frames, key=lambda frame: frame["interior_area"])
    areas = [frame["interior_area"] for frame in ranked]
    if len(set(areas)) != 3:
        return None
    size_rank_by_id = {
        id(ranked[0]): "smallest",
        id(ranked[1]): "middle",
        id(ranked[2]): "largest",
    }
    target_color = target["marker_cells"][0][2]
    decoy_colors = [cell[2] for cell in decoy["marker_cells"]]
    relation = (
        "same_as_target"
        if all(color == target_color for color in decoy_colors)
        else "distinct"
    )
    return {
        "target_slot": target_slot,
        "target_size_rank": size_rank_by_id[id(target)],
        "decoy_color_relation": relation,
        "decoy_marker_count": decoy["marker_count"],
        "target_color": target_color,
        "marker_counts": counts,
        "target": target,
        "decoy": decoy,
    }


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Recover every declared exact axis from a valid generated scene."""
    facts = _generated_role_facts(grid)
    if facts is None:
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "target_slot": facts["target_slot"],
        "target_size_rank": facts["target_size_rank"],
        "decoy_color_relation": facts["decoy_color_relation"],
        "decoy_marker_count": facts["decoy_marker_count"],
        "target_color": facts["target_color"],
    }


def strict_canonical_like(grid: Any) -> list[str]:
    """Linked canonical manifold: exact roles, canonical dimensions, four colors."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    info = _analyze_scene(grid)
    frames = info["frames"]
    if len(frames) != 3 or sorted(frame["marker_count"] for frame in frames) != [0, 1, 2]:
        reasons.append("canonical scenes have exactly three frames with marker counts [0, 1, 2]")
        return reasons
    target = info["target"]
    decoy = next(frame for frame in frames if frame["marker_count"] == 2)
    dimensions = (len(grid), len(grid[0]))
    if dimensions not in _CANONICAL_DIMENSION_SET:
        reasons.append(f"dimensions {dimensions!r} are outside the five canonical profiles")
    palette = {value for row in grid for value in row}
    if len(palette) != 4:
        reasons.append(f"canonical inputs use exactly four colors, found palette {sorted(palette)}")
    target_color = target["marker_cells"][0][2]
    decoy_colors = {cell[2] for cell in decoy["marker_cells"]}
    if target_color in decoy_colors:
        reasons.append("canonical target marker color is distinct from the repeated decoy color")
    if len(decoy_colors) != 1:
        reasons.append("canonical two-marker decoy repeats one color")
    return reasons


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Pure Python mirror for tests; the selected Racket source remains authority."""
    info = _analyze_scene(grid)
    if info.get("errors"):
        raise ValueError("invalid frame lesson: " + "; ".join(info["errors"]))
    target = info["target"]
    color = int(target["marker_cells"][0][2])
    row0, col0, row1, col1 = target["bbox"]
    output = [list(row) for row in grid]
    for row in range(row0 + 1, row1):
        for col in range(col0 + 1, col1):
            if output[row][col] == 0:
                output[row][col] = color
    return output


def _fill_frame_zeros(output: Grid, frame: dict[str, Any], color: int) -> None:
    row0, col0, row1, col1 = frame["bbox"]
    for row in range(row0 + 1, row1):
        for col in range(col0 + 1, col1):
            if output[row][col] == 0:
                output[row][col] = color


def _fill_any_marked_frame(grid: Sequence[Sequence[int]]) -> Grid:
    info = _analyze_scene(grid)
    output = [list(row) for row in grid]
    if info.get("errors"):
        return output
    for frame in info["frames"]:
        if frame["marker_count"]:
            _fill_frame_zeros(output, frame, int(frame["marker_cells"][0][2]))
    return output


def _fill_global_unique_marker_color(grid: Sequence[Sequence[int]]) -> Grid:
    info = _analyze_scene(grid)
    output = [list(row) for row in grid]
    if info.get("errors"):
        return output
    counts = Counter(
        cell[2]
        for frame in info["frames"]
        for cell in frame["marker_cells"]
    )
    unique_colors = {color for color, count in counts.items() if count == 1}
    candidates = [
        (frame, cell[2])
        for frame in info["frames"]
        for cell in frame["marker_cells"]
        if cell[2] in unique_colors
    ]
    if len(candidates) == 1:
        _fill_frame_zeros(output, candidates[0][0], int(candidates[0][1]))
    return output


def _fill_odd_marker_frames(grid: Sequence[Sequence[int]]) -> Grid:
    """Plausible rival: treat odd marker multiplicity as the selection rule."""
    info = _analyze_scene(grid)
    output = [list(row) for row in grid]
    if info.get("errors"):
        return output
    for frame in info["frames"]:
        if frame["marker_count"] % 2 == 1:
            _fill_frame_zeros(output, frame, int(frame["marker_cells"][0][2]))
    return output


def _fill_largest_marked_frame(grid: Sequence[Sequence[int]]) -> Grid:
    info = _analyze_scene(grid)
    output = [list(row) for row in grid]
    if info.get("errors"):
        return output
    marked = [frame for frame in info["frames"] if frame["marker_count"]]
    if marked:
        frame = max(marked, key=lambda item: item["interior_area"])
        _fill_frame_zeros(output, frame, int(frame["marker_cells"][0][2]))
    return output


def _fill_first_marked_frame(grid: Sequence[Sequence[int]]) -> Grid:
    info = _analyze_scene(grid)
    output = [list(row) for row in grid]
    if info.get("errors"):
        return output
    marked = [frame for frame in info["frames"] if frame["marker_count"]]
    if marked:
        frame = marked[0]
        _fill_frame_zeros(output, frame, int(frame["marker_cells"][0][2]))
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "fill_any_marked_frame": _fill_any_marked_frame,
    "global_unique_marker_color": _fill_global_unique_marker_color,
    "odd_marker_count": _fill_odd_marker_frames,
    "largest_marked_frame": _fill_largest_marked_frame,
    "first_marked_frame": _fill_first_marked_frame,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "global_unique_marker_color": _fill_global_unique_marker_color,
    "odd_marker_count": _fill_odd_marker_frames,
}


def _valid_and_refutes(grid: Any, rival_name: str) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "multi_marker_decoy_refutes_fill_any": lambda grid: _valid_and_refutes(grid, "fill_any_marked_frame"),
    "shared_color_refutes_global_unique": lambda grid: _valid_and_refutes(grid, "global_unique_marker_color"),
    "three_marker_decoy_refutes_odd_count": lambda grid: _valid_and_refutes(grid, "odd_marker_count"),
    "target_not_largest_refutes_size": lambda grid: _valid_and_refutes(grid, "largest_marked_frame"),
    "target_not_first_refutes_position": lambda grid: _valid_and_refutes(grid, "first_marked_frame"),
}
WITNESS_RIVALS = {
    "multi_marker_decoy_refutes_fill_any": ["fill_any_marked_frame"],
    "shared_color_refutes_global_unique": ["global_unique_marker_color"],
    "three_marker_decoy_refutes_odd_count": ["odd_marker_count"],
    "target_not_largest_refutes_size": ["largest_marked_frame"],
    "target_not_first_refutes_position": ["first_marked_frame"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require a complete four-example window that kills every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the canonical rule")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons
