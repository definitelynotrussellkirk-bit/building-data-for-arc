"""Matched-input direct sweep versus first-hit relay parametric family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator

TASK_ID = "e64c021e29ad"
VERSION = "1.0.0"
DIRECT = {"sweep_mode": "all"}
RELAY = {"sweep_mode": "first_hit_relay"}
SETTINGS = (DIRECT, RELAY)
_DIRS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
_DEMO_SIZES = ((10, 12), (12, 14), (14, 16), (16, 18), (18, 20), (20, 22))
_QUERY_SIZES = ((11, 15), (17, 21), (24, 27), (30, 30))
_HOME = Path(__file__).resolve().parent
_CANONICAL = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
_RELAY_PROGRAM = (_HOME / "relay.rkt").read_text(encoding="utf-8")
_BASE, _BASE_PATH, _BASE_SHA256 = load_selected_generator(TASK_ID, root=find_root(__file__))


def _mode(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"sweep_mode"}
            or type(settings["sweep_mode"]) is not str
            or settings["sweep_mode"] not in {"all", "first_hit_relay"}):
        raise ValueError("settings must contain only sweep_mode=all|first_hit_relay")
    return settings["sweep_mode"]


def program(settings) -> str:
    return _CANONICAL if _mode(settings) == "all" else _RELAY_PROGRAM


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list
            or len(row) != len(grid[0]) or any(type(value) is not int or not 0 <= value <= 9
            for value in row) for row in grid)):
        raise ValueError("expected a rectangular 1..30 grid of exact integer colors 0..9")
    return grid


def _records(grid):
    _grid(grid)
    records = _BASE._component_records(grid)
    colors = [int(record["color"]) for record in records]
    if len(records) < 3 or len(colors) != len(set(colors)) or colors.count(9) != 1:
        raise ValueError("expected at least three distinct-color objects including exactly one color-9 probe")
    markers = set()
    for record in records:
        if len(record["markers"]) != 1 or record["code"] not in _DIRS:
            raise ValueError("every object needs exactly one adjacent direction code")
        marker = next(iter(record["markers"]))
        if marker in markers:
            raise ValueError("direction code cannot be shared by two objects")
        markers.add(marker)
    arrow_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value in _DIRS}
    if markers != arrow_cells:
        raise ValueError("all direction codes must belong to exactly one object")
    probe = next(record for record in records if int(record["color"]) == 9)
    if len(probe["cells"]) != 1:
        raise ValueError("the relay probe must be a singleton object")
    return records


def _sweep_cells(cells, code, height, width):
    dr, dc = _DIRS[int(code)]
    result = set()
    for row, col in cells:
        r, c = row, col
        while 0 <= r < height and 0 <= c < width:
            result.add((r, c))
            r += dr
            c += dc
    return sorted(result)


def _paint(height, width, path, color, base=None):
    out = [[0] * width for _ in range(height)] if base is None else [row[:] for row in base]
    for row, col in path:
        out[row][col] = int(color)
    return out


def _direct(grid):
    _records(grid)
    return _BASE._paint_sweep(grid, lambda record: int(record["code"]))


def _trace(grid):
    records = _records(grid)
    probe = next(record for record in records if int(record["color"]) == 9)
    probe_cell = tuple(probe["cells"])[0]
    probe_code = int(probe["code"])
    dr, dc = _DIRS[probe_code]
    by_cell = {cell: record for record in records for cell in record["cells"]}
    path = [probe_cell]
    hits = []
    hit_positions = []
    seen = set()
    row, col = probe_cell[0] + dr, probe_cell[1] + dc
    first_hit = None
    while 0 <= row < len(grid) and 0 <= col < len(grid[0]):
        record = by_cell.get((row, col))
        if record is not None and int(record["color"]) != 9:
            key = int(record["color"])
            if key not in seen:
                seen.add(key)
                hits.append(record)
                hit_positions.append((row, col))
            if first_hit is None:
                first_hit = (row, col)
        elif first_hit is None:
            path.append((row, col))
        row += dr
        col += dc
    if not hits:
        raise ValueError("probe ray must hit at least one other object")
    return {
        "records": records,
        "probe": probe,
        "probe_cell": probe_cell,
        "probe_code": probe_code,
        "path": path,
        "hits": hits,
        "hit_positions": hit_positions,
    }


def relay_intermediate(grid):
    trace = _trace(grid)
    target, last = trace["hits"][0], trace["hits"][-1]
    return {
        "probe_code": trace["probe_code"],
        "hit_position": list(trace["hit_positions"][0]),
        "hit_color": int(target["color"]),
        "target_code": int(target["code"]),
        "last_hit_color": int(last["color"]),
        "path_length": len(trace["path"]),
    }


def _relay(grid, *, target="first", direction="target", include_path=True, include_target=True):
    trace = _trace(grid)
    nonprobe = [record for record in trace["records"] if int(record["color"]) != 9]
    if target == "first":
        selected = trace["hits"][0]
    elif target == "last":
        selected = trace["hits"][-1]
    elif target == "nearest":
        pr, pc = trace["probe_cell"]
        selected = min(nonprobe, key=lambda record: (
            min(abs(r-pr) + abs(c-pc) for r, c in record["cells"]), int(record["color"])))
    elif isinstance(target, int):
        selected = next(record for record in nonprobe if int(record["color"]) == target)
    else:
        raise ValueError("unknown relay target")
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    if include_path:
        out = _paint(height, width, trace["path"], 9, out)
    if include_target:
        code = int(selected["code"]) if direction == "target" else trace["probe_code"]
        out = _paint(height, width, _sweep_cells(selected["cells"], code, height, width), selected["color"], out)
    return out


def solve(grid, settings):
    return _direct(grid) if _mode(settings) == "all" else _relay(grid)


def _relay_rivals(grid):
    return {
        "direct_all": _direct(grid),
        "last_hit_object": _relay(grid, target="last"),
        "nearest_object": _relay(grid, target="nearest"),
        "use_probe_code_for_target": _relay(grid, direction="probe"),
        "omit_probe_path": _relay(grid, include_path=False),
        "probe_path_only": _relay(grid, include_target=False),
        **{f"fixed_target_color_{color}": _relay(grid, target=color) for color in range(5, 9)},
    }


def _direct_rivals(grid):
    return {
        "first_hit_relay": _relay(grid),
        "marker_side_sweep": _BASE._rival_marker_side(grid),
        "object_color_direction": _BASE._rival_object_color(grid),
        "bounding_box_sweep": _BASE._rival_bounding_box(grid),
        "ignore_color_9": _BASE._rival_ignore_color_9(grid),
        "largest_object_only": _BASE._rival_largest_only(grid),
        "fixed_up": _BASE._rival_fixed_up(grid),
    }


def rival_outputs(grid, settings):
    return _direct_rivals(grid) if _mode(settings) == "all" else _relay_rivals(grid)


def lesson_report(episode, settings):
    mode = _mode(settings)
    train, test = episode["train"], episode["test"]
    if not train or not test:
        raise ValueError("lesson needs demonstrations and queries")
    setting_survivors = []
    for candidate in SETTINGS:
        if all(solve(pair["input"], candidate) == pair["output"] for pair in train):
            setting_survivors.append(deepcopy(candidate))
    names = sorted(rival_outputs(train[0]["input"], settings))
    survivors = set(names)
    rejected = {}
    for index, pair in enumerate(train):
        for name, prediction in rival_outputs(pair["input"], settings).items():
            if prediction != pair["output"]:
                survivors.discard(name)
                rejected.setdefault(name, index)
    disagreements = []
    for name in sorted(survivors):
        if any(rival_outputs(pair["input"], settings)[name] != pair["output"] for pair in test):
            disagreements.append(name)
    all_pairs = train + test
    equivalent = [
        name for name in names
        if all(rival_outputs(pair["input"], settings)[name] == pair["output"]
               for pair in all_pairs)
    ]
    return {
        "mode": mode,
        "setting_survivors": setting_survivors,
        "rival_count": len(names),
        "rejected_by_demo": rejected,
        "demo_survivors": sorted(survivors),
        "surviving_query_disagreements": disagreements,
        "equivalent_rivals": equivalent,
        "scope": ("finite direct/relay setting check plus task-local structural rivals; "
                  "equivalent_rivals are observed label-equivalent, not claimed rejected"),
    }


def _seeded(seed, role, index, attempt):
    raw = json.dumps([TASK_ID, VERSION, seed, role, index, attempt], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest(), "big"))


def _add(origin, forward, lateral, d, q):
    return origin[0] + forward*d[0] + lateral*q[0], origin[1] + forward*d[1] + lateral*q[1]


def _shape(anchor, offsets, d, q):
    return frozenset(_add(anchor, forward, lateral, d, q) for forward, lateral in offsets)


def _inside(cells, height, width):
    return all(0 <= row < height and 0 <= col < width for row, col in cells)


def _separated(objects):
    for index, left in enumerate(objects):
        for right in objects[index+1:]:
            if any(abs(r-rr) + abs(c-cc) <= 1 for r, c in left["cells"] for rr, cc in right["cells"]):
                return False
    return True


def _marker_candidates(obj, side):
    dr, dc = _DIRS[side]
    return sorted({(r+dr, c+dc) for r, c in obj["cells"] if (r+dr, c+dc) not in obj["cells"]})


def _assign_markers(objects, height, width, protected, rng):
    occupied = set().union(*(obj["cells"] for obj in objects))
    chosen = set()
    for index, obj in enumerate(objects):
        code = int(obj["code"])
        sides = [((code + offset - 1) % 4) + 1 for offset in (1, 2, 3)]
        sides = sides[index % len(sides):] + sides[:index % len(sides)]
        candidates = []
        for side in sides:
            values = _marker_candidates(obj, side)
            rng.shuffle(values)
            candidates.extend((side, cell) for cell in values)
        for side, cell in candidates:
            if not (0 <= cell[0] < height and 0 <= cell[1] < width):
                continue
            if cell in occupied or cell in chosen or cell in protected:
                continue
            if any(cell in {(r+dr, c+dc) for dr, dc in _DIRS.values() for r, c in other["cells"]}
                   for other in objects if other is not obj):
                continue
            obj["marker"] = cell
            obj["marker_side"] = side
            chosen.add(cell)
            break
        else:
            raise ValueError("could not assign independent marker")


def _scene(seed, role, index, attempt=0):
    sizes = _DEMO_SIZES if role == "demo" else _QUERY_SIZES
    height, width = sizes[index]
    rng = _seeded(seed, role, index, attempt)
    direction = 1 + rng.randrange(4)
    d = _DIRS[direction]
    q = (-d[1], d[0])
    axis = height if d[0] else width
    perpendicular = width if d[0] else height
    span = max(3, perpendicular // 2 - 3)
    mid = perpendicular // 2 + rng.choice((-1, 0, 1))
    mid = min(perpendicular - span - 2, max(span + 1, mid))
    if direction == 1:
        probe = (height - 2, mid)
    elif direction == 2:
        probe = (mid, 1)
    elif direction == 3:
        probe = (1, mid)
    else:
        probe = (mid, width - 2)
    target_distance = max(4, axis // 2 - 1)
    far_distance = min(axis - 3, target_distance + max(3, axis // 4))
    near_lateral = max(2, span - 2)
    target_anchor = _add(probe, target_distance, 0, d, q)
    far_anchor = _add(probe, far_distance, 0, d, q)
    near_anchor = _add(probe, 1, near_lateral, d, q)
    wide_anchor = _add(probe, target_distance - 1, -span, d, q)
    role_offset = 0 if role == "demo" else 2
    target_color = 5 + ((seed + index + role_offset) % 4)
    remaining = [color for color in range(5, 9) if color != target_color]
    rng.shuffle(remaining)
    colors = [target_color, *remaining]
    turn = 1 if (seed + index + role_offset) % 2 == 0 else 3
    target_code = ((direction - 1 + turn) % 4) + 1
    objects = [
        {"color": 9, "code": direction, "cells": frozenset({probe})},
        {"color": colors[0], "code": target_code,
         "cells": _shape(target_anchor, ((0, 0), (0, 1), (1, 0)), d, q)},
        {"color": colors[1], "code": ((direction + 1) % 4) + 1,
         "cells": _shape(far_anchor, ((0, 0), (0, -1)), d, q)},
        {"color": colors[2], "code": ((direction + 2) % 4) + 1,
         "cells": _shape(near_anchor, ((0, 0), (1, 0), (1, 1)), d, q)},
        {"color": colors[3], "code": ((direction + 3) % 4) + 1,
         "cells": _shape(wide_anchor, ((0, 0), (0, 1), (1, 0), (1, 1)), d, q)},
    ]
    if any(not _inside(obj["cells"], height, width) for obj in objects) or not _separated(objects):
        raise ValueError("scene geometry did not fit")
    protected = set()
    r, c = probe[0] + d[0], probe[1] + d[1]
    while 0 <= r < height and 0 <= c < width:
        protected.add((r, c)); r += d[0]; c += d[1]
    _assign_markers(objects, height, width, protected, rng)
    grid = [[0] * width for _ in range(height)]
    for obj in objects:
        for row, col in obj["cells"]:
            grid[row][col] = obj["color"]
        row, col = obj["marker"]
        grid[row][col] = obj["code"]
    _records(grid)
    info = relay_intermediate(grid)
    if (info["hit_color"] != target_color or info["hit_color"] == info["last_hit_color"]
            or info["target_code"] == info["probe_code"]):
        raise ValueError("scene did not preserve relay dependency")
    direct, relay = _direct(grid), _relay(grid)
    if direct == relay:
        raise ValueError("settings are not visibly distinct")
    relay_required = {
        name: value for name, value in _relay_rivals(grid).items()
        if name != f"fixed_target_color_{target_color}"
    }
    if any(value == relay for value in relay_required.values()):
        raise ValueError("scene left a required relay rival equivalent")
    direct_required = {
        name: value for name, value in _direct_rivals(grid).items()
        if name != "bounding_box_sweep"
    }
    if any(value == direct for value in direct_required.values()):
        raise ValueError("scene left a required direct rival equivalent")
    return grid


def _build_scene(seed, role, index):
    for attempt in range(32):
        try:
            return _scene(seed, role, index, attempt)
        except ValueError:
            continue
    raise RuntimeError(f"32 attempts failed for {role} {index}")


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    episode = {"train": [], "test": [], "program_solution": program(settings),
               "settings": {"sweep_mode": mode}}
    for role, split, count in (("demo", "train", demos), ("query", "test", queries)):
        for index in range(count):
            grid = _build_scene(seed, role, index)
            episode[split].append({"input": grid, "output": solve(grid, settings)})
    identities = [json.dumps(pair["input"], separators=(",", ":"))
                  for split in ("train", "test") for pair in episode[split]]
    if len(identities) != len(set(identities)):
        raise RuntimeError("generated duplicate demonstration/query inputs")
    report = lesson_report(episode, settings)
    if report["setting_survivors"] != [{"sweep_mode": mode}]:
        raise RuntimeError(f"setting not identified by demonstrations: {report}")
    if report["surviving_query_disagreements"]:
        raise RuntimeError(f"visible teaching ambiguity: {report['surviving_query_disagreements']}")
    return episode
