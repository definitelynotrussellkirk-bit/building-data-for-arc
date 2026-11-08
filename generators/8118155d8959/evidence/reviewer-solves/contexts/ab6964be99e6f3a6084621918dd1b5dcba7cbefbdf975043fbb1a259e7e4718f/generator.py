"""Generator for task 8118155d8959 — rank blue objects by cell count.

The input contains exactly three 4-connected blue (1) objects with distinct
cell counts.  Sort those objects by occupied-cell count ascending (canonical
ties are broken by top row, then left column), recolor them 2, 3, and 8, and
preserve every non-blue cell.

A three-example semantic schedule deliberately includes a case where occupied
cell count and bounding-box area disagree.  This is necessary because every
canonical demonstration is also explained by the plausible but wrong rule
"rank the blue objects by bounding-box area".
"""
from __future__ import annotations

import copy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8118155d8959"
TASK_ID = GENERATOR_ID
VERSION = "2.0.1"
RULE_HASH = "ed7a95a7119d"

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A canonical-size zero-background grid contains exactly three blue (1) "
    "4-connected objects whose cell counts are a demonstrated distinct-size "
    "profile. Sort the blue objects by occupied-cell count ascending and "
    "recolor them 2, 3, and 8; preserve all non-blue distractor objects. "
    "Every three-example lesson includes deliberate cell-count versus "
    "bounding-box-area, spatial-order, and shape-lookup conflicts."
)

INVARIANTS = [
    "the grid profile (height, width, palette size) matches a canonical input",
    "exactly three 4-connected blue objects have a canonical distinct-size set",
    "input colors are 0, 1, and one to three preserved colors from 5, 6, 7, 9",
    "every non-blue distractor component has two to four cells",
    "every three consecutive samples refute bbox-area, position, and shape rivals",
]

# Each value is (height, width, number of distinct distractor colors).  The
# resulting (height, width, total palette size) tuples are exactly the five
# profiles observed across canonical train and test inputs.
_SCENE_PROFILE_SPECS: dict[str, tuple[int, int, int]] = {
    "h11_w12_p5": (11, 12, 3),
    "h11_w12_p4": (11, 12, 2),
    "h12_w10_p3": (12, 10, 1),
    "h10_w12_p4": (10, 12, 2),
    "h10_w11_p5": (10, 11, 3),
}
SCENE_PROFILES = tuple(_SCENE_PROFILE_SPECS)
_PROFILE_BY_OBSERVABLE = {
    (height, width, distractor_colors + 2): name
    for name, (height, width, distractor_colors) in _SCENE_PROFILE_SPECS.items()
}

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "difficulty-rotated keyed draw over canonical profiles",
        "valid": "h11_w12_p5|h11_w12_p4|h12_w10_p3|h10_w12_p4|h10_w11_p5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_ALLOWED_INPUT_COLORS = frozenset((0, 1, 5, 6, 7, 9))
_DISTRACTOR_COLORS = (5, 6, 7, 9)
_CANONICAL_BLUE_SIZE_SETS = frozenset(
    ((2, 3, 4), (2, 3, 5), (2, 4, 5), (3, 4, 5))
)
_OUTPUT_COLORS = (2, 3, 8)

# Connected, normalized shapes.  The bbox-conflict cell uses area sequence
# 3, 6, 5 for sizes 3, 4, 5, swapping the final two ranks under bbox area.
_DOMINO = ((0, 0), (0, 1))
_LINE3 = ((0, 0), (0, 1), (0, 2))
_L3 = ((0, 0), (1, 0), (1, 1))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_Z4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_LINE5 = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))
_PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_DISTRACTOR_SHAPES = {
    2: _DOMINO,
    3: _L3,
    4: ((0, 0), (0, 1), (1, 0), (1, 1)),
}

_SEMANTIC_PROFILES = (
    "bbox_area_conflict",
    "position_conflict_small",
    "position_conflict_large",
)
SCHEDULE_PROFILES = _SEMANTIC_PROFILES


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform(
    cells: Iterable[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    raw: list[tuple[int, int]] = []
    for r, c in cells:
        if code == 1:
            raw.append((c, -r))
        elif code == 2:
            raw.append((-r, -c))
        elif code == 3:
            raw.append((-c, r))
        elif code == 4:
            raw.append((r, -c))
        elif code == 5:
            raw.append((-r, c))
        elif code == 6:
            raw.append((c, r))
        elif code == 7:
            raw.append((-c, -r))
        else:
            raw.append((r, c))
    return _normalize(raw)


def _orient(cells: Iterable[tuple[int, int]], rng) -> tuple[tuple[int, int], ...]:
    options = tuple(sorted({_transform(cells, code) for code in range(8)}))
    return rng.choice(options)


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return 1 + max(r for r, _ in cells), 1 + max(c for _, c in cells)


def _paint(
    grid: list[list[int]],
    row: int,
    col: int,
    cells: Iterable[tuple[int, int]],
    color: int,
) -> None:
    for dr, dc in cells:
        rr, cc = row + dr, col + dc
        if grid[rr][cc] != 0:
            raise ValueError(f"placement collision at ({rr}, {cc})")
        grid[rr][cc] = color


def _components_of_color(grid: list[list[int]], color: int) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            records.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "size": len(cells),
                    "bbox": bbox,
                    "bbox_area": (bbox[2] - bbox[0] + 1)
                    * (bbox[3] - bbox[1] + 1),
                }
            )
    return records


