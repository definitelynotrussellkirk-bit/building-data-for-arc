#!/usr/bin/env python3
"""Native episode-fixed vertical/plus family for ec23789c7821.

The default setting is the byte-exact canonical rule.  The alternative is a
true composition: stage A performs the canonical H3-to-V3 rewrite while
preserving all non-target cells; stage B consumes that full intermediate,
finds exact vertical triples, and adds left/right arms at their centers.
Inputs are deterministic and independent of the private setting.
"""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "ec23789c7821"
SETTINGS = ({"finish": "vertical"}, {"finish": "plus"})
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
DEMO_SHAPES = ((9, 10), (12, 13), (15, 16), (18, 19), (21, 22), (24, 25))
QUERY_SHAPES = ((10, 12), (16, 18), (23, 25), (30, 30))


def _canonical_program() -> str:
    matches: list[str] = []
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if not matches or len(set(matches)) != 1:
        raise RuntimeError(f"expected one stable canonical program for {TASK_ID}")
    return matches[0]


CANONICAL_PROGRAM = _canonical_program()
PLUS_PROGRAM = r"""(rule!
 ;; A: perform the exact canonical horizontal-triple rewrite first.
 (let ((dummy 0))
   (let* ((used
            (apply append
              (for*/list ((r (in-range (rows g)))
                          (c (in-range 0 (- (cols g) 2))))
                (let ((v (at g r c)))
                  (if (and (not (= v 0))
                           (= (at g r (+ c 1)) v)
                           (= (at g r (+ c 2)) v)
                           (> r 0)
                           (< r (- (rows g) 1)))
                      (list (list r c) (list r (+ c 1)) (list r (+ c 2)))
                      (list))))))
          (turned
            (for*/fold ((out (empty-grid (rows g) (cols g) 0)))
                       ((r (in-range (rows g)))
                        (c (in-range 0 (- (cols g) 2))))
              (let ((v (at g r c)))
                (if (and (not (= v 0))
                         (= (at g r (+ c 1)) v)
                         (= (at g r (+ c 2)) v)
                         (> r 0)
                         (< r (- (rows g) 1)))
                    (set-cell
                      (set-cell
                        (set-cell out (- r 1) (+ c 1) v)
                        r (+ c 1) v)
                      (+ r 1) (+ c 1) v)
                    out))))
          (canonical-intermediate
            (for*/fold ((out turned))
                       ((r (in-range (rows g)))
                        (c (in-range (cols g))))
              (if (and (not (= (at g r c) 0))
                       (not (member? (list r c) used)))
                  (set-cell out r c (at g r c))
                  out))))
     ;; B: find exact vertical triples in canonical-intermediate and add arms.
     (for*/fold ((out canonical-intermediate))
                ((r (in-range 0 (- (rows canonical-intermediate) 2)))
                 (c (in-range 1 (- (cols canonical-intermediate) 1))))
       (let ((v (at canonical-intermediate r c)))
         (if (and (not (= v 0))
                  (= (at canonical-intermediate (+ r 1) c) v)
                  (= (at canonical-intermediate (+ r 2) c) v)
                  (not (= (safe-at canonical-intermediate (- r 1) c -1) v))
                  (not (= (safe-at canonical-intermediate (+ r 3) c -1) v)))
             (set-cell
               (set-cell out (+ r 1) (- c 1) v)
               (+ r 1) (+ c 1) v)
             out))))))"""


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: dict[str, Any] | None) -> dict[str, str]:
    if value is None:
        value = dict(DEFAULT_SETTINGS)
    if type(value) is not dict or set(value) != {"finish"}:
        raise ValueError("settings must name exactly finish")
    finish = value["finish"]
    if finish not in {"vertical", "plus"}:
        raise ValueError("finish must be vertical or plus")
    return {"finish": finish}


def program(settings: dict[str, Any] | None = None) -> str:
    selected = _settings(settings)
    return CANONICAL_PROGRAM if selected["finish"] == "vertical" else PLUS_PROGRAM


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _rng(seed: int, stream: str, index: int) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    _integer(index, "index", 0, 10_000)
    raw = f"{TASK_ID}|{seed}|{stream}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty 2D list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30 ARC bounds")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC colors 0..9")
    return height, width


