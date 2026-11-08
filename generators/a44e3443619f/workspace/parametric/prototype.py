"""Proposed single-pass/cascade family for a44e3443619f.

The canonical ``single`` setting is byte-for-byte the selected source rule:
fill every zero centre of a red diagonal X with blue.  The ``cascade`` setting
first performs that exact pass, then recolours a red cell green when the newly
blue intermediate supplies all four of its immediate diagonal neighbours.

Inputs are sampled independently of the hidden setting.  Complete 5x5 red
lattices create four first-pass centres surrounding one second-pass target;
near-identical eight-cell lattices create only three centres and are retained as
negative controls.  Protected Racket remains the label authority during native
preflight; the Python implementation is a tested mirror and authoring oracle.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "a44e3443619f"
PARAMETER = "completion_depth"
PARAMETERS = {PARAMETER: ["single", "cascade"]}
DEFAULT = {PARAMETER: "single"}
SETTINGS = tuple({PARAMETER: value} for value in PARAMETERS[PARAMETER])
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERIES = 4
MAX_SEED = 2**63 - 1

HERE = Path(__file__).resolve().parent

_CANONICAL = """(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (= (at g r c) 0)
               (all? (lambda (d) (= (safe-at g (+ r (first d)) (+ c (second d)) 0) 2)) diagonal-deltas))
          1
          (at g r c)))))"""
_CASCADE = (HERE / "cascade.rkt").read_text(encoding="utf-8").rstrip("\n")
_PROGRAMS = {"single": _CANONICAL, "cascade": _CASCADE}
_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_OUTER_CORNERS = ((0, 0), (0, 4), (4, 0), (4, 4))

# (height, width, role counts).  The first two profiles deliberately keep
# dimensions fixed while changing the number of causal targets.
_TRAIN_PROFILES = (
    (13, 17, {"complete": 1, "incomplete": 1, "standalone": 1, "partial": 1}),
    (13, 17, {"complete": 2, "incomplete": 1, "standalone": 1, "partial": 0}),
    (17, 13, {"complete": 2, "incomplete": 1, "standalone": 1, "partial": 0}),
    (17, 17, {"complete": 2, "incomplete": 1, "standalone": 1, "partial": 0}),
    (23, 25, {"complete": 4, "incomplete": 2, "standalone": 2, "partial": 1}),
    (29, 27, {"complete": 5, "incomplete": 3, "standalone": 2, "partial": 2}),
)
_QUERY_PROFILES = (
    (9, 17, {"complete": 1, "incomplete": 0, "standalone": 1, "partial": 0}),
    (17, 9, {"complete": 1, "incomplete": 1, "standalone": 0, "partial": 0}),
    (23, 23, {"complete": 4, "incomplete": 2, "standalone": 2, "partial": 1}),
    (30, 30, {"complete": 8, "incomplete": 4, "standalone": 2, "partial": 2}),
)


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _strict_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in PARAMETERS[PARAMETER]:
        raise ValueError(f"{PARAMETER} must be one of {PARAMETERS[PARAMETER]!r}")
    return {PARAMETER: value}


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 by 1..30 list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer ARC colours")
    return grid


def program(settings: object) -> str:
    return _PROGRAMS[_settings(settings)[PARAMETER]]


def stage_one(grid: list[list[int]]) -> list[list[int]]:
    """Canonical red-X completion pass."""
    _grid(grid)
    h, w = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and all(grid[r + dr][c + dc] == 2 for dr, dc in _DIAGONALS):
                output[r][c] = 1
    return output


def _target_cells(intermediate: list[list[int]]) -> set[tuple[int, int]]:
    _grid(intermediate)
    h, w = len(intermediate), len(intermediate[0])
    return {
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if intermediate[r][c] == 2
        and all(intermediate[r + dr][c + dc] == 1 for dr, dc in _DIAGONALS)
    }


def stage_two(intermediate: list[list[int]]) -> list[list[int]]:
    """Consume the first-pass grid and recolour every supported red target."""
    _grid(intermediate)
    targets = _target_cells(intermediate)
    return [
        [3 if (r, c) in targets else value for c, value in enumerate(row)]
        for r, row in enumerate(intermediate)
    ]


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    chosen = _settings(settings)[PARAMETER]
    first = stage_one(grid)
    return first if chosen == "single" else stage_two(first)


def _paint_cell(grid: list[list[int]], r: int, c: int) -> None:
    if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
        raise ValueError(f"motif cell {(r, c)} is outside the grid")
    if grid[r][c] not in (0, 2):
        raise ValueError("motifs may only occupy background/red cells")
    grid[r][c] = 2


def _paint_complete(grid: list[list[int]], top: int, left: int) -> None:
    for dr in (0, 2, 4):
        for dc in (0, 2, 4):
            _paint_cell(grid, top + dr, left + dc)


def _paint_incomplete(grid: list[list[int]], top: int, left: int, missing: tuple[int, int]) -> None:
    if missing not in _OUTER_CORNERS:
        raise ValueError("incomplete motif must omit one outer lattice corner")
    for dr in (0, 2, 4):
        for dc in (0, 2, 4):
            if (dr, dc) != missing:
                _paint_cell(grid, top + dr, left + dc)


def _paint_x(grid: list[list[int]], top: int, left: int, *, missing: tuple[int, int] | None = None) -> None:
    corners = ((0, 0), (0, 2), (2, 0), (2, 2))
    if missing is not None and missing not in corners:
        raise ValueError("partial X must omit one X corner")
    for dr, dc in corners:
        if (dr, dc) != missing:
            _paint_cell(grid, top + dr, left + dc)


def make_control_scene(
    height: int,
    width: int,
    *,
    complete: list[tuple[int, int]] | tuple[tuple[int, int], ...] = (),
    incomplete: list[tuple[int, int]] | tuple[tuple[int, int], ...] = (),
    standalone: list[tuple[int, int]] | tuple[tuple[int, int], ...] = (),
    partial: list[tuple[int, int]] | tuple[tuple[int, int], ...] = (),
    nuisance: list[tuple[int, int]] | tuple[tuple[int, int], ...] = (),
) -> list[list[int]]:
    """Build a small explicit audit scene from motif top-left coordinates."""
    _strict_int("height", height, 1, 30)
    _strict_int("width", width, 1, 30)
    grid = [[0] * width for _ in range(height)]
    for top, left in complete:
        _paint_complete(grid, top, left)
    for index, (top, left) in enumerate(incomplete):
        _paint_incomplete(grid, top, left, _OUTER_CORNERS[index % 4])
    for top, left in standalone:
        _paint_x(grid, top, left)
    for index, (top, left) in enumerate(partial):
        _paint_x(grid, top, left, missing=((0, 0), (0, 2), (2, 0), (2, 2))[index % 4])
    for r, c in nuisance:
        _paint_cell(grid, r, c)
    return grid


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    """Return semantic counts used by tests/certificates, not private labels."""
    _grid(grid)
    first = stage_one(grid)
    new_blue = {
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0 and first[r][c] == 1
    }
    targets = _target_cells(first)
    near_misses: set[tuple[int, int]] = set()
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if first[r][c] == 2 and sum(first[r + dr][c + dc] == 1 for dr, dc in _DIAGONALS) == 3:
                near_misses.add((r, c))
    clustered_blue = {
        (r + dr, c + dc)
        for r, c in targets | near_misses
        for dr, dc in _DIAGONALS
        if (r + dr, c + dc) in new_blue
    }
    return {
        "shape": [len(grid), len(grid[0])],
        "stage_one_centers": len(new_blue),
        "cascade_targets": len(targets),
        "target_cells": sorted(targets),
        "incomplete_motifs": len(near_misses),
        "near_miss_cells": sorted(near_misses),
        "standalone_x": len(new_blue - clustered_blue),
        "occupied": sum(cell != 0 for row in grid for cell in row),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|cascade-scenes-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _slots(height: int, width: int) -> list[tuple[int, int]]:
    rows = list(range(0, height - 4, 8))
    cols = list(range(0, width - 4, 8))
    return [(r, c) for r in rows for c in cols]


def _jittered_origin(height: int, width: int, slot: tuple[int, int], rng: random.Random) -> tuple[int, int]:
    r, c = slot
    max_jitter = min(1, height - 5 - r, width - 5 - c)
    jitter_r = rng.randint(0, max_jitter) if max_jitter >= 0 else 0
    jitter_c = rng.randint(0, max_jitter) if max_jitter >= 0 else 0
    return r + jitter_r, c + jitter_c


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, counts = profiles[index]
    rng = _rng(seed, split, index)
    slots = _slots(height, width)
    roles = [role for role in ("complete", "incomplete", "standalone", "partial")
             for _ in range(counts[role])]
    if len(roles) != len(slots):
        raise RuntimeError(f"profile role/slot mismatch for {split}[{index}]")

    assignments: list[tuple[str, tuple[int, int], int]] = []
    if split == "test" and index == 3:
        # Preserve genuine 30x30 boundary contact at both ends while randomising
        # all remaining roles independently of the hidden setting.
        low = (0, 0)
        high = (24, 24)
        assignments.extend([("complete", low, 0), ("complete", high, 1)])
        slots = [slot for slot in slots if slot not in {low, high}]
        roles.remove("complete")
        roles.remove("complete")
        rng.shuffle(slots)
        rng.shuffle(roles)
        assignments.extend((role, slot, -1) for role, slot in zip(roles, slots))
    else:
        rng.shuffle(slots)
        rng.shuffle(roles)
        assignments.extend((role, slot, -1) for role, slot in zip(roles, slots))

    grid = [[0] * width for _ in range(height)]
    for ordinal, (role, slot, forced_jitter) in enumerate(assignments):
        if forced_jitter == 0:
            top, left = slot
        elif forced_jitter == 1:
            top, left = slot[0] + 1, slot[1] + 1
        else:
            top, left = _jittered_origin(height, width, slot, rng)
        if role == "complete":
            _paint_complete(grid, top, left)
        elif role == "incomplete":
            _paint_incomplete(grid, top, left, _OUTER_CORNERS[rng.randrange(4)])
        elif role == "standalone":
            _paint_x(grid, top, left)
        elif role == "partial":
            _paint_x(grid, top, left, missing=((0, 0), (0, 2), (2, 0), (2, 2))[rng.randrange(4)])
        else:  # pragma: no cover - internal profile guard
            raise RuntimeError(role)

    analysis = analyze_scene(grid)
    expected_stage_one = 4 * counts["complete"] + 3 * counts["incomplete"] + counts["standalone"]
    expected = {
        "stage_one_centers": expected_stage_one,
        "cascade_targets": counts["complete"],
        "incomplete_motifs": counts["incomplete"],
        "standalone_x": counts["standalone"],
    }
    observed = {key: analysis[key] for key in expected}
    if observed != expected:
        raise RuntimeError(f"scene profile interaction: expected {expected}, observed {observed}")
    return grid


def _shortcut(name: str, grid: list[list[int]]) -> list[list[int]]:
    first = stage_one(grid)
    targets = sorted(_target_cells(first))
    if name == "skip_stage_one":
        return stage_two(grid)
    if name == "all_blue_green":
        return [[3 if value == 1 else value for value in row] for row in first]
    if name == "fixed_grid_center":
        output = [row[:] for row in first]
        r, c = len(output) // 2, len(output[0]) // 2
        output[r][c] = 3
        return output
    if name in {"first_target_only", "last_target_only"}:
        output = [row[:] for row in first]
        if targets:
            r, c = targets[0 if name == "first_target_only" else -1]
            output[r][c] = 3
        return output
    if name == "green_every_red":
        return [[3 if value == 2 else value for value in row] for row in first]
    raise KeyError(name)


SHORTCUTS = (
    "skip_stage_one",
    "all_blue_green",
    "fixed_grid_center",
    "first_target_only",
    "last_target_only",
    "green_every_red",
)


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    if not MIN_DEMOS <= len(train) <= MAX_DEMOS:
        raise ValueError("demonstration count must be in 2..6")
    if len(test) != QUERIES:
        raise ValueError("query count must be exactly four")
    pairs = train + test
    inputs: list[str] = []
    for pair in pairs:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each pair must contain input and output")
        _grid(pair["input"])
        _grid(pair["output"])
        inputs.append(digest(pair["input"]))
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration and query inputs must be distinct")

    if execute is None:
        apply = lambda text, grid: transform(
            grid, next(setting for setting in SETTINGS if program(setting) == text)
        )
    else:
        apply = execute

    records = []
    for setting in SETTINGS:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if apply(program(setting), pair["input"]) != pair["output"]
        ]
        records.append({"settings": dict(setting), "disagreeing_demo_indices": disagreements})
    survivors = [row["settings"] for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected completion depth: {survivors}")

    shortcut_disagreements: dict[str, list[int]] = {}
    shortcut_survivors: list[str] = []
    for name in SHORTCUTS:
        disagreements = [
            index for index, pair in enumerate(train)
            if _shortcut(name, pair["input"]) != pair["output"]
        ]
        shortcut_disagreements[name] = disagreements
        if not disagreements:
            shortcut_survivors.append(name)
    if shortcut_survivors:
        raise ValueError(f"declared wrong shortcuts survive demonstrations: {shortcut_survivors}")

    query_rows = []
    for index, pair in enumerate(test):
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError(f"query label disagrees with fixed setting at index {index}")
        query_rows.append({
            "input_sha256": digest(pair["input"]),
            "output_sha256": digest(pair["output"]),
            "analysis": analyze_scene(pair["input"]),
        })
    return {
        "status": "pass",
        "survivors": survivors,
        "setting_disagreements": records,
        "shortcut_disagreements": shortcut_disagreements,
        "shortcut_survivors": shortcut_survivors,
        "queries": query_rows,
        "train_analysis": [analyze_scene(pair["input"]) for pair in train],
    }


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, QUERIES, QUERIES)
    chosen = _settings(settings)
    train = []
    for index in range(demos):
        grid = _scene(seed, "train", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(queries):
        grid = _scene(seed, "test", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    episode: dict[str, Any] = {
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
    }
    episode["certificate"] = certify(episode)
    return episode


def crossed_controls() -> dict[str, list[dict[str, Any]]]:
    """Small explicit controls retained by the adversarial audit."""
    varying = [
        make_control_scene(13, 13, complete=[(0, 0)], incomplete=[(0, 8)], standalone=[(9, 1)]),
        make_control_scene(13, 13, complete=[(0, 0), (8, 8)], incomplete=[(0, 8)], standalone=[(9, 1)]),
    ]
    nuisance = [
        make_control_scene(13, 13, complete=[(0, 0), (8, 8)], incomplete=[(0, 8)], standalone=[(9, 1)], nuisance=[(6, 6)]),
        make_control_scene(13, 13, complete=[(0, 0), (8, 8)], incomplete=[(0, 8)], standalone=[(9, 1)], nuisance=[(6, 5)]),
    ]
    return {
        "different_intermediate_same_profile": [
            {"input": grid, "analysis": analyze_scene(grid)} for grid in varying
        ],
        "same_targets_different_nuisance": [
            {"input": grid, "analysis": analyze_scene(grid)} for grid in nuisance
        ],
    }
