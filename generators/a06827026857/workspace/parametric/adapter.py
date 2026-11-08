"""Native window-scope family for ``a06827026857``.

Every setting first discovers all solid monochrome nonzero 3x3 windows in the
original input.  The canonical ``all_windows`` setting paints the four corners
of every discovered window.  The ``dominant_color`` setting instead counts
windows per color and paints only windows of the unique most-supported color.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "a06827026857"
HERE = Path(__file__).resolve().parent
SETTINGS = ("all_windows", "dominant_color")
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

# (height, width, ((role, row, col, height, width), ...))
_DEMO_PROFILES = (
    (12, 18, (("decoy_a", 0, 0, 3, 4), ("dominant", 1, 8, 5, 5),
              ("decoy_b", 8, 0, 4, 4), ("decoy_a", 10, 7, 2, 8))),
    (16, 18, (("decoy_a", 0, 0, 3, 5), ("dominant", 1, 8, 3, 4),
              ("dominant", 7, 8, 3, 4), ("decoy_b", 11, 0, 3, 4),
              ("decoy_a", 14, 8, 2, 6))),
    (18, 20, (("decoy_a", 0, 0, 5, 3), ("dominant", 0, 10, 4, 6),
              ("decoy_b", 10, 0, 3, 6), ("decoy_c", 12, 12, 4, 4),
              ("decoy_a", 16, 0, 2, 6))),
    (20, 22, (("decoy_a", 0, 0, 4, 4), ("dominant", 1, 10, 6, 5),
              ("decoy_b", 12, 0, 5, 4), ("decoy_c", 12, 12, 3, 5),
              ("decoy_a", 18, 0, 2, 8))),
    (24, 25, (("decoy_a", 0, 0, 5, 4), ("dominant", 0, 11, 4, 5),
              ("dominant", 8, 11, 3, 5), ("decoy_b", 14, 0, 4, 5),
              ("decoy_a", 22, 0, 2, 8), ("noise", 22, 18, 2, 6))),
    (27, 29, (("decoy_a", 0, 0, 4, 8), ("dominant", 0, 14, 7, 6),
              ("decoy_b", 12, 0, 5, 5), ("decoy_c", 14, 14, 4, 6),
              ("decoy_a", 25, 0, 2, 6))),
)

_QUERY_PROFILES = (
    (14, 21, (("decoy_a", 0, 0, 3, 5), ("dominant", 0, 10, 5, 6),
              ("decoy_b", 8, 0, 4, 5), ("decoy_a", 12, 10, 2, 8))),
    (20, 20, (("decoy_a", 0, 0, 4, 5), ("dominant", 0, 10, 3, 5),
              ("dominant", 7, 10, 4, 4), ("decoy_b", 12, 0, 4, 5),
              ("decoy_a", 18, 0, 2, 6))),
    (25, 28, (("decoy_a", 0, 0, 5, 6), ("dominant", 0, 14, 7, 7),
              ("decoy_b", 13, 0, 5, 7), ("decoy_c", 15, 16, 4, 7),
              ("decoy_a", 23, 0, 2, 10))),
    # Lawful 30x30 stress: 371 foreground cells and 141 qualifying windows.
    (30, 30, (("decoy_a", 0, 0, 6, 6), ("dominant", 0, 12, 10, 8),
              ("decoy_b", 12, 0, 9, 7), ("dominant", 15, 19, 8, 9),
              ("decoy_a", 25, 0, 2, 30), ("decoy_a", 28, 0, 2, 30))),
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"window_scope"}:
        raise ValueError("settings must contain exactly window_scope")
    scope = value["window_scope"]
    if type(scope) is not str or scope not in SETTINGS:
        raise ValueError(f"window_scope must be one of {SETTINGS!r}")
    return {"window_scope": scope}


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _rng(seed: int, role: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:native-window-scope-v1:{seed}:{role}".encode()).digest()
    return random.Random(digest)


def _program_path(scope: str) -> Path:
    return HERE / ("canonical.rkt" if scope == "all_windows" else "dominant_color.rkt")


def program(settings: object) -> str:
    selected = _settings(settings)
    return _program_path(selected["window_scope"]).read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "wrong_first_color.rkt").read_text(encoding="utf-8")


def _windows(value: object) -> list[tuple[int, int, int]]:
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    found: list[tuple[int, int, int]] = []
    for r in range(max(0, h - 2)):
        for c in range(max(0, w - 2)):
            color = grid[r][c]
            if color != 0 and all(
                grid[r + dy][c + dx] == color
                for dy in range(3)
                for dx in range(3)
            ):
                found.append((r, c, color))
    return found


def _support(windows: Iterable[tuple[int, int, int]]) -> Counter[int]:
    return Counter(color for _r, _c, color in windows)


def _dominant_color(windows: list[tuple[int, int, int]]) -> tuple[int, bool]:
    counts = _support(windows)
    if not counts:
        raise ValueError("dominant_color requires at least one qualifying 3x3 window")
    maximum = max(counts.values())
    leaders = sorted(color for color, count in counts.items() if count == maximum)
    return leaders[0], len(leaders) == 1


def _paint(value: object, selected_color: int | None) -> list[list[int]]:
    grid = _grid(value)
    out = [[0] * len(grid[0]) for _ in grid]
    for r, c, color in _windows(grid):
        if selected_color is None or color == selected_color:
            for y, x in ((r, c), (r, c + 2), (r + 2, c), (r + 2, c + 2)):
                out[y][x] = color
    return out


def predict(value: object, settings: object) -> list[list[int]]:
    selected = _settings(settings)
    windows = _windows(value)
    if selected["window_scope"] == "all_windows":
        return _paint(value, None)
    dominant, _unique = _dominant_color(windows)
    return _paint(value, dominant)


def predict_first_color(value: object) -> list[list[int]]:
    windows = _windows(value)
    if not windows:
        return _paint(value, None)
    return _paint(value, windows[0][2])


def _palette(seed: int, split: str, index: int) -> dict[str, int]:
    colors = _rng(seed, f"{split}:{index}:palette").sample(range(1, 10), 5)
    return dict(zip(("dominant", "decoy_a", "decoy_b", "decoy_c", "noise"), colors))


def _scene(seed: int, split: str, index: int, profile: tuple) -> list[list[int]]:
    height, width, rectangles = profile
    grid = [[0] * width for _ in range(height)]
    palette = _palette(seed, split, index)
    for role, row, col, rect_h, rect_w in rectangles:
        color = palette[role]
        for r in range(row, row + rect_h):
            for c in range(col, col + rect_w):
                if grid[r][c] != 0:
                    raise RuntimeError("profile rectangles overlap")
                grid[r][c] = color
    return grid


def _demo_bank(seed: int) -> list[list[list[int]]]:
    return [_scene(seed, "demo", index, profile) for index, profile in enumerate(_DEMO_PROFILES)]


def _query_bank(seed: int) -> tuple[list[list[list[int]]], list[int]]:
    source = [_scene(seed, "query", index, profile) for index, profile in enumerate(_QUERY_PROFILES)]
    order = list(range(len(source)))
    _rng(seed, "query-permutation").shuffle(order)
    return [source[index] for index in order], order


def query_source_order(seed: object) -> list[int]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    return _query_bank(seed)[1]


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", *QUERY_LIMITS)
    demo_inputs = _demo_bank(seed)[:demos]
    query_inputs = _query_bank(seed)[0][:queries]
    all_inputs = demo_inputs + query_inputs
    keys = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("deterministic sampler produced duplicate inputs")
    pair = lambda grid: {"input": _copy(grid), "output": predict(grid, selected)}
    return {
        "train": [pair(grid) for grid in demo_inputs],
        "test": [pair(grid) for grid in query_inputs],
        "program_solution": program(selected),
    }


def surviving_settings(demos: Iterable[dict[str, object]]) -> list[dict[str, str]]:
    pairs = list(demos)
    survivors: list[dict[str, str]] = []
    for scope in SETTINGS:
        setting = {"window_scope": scope}
        if all(predict(pair["input"], setting) == pair["output"] for pair in pairs):
            survivors.append(setting)
    return survivors


def observe(value: object) -> dict[str, object]:
    grid = _grid(value)
    windows = _windows(grid)
    counts = _support(windows)
    dominant, unique = _dominant_color(windows)
    foreground = [(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell != 0]
    h, w = len(grid), len(grid[0])
    touches: list[str] = []
    if any(r == 0 for r, _c in foreground):
        touches.append("top")
    if any(r == h - 1 for r, _c in foreground):
        touches.append("bottom")
    if any(c == 0 for _r, c in foreground):
        touches.append("left")
    if any(c == w - 1 for _r, c in foreground):
        touches.append("right")
    return {
        "height": h,
        "width": w,
        "foreground_cells": len(foreground),
        "window_count": len(windows),
        "window_colors": sorted(counts),
        "support_by_color": dict(sorted(counts.items())),
        "dominant_color": dominant,
        "dominant_unique": unique,
        "first_window_color": windows[0][2],
        "touches": touches,
    }


def explain_dependency(value: object, settings: object) -> dict[str, object]:
    selected = _settings(settings)
    info = observe(value)
    scope = selected["window_scope"]
    return {
        "step_a": "Scan the original grid for every solid monochrome nonzero 3x3 window and count qualifying windows by color.",
        "intermediate": "The row-major window records, per-color support counts, and unique input-derived dominant color.",
        "step_b": (
            "Paint the four corners of every qualifying window."
            if scope == "all_windows"
            else "Paint the four corners only for windows whose color equals the dominant color discovered in step A."
        ),
        "why_b_depends_on_a": (
            "In dominant_color, the selected windows cannot be known until the support counts identify the dominant color; "
            "substituting the first window's color changes the final grid."
        ),
        "support_by_color": info["support_by_color"],
        "dominant_color": info["dominant_color"],
        "first_window_color": info["first_window_color"],
    }


def dependency_case(seed: object = 0, settings: object = None) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings({"window_scope": "dominant_color"} if settings is None else settings)
    if selected["window_scope"] != "dominant_color":
        raise ValueError("dependency witness requires dominant_color")
    grid = _scene(seed, "query", 3, _QUERY_PROFILES[3])
    output = predict(grid, selected)
    alternate = predict_first_color(grid)
    if alternate == output:
        raise RuntimeError("dependency witness unexpectedly collapsed")
    explanation = explain_dependency(grid, selected)
    return {
        "input": grid,
        "settings": selected,
        "intermediate_value": {
            "support_by_color": explanation["support_by_color"],
            "dominant_color": explanation["dominant_color"],
            "first_window_color": explanation["first_window_color"],
        },
        "program": program(selected),
        "output": output,
        "counterfactual_program": counterfactual_program(),
        "counterfactual_output": alternate,
        "ablation": "wrong_intermediate",
    }
