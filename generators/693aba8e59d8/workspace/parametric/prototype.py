"""Episode-fixed parametric family for ARC task ``693aba8e59d8``.

The exact canonical setting rotates the extracted color-6 template according to
anchor color.  The alternate setting first measures the template bounding-box
area, reduces it modulo four, and adds that input-derived offset to every anchor
rotation.  Inputs are sampled independently of the private setting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Callable

try:
    from reviewer_support import public_challenge_bytes
except ImportError:  # direct authoring outside the staged runtime
    _SUPPORT = Path(__file__).resolve().parents[4] / "shared" / "runtime" / "reviewer_support.py"
    _SPEC = importlib.util.spec_from_file_location("_reviewer_support_693aba8e59d8", _SUPPORT)
    if _SPEC is None or _SPEC.loader is None:
        raise
    _MODULE = importlib.util.module_from_spec(_SPEC)
    _SPEC.loader.exec_module(_MODULE)
    public_challenge_bytes = _MODULE.public_challenge_bytes


TASK_ID = "693aba8e59d8"
HERE = Path(__file__).resolve().parent
PARAMETER_NAME = "rotation_rule"
SETTINGS = ("anchor_color", "bbox_area_offset")
DEFAULT_SETTING = "anchor_color"
SHORTCUTS = (
    "always_offset_one",
    "always_offset_two",
    "always_offset_three",
    "cell_count_offset",
    "bbox_height_offset",
    "bbox_width_offset",
    "no_rotation",
    "reverse_anchor",
)

# The first two demonstrations intentionally contrast both bounding-box offsets
# and both cell-count classes, so the minimum supported lesson rejects constant
# offsets and the tempting cell-count shortcut.
DEMO_PROFILES = (
    (15, 15, "v5"),   # bbox area 9 -> offset 1, five cells
    (16, 18, "l4"),   # bbox area 6 -> offset 2, four cells
    (18, 17, "w5"),   # bbox area 9 -> offset 1, five cells
    (20, 22, "p5"),   # bbox area 6 -> offset 2, five cells
    (23, 24, "v5"),
    (25, 27, "l4"),
)
QUERY_PROFILES = (
    (17, 19, "p5"),
    (21, 23, "w5"),
    (26, 28, "l4"),
    (30, 30, "v5"),
)

_SHAPE_CELLS = {
    "l4": frozenset(((0, 0), (1, 0), (2, 0), (2, 1))),
    "v5": frozenset(((0, 0), (0, 1), (0, 2), (1, 0), (2, 0))),
    "w5": frozenset(((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))),
    "p5": frozenset(((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))),
}
_PHASE_COLORS = (
    (1, 2, 3, 4),
    (2, 3, 4, 1),
    (3, 4, 1, 2),
    (4, 1, 2, 3),
)


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _setting(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER_NAME}
        or type(settings[PARAMETER_NAME]) is not str
        or settings[PARAMETER_NAME] not in SETTINGS
    ):
        raise ValueError("settings must contain only rotation_rule=anchor_color|bbox_area_offset")
    return settings[PARAMETER_NAME]


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return value


def _normalize_cells(cells) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    if not cells:
        return frozenset()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _rotate_cells_cw(cells) -> frozenset[tuple[int, int]]:
    cells = _normalize_cells(cells)
    height = max(row for row, _ in cells) + 1
    return _normalize_cells((col, height - 1 - row) for row, col in cells)


def _rotate_cells(cells, turns: int) -> frozenset[tuple[int, int]]:
    out = _normalize_cells(cells)
    for _ in range(turns % 4):
        out = _rotate_cells_cw(out)
    return out


def _cells_to_grid(cells) -> list[list[int]]:
    normalized = _normalize_cells(cells)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1
    out = [[0] * width for _ in range(height)]
    for row, col in normalized:
        out[row][col] = 6
    return out


def _rotate_grid_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_grid(grid: list[list[int]], turns: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    for _ in range(turns % 4):
        out = _rotate_grid_cw(out)
    return out


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        row, col = todo.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    return seen == cells


def _facts(grid: object) -> dict[str, Any]:
    data = _grid(grid)
    base_cells = {
        (row, col)
        for row, values in enumerate(data)
        for col, value in enumerate(values)
        if value == 6
    }
    if not base_cells or not _connected(base_cells):
        raise ValueError("input must contain one connected color-6 base object")
    top = min(row for row, _ in base_cells)
    bottom = max(row for row, _ in base_cells)
    left = min(col for _, col in base_cells)
    right = max(col for _, col in base_cells)
    base_grid = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for row, col in base_cells:
        base_grid[row - top][col - left] = 6
    anchors = [
        (row, col, value)
        for row, values in enumerate(data)
        for col, value in enumerate(values)
        if value in (1, 2, 3, 4)
    ]
    if len(anchors) != 4 or {value for _, _, value in anchors} != {1, 2, 3, 4}:
        raise ValueError("input must contain exactly one anchor of each color 1..4")
    height, width = len(base_grid), len(base_grid[0])
    return {
        "height": len(data),
        "width": len(data[0]),
        "base_cells": sorted([list(cell) for cell in base_cells]),
        "base_grid": base_grid,
        "base_cell_count": len(base_cells),
        "bbox_height": height,
        "bbox_width": width,
        "bbox_area": height * width,
        "bbox_area_offset": (height * width) % 4,
        "anchors": [list(anchor) for anchor in sorted(anchors)],
    }


def features(grid: object) -> dict[str, Any]:
    return deepcopy(_facts(grid))


def _offset(mode: str, facts: dict[str, Any]) -> int:
    if mode == "anchor_color":
        return 0
    if mode == "bbox_area_offset":
        return facts["bbox_area_offset"]
    if mode == "always_offset_one":
        return 1
    if mode == "always_offset_two":
        return 2
    if mode == "always_offset_three":
        return 3
    if mode == "cell_count_offset":
        return facts["base_cell_count"] % 4
    if mode == "bbox_height_offset":
        return facts["bbox_height"] % 4
    if mode == "bbox_width_offset":
        return facts["bbox_width"] % 4
    if mode in ("no_rotation", "reverse_anchor"):
        return facts["bbox_area_offset"]
    raise ValueError(f"unsupported rotation rule: {mode}")


def _stamp(output: list[list[int]], subgrid: list[list[int]], anchor: tuple[int, int]) -> None:
    top = anchor[0] - len(subgrid) // 2
    left = anchor[1] - len(subgrid[0]) // 2
    for drow, values in enumerate(subgrid):
        for dcol, value in enumerate(values):
            row, col = top + drow, left + dcol
            if value and 0 <= row < len(output) and 0 <= col < len(output[0]):
                output[row][col] = value


def _transform(grid: list[list[int]], mode: str, *, forced_offset: int | None = None) -> list[list[int]]:
    facts = _facts(grid)
    output = [[0] * facts["width"] for _ in range(facts["height"])]
    offset = _offset(mode, facts) if forced_offset is None else forced_offset % 4
    for row, col, code in facts["anchors"]:
        if mode == "no_rotation":
            turns = 0
        elif mode == "reverse_anchor":
            turns = ((1 - code) + offset) % 4
        else:
            turns = ((code - 1) + offset) % 4
        _stamp(output, _rotate_grid(facts["base_grid"], turns), (row, col))
    return output


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    return _transform(grid, _setting(settings))


def transform_with_offset(grid: list[list[int]], wrong_offset: int) -> list[list[int]]:
    _integer(wrong_offset, 0, 3, "wrong_offset")
    return _transform(grid, "bbox_area_offset", forced_offset=wrong_offset)


def program(settings: dict[str, str]) -> str:
    setting = _setting(settings)
    filename = "canonical.rkt" if setting == "anchor_color" else "bbox_area_offset.rkt"
    return (HERE / filename).read_text(encoding="utf-8").rstrip("\n")


def _replace_offset(expression: str) -> str:
    source = program({PARAMETER_NAME: "bbox_area_offset"})
    old = "(offset (modulo (* (rows base-grid) (cols base-grid)) 4))"
    if source.count(old) != 1:
        raise ValueError("pinned alternate offset expression changed")
    return source.replace(old, f"(offset {expression})")


def _replace_turns(expression: str) -> str:
    source = program({PARAMETER_NAME: "bbox_area_offset"})
    old = "(modulo (+ (- (third anchor) 1) offset) 4)"
    if source.count(old) != 1:
        raise ValueError("pinned alternate turn expression changed")
    return source.replace(old, expression)


def rival_programs() -> dict[str, str]:
    return {
        "anchor_color": program({PARAMETER_NAME: "anchor_color"}),
        "bbox_area_offset": program({PARAMETER_NAME: "bbox_area_offset"}),
        "always_offset_one": _replace_offset("1"),
        "always_offset_two": _replace_offset("2"),
        "always_offset_three": _replace_offset("3"),
        "cell_count_offset": _replace_offset("(modulo (length (obj-cells base)) 4)"),
        "bbox_height_offset": _replace_offset("(modulo (rows base-grid) 4)"),
        "bbox_width_offset": _replace_offset("(modulo (cols base-grid) 4)"),
        "no_rotation": _replace_turns("0"),
        "reverse_anchor": _replace_turns("(modulo (+ (- 1 (third anchor)) offset) 4)"),
    }


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {name: _transform(grid, name) for name in (*SETTINGS, *SHORTCUTS)}


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:bbox-area-offset-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _distractors(height: int, width: int, rng: random.Random) -> list[list[int]]:
    grid = [[0] * width for _ in range(height)]
    salt = rng.randrange(1, 10_000)
    for row in range(height):
        for col in range(width):
            boundary = row in (0, height - 1) or col in (0, width - 1)
            chosen = boundary and ((row + col + salt) % 2 == 0)
            chosen = chosen or (1 < row < height - 2 and 1 < col < width - 2
                                and (row * 5 + col * 7 + salt) % 11 == 0)
            if chosen:
                grid[row][col] = 8 if (row * 3 + col + salt) % 2 else 9
    # Explicitly guarantee every boundary is represented, independent of parity.
    for row, col in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
        grid[row][col] = 8 + ((row + col + salt) % 2)
    return grid


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    height, width, shape_name = profiles[index]
    rng = _rng(seed, split, index)
    grid = _distractors(height, width, rng)

    orientation = (rng.randrange(4) + index) % 4
    shape = _rotate_cells(_SHAPE_CELLS[shape_name], orientation)
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    center_row, center_col = height // 2, width // 2
    jitter_row = rng.choice((-1, 0, 1))
    jitter_col = rng.choice((-1, 0, 1))
    top = center_row - shape_height // 2 + jitter_row
    left = center_col - shape_width // 2 + jitter_col

    anchors = {
        "north": (2, center_col),
        "east": (center_row, width - 3),
        "south": (height - 3, center_col),
        "west": (center_row, 2),
    }
    phase = (seed + index + (0 if split == "train" else 2)) % 4
    phase_colors = _PHASE_COLORS[phase]
    for color, name in zip(phase_colors, ("north", "east", "south", "west")):
        row, col = anchors[name]
        grid[row][col] = color
    for drow, dcol in shape:
        grid[top + drow][left + dcol] = 6

    facts = _facts(grid)
    expected_area = 9 if shape_name in ("v5", "w5") else 6
    if facts["bbox_area"] != expected_area:
        raise AssertionError("base bounding-box area drifted")
    if facts["bbox_area_offset"] not in (1, 2):
        raise AssertionError("constructed offset must be one or two")
    outputs = rival_outputs(grid)
    if outputs["anchor_color"] == outputs["bbox_area_offset"]:
        raise AssertionError("admitted settings must disagree on every sampled input")
    return grid


def teaching_certificate(train, query_inputs, settings):
    chosen = _setting(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    names = (*SETTINGS, *SHORTCUTS)
    rejected: dict[str, int] = {}
    for index, pair in enumerate(train):
        _grid(pair["output"])
        for name, output in rival_outputs(pair["input"]).items():
            if output != pair["output"]:
                rejected.setdefault(name, index)
    survivors = [name for name in names if name not in rejected]
    if chosen not in survivors:
        raise ValueError("demonstration labels contradict selected rotation rule")
    query_identifiable = []
    for grid in query_inputs:
        outputs = rival_outputs(grid)
        query_identifiable.append(all(outputs[name] == outputs[chosen] for name in survivors))
    return {
        "scope": (
            "two admitted rotation rules plus constant-offset, cell-count, "
            "single-dimension, no-rotation, and reversed-anchor shortcuts"
        ),
        "survivors": survivors,
        "rejected": rejected,
        "identified": survivors == [chosen],
        "query_identifiable": query_identifiable,
        "query_answers_used_for_fitting": False,
    }


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "program_solution": program(settings),
        "reference": "proposed_parametric",
        "training_admitted": False,
    }
    for split, count in (("train", demos), ("test", queries)):
        episode[split] = []
        for index in range(count):
            grid = _draw(seed, split, index)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    episode["certificate"] = verify_episode(episode)
    return episode


def verify_episode(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _setting(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution does not match the selected rule")
    seen = set()
    for split, bounds in (("train", (2, 6)), ("test", (1, 4))):
        pairs = episode.get(split)
        if type(pairs) is not list or not bounds[0] <= len(pairs) <= bounds[1]:
            raise ValueError(f"unsupported {split} count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            expected = transform(pair["input"], settings)
            _grid(pair["output"])
            if pair["output"] != expected:
                raise ValueError(f"{split} label disagrees with the selected rule")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("all inputs must be distinct")
            seen.add(key)
    certificate = teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], settings
    )
    if not certificate["identified"] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify the selected rotation rule")
    return certificate


def visible_turn(episode: dict[str, Any], index: int) -> bytes:
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})
