"""BBox-corner marking with an optional selector-addressed frame relay.

The default program is the exact canonical rule.  The alternate first performs
that same marking.  A red selector then scans right across the *completed*
intermediate to the first newly blue corner; the matching blue corner to its
right and below define the selected bounding box, whose zero-valued perimeter
cells are painted green.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "fc5f4c1fd7c2"
VERSION = "corner-selector-frame-v1"
HERE = Path(__file__).resolve().parent
PARAMETER = "finish_mode"
MODES = ("mark_only", "selector_frame")
SETTINGS = tuple({PARAMETER: mode} for mode in MODES)

# shape, object count.  The slot layout is selected from the object count.
DEMO_PROFILES = (
    (14, 21, 5),
    (16, 21, 6),
    (18, 24, 6),
    (21, 24, 7),
    (24, 27, 8),
    (27, 30, 9),
)
QUERY_PROFILES = (
    (15, 21, 5),
    (20, 24, 6),
    (25, 27, 8),
    (30, 30, 9),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {PARAMETER}:
        raise ValueError("settings must name exactly finish_mode")
    mode = value[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"finish_mode must be one of {MODES}")
    return {PARAMETER: mode}


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(value)


def program(settings: Any) -> str:
    mode = _setting(settings)[PARAMETER]
    filename = "canonical.rkt" if mode == "mark_only" else "selector_frame.rkt"
    return (HERE / filename).read_bytes().decode("utf-8")


def _components(grid: list[list[int]], color: int = 4) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = list(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def mark_corners(grid: Any) -> list[list[int]]:
    data = _grid(grid)
    for cells in _components(data, 4):
        r1, c1, r2, c2 = _bbox(cells)
        for r, c in ((r1, c1), (r1, c2), (r2, c1), (r2, c2)):
            data[r][c] = 1
    return data


def _relay_bbox(stage_a: list[list[int]], original: list[list[int]]) -> tuple[int, int, int, int] | None:
    selector = next(
        ((r, c) for r, row in enumerate(original) for c, value in enumerate(row) if value == 2),
        None,
    )
    if selector is None:
        return None
    sr, sc = selector
    hit = next(((sr, c) for c in range(sc + 1, len(stage_a[0])) if stage_a[sr][c] == 1), None)
    if hit is None:
        return None
    r1, c1 = hit
    right = next((c for c in range(c1 + 1, len(stage_a[0])) if stage_a[r1][c] == 1), None)
    bottom = next((r for r in range(r1 + 1, len(stage_a)) if stage_a[r][c1] == 1), None)
    if right is None or bottom is None:
        return None
    return r1, c1, bottom, right


def _frame(stage_a: list[list[int]], bbox: tuple[int, int, int, int] | None) -> list[list[int]]:
    result = deepcopy(stage_a)
    if bbox is None:
        return result
    r1, c1, r2, c2 = bbox
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if result[r][c] != 1 and (r in (r1, r2) or c in (c1, c2)):
                result[r][c] = 3
    return result


def transform(grid: Any, settings: Any) -> list[list[int]]:
    chosen = _setting(settings)[PARAMETER]
    original = _grid(grid)
    stage_a = mark_corners(original)
    if chosen == "mark_only":
        return stage_a
    return _frame(stage_a, _relay_bbox(stage_a, original))


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}:{purpose}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _bands(length: int, count: int) -> list[tuple[int, int]]:
    return [(length * i // count, length * (i + 1) // count - 1) for i in range(count)]


def _slot_bboxes(seed: int, split: str, index: int, h: int, w: int, count: int) -> tuple[list[tuple[int, int, int, int]], int]:
    rows = 2 if count <= 6 else 3
    cols = 3
    slots = [(rb, cb) for rb in _bands(h, rows) for cb in _bands(w, cols)]
    rng = _rng(seed, split, index, "slots")

    central = [i for i, (_rb, cb) in enumerate(slots) if cb[0] <= w // 2 <= cb[1]]
    selected_slot = central[(seed + index) % len(central)]
    available = list(range(len(slots)))
    if count < len(available):
        removable = [i for i in available if i != selected_slot and i not in central[:1]]
        rng.shuffle(removable)
        omitted = set(removable[: len(available) - count])
        available = [i for i in available if i not in omitted]
    if selected_slot not in available:
        raise AssertionError("selected slot was omitted")

    bboxes: list[tuple[int, int, int, int]] = []
    selected_index = -1
    # At least one small and one large object; the selected object is medium.
    tiers = [0, 2, 1, 2, 0, 1, 2, 0, 1]
    rng.shuffle(tiers)
    for object_index, slot_index in enumerate(available):
        (sr1, sr2), (sc1, sc2) = slots[slot_index]
        max_h = max(3, sr2 - sr1 - 1)
        max_w = max(3, sc2 - sc1 - 1)
        tier = 1 if slot_index == selected_slot else tiers[object_index]
        if tier == 0:
            sh, sw = 3, 3
        elif tier == 1:
            sh, sw = max(4, max_h - 1), max(4, max_w - 1)
            sh, sw = min(sh, max_h), min(sw, max_w)
        else:
            sh, sw = max_h, max_w
        low_r, high_r = sr1 + 1, sr2 - sh
        low_c, high_c = sc1 + 1, sc2 - sw
        r1 = low_r if high_r < low_r else rng.randint(low_r, high_r)
        c1 = low_c if high_c < low_c else rng.randint(low_c, high_c)
        bbox = (r1, c1, r1 + sh - 1, c1 + sw - 1)
        if slot_index == selected_slot:
            selected_index = len(bboxes)
        bboxes.append(bbox)
    if selected_index < 0:
        raise AssertionError("no selected object")

    # Selected object must be neither area nor horizontal-position extreme.
    areas = [(r2 - r1 + 1) * (c2 - c1 + 1) for r1, c1, r2, c2 in bboxes]
    selected_area = areas[selected_index]
    if not (min(areas) < selected_area < max(areas)):
        # Deterministically force one small and one large non-selected box.
        other = [i for i in range(len(bboxes)) if i != selected_index]
        small, large = other[0], other[-1]
        for i, tier in ((small, 0), (large, 2)):
            r1, c1, r2, c2 = bboxes[i]
            (sr1, sr2), (sc1, sc2) = slots[available[i]]
            sh = 3 if tier == 0 else max(5, min(sr2 - sr1 - 1, 7))
            sw = 3 if tier == 0 else max(5, min(sc2 - sc1 - 1, 7))
            sh = min(sh, sr2 - sr1 - 1)
            sw = min(sw, sc2 - sc1 - 1)
            bboxes[i] = (sr1 + 1, sc1 + 1, sr1 + sh, sc1 + sw)
        areas = [(r2 - r1 + 1) * (c2 - c1 + 1) for r1, c1, r2, c2 in bboxes]
        if not (min(areas) < areas[selected_index] < max(areas)):
            raise AssertionError("profile cannot establish middle-area selector")
    cstarts = [bbox[1] for bbox in bboxes]
    if bboxes[selected_index][1] in (min(cstarts), max(cstarts)):
        raise AssertionError("selected object must not be leftmost or rightmost")
    return bboxes, selected_index


def _path(a: tuple[int, int], b: tuple[int, int], vertical_first: bool) -> list[tuple[int, int]]:
    ar, ac = a
    br, bc = b
    result: list[tuple[int, int]] = []
    if vertical_first:
        step = 1 if br >= ar else -1
        result.extend((r, ac) for r in range(ar, br + step, step))
        step = 1 if bc >= ac else -1
        result.extend((br, c) for c in range(ac, bc + step, step))
    else:
        step = 1 if bc >= ac else -1
        result.extend((ar, c) for c in range(ac, bc + step, step))
        step = 1 if br >= ar else -1
        result.extend((r, bc) for r in range(ar, br + step, step))
    return result


def _motif_cells(bbox: tuple[int, int, int, int], rng: random.Random) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    anchor = (rng.randint(r1 + 1, r2 - 1), rng.randint(c1 + 1, c2 - 1))
    endpoints = [
        (r1, rng.randint(c1 + 1, c2 - 1)),
        (r2, rng.randint(c1 + 1, c2 - 1)),
        (rng.randint(r1 + 1, r2 - 1), c1),
        (rng.randint(r1 + 1, r2 - 1), c2),
    ]
    cells: set[tuple[int, int]] = {anchor}
    for endpoint in endpoints:
        cells.update(_path(endpoint, anchor, bool(rng.randrange(2))))
    corners = {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}
    cells.difference_update(corners)
    return cells


def _profile(split: str, index: int) -> tuple[int, int, int]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    if not 0 <= index < len(profiles):
        raise ValueError("profile index outside available bank")
    return profiles[index]


def _draw_scene(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, count = _profile(split, index)
    bboxes, selected = _slot_bboxes(seed, split, index, h, w, count)
    grid = [[0] * w for _ in range(h)]
    rng = _rng(seed, split, index, "motifs")
    for bbox in bboxes:
        for r, c in _motif_cells(bbox, rng):
            grid[r][c] = 4
    r1, c1, _r2, _c2 = bboxes[selected]
    if c1 < 2 or grid[r1][c1 - 2] != 0 or grid[r1][c1 - 1] != 0:
        raise AssertionError("selected slot lacks a clear selector ray")
    grid[r1][c1 - 2] = 2

    analysis = analyze(grid)
    if analysis["selected_bbox"] != list(bboxes[selected]):
        raise AssertionError("selector did not recover the authored bbox")
    return grid


def analyze(grid: Any) -> dict[str, Any]:
    original = _grid(grid)
    stage_a = mark_corners(original)
    selected = _relay_bbox(stage_a, original)
    framed = _frame(stage_a, selected)
    return {
        "shape": [len(original), len(original[0])],
        "selector": next(
            ([r, c] for r, row in enumerate(original) for c, value in enumerate(row) if value == 2),
            None,
        ),
        "bboxes": [list(_bbox(component)) for component in _components(original, 4)],
        "selected_bbox": list(selected) if selected else None,
        "frame_cells": [
            [r, c]
            for r in range(len(original))
            for c in range(len(original[0]))
            if stage_a[r][c] != framed[r][c]
        ],
    }


def _pair(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    pairs = list(demos)
    survivors: list[dict[str, str]] = []
    for candidate in SETTINGS:
        try:
            if pairs and all(
                type(pair) is dict and pair.get("output") == transform(pair.get("input"), candidate)
                for pair in pairs
            ):
                survivors.append(dict(candidate))
        except (TypeError, ValueError):
            continue
    return survivors


def _bbox_ranked(grid: list[list[int]], key: str) -> tuple[int, int, int, int]:
    boxes = [_bbox(component) for component in _components(grid, 4)]
    if key == "largest":
        return max(boxes, key=lambda b: ((b[2] - b[0] + 1) * (b[3] - b[1] + 1), -b[0], -b[1]))
    if key == "smallest":
        return min(boxes, key=lambda b: ((b[2] - b[0] + 1) * (b[3] - b[1] + 1), b[0], b[1]))
    if key == "leftmost":
        return min(boxes, key=lambda b: (b[1], b[0]))
    if key == "rightmost":
        return max(boxes, key=lambda b: (b[1], -b[0]))
    raise ValueError(key)


def simple_rival_outputs(pairs: Iterable[dict[str, Any]]) -> dict[str, list[list[list[int]]]]:
    material = list(pairs)
    result: dict[str, list[list[list[int]]]] = {}
    for name in ("largest", "smallest", "leftmost", "rightmost"):
        outputs = []
        for pair in material:
            grid = _grid(pair["input"])
            outputs.append(_frame(mark_corners(grid), _bbox_ranked(grid, name)))
        result[f"frame_{name}"] = outputs
    all_outputs = []
    for pair in material:
        grid = _grid(pair["input"])
        out = mark_corners(grid)
        for box in [_bbox(component) for component in _components(grid, 4)]:
            out = _frame(out, box)
        all_outputs.append(out)
    result["frame_all"] = all_outputs
    return result


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    chosen = _setting(settings)
    train = [_pair(_draw_scene(seed, "train", index), chosen) for index in range(demos)]
    test = [_pair(_draw_scene(seed, "test", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify finish_mode")
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("episode contains duplicate inputs")
    return {"train": train, "test": test, "program_solution": program(chosen)}
