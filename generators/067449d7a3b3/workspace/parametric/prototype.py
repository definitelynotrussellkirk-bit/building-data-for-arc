"""Native parametric prototype for ARC task 067449d7a3b3.

The selected canonical program uses color-preserving 8-connectivity and sizes
its green halo from the larger side of each object's bounding box.  This
prototype makes both choices explicit while keeping input sampling independent
of the selected setting.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Callable, Iterable

TASK_ID = "067449d7a3b3"
PARAMETERS = {
    "border_basis": ("max_side", "min_side"),
    "connectivity": (4, 8),
}
DEFAULT_SETTINGS = {"border_basis": "max_side", "connectivity": 8}
DEMO_SHAPES = ((20, 24), (21, 25), (22, 26), (23, 27), (24, 28), (25, 29))
QUERY_SHAPES = ((10, 10), (16, 18), (21, 14), (30, 30))
_NONMAROON = (2, 4, 5, 6, 7, 8)

Grid = list[list[int]]
Settings = dict[str, object]


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: object) -> dict[str, object]:
    if type(settings) is not dict or set(settings) != set(PARAMETERS):
        raise ValueError("settings must contain exactly border_basis and connectivity")
    border = settings["border_basis"]
    connectivity = settings["connectivity"]
    if type(border) is not str or border not in PARAMETERS["border_basis"]:
        raise ValueError("border_basis must be max_side or min_side")
    if type(connectivity) is not int or connectivity not in PARAMETERS["connectivity"]:
        raise ValueError("connectivity must be exact integer 4 or 8")
    return {"border_basis": border, "connectivity": connectivity}


def settings_space() -> list[dict[str, object]]:
    """Return the declared Cartesian space in stable promotion order."""
    return [
        {"border_basis": border, "connectivity": connectivity}
        for border in PARAMETERS["border_basis"]
        for connectivity in PARAMETERS["connectivity"]
    ]


def program(settings: object) -> str:
    """Materialize exact Racket for one setting; default bytes are untouched."""
    setting = normalize_settings(settings)
    source = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    if setting["connectivity"] == 4:
        old = "(objects-8 g bg)"
        if source.count(old) != 1:
            raise ValueError("canonical object parser changed; review the variant")
        source = source.replace(old, "(objects g bg)")
    if setting["border_basis"] == "min_side":
        old = "(max rh rw)"
        if source.count(old) != 1:
            raise ValueError("canonical halo basis changed; review the variant")
        source = source.replace(old, "(min rh rw)")
    return source


def _validate_grid(grid: object) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not grid
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not grid[0]
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have dimensions in 1..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _neighbors(connectivity: int) -> tuple[tuple[int, int], ...]:
    if connectivity == 4:
        return ((-1, 0), (0, -1), (0, 1), (1, 0))
    return tuple(
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if dr or dc
    )


def _components(grid: Grid, connectivity: int) -> list[dict[str, object]]:
    h, w = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    neighbors = _neighbors(connectivity)
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            seen.add((r0, c0))
            todo = [(r0, c0)]
            cells: list[tuple[int, int]] = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in neighbors:
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < h
                        and 0 <= point[1] < w
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        todo.append(point)
            cells.sort()
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "r1": min(rs),
                    "c1": min(cs),
                    "r2": max(rs),
                    "c2": max(cs),
                }
            )
    return result


def _rectangles(grid: Grid, settings: object) -> list[dict[str, object]]:
    setting = normalize_settings(settings)
    result = _components(grid, int(setting["connectivity"]))
    for obj in result:
        rh = int(obj["r2"]) - int(obj["r1"]) + 1
        rw = int(obj["c2"]) - int(obj["c1"]) + 1
        side = max(rh, rw) if setting["border_basis"] == "max_side" else min(rh, rw)
        obj["height"] = rh
        obj["width"] = rw
        obj["border"] = side // 2
        obj["solid"] = len(obj["cells"]) == rh * rw
    return result


def _apply(
    grid: Grid,
    settings: object,
    include: Callable[[dict[str, object]], bool] | None = None,
) -> Grid:
    h, w = _validate_grid(grid)
    original = copy.deepcopy(grid)
    rects = _rectangles(original, settings)
    if include is not None:
        rects = [rect for rect in rects if include(rect)]

    # The canonical program performs the complete stem phase first.
    after_stems = copy.deepcopy(original)
    for rect in rects:
        r2 = int(rect["r2"])
        c1 = int(rect["c1"])
        c2 = int(rect["c2"])
        stem_start = r2 + int(rect["border"]) + 1
        for r in range(stem_start, h):
            for c in range(c1, c2 + 1):
                after_stems[r][c] = 1

    # It then overlays each clipped halo, preserving only original maroon cells.
    after_borders = after_stems
    for rect in rects:
        r1, c1 = int(rect["r1"]), int(rect["c1"])
        r2, c2 = int(rect["r2"]), int(rect["c2"])
        border = int(rect["border"])
        for r in range(r1 - border, r2 + border + 1):
            for c in range(c1 - border, c2 + border + 1):
                if (
                    0 <= r < h
                    and 0 <= c < w
                    and (r < r1 or r > r2 or c < c1 or c > c2)
                    and original[r][c] != 9
                ):
                    after_borders[r][c] = 3
    return after_borders


def transform(grid: Grid, settings: object) -> Grid:
    """Independent Python mirror; qualification still executes protected Racket."""
    return _apply(grid, settings)


def shortcut_outputs(grid: Grid, settings: object) -> dict[str, Grid]:
    """Finite nearby rivals used only as a teaching audit."""
    setting = normalize_settings(settings)
    return {
        "identity": copy.deepcopy(grid),
        "maroon_only": _apply(grid, setting, lambda obj: obj["color"] == 9),
        "solid_rectangles_only": _apply(grid, setting, lambda obj: bool(obj["solid"])),
        "ignore_singletons": _apply(grid, setting, lambda obj: len(obj["cells"]) > 1),
    }


def _rng(seed: int, stream: str, index: int) -> random.Random:
    payload = json.dumps(
        [TASK_ID, "parametric-input-v1", seed, stream, index],
        separators=(",", ":"),
    ).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _blank(h: int, w: int) -> Grid:
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint(grid: Grid, cells: Iterable[tuple[int, int]], color: int) -> None:
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            raise AssertionError(f"template cell outside {h}x{w}: {(r, c)}")
        if grid[r][c] != 0:
            raise AssertionError(f"template overlap at {(r, c)}")
        grid[r][c] = color


def _palette(seed: int, stream: str, index: int) -> tuple[int, int, int]:
    rng = _rng(seed, stream, index)
    colors = rng.sample(_NONMAROON, 3)
    return colors[0], colors[1], colors[2]


def _demo_scene(seed: int, index: int, h: int, w: int) -> Grid:
    """Each ordinary demo separates all settings and four named shortcuts."""
    if h < 20 or w < 24:
        raise ValueError("demonstration template requires at least 20x24")
    diagonal_color, irregular_color, rectangle_color = _palette(seed, "demo", index)
    grid = _blank(h, w)
    shift_r = index % 2
    shift_c = (seed + index) % 2

    # Same-color lobes meet only diagonally: 8-connectivity sees one 4x6 box,
    # while 4-connectivity sees two 2x3 boxes.
    r0, c0 = 1 + shift_r, 1 + shift_c
    first = ((r, c) for r in range(r0, r0 + 2) for c in range(c0, c0 + 3))
    second = ((r, c) for r in range(r0 + 2, r0 + 4) for c in range(c0 + 3, c0 + 6))
    _paint(grid, first, diagonal_color)
    _paint(grid, second, diagonal_color)

    # A non-square rectangle isolates the max-side/min-side halo decision.
    rr, rc = 1 + (index + 1) % 2, w - 5
    _paint(grid, ((r, c) for r in range(rr, rr + 5) for c in range(rc, rc + 2)), rectangle_color)

    # A non-solid object refutes the solid-rectangle shortcut at either connectivity.
    lr, lc = 9 + shift_r, 11 + shift_c
    _paint(
        grid,
        ((lr, lc), (lr + 1, lc), (lr + 2, lc), (lr + 2, lc + 1), (lr + 2, lc + 2)),
        irregular_color,
    )

    # A maroon singleton has a visible stem but no halo, refuting singleton omission.
    _paint(grid, ((10 + shift_r, w - 2),), 9)
    return grid


def _query_anchor(seed: int) -> Grid:
    del seed
    grid = _blank(10, 10)
    _paint(grid, ((r, c) for r in range(1, 3) for c in range(1, 5)), 9)
    _paint(grid, ((r, c) for r in range(1, 4) for c in range(7, 9)), 9)
    return grid


def _query_transfer(seed: int) -> Grid:
    diag, irregular, rectangle = _palette(seed, "query", 1)
    grid = _blank(16, 18)
    _paint(grid, ((r, c) for r in range(1, 3) for c in range(1, 3)), diag)
    _paint(grid, ((r, c) for r in range(3, 5) for c in range(3, 5)), diag)
    _paint(grid, ((r, c) for r in range(1, 6) for c in range(13, 15)), rectangle)
    _paint(grid, ((8, 7), (9, 7), (10, 7), (10, 8), (10, 9)), irregular)
    _paint(grid, ((8, 16),), 9)
    return grid


def _query_boundary(seed: int) -> Grid:
    diag, irregular, rectangle = _palette(seed, "query", 2)
    grid = _blank(21, 14)
    _paint(grid, ((r, c) for r in range(0, 2) for c in range(0, 2)), diag)
    _paint(grid, ((r, c) for r in range(2, 4) for c in range(2, 4)), diag)
    _paint(grid, ((r, c) for r in range(0, 5) for c in range(12, 14)), rectangle)
    _paint(grid, ((18, 0), (19, 0), (20, 0), (20, 1), (20, 2)), irregular)
    _paint(grid, ((9, 7),), 9)
    return grid


def _query_stress(seed: int) -> Grid:
    grid = _demo_scene(seed, 5, 30, 30)
    rng = _rng(seed, "query", 3)
    colors = rng.sample(_NONMAROON, 3)
    additions = (
        (colors[0], ((r, c) for r in range(3, 6) for c in range(15, 17))),
        (colors[1], ((r, c) for r in range(17, 20) for c in range(3, 5))),
        (colors[2], ((r, c) for r in range(18, 21) for c in range(22, 25))),
    )
    for color, cells in additions:
        _paint(grid, cells, color)
    return grid


def sample_inputs(seed: int, demos: int, queries: int) -> dict[str, list[Grid]]:
    """Sample only inputs; the selected setting is intentionally not an argument."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    train = [
        _demo_scene(seed, index, *DEMO_SHAPES[index])
        for index in range(demos)
    ]
    test = [
        _query_anchor(seed),
        _query_transfer(seed),
        _query_boundary(seed),
        _query_stress(seed),
    ]
    raw = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(raw) != len(set(raw)):
        raise ValueError("sampler produced duplicate inputs")
    return {"train": train, "test": test}


