"""Native smallest-enclosing-frame to width-indexed payload family."""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "1137ac565856"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "frame_width_relay")
DEFAULT_MODE = "canonical"
HYPOTHESES = MODES + (
    "global_smallest_relay",
    "constant_first",
    "constant_second",
    "constant_third",
)
DEMO_PROFILES = (
    (18, 24, 1),
    (20, 25, 2),
    (22, 26, 3),
    (24, 27, 1),
    (26, 28, 2),
    (28, 29, 3),
)
QUERY_PROFILES = (
    (19, 24, 2),
    (21, 26, 3),
    (25, 28, 1),
    (30, 30, 3),
)
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
FRAME_COLORS = (1, 3, 4, 5, 6, 7)


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def _mode(value: Any, *, hypothesis: bool = False) -> str:
    options = HYPOTHESES if hypothesis else MODES
    if type(value) is not str or value not in options:
        raise ValueError(f"mode must be one of {options}")
    return value


def program_for(mode: str) -> str:
    selected = _mode(mode)
    return _read("canonical.rkt" if selected == "canonical" else "frame_width_relay.rkt")


def counterfactual_program() -> str:
    return _read("wrong_global_smallest.rkt")


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_grid(value: Any) -> list[list[int]]:
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


def _blank(height: int, width: int, color: int = 0) -> list[list[int]]:
    return [[color for _ in range(width)] for _ in range(height)]


def _rect(height: int, width: int) -> set[tuple[int, int]]:
    return {(r, c) for r in range(height) for c in range(width)}


def _l_shape(height: int, width: int) -> set[tuple[int, int]]:
    return {(r, 0) for r in range(height)} | {(height - 1, c) for c in range(width)}


def _t_shape(height: int, width: int) -> set[tuple[int, int]]:
    center = width // 2
    return {(0, c) for c in range(width)} | {(r, center) for r in range(height)}


def _paint(grid: list[list[int]], shape: Iterable[tuple[int, int]], top: int, left: int, color: int) -> None:
    height, width = len(grid), len(grid[0])
    cells = {(top + r, left + c) for r, c in shape}
    if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
        raise ValueError("shape falls outside scene")
    if any(grid[r][c] != 0 for r, c in cells):
        raise ValueError("shape overlaps existing content")
    for r, c in cells:
        grid[r][c] = color


def _frame_cells(top: int, left: int, size: int) -> set[tuple[int, int]]:
    bottom, right = top + size - 1, left + size - 1
    return {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }


def _draw_frame(grid: list[list[int]], top: int, left: int, size: int, color: int) -> None:
    cells = _frame_cells(top, left, size)
    if any(grid[r][c] != 0 for r, c in cells):
        raise ValueError("frame overlaps existing content")
    for r, c in cells:
        grid[r][c] = color


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    pts = tuple(cells)
    return min(r for r, _ in pts), min(c for _, c in pts), max(r for r, _ in pts), max(c for _, c in pts)


def _components(value: Any) -> list[dict[str, Any]]:
    grid = validate_grid(value)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for dr, dc in DIR4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": cells, "bbox": _bbox(cells)})
    return result


def _marker(grid: list[list[int]]) -> tuple[int, int]:
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(markers) != 1:
        raise ValueError(f"expected one red marker, found {len(markers)}")
    return markers[0]


def _complete_frame(grid: list[list[int]], obj: dict[str, Any]) -> bool:
    r0, c0, r1, c1 = obj["bbox"]
    color = obj["color"]
    return all(
        grid[r][c] == color
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    )


def _frame_objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    return [
        obj for obj in _components(grid)
        if obj["color"] not in (2, 9) and _complete_frame(grid, obj)
    ]


def _area(obj: dict[str, Any]) -> int:
    r0, c0, r1, c1 = obj["bbox"]
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _enclosing(obj: dict[str, Any], marker: tuple[int, int]) -> bool:
    r0, c0, r1, c1 = obj["bbox"]
    return r0 < marker[0] < r1 and c0 < marker[1] < c1


def _chosen_frame(grid: list[list[int]], rule: str = "canonical") -> dict[str, Any]:
    marker = _marker(grid)
    frames = _frame_objects(grid)
    if rule == "canonical":
        candidates = [obj for obj in frames if _enclosing(obj, marker)]
        key = _area
    elif rule == "global_smallest":
        candidates = frames
        key = _area
    elif rule == "largest_enclosing":
        candidates = [obj for obj in frames if _enclosing(obj, marker)]
        key = lambda obj: -_area(obj)
    else:
        raise ValueError(f"unknown frame selection rule {rule}")
    if not candidates:
        raise ValueError("scene has no candidate frame")
    return sorted(candidates, key=lambda obj: (key(obj), obj["bbox"]))[0]


def _selector(obj: dict[str, Any]) -> int:
    _r0, c0, _r1, c1 = obj["bbox"]
    width = c1 - c0 + 1
    selector = (width - 1) // 2
    if width not in (3, 5, 7) or selector not in (1, 2, 3):
        raise ValueError(f"selected frame width must be 3,5,7; got {width}")
    return selector


