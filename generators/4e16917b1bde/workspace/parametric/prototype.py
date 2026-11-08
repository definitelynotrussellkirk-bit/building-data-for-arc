"""Native parametric depth-placement family for ARC task 4e16917b1bde.

The source grammar is shared across settings: a full-height colored divider and
colored source cells on one side.  ``same_depth`` is the exact canonical rule.
``reverse_depth`` first measures the furthest source distance from the divider,
then copies every source cell to the opposite side with its depth order reversed
inside that input-derived span.
"""
from __future__ import annotations

from copy import deepcopy
from functools import cache
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "4e16917b1bde"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)

Grid = list[list[int]]
POLICIES = ("same_depth", "reverse_depth")
DEFAULT_POLICY = "same_depth"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

# Profiles deliberately make the first two demonstrations disagree with
# side-, parity-, palette-, and gap-conditioned shortcuts while keeping the
# rule action fixed within an episode.  Query 4 is a substantive 30x30 case.
_DEMO_PROFILES = (
    {"h": 8, "w": 13, "divider": 6, "side": "left", "depths": (1, 4, 5), "count": 10, "colors": 1, "divider_color": 5},
    {"h": 9, "w": 14, "divider": 4, "side": "right", "depths": (2, 4), "count": 11, "colors": 3, "divider_color": 8},
    {"h": 10, "w": 17, "divider": 11, "side": "left", "depths": (1, 2, 5), "count": 15, "colors": 2},
    {"h": 12, "w": 19, "divider": 6, "side": "right", "depths": (1, 3, 6), "count": 18, "colors": 4},
    {"h": 16, "w": 23, "divider": 11, "side": "left", "depths": (2, 4, 7, 10), "count": 24, "colors": 3},
    {"h": 20, "w": 29, "divider": 14, "side": "right", "depths": (1, 5, 9, 13), "count": 30, "colors": 4},
)
_QUERY_PROFILES = (
    {"h": 14, "w": 17, "divider": 8, "side": "left", "depths": (1, 3, 7), "count": 20, "colors": 2},
    {"h": 18, "w": 21, "divider": 7, "side": "right", "depths": (2, 4, 7), "count": 24, "colors": 3},
    {"h": 24, "w": 27, "divider": 16, "side": "left", "depths": (1, 4, 7, 10), "count": 32, "colors": 4},
    {"h": 30, "w": 30, "divider": 14, "side": "left", "depths": (1, 3, 6, 10, 14), "count": 42, "colors": 4},
)

_REVERSE_DEPTH_PROGRAM = """(rule! (lambda (g)
  (let* ((dividers
          (filter
           (lambda (c)
             (let ((v (at g 0 c)))
               (and (not (= v 0))
                    (all? (lambda (r) (= (at g r c) v))
                          (range (rows g))))))
           (range (cols g))))
         (divider (first dividers))
         (dcolor (at g 0 divider))
         (sources
          (filter
           (lambda (p)
             (let ((r (first p)) (c (second p)))
               (and (not (= c divider))
                    (not (= (at g r c) 0))
                    (not (= (at g r c) dcolor)))))
           (grid-positions g)))
         (max-depth
          (apply max
                 (map (lambda (p) (abs (- (second p) divider))) sources))))
    (for/fold ([out g]) ([p (in-list sources)])
      (let* ((r (first p))
             (c (second p))
             (v (at g r c))
             (depth (abs (- c divider)))
             (target-depth (+ 1 (- max-depth depth)))
             (direction (if (< c divider) 1 -1))
             (target-col (+ divider (* direction target-depth))))
        (if (and (in-bounds? r target-col (rows g) (cols g))
                 (= (at out r target-col) 0))
            (set-cell out r target-col v)
            out))))))"""


@cache
def _generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def _validate_policy(policy: Any) -> str:
    if type(policy) is not str:
        raise TypeError("depth policy must be an exact string")
    if policy not in POLICIES:
        raise ValueError(f"unknown depth policy: {policy!r}")
    return policy


@cache
def canonical_program() -> str:
    matches: list[dict[str, Any]] = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(matches)}")
    source = matches[0].get("program_solution")
    if type(source) is not str or not source:
        raise ValueError(f"canonical row for {TASK_ID} has no program_solution")
    return source


