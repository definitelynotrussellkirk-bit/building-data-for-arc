"""Generator for ``Fill Rectangles From Four Corners`` (42fb6b33deea).

The executable authority is count-gated: each non-background color with
exactly four cells is painted across its bounding box on a fresh zero canvas.
The teaching distribution includes both ordinary four-corner rectangles and
exactly-four non-corner witnesses, plus three- and five-cell count distractors.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "42fb6b33deea"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"  # bounded-work layouts plus count-gated teaching witnesses
RULE_HASH = "b800fc792026"  # normalized canonical program_solution

SUMMARY = (
    "A zero-background grid contains one to three target colors with exactly "
    "four cells. Most targets mark the four corners of a rectangle; scheduled "
    "count witnesses replace one corner by another cell inside the same box. "
    "Optional distractors have three or five cells. Fill the bounding box of "
    "every EXACTLY-four color on a fresh zero canvas and erase all others."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "one to three target colors have exactly four cells and a nontrivial bounding box",
    "count-witness samples replace one corner of the first target without changing its bounding box",
    "the corner-only lesson role uses an exact canonical grid/palette profile in every difficulty band",
    "target bounding boxes do not overlap, so rectangle paints are order-independent",
    "zero to two distractor colors have three or five cells and are ignored by the rule",
    "every three-example lesson contains two exact-four non-corner witnesses and one ordinary corner example",
]

TARGET_STYLES = ("corners", "count_witness")
PALETTE_KINDS = ("default", "warm", "cool", "varied")
_CANONICAL_THREE_COLOR_DIMS = ((8, 11), (9, 10), (9, 12), (10, 10))
_INTEGER_AXES = ("grid_h", "grid_w", "n_target_colors", "n_distractor_colors")
_LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = (
    "count_witness_no_distractor",
    "corners_below_four",
    "count_witness_below_and_above_four",
)
_PALETTE_ORDERS = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 8, 9, 6, 3, 1, 5, 7),
    "cool": (1, 3, 5, 6, 7, 2, 4, 8, 9),
    "varied": (9, 5, 2, 7, 3, 8, 1, 6, 4),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor on role 1; otherwise difficulty-skewed 5..16",
        "valid": "5..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor on role 1; otherwise difficulty-skewed 7..18",
        "valid": "7..18",
    },
    "n_target_colors": {
        "type": "int",
        "default": "three-step lesson schedule: 2,1,2-or-3",
        "valid": "1..3",
    },
    "n_distractor_colors": {
        "type": "int",
        "default": "three-step lesson schedule: 0,1,2",
        "valid": "0..2",
    },
    "target_style": {
        "type": "str",
        "default": "three-step lesson schedule: count_witness,corners,count_witness",
        "valid": "|".join(TARGET_STYLES),
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed choice",
        "valid": "|".join(PALETTE_KINDS),
    },
}

BBox = tuple[int, int, int, int]
Cell = tuple[int, int]


def _bbox(cells: Iterable[Cell]) -> BBox:
    cells = list(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_cells(box: BBox) -> set[Cell]:
    top, left, bottom, right = box
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }


def _corners(box: BBox) -> tuple[Cell, Cell, Cell, Cell]:
    top, left, bottom, right = box
    return (
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    )


def _target_cells(box: BBox, style: str, rng) -> set[Cell]:
    """Return four target cells while preserving ``box`` as their bbox."""
    corners = set(_corners(box))
    if style == "corners":
        return corners
    if style != "count_witness":
        raise ValueError(f"unsupported target style: {style}")

    noncorners = list(_bbox_cells(box) - corners)
    if not noncorners:
        raise ValueError(f"cannot build a count witness in trivial bbox {box}")
    removed = rng.choice(tuple(corners))
    replacement = rng.choice(noncorners)
    selected = (corners - {removed}) | {replacement}
    if _bbox(selected) != box:
        raise RuntimeError("count-witness construction changed the target bbox")
    return selected


def _bbox_overlap(left: BBox, right: BBox) -> bool:
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _validate_generate_scalars(sample_index, overrides) -> None:
    """Reject unknown or coercible controls so every advertised axis is exact."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    for axis in _INTEGER_AXES:
        if axis in overrides and type(overrides[axis]) is not int:
            raise TypeError(f"{axis} must be an integer")