def _blue_records(grid: list[list[int]]) -> list[dict[str, Any]]:
    return _components_of_color(grid, 1)


def _canonical_order(records: list[dict[str, Any]]) -> list[int]:
    return sorted(
        range(len(records)),
        key=lambda i: (
            records[i]["size"],
            records[i]["bbox"][0],
            records[i]["bbox"][1],
        ),
    )


def _recolor_by_order(grid: list[list[int]], order: list[int]) -> list[list[int]]:
    records = _blue_records(grid)
    if len(records) != 3 or len(order) != 3:
        raise ValueError("rule domain requires exactly three blue components")
    output = copy.deepcopy(grid)
    for record_index, new_color in zip(order, _OUTPUT_COLORS):
        for row, col in records[record_index]["cells"]:
            output[row][col] = new_color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror; selected Racket source remains output authority."""
    records = _blue_records(grid)
    return _recolor_by_order(grid, _canonical_order(records))


def _rival_bbox_area(grid: list[list[int]]) -> list[list[int]]:
    records = _blue_records(grid)
    order = sorted(
        range(len(records)),
        key=lambda i: (
            records[i]["bbox_area"],
            records[i]["bbox"][0],
            records[i]["bbox"][1],
        ),
    )
    return _recolor_by_order(grid, order)


def _rival_left_to_right(grid: list[list[int]]) -> list[list[int]]:
    records = _blue_records(grid)
    order = sorted(
        range(len(records)),
        key=lambda i: (records[i]["bbox"][1], records[i]["bbox"][0]),
    )
    return _recolor_by_order(grid, order)


def _rival_top_to_bottom(grid: list[list[int]]) -> list[list[int]]:
    records = _blue_records(grid)
    order = sorted(
        range(len(records)),
        key=lambda i: (records[i]["bbox"][0], records[i]["bbox"][1]),
    )
    return _recolor_by_order(grid, order)


def _rival_descending_size(grid: list[list[int]]) -> list[list[int]]:
    records = _blue_records(grid)
    order = sorted(
        range(len(records)),
        key=lambda i: (
            -records[i]["size"],
            records[i]["bbox"][0],
            records[i]["bbox"][1],
        ),
    )
    return _recolor_by_order(grid, order)


def _rival_erase_distractors(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] not in (0, 1):
                output[row][col] = 0
    return output


def _shape_signature(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Canonical morphology signature, invariant to rotations/reflections."""
    return min(_transform(cells, code) for code in range(8))


_MORPHOLOGY_LOOKUP_COLORS = {
    _shape_signature(_DOMINO): 2,
    _shape_signature(_LINE3): 2,
    _shape_signature(_L3): 3,
    _shape_signature(_T4): 3,
    _shape_signature(_Z4): 8,
    _shape_signature(_LINE5): 8,
    _shape_signature(_PLUS5): 8,
}