def lesson_certificate(demos: object, query_inputs: object) -> dict[str, object]:
    """Fit declared settings and named rivals on demonstrations only."""
    if type(demos) is not list or not demos:
        raise ValueError("at least one demonstration is required")
    if type(query_inputs) is not list or not query_inputs:
        raise ValueError("at least one query input is required")
    normalized_demos: list[dict[str, Grid]] = []
    for pair in demos:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each demonstration needs input and output")
        _validate_grid(pair["input"])
        _validate_grid(pair["output"])
        normalized_demos.append(pair)
    for grid in query_inputs:
        _validate_grid(grid)

    survivors = [
        setting
        for setting in settings_space()
        if all(transform(pair["input"], setting) == pair["output"] for pair in normalized_demos)
    ]
    shortcut_survivors: list[dict[str, object]] = []
    for setting in settings_space():
        names = shortcut_outputs(normalized_demos[0]["input"], setting)
        for name in names:
            if all(
                shortcut_outputs(pair["input"], setting)[name] == pair["output"]
                for pair in normalized_demos
            ):
                shortcut_survivors.append({"settings": setting, "name": name})

    hypotheses: list[Callable[[Grid], Grid]] = [
        lambda grid, setting=setting: transform(grid, setting)
        for setting in survivors
    ]
    hypotheses.extend(
        lambda grid, setting=row["settings"], name=str(row["name"]): shortcut_outputs(grid, setting)[name]
        for row in shortcut_survivors
    )
    ambiguous_queries: list[int] = []
    for index, grid in enumerate(query_inputs):
        predictions = [hypothesis(grid) for hypothesis in hypotheses]
        if predictions and any(prediction != predictions[0] for prediction in predictions[1:]):
            ambiguous_queries.append(index)
    return {
        "surviving_settings": copy.deepcopy(survivors),
        "surviving_shortcuts": copy.deepcopy(shortcut_survivors),
        "ambiguous_queries": ambiguous_queries,
        "query_count": len(query_inputs),
        "query_outputs_consulted": False,
        "scope": "finite four-setting family plus identity, maroon-only, solid-only, and singleton-omission rivals",
    }


