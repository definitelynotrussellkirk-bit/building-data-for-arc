"""Constructive native family for fixed and selector-parity marker crops."""
from __future__ import annotations

import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "9c3781759581"
VERSION = "native-selector-parity-v1"
POLICIES = ("fixed_color_9", "selector_parity")
_HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HERE / "canonical.rkt").read_text(encoding="utf-8")
SELECTOR_PROGRAM = (_HERE / "selector-parity.rkt").read_text(encoding="utf-8").rstrip("\n")
WRONG_SELECTOR_PROGRAM = (_HERE / "wrong-selector.rkt").read_text(encoding="utf-8").rstrip("\n")

_DEMO_DIMS = ((11, 13), (13, 12), (14, 15), (16, 14), (18, 19), (20, 18))
_QUERY_DIMS = ((17, 21), (22, 18), (24, 26), (30, 30))
_DEMO_SELECTOR_COUNTS = (1, 2, 3, 4, 5, 6)
_QUERY_SELECTOR_COUNTS = (3, 4, 5, 6)
_FILLERS = (1, 3, 4, 6, 7, 8)


def validate_settings(settings: Any) -> dict[str, str]:
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dictionary naming crop_policy")
    if set(settings) != {"crop_policy"}:
        raise ValueError("settings must name exactly crop_policy")
    value = settings["crop_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"crop_policy must be one of {POLICIES}")
    return {"crop_policy": value}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: Any) -> str:
    policy = validate_settings(settings)["crop_policy"]
    return CANONICAL_PROGRAM if policy == "fixed_color_9" else SELECTOR_PROGRAM


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}|{VERSION}|{seed}|{split}|{index}".encode("utf-8")
    number = int.from_bytes(hashlib.sha256(material).digest()[:16], "big")
    return random.Random(number)


def _inside(box: tuple[int, int, int, int], r: int, c: int) -> bool:
    r0, c0, r1, c1 = box
    return r0 <= r <= r1 and c0 <= c <= c1


