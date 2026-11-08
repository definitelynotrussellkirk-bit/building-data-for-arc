"""Native finite parametric family for ARC generator af373b71d67d.

The canonical ``clockwise`` setting is byte-for-byte the selected reference
program.  ``counterclockwise`` keeps the same extraction, erasure and frame
anchor but reverses the quarter-turn.  Inputs are sampled independently of the
private setting, so demonstration labels teach the rule difference.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "af373b71d67d"
PARAMETER_NAME = "turn_direction"
DIRECTIONS = ("clockwise", "counterclockwise")
DEFAULT_SETTINGS = {PARAMETER_NAME: "clockwise"}

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
COUNTERCLOCKWISE_PROGRAM = (_HOME / "counterclockwise.rkt").read_text(encoding="utf-8")

MOTIFS = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
)
FRAME_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)

# h, w, motif_top, motif_left, inclusive frame bbox.
DEMO_SPECS = (
    (12, 15, 1, 1, (3, 7, 10, 14)),
    (14, 16, 10, 1, (1, 6, 8, 15)),
    (13, 18, 1, 14, (3, 1, 12, 10)),
    (16, 20, 12, 16, (0, 0, 9, 11)),
    (18, 22, 1, 1, (5, 8, 17, 21)),
    (20, 24, 16, 1, (1, 8, 13, 22)),
)
QUERY_SPECS = (
    (13, 17, 1, 1, (4, 8, 12, 16)),
    (17, 19, 13, 15, (0, 0, 10, 11)),
    (24, 26, 1, 21, (4, 1, 22, 18)),
    (30, 30, 27, 0, (0, 6, 23, 29)),
)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain only {PARAMETER_NAME}")
    value = settings[PARAMETER_NAME]
    if type(value) is not str or value not in DIRECTIONS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {DIRECTIONS}")
    return value


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: Any) -> str:
    direction = _validate_settings(settings)
    return CANONICAL_PROGRAM if direction == "clockwise" else COUNTERCLOCKWISE_PROGRAM


def counterfactual_program(settings: Any) -> str:
    """Opposite-direction Racket source for a wrong-intermediate witness."""
    direction = _validate_settings(settings)
    return COUNTERCLOCKWISE_PROGRAM if direction == "clockwise" else CANONICAL_PROGRAM


def _normalize(cells) -> tuple[tuple[int, int], ...]:
    cells = tuple((int(r), int(c)) for r, c in cells)
    if not cells:
        raise ValueError("motif cannot be empty")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    max_r = max(r for r, _ in cells)
    return _normalize((c, max_r - r) for r, c in cells)


def _rotate_ccw(cells) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    max_c = max(c for _, c in cells)
    return _normalize((max_c - c, r) for r, c in cells)


def _rotate_half(cells) -> tuple[tuple[int, int], ...]:
    return _rotate_cw(_rotate_cw(cells))


def _shape(cells) -> tuple[int, int]:
    cells = _normalize(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _color_components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while pending:
        start = min(pending)
        pending.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in pending:
                    pending.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(sorted(cells))
    return result


def _border_cells(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = bbox
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def inspect_scene(grid: Any) -> dict[str, Any]:
    grid = _validate_grid(grid)
    colors = sorted({cell for row in grid for cell in row if cell})
    frame_colors = [color for color in colors if color != 3]
    if 3 not in colors or len(frame_colors) != 1:
        raise ValueError("scene needs motif color 3 and exactly one other frame color")
    motif_components = _color_components(grid, 3)
    frame_components = _color_components(grid, frame_colors[0])
    if len(motif_components) != 1 or len(frame_components) != 1:
        raise ValueError("scene needs one motif component and one frame component")
    motif = motif_components[0]
    frame = frame_components[0]
    rows = [r for r, _ in frame]
    cols = [c for _, c in frame]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    if set(frame) != _border_cells(bbox):
        raise ValueError("frame must be an exact rectangular outline")
    if len(motif) < 2 or len(motif) > 5:
        raise ValueError("motif size must be 2..5")
    offsets = _normalize(motif)
    if offsets == _rotate_cw(offsets):
        raise ValueError("motif must change under a quarter turn")
    return {
        "motif_cells": [list(p) for p in motif],
        "normalized_offsets": [list(p) for p in offsets],
        "frame_cells": [list(p) for p in frame],
        "frame_bbox": list(bbox),
        "frame_anchor": [bbox[0] + 1, bbox[1] + 1],
        "frame_color": frame_colors[0],
    }


def oriented_motif_intermediate(grid: Any, settings: Any) -> dict[str, Any]:
    """Step A: extract and orient the input motif for the episode rule."""
    direction = _validate_settings(settings)
    facts = inspect_scene(grid)
    offsets = tuple(tuple(p) for p in facts["normalized_offsets"])
    oriented = _rotate_cw(offsets) if direction == "clockwise" else _rotate_ccw(offsets)
    return {
        "direction": direction,
        "source_offsets": [list(p) for p in offsets],
        "oriented_offsets": [list(p) for p in oriented],
        "frame_anchor": list(facts["frame_anchor"]),
        "frame_bbox": list(facts["frame_bbox"]),
    }


def _stamp(
    grid: list[list[int]],
    offsets,
    *,
    erase_source: bool = True,
    preserve_frame: bool = False,
) -> list[list[int]]:
    facts = inspect_scene(grid)
    output = copy.deepcopy(grid)
    if erase_source:
        for r, c in facts["motif_cells"]:
            output[r][c] = 0
    frame = {tuple(p) for p in facts["frame_cells"]}
    anchor_r, anchor_c = facts["frame_anchor"]
    for dr, dc in _normalize(offsets):
        r, c = anchor_r + dr, anchor_c + dc
        if not (0 <= r < len(output) and 0 <= c < len(output[0])):
            raise ValueError("oriented motif leaves grid")
        if not (preserve_frame and (r, c) in frame):
            output[r][c] = 3
    return output


def transform(grid: Any, settings: Any) -> list[list[int]]:
    grid = _validate_grid(copy.deepcopy(grid))
    intermediate = oriented_motif_intermediate(grid, settings)
    # Step B consumes the oriented offsets and frame anchor encoded by Step A.
    return _stamp(grid, intermediate["oriented_offsets"])


def build_scene(
    height: int,
    width: int,
    *,
    motif,
    motif_top: int,
    motif_left: int,
    frame: tuple[int, int, int, int],
    frame_color: int,
) -> list[list[int]]:
    _exact_int(height, "height", 1, 30)
    _exact_int(width, "width", 1, 30)
    if type(frame_color) is not int or frame_color not in FRAME_COLORS:
        raise ValueError("frame_color must be a declared non-green color")
    offsets = _normalize(motif)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    r0, c0, r1, c1 = frame
    if not (0 <= r0 < r1 < height and 0 <= c0 < c1 < width and r1 - r0 >= 3 and c1 - c0 >= 3):
        raise ValueError("invalid frame bbox")
    for r, c in _border_cells(frame):
        grid[r][c] = frame_color
    for dr, dc in offsets:
        r, c = motif_top + dr, motif_left + dc
        if not (0 <= r < height and 0 <= c < width) or grid[r][c] != 0:
            raise ValueError("motif placement is invalid")
        grid[r][c] = 3
    facts = inspect_scene(grid)
    frame_set = {tuple(p) for p in facts["frame_cells"]}
    if any(
        max(abs(r - fr), abs(c - fc)) <= 1
        for r, c in (tuple(p) for p in facts["motif_cells"])
        for fr, fc in frame_set
    ):
        raise ValueError("motif must be visually separated from frame")
    for direction in DIRECTIONS:
        oriented = oriented_motif_intermediate(grid, {PARAMETER_NAME: direction})
        ar, ac = oriented["frame_anchor"]
        if any(not (0 <= ar + dr < height and 0 <= ac + dc < width) for dr, dc in oriented["oriented_offsets"]):
            raise ValueError("one declared setting leaves grid")
    return grid


def _stable_seed(seed: int, label: str) -> int:
    payload = f"{TASK_ID}:{seed}:{label}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _scene_from_spec(seed: int, index: int, spec) -> list[list[int]]:
    h, w, mt, ml, frame = spec
    rng = random.Random(_stable_seed(seed, f"scene:{index}"))
    motif = MOTIFS[(index + rng.randrange(len(MOTIFS))) % len(MOTIFS)]
    for _ in range(rng.randrange(4)):
        motif = _rotate_cw(motif)
    color = FRAME_COLORS[(index + rng.randrange(len(FRAME_COLORS))) % len(FRAME_COLORS)]
    return build_scene(h, w, motif=motif, motif_top=mt, motif_left=ml, frame=frame, frame_color=color)


def _banks(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = [_scene_from_spec(seed, i, spec) for i, spec in enumerate(DEMO_SPECS)]
    queries = [_scene_from_spec(seed, 100 + i, spec) for i, spec in enumerate(QUERY_SPECS)]
    random.Random(_stable_seed(seed, "query-presentation")).shuffle(queries)
    return demos, queries


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    _validate_settings(settings)
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    demo_inputs, query_inputs = _banks(seed)
    chosen_demos = demo_inputs[:demos]
    chosen_queries = query_inputs[:queries]
    return {
        "train": [{"input": grid, "output": transform(grid, settings)} for grid in chosen_demos],
        "test": [{"input": grid, "output": transform(grid, settings)} for grid in chosen_queries],
        "program_solution": program(settings),
    }


def _fixed_output(grid, orientation: Callable, *, erase_source: bool = True) -> list[list[int]]:
    facts = inspect_scene(grid)
    return _stamp(grid, orientation(facts["normalized_offsets"]), erase_source=erase_source)


SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "unrotated": lambda grid: _fixed_output(grid, _normalize),
    "half_turn": lambda grid: _fixed_output(grid, _rotate_half),
    "keep_source_clockwise": lambda grid: _fixed_output(grid, _rotate_cw, erase_source=False),
    "keep_source_counterclockwise": lambda grid: _fixed_output(grid, _rotate_ccw, erase_source=False),
}


def lesson_certificate(train: list[dict], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    if type(train) is not list or not train:
        raise ValueError("train must be nonempty")
    settings_space = [{PARAMETER_NAME: value} for value in DIRECTIONS]
    surviving_settings = [
        setting
        for setting in settings_space
        if all(transform(pair["input"], setting) == pair["output"] for pair in train)
    ]
    surviving_shortcuts = [
        name
        for name, rival in SHORTCUTS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in train)
    ]
    return {
        "scope": "finite declared settings and four executable shortcuts",
        "surviving_settings": surviving_settings,
        "surviving_shortcuts": surviving_shortcuts,
        "query_count": len(query_inputs),
        "query_outputs_consulted": False,
    }


def public_projection(challenge: dict) -> dict:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in challenge["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in challenge["test"]],
    }


def public_bytes(challenge: dict) -> bytes:
    return (json.dumps(public_projection(challenge), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def public_id(challenge: dict) -> str:
    return hashlib.sha256(public_bytes(challenge)).hexdigest()


def visible_turn(challenge: dict, index: int) -> dict:
    if type(index) is not int or not 0 <= index < len(challenge["test"]):
        raise ValueError("turn index out of range")
    return {
        "train": public_projection(challenge)["train"],
        "test": [{"input": copy.deepcopy(challenge["test"][index]["input"])}],
    }


def visible_turn_bytes(challenge: dict, index: int) -> bytes:
    return (json.dumps(visible_turn(challenge, index), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
