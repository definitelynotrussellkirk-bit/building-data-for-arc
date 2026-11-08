"""Parametric nested-frame family for public ARC parent 45a5af55."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("full", "longest_run_core")


def integer(value, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30 or
            type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("expected a rectangular 1..30 exact-integer grid")
    width = len(value[0])
    for row in value:
        if (type(row) is not list or len(row) != width or
                any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)):
            raise ValueError("expected a rectangular 1..30 exact-integer grid")
    return value


def strip_colors(value) -> list[int]:
    grid(value)
    if len(value) < 2 or 2 * (len(value) - 1) > 30:
        raise ValueError("strip height must produce a 2..30 square")
    colors = []
    for row in value:
        if any(cell != row[0] for cell in row):
            raise ValueError("every strip row must be uniform")
        colors.append(row[0])
    if colors[-1] != colors[-2]:
        raise ValueError("the terminal cap must duplicate the preceding row")
    return colors[:-1]


def setting(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"view"} or
            type(settings["view"]) is not str or settings["view"] not in MODES):
        raise ValueError("settings must name exactly one declared view")
    return settings["view"]


def program(settings) -> str:
    mode = setting(settings)
    filename = "canonical.rkt" if mode == "full" else "longest-run-core.rkt"
    return (HERE / filename).read_text()


def _longest_run(colors: list[int]) -> tuple[int, int]:
    best_start = 0
    best_length = 1
    start = 0
    while start < len(colors):
        end = start + 1
        while end < len(colors) and colors[end] == colors[start]:
            end += 1
        length = end - start
        if length > best_length:
            best_start, best_length = start, length
        start = end
    return best_start, best_length


def intermediate(value) -> dict:
    colors = strip_colors(value)
    start, length = _longest_run(colors)
    return {
        "effective_colors": colors,
        "longest_run_start": start,
        "longest_run_length": length,
    }


def _rings(colors: list[int], start: int = 0) -> list[list[int]]:
    kept = len(colors) - start
    side = 2 * kept
    return [
        [colors[start + min(r, c, side - 1 - r, side - 1 - c)] for c in range(side)]
        for r in range(side)
    ]


def solve(value, mode: str = "full") -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("unknown view")
    colors = strip_colors(value)
    start = 0 if mode == "full" else _longest_run(colors)[0]
    return _rings(colors, start)


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"public_eval_45a5af55:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def scene(seed: int, index: int, *, stress: bool = False) -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 2**31 - 1, "index")
    if type(stress) is not bool:
        raise ValueError("stress must be boolean")
    profile = index % 10
    heights = (8, 9, 10, 11, 12, 13, 14, 15, 15, 16)
    widths = (3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
    height = 16 if stress else heights[profile]
    width = widths[profile]
    n = height - 1
    rng = _rng(seed, f"scene:{index}:{int(stress)}")
    palette = list(range(10))
    rng.shuffle(palette)
    cycle = palette[:6]
    offset = rng.randrange(len(cycle))
    colors = [cycle[(offset + i) % len(cycle)] for i in range(n)]
    pivot = 1 + ((profile * 3 + rng.randrange(max(1, n - 4))) % (n - 4))
    forbidden = {colors[pivot - 1], colors[pivot + 3]}
    run_color = next(color for color in cycle if color not in forbidden)
    colors[pivot:pivot + 3] = [run_color] * 3
    rows = [[color] * width for color in colors]
    rows.append(rows[-1][:])
    # Both programs must be total on every generated grid.
    solve(rows, "full")
    solve(rows, "longest_run_core")
    return rows


def generate(seed: int, settings, demos: int = 2, queries: int = 4) -> dict:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    mode = setting(settings)

    def pair(index: int) -> dict:
        inp = scene(seed, index)
        return {"input": inp, "output": solve(inp, mode)}

    return {
        "train": [pair(i) for i in range(demos)],
        "test": [pair(i) for i in range(6, 6 + queries)],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
    }


def query_order(presentation_seed: int = 0) -> list[int]:
    integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    _rng(presentation_seed, "presentation").shuffle(order)
    return order


def public_turn(episode, turn: int, *, presentation_seed: int = 0) -> dict:
    integer(turn, 0, 3, "turn")
    if (type(episode) is not dict or type(episode.get("train")) is not list or
            not 2 <= len(episode["train"]) <= 6 or
            type(episode.get("test")) is not list or len(episode["test"]) != 4):
        raise ValueError("project from a complete episode with four private queries")
    index = query_order(presentation_seed)[turn]
    train = []
    for pair in episode["train"]:
        train.append({"input": copy.deepcopy(grid(pair["input"])),
                      "output": copy.deepcopy(grid(pair["output"]))})
    return {
        "train": train,
        "test": [{"input": copy.deepcopy(grid(episode["test"][index]["input"]))}],
    }
