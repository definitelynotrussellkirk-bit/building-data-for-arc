"""Proposed episode-fixed prototype-rotation family for ``d2708f8b731b``.

The canonical ``identity`` setting matches neutral targets directly to the
colored prototype legend.  The alternate ``quarter_turn`` setting first rotates
each prototype clockwise before matching.  Inputs contain a complete four-shape
rotation orbit, so the same sampled grid is lawful under both private settings.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_bytes

TASK_ID = "d2708f8b731b"
HERE = Path(__file__).resolve().parent
PARAMETER_NAME = "prototype_transform"
SETTINGS = ("identity", "quarter_turn")
SHORTCUTS = ("constant_first", "constant_last", "target_order")
DEFAULT_SETTING = "identity"
PROTOTYPE_VERSION = "1.0.0"

DEMO_PROFILES = (
    (15, 18, 8),
    (17, 21, 12),
    (19, 22, 16),
    (21, 24, 20),
    (24, 27, 28),
    (27, 29, 36),
)
QUERY_PROFILES = (
    (16, 19, 12),
    (20, 23, 20),
    (25, 27, 32),
    (30, 30, 65),
)


def _normalize(cells):
    values = [(int(r), int(c)) for r, c in cells]
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return tuple(sorted((r - r0, c - c0) for r, c in values))


def rotate_cw(shape):
    return _normalize((c, -r) for r, c in shape)


_BASE = ((0, 0), (1, 0), (1, 1))
_orbit = []
shape = _normalize(_BASE)
for _ in range(4):
    _orbit.append(shape)
    shape = rotate_cw(shape)
ORBIT = tuple(_orbit)
if len(set(ORBIT)) != 4:
    raise AssertionError("prototype orbit must contain four distinct orientations")


def _load_selected_generator():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("d270_parametric_selected", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SELECTED = _load_selected_generator()


def _integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _settings(settings: object) -> str:
    if (type(settings) is not dict or set(settings) != {PARAMETER_NAME}
            or type(settings[PARAMETER_NAME]) is not str
            or settings[PARAMETER_NAME] not in SETTINGS):
        raise ValueError(
            "settings must contain only prototype_transform=identity|quarter_turn"
        )
    return settings[PARAMETER_NAME]


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _facts(grid: object) -> dict[str, Any]:
    data = _grid(grid)
    facts, errors = _SELECTED._analyze_grid(data)
    if errors:
        raise ValueError("; ".join(errors))
    return facts


def features(grid: object) -> dict[str, Any]:
    facts = _facts(grid)
    prototype_shapes = tuple(
        tuple(tuple(cell) for cell in record["shape"])
        for record in facts["prototype_records"]
    )
    target_shapes = tuple(
        tuple(tuple(cell) for cell in record["shape"])
        for record in facts["target_records"]
    )
    return {
        "height": facts["grid_h"],
        "width": facts["grid_w"],
        "separator_col": facts["separator_col"],
        "n_prototypes": len(facts["prototype_records"]),
        "n_targets": len(facts["target_records"]),
        "prototype_shapes": prototype_shapes,
        "target_shapes": target_shapes,
        "prototype_colors": tuple(record["swatch"] for record in facts["prototype_records"]),
        "prototype_records": facts["prototype_records"],
        "target_records": facts["target_records"],
    }


def _paint_targets(grid: list[list[int]], mode: str) -> list[list[int]]:
    facts = _facts(grid)
    prototypes = facts["prototype_records"]
    targets = facts["target_records"]
    if len(prototypes) < 2:
        raise ValueError("at least two prototypes are required")
    identity = {tuple(record["shape"]): record["swatch"] for record in prototypes}
    if mode == "identity":
        mapping = identity
    elif mode == "quarter_turn":
        mapping = {rotate_cw(tuple(record["shape"])): record["swatch"] for record in prototypes}
    else:
        mapping = None
    colors = [record["swatch"] for record in prototypes]
    out = copy.deepcopy(grid)
    for record in targets:
        shape = tuple(record["shape"])
        if mapping is not None:
            color = mapping.get(shape, 1)
        elif mode == "constant_first":
            color = colors[0]
        elif mode == "constant_last":
            color = colors[-1]
        elif mode == "target_order":
            r1, c1, _r2, _c2 = record["bbox"]
            color = colors[(r1 + c1) % len(colors)]
        else:
            raise ValueError(f"unsupported transformation: {mode}")
        for row, col in record["cells"]:
            out[row][col] = color
    return out


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    return _paint_targets(grid, _settings(settings))


def program(settings: dict[str, str]) -> str:
    setting = _settings(settings)
    name = "canonical.rkt" if setting == "identity" else "quarter_turn.rkt"
    return (HERE / name).read_text(encoding="utf-8").rstrip("\n")


def _replace_color(expression: str) -> str:
    source = program({PARAMETER_NAME: "identity"})
    old = "(color (if (empty? hit) 1 (second (first hit))))"
    if source.count(old) != 1:
        raise ValueError("pinned canonical target-color expression changed")
    return source.replace(old, f"(color {expression})")


def rival_programs(settings: dict[str, str]) -> dict[str, str]:
    _settings(settings)
    return {
        "identity": program({PARAMETER_NAME: "identity"}),
        "quarter_turn": program({PARAMETER_NAME: "quarter_turn"}),
        "constant_first": _replace_color("(second (first mapping))"),
        "constant_last": _replace_color("(second (last-list mapping))"),
        "target_order": _replace_color(
            "(nth (map (lambda (row) (second row)) mapping) "
            "(modulo (+ (obj-r1 obj) (obj-c1 obj)) (length mapping)))"
        ),
    }


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        name: _paint_targets(grid, name)
        for name in (*SETTINGS, *SHORTCUTS)
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:prototype-rotation-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _paint(grid: list[list[int]], top: int, left: int, shape, color: int) -> None:
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _ordinary_positions(height: int, width: int, separator: int):
    rows = list(range(0, height - 1, 3))
    cols = list(range(separator + 1, width - 1, 3))
    return [(row, col) for row in rows for col in cols]


def _stress_positions():
    rows = (0, 3, 6, 9, 12, 15, 18, 21, 24, 28)
    out = []
    for index, row in enumerate(rows):
        cols = range(10, 29, 3) if index % 2 == 0 else range(11, 28, 3)
        out.extend((row, col) for col in cols)
    if len(out) != 65:
        raise AssertionError("stress profile must contain 65 targets")
    return out


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, target_count = (
        DEMO_PROFILES if split == "train" else QUERY_PROFILES
    )[index]
    stress = split == "test" and index == 3
    separator = 9 if stress else width // 2
    rng = _rng(seed, split, index)
    grid = [[0] * width for _ in range(height)]

    legend_order = list(range(4))
    rng.shuffle(legend_order)
    colors = rng.sample(range(2, 10), 4)
    tops = (0, height // 4, height // 2, height - 2)
    for rank, shape_index in enumerate(legend_order):
        left = 0 if stress and rank in (0, 3) else (seed + index + rank) % 2
        top = tops[rank]
        _paint(grid, top, left, ORBIT[shape_index], 1)
        grid[top + ((seed + rank + index) % 2)][left + 3] = colors[shape_index]

    if stress:
        positions = _stress_positions()
    else:
        positions = _ordinary_positions(height, width, separator)
        if len(positions) < target_count:
            raise AssertionError("profile capacity is too small")
        rng.shuffle(positions)
        positions = sorted(positions[:target_count])
    assignments = [
        (legend_order[rank % 4] + 2) % 4
        for rank in range(target_count)
    ]
    for (top, left), shape_index in zip(positions, assignments):
        _paint(grid, top, left, ORBIT[shape_index], 1)

    facts = features(grid)
    if facts["separator_col"] != separator:
        raise AssertionError(
            f"separator drifted from {separator} to {facts['separator_col']}"
        )
    if set(facts["prototype_shapes"]) != set(ORBIT):
        raise AssertionError("constructed legend lost a rotation orientation")
    if set(facts["target_shapes"]) != set(ORBIT):
        raise AssertionError("constructed targets lost a rotation orientation")
    if facts["n_targets"] != target_count:
        raise AssertionError("target components merged during construction")
    outputs = rival_outputs(grid)
    if outputs["identity"] == outputs["quarter_turn"]:
        raise AssertionError("settings do not disagree")
    for shortcut in SHORTCUTS:
        if outputs[shortcut] in (outputs["identity"], outputs["quarter_turn"]):
            raise AssertionError(f"shortcut {shortcut} fits a constructed input")
    return grid


def teaching_certificate(train, query_inputs, settings):
    chosen = _settings(settings)
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
        raise ValueError("demonstration labels contradict selected transformation")
    identifiable = []
    for grid in query_inputs:
        outputs = rival_outputs(grid)
        identifiable.append(all(outputs[name] == outputs[chosen] for name in survivors))
    return {
        "scope": "two prototype transforms plus two constant-color and one target-position shortcut",
        "survivors": survivors,
        "rejected": rejected,
        "identified": survivors == [chosen],
        "query_identifiable": identifiable,
        "query_answers_used_for_fitting": False,
    }


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(settings),
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
    _settings(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution does not match selected transformation")
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
                raise ValueError(f"{split} label disagrees with selected transformation")
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("all inputs must be distinct")
            seen.add(key)
    certificate = teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], settings
    )
    if not certificate["identified"] or not all(certificate["query_identifiable"]):
        raise ValueError("demonstrations do not identify the selected transformation")
    return certificate


def visible_turn(episode, index: int) -> bytes:
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][index]]}
    )
