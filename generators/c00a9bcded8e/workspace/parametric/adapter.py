"""Native parametric family for c00a9bcded8e.

The byte-exact default extracts the colors of qualifying rectangles in spatial
row-major order.  The alternative first performs that complete analysis and
then replaces the output cell corresponding to the unique largest qualifying
rectangle with color 9.  The second step consumes the detected/grouped rectangle
intermediate; generated scenes make the area winner differ from the perimeter,
height, width, color and fixed-position rivals.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "c00a9bcded8e"
HERE = Path(__file__).resolve().parent
SETTINGS = ("colors_only", "highlight_largest_rectangle")
RIVALS = (
    "highlight_largest_perimeter",
    "highlight_tallest",
    "highlight_widest",
    "highlight_first",
    "highlight_last",
    "highlight_highest_color",
    "highlight_lowest_color",
    "highlight_all",
    "right_to_left",
)
HYPOTHESES = SETTINGS + RIVALS

# h, w, rows, area-winner position, perimeter-winner position
_DEMO_PROFILES = (
    (18, 26, 2, (0, 0), (1, 2)),
    (22, 27, 3, (2, 2), (0, 0)),
    (24, 28, 3, (1, 1), (2, 0)),
    (26, 29, 4, (3, 0), (1, 2)),
    (28, 30, 4, (0, 2), (3, 1)),
    (30, 28, 4, (2, 1), (0, 0)),
)
_QUERY_PROFILES = (
    (18, 26, 2, (1, 1), (0, 2)),
    (23, 27, 3, (0, 2), (2, 0)),
    (27, 29, 3, (2, 0), (1, 2)),
    (30, 30, 4, (3, 2), (0, 0)),
)
_TARGET_DIMS = (6, 5)      # area 30, perimeter 18
_PERIMETER_DIMS = (3, 9)   # area 27, perimeter 20
_OTHER_DIMS = ((5, 5), (4, 6), (6, 4), (3, 7), (5, 4), (4, 5),
               (3, 6), (4, 4), (3, 5), (3, 4), (4, 3), (3, 3))


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> str:
    if type(value) is not dict or set(value) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    finish = value["finish"]
    if type(finish) is not str or finish not in SETTINGS:
        raise ValueError(f"finish must be one of {SETTINGS!r}")
    return finish


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


def _rng(seed: int, role: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:largest-rectangle-v1:{seed}:{role}".encode()).digest()
    return random.Random(digest)


def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


def alternative_program() -> str:
    return (HERE / "highlight_largest_rectangle.rkt").read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "highlight_largest_perimeter.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    finish = _settings(settings)
    return canonical_program() if finish == "colors_only" else alternative_program()


def _components(value: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(value), len(value[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = value[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and value[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
            box_area = (r1 - r0 + 1) * (c1 - c0 + 1)
            result.append(
                {
                    "color": color,
                    "cells": sorted(cells),
                    "size": len(cells),
                    "bbox": (r0, c0, r1, c1),
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "area": box_area,
                    "density": len(cells) / box_area,
                    "center_r": (r0 + r1) / 2,
                    "center_c": (c0 + c1) / 2,
                    "perimeter": 2 * ((r1 - r0 + 1) + (c1 - c0 + 1)) - 4,
                }
            )
    return result


def _grouped_records(value: object) -> list[list[dict[str, Any]]]:
    source = _grid(value)
    rectangles = [
        record
        for record in _components(source)
        if record["size"] >= 9 and record["density"] >= 0.9
    ]
    rectangles.sort(key=lambda record: record["center_r"])
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    last_row: float | None = None
    for rectangle in rectangles:
        if last_row is None or rectangle["center_r"] - last_row < 4:
            current.append(rectangle)
        else:
            groups.append(sorted(current, key=lambda record: record["center_c"]))
            current = [rectangle]
        last_row = rectangle["center_r"]
    if current:
        groups.append(sorted(current, key=lambda record: record["center_c"]))
    if len(groups) not in (2, 3, 4) or any(len(group) != 3 for group in groups):
        raise ValueError("family requires 2..4 spatial rows of exactly three rectangles")
    return groups


def observe(value: object) -> dict[str, Any]:
    source = _grid(value)
    groups = _grouped_records(source)
    flat = [record for group in groups for record in group]
    max_size = max(record["size"] for record in flat)
    max_perimeter = max(record["perimeter"] for record in flat)
    area_winners = [record for record in flat if record["size"] == max_size]
    perimeter_winners = [record for record in flat if record["perimeter"] == max_perimeter]
    position = {id(record): (r, c) for r, group in enumerate(groups) for c, record in enumerate(group)}
    touches: set[str] = set()
    h, w = len(source), len(source[0])
    for record in flat:
        r0, c0, r1, c1 = record["bbox"]
        if r0 == 0:
            touches.add("top")
        if r1 == h - 1:
            touches.add("bottom")
        if c0 == 0:
            touches.add("left")
        if c1 == w - 1:
            touches.add("right")
    return {
        "height": h,
        "width": w,
        "row_count": len(groups),
        "rectangles_per_row": [len(group) for group in groups],
        "qualified_cells": sum(record["size"] for record in flat),
        "largest_area_count": len(area_winners),
        "largest_perimeter_count": len(perimeter_winners),
        "largest_area_position": position[id(area_winners[0])] if len(area_winners) == 1 else None,
        "largest_perimeter_position": position[id(perimeter_winners[0])] if len(perimeter_winners) == 1 else None,
        "largest_area_color": area_winners[0]["color"] if len(area_winners) == 1 else None,
        "largest_perimeter_color": perimeter_winners[0]["color"] if len(perimeter_winners) == 1 else None,
        "touches": sorted(touches),
        "groups": groups,
    }


def _base_output(groups: list[list[dict[str, Any]]]) -> list[list[int]]:
    return [[int(record["color"]) for record in group] for group in groups]


def _highlight(base: list[list[int]], positions: list[tuple[int, int]]) -> list[list[int]]:
    output = deepcopy(base)
    for row, col in positions:
        output[row][col] = 9
    return output


def predict(value: object, hypothesis: str) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}")
    state = observe(value)
    groups = state["groups"]
    flat = [(r, c, record) for r, group in enumerate(groups) for c, record in enumerate(group)]
    base = _base_output(groups)
    if hypothesis == "colors_only":
        return base
    if hypothesis == "right_to_left":
        return [row[::-1] for row in base]
    if hypothesis == "highlight_all":
        return [[9 for _ in row] for row in base]
    if hypothesis == "highlight_largest_rectangle":
        best = max(record["size"] for _, _, record in flat)
        selected = [(r, c) for r, c, record in flat if record["size"] == best]
    elif hypothesis == "highlight_largest_perimeter":
        best = max(record["perimeter"] for _, _, record in flat)
        selected = [(r, c) for r, c, record in flat if record["perimeter"] == best]
    elif hypothesis == "highlight_tallest":
        best = max(record["height"] for _, _, record in flat)
        selected = [(r, c) for r, c, record in flat if record["height"] == best]
    elif hypothesis == "highlight_widest":
        best = max(record["width"] for _, _, record in flat)
        selected = [(r, c) for r, c, record in flat if record["width"] == best]
    elif hypothesis == "highlight_first":
        selected = [(0, 0)]
    elif hypothesis == "highlight_last":
        selected = [(len(groups) - 1, 2)]
    elif hypothesis == "highlight_highest_color":
        best = max(record["color"] for _, _, record in flat)
        selected = [(r, c) for r, c, record in flat if record["color"] == best]
    elif hypothesis == "highlight_lowest_color":
        best = min(record["color"] for _, _, record in flat)
        selected = [(r, c) for r, c, record in flat if record["color"] == best]
    else:  # pragma: no cover - exhaustive guard
        raise AssertionError(hypothesis)
    return _highlight(base, selected)


def explain_dependency(value: object) -> dict[str, Any]:
    state = observe(value)
    return {
        "step_a": "detect qualifying rectangles, group them into spatial rows, and measure their cell counts",
        "intermediate": "row-major rectangle records with colors, positions and measured sizes",
        "step_b": "replace the output cell mapped to the unique largest measured rectangle with color 9",
        "why_b_depends_on_a": "the highlighted output coordinate is unavailable until detection, grouping and size measurement produce the intermediate mapping",
        "largest_area_position": state["largest_area_position"],
        "largest_perimeter_position": state["largest_perimeter_position"],
    }


def _row_tops(height: int, row_heights: list[int]) -> list[int]:
    """Pack row bands with at least one blank row and touch both boundaries."""
    rows = len(row_heights)
    required = sum(row_heights) + rows - 1
    if required > height:
        raise ValueError("profile height cannot separate rectangle rows")
    extra = height - required
    gaps = [1] * (rows - 1)
    for index in range(extra):
        gaps[index % len(gaps)] += 1
    tops = [0]
    for index, gap in enumerate(gaps):
        tops.append(tops[-1] + row_heights[index] + gap)
    return tops


def _x_positions(width: int, dims: list[tuple[int, int]]) -> list[int]:
    widths = [item[1] for item in dims]
    left = 0
    right = width - widths[2]
    middle = (width - widths[1]) // 2
    if left + widths[0] >= middle or middle + widths[1] >= right:
        raise ValueError("profile width cannot separate three rectangle columns")
    return [left, middle, right]


def _scene(seed: int, role: str, index: int, profile: tuple[Any, ...]) -> list[list[int]]:
    height, width, rows, target_position, perimeter_position = profile
    rng = _rng(seed, f"{role}:{index}")
    value = [[0] * width for _ in range(height)]
    positions = [(row, col) for row in range(rows) for col in range(3)]
    dims_by_position: dict[tuple[int, int], tuple[int, int]] = {}
    other_index = 0
    for position in positions:
        if position == target_position:
            dims_by_position[position] = _TARGET_DIMS
        elif position == perimeter_position:
            dims_by_position[position] = _PERIMETER_DIMS
        else:
            dims_by_position[position] = _OTHER_DIMS[other_index % len(_OTHER_DIMS)]
            other_index += 1
    palette = list(range(1, 9))
    rng.shuffle(palette)
    all_row_dims = [
        [dims_by_position[(row, col)] for col in range(3)]
        for row in range(rows)
    ]
    row_heights = [max(rect_h for rect_h, _ in row_dims) for row_dims in all_row_dims]
    row_tops = _row_tops(height, row_heights)
    for row, row_dims in enumerate(all_row_dims):
        starts = _x_positions(width, row_dims)
        for col in range(3):
            rect_h, rect_w = row_dims[col]
            band_top = row_tops[row]
            if row == 0:
                top = band_top
            elif row == rows - 1:
                top = band_top + row_heights[row] - rect_h
            else:
                top = band_top + (row_heights[row] - rect_h) // 2
            left = starts[col]
            color = palette[(row * 3 + col + index) % len(palette)]
            for rr in range(top, top + rect_h):
                for cc in range(left, left + rect_w):
                    value[rr][cc] = color

    # Isolated distractors exercise the component filter without changing labels.
    candidates = []
    for row in range(height):
        for col in range(width):
            if value[row][col] != 0:
                continue
            if any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and value[row + dr][col + dc] != 0
                for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                continue
            candidates.append((row, col))
    rng.shuffle(candidates)
    noise: list[tuple[int, int]] = []
    for row, col in candidates:
        if any(abs(row - rr) + abs(col - cc) <= 1 for rr, cc in noise):
            continue
        value[row][col] = palette[(len(noise) + 3) % len(palette)]
        noise.append((row, col))
        if len(noise) >= min(18, max(6, height * width // 45)):
            break

    state = observe(value)
    if state["largest_area_position"] != target_position:
        raise AssertionError("constructed area winner changed")
    if state["largest_perimeter_position"] != perimeter_position:
        raise AssertionError("constructed perimeter winner changed")
    return value


def input_banks(seed: object, demos: object = 3) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", 2, 6)
    train = [_scene(seed, "demo", index, profile) for index, profile in enumerate(_DEMO_PROFILES[:demos])]
    query = [_scene(seed, "query", index, profile) for index, profile in enumerate(_QUERY_PROFILES)]
    serial = [json.dumps(grid, separators=(",", ":")) for grid in train + query]
    if len(serial) != len(set(serial)):
        raise AssertionError("constructed inputs must be distinct")
    return train, query


def _pair(value: list[list[int]], finish: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(value), "output": predict(value, finish)}


def certificate(train: object, query_inputs: object) -> dict[str, Any]:
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty pair list")
    if type(query_inputs) is not list:
        raise ValueError("query_inputs must be a list")
    survivors = []
    for hypothesis in HYPOTHESES:
        if all(predict(pair["input"], hypothesis) == pair["output"] for pair in train):
            survivors.append(hypothesis)
    query_changing = [
        hypothesis
        for hypothesis in survivors[1:]
        if any(predict(grid, hypothesis) != predict(grid, survivors[0]) for grid in query_inputs)
    ] if survivors else []
    return {"survivors": survivors, "query_changing_survivors": query_changing,
            "finite_hypotheses": list(HYPOTHESES)}


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, Any]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", 2, 6)
    queries = _integer(queries, "queries", 1, 4)
    selected = _settings(settings)
    train_inputs, query_inputs = input_banks(seed, demos)
    for finish in SETTINGS:
        teaching = [_pair(value, finish) for value in train_inputs]
        proof = certificate(teaching, query_inputs)
        if proof["survivors"] != [finish]:
            raise AssertionError(f"teaching inputs do not identify {finish}: {proof['survivors']}")
    return {
        "train": [_pair(value, selected) for value in train_inputs],
        "test": [_pair(value, selected) for value in query_inputs[:queries]],
        "program_solution": program(settings),
    }
