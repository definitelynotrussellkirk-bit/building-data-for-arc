#!/usr/bin/env python3
"""Native episode-fixed equality/matched-box family for 87754dbb8687.

The default setting is the exact canonical rule.  The alternative is a real
composition: A computes that equality matrix; B consumes only that intermediate,
finds every matched color there, and fills the bounding box of its matched cells.
Inputs are generated independently of the private setting.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "87754dbb8687"
SETTINGS = ({"output_mode": "equality"}, {"output_mode": "match_boxes"})
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
DEMO_SHAPES = ((9, 10), (12, 11), (15, 14), (18, 16), (21, 20), (24, 22))
QUERY_SHAPES = ((10, 13), (17, 15), (23, 27), (30, 30))


def _canonical_program() -> str:
    matches: list[str] = []
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    matches.append(row["program_solution"])
    if not matches or len(set(matches)) != 1:
        raise RuntimeError(f"expected one stable canonical program for {TASK_ID}")
    return matches[0]


CANONICAL_PROGRAM = _canonical_program()
MATCH_BOXES_PROGRAM = r"""(rule!
 ;; A: construct the exact canonical equality matrix from the two headers.
 (let* ((canonical-equality
          (grid-from-fn (- h 1) (- w 1) (lambda (r c)
            (let ((a (at g (+ r 1) 0)) (b (at g 0 (+ c 1))))
              (if (and (!= a 0) (= a b)) a 0)))))
        ;; B sees colors and geometry only through A's intermediate.
        (matched-colors
          (filter (lambda (color) (!= color 0))
                  (grid-colors canonical-equality))))
   (for/fold ((out canonical-equality))
             ((color (in-list matched-colors)))
     (let* ((cells (find-color canonical-equality color))
            (bb (bbox-of-cells cells))
            (r1 (first bb)) (c1 (second bb))
            (r2 (third bb)) (c2 (fourth bb)))
       (cellmap out (r c v)
         (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2))
             color
             v))))))"""


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: dict[str, Any] | None) -> dict[str, str]:
    if value is None:
        value = dict(DEFAULT_SETTINGS)
    if type(value) is not dict or set(value) != {"output_mode"}:
        raise ValueError("settings must name exactly output_mode")
    mode = value["output_mode"]
    if mode not in {"equality", "match_boxes"}:
        raise ValueError("output_mode must be equality or match_boxes")
    return {"output_mode": mode}


def program(settings: dict[str, Any] | None = None) -> str:
    selected = _settings(settings)
    return CANONICAL_PROGRAM if selected["output_mode"] == "equality" else MATCH_BOXES_PROGRAM


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _rng(seed: int, stream: str, index: int) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    raw = f"{TASK_ID}|{seed}|{stream}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _mirror_pair(pair: tuple[int, int], length: int) -> tuple[int, int]:
    return length - 1 - pair[1], length - 1 - pair[0]


def _layout_pairs(height: int, width: int, rng: random.Random) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Return separated row/column pairs whose boxes contain real empty gaps."""
    oh, ow = height - 1, width - 1
    if min(oh, ow) >= 24:
        row_pairs = [(1, 5), (8, 12), (oh - 13, oh - 9), (oh - 6, oh - 2)]
        col_pairs = [(1, 5), (8, 12), (ow - 13, ow - 9), (ow - 6, ow - 2)]
        # One match group in each spatial quadrant.
        mapping = [(0, 0), (1, 2), (2, 1), (3, 3)]
        pairs = [(row_pairs[r], col_pairs[c]) for r, c in mapping]
    else:
        pairs = [((0, min(3, oh - 1)), (0, min(3, ow - 1))),
                 ((max(0, oh - 4), oh - 1), (max(0, ow - 4), ow - 1))]
    if rng.randrange(2):
        pairs = [(_mirror_pair(rows, oh), cols) for rows, cols in pairs]
    if rng.randrange(2):
        pairs = [(rows, _mirror_pair(cols, ow)) for rows, cols in pairs]
    return pairs