def _paint_marker_box(
    grid: list[list[int]],
    box: tuple[int, int, int, int],
    marker: int,
    phase: int,
    rng: random.Random,
) -> None:
    r0, c0, r1, c1 = box
    extrema = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    # Extra side extrema make the marker texture less corner-only while retaining
    # the exact same inclusive bbox.
    extrema.add((r0, c0 + (c1 - c0) // 2))
    extrema.add((r0 + (r1 - r0) // 2, c1))
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r, c) in extrema:
                grid[r][c] = marker
            elif (3 * r + 5 * c + phase) % 7 in (0, 1):
                grid[r][c] = _FILLERS[(r + 2 * c + phase) % len(_FILLERS)]
            elif rng.random() < 0.08:
                grid[r][c] = _FILLERS[rng.randrange(len(_FILLERS))]
            else:
                grid[r][c] = 0


def _boxes(height: int, width: int, index: int, stress: bool) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    if stress:
        return (0, 0, 12, 14), (15, 16, 29, 29)
    h5 = 3 + index % 3
    w5 = 4 + (index + 1) % 3
    h9 = 4 + (index + 1) % 2
    w9 = 3 + (index + 2) % 4
    r5 = index % 2
    c5 = (2 * index + 1) % 3
    r9 = height - h9
    c9 = width - w9
    box5 = (r5, c5, r5 + h5 - 1, c5 + w5 - 1)
    box9 = (r9, c9, height - 1, width - 1)
    overlaps = not (
        box5[2] < box9[0]
        or box9[2] < box5[0]
        or box5[3] < box9[1]
        or box9[3] < box5[1]
    )
    if overlaps:
        raise RuntimeError("constructed candidate boxes overlap")
    return box5, box9


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    if split == "demo":
        height, width = _DEMO_DIMS[index]
        selector_count = _DEMO_SELECTOR_COUNTS[index]
    elif split == "query":
        height, width = _QUERY_DIMS[index]
        selector_count = _QUERY_SELECTOR_COUNTS[index]
    else:
        raise ValueError("split must be demo or query")
    rng = _rng(seed, split, index)
    stress = split == "query" and index == 3
    box5, box9 = _boxes(height, width, index, stress)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Sparse whole-canvas payload ensures realistic retained contents and makes
    # the 30x30 case substantive without introducing candidate colors.
    modulus = 7 if stress else 11
    for r in range(height):
        for c in range(width):
            if (r * 7 + c * 11 + seed + index) % modulus == 0:
                grid[r][c] = _FILLERS[rng.randrange(len(_FILLERS))]

    _paint_marker_box(grid, box5, 5, seed + index, rng)
    _paint_marker_box(grid, box9, 9, seed + index + 3, rng)

    candidates = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if not _inside(box5, r, c) and not _inside(box9, r, c)
    ]
    rng.shuffle(candidates)
    if len(candidates) < selector_count:
        raise RuntimeError("not enough selector positions")
    # Spread selectors instead of taking a local cluster from the shuffled list.
    chosen: list[tuple[int, int]] = []
    for r, c in candidates:
        if all(abs(r - rr) + abs(c - cc) >= 2 for rr, cc in chosen):
            chosen.append((r, c))
            if len(chosen) == selector_count:
                break
    if len(chosen) != selector_count:
        chosen = candidates[:selector_count]
    for r, c in chosen:
        grid[r][c] = 2

    # The stress scene explicitly touches every boundary with meaningful content.
    if stress:
        for r, c in ((0, 20), (29, 8), (8, 0), (21, 29)):
            if grid[r][c] not in (5, 9, 2):
                grid[r][c] = _FILLERS[(r + c) % len(_FILLERS)]

    facts = selector_intermediate(grid)
    if facts["selector_count"] != selector_count:
        raise RuntimeError("selector construction changed its exact count")
    if crop(grid, 5) == crop(grid, 9):
        raise RuntimeError("candidate crops must be distinct")
    return grid


def crop(grid: list[list[int]], color: int) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"color {color} is absent")
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def selector_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    count = sum(type(cell) is int and cell == 2 for row in grid for cell in row)
    if not 1 <= count <= 6:
        raise ValueError("selector color 2 must occur 1..6 times")
    parity = "odd" if count % 2 else "even"
    return {"selector_count": count, "selector_parity": parity, "target_color": 5 if parity == "odd" else 9}


def apply_policy(grid: list[list[int]], crop_policy: str) -> list[list[int]]:
    validate_settings({"crop_policy": crop_policy})
    target = 9 if crop_policy == "fixed_color_9" else selector_intermediate(grid)["target_color"]
    return crop(grid, target)


def apply_wrong_intermediate(grid: list[list[int]]) -> list[list[int]]:
    target = 9 if selector_intermediate(grid)["target_color"] == 5 else 5
    return crop(grid, target)


def counterfactual_program() -> str:
    return WRONG_SELECTOR_PROGRAM


def _pair(seed: int, split: str, index: int, policy: str) -> dict[str, list[list[int]]]:
    grid = _sample_input(seed, split, index)
    return {"input": grid, "output": apply_policy(grid, policy)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    policy = validate_settings(settings)["crop_policy"]
    return {
        "train": [_pair(seed, "demo", index, policy) for index in range(demos)],
        "test": [_pair(seed, "query", index, policy) for index in range(queries)],
        "program_solution": program({"crop_policy": policy}),
    }


def causal_case(episode: dict[str, Any]) -> dict[str, Any]:
    for split in ("train", "test"):
        for index, pair in enumerate(episode.get(split, [])):
            facts = selector_intermediate(pair["input"])
            wrong = apply_wrong_intermediate(pair["input"])
            if wrong != pair["output"]:
                return {
                    "split": split,
                    "pair_index": index,
                    "input": pair["input"],
                    "output": pair["output"],
                    "intermediate_value": facts,
                    "counterfactual_output": wrong,
                }
    raise ValueError("episode contains no distinguishing selector-parity case")
