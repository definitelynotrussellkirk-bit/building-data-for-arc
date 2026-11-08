"""Constructive two-setting aligned-panel family for ``e777125624ca``.

``nor`` is the exact selected canonical program. ``sparser_difference`` first
counts occupied cells in each aligned 3-column panel, selects the uniquely
sparser panel, then marks positions where that panel is empty and the other
panel is occupied. Inputs are sampled independently of the hidden setting and
teach both possible selector outcomes in the first two demonstrations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random


TASK_ID = "e777125624ca"
HERE = Path(__file__).resolve().parent
SETTINGS = ("nor", "sparser_difference")
DEMO_HEIGHTS = (5, 8, 11, 14, 17, 20)
QUERY_HEIGHTS = (3, 12, 21, 30)
DEMO_SPARSER = ("left", "right", "left", "right", "left", "right")
QUERY_SPARSER = ("right", "left", "right", "left")


def _integer(value, name, low=None, high=None):
    if type(value) is not int or (low is not None and value < low) or (
        high is not None and value > high
    ):
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"rule_mode"}:
        raise ValueError("settings must contain exactly rule_mode")
    value = settings["rule_mode"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("rule_mode must be nor or sparser_difference")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or len(grid[0]) != 7:
        raise ValueError("grid must have exactly 7 columns")
    if any(
        type(row) is not list
        or len(row) != 7
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings):
    name = _setting(settings)
    filename = "nor.rkt" if name == "nor" else "sparser_difference.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _state(left, right):
    return ("1" if left else "0") + ("1" if right else "0")


def scene_facts(grid):
    _grid(grid)
    state_counts = {state: 0 for state in ("00", "10", "01", "11")}
    left_count = 0
    right_count = 0
    panel_values = set()
    separator_values = {row[3] for row in grid}
    for row in grid:
        for col in range(3):
            left = row[col]
            right = row[col + 4]
            if left:
                left_count += 1
                panel_values.add(left)
            if right:
                right_count += 1
                panel_values.add(right)
            state_counts[_state(left, right)] += 1
    sparser = None
    if left_count < right_count:
        sparser = "left"
    elif right_count < left_count:
        sparser = "right"
    return {
        "height": len(grid),
        "state_counts": state_counts,
        "left_count": left_count,
        "right_count": right_count,
        "sparser": sparser,
        "panel_values": sorted(panel_values),
        "separator_values": sorted(separator_values),
    }


def validate_input(grid):
    try:
        _grid(grid)
    except ValueError as error:
        return [str(error)]
    errors = []
    if not 3 <= len(grid) <= 30:
        errors.append("aligned-panel scenes must have height 3..30")
    facts = scene_facts(grid)
    if len(facts["separator_values"]) != 1 or facts["separator_values"][0] in (0, 8):
        errors.append("separator column must use one nonzero non-8 color")
    if len(facts["panel_values"]) != 1 or facts["panel_values"][0] == 8:
        errors.append("both panels must use one shared nonzero non-8 foreground color")
    if (
        len(facts["separator_values"]) == 1
        and len(facts["panel_values"]) == 1
        and facts["separator_values"][0] == facts["panel_values"][0]
    ):
        errors.append("separator and panel foreground colors must differ")
    missing = [state for state, count in facts["state_counts"].items() if count == 0]
    if missing:
        errors.append("scene must contain all aligned states 00, 10, 01 and 11")
    if facts["sparser"] is None:
        errors.append("panel occupancy counts must differ to select one sparser panel")
    return errors


def _mark_states(grid, states):
    return [
        [8 if _state(row[col], row[col + 4]) in states else 0 for col in range(3)]
        for row in grid
    ]


def transform(grid, settings):
    mode = _setting(settings)
    errors = validate_input(grid)
    if errors:
        raise ValueError("invalid parametric input: " + "; ".join(errors))
    if mode == "nor":
        states = {"00"}
    else:
        states = {"01" if scene_facts(grid)["sparser"] == "left" else "10"}
    return _mark_states(grid, states)


def _rng(seed, stream, index):
    payload = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _state_counts(height, sparser):
    slots = height * 3
    both_zero = max(1, slots // 6)
    both_one = max(1, slots // 4)
    remaining = slots - both_zero - both_one
    small = max(1, remaining // 3)
    large = remaining - small
    if large <= small:
        large = small + 1
        both_zero -= 1
    if min(both_zero, both_one, small, large) < 1:
        raise ValueError("height cannot teach all four states and a unique sparser side")
    if sparser == "left":
        left_only, right_only = small, large
    elif sparser == "right":
        left_only, right_only = large, small
    else:
        raise ValueError("sparser must be left or right")
    counts = {"00": both_zero, "10": left_only, "01": right_only, "11": both_one}
    if sum(counts.values()) != slots or counts["10"] == counts["01"]:
        raise RuntimeError("state allocation did not create a unique sparser panel")
    return counts


def sample_input(seed, stream, index, height, sparser):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 3, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    if sparser not in ("left", "right"):
        raise ValueError("sparser must be left or right")
    rng = _rng(seed, stream, index)
    foreground, separator = rng.sample([value for value in range(1, 10) if value != 8], 2)
    states = []
    for state, count in _state_counts(height, sparser).items():
        states.extend([state] * count)
    rng.shuffle(states)
    grid = []
    cursor = 0
    for _ in range(height):
        row = [0] * 7
        row[3] = separator
        for col in range(3):
            state = states[cursor]
            cursor += 1
            if state[0] == "1":
                row[col] = foreground
            if state[1] == "1":
                row[col + 4] = foreground
        grid.append(row)
    errors = validate_input(grid)
    if errors:
        raise RuntimeError("constructive aligned-panel sampler failed: " + "; ".join(errors))
    if scene_facts(grid)["sparser"] != sparser:
        raise RuntimeError("constructive sampler selected the wrong sparser panel")
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
        "prototype": True,
    }
    seen = set()
    for split, heights, sides in (
        ("train", DEMO_HEIGHTS[:demos], DEMO_SPARSER[:demos]),
        ("test", QUERY_HEIGHTS[:queries], QUERY_SPARSER[:queries]),
    ):
        for index, (height, side) in enumerate(zip(heights, sides)):
            grid = sample_input(seed, split, index, height, side)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise RuntimeError("sampler produced duplicate visible inputs")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result


def rival_outputs(grid):
    facts = scene_facts(grid)
    dynamic = "01" if facts["sparser"] == "left" else "10"
    opposite = "10" if dynamic == "01" else "01"
    return {
        "nor": _mark_states(grid, {"00"}),
        "sparser_difference": _mark_states(grid, {dynamic}),
        "always_left_is_sparser": _mark_states(grid, {"01"}),
        "always_right_is_sparser": _mark_states(grid, {"10"}),
        "opposite_difference": _mark_states(grid, {opposite}),
        "xor": _mark_states(grid, {"10", "01"}),
        "left_zero": _mark_states(grid, {"00", "01"}),
        "right_zero": _mark_states(grid, {"00", "10"}),
        "equality": _mark_states(grid, {"00", "11"}),
        "intersection": _mark_states(grid, {"11"}),
    }


def teaching_failures(demos, queries, settings):
    selected = _setting(settings)
    if type(demos) is not list or type(queries) is not list or not demos or not queries:
        return ["demos and queries must be nonempty lists"]
    prepared = []
    for label, pairs in (("demo", demos), ("query", queries)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                return [f"{label} {index} is malformed"]
            errors = validate_input(pair["input"])
            if errors:
                return [f"{label} {index} input invalid: {'; '.join(errors)}"]
            expected = transform(pair["input"], settings)
            if pair["output"] != expected:
                return [f"{label} {index} label disagrees with {selected}"]
            prepared.append((label, pair, rival_outputs(pair["input"])))

    names = sorted(prepared[0][2])
    names.remove(selected)
    failures = []
    demo_rows = [row for row in prepared if row[0] == "demo"]
    query_rows = [row for row in prepared if row[0] == "query"]
    for name in names:
        survives = all(rivals[name] == pair["output"] for _, pair, rivals in demo_rows)
        disagrees = any(rivals[name] != pair["output"] for _, pair, rivals in query_rows)
        if survives and disagrees:
            failures.append(f"plausible rival {name!r} fits every demo but changes a query")
    return failures
