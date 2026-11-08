"""Native vertical-flip family with an input-derived border-cue axis."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "a6294f07bff6"
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
CUE_AXIS = (HERE / "cue_axis.rkt").read_text(encoding="utf-8")
MODES = ("canonical_ud", "cue_axis")
RIVALS = ("identity", "always_lr", "rotate_180", "transpose", "opposite_cue_axis")


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"flip_rule"}:
        raise ValueError("settings must contain exactly flip_rule")
    mode = settings["flip_rule"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("flip_rule is undeclared")
    return mode


def validate_grid(grid: object) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")
    return deepcopy(grid)


def program(settings: object) -> str:
    return CANONICAL if _mode(settings) == "canonical_ud" else CUE_AXIS


def dependency_intermediate(grid: object) -> dict[str, Any]:
    checked = validate_grid(grid)
    h, w = len(checked), len(checked[0])
    cues = [[r, c] for r, row in enumerate(checked) for c, value in enumerate(row) if value == 9]
    if len(cues) != 1:
        raise ValueError("cue_axis inputs need exactly one color-9 cue")
    cue = cues[0]
    horizontal_edge = cue[0] in (0, h - 1)
    vertical_edge = cue[1] in (0, w - 1)
    if horizontal_edge == vertical_edge:
        raise ValueError("the color-9 cue must lie on exactly one non-corner border")
    return {"cue": cue, "axis": "ud" if horizontal_edge else "lr"}


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid[::-1]]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def solve(grid: object, mode: str) -> list[list[int]]:
    checked = validate_grid(grid)
    if mode == "canonical_ud":
        return _flip_ud(checked)
    if mode == "cue_axis":
        axis = dependency_intermediate(checked)["axis"]
        return _flip_ud(checked) if axis == "ud" else _flip_lr(checked)
    raise ValueError("unknown mode")


def _rng(seed: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _cue_position(side: str, h: int, w: int, rng: random.Random) -> tuple[int, int]:
    if side == "top":
        return 0, rng.randrange(1, w - 1)
    if side == "bottom":
        return h - 1, rng.randrange(1, w - 1)
    if side == "left":
        return rng.randrange(1, h - 1), 0
    if side == "right":
        return rng.randrange(1, h - 1), w - 1
    raise ValueError(side)


def _scene(seed: int, index: int, h: int, w: int, side: str) -> list[list[int]]:
    rng = _rng(seed, f"scene:{index}")
    palette = list(range(1, 9))
    grid = []
    for r in range(h):
        row = []
        for c in range(w):
            if rng.random() < 0.18:
                row.append(0)
            else:
                row.append(palette[(7 * r + 5 * c + 3 * index + rng.randrange(len(palette))) % len(palette)])
        grid.append(row)

    cue = _cue_position(side, h, w, rng)
    grid[cue[0]][cue[1]] = 9

    # Keep real content on every boundary, without creating another cue.
    boundary_points = [(0, 1), (h - 1, w - 2), (1, 0), (h - 2, w - 1)]
    for j, (r, c) in enumerate(boundary_points):
        if (r, c) != cue and grid[r][c] == 0:
            grid[r][c] = palette[(index + j) % len(palette)]

    # Fail closed against accidental symmetries or rival coincidences.
    if grid == _flip_ud(grid):
        r, c = 1, 1
        grid[r][c] = 1 if grid[r][c] != 1 else 2
    if grid == _flip_lr(grid):
        r, c = h - 2, 1
        grid[r][c] = 3 if grid[r][c] != 3 else 4
    if _flip_ud(grid) == _flip_lr(grid):
        r, c = 1, w - 2
        grid[r][c] = 5 if grid[r][c] != 5 else 6

    validate_grid(grid)
    dependency_intermediate(grid)
    return grid


_PROFILES = (
    (5, 6, "left"),
    (7, 5, "top"),
    (9, 11, "right"),
    (12, 8, "bottom"),
    (18, 16, "left"),
    (30, 30, "top"),
    (6, 9, "right"),
    (15, 13, "bottom"),
    (24, 27, "left"),
    (30, 30, "right"),
)


def input_bank(seed: object) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    seed_i = _integer(seed, 0, 2**63 - 1, "seed")
    grids = [_scene(seed_i, index, *profile) for index, profile in enumerate(_PROFILES)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(keys) != len(set(keys)):
        raise ValueError("constructed inputs must be distinct")
    return grids[:6], grids[6:]


def generate(seed: object, settings: object, demos: object = 3, queries: object = 4) -> dict[str, Any]:
    seed_i = _integer(seed, 0, 2**63 - 1, "seed")
    demos_i = _integer(demos, 2, 6, "demos")
    queries_i = _integer(queries, 1, 4, "queries")
    mode = _mode(settings)
    train, test = input_bank(seed_i)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": solve(grid, mode)}

    return {
        "train": [pair(grid) for grid in train[:demos_i]],
        "test": [pair(grid) for grid in test[:queries_i]],
        "program_solution": program({"flip_rule": mode}),
        "meta": {"settings": {"flip_rule": mode}, "seed": seed_i},
    }


def rival_output(grid: object, name: str) -> list[list[int]]:
    checked = validate_grid(grid)
    if name == "identity":
        return checked
    if name == "always_lr":
        return _flip_lr(checked)
    if name == "rotate_180":
        return [row[::-1] for row in checked[::-1]]
    if name == "transpose":
        return [list(row) for row in zip(*checked)]
    if name == "opposite_cue_axis":
        axis = dependency_intermediate(checked)["axis"]
        return _flip_lr(checked) if axis == "ud" else _flip_ud(checked)
    raise ValueError(name)


def public_turn(episode: object, query_index: object) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode is malformed")
    index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }


def public_id(episode: object, query_index: object) -> str:
    raw = json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _program_with_forced_axis(axis: str) -> str:
    needle = "(vertical? (or (= r 0) (= r (- (rows g) 1))))"
    replacement = "(vertical? #t)" if axis == "ud" else "(vertical? #f)"
    if CUE_AXIS.count(needle) != 1:
        raise ValueError("cue-axis program template changed")
    return CUE_AXIS.replace(needle, replacement)


def causal_case(grid: object) -> dict[str, Any]:
    checked = validate_grid(grid)
    intermediate = dependency_intermediate(checked)
    wrong = "lr" if intermediate["axis"] == "ud" else "ud"
    intended = solve(checked, "cue_axis")
    counterfactual = _flip_ud(checked) if wrong == "ud" else _flip_lr(checked)
    return {
        "input": checked,
        "settings": {"flip_rule": "cue_axis"},
        "intermediate_value": {**intermediate, "wrong_axis": wrong},
        "program": CUE_AXIS,
        "output": intended,
        "counterfactual_program": _program_with_forced_axis(wrong),
        "counterfactual_output": counterfactual,
        "ablation": "wrong_intermediate",
    }