def _rival_morphology_lookup(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule learned from the pre-2.0.1 shape/color correlation."""
    records = _blue_records(grid)
    if len(records) != 3:
        raise ValueError("rule domain requires exactly three blue components")
    output = copy.deepcopy(grid)
    fallback_by_size = {2: 2, 3: 3, 4: 3, 5: 8}
    for record in records:
        color = _MORPHOLOGY_LOOKUP_COLORS.get(
            _shape_signature(record["cells"]),
            fallback_by_size.get(record["size"], 8),
        )
        for row, col in record["cells"]:
            output[row][col] = color
    return output


def observe_overrides(grid: list[list[int]]) -> dict[str, str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    profile_key = (
        len(grid),
        width,
        len({value for row in grid for value in row}),
    )
    try:
        profile = _PROFILE_BY_OBSERVABLE[profile_key]
    except KeyError as exc:
        raise ValueError(
            f"grid profile {profile_key} is not one of the canonical scene profiles"
        ) from exc
    return {"scene_profile": profile}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar shared by canonical examples and generated inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]

    errors: list[str] = []
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid contains a non-ARC color"]

    palette = {value for row in grid for value in row}
    if not palette <= _ALLOWED_INPUT_COLORS:
        errors.append(
            "input palette must be a subset of {0,1,5,6,7,9}; "
            f"got {sorted(palette)}"
        )
    if 0 not in palette or 1 not in palette:
        errors.append("input must contain background 0 and blue 1")

    try:
        observe_overrides(grid)
    except ValueError as exc:
        errors.append(str(exc))

    blues = _blue_records(grid)
    if len(blues) != 3:
        errors.append(f"expected exactly 3 blue components; found {len(blues)}")
    else:
        sizes = tuple(sorted(record["size"] for record in blues))
        if sizes not in _CANONICAL_BLUE_SIZE_SETS:
            errors.append(
                f"blue size profile {sizes} is not one of "
                f"{sorted(_CANONICAL_BLUE_SIZE_SETS)}"
            )

    distractor_colors = sorted(palette - {0, 1})
    if not 1 <= len(distractor_colors) <= 3:
        errors.append(
            f"expected 1..3 distinct distractor colors; got {distractor_colors}"
        )
    distractor_components = []
    for color in distractor_colors:
        distractor_components.extend(_components_of_color(grid, color))
    if not 1 <= len(distractor_components) <= 3:
        errors.append(
            f"expected 1..3 distractor components; found {len(distractor_components)}"
        )
    bad_sizes = [record["size"] for record in distractor_components if not 2 <= record["size"] <= 4]
    if bad_sizes:
        errors.append(f"distractor component sizes must lie in 2..4; got {bad_sizes}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated family is deliberately the observed canonical grammar."""
    return self_check(grid)


def semantic_observables(grid) -> dict[str, Any]:
    records = _blue_records(grid)
    return {
        "scene_profile": observe_overrides(grid)["scene_profile"],
        "blue_sizes": tuple(sorted(record["size"] for record in records)),
        "blue_bbox_areas": tuple(
            sorted(record["bbox_area"] for record in records)
        ),
        "canonical_order": tuple(_canonical_order(records)),
        "bbox_order": tuple(
            sorted(
                range(len(records)),
                key=lambda i: (
                    records[i]["bbox_area"],
                    records[i]["bbox"][0],
                    records[i]["bbox"][1],
                ),
            )
        ),
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return _SEMANTIC_PROFILES[sample_index % len(_SEMANTIC_PROFILES)]


def _profile_options(difficulty) -> tuple[str, ...]:
    offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 3)
    return SCENE_PROFILES[offset:] + SCENE_PROFILES[:offset]


def _scheduled_blue_specs(sample_index: int, rng):
    mode = sample_index % 3
    if mode == 0:
        # Occupied sizes 3<4<5, but bbox areas 4<5<6.  The middle and largest
        # ranks swap under the strongest canonical-fitting shortcut.  L3 is
        # intentionally the smallest here, rather than a fixed middle-rank cue.
        return [
            (3, _orient(_L3, rng), "top_right"),
            (4, _orient(_T4, rng), "top_left"),
            (5, _LINE5, "bottom"),
        ]
    if mode == 1:
        # Reuse T4 at a different rank and place LINE3 in the middle rank so a
        # morphology-to-color lookup cannot explain a complete lesson.
        return [
            (2, _orient(_DOMINO, rng), "bottom"),
            (3, _orient(_LINE3, rng), "top_right"),
            (4, _orient(_T4, rng), "top_left"),
        ]
    return [
        (2, _orient(_DOMINO, rng), "top_left"),
        (4, _orient(_Z4, rng), "bottom"),
        (5, _PLUS5, "top_right"),
    ]


def _slot_origin(slot: str, cells, height: int, width: int, rng) -> tuple[int, int]:
    shape_h, shape_w = _dims(cells)
    if slot == "top_left":
        return rng.randint(0, 1), rng.randint(0, 1)
    if slot == "top_right":
        return rng.randint(0, 1), width - shape_w - rng.randint(0, 1)
    if slot == "bottom":
        row = height - shape_h - rng.randint(0, 1)
        center = (width - shape_w) // 2
        col = min(max(0, center + rng.choice((-1, 0, 1))), width - shape_w)
        return row, col
    raise ValueError(f"unknown placement slot {slot!r}")


def _place_distractors(
    grid: list[list[int]],
    colors: list[int],
    sample_index: int,
    rng,
) -> None:
    height, width = len(grid), len(grid[0])
    size_cycle = (2, 3, 4)
    targets = (0, (width - 2) // 2, width - 2)
    for index, color in enumerate(colors):
        size = size_cycle[(sample_index + index) % len(size_cycle)]
        cells = _orient(_DISTRACTOR_SHAPES[size], rng)
        shape_h, shape_w = _dims(cells)
        target_row = (height - shape_h) // 2
        target_col = min(targets[index], width - shape_w)
        candidates = [
            (row, col)
            for row in range(height - shape_h + 1)
            for col in range(width - shape_w + 1)
            if all(grid[row + dr][col + dc] == 0 for dr, dc in cells)
        ]
        if not candidates:
            raise ValueError("no legal distractor placement")
        # Stable random tie-breaking among equally near locations avoids a
        # fixed distractor template while keeping the canonical middle band.
        decorated = [
            (
                abs(row - target_row) + abs(col - target_col),
                rng.random(),
                row,
                col,
            )
            for row, col in candidates
        ]
        _, _, row, col = min(decorated)
        _paint(grid, row, col, cells, color)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_profile = ctx.draw_choice(
        "scene_profile", _profile_options(difficulty)
    )
    height, width, n_distractor_colors = _SCENE_PROFILE_SPECS[scene_profile]
    rng = ctx.draw_rng(f"scene:{difficulty!r}")

    grid = full_grid(height, width, 0)
    for _, cells, slot in _scheduled_blue_specs(sample_index, rng):
        row, col = _slot_origin(slot, cells, height, width, rng)
        _paint(grid, row, col, cells, 1)

    distractor_colors = rng.sample(_DISTRACTOR_COLORS, n_distractor_colors)
    _place_distractors(grid, distractor_colors, sample_index, rng)

    problems = self_check(grid)
    if problems:
        raise ValueError("internal generation invariant failed: " + "; ".join(problems))
    return grid


# ---------------------------------------------------------------------------
# Executable semantic contract
# ---------------------------------------------------------------------------


def _bbox_order_differs(grid) -> bool:
    records = _blue_records(grid)
    bbox_order = sorted(
        range(len(records)),
        key=lambda i: (
            records[i]["bbox_area"],
            records[i]["bbox"][0],
            records[i]["bbox"][1],
        ),
    )
    return bbox_order != _canonical_order(records)


def _left_order_differs(grid) -> bool:
    records = _blue_records(grid)
    left_order = sorted(
        range(len(records)),
        key=lambda i: (records[i]["bbox"][1], records[i]["bbox"][0]),
    )
    return left_order != _canonical_order(records)


def _top_order_differs(grid) -> bool:
    records = _blue_records(grid)
    top_order = sorted(
        range(len(records)),
        key=lambda i: (records[i]["bbox"][0], records[i]["bbox"][1]),
    )
    return top_order != _canonical_order(records)


def _has_preserved_distractors(grid) -> bool:
    return any(value not in (0, 1) for row in grid for value in row)


def _ascending_size_direction_visible(grid) -> bool:
    return _rival_descending_size(grid) != rule_mirror(grid)


def _morphology_lookup_differs(grid) -> bool:
    return _rival_morphology_lookup(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "bbox_area": _rival_bbox_area,
    "left_to_right": _rival_left_to_right,
    "top_to_bottom": _rival_top_to_bottom,
    "descending_size": _rival_descending_size,
    "erase_distractors": _rival_erase_distractors,
    "morphology_lookup": _rival_morphology_lookup,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"bbox_area": _rival_bbox_area}

SEMANTIC_WITNESSES = {
    "cell_count_not_bbox_area": _bbox_order_differs,
    "size_not_left_to_right": _left_order_differs,
    "size_not_top_to_bottom": _top_order_differs,
    "ascending_size_direction": _ascending_size_direction_visible,
    "preserve_nonblue_cells": _has_preserved_distractors,
    "rank_not_shape_identity": _morphology_lookup_differs,
}
WITNESS_RIVALS = {
    "cell_count_not_bbox_area": ["bbox_area"],
    "size_not_left_to_right": ["left_to_right"],
    "size_not_top_to_bottom": ["top_to_bottom"],
    "ascending_size_direction": ["descending_size"],
    "preserve_nonblue_cells": ["erase_distractors"],
    "rank_not_shape_identity": ["morphology_lookup"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared plausible rival survives all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is outside the rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(
                f"demo {index} output disagrees with the blue-size ranking rule"
            )

    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query input is outside the rule domain: {exc}")
        return reasons
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output disagrees with the blue-size ranking rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if not all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        ):
            continue
        if competitor(query["input"]) != query_answer:
            reasons.append(
                f"rival '{name}' fits every demonstration but changes the query answer"
            )
    return reasons
