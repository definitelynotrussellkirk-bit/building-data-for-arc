"""Source-bound fill/bridge-selection episodes; proposed until owner acceptance.

The canonical setting fills every one-cell gap between magenta endpoints.  The
composed setting first performs that exact fill, then finds the completed 6/7
components and recolors the component containing the most *newly inserted*
orange bridge cells cyan.  Inputs deliberately decouple component size from
bridge count so a largest-object shortcut is not equivalent to the rule.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "0a0dded71c43"
HOME = Path(__file__).resolve().parent
MODES = ("fill_only", "select_most_bridges")
DEMO_PROFILES = (
    (9, 11, 3),
    (10, 14, 3),
    (12, 16, 4),
    (14, 18, 4),
    (16, 20, 5),
    (18, 22, 5),
)
QUERY_PROFILES = (
    (12, 15, 4),
    (18, 21, 5),
    (24, 27, 6),
    (30, 30, 6),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings: Any) -> dict[str, str]:
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must contain exactly mode=fill_only|select_most_bridges")
    return {"mode": settings["mode"]}


def program(settings: Any) -> str:
    mode = settings_value(settings)["mode"]
    return (HOME / "rules" / f"{mode}.rkt").read_text(encoding="utf-8")


def strict_grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid requires rectangular rows and exact integer colors 0..9")
    return copy.deepcopy(value)


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, "bridge-selection-v1", seed, split, index], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest(), "big"))


def fill_stage(grid: list[list[int]]) -> list[list[int]]:
    grid = strict_grid(grid)
    h, w = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            horizontal = 0 < c < w - 1 and grid[r][c - 1] == grid[r][c + 1] == 6
            vertical = 0 < r < h - 1 and grid[r - 1][c] == grid[r + 1][c] == 6
            if horizontal or vertical:
                out[r][c] = 7
    return out


def _components67(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    grid = strict_grid(grid)
    h, w = len(grid), len(grid[0])
    active = {(r, c) for r in range(h) for c in range(w) if grid[r][c] in (6, 7)}
    result: list[list[tuple[int, int]]] = []
    while active:
        start = min(active)
        active.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in active:
                    active.remove((nr, nc))
                    queue.append((nr, nc))
                    cells.append((nr, nc))
        result.append(sorted(cells))
    return result


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _records(grid: list[list[int]]) -> tuple[list[list[int]], list[dict[str, Any]]]:
    source = strict_grid(grid)
    filled = fill_stage(source)
    records = []
    for cells in _components67(filled):
        bridges = [(r, c) for r, c in cells if source[r][c] == 0 and filled[r][c] == 7]
        if bridges:
            records.append({
                "cells": cells,
                "bridges": bridges,
                "bridge_count": len(bridges),
                "size": len(cells),
                "bbox": _bbox(cells),
            })
    records.sort(key=lambda row: row["bbox"])
    return filled, records


def _winner(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    return max(records, key=lambda row: (row["bridge_count"], row["size"]))


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    selected = settings_value(settings)
    filled, records = _records(grid)
    if selected["mode"] == "fill_only":
        return filled
    winner = _winner(records)
    if winner is None:
        return filled
    out = copy.deepcopy(filled)
    for r, c in winner["cells"]:
        out[r][c] = 8
    return out


def largest_component_rival(grid: list[list[int]]) -> list[list[int]]:
    filled, records = _records(grid)
    if not records:
        return filled
    chosen = max(records, key=lambda row: (row["size"], row["bridge_count"]))
    out = copy.deepcopy(filled)
    for r, c in chosen["cells"]:
        out[r][c] = 8
    return out


def fixed_location_rival(grid: list[list[int]], bbox: tuple[int, int, int, int] | list[int]) -> list[list[int]]:
    filled, records = _records(grid)
    expected = tuple(bbox)
    chosen = next((row for row in records if tuple(row["bbox"]) == expected), None)
    if chosen is None:
        return filled
    out = copy.deepcopy(filled)
    for r, c in chosen["cells"]:
        out[r][c] = 8
    return out


def skip_a_rival(grid: list[list[int]]) -> list[list[int]]:
    return strict_grid(grid)


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    source = strict_grid(grid)
    filled, records = _records(source)
    winner = _winner(records)
    active = [(r, c) for r, row in enumerate(filled) for c, value in enumerate(row)
              if value in (6, 7)]
    if active:
        r0, c0, r1, c1 = _bbox(active)
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
    else:
        bh = bw = 0
    largest = max(records, key=lambda row: row["size"]) if records else None
    return {
        "component_count": len(records),
        "bridge_count": sum(row["bridge_count"] for row in records),
        "bbox_height": bh,
        "bbox_width": bw,
        "winner_bridge_count": 0 if winner is None else winner["bridge_count"],
        "winner_bbox": [] if winner is None else list(winner["bbox"]),
        "largest_component_is_winner": bool(winner and largest and winner["bbox"] == largest["bbox"]),
        "records": [{k: (list(v) if k == "bbox" else v)
                     for k, v in row.items() if k not in {"cells", "bridges"}}
                    for row in records],
    }


def _rows_for(h: int, count: int) -> list[int]:
    if count == 1:
        return [h // 2]
    return [round(i * (h - 1) / (count - 1)) for i in range(count)]


def _place_color_decoy(grid: list[list[int]], rng: random.Random) -> None:
    h, w = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(max(1, h - 1)) for c in range(max(1, w - 1))]
    rng.shuffle(candidates)
    for r, c in candidates:
        cells = [(r + dr, c + dc) for dr in (0, 1) for dc in (0, 1)]
        if all(rr < h and cc < w and grid[rr][cc] == 0 for rr, cc in cells):
            # Keep the block away from magenta so it cannot perturb bridge components.
            halo = [(rr + dr, cc + dc) for rr, cc in cells
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
            if any(0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 6 for rr, cc in halo):
                continue
            color = rng.choice((1, 2, 3, 4, 5, 9))
            for rr, cc in cells:
                grid[rr][cc] = color
            return


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    _integer(index, 0, len(profiles) - 1, "index")
    h, w, count = profiles[index]
    rng = _rng(seed, split, index)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    rows = _rows_for(h, count)

    winner_slot = (seed + index + (0 if split == "demo" else 1)) % count
    size_slot = (winner_slot + 1 + index) % count
    if size_slot == winner_slot:
        size_slot = (size_slot + 1) % count
    remaining_slots = [slot for slot in range(count) if slot not in {winner_slot, size_slot}]
    remaining_counts = list(range(1, count - 1))
    rng.shuffle(remaining_counts)
    bridge_counts = [None] * count
    bridge_counts[winner_slot] = count
    bridge_counts[size_slot] = count - 1
    for slot, bridges in zip(remaining_slots, remaining_counts):
        bridge_counts[slot] = bridges

    for slot, (row, bridges) in enumerate(zip(rows, bridge_counts)):
        assert bridges is not None
        tail = 5 if slot == size_slot else rng.randint(0, 2)
        length = 2 * bridges + 1 + tail
        if length > w:
            raise ValueError("profile cannot fit bridge motif")
        start = 0 if (slot + index + seed) % 2 == 0 else w - length
        for offset in range(0, 2 * bridges + 1, 2):
            grid[row][start + offset] = 6
        for offset in range(2 * bridges + 1, length):
            grid[row][start + offset] = 6

    _place_color_decoy(grid, rng)
    analysis = analyze_input(grid)
    if analysis["component_count"] != count:
        raise ValueError("constructed motifs unexpectedly merged")
    if analysis["largest_component_is_winner"]:
        raise ValueError("size shortcut was not decoupled")
    return grid


def execute_rule(source: str, grid: list[list[int]], *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    own = bridge is None
    runtime = RacketBridge(timeout=60) if own else bridge
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in strict_grid(grid)) + ")"
    try:
        return strict_grid(runtime.eval_text(f"({wrap_rule(source)} {literal})"))
    finally:
        if own:
            runtime.close()


def _execute_python(source: str, grid: list[list[int]]) -> list[list[int]]:
    for mode in MODES:
        if source == program({"mode": mode}):
            return transform(grid, {"mode": mode})
    raise ValueError("unknown program")


def certify(episode: Any, *, execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = settings_value(episode.get("settings"))
    expected_program = program(settings)
    if episode.get("program_solution") != expected_program:
        raise ValueError("program_solution differs from selected setting")
    train, test = episode.get("train"), episode.get("test")
    if not isinstance(train, list) or not 2 <= len(train) <= 6:
        raise ValueError("train count must be 2..6")
    if not isinstance(test, list) or not 1 <= len(test) <= 4:
        raise ValueError("test count must be 1..4")
    pairs = train + test
    normalized = []
    for pair in pairs:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each pair requires input and output")
        normalized.append((strict_grid(pair["input"]), strict_grid(pair["output"])))
    if len({digest(grid) for grid, _ in normalized}) != len(normalized):
        raise ValueError("all demonstration and query inputs must be distinct")
    run = _execute_python if execute is None else execute
    survivors = []
    for mode in MODES:
        source = program({"mode": mode})
        if all(run(source, pair["input"]) == pair["output"] for pair in train):
            survivors.append({"mode": mode})
    if survivors != [settings]:
        raise ValueError(f"demonstrations do not identify selected label rule: {survivors}")
    query_checks = []
    for pair in test:
        actual = run(expected_program, pair["input"])
        matches = actual == pair["output"]
        if not matches:
            raise ValueError("query label differs from selected rule")
        query_checks.append({"input_sha256": digest(pair["input"]), "label_matches": True})
    return {"fit_scope": "demonstrations_only", "survivors": survivors, "queries": query_checks}


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    selected = settings_value(settings)
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    train = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, selected)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, selected)})
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
        "variant_approved": False,
        "training_admitted": False,
    }
    episode["certificate"] = certify(episode)
    return episode