def _canonical_anchor_dims(seed: int, sample_index: int) -> tuple[int, int]:
    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|canonical-profile", VERSION)
    return rng.choice(_CANONICAL_THREE_COLOR_DIMS)


def _lesson_defaults(seed: int, sample_index: int) -> tuple[int, int, str]:
    """Return a cyclic role that identifies the literal count-gated rule.

    Any three consecutive indices contain all distractor counts and two
    exact-four non-corner witnesses.  Consequently, even after rotating any
    one of four consecutive examples into the query, at least one witness
    remains among the three demonstrations.
    """
    role = sample_index % _LESSON_SCHEDULE_PERIOD
    if role == 0:
        return 2, 0, "count_witness"
    if role == 1:
        return 1, 1, "corners"
    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|lesson-target-count", VERSION)
    return 2 + rng.randrange(2), 2, "count_witness"


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the three deterministic lesson roles to the semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % _LESSON_SCHEDULE_PERIOD]


def _bbox_area(box: BBox) -> int:
    top, left, bottom, right = box
    return (bottom - top + 1) * (right - left + 1)


@lru_cache(maxsize=None)
def _ranked_shapes(
    height: int,
    width: int,
    min_area: int,
    target_area: int,
) -> tuple[tuple[int, int], ...]:
    """Return feasible rectangle shapes, ranked once instead of per draw."""
    shapes = [
        (rect_h, rect_w)
        for rect_h in range(2, min(height, 7) + 1)
        for rect_w in range(2, min(width, 8) + 1)
        if rect_h * rect_w >= min_area
    ]
    shapes.sort(
        key=lambda shape: (
            abs(shape[0] * shape[1] - target_area),
            abs(shape[0] - shape[1]),
            shape,
        )
    )
    return tuple(shapes)


def _partition_spans(length: int, count: int, rng) -> list[tuple[int, int]]:
    """Split an axis into randomized contiguous slabs."""
    base, extra = divmod(length, count)
    sizes = [base + (index < extra) for index in range(count)]
    rng.shuffle(sizes)  # At most three entries: bounded random work.
    spans: list[tuple[int, int]] = []
    start = 0
    for size in sizes:
        spans.append((start, start + size - 1))
        start += size
    return spans


def _orientation_is_feasible(
    height: int,
    width: int,
    count: int,
    min_area: int,
    *,
    vertical: bool,
) -> bool:
    slab_h = height if vertical else height // count
    slab_w = width // count if vertical else width
    return (
        slab_h >= 2
        and slab_w >= 2
        and min(slab_h, 7) * min(slab_w, 8) >= min_area
    )


