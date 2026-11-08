"""Deterministic parametric family for mandatory shortest-path cells.

The canonical setting marks every background cell shared by all shortest paths.
The alternative first derives an input-dependent midpoint mandatory gate, then
marks only cells shared by all shortest paths from that gate to the goal.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "00cccdad1b37"
SCHEMA = "arcpuzzles-shortest-path-parametric-v1"
HOME = Path(__file__).resolve().parent
SEGMENTS = ("whole", "after_gate")
DEMO_PROFILES = ((9, 17), (17, 9), (13, 19), (19, 13), (23, 27), (27, 23))
QUERY_PROFILES = ((7, 13), (16, 20), (24, 27), (30, 30))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"route_segment"}
            or type(settings["route_segment"]) is not str
            or settings["route_segment"] not in SEGMENTS):
        raise ValueError("settings must contain exactly route_segment=whole|after_gate")
    return {"route_segment": settings["route_segment"]}


def program(settings):
    segment = settings_value(settings)["route_segment"]
    filename = "canonical.rkt" if segment == "whole" else "after_gate.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def strict_grid(grid):
    if (type(grid) is not list or not 5 <= len(grid) <= 30
            or type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a 5..30 by 5..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or cell not in {0, 2, 3, 5} for cell in row)
           for row in grid):
        raise ValueError("grid requires exact integer colors from {0,2,3,5}")
    values = [cell for row in grid for cell in row]
    if values.count(2) != 1 or values.count(3) != 1:
        raise ValueError("grid requires exactly one start color 2 and one goal color 3")
    return grid


def _find(grid, color):
    return next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value == color)


def _bfs(grid, start):
    height, width = len(grid), len(grid[0])
    dist = {start: 0}
    ways = {start: 1}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < height and 0 <= nc < width) or grid[nr][nc] == 5:
                continue
            candidate = dist[(r, c)] + 1
            if (nr, nc) not in dist:
                dist[(nr, nc)] = candidate
                ways[(nr, nc)] = ways[(r, c)]
                queue.append((nr, nc))
            elif dist[(nr, nc)] == candidate:
                ways[(nr, nc)] += ways[(r, c)]
    return dist, ways


def _between(grid, start, goal):
    ds, ws = _bfs(grid, start)
    if goal not in ds:
        raise ValueError("start and goal must be connected")
    dg, wg = _bfs(grid, goal)
    best, total = ds[goal], ws[goal]
    mandatory, partial = set(), set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            point = (r, c)
            if value != 0 or point not in ds or point not in dg or ds[point] + dg[point] != best:
                continue
            if ws[point] * wg[point] == total:
                mandatory.add(point)
            else:
                partial.add(point)
    return {"start": start, "goal": goal, "dist": ds, "ways": ws,
            "best": best, "mandatory": mandatory, "partial": partial}


def analyze(grid):
    strict_grid(grid)
    return _between(grid, _find(grid, 2), _find(grid, 3))


def selected_gate(grid):
    result = analyze(grid)
    if not result["mandatory"]:
        raise ValueError("after_gate requires a mandatory background cell")
    best, dist = result["best"], result["dist"]
    return min(result["mandatory"],
               key=lambda point: (abs(2 * dist[point] - best), -dist[point], point))


def _paint(grid, cells):
    result = deepcopy(grid)
    for r, c in cells:
        result[r][c] = 8
    return result


def transform(grid, settings):
    segment = settings_value(settings)["route_segment"]
    result = analyze(grid)
    if segment == "whole":
        return _paint(grid, result["mandatory"])
    gate = selected_gate(grid)
    suffix = _between(grid, gate, result["goal"])["mandatory"]
    return _paint(grid, suffix)


def _rng(seed, domain, index, profile):
    raw = json.dumps([TASK_ID, SCHEMA, seed, domain, index, profile],
                     separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _different_row(rng, height, forbidden):
    choices = [row for row in range(1, height - 1) if row not in forbidden]
    if not choices:
        raise ValueError("not enough rows for distinct route anchors")
    return rng.choice(choices)


def _vertical_board(seed, domain, index, height, width):
    rng = _rng(seed, domain, index, (height, width))
    if width < 11 or height < 7:
        raise ValueError("profile is too small for a multi-gate route")
    count = 2 if width < 15 else (3 if width < 24 else 4)
    columns = [round((i + 1) * (width - 1) / (count + 1)) for i in range(count)]
    columns = [min(width - 3, max(2, col)) for col in columns]
    if len(set(columns)) != count:
        raise ValueError("profile cannot place distinct barriers")
    gaps = rng.sample(list(range(1, height - 1)), count)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col, gap in zip(columns, gaps):
        for row in range(height):
            if row != gap:
                grid[row][col] = 5
    start_row = _different_row(rng, height, {gaps[0]})
    goal_row = _different_row(rng, height, {gaps[-1], start_row})
    reverse = index % 4 in (1, 2)
    if reverse:
        grid[start_row][width - 2] = 2
        grid[goal_row][1] = 3
    else:
        grid[start_row][1] = 2
        grid[goal_row][width - 2] = 3
    return grid


def sample_input(seed, domain, index, profile):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000, "index")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    if (type(profile) not in (tuple, list) or len(profile) != 2
            or any(type(value) is not int for value in profile)):
        raise ValueError("profile must contain exact integer height and width")
    height, width = profile
    integer(height, 7, 30, "height")
    integer(width, 7, 30, "width")
    horizontal = index % 2 == 1
    if horizontal:
        base = _vertical_board(seed, domain, index, width, height)
        grid = [list(row) for row in zip(*base)]
    else:
        grid = _vertical_board(seed, domain, index, height, width)
    strict_grid(grid)
    result = analyze(grid)
    if len(result["mandatory"]) < 2 or not result["partial"]:
        raise ValueError("sampler failed to create multiple gates and partial shortest paths")
    suffix = _between(grid, selected_gate(grid), result["goal"])["mandatory"]
    if not suffix or suffix >= result["mandatory"]:
        raise ValueError("sampler failed to create a strict after-gate suffix")
    return grid


def check_teaching(train, settings):
    chosen = settings_value(settings)["route_segment"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    survivors = []
    for candidate in SEGMENTS:
        setting = {"route_segment": candidate}
        if all(type(pair) is dict and {"input", "output"} <= set(pair)
               and transform(pair["input"], setting) == pair["output"] for pair in train):
            survivors.append(candidate)
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify {chosen}; survivors={survivors}")
    return {"fit_scope": "demonstrations_only", "survivors": survivors,
            "declared_settings": list(SEGMENTS),
            "limits": "Finite declared setting family only; not universal uniqueness."}


def generate(seed, settings, demos=3, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    settings = settings_value(settings)
    result = {"schema": SCHEMA, "task_id": TASK_ID, "seed": seed,
              "settings": settings, "program_solution": program(settings),
              "train": [], "test": []}
    seen = set()
    for split, domain, count, profiles in (("train", "demo", demos, DEMO_PROFILES),
                                            ("test", "query", queries, QUERY_PROFILES)):
        for index in range(count):
            grid = sample_input(seed, domain, index, profiles[index])
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("sampler produced duplicate inputs")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    check_teaching(result["train"], settings)
    return result


def _rival_output(grid, name):
    result = analyze(grid)
    if name == "some_shortest":
        return _paint(grid, result["mandatory"] | result["partial"])
    if name == "straight_line":
        start, goal = result["start"], result["goal"]
        cells = set()
        if start[0] == goal[0]:
            cells = {(start[0], c) for c in range(min(start[1], goal[1]) + 1,
                                                  max(start[1], goal[1])) if grid[start[0]][c] == 0}
        elif start[1] == goal[1]:
            cells = {(r, start[1]) for r in range(min(start[0], goal[0]) + 1,
                                                  max(start[0], goal[0])) if grid[r][start[1]] == 0}
        return _paint(grid, cells)
    if name == "fixed_coordinate_half":
        height, width = len(grid), len(grid[0])
        cells = {p for p in result["mandatory"]
                 if p[0] >= height // 2 or p[1] >= width // 2}
        return _paint(grid, cells)
    if name == "last_gate_only":
        point = max(result["mandatory"], key=lambda p: (result["dist"][p], p))
        return _paint(grid, {point})
    raise ValueError("unknown rival")


def audit(seed=41, demos=3, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    report = {"schema": "arcpuzzles-shortest-path-self-audit-v1", "status": "passed",
              "seed": seed, "demos": demos, "queries": queries, "settings": {}}
    rivals = ("some_shortest", "straight_line", "fixed_coordinate_half", "last_gate_only")
    for chosen in SEGMENTS:
        episode = generate(seed, {"route_segment": chosen}, demos, queries)
        row = {"chosen": chosen, "survivors": check_teaching(
            episode["train"], {"route_segment": chosen})["survivors"],
            "query_count": len(episode["test"]), "rivals": {}}
        for rival in rivals:
            mismatches = [index for index, pair in enumerate(episode["train"])
                          if _rival_output(pair["input"], rival) != pair["output"]]
            row["rivals"][rival] = {"rejected": bool(mismatches),
                                     "first_demonstration": mismatches[0] if mismatches else None}
            if not mismatches:
                report["status"] = "failed"
        report["settings"][chosen] = row
    if report["status"] != "passed":
        raise ValueError("bounded audit found a surviving shortcut")
    return report
