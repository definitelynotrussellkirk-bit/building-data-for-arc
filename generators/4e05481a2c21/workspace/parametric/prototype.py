"""Source-bound parametric packing family for ARC task 4e05481a2c21.

The canonical setting packs extracted enclosed-hole patterns from left to right.
The alternative computes each complete enclosed-hole union first, derives its
cell area, and then packs patterns by descending derived area with left-to-right
tie breaking.  Inputs are setting-neutral; native qualification replays labels
through the exact adjacent Racket programs.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

from reviewer_support import public_challenge_bytes

TASK_ID = "4e05481a2c21"
VERSION = "hole-area-pack-order-v1"
PACK_ORDERS = ("left_to_right", "hole_area_descending")
DEFAULT_PACK_ORDER = "left_to_right"
HERE = Path(__file__).resolve().parent


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"pack_order"}:
        raise ValueError("settings must contain exactly pack_order")
    value = settings["pack_order"]
    if type(value) is not str or value not in PACK_ORDERS:
        raise ValueError("pack_order must be left_to_right or hole_area_descending")
    return value


def _count(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _seed(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    return value


def program_for(pack_order: str) -> str:
    if pack_order not in PACK_ORDERS:
        raise ValueError(f"unsupported pack_order: {pack_order!r}")
    name = "canonical.rkt" if pack_order == "left_to_right" else "hole_area_descending.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def program(settings: Any) -> str:
    return program_for(validate_settings(settings))


def _strict_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return deepcopy(grid)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot bound empty cells")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid: list[list[int]]) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = rr + dr, cc + dc
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        queue.append(nxt)
            result.append((color, frozenset(cells)))
    return result


def _enclosed_regions(cells: frozenset[tuple[int, int]]) -> list[frozenset[tuple[int, int]]]:
    top, left, bottom, right = _bbox(cells)
    zeros = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
             if (r, c) not in cells}
    seen: set[tuple[int, int]] = set()
    enclosed = []
    for start in sorted(zeros):
        if start in seen:
            continue
        queue = [start]
        seen.add(start)
        region = []
        boundary = False
        for row, col in queue:
            region.append((row, col))
            boundary |= row in (top, bottom) or col in (left, right)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = row + dr, col + dc
                if nxt in zeros and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not boundary:
            enclosed.append(frozenset(region))
    return enclosed


def analyze(grid: Any) -> dict[str, Any]:
    source = _strict_grid(grid)
    objects = []
    for color, cells in _components(source):
        regions = _enclosed_regions(cells)
        holes = frozenset().union(*regions) if regions else frozenset()
        if not holes:
            continue
        top, left, bottom, right = _bbox(cells)
        htop, hleft, hbottom, hright = _bbox(holes)
        local = frozenset((r - htop, c - hleft) for r, c in holes)
        objects.append({
            "color": color,
            "cells": cells,
            "bbox": (top, left, bottom, right),
            "left": left,
            "regions": regions,
            "region_count": len(regions),
            "largest_region_area": max(map(len, regions)),
            "hole_cells": holes,
            "local_holes": local,
            "hole_area": len(holes),
            "hole_height": hbottom - htop + 1,
            "hole_width": hright - hleft + 1,
            "hole_bbox_area": (hbottom - htop + 1) * (hright - hleft + 1),
            "object_bbox_area": (bottom - top + 1) * (right - left + 1),
            "colored_area": len(cells),
        })
    objects.sort(key=lambda obj: obj["left"])
    if len(objects) < 2:
        raise ValueError("prototype inputs require at least two hole-bearing objects")
    if len({obj["left"] for obj in objects}) != len(objects):
        raise ValueError("object left edges must be unique")
    return {"height": len(source), "width": len(source[0]), "objects": objects}


def _ordered(objects: list[dict[str, Any]], policy: str) -> list[dict[str, Any]]:
    if policy == "left_to_right":
        return sorted(objects, key=lambda obj: obj["left"])
    if policy == "hole_area_descending":
        return sorted(objects, key=lambda obj: (-obj["hole_area"], obj["left"]))
    keys: dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]] = {
        "right_to_left": lambda obj: (-obj["left"],),
        "hole_area_ascending": lambda obj: (obj["hole_area"], obj["left"]),
        "hole_bbox_area_descending": lambda obj: (-obj["hole_bbox_area"], obj["left"]),
        "object_bbox_area_descending": lambda obj: (-obj["object_bbox_area"], obj["left"]),
        "colored_area_descending": lambda obj: (-obj["colored_area"], obj["left"]),
        "largest_region_descending": lambda obj: (-obj["largest_region_area"], obj["left"]),
        "region_count_descending": lambda obj: (-obj["region_count"], obj["left"]),
        "hole_width_descending": lambda obj: (-obj["hole_width"], obj["left"]),
        "color_ascending": lambda obj: (obj["color"], obj["left"]),
        "area_descending_reverse_ties": lambda obj: (-obj["hole_area"], -obj["left"]),
    }
    if policy not in keys:
        raise ValueError(f"unknown ordering policy: {policy}")
    return sorted(objects, key=keys[policy])


def _pack(records: list[dict[str, Any]]) -> list[list[int]]:
    height = max(obj["hole_height"] for obj in records)
    width = sum(obj["hole_width"] for obj in records) + len(records) - 1
    output = [[0] * width for _ in range(height)]
    left = 0
    for obj in records:
        for row, col in obj["local_holes"]:
            output[row][left + col] = obj["color"]
        left += obj["hole_width"] + 1
    return output


def solve_python(grid: Any, pack_order: str) -> list[list[int]]:
    if pack_order not in PACK_ORDERS and pack_order not in RIVAL_POLICIES:
        raise ValueError(f"unknown pack order: {pack_order}")
    info = analyze(grid)
    return _pack(_ordered(info["objects"], pack_order))


# Hole masks are local zero cells. A full colored rectangle is drawn around them.
SHAPES: dict[str, frozenset[tuple[int, int]]] = {
    "cross5": frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    "rect6": frozenset((r, c) for r in range(2) for c in range(3)),
    "square4": frozenset((r, c) for r in range(2) for c in range(2)),
    "line5": frozenset((0, c) for c in range(5)),
    "split6": frozenset({(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)}),
    "domino2v": frozenset({(0, 0), (1, 0)}),
    "line4": frozenset((0, c) for c in range(4)),
    "zig5": frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)}),
    "split4": frozenset({(0, 0), (0, 1), (2, 1), (2, 2)}),
    "t7": frozenset({(0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1), (3, 1)}),
    "sparse8": frozenset({(0, 0), (0, 1), (0, 2), (0, 3),
                            (5, 0), (5, 1), (5, 2), (5, 3)}),
    "sparse10": frozenset({(0, 0), (0, 1), (0, 2), (0, 3),
                             (2, 1), (2, 2),
                             (5, 0), (5, 1), (5, 2), (5, 3)}),
    "sparse12": frozenset({(0, 0), (0, 1), (0, 2), (0, 3),
                             (1, 0), (1, 1), (1, 2), (1, 3),
                             (5, 0), (5, 1), (5, 2), (5, 3)}),
    "sparse6": frozenset({(0, 0), (0, 1), (0, 2),
                            (5, 1), (5, 2), (5, 3)}),
}


def _shape_box(shape: frozenset[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _flipped(shape: frozenset[tuple[int, int]], rng: random.Random) -> frozenset[tuple[int, int]]:
    height, width = _shape_box(shape)
    flip_y, flip_x = bool(rng.randrange(2)), bool(rng.randrange(2))
    return frozenset((height - 1 - r if flip_y else r,
                      width - 1 - c if flip_x else c) for r, c in shape)


def _rng(seed: int, slot: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}/{VERSION}/{seed}/{slot}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _draw_object(grid: list[list[int]], top: int, left: int, color: int,
                 holes: frozenset[tuple[int, int]]) -> None:
    hole_h, hole_w = _shape_box(holes)
    for row in range(top, top + hole_h + 2):
        for col in range(left, left + hole_w + 2):
            grid[row][col] = color
    for row, col in holes:
        grid[top + 1 + row][left + 1 + col] = 0


def _scene(seed: int, slot: str, height: int, width: int,
           names: list[str], colors: list[int], *, gap: int = 1,
           fixed_tops: list[int] | None = None, left_margin: int | None = None) -> list[list[int]]:
    if len(names) != len(colors):
        raise ValueError("shape/color mismatch")
    rng = _rng(seed, slot)
    shapes = [_flipped(SHAPES[name], rng) for name in names]
    sizes = [(_shape_box(shape)[0] + 2, _shape_box(shape)[1] + 2) for shape in shapes]
    used_width = sum(w for _, w in sizes) + gap * (len(sizes) - 1)
    if used_width > width:
        raise ValueError(f"scene {slot} exceeds width {width}")
    margin = rng.randrange(width - used_width + 1) if left_margin is None else left_margin
    if not 0 <= margin <= width - used_width:
        raise ValueError("invalid left margin")
    tops = []
    for index, (obj_h, _) in enumerate(sizes):
        top = (rng.randrange(height - obj_h + 1) if fixed_tops is None
               else fixed_tops[index])
        if not 0 <= top <= height - obj_h:
            raise ValueError("invalid fixed top")
        tops.append(top)
    grid = [[0] * width for _ in range(height)]
    left = margin
    for shape, color, top, (_, obj_w) in zip(shapes, colors, tops, sizes, strict=True):
        _draw_object(grid, top, left, color, shape)
        left += obj_w + gap
    return grid


def _demo_inputs(seed: int) -> list[list[list[int]]]:
    return [
        _scene(seed, "demo-0", 12, 28,
               ["cross5", "rect6", "square4", "line5"], [8, 2, 6, 4]),
        _scene(seed, "demo-1", 14, 26,
               ["line5", "split6", "square4", "domino2v"], [3, 9, 1, 7]),
        _scene(seed, "demo-2", 15, 24,
               ["zig5", "t7", "split4"], [5, 2, 8], gap=2),
        _scene(seed, "demo-3", 18, 29,
               ["line4", "cross5", "split6", "domino2v"], [9, 4, 2, 6], gap=2),
        _scene(seed, "demo-4", 11, 23,
               ["square4", "line5", "zig5"], [1, 8, 3], gap=2),
        _scene(seed, "demo-5", 20, 30,
               ["t7", "split4", "rect6", "cross5"], [7, 3, 9, 2], gap=2),
    ]


def _query_inputs(seed: int) -> list[list[list[int]]]:
    return [
        _scene(seed, "query-0", 12, 20,
               ["domino2v", "t7", "square4"], [6, 2, 9], gap=2),
        _scene(seed, "query-1", 16, 24,
               ["split4", "rect6", "line5", "domino2v"], [4, 8, 1, 7]),
        _scene(seed, "query-2", 22, 28,
               ["zig5", "split6", "t7", "square4"], [5, 9, 3, 6], gap=2),
        _scene(seed, "query-3-stress", 30, 30,
               ["sparse12", "sparse8", "sparse10", "sparse6"], [2, 5, 8, 3],
               gap=2, fixed_tops=[0, 7, 14, 22], left_margin=0),
    ]


RIVAL_POLICIES = (
    "right_to_left",
    "hole_area_ascending",
    "hole_bbox_area_descending",
    "object_bbox_area_descending",
    "colored_area_descending",
    "largest_region_descending",
    "region_count_descending",
    "hole_width_descending",
    "color_ascending",
    "area_descending_reverse_ties",
)


def _candidate_policies(pack_order: str) -> tuple[str, ...]:
    other = "hole_area_descending" if pack_order == "left_to_right" else "left_to_right"
    return (other, *RIVAL_POLICIES)


def teaching_check(episode: dict[str, Any], pack_order: str) -> dict[str, Any]:
    if pack_order not in PACK_ORDERS:
        raise ValueError("unknown pack_order")
    rows = []
    for policy in _candidate_policies(pack_order):
        demo_differences = []
        for index, pair in enumerate(episode["train"]):
            got = solve_python(pair["input"], policy)
            if got != pair["output"]:
                demo_differences.append(index)
        query_differences = []
        if not demo_differences:
            for index, pair in enumerate(episode["test"]):
                if solve_python(pair["input"], policy) != pair["output"]:
                    query_differences.append(index)
        rows.append({
            "policy": policy,
            "demo_differences": demo_differences,
            "demo_survives": not demo_differences,
            "query_differences": query_differences,
            "harmful": not demo_differences and bool(query_differences),
        })
    other = "hole_area_descending" if pack_order == "left_to_right" else "left_to_right"
    return {
        "pack_order": pack_order,
        "rival_count": len(rows),
        "rivals": rows,
        "settings_disagree_on_demos": any(
            solve_python(pair["input"], other) != pair["output"] for pair in episode["train"]
        ),
        "demo_survivors": [row["policy"] for row in rows if row["demo_survives"]],
        "harmful_survivors": [row["policy"] for row in rows if row["harmful"]],
    }


def generate_episode(seed: int, *, pack_order: str, demos: int = 3,
                     queries: int = 4) -> dict[str, Any]:
    _seed(seed)
    if pack_order not in PACK_ORDERS:
        raise ValueError("unsupported pack_order")
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    demo_inputs = _demo_inputs(seed)
    query_inputs = _query_inputs(seed)
    train = [{"input": grid, "output": solve_python(grid, pack_order)}
             for grid in demo_inputs[:demos]]
    test = [{"input": grid, "output": solve_python(grid, pack_order)}
            for grid in query_inputs[:queries]]
    episode = {
        "train": train,
        "test": test,
        "program_solution": program_for(pack_order),
        "settings": {"pack_order": pack_order},
        "seed": seed,
    }
    audit = teaching_check(episode, pack_order)
    if audit["harmful_survivors"]:
        raise AssertionError(f"teaching hole: {audit['harmful_survivors']}")
    return episode


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    pack_order = validate_settings(settings)
    episode = generate_episode(seed, pack_order=pack_order, demos=demos, queries=queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index outside retained test range")
    value = {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
    return json.loads(public_challenge_bytes(value))


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return public_challenge_bytes(public_view(episode, query_index))


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def derived_area_vector(grid: Any) -> list[dict[str, int]]:
    """Compact A-stage intermediate for the retained causal witness."""
    return [{"left": obj["left"], "color": obj["color"],
             "hole_area": obj["hole_area"], "hole_bbox_area": obj["hole_bbox_area"]}
            for obj in analyze(grid)["objects"]]
