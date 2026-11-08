"""Native parametric family for 70abd9105769.

``mode=canonical`` is the exact selected canonical square-to-center rule.
``mode=majority_frame`` is a real two-stage rule:

A. Reduce every filled odd-sized square to its center cell, preserving color.
B. Recount colors on that intermediate, select the unique object-majority color,
   and draw a color-9 perimeter around the bounding box of its centers while
   preserving all center cells.

The setting-neutral sampler crosses object frequency against source pixel
frequency: the intended color always has more square objects, while a different
color has more raw pixels because its fewer squares are larger.  It also keeps
non-target centers outside the target frame and varies target color, geometry,
size profile, placement, boundaries, and nuisance ranks.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "70abd9105769"
DEFAULT = {"mode": "canonical"}
PARAMETERS = {"mode": ["canonical", "majority_frame"]}
SETTINGS = [{"mode": value} for value in PARAMETERS["mode"]]
CANONICAL_SHA256 = "82b6dc62b353893c6c12921c03c8306c1a99a3c4709a05a4ac9d8d3e9d5c0bcf"

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes

_DEMO_SHAPES = ((20, 24), (21, 25), (22, 26), (23, 27), (24, 28), (25, 29))
_QUERY_SHAPES = ((20, 24), (24, 28), (28, 30), (30, 30))
_DEMO_PROFILES = ("demo_a", "demo_b", "demo_c", "demo_d", "demo_e", "demo_f")
_QUERY_PROFILES = ("query_a", "query_b", "query_c", "stress")

# Target slots avoid all four corners and one complete outer column.  Therefore
# the intended target-center bbox differs from the bbox of all centers even
# after horizontal/vertical flips.  Corner slots are always nuisance objects.
_PROFILE_LAYOUTS = {
    "demo_a": {"target": (1, 6, 9), "decoy": (2, 7), "extra": (0, 3, 8, 11)},
    "demo_b": {"target": (1, 4, 6, 10), "decoy": (2, 5, 7), "extra": (0, 3, 8, 11)},
    "demo_c": {"target": (2, 5, 6, 9), "decoy": (3, 7), "extra": (0, 4, 11)},
    "demo_d": {"target": (1, 2, 5, 6, 10), "decoy": (3, 4, 7, 11), "extra": (0, 8)},
    "demo_e": {"target": (2, 4, 6, 9), "decoy": (3, 7, 11), "extra": (0, 5, 8)},
    "demo_f": {"target": (1, 4, 5, 9, 10), "decoy": (3, 7, 11), "extra": (0, 6, 8)},
    "query_a": {"target": (1, 5, 6, 10), "decoy": (3, 7, 11), "extra": (0, 4, 8)},
    "query_b": {"target": (1, 2, 5, 6, 10), "decoy": (3, 4, 7, 11), "extra": (0, 8)},
    "query_c": {"target": (2, 4, 6, 9), "decoy": (3, 7, 11), "extra": (0, 5, 8)},
    "stress": {"target": (1, 2, 5, 6, 10), "decoy": (3, 4, 7, 11), "extra": (0, 8, 9)},
}
_PROFILE_INDEX = {name: index for index, name in enumerate((*_DEMO_PROFILES, *_QUERY_PROFILES))}


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}; bool is forbidden")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"mode"}:
        raise ValueError("settings must name exactly mode")
    mode = value["mode"]
    if type(mode) is not str or mode not in PARAMETERS["mode"]:
        raise ValueError("mode must be 'canonical' or 'majority_frame'")
    return {"mode": mode}


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


def _read_rule(name: str) -> str:
    text = (HERE / name).read_text(encoding="utf-8")
    return text[:-1] if text.endswith("\n") else text


def canonical_source() -> str:
    source = _read_rule("canonical.rkt")
    if hashlib.sha256(source.encode()).hexdigest() != CANONICAL_SHA256:
        raise ValueError("canonical.rkt drifted from selected authority")
    return source


def program(settings: Any) -> str:
    mode = _settings(settings)["mode"]
    return canonical_source() if mode == "canonical" else _read_rule("majority_frame.rkt")


def skip_stage_a_program() -> str:
    return _read_rule("skip_stage_a.rkt")


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    return _digest(_grid(grid))


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|majority-frame-v1|{seed}|{domain}|{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    value = _grid(grid)
    height, width = len(value), len(value[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(height):
        for c in range(width):
            if value[r][c] == 0 or (r, c) in seen:
                continue
            color = value[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and value[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
            side_h, side_w = r2 - r1 + 1, c2 - c1 + 1
            expected = {(rr, cc) for rr in range(r1, r2 + 1) for cc in range(c1, c2 + 1)}
            if side_h != side_w or side_h < 3 or side_h % 2 == 0 or set(cells) != expected:
                raise ValueError("every nonzero component must be a filled odd-sized square")
            result.append(
                {
                    "color": color,
                    "cells": sorted(cells),
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "side": side_h,
                    "center": (r1 + side_h // 2, c1 + side_w // 2),
                }
            )
    if not result:
        raise ValueError("scene must contain at least one square")
    return sorted(result, key=lambda obj: (obj["r1"], obj["c1"], obj["color"]))


def stage_a_grid(grid: Any) -> list[list[int]]:
    value = _grid(grid)
    out = [[0 for _ in row] for row in value]
    for obj in _components(value):
        r, c = obj["center"]
        out[r][c] = obj["color"]
    return out


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = list(cells)
    if not points:
        raise ValueError("cannot take bounding box of no cells")
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    return min(rows), min(cols), max(rows), max(cols)


def _nonzero_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    value = _grid(grid)
    return [(r, c) for r, row in enumerate(value) for c, cell in enumerate(row) if cell]


def _cells_of_color(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    value = _grid(grid)
    return [(r, c) for r, row in enumerate(value) for c, cell in enumerate(row) if cell == color]


def _unique_majority(counts: Counter[int] | dict[int, int]) -> int:
    if not counts:
        raise ValueError("no nonzero colors")
    maximum = max(counts.values())
    winners = sorted(color for color, count in counts.items() if count == maximum)
    if len(winners) != 1:
        raise ValueError(f"majority color is tied: {winners}")
    return winners[0]


def frame_positions(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    r1, c1, r2, c2 = _bbox(cells)
    return [
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    ]


def frame_cells(stage: Any, color: int) -> list[tuple[int, int]]:
    value = _grid(stage)
    cells = _cells_of_color(value, color)
    return [(r, c) for r, c in frame_positions(cells) if value[r][c] == 0]


def _paint_zero_cells(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    out = [list(row) for row in _grid(grid)]
    for r, c in cells:
        if out[r][c] == 0:
            out[r][c] = color
    return out


def _paint_all_cells(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    out = [list(row) for row in _grid(grid)]
    for r, c in cells:
        out[r][c] = color
    return out


def _majority_frame_transform(grid: list[list[int]]) -> list[list[int]]:
    stage = stage_a_grid(grid)
    counts = Counter(cell for row in stage for cell in row if cell)
    target = _unique_majority(counts)
    return _paint_zero_cells(stage, frame_positions(_cells_of_color(stage, target)), 9)


def skip_stage_a_transform(grid: Any) -> list[list[int]]:
    value = _grid(grid)
    counts = Counter(cell for row in value for cell in row if cell)
    target = _unique_majority(counts)
    return _paint_zero_cells(value, frame_positions(_cells_of_color(value, target)), 9)


def transform(grid: Any, settings: Any) -> list[list[int]]:
    value = _grid(grid)
    mode = _settings(settings)["mode"]
    return stage_a_grid(value) if mode == "canonical" else _majority_frame_transform(value)


def changed_cells(before: Any, after: Any, *, old: int, new: int) -> int:
    a, b = _grid(before), _grid(after)
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError("grids must have equal dimensions")
    return sum(
        a[r][c] == old and b[r][c] == new
        for r in range(len(a))
        for c in range(len(a[0]))
    )


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    if height < 20 or width < 24:
        raise ValueError("parametric scenes require at least 20x24")
    rows, cols, gap = 3, 4, 1
    usable_h = height - gap * (rows - 1)
    usable_w = width - gap * (cols - 1)
    heights = [usable_h // rows + int(i < usable_h % rows) for i in range(rows)]
    widths = [usable_w // cols + int(i < usable_w % cols) for i in range(cols)]
    r_starts, c_starts = [], []
    cursor = 0
    for size in heights:
        r_starts.append(cursor)
        cursor += size + gap
    cursor = 0
    for size in widths:
        c_starts.append(cursor)
        cursor += size + gap
    return [
        (r_starts[r], c_starts[c], heights[r], widths[c])
        for r in range(rows)
        for c in range(cols)
    ]


def _map_slot(index: int, orientation: int) -> int:
    row, col = divmod(index, 4)
    if orientation & 1:
        col = 3 - col
    if orientation & 2:
        row = 2 - row
    return row * 4 + col


def _placement_offset(
    slot_index: int,
    slot_h: int,
    slot_w: int,
    size: int,
    rng: random.Random,
    *,
    stress: bool,
) -> tuple[int, int]:
    row, col = divmod(slot_index, 4)
    if stress:
        dr = 0 if row == 0 else slot_h - size if row == 2 else (slot_h - size) // 2
        dc = 0 if col == 0 else slot_w - size if col == 3 else (slot_w - size) // 2
        return dr, dc
    # Outer-row/column slots touch the corresponding canvas boundary.  Because
    # target objects never occupy corner slots, this crosses target role against
    # top-left/bottom-right source position by construction rather than chance.
    row_options = (0, (slot_h - size) // 2, slot_h - size)
    col_options = (0, (slot_w - size) // 2, slot_w - size)
    dr = 0 if row == 0 else slot_h - size if row == 2 else rng.choice(row_options)
    dc = 0 if col == 0 else slot_w - size if col == 3 else rng.choice(col_options)
    return dr, dc


def _place_square(
    grid: list[list[int]],
    slot: tuple[int, int, int, int],
    slot_index: int,
    size: int,
    color: int,
    rng: random.Random,
    *,
    stress: bool,
) -> tuple[int, int]:
    r0, c0, slot_h, slot_w = slot
    if size > slot_h or size > slot_w:
        raise ValueError(f"{size}x{size} square does not fit slot {slot_index}")
    dr, dc = _placement_offset(slot_index, slot_h, slot_w, size, rng, stress=stress)
    top, left = r0 + dr, c0 + dc
    for r in range(top, top + size):
        for c in range(left, left + size):
            if grid[r][c] != 0:
                raise ValueError("slot collision")
            grid[r][c] = color
    return top + size // 2, left + size // 2


def _role_colors(seed: int, profile: str) -> tuple[int, int, tuple[int, ...]]:
    index = _PROFILE_INDEX[profile]
    target = 2 + ((seed + 2 * index) % 5)
    decoy = 2 + ((seed + 2 * index + 1) % 5)
    if decoy == target:
        raise AssertionError("role colors must differ")
    return target, decoy, (1, 7, 8)


def build_scene(seed: int, index: int, height: int, width: int, *, profile: str) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(index, 0, 2**31 - 1, "index")
    _integer(height, 20, 30, "height")
    _integer(width, 24, 30, "width")
    if profile not in _PROFILE_LAYOUTS:
        raise ValueError(f"unknown profile {profile!r}")
    layout = _PROFILE_LAYOUTS[profile]
    rng = _rng(seed, f"scene:{profile}", index)
    orientation = rng.randrange(4)
    slots = _slots(height, width)
    target_color, decoy_color, extra_colors = _role_colors(seed, profile)
    stress = profile == "stress"
    grid = [[0] * width for _ in range(height)]

    target_slots = [_map_slot(slot, orientation) for slot in layout["target"]]
    decoy_slots = [_map_slot(slot, orientation) for slot in layout["decoy"]]
    extra_slots = [_map_slot(slot, orientation) for slot in layout["extra"]]
    if len(set((*target_slots, *decoy_slots, *extra_slots))) != (
        len(target_slots) + len(decoy_slots) + len(extra_slots)
    ):
        raise AssertionError("profile slots overlap")

    # Prefer one or two large target squares for shape variation, but cap the
    # count so the fewer all-5x5 decoys remain the unique raw-pixel majority.
    target_fives = 0 if profile in {"demo_a", "demo_b"} else (2 if len(target_slots) >= 5 else 1)
    while target_fives and 9 * len(target_slots) + 16 * target_fives >= 25 * len(decoy_slots):
        target_fives -= 1
    target_order = list(range(len(target_slots)))
    rng.shuffle(target_order)
    target_sizes = [3] * len(target_slots)
    for position in target_order[:target_fives]:
        target_sizes[position] = 5

    centers: dict[str, list[tuple[int, int]]] = {"target": [], "decoy": [], "extra": []}
    for slot_index, size in zip(target_slots, target_sizes):
        centers["target"].append(
            _place_square(
                grid,
                slots[slot_index],
                slot_index,
                size,
                target_color,
                rng,
                stress=stress,
            )
        )
    for slot_index in decoy_slots:
        centers["decoy"].append(
            _place_square(
                grid,
                slots[slot_index],
                slot_index,
                5,
                decoy_color,
                rng,
                stress=stress,
            )
        )
    for position, slot_index in enumerate(extra_slots):
        color = extra_colors[position % len(extra_colors)]
        centers["extra"].append(
            _place_square(
                grid,
                slots[slot_index],
                slot_index,
                3,
                color,
                rng,
                stress=stress,
            )
        )

    facts = scene_facts(grid)
    if facts["object_majority_color"] != target_color:
        raise AssertionError("target must be the unique object-majority color")
    if facts["pixel_majority_color"] != decoy_color:
        raise AssertionError("decoy must be the unique raw-pixel-majority color")
    if facts["target_center_bbox"] == facts["all_center_bbox"]:
        raise AssertionError("target frame must differ from all-center frame")
    return {
        "grid": grid,
        "profile": profile,
        "orientation": orientation,
        "target_color": target_color,
        "pixel_decoy_color": decoy_color,
        "target_count": facts["object_counts"][target_color],
        "target_pixel_count": facts["pixel_counts"][target_color],
        "pixel_decoy_count": facts["pixel_counts"][decoy_color],
        "target_center_bbox": facts["target_center_bbox"],
        "all_center_bbox": facts["all_center_bbox"],
        "centers": centers,
    }


def scene_facts(grid: Any) -> dict[str, Any]:
    value = _grid(grid)
    objects = _components(value)
    object_counts = Counter(obj["color"] for obj in objects)
    pixel_counts = Counter(cell for row in value for cell in row if cell)
    object_majority = _unique_majority(object_counts)
    pixel_majority = _unique_majority(pixel_counts)
    stage = stage_a_grid(value)
    target_cells = _cells_of_color(stage, object_majority)
    return {
        "object_counts": dict(sorted(object_counts.items())),
        "pixel_counts": dict(sorted(pixel_counts.items())),
        "object_majority_color": object_majority,
        "pixel_majority_color": pixel_majority,
        "target_color": object_majority,
        "target_center_bbox": _bbox(target_cells),
        "all_center_bbox": _bbox(_nonzero_cells(stage)),
        "square_sizes": sorted(obj["side"] for obj in objects),
        "square_count": len(objects),
        "nonzero_cells": sum(pixel_counts.values()),
    }


def _center_of_object(obj: dict[str, Any]) -> tuple[int, int]:
    return obj["center"]


def _blank_like(grid: list[list[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in _grid(grid)]


def canonical_rivals(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    value = _grid(grid)
    objects = _components(value)
    by_color: dict[int, list[dict[str, Any]]] = {}
    for obj in objects:
        by_color.setdefault(obj["color"], []).append(obj)

    def one_per_color(which: str) -> list[list[int]]:
        out = _blank_like(value)
        for color, candidates in by_color.items():
            if which == "first":
                chosen = min(candidates, key=lambda obj: (obj["r1"], obj["c1"]))
                r, c = chosen["center"]
            elif which == "largest":
                chosen = max(candidates, key=lambda obj: (obj["side"], -obj["r1"], -obj["c1"]))
                r, c = chosen["center"]
            elif which == "combined":
                cells = [cell for obj in candidates for cell in obj["cells"]]
                r1, c1, r2, c2 = _bbox(cells)
                r, c = (r1 + r2) // 2, (c1 + c2) // 2
            else:
                raise AssertionError(which)
            out[r][c] = color
        return out

    top_left = _blank_like(value)
    bottom_right = _blank_like(value)
    for obj in objects:
        top_left[obj["r1"]][obj["c1"]] = obj["color"]
        bottom_right[obj["r2"]][obj["c2"]] = obj["color"]
    return {
        "blank": _blank_like(value),
        "identity": [list(row) for row in value],
        "first_component_per_color": one_per_color("first"),
        "largest_component_per_color": one_per_color("largest"),
        "combined_bbox_center_per_color": one_per_color("combined"),
        "top_left_of_each_square": top_left,
        "bottom_right_of_each_square": bottom_right,
    }


def _frame_color_on_stage(stage: list[list[int]], color: int, *, frame_color: int = 9) -> list[list[int]]:
    return _paint_zero_cells(stage, frame_positions(_cells_of_color(stage, color)), frame_color)


def _fill_bbox_on_stage(stage: list[list[int]], color: int) -> list[list[int]]:
    r1, c1, r2, c2 = _bbox(_cells_of_color(stage, color))
    return _paint_zero_cells(
        stage,
        ((r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)),
        9,
    )


def _corners_on_stage(stage: list[list[int]], color: int) -> list[list[int]]:
    r1, c1, r2, c2 = _bbox(_cells_of_color(stage, color))
    return _paint_zero_cells(stage, ((r1, c1), (r1, c2), (r2, c1), (r2, c2)), 9)


def majority_rivals(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    value = _grid(grid)
    stage = stage_a_grid(value)
    center_counts = Counter(cell for row in stage for cell in row if cell)
    pixel_counts = Counter(cell for row in value for cell in row if cell)
    intended = _unique_majority(center_counts)
    colors = sorted(center_counts)
    second = sorted(center_counts, key=lambda color: (-center_counts[color], color))[1]
    least = sorted(center_counts, key=lambda color: (center_counts[color], color))[0]
    objects = _components(value)
    largest_obj = max(objects, key=lambda obj: (len(obj["cells"]), -obj["r1"], -obj["c1"]))
    first_obj = min(objects, key=lambda obj: (obj["r1"], obj["c1"]))
    last_obj = max(objects, key=lambda obj: (obj["r2"], obj["c2"]))
    last_anchor_obj = max(objects, key=lambda obj: (obj["r1"], obj["c1"]))
    all_frame = _paint_zero_cells(stage, frame_positions(_nonzero_cells(stage)), 9)
    overwrite = _paint_all_cells(stage, frame_positions(_cells_of_color(stage, intended)), 9)
    return {
        "canonical_only": stage,
        "skip_stage_a": skip_stage_a_transform(value),
        "raw_pixel_majority_on_centers": _frame_color_on_stage(stage, _unique_majority(pixel_counts)),
        "frame_all_centers": all_frame,
        "least_frequent_center_color": _frame_color_on_stage(stage, least),
        "second_most_frequent_center_color": _frame_color_on_stage(stage, second),
        "smallest_numeric_color": _frame_color_on_stage(stage, colors[0]),
        "largest_numeric_color": _frame_color_on_stage(stage, colors[-1]),
        "largest_input_square_color": _frame_color_on_stage(stage, largest_obj["color"]),
        "top_left_input_square_color": _frame_color_on_stage(stage, first_obj["color"]),
        "bottom_right_input_square_color": _frame_color_on_stage(stage, last_obj["color"]),
        "last_top_left_anchor_color": _frame_color_on_stage(stage, last_anchor_obj["color"]),
        "fill_target_bbox": _fill_bbox_on_stage(stage, intended),
        "target_bbox_corners_only": _corners_on_stage(stage, intended),
        "overwrite_target_centers": overwrite,
        "frame_color_8": _frame_color_on_stage(stage, intended, frame_color=8),
    }


def shortcut_outputs(grid: list[list[int]], settings: dict[str, str]) -> dict[str, list[list[int]]]:
    mode = _settings(settings)["mode"]
    return canonical_rivals(grid) if mode == "canonical" else majority_rivals(grid)


def certify(episode: dict[str, Any]) -> dict[str, Any]:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must be exactly four")
    seen = set()
    for pair in train + test:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("pairs must contain exactly input and output")
        grid, output = _grid(pair["input"]), _grid(pair["output"])
        if (len(grid), len(grid[0])) != (len(output), len(output[0])):
            raise ValueError("output dimensions must match input")
        key = grid_sha256(grid)
        if key in seen:
            raise ValueError("all inputs must be distinct")
        seen.add(key)
        if transform(grid, chosen) != output:
            raise ValueError("claim label disagrees with selected Python semantics")

    survivors = [
        setting
        for setting in SETTINGS
        if all(transform(pair["input"], setting) == pair["output"] for pair in train)
    ]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify chosen mode: {survivors}")

    names = sorted(shortcut_outputs(train[0]["input"], chosen))
    refutations = {
        name: any(shortcut_outputs(pair["input"], chosen)[name] != pair["output"] for pair in train)
        for name in names
    }
    if not all(refutations.values()):
        raise ValueError(f"declared shortcut survives demonstrations: {refutations}")
    return {
        "scope": "two settings plus task-specific semantic shortcuts",
        "survivors": copy.deepcopy(survivors),
        "shortcut_refutations": refutations,
        "query_input_sha256": [grid_sha256(pair["input"]) for pair in test],
    }


def generate(
    seed: int,
    settings: dict[str, str] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    if settings is None:
        settings = _rng(seed, "settings").choice(SETTINGS)
    chosen = _settings(settings)

    train = []
    for index in range(demos):
        height, width = _DEMO_SHAPES[index]
        scene = build_scene(seed, index, height, width, profile=_DEMO_PROFILES[index])
        train.append({"input": scene["grid"], "output": transform(scene["grid"], chosen)})
    test = []
    for slot, ((height, width), profile) in enumerate(zip(_QUERY_SHAPES, _QUERY_PROFILES)):
        scene = build_scene(seed, 10_000 + slot, height, width, profile=profile)
        test.append({"input": scene["grid"], "output": transform(scene["grid"], chosen)})

    episode = {
        "schema": "70abd9105769-majority-frame-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "selection_scope": "once_per_episode",
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


class RacketRunner:
    """One protected Racket process for bounded authoring evidence."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc: Any) -> None:
        self.bridge.close()


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be the exact integer 0..3")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must contain demonstrations and four queries")
    return public_challenge_bytes({"train": train, "test": [test[query_index]]})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mode", choices=PARAMETERS["mode"], default="canonical")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    episode = generate(args.seed, {"mode": args.mode}, args.demos, args.queries)
    result = {
        "status": "prototype_proposed",
        "settings": episode["settings"],
        "counts": {"demos": len(episode["train"]), "queries": len(episode["test"])},
        "certificate": episode["certificate"],
    }
    if args.racket:
        with RacketRunner() as execute:
            for pair in episode["train"] + episode["test"]:
                if execute(episode["program_solution"], pair["input"]) != pair["output"]:
                    raise RuntimeError("protected Racket disagreed with claim label")
            result["racket"] = execute.identity
            result["racket_evaluations"] = len(episode["train"]) + len(episode["test"])
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"episode": episode, "result": result}, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
