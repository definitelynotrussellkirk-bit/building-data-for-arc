#!/usr/bin/env python3
"""Episode-fixed frame-order family for 74a2d06b72b1.

The canonical setting counts marker cells from the outermost frame inward.
The nearby setting counts the same markers from the innermost frame outward.
Both then fill the selected frame's interior while excluding the next frame
farther inward, so the selector genuinely feeds the ring construction.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "74a2d06b72b1"
SCHEMA = "arcpuzzles-frame-order-episode-v1"
ORDERS = ("outer_first", "inner_first")
DEMO_PROFILES = (
    (15, 16, 3, 1),
    (17, 18, 3, 2),
    (20, 19, 4, 1),
    (23, 24, 4, 3),
    (27, 26, 5, 2),
    (29, 30, 5, 4),
)
QUERY_PROFILES = (
    (18, 20, 4, 3),
    (22, 21, 4, 1),
    (26, 28, 5, 4),
    (30, 30, 5, 2),
)


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines() if line.strip()]
    sources = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    if len(sources) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}")
    return next(iter(sources))


CANONICAL_PROGRAM = _canonical_program()
_OUTER_INDEX = "(define idx (- (length (find-color g 2)) 1))"
_INNER_INDEX = "(define idx (- (length frames) (length (find-color g 2))))"
if CANONICAL_PROGRAM.count(_OUTER_INDEX) != 1:
    raise RuntimeError("canonical frame selector patch point changed")
INNER_FIRST_PROGRAM = CANONICAL_PROGRAM.replace(_OUTER_INDEX, _INNER_INDEX)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings: dict[str, Any]) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"frame_order"}:
        raise ValueError("settings must name exactly frame_order")
    order = settings["frame_order"]
    if order not in ORDERS:
        raise ValueError("frame_order must be outer_first or inner_first")
    return {"frame_order": order}


def program(settings: dict[str, Any]) -> str:
    order = settings_value(settings)["frame_order"]
    return CANONICAL_PROGRAM if order == "outer_first" else INNER_FIRST_PROGRAM


def _strict_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not grid or len(grid) > 30 or type(grid[0]) is not list
            or not grid[0] or len(grid[0]) > 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be a 1..30 rectangular exact-integer grid")
    return grid


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        first = min(unseen)
        stack = [first]
        unseen.remove(first)
        cells = {first}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(cells)
    return result


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    _strict_grid(grid)
    frames = []
    for cells in _components(grid, 1):
        r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
        border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if r in (r0, r1) or c in (c0, c1)}
        if cells == border and r1 - r0 >= 2 and c1 - c0 >= 2:
            frames.append((r0, c0, r1, c1))
    frames.sort(key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1), reverse=True)
    if len(frames) < 2:
        raise ValueError("input needs at least two complete frames")
    for outer, inner in zip(frames, frames[1:]):
        if not (outer[0] < inner[0] and outer[1] < inner[1]
                and outer[2] > inner[2] and outer[3] > inner[3]):
            raise ValueError("frames must be strictly nested")
    markers = sum(cell == 2 for row in grid for cell in row)
    if not 1 <= markers <= len(frames):
        raise ValueError("marker count must select one frame")
    return {"frames": frames, "marker_count": markers}


def intermediate(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    selected = settings_value(settings)["frame_order"]
    analysis = analyze(grid)
    frames = analysis["frames"]
    count = analysis["marker_count"]
    index = count - 1 if selected == "outer_first" else len(frames) - count
    inner = frames[index + 1] if index + 1 < len(frames) else None
    return {"marker_count": count, "selected_index": index,
            "selected_frame": list(frames[index]),
            "next_inner_frame": list(inner) if inner is not None else None}


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    state = intermediate(grid, settings)
    r0, c0, r1, c1 = state["selected_frame"]
    inner = state["next_inner_frame"]
    out = deepcopy(grid)
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            blocked = inner is not None and inner[0] <= r <= inner[2] and inner[1] <= c <= inner[3]
            if out[r][c] == 0 and not blocked:
                out[r][c] = 8
    return out


def _rng(seed: int, domain: str, index: int) -> random.Random:
    payload = json.dumps([TASK_ID, SCHEMA, seed, domain, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    r0, c0, r1, c1 = box
    for r in range(r0, r1 + 1):
        grid[r][c0] = grid[r][c1] = 1
    for c in range(c0, c1 + 1):
        grid[r0][c] = grid[r1][c] = 1


def sample_input(seed: int, domain: str, index: int, profile: tuple[int, int, int, int]) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    h, w, count, markers = profile
    rng = _rng(seed, domain, index)
    minimum = 3 + 4 * (count - 1)
    if min(h - 2, w - 2) < minimum:
        raise ValueError("profile cannot fit separated nested frames")
    boxes = [(1, 1, h - 2, w - 2)]
    for level in range(1, count):
        r0, c0, r1, c1 = boxes[-1]
        remaining = count - level - 1
        min_after = 3 + 4 * remaining
        row_extra = max(0, (r1 - r0 + 1) - 4 - min_after)
        col_extra = max(0, (c1 - c0 + 1) - 4 - min_after)
        top = 2 + (1 if row_extra > 0 and rng.randrange(2) else 0)
        bottom = 2 + (1 if row_extra > 1 and rng.randrange(2) else 0)
        left = 2 + (1 if col_extra > 0 and rng.randrange(2) else 0)
        right = 2 + (1 if col_extra > 1 and rng.randrange(2) else 0)
        if r1 - r0 + 1 - top - bottom < min_after:
            top = bottom = 2
        if c1 - c0 + 1 - left - right < min_after:
            left = right = 2
        boxes.append((r0 + top, c0 + left, r1 - bottom, c1 - right))
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for box in boxes:
        _draw_frame(grid, box)
    outer = boxes[0]
    free = [(r, c) for r in range(h) for c in range(w)
            if not (outer[0] <= r <= outer[2] and outer[1] <= c <= outer[3])]
    rng.shuffle(free)
    for r, c in free[:markers]:
        grid[r][c] = 2
    info = analyze(grid)
    if len(info["frames"]) != count or info["marker_count"] != markers:
        raise ValueError("sampler failed its frame/count contract")
    return grid


def check_teaching(train: list[dict[str, Any]], settings: dict[str, Any]) -> dict[str, Any]:
    chosen = settings_value(settings)["frame_order"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    survivors = []
    for order in ORDERS:
        candidate = {"frame_order": order}
        if all(type(pair) is dict and {"input", "output"} <= set(pair)
               and transform(pair["input"], candidate) == pair["output"] for pair in train):
            survivors.append(order)
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify {chosen}; survivors={survivors}")
    return {"fit_scope": "demonstrations_only", "survivors": survivors,
            "declared_settings": list(ORDERS),
            "limits": "Finite declared setting family only; not universal uniqueness."}


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    selected = settings_value(settings)
    result = {"schema": SCHEMA, "task_id": TASK_ID, "seed": seed,
              "settings": selected, "program_solution": program(selected),
              "train": [], "test": []}
    seen = set()
    for split, domain, count, profiles in (("train", "demo", demos, DEMO_PROFILES),
                                            ("test", "query", queries, QUERY_PROFILES)):
        for index in range(count):
            grid = sample_input(seed, domain, index, profiles[index])
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate generated input")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, selected)})
    check_teaching(result["train"], selected)
    return result


def verify_episode(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    selected = settings_value(episode.get("settings"))
    if episode.get("task_id") != TASK_ID or episode.get("program_solution") != program(selected):
        raise ValueError("episode identity/program mismatch")
    seen = set()
    for split in ("train", "test"):
        pairs = episode.get(split)
        if type(pairs) is not list or not pairs:
            raise ValueError("episode splits must be nonempty lists")
        for pair in pairs:
            _strict_grid(pair.get("input")); _strict_grid(pair.get("output"))
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate episode input")
            seen.add(key)
            if transform(pair["input"], selected) != pair["output"]:
                raise ValueError("label mismatch")
    return check_teaching(episode["train"], selected)


def audit(seed: int = 41) -> dict[str, Any]:
    report = {"schema": "arcpuzzles-frame-order-self-audit-v1", "status": "passed", "settings": {}}
    for order in ORDERS:
        episode = generate(seed, {"frame_order": order}, demos=2, queries=4)
        rivals = {
            "always_outermost": lambda grid: _paint_fixed(grid, 0),
            "always_innermost": lambda grid: _paint_fixed(grid, len(analyze(grid)["frames"]) - 1),
            "fill_selected_interior": lambda grid: _fill_without_inner_exclusion(grid, {"frame_order": order}),
        }
        rows = {}
        for name, rival in rivals.items():
            mismatches = [i for i, pair in enumerate(episode["train"]) if rival(pair["input"]) != pair["output"]]
            rows[name] = {"rejected": bool(mismatches), "first_demonstration": mismatches[0] if mismatches else None}
            if not mismatches:
                report["status"] = "failed"
        report["settings"][order] = {"survivors": check_teaching(episode["train"], {"frame_order": order})["survivors"], "rivals": rows}
    if report["status"] != "passed":
        raise ValueError("bounded frame-order audit found a surviving shortcut")
    return report


def _paint_fixed(grid: list[list[int]], index: int) -> list[list[int]]:
    info = analyze(grid); frames = info["frames"]
    index = max(0, min(index, len(frames) - 1))
    out = deepcopy(grid); selected = frames[index]
    inner = frames[index + 1] if index + 1 < len(frames) else None
    for r in range(selected[0] + 1, selected[2]):
        for c in range(selected[1] + 1, selected[3]):
            if out[r][c] == 0 and not (inner and inner[0] <= r <= inner[2] and inner[1] <= c <= inner[3]):
                out[r][c] = 8
    return out


def _fill_without_inner_exclusion(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    state = intermediate(grid, settings); out = deepcopy(grid)
    r0, c0, r1, c1 = state["selected_frame"]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if out[r][c] == 0:
                out[r][c] = 8
    return out
