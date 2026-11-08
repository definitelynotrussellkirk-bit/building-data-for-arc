"""Native anti-diagonal copy family with a post-copy component relay.

``copy_only`` is the exact canonical program. ``largest_after_copy`` first
performs that copy, then finds the unique largest monochromatic 8-connected
object in the copied intermediate and recolors it yellow (4).  The sampler
constructs a rank inversion: a larger source-side distractor is largest before
copying, while a smaller near-axis diagonal cluster joins its reflected copy
and becomes uniquely largest only after stage A.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = "bbbec840ce41"
FINISHES = ("copy_only", "largest_after_copy")
DEFAULT_FINISH = "copy_only"
DEMO_SIZES = (8, 10, 12, 14, 16, 18)
QUERY_SIZES = (20, 24, 28, 30)
PALETTE = (1, 2, 3, 5, 6, 7, 8, 9)
DELTAS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be an exact dictionary")
    if set(settings) != {"finish"}:
        raise ValueError("settings must name exactly finish")
    finish = settings["finish"]
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be copy_only or largest_after_copy")
    return finish


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if len(value) != width:
        raise ValueError("anti-diagonal family requires a square grid")
    return [row[:] for row in value]


def program(settings: dict[str, Any]) -> str:
    finish = _finish(settings)
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if finish == "copy_only":
        return canonical
    from puzzle_generators.rule_wrap import wrap_rule

    copied = wrap_rule(canonical)
    return f"""(rule! (lambda (g)
  (define copied ({copied} g))
  (define objs (objects-8 copied 0))
  (if (null? objs)
      copied
      (let ((winner (pick-max objs obj-size)))
        (paint-cells copied (obj-cells winner) 4)))))"""


def counterfactual_program() -> str:
    """Wrong intermediate: rank objects before the canonical copy stage."""
    from puzzle_generators.rule_wrap import wrap_rule

    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    copied = wrap_rule(canonical)
    return f"""(rule! (lambda (g)
  (define n (rows g))
  (define pre (objects-8 g 0))
  (define copied ({copied} g))
  (if (null? pre)
      copied
      (let* ((winner (pick-max pre obj-size))
             (cells (obj-cells winner))
             (mirrors (map (lambda (p)
                             (list (- n 1 (second p))
                                   (- n 1 (first p))))
                           cells)))
        (paint-cells copied (append cells mirrors) 4)))))"""


def four_connected_program() -> str:
    from puzzle_generators.rule_wrap import wrap_rule

    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    copied = wrap_rule(canonical)
    return f"""(rule! (lambda (g)
  (define copied ({copied} g))
  (define objs (objects copied 0))
  (if (null? objs)
      copied
      (paint-cells copied (obj-cells (pick-max objs obj-size)) 4))))"""


def _components(grid: list[list[int]], *, connectivity: int = 8) -> list[dict[str, Any]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    pending = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if source[r][c] != 0
    }
    deltas = DELTAS_8 if connectivity == 8 else ((-1, 0), (1, 0), (0, -1), (0, 1))
    result: list[dict[str, Any]] = []
    while pending:
        start = min(pending)
        color = source[start[0]][start[1]]
        pending.remove(start)
        cells = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in deltas:
                nxt = row + dr, col + dc
                if nxt in pending and source[nxt[0]][nxt[1]] == color:
                    pending.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        result.append({"color": color, "cells": cells})
    return sorted(result, key=lambda obj: (min(obj["cells"]), obj["color"]))


def _ranked(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(objects, key=lambda obj: (-len(obj["cells"]), min(obj["cells"]), obj["color"]))


def copy_across_antidiagonal(grid: list[list[int]]) -> list[list[int]]:
    source = _grid(grid)
    n = len(source)
    output = [row[:] for row in source]
    for row in range(n):
        for col in range(n):
            value = source[row][col]
            if value:
                output[n - 1 - col][n - 1 - row] = value
    return output


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    finish = _finish(settings)
    copied = copy_across_antidiagonal(grid)
    if finish == "copy_only":
        return copied
    objects = _ranked(_components(copied, connectivity=8))
    if not objects:
        return copied
    output = [row[:] for row in copied]
    for row, col in objects[0]["cells"]:
        output[row][col] = 4
    return output


def wrong_intermediate_transform(grid: list[list[int]]) -> list[list[int]]:
    source = _grid(grid)
    n = len(source)
    copied = copy_across_antidiagonal(source)
    pre = _ranked(_components(source, connectivity=8))
    if not pre:
        return copied
    cells = set(pre[0]["cells"])
    cells.update((n - 1 - col, n - 1 - row) for row, col in list(cells))
    output = [row[:] for row in copied]
    for row, col in cells:
        output[row][col] = 4
    return output


def relay_state(grid: list[list[int]]) -> dict[str, Any]:
    source = _grid(grid)
    n = len(source)
    copied = copy_across_antidiagonal(source)
    pre = _ranked(_components(source, connectivity=8))
    post = _ranked(_components(copied, connectivity=8))
    winner = post[0] if post else {"cells": set(), "color": 0}
    relay_source = {
        cell for cell in winner["cells"] if sum(cell) < n - 1
    }
    return {
        "intermediate": copied,
        "pre_largest_cells": sorted(pre[0]["cells"]) if pre else [],
        "pre_largest_size": len(pre[0]["cells"]) if pre else 0,
        "post_largest_cells": sorted(winner["cells"]),
        "post_largest_size": len(winner["cells"]),
        "post_second_size": len(post[1]["cells"]) if len(post) > 1 else 0,
        "relay_source_size": len(relay_source),
        "unique_post_largest": bool(post) and (len(post) == 1 or len(post[0]["cells"]) > len(post[1]["cells"])),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"bbbec840ce41/anti-copy-relay-v1/{seed}/{split}/{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _place(grid: list[list[int]], cells: list[tuple[int, int]], color: int) -> None:
    n = len(grid)
    for row, col in cells:
        if not (0 <= row < n and 0 <= col < n):
            raise ValueError("component does not fit")
        if row + col >= n - 1:
            raise ValueError("sources must stay strictly above the anti-diagonal")
        if grid[row][col] != 0:
            raise ValueError("source components overlap")
    for row, col in cells:
        grid[row][col] = color


def _scene(seed: int, split: str, index: int, n: int) -> list[list[int]]:
    _integer(n, 8, 30, "n")
    rng = _rng(seed, split, index)
    colors = list(PALETTE)
    rng.shuffle(colors)
    k = max(2, min(7, n // 4))
    grid = [[0 for _ in range(n)] for _ in range(n)]

    # The source-side distractor is uniquely largest before stage A.
    _place(grid, [(0, col) for col in range(k + 1)], colors[0])
    _place(grid, [(2, col) for col in range(k)], colors[1])
    tertiary = max(2, k - 1)
    _place(grid, [(4, col) for col in range(tertiary)], colors[2])

    occupied = {(r, c) for r in range(n) for c in range(n) if grid[r][c]}
    starts = []
    for start in range(0, n - k - 1):
        cells = [(start + offset, n - 2 - start - offset) for offset in range(k)]
        if all(cell not in occupied for cell in cells):
            starts.append(start)
    if not starts:
        raise ValueError("no relay placement fits")
    start = rng.choice(starts)
    relay = [(start + offset, n - 2 - start - offset) for offset in range(k)]
    _place(grid, relay, colors[3])

    # Add unique-color singletons to broaden palettes and boundary positions.
    singleton_count = min(4, max(1, n // 8 + 1))
    candidates = [
        (row, col)
        for row in range(n)
        for col in range(n)
        if row + col < n - 1 and grid[row][col] == 0
    ]
    rng.shuffle(candidates)
    for color, cell in zip(colors[4:4 + singleton_count], candidates):
        _place(grid, [cell], color)

    state = relay_state(grid)
    if (
        not state["unique_post_largest"]
        or state["pre_largest_size"] <= state["relay_source_size"]
        or state["post_largest_size"] != 2 * state["relay_source_size"]
        or state["pre_largest_cells"] == state["post_largest_cells"]
    ):
        raise RuntimeError("constructed rank inversion failed")
    return grid


def sample_input(seed: int, split: str, index: int, *, n: int | None = None) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    limits = DEMO_SIZES if split == "train" else QUERY_SIZES
    _integer(index, 0, len(limits) - 1, "index")
    size = limits[index] if n is None else _integer(n, 8, 30, "n")
    return _scene(seed, split, index, size)


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    finish = _finish(settings)
    selected = {"finish": finish}
    train = []
    test = []
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, selected)})
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(selected),
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict:
        raise TypeError("episode must be a dictionary")
    if type(query_index) is not int or isinstance(query_index, bool):
        raise ValueError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("query_index is outside the stored query range")
    return {
        "train": deepcopy(train),
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }
