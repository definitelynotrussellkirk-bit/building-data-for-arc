"""Native parametric family for 1b6b40a92e4f.

The canonical setting independently normalizes the red and green footprints and
then overlays them.  The alternate keeps the same two-stage reasoning but rotates
the normalized green intermediate clockwise before the overlay.  Input sampling
is setting-independent and each ordinary teaching pair separates the settings.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "1b6b40a92e4f"
HOME = Path(__file__).resolve().parent
MODES = ("as_is", "rotate_cw")
CANONICAL = (HOME / "canonical.rkt").read_text(encoding="utf-8")

ROTATE_CW = r'''(rule!
  (let* ((cells2 (normalize-cells (find-color g 2)))
         (raw3 (normalize-cells (find-color g 3)))
         (max-r3 (if (empty? raw3) 0 (apply max (map first raw3))))
         (cells3 (if (empty? raw3)
                     raw3
                     (normalize-cells
                       (map (lambda (p)
                              (list (second p) (- max-r3 (first p))))
                            raw3))))
         (both (append cells2 cells3)))
    (if (empty? both)
        (list (list 0))
        (let ((max-r (apply max (map first both)))
              (max-c (apply max (map second both))))
          (grid-from-fn (+ max-r 1) (+ max-c 1)
            (lambda (r c)
              (let ((p (list r c)))
                (cond [(and (member? p cells2) (member? p cells3)) 8]
                      [(member? p cells2) 2]
                      [(member? p cells3) 3]
                      [else 0]))))))))'''

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Canvas, target size per footprint, growth box.  The final query is a genuine
# 30x30 scene with >70 active cells and opposite-corner boundary contacts.
_TRAIN_SPECS = (
    (12, 14, 7, 8, 5, 5),
    (13, 16, 8, 9, 5, 6),
    (15, 18, 10, 11, 6, 6),
    (17, 20, 12, 13, 7, 7),
    (19, 22, 14, 15, 8, 8),
    (21, 24, 16, 18, 8, 9),
)
_QUERY_SPECS = (
    (14, 18, 12, 14, 7, 7),
    (18, 22, 18, 20, 8, 9),
    (24, 28, 28, 30, 10, 11),
    (30, 30, 38, 38, 12, 12),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_mode(mode: Any) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"green_pose must be one of {list(MODES)}")
    return mode


def program_for(mode: str) -> str:
    mode = validate_mode(mode)
    return CANONICAL if mode == "as_is" else ROTATE_CW


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    if not cells:
        return cells
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _orient(cells: Iterable[tuple[int, int]], orientation: str) -> frozenset[tuple[int, int]]:
    cells = _normalize(cells)
    if not cells:
        return cells
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    if orientation == "as_is":
        result = cells
    elif orientation == "rotate_cw":
        result = {(c, height - 1 - r) for r, c in cells}
    elif orientation == "rotate_ccw":
        result = {(width - 1 - c, r) for r, c in cells}
    elif orientation == "rotate_180":
        result = {(height - 1 - r, width - 1 - c) for r, c in cells}
    elif orientation == "mirror_lr":
        result = {(r, width - 1 - c) for r, c in cells}
    else:
        raise ValueError(f"unknown orientation: {orientation}")
    return _normalize(result)


def _color_cells(grid: list[list[int]], color: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    )


def intermediate(grid: list[list[int]], mode: str) -> dict[str, list[list[int]]]:
    mode = validate_mode(mode)
    red = _normalize(_color_cells(grid, 2))
    green = _orient(_color_cells(grid, 3), mode)
    return {
        "normalized_red": [list(cell) for cell in sorted(red)],
        "green_after_pose": [list(cell) for cell in sorted(green)],
    }


def _overlay(red: Iterable[tuple[int, int]], green: Iterable[tuple[int, int]], *, swap=False, union8=False, bottom_right=False) -> list[list[int]]:
    red = _normalize(red)
    green = _normalize(green)
    if bottom_right and red and green:
        height = max(max(r for r, _ in red), max(r for r, _ in green)) + 1
        width = max(max(c for _, c in red), max(c for _, c in green)) + 1
        red_h, red_w = max(r for r, _ in red) + 1, max(c for _, c in red) + 1
        green_h, green_w = max(r for r, _ in green) + 1, max(c for _, c in green) + 1
        red = {(r + height - red_h, c + width - red_w) for r, c in red}
        green = {(r + height - green_h, c + width - green_w) for r, c in green}
    both = set(red) | set(green)
    if not both:
        return [[0]]
    height = max(r for r, _ in both) + 1
    width = max(c for _, c in both) + 1
    result = [[0] * width for _ in range(height)]
    for r, c in both:
        in_red, in_green = (r, c) in red, (r, c) in green
        if union8:
            value = 8
        elif in_red and in_green:
            value = 8
        elif in_red:
            value = 3 if swap else 2
        else:
            value = 2 if swap else 3
        result[r][c] = value
    return result


def transform(grid: list[list[int]], mode: str) -> list[list[int]]:
    mode = validate_mode(mode)
    red = _normalize(_color_cells(grid, 2))
    green = _orient(_color_cells(grid, 3), mode)
    return _overlay(red, green)


def rival_transform(grid: list[list[int]], rival: str) -> list[list[int]]:
    red = _normalize(_color_cells(grid, 2))
    green = _normalize(_color_cells(grid, 3))
    if rival == "rotate_ccw_green":
        return _overlay(red, _orient(green, "rotate_ccw"))
    if rival == "rotate_180_green":
        return _overlay(red, _orient(green, "rotate_180"))
    if rival == "mirror_green":
        return _overlay(red, _orient(green, "mirror_lr"))
    if rival == "rotate_red":
        return _overlay(_orient(red, "rotate_cw"), green)
    if rival == "swap_exclusive_colors":
        return _overlay(red, green, swap=True)
    if rival == "paint_union_8":
        return _overlay(red, green, union8=True)
    if rival == "bottom_right_alignment":
        return _overlay(red, green, bottom_right=True)
    raise ValueError(f"unknown rival: {rival}")


RIVALS = (
    "rotate_ccw_green",
    "rotate_180_green",
    "mirror_green",
    "rotate_red",
    "swap_exclusive_colors",
    "paint_union_8",
    "bottom_right_alignment",
)


def _grow_poly(rng: random.Random, target: int, max_h: int, max_w: int) -> frozenset[tuple[int, int]]:
    if target > max_h * max_w:
        raise ValueError("target exceeds growth box")
    for _ in range(80):
        start = (rng.randrange(max_h), rng.randrange(max_w))
        cells = {start}
        while len(cells) < target:
            frontier = sorted({
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _CARD
                if 0 <= r + dr < max_h and 0 <= c + dc < max_w
                and (r + dr, c + dc) not in cells
            })
            if not frontier:
                break
            # Bias toward candidates that increase the current bounding box so
            # the stress footprints occupy a real region rather than a knot.
            top = min(r for r, _ in cells); bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells); right = max(c for _, c in cells)
            expanding = [p for p in frontier if p[0] < top or p[0] > bottom or p[1] < left or p[1] > right]
            pool = expanding * 2 + frontier
            cells.add(rng.choice(pool))
        if len(cells) != target:
            continue
        normalized = _normalize(cells)
        height = max(r for r, _ in normalized) + 1
        width = max(c for _, c in normalized) + 1
        if height >= min(3, max_h) and width >= min(3, max_w):
            return normalized
    raise RuntimeError("could not grow a connected polyomino")


def _candidate_is_teachable(red, green) -> bool:
    as_is = _overlay(red, green)
    rotated = _overlay(red, _orient(green, "rotate_cw"))
    if as_is == rotated:
        return False
    for posed_green in (green, _orient(green, "rotate_cw")):
        if not (set(red) & set(posed_green)):
            return False
        if not (set(red) - set(posed_green)) or not (set(posed_green) - set(red)):
            return False
    # Reject geometry on which common shortcuts accidentally coincide with
    # either declared setting.  This makes every two-demo prefix constructive.
    dummy = _place_pair(red, green, 30, 30, random.Random(0), stress=True)
    for mode in MODES:
        truth = transform(dummy, mode)
        other = transform(dummy, MODES[1 - MODES.index(mode)])
        if truth == other:
            return False
        if any(rival_transform(dummy, rival) == truth for rival in RIVALS):
            return False
    return True


def _place_pair(red, green, height: int, width: int, rng: random.Random, *, stress: bool) -> list[list[int]]:
    red = _normalize(red); green = _normalize(green)
    rh, rw = max(r for r, _ in red) + 1, max(c for _, c in red) + 1
    gh, gw = max(r for r, _ in green) + 1, max(c for _, c in green) + 1
    if stress:
        red_top, red_left = 0, 0
        green_top, green_left = height - gh, width - gw
    else:
        split = max(rw + 2, width // 2)
        if split + gw > width:
            split = width - gw
        red_left = rng.randint(0, max(0, split - rw - 1))
        green_left = rng.randint(split, width - gw)
        red_top = rng.randint(0, height - rh)
        green_top = rng.randint(0, height - gh)
        if rng.random() < 0.35:
            red_top = 0
        if rng.random() < 0.35:
            green_top = height - gh
    grid = [[0] * width for _ in range(height)]
    for r, c in red:
        grid[red_top + r][red_left + c] = 2
    for r, c in green:
        rr, cc = green_top + r, green_left + c
        if grid[rr][cc] != 0:
            raise RuntimeError("placement overlap")
        grid[rr][cc] = 3
    return grid


def _build_input(seed: int, index: int, spec: tuple[int, int, int, int, int, int], *, query: bool) -> list[list[int]]:
    height, width, red_size, green_size, max_h, max_w = spec
    rng = random.Random(f"{TASK_ID}:input:{seed}:{'query' if query else 'train'}:{index}")
    for _ in range(300):
        red = _grow_poly(rng, red_size, max_h, max_w)
        green = _grow_poly(rng, green_size, max_h, max_w)
        if not _candidate_is_teachable(red, green):
            continue
        grid = _place_pair(red, green, height, width, rng, stress=query and height == width == 30)
        if _valid_input(grid):
            return grid
    raise RuntimeError(f"could not construct teachable input {index}")


def _components(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells); count = 0
    while remaining:
        count += 1
        start = min(remaining); remaining.remove(start)
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt); queue.append(nxt)
    return count


def _valid_input(grid: list[list[int]]) -> bool:
    red, green = set(_color_cells(grid, 2)), set(_color_cells(grid, 3))
    if not red or not green or _components(red) != 1 or _components(green) != 1:
        return False
    if any(abs(r-r2) <= 1 and abs(c-c2) <= 1 for r,c in red for r2,c2 in green):
        return False
    return transform(grid, "as_is") != transform(grid, "rotate_cw")


@lru_cache(maxsize=128)
def _episode_inputs_cached(seed: int) -> tuple[tuple, tuple]:
    _integer(seed, 0, 2**63 - 1, "seed")
    train = tuple(_build_input(seed, index, spec, query=False) for index, spec in enumerate(_TRAIN_SPECS))
    queries = [_build_input(seed, index, spec, query=True) for index, spec in enumerate(_QUERY_SPECS)]
    order = list(range(4))
    random.Random(f"{TASK_ID}:presentation:{seed}").shuffle(order)
    test = tuple(queries[index] for index in order)
    serial = [json.dumps(grid, separators=(",", ":")) for grid in (*train, *test)]
    if len(serial) != len(set(serial)):
        raise RuntimeError("input bank must be globally distinct")
    return train, test


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    train, test = _episode_inputs_cached(_integer(seed, 0, 2**63 - 1, "seed"))
    return {"train": deepcopy(list(train)), "test": deepcopy(list(test))}


def teaching_check(pairs: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    mode = validate_mode(mode)
    survivors = [candidate for candidate in MODES if all(transform(pair["input"], candidate) == pair["output"] for pair in pairs)]
    rival_survivors = [rival for rival in RIVALS if all(rival_transform(pair["input"], rival) == pair["output"] for pair in pairs)]
    return {"mode": mode, "survivors": survivors, "rival_survivors": rival_survivors, "demonstrations": len(pairs)}


def generate_episode(seed: int, mode: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    mode = validate_mode(mode)
    inputs = episode_inputs(seed)
    pair = lambda grid: {"input": deepcopy(grid), "output": transform(grid, mode)}
    episode = {
        "train": [pair(grid) for grid in inputs["train"][:demos]],
        "test": [pair(grid) for grid in inputs["test"][:queries]],
        "program_solution": program_for(mode),
    }
    check = teaching_check(episode["train"], mode)
    if check["survivors"] != [mode] or check["rival_survivors"]:
        raise RuntimeError(f"teaching prefix failed: {check}")
    return episode


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a stored private query")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def input_metrics(grid: list[list[int]]) -> dict[str, Any]:
    height, width = len(grid), len(grid[0])
    red, green = set(_color_cells(grid, 2)), set(_color_cells(grid, 3))
    sides = []
    if any(r == 0 for r, _ in red | green): sides.append("top")
    if any(r == height - 1 for r, _ in red | green): sides.append("bottom")
    if any(c == 0 for _, c in red | green): sides.append("left")
    if any(c == width - 1 for _, c in red | green): sides.append("right")
    return {
        "shape": [height, width],
        "foreground_cells": len(red) + len(green),
        "red_components": _components(red),
        "green_components": _components(green),
        "boundary_sides": sides,
        "red_bbox": [max(r for r, _ in _normalize(red)) + 1, max(c for _, c in _normalize(red)) + 1],
        "green_bbox": [max(r for r, _ in _normalize(green)) + 1, max(c for _, c in _normalize(green)) + 1],
    }
