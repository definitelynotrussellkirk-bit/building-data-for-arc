"""Matched-input green-rectangle scope family for ``34f8510e39d0``.

Step A segments the green filled rectangles and derives their input-dependent
areas.  The episode-fixed scope selects either every green rectangle (the exact
canonical default) or the unique largest one.  Step B recolors the selected
rectangles' true bounding-box perimeters cyan while preserving interiors and all
distractors.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "34f8510e39d0"
SETTINGS = ("all_green", "largest_only")
DEFAULT = "all_green"
RIVALS = ("opposite_scope", "fill_selected", "color_blind_size", "smallest_only")

DEMO_SPECS = (
    (10, 12),
    (12, 14),
    (15, 16),
    (18, 20),
    (24, 24),
    (28, 30),
)
QUERY_SPECS = (
    (14, 17),
    (19, 21),
    (25, 27),
    (30, 30),
)

_TASK_HOME = Path(__file__).resolve().parents[2]
_name = "_generator_34f_" + hashlib.sha256(str(_TASK_HOME).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _TASK_HOME / "generator.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load task generator.py")
generator = importlib.util.module_from_spec(_spec)
sys.modules[_name] = generator
_spec.loader.exec_module(generator)


def integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def setting(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("scope must be all_green or largest_only")
    return value


def _rectangles(value: object) -> list[dict[str, Any]]:
    errors = generator.self_check(value)
    if errors:
        raise ValueError(f"invalid rectangle scene: {errors}")
    boxes = generator._green_boxes(value)
    rows = []
    for r0, c0, r1, c1 in boxes:
        rows.append(
            {
                "bbox": (r0, c0, r1, c1),
                "height": r1 - r0 + 1,
                "width": c1 - c0 + 1,
                "area": (r1 - r0 + 1) * (c1 - c0 + 1),
            }
        )
    return sorted(rows, key=lambda row: (-row["area"], row["bbox"][0], row["bbox"][1]))


def _size_matched_distractor(value: object, green: list[dict[str, Any]]) -> bool:
    target_shapes = {(row["height"], row["width"]) for row in green}
    colors = sorted({cell for row in value for cell in row} - {0, 3, 8})
    for color in colors:
        for comp in generator._components_of_color(value, color):
            solid, (r0, c0, r1, c1) = generator._solid_rect(comp)
            if solid and (r1 - r0 + 1, c1 - c0 + 1) in target_shapes:
                return True
    return False


def intermediate(value: object) -> dict[str, Any]:
    green = _rectangles(value)
    return {
        "height": len(value),
        "width": len(value[0]),
        "green_rectangles": [
            {
                "bbox": list(row["bbox"]),
                "height": row["height"],
                "width": row["width"],
                "area": row["area"],
            }
            for row in green
        ],
        "largest_bbox": list(green[0]["bbox"]),
        "largest_area": green[0]["area"],
        "largest_is_unique": sum(row["area"] == green[0]["area"] for row in green) == 1,
        "size_matched_distractor": _size_matched_distractor(value, green),
    }


def _selected_boxes(value: object, scope: str) -> list[tuple[int, int, int, int]]:
    mode = setting(scope)
    rows = _rectangles(value)
    return [row["bbox"] for row in rows] if mode == "all_green" else [rows[0]["bbox"]]


def solve(value: object, scope: str) -> list[list[int]]:
    return generator._outline_boxes(value, _selected_boxes(value, scope))


def solve_smallest_only(value: object) -> list[list[int]]:
    rows = _rectangles(value)
    return generator._outline_boxes(value, [rows[-1]["bbox"]])


def _fill_selected(value: object, scope: str) -> list[list[int]]:
    selected = set()
    for r0, c0, r1, c1 in _selected_boxes(value, scope):
        selected.update((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
    return [
        [8 if (r, c) in selected and value[r][c] == 3 else value[r][c] for c in range(len(value[0]))]
        for r in range(len(value))
    ]


def solve_rival(value: object, scope: str, rival: str) -> list[list[int]]:
    mode = setting(scope)
    if rival not in RIVALS:
        raise ValueError("unknown rival")
    if rival == "opposite_scope":
        return solve(value, "largest_only" if mode == "all_green" else "all_green")
    if rival == "fill_selected":
        return _fill_selected(value, mode)
    if rival == "color_blind_size":
        return generator._outline_rectangles_by_size_rival(value)
    return solve_smallest_only(value)


def _derived_seed(seed: int, split: str, index: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}:scope-v1:{seed}:{split}:{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _shape_bank(height: int, width: int) -> tuple[tuple[int, int], ...]:
    m = min(height, width)
    if m <= 12:
        return ((3, 4), (2, 4), (2, 3))
    if m <= 17:
        return ((5, 6), (4, 5), (2, 4))
    if m <= 22:
        return ((6, 7), (5, 6), (3, 5))
    if m <= 27:
        return ((7, 8), (6, 7), (4, 6))
    return ((8, 9), (7, 8), (5, 7))


def _orient(shape: tuple[int, int], slot_h: int, slot_w: int, rng: random.Random) -> tuple[int, int]:
    choices = [shape]
    if shape[0] != shape[1] and shape[1] + 2 <= slot_h and shape[0] + 2 <= slot_w:
        choices.append((shape[1], shape[0]))
    return rng.choice(choices)


def _paint_rect(grid: list[list[int]], color: int, slot: tuple[int, int, int, int], shape: tuple[int, int], rng: random.Random) -> tuple[int, int, int, int]:
    sr0, sc0, sr1, sc1 = slot
    slot_h, slot_w = sr1 - sr0, sc1 - sc0
    rh, rw = _orient(shape, slot_h, slot_w, rng)
    if rh + 2 > slot_h or rw + 2 > slot_w:
        raise AssertionError(f"shape {rh}x{rw} does not fit slot {slot_h}x{slot_w}")
    r = rng.randint(sr0 + 1, sr1 - rh - 1)
    c = rng.randint(sc0 + 1, sc1 - rw - 1)
    for rr in range(r, r + rh):
        for cc in range(c, c + rw):
            grid[rr][cc] = color
    return r, c, rh, rw


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    specs = DEMO_SPECS if split == "train" else QUERY_SPECS
    height, width = specs[index]
    rng = random.Random(_derived_seed(seed, split, index))
    grid = [[0] * width for _ in range(height)]
    rm, cm = height // 2, width // 2
    slots = [(0, 0, rm, cm), (0, cm, rm, width), (rm, 0, height, cm), (rm, cm, height, width)]
    rng.shuffle(slots)
    largest, medium, smallest = _shape_bank(height, width)
    # Choose one orientation that fits both assigned slots so the distractor is
    # an exact geometric twin even when odd canvas dimensions make quadrants unequal.
    orientations = [largest]
    if largest[0] != largest[1]:
        orientations.append((largest[1], largest[0]))
    fitting = [
        shape
        for shape in orientations
        if all(
            shape[0] + 2 <= slot[2] - slot[0]
            and shape[1] + 2 <= slot[3] - slot[1]
            for slot in slots[:2]
        )
    ]
    if not fitting:
        raise AssertionError("largest shape has no shared orientation across assigned slots")
    largest_oriented = rng.choice(fitting)

    def paint_exact(color: int, slot: tuple[int, int, int, int], shape: tuple[int, int]) -> None:
        sr0, sc0, sr1, sc1 = slot
        rh, rw = shape
        if rh + 2 > sr1 - sr0 or rw + 2 > sc1 - sc0:
            raise AssertionError("largest shape does not fit assigned slot")
        r = rng.randint(sr0 + 1, sr1 - rh - 1)
        c = rng.randint(sc0 + 1, sc1 - rw - 1)
        for rr in range(r, r + rh):
            for cc in range(c, c + rw):
                grid[rr][cc] = color
    paint_exact(3, slots[0], largest_oriented)
    paint_exact(rng.choice((1, 2, 4, 5, 6, 7, 9)), slots[1], largest_oriented)
    _paint_rect(grid, 3, slots[2], medium, rng)
    _paint_rect(grid, 3, slots[3], smallest, rng)
    errors = generator.self_check(grid)
    if errors:
        raise AssertionError(f"authored scene failed base grammar: {errors}")
    info = intermediate(grid)
    areas = [row["area"] for row in info["green_rectangles"]]
    if len(areas) != 3 or areas.count(max(areas)) != 1 or not info["size_matched_distractor"]:
        raise AssertionError("authored scene lost scope witnesses")
    return grid


def generate(seed: object, scope: object, demos: object, queries: object) -> dict[str, Any]:
    seed_i = integer(seed, 0, 2**63 - 1, "seed")
    mode = setting(scope)
    demo_count = integer(demos, 2, 6, "demos")
    query_count = integer(queries, 1, 4, "queries")
    train = []
    for index in range(demo_count):
        data = _draw(seed_i, "train", index)
        train.append({"input": data, "output": solve(data, mode)})
    test = []
    for index in range(query_count):
        data = _draw(seed_i, "test", index)
        test.append({"input": data, "output": solve(data, mode)})
    return {"train": train, "test": test, "private_query_bank": copy.deepcopy(test)}