def generate_episode(
    seed: int,
    settings: object,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, object]:
    _integer(seed, 0, 2**63 - 1, "seed")
    setting = normalize_settings(settings)
    sampled = sample_inputs(seed, demos, queries)
    train = [
        {"input": copy.deepcopy(grid), "output": transform(grid, setting)}
        for grid in sampled["train"]
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": transform(grid, setting)}
        for grid in sampled["test"]
    ]
    certificate = lesson_certificate(train, [pair["input"] for pair in test])
    if certificate["surviving_settings"] != [setting] or certificate["surviving_shortcuts"]:
        raise ValueError("demonstrations do not uniquely teach the requested setting")
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(setting),
        "train": train,
        "test": test,
        "program_solution": program(setting),
        "certificate": certificate,
        "status": "proposed",
        "training_admitted": False,
    }


def public_projection(episode: object) -> dict[str, object]:
    """Return the exact visible batch challenge using the shared public helper."""
    from reviewer_support import public_challenge_bytes

    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    return json.loads(public_challenge_bytes(episode))


def visible_turn_bytes(episode: object, index: int) -> bytes:
    """Project exactly one query with no index, total count, or future inputs."""
    from reviewer_support import public_challenge_bytes

    if type(episode) is not dict or type(episode.get("test")) is not list:
        raise ValueError("episode needs a test list")
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes(
        {"train": episode.get("train"), "test": [episode["test"][index]]}
    )


def visible_turn(episode: object, index: int) -> dict[str, object]:
    return json.loads(visible_turn_bytes(episode, index))


def visible_turn_id(episode: object, index: int) -> str:
    """Hash exactly the bytes released for one controller-selected turn."""
    return hashlib.sha256(visible_turn_bytes(episode, index)).hexdigest()


def episode_id(episode: object) -> str:
    from reviewer_support import public_challenge_id

    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    return public_challenge_id(episode)