def program_for(policy: str) -> str:
    policy = _validate_policy(policy)
    return canonical_program() if policy == "same_depth" else _REVERSE_DEPTH_PROGRAM


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(value: Any, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def depth_facts(grid: Grid) -> dict[str, Any]:
    errors, facts = _generator()._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    divider = facts["divider_col"]
    depths = sorted({abs(col - divider) for _, col, _ in facts["sources"]})
    return {
        "divider_col": divider,
        "divider_color": facts["divider_color"],
        "source_side": facts["source_side"],
        "depths": depths,
        "max_depth": max(depths),
        "min_depth": min(depths),
        "source_count": len(facts["sources"]),
        "source_colors": sorted({value for _, _, value in facts["sources"]}),
        "sources": [list(item) for item in facts["sources"]],
    }


def _apply_with_span(grid: Grid, span: int, *, reverse: bool) -> Grid:
    errors, facts = _generator()._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if type(span) is not int or span < 1:
        raise ValueError("span must be a positive integer")
    divider = facts["divider_col"]
    result = [list(row) for row in grid]
    for row, col, value in facts["sources"]:
        depth = abs(col - divider)
        target_depth = span + 1 - depth if reverse else depth
        direction = 1 if col < divider else -1
        target_col = divider + direction * target_depth
        if not 0 <= target_col < len(grid[0]):
            raise ValueError(f"target column {target_col} is out of bounds")
        if result[row][target_col] != 0:
            raise ValueError(f"target {(row, target_col)} is not background")
        result[row][target_col] = value
    return result


def apply_policy(grid: Grid, policy: str) -> Grid:
    policy = _validate_policy(policy)
    facts = depth_facts(grid)
    return _apply_with_span(
        grid,
        facts["max_depth"],
        reverse=policy == "reverse_depth",
    )


def apply_reverse_with_span(grid: Grid, span: int) -> Grid:
    """Audit helper for a wrong input-derived intermediate."""
    return _apply_with_span(grid, span, reverse=True)


def _profile_rng(seed: int, split: str, slot: int, attempt: int) -> random.Random:
    material = f"{TASK_ID}|depth-policy-v1|{seed}|{split}|{slot}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _palette(seed: int, split: str, slot: int, divider_color: int, count: int) -> tuple[int, ...]:
    colors = [value for value in range(1, 10) if value != divider_color]
    material = f"{TASK_ID}|palette|{seed}|{split}|{slot}".encode()
    rng = random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))
    rng.shuffle(colors)
    return tuple(colors[:count])


def _make_input(seed: int, split: str, slot: int, profile: dict[str, Any]) -> Grid:
    h = profile["h"]
    w = profile["w"]
    divider = profile["divider"]
    side = profile["side"]
    depths = tuple(profile["depths"])
    count = profile["count"]
    color_count = profile["colors"]
    if max(depths) > min(divider, w - 1 - divider):
        raise AssertionError("profile depth exceeds symmetric divider span")
    if count > h * len(depths):
        raise AssertionError("profile source count exceeds available cells")

    fixed_divider = profile.get("divider_color")
    divider_color = fixed_divider or (((seed + slot * 3 + (0 if split == "demo" else 5)) % 9) + 1)
    palette = _palette(seed, split, slot, divider_color, color_count)

    for attempt in range(256):
        rng = _profile_rng(seed, split, slot, attempt)
        candidates = [(row, depth) for depth in depths for row in range(h)]
        forced: list[tuple[int, int]] = [(0, max(depths)), (h - 1, min(depths))]
        for index, depth in enumerate(depths):
            forced.append(((2 * index + 1 + slot) % h, depth))
        positions: list[tuple[int, int]] = []
        for item in forced:
            if item not in positions:
                positions.append(item)
        remainder = [item for item in candidates if item not in positions]
        rng.shuffle(remainder)
        positions.extend(remainder[: count - len(positions)])
        rng.shuffle(positions)

        if color_count == 1:
            source_colors = [palette[0]] * count
        else:
            source_colors = list(palette)
            source_colors.extend([palette[0]] * (count - len(source_colors)))
            rng.shuffle(source_colors)

        grid = [[0 for _ in range(w)] for _ in range(h)]
        for row in range(h):
            grid[row][divider] = divider_color
        for (row, depth), color in zip(positions, source_colors):
            col = divider - depth if side == "left" else divider + depth
            grid[row][col] = color

        if _generator().self_check(grid):
            continue
        if apply_policy(grid, "same_depth") == apply_policy(grid, "reverse_depth"):
            continue
        return grid
    raise RuntimeError(f"could not construct distinguishing {split} profile {slot}")


def episode_inputs(seed: int, demos: int, queries: int) -> list[Grid]:
    seed = _validate_seed(seed)
    demos = _validate_count(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _validate_count(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    demo_inputs = [
        _make_input(seed, "demo", slot, _DEMO_PROFILES[slot])
        for slot in range(demos)
    ]
    query_inputs = [
        _make_input(seed, "query", slot, _QUERY_PROFILES[slot])
        for slot in range(queries)
    ]
    inputs = demo_inputs + query_inputs
    frozen = {tuple(tuple(row) for row in grid) for grid in inputs}
    if len(frozen) != len(inputs):
        raise AssertionError("episode inputs must be distinct")
    return inputs


def generate_episode(seed: int, depth_policy: str, demos: int, queries: int) -> dict[str, Any]:
    depth_policy = _validate_policy(depth_policy)
    inputs = episode_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": grid, "output": apply_policy(grid, depth_policy)}
            for grid in inputs[:demos]
        ],
        "test": [
            {"input": grid, "output": apply_policy(grid, depth_policy)}
            for grid in inputs[demos:]
        ],
        "program_solution": program_for(depth_policy),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Project one model-visible turn without settings, code, labels, or count hints."""
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode needs train and test lists")
    if not 0 <= query_index < len(test):
        raise IndexError("query_index is outside the private query list")
    visible_train = []
    for pair in train:
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            raise ValueError("every demonstration needs input and output")
        visible_train.append({"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])})
    query = test[query_index]
    if not isinstance(query, dict) or "input" not in query:
        raise ValueError("query needs an input")
    return {"train": visible_train, "test": [{"input": deepcopy(query["input"])}]}
