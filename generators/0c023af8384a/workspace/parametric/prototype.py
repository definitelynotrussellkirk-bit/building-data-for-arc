"""Deterministic parametric lessons for vertical mirror completion."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any


TASK_ID = "0c023af8384a"
HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text()
SELECTED_HORIZONTAL_PROGRAM = (HOME / "selected_horizontal.rkt").read_text()
SETTINGS = ("vertical", "vertical_then_selected_horizontal")

_DEMO_PROFILES = ((7, 9), (9, 11), (11, 13), (13, 15), (15, 17), (17, 19))
_QUERY_PROFILES = ((9, 12), (16, 20), (23, 29), (30, 30))


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _settings(value: dict[str, Any] | None) -> dict[str, str]:
    selected = {"completion": "vertical"} if value is None else value
    if not isinstance(selected, dict) or set(selected) != {"completion"}:
        raise ValueError("settings must name exactly completion")
    completion = selected["completion"]
    if completion not in SETTINGS:
        raise ValueError("completion must be vertical or vertical_then_selected_horizontal")
    return {"completion": completion}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _grid(value: list[list[int]]) -> list[list[int]]:
    if (
        type(value) is not list
        or not value
        or type(value[0]) is not list
        or not value[0]
        or len(value) > 30
        or len(value[0]) > 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular with exact integer colors")
    return [row[:] for row in value]


def program(settings: dict[str, Any] | None = None) -> str:
    completion = _settings(settings)["completion"]
    return CANONICAL_PROGRAM if completion == "vertical" else SELECTED_HORIZONTAL_PROGRAM


def vertical_intermediate(grid: list[list[int]]) -> list[list[int]]:
    source = _grid(grid)
    h, w = len(source), len(source[0])
    out = [row[:] for row in source]
    for r in range(h):
        for c in range(w):
            value = source[r][c]
            if value != 0:
                out[h - 1 - r][c] = value
    return out


def selected_color(grid: list[list[int]]) -> int:
    counts = {color: sum(cell == color for row in grid for cell in row) for color in range(1, 10)}
    return min(range(1, 10), key=lambda color: (-counts[color], color))


def selected_horizontal_completion(intermediate: list[list[int]]) -> list[list[int]]:
    source = _grid(intermediate)
    selected = selected_color(source)
    h, w = len(source), len(source[0])
    out = [row[:] for row in source]
    for r in range(h):
        for c in range(w):
            if source[r][c] == selected:
                out[r][w - 1 - c] = selected
    return out


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    completion = _settings(settings)["completion"]
    intermediate = vertical_intermediate(grid)
    if completion == "vertical":
        return intermediate
    return selected_horizontal_completion(intermediate)


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|{seed}|{split}|{index}|v3".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8], "big"))


def _take_cells(
    rng: random.Random,
    candidates: list[tuple[int, int]],
    count: int,
    blocked: set[tuple[int, int]],
    h: int,
    *,
    reserve_horizontal: bool,
    w: int,
) -> list[tuple[int, int]]:
    pool = candidates[:]
    rng.shuffle(pool)
    chosen: list[tuple[int, int]] = []
    for r, c in pool:
        mirror = (h - 1 - r, c)
        horizontal = (r, w - 1 - c)
        diagonal = (h - 1 - r, w - 1 - c)
        required = {r_c for r_c in ((r, c), mirror) if r_c not in blocked}
        if (r, c) in blocked or mirror in blocked:
            continue
        if reserve_horizontal and (horizontal in blocked or diagonal in blocked):
            continue
        chosen.append((r, c))
        blocked.update(required)
        if reserve_horizontal:
            blocked.update((horizontal, diagonal))
        if len(chosen) == count:
            return chosen
    raise ValueError(f"could not place {count} cells in {h}x{w}")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    if split not in {"demo", "query"} or not 0 <= index < len(profiles):
        raise ValueError("unknown split/index")
    h, w = profiles[index]
    rng = _rng(seed, split, index)
    grid = [[0] * w for _ in range(h)]
    colors = rng.sample(range(1, 10), 6)
    focus, axis_first, axis_second, side_top, side_bottom, extra = colors
    focus_count = max(3, min(12, (h * w) // 55))
    if h == 30:
        focus_count = 12
    top_rows = list(range(0, h // 2))
    bottom_rows = list(range((h + 1) // 2, h))
    left_cols = list(range(0, max(1, w // 2 - 1)))
    right_cols = list(range(w // 2 + (w % 2), w))
    # Alternate the selected color's side within every six-demo lesson.  This
    # makes both "always choose the left-side color" and its right-side mirror
    # fail while keeping the actual rule (count after vertical completion) fixed.
    focus_on_left = (seed + index + (0 if split == "demo" else 1)) % 2 == 0
    focus_cols = left_cols if focus_on_left else right_cols
    distractor_cols = right_cols if focus_on_left else left_cols
    blocked: set[tuple[int, int]] = set()

    top_focus = focus_count // 2
    bottom_focus = focus_count - top_focus
    focus_cells = _take_cells(
        rng,
        [(r, c) for r in top_rows for c in focus_cols],
        top_focus,
        blocked,
        h,
        reserve_horizontal=True,
        w=w,
    )
    focus_cells += _take_cells(
        rng,
        [(r, c) for r in bottom_rows for c in focus_cols],
        bottom_focus,
        blocked,
        h,
        reserve_horizontal=True,
        w=w,
    )
    for r, c in focus_cells:
        grid[r][c] = focus

    if h % 2:
        axis = h // 2
        available = [(axis, c) for c in range(w) if (axis, c) not in blocked]
        rng.shuffle(available)
        # Alternate between one and two axis-only competitors.  Axis cells do
        # not gain copies in A, whereas the off-axis focus doubles.  The focus
        # therefore wins after A while appearing at raw-frequency rank two or
        # three across every three-demonstration lesson.
        axis_plan = [(axis_first, focus_count + 1)]
        if index % 2:
            axis_plan.append((axis_second, focus_count + 2))
        cursor = 0
        for color, count in axis_plan:
            if cursor + count > len(available):
                raise ValueError("axis competitor plan does not fit")
            for r, c in available[cursor : cursor + count]:
                grid[r][c] = color
                blocked.add((r, c))
            cursor += count

    side_count = max(2, min(6, focus_count // 2))
    for color, rows in ((side_top, top_rows), (side_bottom, bottom_rows)):
        cells = _take_cells(
            rng,
            [(r, c) for r in rows for c in distractor_cols],
            side_count,
            blocked,
            h,
            reserve_horizontal=False,
            w=w,
        )
        for r, c in cells:
            grid[r][c] = color

    # Distributed singletons add distractors without challenging the focus count.
    extras = [(r, c) for r in range(h) for c in range(w) if (r, c) not in blocked]
    rng.shuffle(extras)
    for r, c in extras[: max(1, min(6, h // 5))]:
        grid[r][c] = extra
        blocked.add((r, c))
        blocked.add((h - 1 - r, c))

    return grid


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer("demos", demos, 3, 6)
    queries = _integer("queries", queries, 1, 4)
    train = []
    test = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, selected)})
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, selected)})
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
