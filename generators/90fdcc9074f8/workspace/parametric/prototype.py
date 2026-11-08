#!/usr/bin/env python3
"""Episode-fixed panel vote-policy family for 90fdcc9074f8.

The canonical setting keeps cells marked by at least two of three panels.
The nearby setting keeps only cells marked by all three.  The resulting
input-dependent repaired mask is then consumed by the unchanged component-wise
onion-depth and crop stage.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "90fdcc9074f8"
SCHEMA = "arcpuzzles-vote-policy-episode-v1"
POLICIES = ("majority", "unanimous")
DEMO_PROFILES = ((7, 7), (9, 8), (12, 9), (16, 7), (22, 8), (28, 9))
QUERY_PROFILES = ((10, 9), (18, 8), (24, 9), (30, 9))


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines() if line.strip()]
    sources = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    if len(sources) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}")
    return next(iter(sources))


CANONICAL_PROGRAM = _canonical_program()
_MAJORITY = "(if (>= (* hits 2) n) 1 0)"
_UNANIMOUS = "(if (= hits n) 1 0)"
if CANONICAL_PROGRAM.count(_MAJORITY) != 1:
    raise RuntimeError("canonical vote patch point changed")
UNANIMOUS_PROGRAM = CANONICAL_PROGRAM.replace(_MAJORITY, _UNANIMOUS)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings: dict[str, Any]) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"vote_policy"}:
        raise ValueError("settings must name exactly vote_policy")
    policy = settings["vote_policy"]
    if policy not in POLICIES:
        raise ValueError("vote_policy must be majority or unanimous")
    return {"vote_policy": policy}


def program(settings: dict[str, Any]) -> str:
    policy = settings_value(settings)["vote_policy"]
    return CANONICAL_PROGRAM if policy == "majority" else UNANIMOUS_PROGRAM


def _strict_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not grid or len(grid) > 30 or type(grid[0]) is not list
            or not grid[0] or len(grid[0]) > 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be a 1..30 rectangular exact-integer grid")
    return grid


def split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    _strict_grid(grid)
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(separators) != 2:
        raise ValueError("input needs exactly two full color-9 separator columns")
    a, b = separators
    panels = [[row[:a] for row in grid], [row[a + 1:b] for row in grid], [row[b + 1:] for row in grid]]
    shapes = {(len(panel), len(panel[0]) if panel and panel[0] else 0) for panel in panels}
    if len(shapes) != 1 or 0 in next(iter(shapes)):
        raise ValueError("three panels must have equal positive dimensions")
    return panels


def aggregate(grid: list[list[int]], settings: dict[str, Any]) -> list[list[bool]]:
    policy = settings_value(settings)["vote_policy"]
    panels = split_panels(grid)
    h, w = len(panels[0]), len(panels[0][0])
    threshold = 2 if policy == "majority" else 3
    return [[sum(panel[r][c] != 0 for panel in panels) >= threshold for c in range(w)] for r in range(h)]


def _components(mask: list[list[bool]]) -> list[set[tuple[int, int]]]:
    h, w = len(mask), len(mask[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if mask[r][c]}
    result = []
    while unseen:
        first = min(unseen); unseen.remove(first)
        stack = [first]; cells = {first}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point); cells.add(point); stack.append(point)
        result.append(cells)
    return result


def depth_map(mask: list[list[bool]]) -> list[list[int]]:
    h, w = len(mask), len(mask[0])
    layers = [[0 for _ in range(w)] for _ in range(h)]
    for component in _components(mask):
        current = set(component); depth = 1
        while current:
            boundary = {point for point in current if any((point[0] + dr, point[1] + dc) not in current
                                                          for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))}
            for r, c in boundary:
                layers[r][c] = depth
            current -= boundary; depth += 1
    cells = [(r, c) for r in range(h) for c in range(w) if layers[r][c] != 0]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in layers[r0:r1 + 1]]


def intermediate(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    mask = aggregate(grid, settings)
    return {"vote_policy": settings_value(settings)["vote_policy"],
            "mask": [[1 if value else 0 for value in row] for row in mask],
            "occupied_cells": sum(value for row in mask for value in row)}


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    return depth_map(aggregate(grid, settings))


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    majority = aggregate(grid, {"vote_policy": "majority"})
    unanimous = aggregate(grid, {"vote_policy": "unanimous"})
    panels = split_panels(grid)
    disagreements = sum(len({panel[r][c] != 0 for panel in panels}) > 1
                        for r in range(len(panels[0])) for c in range(len(panels[0][0])))
    return {"majority_cells": sum(v for row in majority for v in row),
            "unanimous_cells": sum(v for row in unanimous for v in row),
            "disagreements": disagreements,
            "panel_shape": [len(panels[0]), len(panels[0][0])]}


def _rng(seed: int, domain: str, index: int) -> random.Random:
    payload = json.dumps([TASK_ID, SCHEMA, seed, domain, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _base_mask(h: int, w: int, index: int) -> list[list[bool]]:
    top = max(1, h // 9); bottom = h - 1 - max(1, h // 10)
    left = 1; right = w - 2
    mask = [[False for _ in range(w)] for _ in range(h)]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            mask[r][c] = True
    # Shape-dependent boundary cuts preserve a thick connected core while
    # varying topology and preventing a fixed bounding-box shortcut.
    cuts = 1 + index % 3
    for offset in range(cuts):
        if top + offset <= bottom:
            mask[top + offset][left] = False
        if bottom - offset >= top:
            mask[bottom - offset][right] = False
    if index % 2 and bottom - top >= 5:
        mid = (top + bottom) // 2
        mask[mid][left] = False
        mask[mid][right] = False
    return mask


def _boundary(mask: list[list[bool]]) -> list[tuple[int, int]]:
    h, w = len(mask), len(mask[0])
    return [(r, c) for r in range(h) for c in range(w) if mask[r][c]
            and any(not (0 <= r + dr < h and 0 <= c + dc < w) or not mask[r + dr][c + dc]
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))]


def _connected_cells(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    unseen = set(cells)
    stack = [unseen.pop()]
    reached = 1
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (r + dr, c + dc)
            if point in unseen:
                unseen.remove(point)
                stack.append(point)
                reached += 1
    return reached == len(cells)


def _connected_fringe(mask: list[list[bool]], rng: random.Random, count: int) -> list[tuple[int, int]]:
    """Choose boundary omissions while preserving a connected unanimous core."""
    candidates = _boundary(mask)
    rng.shuffle(candidates)
    remaining = {(r, c) for r, row in enumerate(mask) for c, value in enumerate(row) if value}
    selected: list[tuple[int, int]] = []
    for point in candidates:
        trial = remaining - {point}
        if len(trial) >= 4 and _connected_cells(trial):
            selected.append(point)
            remaining = trial
            if len(selected) == count:
                return selected
    raise ValueError("profile cannot supply enough connectivity-safe fringe cells")


def sample_input(seed: int, domain: str, index: int, profile: tuple[int, int]) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    h, w = profile
    if not (5 <= h <= 30 and 5 <= w <= 9):
        raise ValueError("unsupported panel profile")
    rng = _rng(seed, domain, index)
    mask = _base_mask(h, w, index)
    panels = [[[0 for _ in range(w)] for _ in range(h)] for _ in range(3)]
    for r in range(h):
        for c in range(w):
            if mask[r][c]:
                for panel in panels:
                    panel[r][c] = 1
    boundary_count = len(_boundary(mask))
    fringe_count = max(2, min(boundary_count // 3, 2 + h // 4))
    fringe = _connected_fringe(mask, rng, fringe_count)
    for j, (r, c) in enumerate(fringe):
        panels[(j + index) % 3][r][c] = 0
    outside = [(r, c) for r in range(h) for c in range(w) if not mask[r][c]]
    rng.shuffle(outside)
    for j, (r, c) in enumerate(outside[:max(1, min(4, h // 8 + 1))]):
        panels[(j + 1 + index) % 3][r][c] = 1
    grid = [[0 for _ in range(3 * w + 2)] for _ in range(h)]
    for r in range(h):
        grid[r][w] = 9; grid[r][2 * w + 1] = 9
    for panel_index, panel in enumerate(panels):
        left = panel_index * (w + 1)
        for r in range(h):
            for c in range(w):
                grid[r][left + c] = panel[r][c]
    info = analyze(grid)
    if info["majority_cells"] <= info["unanimous_cells"] or info["unanimous_cells"] < 4:
        raise ValueError("sampler failed to distinguish vote policies")
    if len(_components(aggregate(grid, {"vote_policy": "unanimous"}))) != 1:
        raise ValueError("unanimous repaired mask must remain connected")
    return grid


def check_teaching(train: list[dict[str, Any]], settings: dict[str, Any]) -> dict[str, Any]:
    chosen = settings_value(settings)["vote_policy"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    survivors = []
    for policy in POLICIES:
        candidate = {"vote_policy": policy}
        if all(type(pair) is dict and {"input", "output"} <= set(pair)
               and transform(pair["input"], candidate) == pair["output"] for pair in train):
            survivors.append(policy)
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify {chosen}; survivors={survivors}")
    return {"fit_scope": "demonstrations_only", "survivors": survivors,
            "declared_settings": list(POLICIES),
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
    report = {"schema": "arcpuzzles-vote-policy-self-audit-v1", "status": "passed", "settings": {}}
    for policy in POLICIES:
        episode = generate(seed, {"vote_policy": policy}, demos=2, queries=4)
        rivals = {
            "first_panel_only": lambda grid: depth_map([[cell != 0 for cell in row] for row in split_panels(grid)[0]]),
            "union": lambda grid: depth_map([[any(panel[r][c] != 0 for panel in split_panels(grid))
                                               for c in range(len(split_panels(grid)[0][0]))]
                                              for r in range(len(split_panels(grid)[0]))]),
            "skip_depth": lambda grid: [[1 if value else 0 for value in row] for row in aggregate(grid, {"vote_policy": policy})],
        }
        rows = {}
        for name, rival in rivals.items():
            mismatches = [i for i, pair in enumerate(episode["train"]) if rival(pair["input"]) != pair["output"]]
            rows[name] = {"rejected": bool(mismatches), "first_demonstration": mismatches[0] if mismatches else None}
            if not mismatches:
                report["status"] = "failed"
        report["settings"][policy] = {"survivors": check_teaching(episode["train"], {"vote_policy": policy})["survivors"], "rivals": rows}
    if report["status"] != "passed":
        raise ValueError("bounded vote-policy audit found a surviving shortcut")
    return report