def _choose_target_boxes(
    height: int,
    width: int,
    count: int,
    rng,
) -> list[BBox]:
    total_cells = height * width
    min_area = max(6, (8 * total_cells + 999) // 100 // count + 4)
    target_area = max(min_area, round(0.13 * total_cells / count) + 4)
    orientations = [
        vertical
        for vertical in (True, False)
        if _orientation_is_feasible(
            height,
            width,
            count,
            min_area,
            vertical=vertical,
        )
    ]
    if not orientations:
        raise ValueError(
            f"cannot place {count} non-overlapping nontrivial rectangles "
            f"inside {height}x{width}"
        )
    vertical = rng.choice(orientations)
    spans = _partition_spans(width if vertical else height, count, rng)
    boxes: list[BBox] = []
    for start, end in spans:
        zone_h = height if vertical else end - start + 1
        zone_w = end - start + 1 if vertical else width
        shapes = _ranked_shapes(zone_h, zone_w, min_area, target_area)
        if not shapes:
            raise ValueError(
                f"cannot place a target rectangle inside {zone_h}x{zone_w} slab"
            )
        # Sampling among the closest few areas retains shape diversity without
        # shuffling thousands of positioned boxes on every override draw.
        rect_h, rect_w = rng.choice(shapes[: min(8, len(shapes))])
        local_top = rng.randrange(zone_h - rect_h + 1)
        local_left = rng.randrange(zone_w - rect_w + 1)
        top = local_top + (0 if vertical else start)
        left = local_left + (start if vertical else 0)
        boxes.append((top, left, top + rect_h - 1, left + rect_w - 1))
    return boxes


def _distractor_cells(
    box: BBox,
    cell_count: int,
    occupied: set[Cell],
    rng,
) -> set[Cell] | None:
    corners = tuple(_corners(box))
    if cell_count == 3:
        omissions = list(range(len(corners)))
        rng.shuffle(omissions)
        for omitted in omissions:
            selected = {cell for index, cell in enumerate(corners) if index != omitted}
            if not selected & occupied:
                return selected
        return None

    if set(corners) & occupied:
        return None
    top, left, bottom, right = box
    interior = [
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (row, col) not in corners and (row, col) not in occupied
    ]
    if not interior:
        return None
    return set(corners) | {rng.choice(interior)}


def _place_distractor(
    grid: list[list[int]],
    color: int,
    cell_count: int,
    occupied: set[Cell],
    rng,
) -> None:
    height, width = len(grid), len(grid[0])
    if cell_count not in (3, 5):
        raise ValueError(f"unsupported distractor cell count: {cell_count}")

    shapes = _ranked_shapes(height, width, 6, 6)
    # Sparse random probes handle ordinary cases in constant work.
    for _ in range(96):
        rect_h, rect_w = rng.choice(shapes)
        top = rng.randrange(height - rect_h + 1)
        left = rng.randrange(width - rect_w + 1)
        box = (top, left, top + rect_h - 1, left + rect_w - 1)
        selected = _distractor_cells(box, cell_count, occupied, rng)
        if selected is None:
            continue
        for row, col in selected:
            grid[row][col] = color
        occupied.update(selected)
        return

    # Deterministic exhaustive fallback preserves exact boundary overrides.
    for rect_h, rect_w in shapes:
        for top in range(height - rect_h + 1):
            for left in range(width - rect_w + 1):
                box = (top, left, top + rect_h - 1, left + rect_w - 1)
                selected = _distractor_cells(box, cell_count, occupied, rng)
                if selected is None:
                    continue
                for row, col in selected:
                    grid[row][col] = color
                occupied.update(selected)
                return

    # This can only be reached in very dense explicit boundary combinations.
    # Reject rather than silently changing the requested distractor count.
    raise ValueError(
        f"cannot place a {cell_count}-cell distractor inside {height}x{width}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_scalars(sample_index, overrides)
    default_targets, default_distractors, default_style = _lesson_defaults(
        seed, sample_index
    )
    effective_overrides = dict(overrides)
    effective_overrides.setdefault("n_target_colors", default_targets)
    effective_overrides.setdefault("n_distractor_colors", default_distractors)
    effective_overrides.setdefault("target_style", default_style)
    if sample_index % _LESSON_SCHEDULE_PERIOD == 1:
        anchor_h, anchor_w = _canonical_anchor_dims(seed, sample_index)
        effective_overrides.setdefault("grid_h", anchor_h)
        effective_overrides.setdefault("grid_w", anchor_w)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int_diff("grid_h", 5, 16)
    width = ctx.draw_int_diff("grid_w", 7, 18)
    n_targets = ctx.draw_int("n_target_colors", 1, 3)
    n_distractors = ctx.draw_int("n_distractor_colors", 0, 2)
    target_style = ctx.draw_choice("target_style", TARGET_STYLES)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    if n_targets + n_distractors > 9:
        raise ValueError("requested more non-background colors than available")

    layout_rng = ctx.draw_rng("layout")
    target_boxes = _choose_target_boxes(height, width, n_targets, layout_rng)

    palette = list(_PALETTE_ORDERS[palette_kind])
    # Keep palette identity independent from layout-search implementation.
    palette_rng = ctx.draw_rng("palette-rotation")
    rotate = palette_rng.randrange(len(palette))
    palette = palette[rotate:] + palette[:rotate]
    colors = palette[: n_targets + n_distractors]

    grid = full_grid(height, width, 0)
    occupied: set[Cell] = set()
    for index, (color, box) in enumerate(zip(colors[:n_targets], target_boxes)):
        style = target_style if index == 0 else "corners"
        for row, col in _target_cells(box, style, layout_rng):
            grid[row][col] = color
            occupied.add((row, col))

    distractor_counts = (3, 5)
    for index, color in enumerate(colors[n_targets:]):
        _place_distractor(
            grid,
            color,
            distractor_counts[index % len(distractor_counts)],
            occupied,
            layout_rng,
        )
    return grid


def _color_cell_sets(grid: list[list[int]]) -> dict[int, list[Cell]]:
    by_color: dict[int, list[Cell]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                by_color[value].append((row, col))
    return dict(by_color)


def _analysis(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "targets": [], "distractors": []}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must have non-empty rows"], "targets": [], "distractors": []}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "targets": [], "distractors": []}
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC limits: {len(grid)}x{width}")
    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("grid contains a non-integer color outside 0..9")
                return {"errors": errors, "targets": [], "distractors": []}

    targets: list[tuple[int, BBox]] = []
    count_witnesses: list[int] = []
    distractors: list[tuple[int, int, BBox]] = []
    for color, cells in sorted(_color_cell_sets(grid).items()):
        box = _bbox(cells)
        if len(cells) == 4:
            if len(_bbox_cells(box)) <= 4:
                errors.append(
                    f"color {color} has a trivial bbox that adds no filled cells"
                )
            if set(cells) != set(_corners(box)):
                count_witnesses.append(color)
            targets.append((color, box))
        elif len(cells) == 3:
            if not set(cells).issubset(set(_corners(box))):
                errors.append(
                    f"three-cell distractor color {color} is not an incomplete rectangle"
                )
            distractors.append((color, 3, box))
        elif len(cells) == 5:
            corners = set(_corners(box))
            if not corners.issubset(set(cells)) or len(set(cells) - corners) != 1:
                errors.append(
                    f"five-cell distractor color {color} must be four bbox corners plus one interior cell"
                )
            distractors.append((color, 5, box))
        else:
            errors.append(
                f"color {color} has {len(cells)} cells; expected target count 4 or distractor count 3/5"
            )

    if not targets:
        errors.append("expected at least one four-corner target rectangle")
    if len(targets) > 3:
        errors.append(f"expected at most three target colors, got {len(targets)}")
    if len(distractors) > 2:
        errors.append(f"expected at most two distractor colors, got {len(distractors)}")
    if len(count_witnesses) > 1:
        errors.append(
            "expected at most one exact-four non-corner witness, got "
            f"{len(count_witnesses)}"
        )
    for index, (left_color, left_box) in enumerate(targets):
        for right_color, right_box in targets[index + 1 :]:
            if _bbox_overlap(left_box, right_box):
                errors.append(
                    "target bboxes overlap and make paint order observable: "
                    f"{left_color} {left_box} vs {right_color} {right_box}"
                )
    return {
        "errors": errors,
        "targets": targets,
        "count_witnesses": count_witnesses,
        "distractors": distractors,
        "height": len(grid),
        "width": width,
    }


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "n_target_colors": len(analysis["targets"]),
        "n_distractor_colors": len(analysis["distractors"]),
        "target_style": (
            "count_witness" if analysis["count_witnesses"] else "corners"
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analysis(grid)["errors"])


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket authority for tests/audits."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for color, cells in sorted(_color_cell_sets(grid).items()):
        if len(cells) != 4:
            continue
        top, left, bottom, right = _bbox(cells)
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                output[row][col] = color
    return output

# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------


def _four_actual_corners_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: fill only literal four-corner rectangles."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for color, cells in sorted(_color_cell_sets(grid).items()):
        if len(cells) != 4:
            continue
        box = _bbox(cells)
        if set(cells) != set(_corners(box)):
            continue
        for row, col in _bbox_cells(box):
            output[row][col] = color
    return output


def _exact_four_noncorner(grid: list[list[int]]) -> bool:
    """Whether a color has four cells that are not all bbox corners."""
    return any(
        len(cells) == 4 and set(cells) != set(_corners(_bbox(cells)))
        for cells in _color_cell_sets(grid).values()
    )


SEMANTIC_RIVALS = {
    "four_actual_corners_only": _four_actual_corners_only,
}
SEMANTIC_WITNESSES = {
    "exact_four_noncorner": _exact_four_noncorner,
}
WITNESS_RIVALS = {
    "exact_four_noncorner": ["four_actual_corners_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
strict_canonical_like = self_check


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid labels and demonstrations that eliminate each rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the lawful count-gated grammar")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output is not the authoritative count-gated fill")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the lawful count-gated grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the authoritative count-gated fill")
            continue
        valid_demos.append(demo)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons

