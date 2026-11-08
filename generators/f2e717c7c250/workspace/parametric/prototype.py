"""Native crop-then-dominant-key rotation family for f2e717c7c250."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "f2e717c7c250"
POSTPROCESSES = ("crop_only", "dominant_key_rotate")
DEFAULT_POSTPROCESS = "crop_only"
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8").rstrip("\n")
DOMINANT_ROTATE_PROGRAM = Path(__file__).with_name("dominant_key_rotate.rkt").read_text(encoding="utf-8").rstrip("\n")
WRONG_DIRECTION_PROGRAM = Path(__file__).with_name("wrong_direction.rkt").read_text(encoding="utf-8").rstrip("\n")

_DEMO_SPECS = (
    (12, 16, (0, 1, 3, 4), (6, 11, 2, 3)),
    (13, 17, (1, 11, 2, 3), (7, 1, 3, 5)),
    (15, 19, (1, 1, 4, 4), (9, 13, 2, 4)),
    (18, 20, (2, 13, 3, 3), (10, 1, 3, 6)),
    (20, 24, (0, 2, 4, 5), (13, 17, 3, 4)),
    (24, 28, (15, 20, 2, 5), (1, 1, 3, 7)),
)
_QUERY_SPECS = (
    (14, 18, (1, 12, 2, 4), (7, 1, 3, 5)),
    (17, 21, (1, 1, 3, 6), (10, 15, 2, 5)),
    (22, 27, (14, 20, 3, 4), (1, 1, 4, 5)),
    (30, 30, (0, 0, 6, 6), (24, 24, 4, 6)),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"postprocess"}:
        raise ValueError("settings must contain exactly postprocess")
    value = settings["postprocess"]
    if type(value) is not str or value not in POSTPROCESSES:
        raise ValueError(f"postprocess must be one of {POSTPROCESSES}")
    return {"postprocess": value}


def rule_text(postprocess: str) -> str:
    if postprocess == "crop_only":
        return CANONICAL_PROGRAM
    if postprocess == "dominant_key_rotate":
        return DOMINANT_ROTATE_PROGRAM
    raise ValueError(f"unknown postprocess {postprocess!r}")


def counterfactual_program() -> str:
    return WRONG_DIRECTION_PROGRAM


def _mix(*parts: object) -> int:
    text = ":".join(map(str, (TASK_ID, "dominant-key-rotate-v1", *parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid[::-1]]


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    if type(grid) is not list or len(grid) < 3 or type(grid[0]) is not list or not grid[0]:
        raise ValueError("input must contain header, separator and body")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("input must be rectangular")
    keys = [value for value in grid[0] if value != 0]
    if len(keys) != 2 or len(set(keys)) != 2:
        raise ValueError("header must contain exactly two distinct keys")
    if any(grid[1]):
        raise ValueError("separator row must be blank")
    body = [row[:] for row in grid[2:]]
    cells = [(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value in keys]
    if not cells:
        raise ValueError("body has no key-colored cells")
    counts = [sum(value == key for row in body for value in row) for key in keys]
    if 0 in counts or counts[0] == counts[1]:
        raise ValueError("each key must occur and key counts must be unequal")
    r1 = min(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    r2 = max(r for r, _ in cells)
    c2 = max(c for _, c in cells)
    crop = [row[c1:c2 + 1] for row in body[r1:r2 + 1]]
    return {
        "keys": keys,
        "counts": counts,
        "dominant_key_index": 0 if counts[0] > counts[1] else 1,
        "bbox": (r1, c1, r2, c2),
        "crop": crop,
    }


def apply_postprocess(grid: list[list[int]], postprocess: str) -> list[list[int]]:
    facts = analyze(grid)
    crop = facts["crop"]
    if postprocess == "crop_only":
        return deepcopy(crop)
    if postprocess == "dominant_key_rotate":
        return rotate_cw(crop) if facts["dominant_key_index"] == 0 else rotate_ccw(crop)
    raise ValueError(f"unknown postprocess {postprocess!r}")


def apply_wrong_direction(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze(grid)
    return rotate_ccw(facts["crop"]) if facts["dominant_key_index"] == 0 else rotate_cw(facts["crop"])


def _paint_rect(body, spec, color):
    top, left, height, width = spec
    for r in range(top, top + height):
        for c in range(left, left + width):
            if body[r][c] != 0:
                raise ValueError("scene rectangles overlap")
            body[r][c] = color


def _transform(body: list[list[int]], seed: int, split: str, index: int):
    mode = _mix(seed, split, index, "transform") % 4
    if mode == 1:
        return _flip_lr(body)
    if mode == 2:
        return _flip_ud(body)
    if mode == 3:
        return rotate_180(body)
    return [row[:] for row in body]


def _build_input(seed: int, split: str, index: int, spec) -> list[list[int]]:
    height, width, first, second = spec
    body_h = height - 2
    rng = random.Random(_mix(seed, split, index, "colors"))
    key_colors = sorted(rng.sample(range(1, 10), 2))
    remaining = [color for color in range(1, 10) if color not in key_colors]
    distractor_colors = rng.sample(remaining, 3)
    body = [[0 for _ in range(width)] for _ in range(body_h)]
    _paint_rect(body, first, key_colors[0])
    _paint_rect(body, second, key_colors[1])

    key_cells = [(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value in key_colors]
    r1, c1 = min(r for r, _ in key_cells), min(c for _, c in key_cells)
    r2, c2 = max(r for r, _ in key_cells), max(c for _, c in key_cells)
    modulus = 5 if (height, width) == (30, 30) else 9
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if body[r][c] == 0 and _mix(seed, split, index, r, c, "inside") % modulus == 0:
                body[r][c] = distractor_colors[(r + 2 * c + index) % len(distractor_colors)]

    # Place a small excluded distractor outside the selected box when space exists.
    outside = [
        (r, c) for r in range(body_h) for c in range(width)
        if not (r1 <= r <= r2 and c1 <= c <= c2) and body[r][c] == 0
    ]
    for r, c in outside[: min(5, len(outside))]:
        body[r][c] = distractor_colors[-1]

    body = _transform(body, seed, split, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    marker_columns = sorted(rng.sample(range(width), 2))
    for column, color in zip(marker_columns, key_colors):
        grid[0][column] = color
    grid[2:] = body
    facts = analyze(grid)
    expected_counts = [first[2] * first[3], second[2] * second[3]]
    if facts["counts"] != expected_counts:
        raise ValueError(f"key count drift: {facts['counts']} != {expected_counts}")
    if apply_postprocess(grid, "crop_only") == apply_postprocess(grid, "dominant_key_rotate"):
        raise ValueError("scene is invariant under its selected rotation")
    return grid


def _pair(seed: int, split: str, index: int, spec, postprocess: str):
    grid = _build_input(seed, split, index, spec)
    return {"input": grid, "output": apply_postprocess(grid, postprocess)}


def generate_episode(seed: int, *, postprocess: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1 (not bool)")
    if postprocess not in POSTPROCESSES:
        raise ValueError(f"unknown postprocess {postprocess!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [_pair(seed, "train", i, _DEMO_SPECS[i], postprocess) for i in range(demos)]
    test = [_pair(seed, "test", i, _QUERY_SPECS[i], postprocess) for i in range(queries)]
    return {"train": train, "test": test, "program_solution": rule_text(postprocess)}


def public_turn(episode: dict[str, Any], query_index: int = 0):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a retained query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return (json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")) + "\n").encode()


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0):
    episode = generate_episode(seed, postprocess="dominant_key_rotate", demos=2, queries=4)
    pair = next(pair for pair in episode["train"] + episode["test"] if apply_wrong_direction(pair["input"]) != pair["output"])
    facts = analyze(pair["input"])
    return {
        "settings": {"postprocess": "dominant_key_rotate"},
        "program": DOMINANT_ROTATE_PROGRAM,
        "input": deepcopy(pair["input"]),
        "output": deepcopy(pair["output"]),
        "intermediate_value": {
            "canonical_crop_bbox": list(facts["bbox"]),
            "key_cell_counts": facts["counts"],
            "dominant_key_index": facts["dominant_key_index"],
        },
        "counterfactual_program": WRONG_DIRECTION_PROGRAM,
        "counterfactual_output": apply_wrong_direction(pair["input"]),
        "ablation": "wrong_intermediate",
    }