def _target_windows(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    height, width = _validate_grid(grid)
    windows: list[tuple[int, int, int]] = []
    for r in range(height):
        for c in range(max(0, width - 2)):
            value = grid[r][c]
            if (
                value != 0
                and grid[r][c + 1] == value
                and grid[r][c + 2] == value
                and r > 0
                and r < height - 1
            ):
                windows.append((r, c, value))
    return windows


def canonical_transform(grid: list[list[int]]) -> list[list[int]]:
    """Literal Python mirror of the protected canonical H3-to-V3 program."""
    height, width = _validate_grid(grid)
    windows = _target_windows(grid)
    used = {(r, c + offset) for r, c, _ in windows for offset in range(3)}
    out = [[0] * width for _ in range(height)]
    for r, c, value in windows:
        center = c + 1
        out[r - 1][center] = value
        out[r][center] = value
        out[r + 1][center] = value
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 0 and (r, c) not in used:
                out[r][c] = grid[r][c]
    return out


def plus_from_intermediate(intermediate: list[list[int]]) -> list[list[int]]:
    """Add arms only at exact V3s found in stage A's full intermediate."""
    height, width = _validate_grid(intermediate)
    out = [row[:] for row in intermediate]
    if height < 3 or width < 3:
        return out
    for r in range(height - 2):
        for c in range(1, width - 1):
            value = intermediate[r][c]
            if value == 0:
                continue
            if intermediate[r + 1][c] != value or intermediate[r + 2][c] != value:
                continue
            if r > 0 and intermediate[r - 1][c] == value:
                continue
            if r + 3 < height and intermediate[r + 3][c] == value:
                continue
            out[r + 1][c - 1] = value
            out[r + 1][c + 1] = value
    return out


def transform(grid: list[list[int]], settings: dict[str, Any] | None = None) -> list[list[int]]:
    selected = _settings(settings)
    intermediate = canonical_transform(grid)
    return intermediate if selected["finish"] == "vertical" else plus_from_intermediate(intermediate)


def _quadrant_anchors(candidates: list[tuple[int, int]], height: int, width: int) -> list[tuple[int, int]]:
    """Choose one target center near each quadrant center when the grid is large."""
    if height < 24 or width < 24:
        return []
    goals = (
        (height * 0.25, width * 0.25),
        (height * 0.25, width * 0.75),
        (height * 0.75, width * 0.25),
        (height * 0.75, width * 0.75),
    )
    anchors: list[tuple[int, int]] = []
    for goal_r, goal_c in goals:
        available = [candidate for candidate in candidates if candidate not in anchors]
        selected = min(
            available,
            key=lambda candidate: (candidate[0] - goal_r) ** 2 + (candidate[1] + 1 - goal_c) ** 2,
        )
        anchors.append(selected)
    return anchors


def sample_input(seed: int, stream: str, index: int, height: int, width: int) -> list[list[int]]:
    _integer(height, "height", 7, 30)
    _integer(width, "width", 7, 30)
    rng = _rng(seed, stream, index)
    grid = [[0] * width for _ in range(height)]

    # Four-column spacing leaves one blank column between H3 targets and
    # still supports two independent targets at the declared 7x7 minimum.
    candidates = [(r, c) for r in range(2, height - 2, 5) for c in range(0, width - 2, 4)]
    if len(candidates) < 2:
        raise ValueError("shape cannot support two separated target triples")
    anchors = _quadrant_anchors(candidates, height, width)
    remainder = [candidate for candidate in candidates if candidate not in anchors]
    rng.shuffle(remainder)
    target_count = min(len(candidates), max(2, 2 + (height * width) // 90, len(anchors)))
    chosen = anchors + remainder[: target_count - len(anchors)]

    colors = list(range(1, 10))
    rng.shuffle(colors)
    for target_index, (r, c) in enumerate(chosen):
        color = colors[target_index % len(colors)]
        grid[r][c:c + 3] = [color, color, color]

    # Preserved boundary cues and length-two distractors teach that stage A
    # transforms targets rather than deleting all other colored material.
    marker, top_pair, bottom_pair, side_pair = colors[-1], colors[-2], colors[-3], colors[-4]
    grid[0][0] = marker
    grid[0][width - 2:width] = [top_pair, top_pair]
    grid[height - 1][0:2] = [bottom_pair, bottom_pair]
    # Rows 3 and 4 are outside the target-row lattice (2, 7, 12, ...),
    # so this preserved side pair never overwrites a minimum-size target.
    grid[3][width - 1] = side_pair
    grid[4][width - 1] = side_pair
    return grid


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
    survivors = [
        dict(candidate)
        for candidate in SETTINGS
        if all(transform(pair["input"], candidate) == pair["output"] for pair in train)
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify one setting: {survivors}")
    return {
        "survivors": survivors,
        "demo_only": True,
        "query_checks": [{"index": index, "identified": True} for index in range(len(test))],
    }


def generate(seed: int, settings: dict[str, Any] | None, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", *QUERY_LIMITS)
    train_inputs = [sample_input(seed, "demo", index, *DEMO_SHAPES[index]) for index in range(demos)]
    test_inputs = [sample_input(seed, "query", index, *QUERY_SHAPES[index]) for index in range(queries)]
    if len({digest(grid) for grid in train_inputs + test_inputs}) != demos + queries:
        raise ValueError("all demonstration and query inputs must be distinct")
    episode = {
        "schema": f"{TASK_ID}-parametric-vertical-plus-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "program_solution": program(selected),
        "train": [{"input": grid, "output": transform(grid, selected)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, selected)} for grid in test_inputs],
    }
    episode["certificate"] = certify(episode)
    return episode
