"""Matched-input parity crop and input-derived payload relay family.

The alternative first performs the canonical parity-dependent 2x2 crop.  The
crop's upper-left color is an input-dependent key.  A separate marker row maps
that key to one of two 2x2 payloads, which is then returned.  Marker placement
varies independently of parity, so the second stage cannot be replaced by a
fixed left/right choice.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ("corner_crop", "corner_key_payload")

_DEMOS = (7, 9, 8, 10, 11, 12)
_QUERIES = (13, 16, 21, 30)


def _read(name: str) -> str:
    return (HOME / name).read_text(encoding="utf-8")


def program_for(mode: str) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError("rule_mode is not declared")
    return _read("canonical.rkt" if mode == "corner_crop" else "corner_key_payload.rkt")


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"rule_mode"}:
        raise ValueError("settings must contain exactly rule_mode")
    mode = settings["rule_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("rule_mode is not declared")
    return {"rule_mode": mode}


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _rng(seed: int, split: str, slot: int) -> random.Random:
    raw = hashlib.sha256(f"a897-parametric-v1:{seed}:{split}:{slot}".encode()).digest()
    return random.Random(int.from_bytes(raw[:8], "big"))


def _corner_crop(grid, *, opposite: bool = False):
    w = len(grid[0])
    even = w % 2 == 0
    choose_right = even ^ opposite
    c0 = w - 2 if choose_right else 0
    return [row[c0:c0 + 2] for row in grid[:2]]


def _keys(grid):
    return grid[0][0], grid[0][-2]


def _payload(grid, key: int):
    h, w = len(grid), len(grid[0])
    marker_row = h - 3
    matches = [c for c in range(w) if grid[marker_row][c] == key]
    if len(matches) != 1:
        raise ValueError(f"expected one payload marker for key {key}, found {matches}")
    c0 = matches[0]
    if not 0 <= c0 <= w - 2:
        raise ValueError("payload marker lacks a 2x2 payload")
    return [row[c0:c0 + 2] for row in grid[h - 2:h]]


def output_for(grid, mode: str):
    if mode not in MODES:
        raise ValueError("unknown rule_mode")
    chosen = _corner_crop(grid)
    if mode == "corner_crop":
        return chosen
    return _payload(grid, chosen[0][0])


def _different_pattern(rng, forbidden):
    for _ in range(200):
        values = [rng.randrange(1, 10) for _ in range(4)]
        pattern = [values[:2], values[2:]]
        if len(set(values)) >= 3 and pattern not in forbidden:
            return pattern
    raise RuntimeError("could not make a distinct 2x2 pattern")


def _build(seed: int, slot: int, side: int, *, split: str):
    rng = _rng(seed, split, slot)
    grid = [[rng.randrange(1, 10) for _ in range(side)] for _ in range(side)]
    for r in range(side - 3, side):
        grid[r] = [0] * side

    colors = list(range(1, 10))
    rng.shuffle(colors)
    left_key, right_key = colors[:2]
    left_rest = rng.sample([c for c in range(1, 10) if c != left_key], 3)
    right_rest = rng.sample([c for c in range(1, 10) if c != right_key], 3)
    left = [[left_key, left_rest[0]], [left_rest[1], left_rest[2]]]
    right = [[right_key, right_rest[0]], [right_rest[1], right_rest[2]]]
    if right == left:
        right[1].reverse()
    for r in range(2):
        grid[r][:2] = left[r]
        grid[r][-2:] = right[r]

    payload_left = _different_pattern(rng, [left, right])
    payload_right = _different_pattern(rng, [left, right, payload_left])
    left_col, right_col = 1, side - 3
    # The first three teaching scenes deliberately vary marker mapping: the two
    # odd scenes put the selected left key on opposite sides, then the even scene
    # exposes the other canonical parity branch.
    swap = slot % 2 == 1
    marker_left, marker_right = ((right_key, left_key) if swap else (left_key, right_key))
    grid[side - 3][left_col] = marker_left
    grid[side - 3][right_col] = marker_right
    for rr in range(2):
        grid[side - 2 + rr][left_col:left_col + 2] = payload_left[rr]
        grid[side - 2 + rr][right_col:right_col + 2] = payload_right[rr]

    # Guard the authored contract directly.
    assert len({v for row in grid[:2] for v in row[:2]}) >= 3
    assert len({v for row in grid[:2] for v in row[-2:]}) >= 3
    assert _keys(grid)[0] != _keys(grid)[1]
    assert output_for(grid, "corner_crop") != output_for(grid, "corner_key_payload")
    return grid


def select_inputs(seed: int, demos: int, queries: int):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 3, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = [{"input": _build(seed, i, _DEMOS[i], split="demo")} for i in range(demos)]
    test = [{"input": _build(seed, i, _QUERIES[i], split="query")} for i in range(queries)]
    return {"train": train, "test": test}


def _wrong_outputs(grid, chosen):
    left_key, right_key = _keys(grid)
    canonical = output_for(grid, "corner_crop")
    relay = output_for(grid, "corner_key_payload")
    w = len(grid[0])
    left_payload = _payload(grid, grid[-3][1])
    right_payload = _payload(grid, grid[-3][w - 3])
    odd = w % 2 == 1
    return {
        "opposite_setting": relay if chosen == "corner_crop" else canonical,
        "fixed_left_crop": [row[:2] for row in grid[:2]],
        "fixed_right_crop": [row[-2:] for row in grid[:2]],
        "fixed_left_payload": left_payload,
        "fixed_right_payload": right_payload,
        "odd_left_even_right_payload": left_payload if odd else right_payload,
        "odd_right_even_left_payload": right_payload if odd else left_payload,
        "opposite_key_payload": _payload(grid, right_key if odd else left_key),
    }


def assess_demos(demos, chosen: str):
    if chosen not in MODES:
        raise ValueError("unknown rule_mode")
    setting_survivors = [m for m in MODES if all(output_for(p["input"], m) == p["output"] for p in demos)]
    names = list(_wrong_outputs(demos[0]["input"], chosen))
    survivors = [n for n in names if all(_wrong_outputs(p["input"], chosen)[n] == p["output"] for p in demos)]
    return {"demonstrations": len(demos), "setting_survivors": setting_survivors,
            "harmful_shortcut_survivors": survivors, "rivals_tested": len(names)}


def generate_episode(seed: int, mode: str, demos: int = 3, queries: int = 4):
    if mode not in MODES:
        raise ValueError("unknown rule_mode")
    selected = select_inputs(seed, demos, queries)
    return {
        "program_solution": program_for(mode),
        "train": [{"input": deepcopy(p["input"]), "output": output_for(p["input"], mode)} for p in selected["train"]],
        "test": [{"input": deepcopy(p["input"]), "output": output_for(p["input"], mode)} for p in selected["test"]],
    }


def public_turn(episode, query_index: int):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {"train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(episode["test"][query_index]["input"])}]}


def _counterfactual_program():
    return """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (wrong (if (member? w (list 2 4 6 8 10 12 14 16 18 20 22 24 26 28 30))
                    (subgrid g 0 0 1 1)
                    (subgrid g 0 (- w 2) 1 (- w 1))))
         (key (at wrong 0 0))
         (marker-row (- h 3))
         (matches (for/list ((c (in-range w)) #:when (= (at g marker-row c) key)) c))
         (payload-col (first matches)))
    (subgrid g (- h 2) payload-col (- h 1) (+ payload-col 1)))))"""


def causal_case(grid):
    chosen = _corner_crop(grid)
    wrong = _corner_crop(grid, opposite=True)
    return {
        "input": deepcopy(grid),
        "settings": {"rule_mode": "corner_key_payload"},
        "intermediate_value": {"selected_crop": chosen, "selected_key": chosen[0][0],
                               "wrong_key": wrong[0][0]},
        "program": program_for("corner_key_payload"),
        "output": output_for(grid, "corner_key_payload"),
        "counterfactual_program": _counterfactual_program(),
        "counterfactual_output": _payload(grid, wrong[0][0]),
        "ablation": "wrong_intermediate",
    }
