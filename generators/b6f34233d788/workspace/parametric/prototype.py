"""Native ranking-priority family for b6f34233d788.

Both settings perform the same input-dependent two-stage computation:
A extracts every object and computes its hole count, occupied area, bbox and
crop; B consumes those descriptors to rank and horizontally pack the crops.
The canonical setting prioritizes holes, while the alternate prioritizes area.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "b6f34233d788"
HOME = Path(__file__).resolve().parent
RANKINGS = ("holes_then_area", "area_then_holes")
CANONICAL = (HOME / "canonical.rkt").read_text(encoding="utf-8")
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _balanced_expression(source: str, start: int) -> tuple[str, int]:
    depth = 0
    for index in range(start, len(source)):
        char = source[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start : index + 1], index + 1
    raise ValueError("unterminated comparator expression")


def _area_first_program() -> str:
    start = CANONICAL.index("(or (> ha hb)")
    old, end = _balanced_expression(CANONICAL, start)
    expected_prefix = "(or (> ha hb) (and (= ha hb)"
    if not old.startswith(expected_prefix):
        raise RuntimeError("canonical comparator changed unexpectedly")
    new = (
        "(or (> (obj-size a) (obj-size b)) "
        "(and (= (obj-size a) (obj-size b)) "
        "(or (> ha hb) "
        "(and (= ha hb) (e8b-list< (obj-bbox a) (obj-bbox b))))))"
    )
    result = CANONICAL[:start] + new + CANONICAL[end:]
    if result == CANONICAL:
        raise RuntimeError("alternate comparator edit was ineffective")
    return result


AREA_FIRST = _area_first_program()

# Canvas / number of objects.  Shape descriptors are designed so both primary
# and secondary keys are taught: a 16-cell double-ring ties a 16-cell solid on
# area but differs in holes; two 0-hole solids differ in area.
_TRAIN_SPECS = (
    (16, 20, 4),
    (17, 22, 4),
    (18, 24, 5),
    (20, 25, 5),
    (22, 27, 5),
    (24, 29, 6),
)
_QUERY_SPECS = (
    (18, 22, 4),
    (22, 26, 5),
    (26, 29, 6),
    (30, 30, 5),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_ranking(value: Any) -> str:
    if type(value) is not str or value not in RANKINGS:
        raise ValueError(f"ranking must be one of {list(RANKINGS)}")
    return value


def program_for(ranking: str) -> str:
    ranking = validate_ranking(ranking)
    return CANONICAL if ranking == "holes_then_area" else AREA_FIRST


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    top = min(r for r, _ in cells); left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _rotate(cells: Iterable[tuple[int, int]], turns: int) -> frozenset[tuple[int, int]]:
    result = _normalize(cells)
    for _ in range(turns % 4):
        height = max(r for r, _ in result) + 1
        result = _normalize((c, height - 1 - r) for r, c in result)
    return result


def _ring(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    )


def _multi_ring(holes: int, width: int = 4) -> frozenset[tuple[int, int]]:
    height = 2 * holes + 1
    return frozenset(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r % 2 == 0 or c in (0, width - 1)
    )


def _large_blob(variant: int) -> frozenset[tuple[int, int]]:
    # 5x5 minus one corner: connected, hole-free, occupied area 24.
    missing = ((0, 0), (0, 4), (4, 0), (4, 4))[variant % 4]
    return frozenset((r, c) for r in range(5) for c in range(5) if (r, c) != missing)


def _base_shapes(seed: int, index: int, count: int) -> list[dict[str, Any]]:
    rng = random.Random(f"{TASK_ID}:shapes:{seed}:{index}")
    shapes = [
        {"role": "solid_tie", "cells": frozenset((r, c) for r in range(4) for c in range(4))},  # area 16, holes 0
        {"role": "ring", "cells": _ring(3, 3)},                                                # area 8, holes 1
        {"role": "large_blob", "cells": _large_blob(rng.randrange(4))},                       # area 24, holes 0
        {"role": "double_ring", "cells": _multi_ring(2, 4)},                                  # area 16, holes 2
        {"role": "triple_ring", "cells": _multi_ring(3, 4)},                                  # area 22, holes 3
        {"role": "small_blob", "cells": frozenset((r, c) for r in range(3) for c in range(3))}, # area 9, holes 0
    ][:count]
    # Rotate asymmetric blobs and compact crops while keeping the 7x4
    # triple-ring vertical.  Transposing that crop to 4x7 can make the packed
    # six-object output 31--32 columns wide, outside ARC's 30x30 grid contract.
    for row in shapes:
        turns = 0 if row["role"] == "triple_ring" else rng.randrange(4)
        row["cells"] = _rotate(row["cells"], turns)
    rng.shuffle(shapes)
    return shapes


def _free(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    cells = set(cells)
    for r, c in cells:
        if not (0 <= r < height and 0 <= c < width) or grid[r][c] != 0:
            return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) not in cells and 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 0:
                    return False
    return True


def _place_shapes(seed: int, index: int, height: int, width: int, rows: list[dict[str, Any]], *, stress: bool) -> list[list[int]]:
    rng = random.Random(f"{TASK_ID}:placement:{seed}:{index}:{height}:{width}")
    colors = rng.sample(list(range(1, 10)), len(rows))
    for _attempt in range(400):
        grid = [[0] * width for _ in range(height)]
        order = list(range(len(rows)))
        rng.shuffle(order)
        placed = {}
        success = True
        for sequence, object_index in enumerate(order):
            shape = rows[object_index]["cells"]
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            candidates = [(r, c) for r in range(height - sh + 1) for c in range(width - sw + 1)]
            rng.shuffle(candidates)
            if stress and sequence == 0:
                candidates.insert(0, (0, 0))
            if stress and sequence == 1:
                candidates.insert(0, (height - sh, width - sw))
            found = False
            for top, left in candidates:
                absolute = {(top + r, left + c) for r, c in shape}
                if not _free(grid, absolute):
                    continue
                for r, c in absolute:
                    grid[r][c] = colors[object_index]
                placed[rows[object_index]["role"]] = (top, left)
                found = True
                break
            if not found:
                success = False
                break
        if not success:
            continue
        # Force both secondary-key lessons.  Area-only would put the earlier
        # 16-cell solid before the 16-cell double ring; holes-only would put the
        # earlier small solid before the larger 0-hole blob.
        solid = placed.get("solid_tie")
        double = placed.get("double_ring")
        large = placed.get("large_blob")
        if solid is None or double is None or large is None:
            continue
        if not (solid < double and solid < large):
            continue
        if _scene_is_teachable(grid):
            return grid
    raise RuntimeError("could not place a teachable isolated object scene")


def _components(grid: list[list[int]]) -> list[frozenset[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while remaining:
        start = min(remaining); remaining.remove(start)
        cells = {start}; queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt); cells.add(nxt); queue.append(nxt)
        result.append(frozenset(cells))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _crop(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    top, left, bottom, right = _bbox(cells)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _hole_count(crop: list[list[int]]) -> int:
    height, width = len(crop), len(crop[0])
    zeros = {(r, c) for r in range(height) for c in range(width) if crop[r][c] == 0}
    holes = 0
    while zeros:
        start = min(zeros); zeros.remove(start)
        queue = deque([start])
        touches = start[0] in (0, height - 1) or start[1] in (0, width - 1)
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in zeros:
                    zeros.remove(nxt); queue.append(nxt)
                    if nxt[0] in (0, height - 1) or nxt[1] in (0, width - 1):
                        touches = True
        if not touches:
            holes += 1
    return holes


def intermediate(grid: list[list[int]]) -> list[dict[str, Any]]:
    result = []
    for cells in _components(grid):
        box = _bbox(cells)
        crop = _crop(grid, cells)
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            raise ValueError("objects must be monochrome")
        result.append({
            "holes": _hole_count(crop),
            "area": len(cells),
            "bbox": list(box),
            "color": next(iter(colors)),
            "crop": crop,
        })
    return result


def _rank(descriptors: list[dict[str, Any]], ranking: str) -> list[dict[str, Any]]:
    ranking = validate_ranking(ranking)
    if ranking == "holes_then_area":
        key = lambda row: (-row["holes"], -row["area"], tuple(row["bbox"]))
    else:
        key = lambda row: (-row["area"], -row["holes"], tuple(row["bbox"]))
    return sorted(descriptors, key=key)


def _pack(rows: list[dict[str, Any]], *, center: bool = True) -> list[list[int]]:
    crops = [row["crop"] for row in rows]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for crop in crops:
        top = (height - len(crop)) // 2 if center else 0
        for r, values in enumerate(crop):
            for c, value in enumerate(values):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(crop[0]) + 1
    return out


def transform(grid: list[list[int]], ranking: str) -> list[list[int]]:
    return _pack(_rank(intermediate(grid), ranking))


def rival_transform(grid: list[list[int]], rival: str) -> list[list[int]]:
    rows = intermediate(grid)
    if rival == "holes_only":
        ranked = sorted(rows, key=lambda row: (-row["holes"], tuple(row["bbox"])))
    elif rival == "area_only":
        ranked = sorted(rows, key=lambda row: (-row["area"], tuple(row["bbox"])))
    elif rival == "input_bbox":
        ranked = sorted(rows, key=lambda row: tuple(row["bbox"]))
    elif rival == "holes_ascending":
        ranked = sorted(rows, key=lambda row: (row["holes"], -row["area"], tuple(row["bbox"])))
    elif rival == "area_ascending":
        ranked = sorted(rows, key=lambda row: (row["area"], -row["holes"], tuple(row["bbox"])))
    elif rival == "top_aligned":
        return _pack(_rank(rows, "holes_then_area"), center=False)
    elif rival == "discard_smallest":
        ranked = _rank(rows, "holes_then_area")
        ranked = [row for row in ranked if row["area"] != min(item["area"] for item in ranked)]
    else:
        raise ValueError(f"unknown rival: {rival}")
    return _pack(ranked)


RIVALS = (
    "holes_only",
    "area_only",
    "input_bbox",
    "holes_ascending",
    "area_ascending",
    "top_aligned",
    "discard_smallest",
)


def _scene_is_teachable(grid: list[list[int]]) -> bool:
    holes = transform(grid, "holes_then_area")
    area = transform(grid, "area_then_holes")
    if holes == area:
        return False
    # Each declared setting must disagree with every shortcut in the bounded
    # bank on every candidate.  This makes any two-demo prefix robust.
    for truth in (holes, area):
        if any(rival_transform(grid, rival) == truth for rival in RIVALS):
            return False
    descriptors = intermediate(grid)
    if not any(a["holes"] > b["holes"] and a["area"] < b["area"] for a in descriptors for b in descriptors):
        return False
    if not any(a["area"] == b["area"] and a["holes"] != b["holes"] for i, a in enumerate(descriptors) for b in descriptors[i + 1 :]):
        return False
    if not any(a["holes"] == b["holes"] and a["area"] != b["area"] for i, a in enumerate(descriptors) for b in descriptors[i + 1 :]):
        return False
    return True


def _build_input(seed: int, index: int, spec: tuple[int, int, int], *, query: bool) -> list[list[int]]:
    height, width, count = spec
    shapes = _base_shapes(seed + (10_000 if query else 0), index, count)
    return _place_shapes(seed + (10_000 if query else 0), index, height, width, shapes, stress=query and height == width == 30)


@lru_cache(maxsize=128)
def _episode_inputs_cached(seed: int) -> tuple[tuple, tuple]:
    _integer(seed, 0, 2**63 - 1, "seed")
    train = tuple(_build_input(seed, index, spec, query=False) for index, spec in enumerate(_TRAIN_SPECS))
    queries = [_build_input(seed, index, spec, query=True) for index, spec in enumerate(_QUERY_SPECS)]
    order = list(range(4))
    random.Random(f"{TASK_ID}:presentation:{seed}").shuffle(order)
    test = tuple(queries[index] for index in order)
    serial = [json.dumps(grid, separators=(",", ":")) for grid in (*train, *test)]
    if len(serial) != len(set(serial)):
        raise RuntimeError("input bank must be globally distinct")
    return train, test


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    train, test = _episode_inputs_cached(_integer(seed, 0, 2**63 - 1, "seed"))
    return {"train": deepcopy(list(train)), "test": deepcopy(list(test))}


def teaching_check(pairs: list[dict[str, Any]], ranking: str) -> dict[str, Any]:
    ranking = validate_ranking(ranking)
    survivors = [candidate for candidate in RANKINGS if all(transform(pair["input"], candidate) == pair["output"] for pair in pairs)]
    rival_survivors = [rival for rival in RIVALS if all(rival_transform(pair["input"], rival) == pair["output"] for pair in pairs)]
    return {"ranking": ranking, "survivors": survivors, "rival_survivors": rival_survivors, "demonstrations": len(pairs)}


def generate_episode(seed: int, ranking: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    ranking = validate_ranking(ranking)
    inputs = episode_inputs(seed)
    pair = lambda grid: {"input": deepcopy(grid), "output": transform(grid, ranking)}
    episode = {
        "train": [pair(grid) for grid in inputs["train"][:demos]],
        "test": [pair(grid) for grid in inputs["test"][:queries]],
        "program_solution": program_for(ranking),
    }
    check = teaching_check(episode["train"], ranking)
    if check["survivors"] != [ranking] or check["rival_survivors"]:
        raise RuntimeError(f"teaching prefix failed: {check}")
    return episode


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a stored private query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def input_metrics(grid: list[list[int]]) -> dict[str, Any]:
    height, width = len(grid), len(grid[0])
    descriptors = intermediate(grid)
    active = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    sides = []
    if any(r == 0 for r, _ in active): sides.append("top")
    if any(r == height - 1 for r, _ in active): sides.append("bottom")
    if any(c == 0 for _, c in active): sides.append("left")
    if any(c == width - 1 for _, c in active): sides.append("right")
    return {
        "shape": [height, width],
        "objects": len(descriptors),
        "foreground_cells": len(active),
        "hole_counts": [row["holes"] for row in descriptors],
        "areas": [row["area"] for row in descriptors],
        "boundary_sides": sides,
        "packed_shapes": {
            ranking: [len(packed), len(packed[0])]
            for ranking in RANKINGS
            for packed in (transform(grid, ranking),)
        },
    }
