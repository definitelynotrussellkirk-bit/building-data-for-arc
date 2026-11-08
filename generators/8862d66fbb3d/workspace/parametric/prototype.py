"""Parametric transform/intersection family with an overlap-adjacency finish.

The canonical setting returns every occupied cell in the command-guided
intersection.  The alternative first constructs that exact intermediate mask,
then keeps only cells having an orthogonal neighbor in the intermediate.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import itertools
import json
import random
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "8862d66fbb3d"
PARAMETER = "finish"
SETTINGS = ("all_overlap", "adjacent_overlap")
DEFAULT = {PARAMETER: SETTINGS[0]}
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    SETTINGS[0]: _HOME / "canonical.rkt",
    SETTINGS[1]: _HOME / "adjacent_overlap.rkt",
}
_CELLS = tuple((r, c) for r in range(3) for c in range(3))

# Each profile is the exact occupied intersection after the command transform.
# The first two visible demonstrations refute horizontal-only, vertical-only,
# 8-neighbor, endpoint-only, and wrong-left-intermediate shortcuts.
_TRAIN_OVERLAPS = (
    frozenset({(0, 0), (0, 1), (1, 2)}),
    frozenset({(0, 2), (1, 2), (2, 2), (2, 0)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 2)}),
    frozenset({(0, 0), (0, 1), (1, 1), (2, 0)}),
    frozenset({(0, 0), (1, 1), (2, 2)}),
    frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)}),
)
_QUERY_OVERLAPS = (
    frozenset({(0, 0), (0, 1), (1, 2), (2, 2)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 2)}),
    frozenset({(0, 0), (1, 1), (2, 2)}),
    frozenset({(0, 0), (0, 1), (1, 1), (2, 1)}),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAM_FILES[_finish(settings)].read_text(encoding="utf-8")


def _grid(value: Any) -> tuple[int, int]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(value[0])
    if len(value) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return len(value), width


def _transform_point(point: tuple[int, int], cmd: int) -> tuple[int, int]:
    r, c = point
    if cmd == 1:
        return r, c
    if cmd == 2:
        return c, 2 - r
    if cmd == 3:
        return 2 - r, 2 - c
    if cmd in (4, 7):
        return c, r
    if cmd == 5:
        return r, 2 - c
    if cmd == 6:
        return 2 - r, c
    if cmd == 8:
        return 2 - c, 2 - r
    raise ValueError("command must be in 1..8")


def _transform_mask(cells: Iterable[tuple[int, int]], cmd: int) -> frozenset[tuple[int, int]]:
    return frozenset(_transform_point(point, cmd) for point in cells)


def _inverse_mask(cells: Iterable[tuple[int, int]], cmd: int) -> frozenset[tuple[int, int]]:
    inverse = {_transform_point(point, cmd): point for point in _CELLS}
    return frozenset(inverse[point] for point in cells)


def _panel_state(grid: list[list[int]]) -> tuple[int, frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    if _grid(grid) != (4, 7):
        raise ValueError("input must be exactly 4x7")
    cmd = grid[0][0]
    if not 1 <= cmd <= 8:
        raise ValueError("command must be in 1..8")
    if any(grid[0][c] != 0 for c in range(1, 7)) or any(grid[r][3] != 0 for r in range(1, 4)):
        raise ValueError("input must preserve the command row and blank separator")
    left = frozenset((r, c) for r in range(3) for c in range(3) if grid[1 + r][c] != 0)
    right = frozenset((r, c) for r in range(3) for c in range(3) if grid[1 + r][4 + c] != 0)
    return cmd, left, right


def overlap_cells(grid: list[list[int]]) -> frozenset[tuple[int, int]]:
    cmd, left, right = _panel_state(grid)
    return left & _transform_mask(right, cmd)


def _neighbor_count(cells: frozenset[tuple[int, int]], point: tuple[int, int], diagonals: bool = False) -> int:
    r, c = point
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonals:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return sum((r + dr, c + dc) in cells for dr, dc in deltas)


def adjacent_cells(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return frozenset(point for point in cells if _neighbor_count(cells, point) > 0)


def _mask_grid(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    selected = set(cells)
    return [[7 if (r, c) in selected else 0 for c in range(3)] for r in range(3)]


def solve(grid: list[list[int]], settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    overlap = overlap_cells(grid)
    return _mask_grid(overlap if finish == SETTINGS[0] else adjacent_cells(overlap))


def wrong_intermediate_solve(grid: list[list[int]]) -> list[list[int]]:
    """Counterfactual: filter adjacency on the left mask instead of intersection."""
    _, left, _ = _panel_state(grid)
    return _mask_grid(adjacent_cells(left))


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if _grid(left) != _grid(right):
        raise ValueError("grids must have the same shape")
    return sum(left[r][c] != right[r][c] for r in range(len(left)) for c in range(len(left[0])))


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|adjacent-overlap-input-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _equivalent_commands(cmd: int) -> set[int]:
    return {4, 7} if cmd in (4, 7) else {cmd}


def _candidate_commands(seed: int, split: str, index: int) -> list[int]:
    commands = [1, 2, 3, 4, 5, 6, 8, 7]
    digest = hashlib.sha256(f"{seed}|{split}|{index}|commands".encode()).digest()
    offset = digest[0] % len(commands)
    return commands[offset:] + commands[:offset]


def _construct_masks(
    desired: frozenset[tuple[int, int]],
    cmd: int,
    rng: random.Random,
) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    remaining = [point for point in _CELLS if point not in desired]
    extra = 1 if len(desired) >= 4 else 2
    left_choices = list(itertools.combinations(remaining, extra))
    rng.shuffle(left_choices)
    best = None
    for left_only_tuple in left_choices:
        left_only = frozenset(left_only_tuple)
        right_pool = [point for point in remaining if point not in left_only]
        right_choices = list(itertools.combinations(right_pool, extra))
        rng.shuffle(right_choices)
        for transformed_only_tuple in right_choices:
            transformed = desired | frozenset(transformed_only_tuple)
            left = desired | left_only
            right = _inverse_mask(transformed, cmd)
            if cmd != 1 and right == transformed:
                continue
            outputs = {code: left & _transform_mask(right, code) for code in range(1, 9)}
            if any(outputs[code] == desired for code in range(1, 9) if code not in _equivalent_commands(cmd)):
                continue
            wrong = adjacent_cells(left)
            score = len(wrong.symmetric_difference(adjacent_cells(desired)))
            candidate = (score, left, right)
            if best is None or candidate[0] > best[0]:
                best = candidate
    if best is None:
        raise RuntimeError("could not construct a command-discriminating panel pair")
    return best[1], best[2]


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, MAX_SEED)
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    profiles = _TRAIN_OVERLAPS if split == "train" else _QUERY_OVERLAPS
    _integer("index", index, 0, len(profiles) - 1)
    desired = profiles[index]
    rng = _rng(seed, split, index)
    chosen = None
    for cmd in _candidate_commands(seed, split, index):
        try:
            left, right = _construct_masks(desired, cmd, rng)
        except RuntimeError:
            continue
        chosen = (cmd, left, right)
        break
    if chosen is None:
        raise RuntimeError("no lawful command/mask construction")
    cmd, left, right = chosen
    colors = list((1, 2, 3, 4, 5, 6, 8, 9))
    rng.shuffle(colors)
    left_palette, right_palette = colors[:2], colors[2:4]
    grid = [[0 for _ in range(7)] for _ in range(4)]
    grid[0][0] = cmd
    for offset, (r, c) in enumerate(sorted(left)):
        grid[1 + r][c] = left_palette[offset % 2]
    for offset, (r, c) in enumerate(sorted(right)):
        grid[1 + r][4 + c] = right_palette[offset % 2]
    if overlap_cells(grid) != desired:
        raise RuntimeError("constructed input changed the desired intersection")
    if wrong_intermediate_solve(grid) == solve(grid, {PARAMETER: SETTINGS[1]}):
        raise RuntimeError("constructed input does not expose the wrong-intermediate shortcut")
    return grid


def _horizontal_only(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return frozenset((r, c) for r, c in cells if (r, c - 1) in cells or (r, c + 1) in cells)


def _vertical_only(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return frozenset((r, c) for r, c in cells if (r - 1, c) in cells or (r + 1, c) in cells)


def _diagonal_neighbors(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return frozenset(point for point in cells if _neighbor_count(cells, point, diagonals=True) > 0)


def _degree_one(cells: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return frozenset(point for point in cells if _neighbor_count(cells, point) == 1)


def rival_outputs(grid: list[list[int]], settings: Any) -> dict[str, list[list[int]]]:
    finish = _finish(settings)
    overlap = overlap_cells(grid)
    selected = solve(grid, settings)
    outputs = {
        "other_setting": solve(grid, {PARAMETER: SETTINGS[1] if finish == SETTINGS[0] else SETTINGS[0]}),
        "horizontal_only": _mask_grid(_horizontal_only(overlap)),
        "vertical_only": _mask_grid(_vertical_only(overlap)),
        "eight_neighbor": _mask_grid(_diagonal_neighbors(overlap)),
        "degree_one_only": _mask_grid(_degree_one(overlap)),
        "left_mask_intermediate": wrong_intermediate_solve(grid),
    }
    return outputs


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _finish(settings)
    train = episode.get("train")
    if type(train) is not list or len(train) < MIN_DEMOS:
        raise ValueError("episode needs at least two demonstrations")
    names = set()
    per_demo: list[dict[str, list[list[int]]]] = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations require input/output grids")
        expected = solve(pair["input"], settings)
        if pair["output"] != expected:
            raise ValueError("demonstration label differs from selected rule")
        outputs = rival_outputs(pair["input"], settings)
        names.update(outputs)
        per_demo.append(outputs)
    surviving = sorted(
        name
        for name in names
        if all(outputs.get(name) == pair["output"] for outputs, pair in zip(per_demo, train))
    )
    return {
        "status": "identified" if not surviving else "ambiguous",
        "surviving_rivals": surviving,
        "demonstrations": len(train),
        "used_query_answers": False,
        "limits": "Finite named rivals fitted to demonstrations only; not universal uniqueness.",
    }


def dependency_trace(grid: list[list[int]], settings: Any) -> dict[str, Any]:
    finish = _finish(settings)
    cmd, left, right = _panel_state(grid)
    transformed = _transform_mask(right, cmd)
    overlap = left & transformed
    adjacent = adjacent_cells(overlap)
    return {
        "setting": {PARAMETER: finish},
        "step_a": "transform the right mask by the command and intersect it with the left mask",
        "intermediate": {"grid": _mask_grid(overlap), "occupied_cells": len(overlap)},
        "step_b": "keep only overlap cells with an orthogonal overlap neighbor",
        "adjacent_overlap_cells": len(adjacent),
        "why_b_depends_on_a": "adjacency is measured inside the command-dependent intersection, not in either source panel",
        "command": cmd,
    }


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer("seed", seed, 0, MAX_SEED)
    _finish(settings)
    _integer("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _integer("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train = [
        {"input": (grid := sample_input(seed, "train", index)), "output": solve(grid, settings)}
        for index in range(demos)
    ]
    test = [
        {"input": (grid := sample_input(seed, "test", index)), "output": solve(grid, settings)}
        for index in range(queries)
    ]
    fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(fingerprints) != len(set(fingerprints)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "sampling": {"draws": demos + queries, "duplicate_rejections": 0},
    }
    certificate = teaching_check(episode)
    if certificate["surviving_rivals"]:
        raise RuntimeError("constructed demonstrations leave declared rivals alive: " + ", ".join(certificate["surviving_rivals"]))
    episode["teaching"] = certificate
    return episode


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    test = episode["test"]
    _integer("query_index", query_index, 0, len(test) - 1)
    try:
        query = {"input": deepcopy(test[query_index]["input"])}
        if query_index == 0:
            train = [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]]
            return {"train": train, "test": [query]}
        return {"test": [query]}
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs require valid grids") from error


__all__ = [
    "DEFAULT", "SETTINGS", "adjacent_cells", "changed_cells", "dependency_trace",
    "generate", "overlap_cells", "program", "public_turn", "rival_outputs",
    "sample_input", "solve", "teaching_check", "wrong_intermediate_solve",
]
