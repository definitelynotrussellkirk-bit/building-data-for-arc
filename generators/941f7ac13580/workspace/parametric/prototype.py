"""Source-bound two-setting family for ARC task 941f7ac13580.

The canonical setting emits component sizes in top-left order.  The alternative
first identifies the unique border-touching object (step A), uses its cell count
as an input-dependent rotation offset (intermediate), then rotates the canonical
size sequence by that offset (step B).
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "941f7ac13580"
PARAMETERS = {"sequence_origin": ["top_left", "border_size"]}
DEFAULT = {"sequence_origin": "top_left"}
SETTINGS = [
    {"sequence_origin": "top_left"},
    {"sequence_origin": "border_size"},
]
DEMO_SHAPES = ((10, 12), (12, 15), (14, 18), (17, 20), (20, 23), (22, 26))
QUERY_SHAPES = ((11, 14), (16, 19), (23, 26), (30, 30))
SIDES = ("top", "bottom", "right", "left")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}; bool is forbidden")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"sequence_origin"}:
        raise ValueError("settings must name exactly sequence_origin")
    origin = value["sequence_origin"]
    if type(origin) is not str or origin not in PARAMETERS["sequence_origin"]:
        raise ValueError("sequence_origin must be 'top_left' or 'border_size'")
    return {"sequence_origin": origin}


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
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    token = [TASK_ID, "border-size-v1", seed, domain, index]
    return random.Random(int(_digest(token), 16))


def _program_path(origin: str) -> Path:
    return HERE / ("canonical.rkt" if origin == "top_left" else "border_size.rkt")


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return _program_path(chosen["sequence_origin"]).read_text(encoding="utf-8")


def _components(grid: Any) -> list[dict[str, Any]]:
    value = _grid(grid)
    h, w = len(value), len(value[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = value[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and value[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "top": min(r for r, _ in cells),
                    "left": min(c for _, c in cells),
                    "bottom": max(r for r, _ in cells),
                    "right": max(c for _, c in cells),
                }
            )
    result.sort(key=lambda item: (item["top"], item["left"]))
    return result


def scene_facts(grid: Any) -> dict[str, Any]:
    value = _grid(grid)
    h, w = len(value), len(value[0])
    components = _components(value)
    border = [
        item
        for item in components
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in item["cells"])
    ]
    sizes = [item["size"] for item in components]
    rotation = border[0]["size"] % len(components) if len(border) == 1 and components else None
    return {
        "height": h,
        "width": w,
        "components": components,
        "object_count": len(components),
        "sizes": sizes,
        "border_object_count": len(border),
        "border_object_index": components.index(border[0]) if len(border) == 1 else None,
        "border_object_size": border[0]["size"] if len(border) == 1 else None,
        "rotation": rotation,
        "nonzero_cells": sum(sizes),
    }


def transform(grid: Any, settings: Any) -> list[list[int]]:
    chosen = _settings(settings)
    facts = scene_facts(grid)
    if facts["border_object_count"] != 1:
        raise ValueError("expected exactly one border-touching object")
    if not 3 <= facts["object_count"] <= 9:
        raise ValueError("expected 3..9 components")
    if any(not 1 <= size <= 9 for size in facts["sizes"]):
        raise ValueError("component sizes must be 1..9")
    sizes = list(facts["sizes"])
    if chosen["sequence_origin"] == "border_size":
        offset = facts["rotation"]
        if offset == 0:
            raise ValueError("border-size rotation must be nonzero")
        sizes = sizes[offset:] + sizes[:offset]
    return [sizes]


def _blocked(cells: set[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (row + dr, col + dc)
        for row, col in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= row + dr < h and 0 <= col + dc < w
    }


def _shape(rng: random.Random, size: int) -> tuple[tuple[int, int], ...]:
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(tuple(cells))
        dr, dc = rng.choice(CARDINAL)
        cells.add((row + dr, col + dc))
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _border_cells(side: str, size: int, h: int, w: int, rng: random.Random):
    if side in ("top", "bottom"):
        left = rng.randint(1, w - size - 1)
        row = 0 if side == "top" else h - 1
        return {(row, left + offset) for offset in range(size)}
    top = rng.randint(1, h - size - 1)
    col = 0 if side == "left" else w - 1
    return {(top + offset, col) for offset in range(size)}


def _compact_snake(size: int) -> tuple[tuple[int, int], ...]:
    if size == 1:
        return ((0, 0),)
    width = (size + 1) // 2
    cells = []
    for index in range(size):
        row, offset = divmod(index, width)
        col = offset if row % 2 == 0 else width - 1 - offset
        cells.append((row, col))
    return tuple(cells)


def _place_interiors(
    rng: random.Random,
    sizes: list[int],
    h: int,
    w: int,
    occupied: set[tuple[int, int]],
    side: str,
) -> list[set[tuple[int, int]]]:
    """Construct all interiors in separated row bands; no retries or search."""
    count = len(sizes)
    use_compact = h >= 3 * count + 3
    step = 3 if use_compact else 2
    if side == "top":
        rows = [2 + step * index for index in range(count)]
    elif side == "bottom":
        rows = [h - 3 - step * index for index in range(count)]
    else:
        rows = [1 + step * index for index in range(count)]
    if any(row < 1 or row >= h - 1 for row in rows):
        raise RuntimeError(f"row-band construction does not fit {count} interiors on {h}x{w}")
    rng.shuffle(rows)

    result: list[set[tuple[int, int]]] = []
    for object_index, (size, top) in enumerate(zip(sizes, rows)):
        shape = _compact_snake(size) if use_compact and object_index % 2 == 0 else tuple((0, c) for c in range(size))
        sh = max(row for row, _ in shape) + 1
        sw = max(col for _, col in shape) + 1
        if top + sh > h - 1:
            raise RuntimeError("compact row band touches the grid border")
        min_left = 2 if side == "left" else 1
        max_left = w - sw - (2 if side == "right" else 1)
        if min_left > max_left:
            raise RuntimeError(f"object size {size} does not fit interior width {w}")
        left = rng.randint(min_left, max_left)
        cells = {(top + row, left + col) for row, col in shape}
        if not occupied.isdisjoint(_blocked(cells, h, w)):
            raise RuntimeError("constructive row bands unexpectedly overlap")
        occupied.update(cells)
        result.append(cells)
    return result

def _sizes(index: int, count: int, rng: random.Random) -> list[int]:
    # Every schedule is distinct-valued and has enough mass for substantive
    # stress. Any nonzero cyclic shift therefore changes the answer.
    schedules = {
        4: [2, 4, 7, 9],
        5: [1, 3, 5, 7, 9],
        6: [1, 2, 4, 5, 7, 9],
    }
    values = list(schedules[count])
    offset = (index + rng.randrange(count)) % count
    return values[offset:] + values[:offset]

def _scene(seed: int, index: int, *, query_slot: int | None = None) -> list[list[int]]:
    rng = _rng(seed, "query" if query_slot is not None else "demo", index)
    h, w = (QUERY_SHAPES[query_slot] if query_slot is not None else DEMO_SHAPES[index % 6])
    count = 5 if query_slot == 3 else 4 + (index % 3)
    sizes = _sizes(index, count, rng)
    side = SIDES[(index + (query_slot or 0)) % len(SIDES)]

    # Ensure the border size is a nonzero rotation and fit the chosen side.
    span = w - 2 if side in ("top", "bottom") else h - 2
    largest_offset = max(sizes) % count
    fitting = [
        size
        for size in sizes
        if size % count not in (0, largest_offset) and size <= span
    ]
    if not fitting:
        fitting = [size for size in sizes if size % count != 0 and size <= span]
    if not fitting:
        raise RuntimeError("scene schedule has no legal border anchor")
    border_size = fitting[(index + (query_slot or 0)) % len(fitting)]
    interior_sizes = list(sizes)
    interior_sizes.remove(border_size)  # consume the anchor size exactly once

    border = _border_cells(side, border_size, h, w, rng)
    occupied = set(border)
    objects = [border, *_place_interiors(rng, interior_sizes, h, w, occupied, side)]

    palette = rng.sample(list(range(1, 10)), count)
    grid = [[0] * w for _ in range(h)]
    for cells, color in zip(objects, palette):
        for row, col in cells:
            grid[row][col] = color

    facts = scene_facts(grid)
    if (
        facts["object_count"] != count
        or facts["border_object_count"] != 1
        or facts["rotation"] in (None, 0)
        or len(set(facts["sizes"])) != count
    ):
        raise AssertionError(f"invalid constructed scene: {facts}")
    return grid


def _apply_python(source: str, grid: list[list[int]]) -> list[list[int]]:
    for setting in SETTINGS:
        if program(setting) == source:
            return transform(grid, setting)
    raise ValueError("unknown program")


def _rivals(grid: list[list[int]], chosen: dict[str, str]) -> dict[str, list[list[int]]]:
    facts = scene_facts(grid)
    sizes = list(facts["sizes"])
    count = len(sizes)
    border_index = facts["border_object_index"]
    largest = max(sizes)
    wrong = (facts["rotation"] + 1) % count
    if wrong == 0:
        wrong = 1
    return {
        "fixed_first": [sizes],
        "border_rank": [sizes[border_index:] + sizes[:border_index]],
        "largest_size": [sizes[largest % count :] + sizes[: largest % count]],
        "sort_by_size": [sorted(sizes)],
        "wrong_offset_plus_one": [sizes[wrong:] + sizes[:wrong]],
        "reverse": [list(reversed(sizes))],
    }


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    chosen = _settings(episode.get("settings"))
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must be exactly four")
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program_solution differs from fixed settings")

    apply = execute or _apply_python
    inputs: set[str] = set()
    scenes = []
    for pair in train + test:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each pair needs input/output")
        grid = _grid(pair["input"])
        _grid(pair["output"])
        key = _digest(grid)
        if key in inputs:
            raise ValueError("all inputs must be distinct")
        inputs.add(key)
        facts = scene_facts(grid)
        if facts["border_object_count"] != 1 or facts["rotation"] in (None, 0):
            raise ValueError("scene lacks unique nonidentity border-size dependency")
        scenes.append({
            "shape": [facts["height"], facts["width"]],
            "object_count": facts["object_count"],
            "border_object_index": facts["border_object_index"],
            "border_object_size": facts["border_object_size"],
            "rotation": facts["rotation"],
            "nonzero_cells": facts["nonzero_cells"],
        })

    survivor_rows = []
    for setting in SETTINGS:
        disagreements = []
        source = program(setting)
        for index, pair in enumerate(train):
            if apply(source, pair["input"]) != pair["output"]:
                disagreements.append(index)
        survivor_rows.append({"settings": setting, "disagreeing_demo_indices": disagreements})
    survivors = [row["settings"] for row in survivor_rows if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify settings: {survivors}")

    for pair in train + test:
        if apply(program(chosen), pair["input"]) != pair["output"]:
            raise ValueError("label disagrees with chosen program")

    rival_refutations = {}
    for name in _rivals(train[0]["input"], chosen):
        rival_refutations[name] = any(
            _rivals(pair["input"], chosen)[name] != pair["output"] for pair in train
        )
    # fixed_first is the actual canonical setting, so it is expected to survive
    # only when canonical is chosen; the declared alternate program remains the
    # identification rival in that case. Other shortcuts must always be killed.
    required = {k: v for k, v in rival_refutations.items() if k != "fixed_first"}
    if not all(required.values()):
        raise ValueError(f"declared shortcut survives: {required}")

    return {
        "scope": "two declared setting programs plus five explicit shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "setting_refutations": survivor_rows,
        "shortcut_refutations": rival_refutations,
        "scenes": scenes,
    }


def generate(
    seed: int,
    settings: dict[str, str] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(_rng(seed, "settings").choice(SETTINGS) if settings is None else settings)

    train = []
    for index in range(demos):
        grid = _scene(seed, index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for slot in range(4):
        index = 10_000 + slot
        grid = _scene(seed, index, query_slot=slot)
        test.append({"input": grid, "output": transform(grid, chosen)})

    episode = {
        "schema": "941f7ac13580-border-size-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
    }
    episode["program_sha256"] = hashlib.sha256(
        episode["program_solution"].encode()
    ).hexdigest()
    episode["certificate"] = certify(episode)
    return episode


class RacketRunner:
    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc: Any) -> None:
        self.bridge.close()