def _payloads(grid: list[list[int]]) -> list[dict[str, Any]]:
    payloads = [obj for obj in _components(grid) if obj["color"] == 9]
    payloads.sort(key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    if len(payloads) != 3:
        raise ValueError(f"expected three color-9 payloads, found {len(payloads)}")
    return payloads


def _payload_output(grid: list[list[int]], selector: int) -> list[list[int]]:
    payloads = _payloads(grid)
    out = _blank(len(grid), len(grid[0]))
    for r, c in payloads[selector - 1]["cells"]:
        out[r][c] = 8
    return out


def _canonical_output(grid: list[list[int]]) -> list[list[int]]:
    chosen = _chosen_frame(grid, "canonical")
    r0, c0, r1, c1 = chosen["bbox"]
    return _blank(r1 - r0 + 1, c1 - c0 + 1, chosen["color"])


def transform(value: Any, mode: str) -> list[list[int]]:
    grid = validate_grid(value)
    selected = _mode(mode, hypothesis=True)
    if selected == "canonical":
        return _canonical_output(grid)
    if selected == "frame_width_relay":
        selector = _selector(_chosen_frame(grid, "canonical"))
    elif selected == "global_smallest_relay":
        selector = _selector(_chosen_frame(grid, "global_smallest"))
    elif selected == "constant_first":
        selector = 1
    elif selected == "constant_second":
        selector = 2
    elif selected == "constant_third":
        selector = 3
    else:
        raise ValueError(f"unsupported hypothesis {selected}")
    return _payload_output(grid, selector)


def explain_dependency(value: Any) -> dict[str, Any]:
    grid = validate_grid(value)
    chosen = _chosen_frame(grid, "canonical")
    global_smallest = _chosen_frame(grid, "global_smallest")
    selector = _selector(chosen)
    counterfactual = _selector(global_smallest)
    return {
        "step_a": "identify the smallest complete rectangular frame that strictly encloses the red marker",
        "intermediate": "the selected frame width converted from 3,5,7 to payload index 1,2,3",
        "step_b": "use that index to select the row-major color-9 payload and repaint it color 8",
        "why_b_depends_on_a": "the payload index depends on which frame survives the enclosure and minimum-area test, not on the globally smallest frame",
        "chosen_frame_color": chosen["color"],
        "chosen_frame_width": chosen["bbox"][3] - chosen["bbox"][1] + 1,
        "selector": selector,
        "counterfactual_selector": counterfactual,
        "output": transform(grid, "frame_width_relay"),
        "counterfactual_output": transform(grid, "global_smallest_relay"),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"1137ac565856-parametric-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _profile(seed: int, split: str, index: int) -> tuple[int, int, int]:
    del seed
    return (DEMO_PROFILES if split == "train" else QUERY_PROFILES)[index]


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, selector = _profile(seed, split, index)
    rng = _rng(seed, split, index)
    grid = _blank(height, width)
    selected_size = 2 * selector + 1
    outer_size = selected_size + 6
    frame_colors = list(FRAME_COLORS)
    rng.shuffle(frame_colors)
    outer_color, chosen_color, decoy_color = frame_colors[:3]
    _draw_frame(grid, 1, 1, outer_size, outer_color)
    _draw_frame(grid, 4, 4, selected_size, chosen_color)
    marker_span = selected_size - 2
    marker_row = 5 + ((seed + index) % marker_span)
    marker_col = 5 + ((seed * 3 + index) % marker_span)
    grid[marker_row][marker_col] = 2

    decoy_size = 5 if selector == 1 else 3
    decoy_top = height - decoy_size
    _draw_frame(grid, decoy_top, 1, decoy_size, decoy_color)

    if (height, width) == (30, 30):
        payload_shapes = (_rect(6, 8), _rect(6, 7), _rect(5, 9))
        payload_slots = ((0, 21), (10, 21), (24, 21))
    else:
        payload_shapes = (_rect(3, 4), _l_shape(4, 4), _t_shape(3, 5))
        payload_slots = ((1, width - 5), (7, width - 5), (13, width - 6))
    order = list(range(3))
    rng.shuffle(order)
    for slot_index, shape_index in enumerate(order):
        top, left = payload_slots[slot_index]
        _paint(grid, payload_shapes[shape_index], top, left, 9)

    _validate_scene(grid, expected_selector=selector)
    return grid


def _validate_scene(value: Any, *, expected_selector: int | None = None) -> None:
    grid = validate_grid(value)
    _marker(grid)
    frames = _frame_objects(grid)
    if len(frames) != 3:
        raise ValueError(f"scene must contain exactly three frame objects, found {len(frames)}")
    enclosing = [obj for obj in frames if _enclosing(obj, _marker(grid))]
    if len(enclosing) != 2:
        raise ValueError(f"scene must contain two enclosing frames, found {len(enclosing)}")
    selector = _selector(_chosen_frame(grid, "canonical"))
    if expected_selector is not None and selector != expected_selector:
        raise ValueError(f"observed selector {selector} differs from requested {expected_selector}")
    _payloads(grid)
    if selector in (2, 3) and _selector(_chosen_frame(grid, "global_smallest")) == selector:
        raise ValueError("non-enclosing decoy failed to distinguish global-smallest shortcut")


def certificate(train: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(transform(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    declared = [mode for mode in MODES if mode in survivors]
    selected = declared[0] if len(declared) == 1 else None
    query_changing = []
    if selected is not None:
        for hypothesis in survivors:
            if any(transform(grid, hypothesis) != transform(grid, selected) for grid in query_inputs):
                query_changing.append(hypothesis)
    return {
        "survivors": survivors,
        "selected_declared_mode": selected,
        "query_changing_survivors": query_changing,
        "hypotheses": list(HYPOTHESES),
    }


def build_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    selected = _mode(mode)
    seen: set[tuple[tuple[int, ...], ...]] = set()

    def collect(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        pairs = []
        for index in range(count):
            grid = _scene(seed, split, index)
            key = tuple(tuple(row) for row in grid)
            if key in seen:
                raise RuntimeError("scene schedule produced a duplicate input")
            seen.add(key)
            pairs.append({"input": grid, "output": transform(grid, selected)})
        return pairs

    return {
        "train": collect("train", demos),
        "test": collect("test", queries),
        "program_solution": program_for(selected),
    }
