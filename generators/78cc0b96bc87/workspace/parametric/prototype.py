"""Checkerboard family with a completed-slice relay alternative.

``checkerboard_only`` is the byte-exact canonical rule.  The alternative first
builds that complete checkerboard, then uses each external color-8 marker to
select one completed interior row or column and copies the entire slice into an
equally long exterior lane.  The lane therefore depends on cells created by the
first stage rather than on the sparse input cue cells.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any


TASK_ID = "78cc0b96bc87"
HERE = Path(__file__).resolve().parent
RELAY_RULES = ("checkerboard_only", "marker_slice_relay")
SIDES = ("left", "right", "up", "down")


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: dict[str, Any]) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"relay_rule"}:
        raise ValueError("settings must contain exactly relay_rule")
    value = settings["relay_rule"]
    if type(value) is not str or value not in RELAY_RULES:
        raise ValueError(f"relay_rule must be one of {RELAY_RULES}")
    return {"relay_rule": value}


def program(settings: dict[str, Any]) -> str:
    rule = normalize_settings(settings)["relay_rule"]
    name = "canonical.rkt" if rule == "checkerboard_only" else "marker_slice_relay.rkt"
    return (HERE / name).read_text()


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not 6 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 6 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be rectangular with dimensions in 6..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer ARC colors")
    return len(grid), width


def _frame(grid: list[list[int]]) -> dict[str, int]:
    height, width = _validate_grid(grid)
    cells = [(row, column) for row in range(height) for column in range(width) if grid[row][column] == 1]
    if not cells:
        raise ValueError("input needs a color-1 frame")
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    top, bottom = min(rows), max(rows)
    left, right = min(columns), max(columns)
    if bottom - top < 3 or right - left < 3:
        raise ValueError("frame needs a strict interior at least 2x2")
    expected = {
        (top, column) for column in range(left, right + 1)
    } | {
        (bottom, column) for column in range(left, right + 1)
    } | {
        (row, left) for row in range(top + 1, bottom)
    } | {
        (row, right) for row in range(top + 1, bottom)
    }
    if set(cells) != expected:
        raise ValueError("color 1 must be exactly one complete rectangular frame")
    return {
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "height": bottom - top + 1,
        "width": right - left + 1,
        "interior_height": bottom - top - 1,
        "interior_width": right - left - 1,
    }


def _seeds(grid: list[list[int]], frame: dict[str, int]) -> list[tuple[int, int, int]]:
    result = [
        (row, column, grid[row][column])
        for row in range(frame["top"] + 1, frame["bottom"])
        for column in range(frame["left"] + 1, frame["right"])
        if grid[row][column] != 0
    ]
    if len(result) != 2:
        raise ValueError("strict frame interior must contain exactly two nonzero seeds")
    result.sort()
    if result[0][0] != result[1][0] or result[0][1] >= result[1][1]:
        raise ValueError("seeds must share one row and have a strict left/right order")
    if result[0][2] in (0, 1, 8, 9) or result[1][2] in (0, 1, 8, 9) or result[0][2] == result[1][2]:
        raise ValueError("seed colors must be distinct from background, frame, markers, and distractors")
    left_parity = (result[0][0] - frame["top"] - 1 + result[0][1] - frame["left"] - 1) % 2
    right_parity = (result[1][0] - frame["top"] - 1 + result[1][1] - frame["left"] - 1) % 2
    if left_parity != 0 or right_parity != 1:
        raise ValueError("left seed must occupy even parity and right seed odd parity")
    return result


def _lane_for_marker(
    marker: tuple[int, int], frame: dict[str, int]
) -> dict[str, Any]:
    row, column = marker
    top, bottom = frame["top"], frame["bottom"]
    left, right = frame["left"], frame["right"]
    interior_h, interior_w = frame["interior_height"], frame["interior_width"]
    if top < row < bottom and column == left - interior_w:
        source = [(row, c) for c in range(left + 1, right)]
        target = [(row, c) for c in range(left - interior_w, left)]
        side = "left"
    elif top < row < bottom and column == right + interior_w:
        source = [(row, c) for c in range(left + 1, right)]
        target = [(row, c) for c in range(right + 1, right + interior_w + 1)]
        side = "right"
    elif left < column < right and row == top - interior_h:
        source = [(r, column) for r in range(top + 1, bottom)]
        target = [(r, column) for r in range(top - interior_h, top)]
        side = "up"
    elif left < column < right and row == bottom + interior_h:
        source = [(r, column) for r in range(top + 1, bottom)]
        target = [(r, column) for r in range(bottom + 1, bottom + interior_h + 1)]
        side = "down"
    else:
        raise ValueError("every marker must terminate one exact frame-sized exterior relay lane")
    return {"side": side, "marker": [row, column], "source": source, "target": target}


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    frame = _frame(grid)
    seeds = _seeds(grid, frame)
    markers = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 8
    ]
    if not markers or len(markers) > 4:
        raise ValueError("input needs one to four color-8 relay markers")
    lanes = [_lane_for_marker(marker, frame) for marker in markers]
    if len({lane["side"] for lane in lanes}) != len(lanes):
        raise ValueError("at most one marker is allowed on each side")
    seed_points = {(row, column) for row, column, _ in seeds}
    for lane in lanes:
        if seed_points & set(lane["source"]):
            raise ValueError("relay source slice must be blank in the sparse input")
    allowed_outside = {0, 8, 9}
    for row in range(height):
        for column in range(width):
            inside_or_border = frame["top"] <= row <= frame["bottom"] and frame["left"] <= column <= frame["right"]
            if not inside_or_border and grid[row][column] not in allowed_outside:
                raise ValueError("outside cells may only be background, markers, or color-9 distractors")
    return {
        "height": height,
        "width": width,
        "frame": frame,
        "seeds": [list(seed) for seed in seeds],
        "left_color": seeds[0][2],
        "right_color": seeds[1][2],
        "markers": [list(marker) for marker in markers],
        "relay_lanes": lanes,
    }


def checkerboard_only(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze_input(grid)
    height, width = facts["height"], facts["width"]
    frame = facts["frame"]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(frame["left"], frame["right"] + 1):
        output[frame["top"]][column] = 1
        output[frame["bottom"]][column] = 1
    for row in range(frame["top"] + 1, frame["bottom"]):
        output[row][frame["left"]] = 1
        output[row][frame["right"]] = 1
    for row in range(frame["top"] + 1, frame["bottom"]):
        for column in range(frame["left"] + 1, frame["right"]):
            parity = (row - frame["top"] - 1 + column - frame["left"] - 1) % 2
            output[row][column] = facts["left_color"] if parity == 0 else facts["right_color"]
    return output


def _relay(stage: list[list[int]], lanes: list[dict[str, Any]]) -> list[list[int]]:
    output = copy.deepcopy(stage)
    for lane in lanes:
        values = [stage[row][column] for row, column in lane["source"]]
        for (row, column), value in zip(lane["target"], values):
            output[row][column] = value
    return output


def solve_python(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    rule = normalize_settings(settings)["relay_rule"]
    facts = analyze_input(grid)
    stage = checkerboard_only(grid)
    return stage if rule == "checkerboard_only" else _relay(stage, facts["relay_lanes"])


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:marker-slice-relay-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


_TRAIN_PROFILES = (
    {"shape": (14, 22), "frame": (3, 8, 8, 8), "sides": ("left",), "layout": "shifted_pair"},
    {"shape": (22, 14), "frame": (8, 3, 8, 8), "sides": ("up",), "layout": "spaced_pair"},
    {"shape": (15, 23), "frame": (3, 4, 7, 9), "sides": ("right",), "layout": "canonical_pair"},
    {"shape": (23, 15), "frame": (4, 4, 9, 7), "sides": ("down",), "layout": "shifted_pair"},
    {"shape": (18, 28), "frame": (5, 10, 8, 8), "sides": ("left", "right"), "layout": "spaced_pair"},
    {"shape": (28, 18), "frame": (10, 5, 8, 8), "sides": ("up", "down"), "layout": "canonical_pair"},
)
_TEST_PROFILES = (
    {"shape": (16, 24), "frame": (4, 5, 8, 8), "sides": ("right",), "layout": "spaced_pair"},
    {"shape": (24, 16), "frame": (5, 4, 8, 8), "sides": ("down",), "layout": "canonical_pair"},
    {"shape": (25, 25), "frame": (10, 10, 9, 9), "sides": ("left", "up"), "layout": "shifted_pair"},
    {"shape": (30, 30), "frame": (10, 10, 10, 10), "sides": SIDES, "layout": "spaced_pair", "corners": True},
)
_HIGH_LEFT = ((7, 3), (6, 2), (5, 4))
_LOW_LEFT = ((2, 6), (3, 7), (4, 5))


def _seed_offsets(layout: str, interior_h: int, interior_w: int) -> tuple[tuple[int, int], tuple[int, int]]:
    if layout == "canonical_pair":
        result = ((0, 0), (0, 1))
    elif layout == "shifted_pair":
        result = ((1, 1), (1, 2))
    elif layout == "spaced_pair":
        result = ((2, 0), (2, 3))
    else:
        raise ValueError(layout)
    if result[1][0] >= interior_h or result[1][1] >= interior_w:
        raise ValueError("profile interior too small for seed layout")
    return result



def _input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _TEST_PROFILES
    profile = profiles[index]
    rng = _rng(seed, split, index)
    height, width = profile["shape"]
    top, left, frame_h, frame_w = profile["frame"]
    bottom, right = top + frame_h - 1, left + frame_w - 1
    interior_h, interior_w = frame_h - 2, frame_w - 2
    if not (0 <= top < bottom < height and 0 <= left < right < width):
        raise RuntimeError("invalid fixed profile")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(left, right + 1):
        grid[top][column] = 1
        grid[bottom][column] = 1
    for row in range(top + 1, bottom):
        grid[row][left] = 1
        grid[row][right] = 1

    seed_a, seed_b = _seed_offsets(profile["layout"], interior_h, interior_w)
    palette = _HIGH_LEFT if index % 2 == 0 else _LOW_LEFT
    left_color, right_color = palette[(seed + index) % len(palette)]
    seed_row = top + 1 + seed_a[0]
    seed_left = left + 1 + seed_a[1]
    seed_right = left + 1 + seed_b[1]
    grid[seed_row][seed_left] = left_color
    grid[seed_row][seed_right] = right_color

    horizontal_sides = [side for side in profile["sides"] if side in ("left", "right")]
    vertical_sides = [side for side in profile["sides"] if side in ("up", "down")]
    row_candidates = [offset for offset in range(interior_h) if offset != seed_a[0]]
    column_candidates = [offset for offset in range(interior_w) if offset not in (seed_a[1], seed_b[1])]
    # Stable rotations preserve distinct offsets while varying which completed
    # parity each side relays across seeds.
    row_shift = rng.randrange(len(row_candidates)) if row_candidates else 0
    col_shift = rng.randrange(len(column_candidates)) if column_candidates else 0
    row_offsets = (row_candidates[row_shift:] + row_candidates[:row_shift])[: len(horizontal_sides)]
    col_offsets = (column_candidates[col_shift:] + column_candidates[:col_shift])[: len(vertical_sides)]
    for side, offset in zip(horizontal_sides, row_offsets):
        row = top + 1 + offset
        column = left - interior_w if side == "left" else right + interior_w
        if not 0 <= column < width:
            raise RuntimeError("horizontal marker does not fit")
        grid[row][column] = 8
    for side, offset in zip(vertical_sides, col_offsets):
        row = top - interior_h if side == "up" else bottom + interior_h
        column = left + 1 + offset
        if not 0 <= row < height:
            raise RuntimeError("vertical marker does not fit")
        grid[row][column] = 8

    if profile.get("corners"):
        for row, column in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
            grid[row][column] = 9
    analyze_input(grid)
    return grid


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        return {"ok": False, "reason": "episode needs a training list"}
    survivors = []
    for name in RELAY_RULES:
        candidate = {"relay_rule": name}
        try:
            if all(solve_python(pair["input"], candidate) == pair["output"] for pair in episode["train"]):
                survivors.append(name)
        except (KeyError, TypeError, ValueError):
            return {"ok": False, "reason": "malformed demonstration"}
    selected = normalize_settings(episode.get("settings", {}))["relay_rule"]
    return {
        "ok": survivors == [selected],
        "survivors": survivors,
        "expected": [selected],
        "finite_family": list(RELAY_RULES),
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    normalized = normalize_settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    used: set[str] = set()
    splits: dict[str, list[dict[str, list[list[int]]]]] = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            grid = _input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in used:
                raise RuntimeError("constructed duplicate input")
            used.add(key)
            canonical = solve_python(grid, {"relay_rule": "checkerboard_only"})
            relay = solve_python(grid, {"relay_rule": "marker_slice_relay"})
            if canonical == relay:
                raise RuntimeError("constructed input does not distinguish settings")
            pairs.append({"input": grid, "output": solve_python(grid, normalized)})
        splits[split] = pairs
    episode = {
        "train": splits["train"],
        "test": splits["test"],
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    certificate = teaching_check(episode)
    if not certificate["ok"]:
        raise RuntimeError(f"demonstrations failed finite identification: {certificate}")
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