def sample_input(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    _integer(height, "height", 5, 30)
    _integer(width, "width", 5, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    _integer(index, "index", 0, 10_000)
    rng = _rng(seed, stream, index)
    pairs = _layout_pairs(height, width, rng)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    shared = colors[: len(pairs)]
    remaining = colors[len(pairs):]
    if len(remaining) < 2:
        raise ValueError("insufficient exclusive colors")
    top_only, left_only = remaining[0], remaining[1]
    top = [top_only] * (width - 1)
    left = [left_only] * (height - 1)
    # Add deterministic visual texture without introducing accidental sharing.
    if len(remaining) >= 4:
        for c in range(1, len(top), 4):
            top[c] = remaining[2]
        for r in range(2, len(left), 5):
            left[r] = remaining[3]
    for color, (row_pair, col_pair) in zip(shared, pairs):
        for r in row_pair:
            left[r] = color
        for c in col_pair:
            top[c] = color
    grid = [[0] * width for _ in range(height)]
    grid[0][1:] = top
    for r, color in enumerate(left, start=1):
        grid[r][0] = color
    return grid


def canonical_equality(grid: list[list[int]]) -> list[list[int]]:
    if type(grid) is not list or len(grid) < 2 or type(grid[0]) is not list or len(grid[0]) < 2:
        raise ValueError("input must be a rectangular header grid")
    width = len(grid[0])
    if width > 30 or len(grid) > 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("input must be rectangular and at most 30x30")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact ARC colors")
    top = grid[0][1:]
    return [[grid[r][0] if grid[r][0] != 0 and grid[r][0] == top[c] else 0
             for c in range(width - 1)] for r in range(1, len(grid))]


def match_boxes_from_intermediate(intermediate: list[list[int]]) -> list[list[int]]:
    if type(intermediate) is not list or not intermediate or type(intermediate[0]) is not list or not intermediate[0]:
        raise ValueError("intermediate must be a nonempty rectangular grid")
    width = len(intermediate[0])
    if len(intermediate) > 30 or width > 30 or any(
        type(row) is not list or len(row) != width for row in intermediate
    ):
        raise ValueError("intermediate must be rectangular and at most 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in intermediate for value in row):
        raise ValueError("intermediate cells must be exact ARC colors")
    out = [row[:] for row in intermediate]
    colors = sorted({value for row in intermediate for value in row if value != 0})
    for color in colors:
        cells = [(r, c) for r, row in enumerate(intermediate) for c, value in enumerate(row)
                 if value == color]
        if not cells:
            continue
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                out[r][c] = color
    return out


def transform(grid: list[list[int]], settings: dict[str, Any] | None = None) -> list[list[int]]:
    selected = _settings(settings)
    intermediate = canonical_equality(grid)
    return intermediate if selected["output_mode"] == "equality" else match_boxes_from_intermediate(intermediate)


def certify(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    selected = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(selected):
        raise ValueError("program_solution differs from selected setting")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not DEMO_LIMITS[0] <= len(train) <= DEMO_LIMITS[1]:
        raise ValueError(f"demonstration count must be in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if type(test) is not list or not QUERY_LIMITS[0] <= len(test) <= QUERY_LIMITS[1]:
        raise ValueError(f"query count must be in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")
    seen_inputs: set[str] = set()
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or "input" not in pair or "output" not in pair:
                raise ValueError(f"invalid {split} pair {index}")
            fingerprint = digest(pair["input"])
            if fingerprint in seen_inputs:
                raise ValueError("all demonstration and query inputs must be distinct")
            seen_inputs.add(fingerprint)
            if transform(pair["input"], selected) != pair["output"]:
                raise ValueError(f"label mismatch in {split} pair {index}")
    survivors = [dict(candidate) for candidate in SETTINGS
                 if all(transform(pair["input"], candidate) == pair["output"] for pair in train)]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify one setting: {survivors}")
    return {"survivors": survivors, "demo_only": True,
            "query_checks": [{"index": i, "identified": True} for i in range(len(test))]}


def generate(seed: int, settings: dict[str, Any] | None, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", *QUERY_LIMITS)
    train_inputs = [sample_input(seed, "demo", i, *DEMO_SHAPES[i]) for i in range(demos)]
    test_inputs = [sample_input(seed, "query", i, *QUERY_SHAPES[i]) for i in range(queries)]
    if len({digest(grid) for grid in train_inputs + test_inputs}) != demos + queries:
        raise ValueError("all demonstration and query inputs must be distinct")
    episode = {
        "schema": f"{TASK_ID}-parametric-match-boxes-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "program_solution": program(selected),
        "train": [{"input": grid, "output": transform(grid, selected)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, selected)} for grid in test_inputs],
    }
    episode["certificate"] = certify(episode)
    return episode
