"""Constructive marker-relay bounding-box lessons for task 6347dcb736b5.

``all_objects`` is the exact canonical program. ``marker_relay`` first draws
all component bounding boxes, samples the one newly painted corner adjacent to
the color-9 marker, then uses that input-dependent color to select and outline a
remote disconnected same-color partner. Inputs are independent of the setting.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
TASK_ID = "6347dcb736b5"
SCOPES = ("all_objects", "marker_relay")
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4

# box tuples are inclusive (r1, c1, r2, c2). Two pairs of disconnected
# components share colors: selected_source/selected_payload and distract_pair.
_DEMO_SPECS = (
    {
        "shape": (10, 14),
        "boxes": ((2, 1, 5, 4), (6, 9, 9, 13), (0, 8, 2, 10), (6, 0, 9, 3), (3, 7, 5, 11)),
        "selected": (0, 1), "distractor": (2, 3), "marker": (0, "tl"),
    },
    {
        "shape": (12, 16),
        "boxes": ((0, 0, 3, 3), (0, 7, 2, 11), (0, 13, 5, 15), (7, 0, 11, 4), (5, 7, 8, 10), (8, 13, 11, 15)),
        "selected": (4, 2), "distractor": (0, 3), "marker": (4, "br"),
    },
    {
        "shape": (14, 18),
        "boxes": ((1, 6, 5, 10), (9, 0, 13, 5), (0, 0, 3, 3), (8, 13, 13, 17)),
        "selected": (0, 1), "distractor": (2, 3), "marker": (0, "tr"),
    },
    {
        "shape": (16, 20),
        "boxes": ((0, 0, 4, 4), (0, 13, 5, 19), (6, 1, 10, 5), (6, 9, 11, 13), (12, 15, 15, 19), (12, 0, 15, 5)),
        "selected": (3, 1), "distractor": (2, 4), "marker": (3, "bl"),
    },
    {
        "shape": (20, 24),
        "boxes": ((2, 2, 8, 7), (0, 11, 4, 16), (0, 19, 5, 23), (11, 0, 19, 5), (10, 9, 15, 14), (12, 18, 19, 23), (7, 17, 10, 21)),
        "selected": (0, 3), "distractor": (2, 5), "marker": (0, "tl"),
    },
    {
        "shape": (24, 26),
        "boxes": ((0, 0, 5, 5), (0, 10, 7, 15), (0, 20, 4, 25), (9, 2, 15, 8), (10, 12, 14, 17), (8, 21, 15, 25), (18, 6, 23, 13)),
        "selected": (3, 1), "distractor": (0, 5), "marker": (3, "tr"),
    },
)
_QUERY_SPECS = (
    {
        "shape": (8, 12),
        "boxes": ((2, 0, 5, 3), (0, 7, 2, 11), (5, 8, 7, 11), (5, 4, 7, 6)),
        "selected": (0, 2), "distractor": (1, 3), "marker": (0, "tr"),
    },
    {
        "shape": (14, 18),
        "boxes": ((0, 0, 4, 4), (2, 7, 6, 11), (0, 14, 4, 17), (9, 0, 13, 6), (9, 12, 13, 17)),
        "selected": (1, 3), "distractor": (0, 4), "marker": (1, "br"),
    },
    {
        "shape": (22, 26),
        "boxes": ((0, 0, 7, 7), (0, 11, 5, 17), (0, 21, 8, 25), (10, 0, 15, 5), (10, 9, 17, 16), (12, 20, 21, 25)),
        "selected": (4, 0), "distractor": (2, 5), "marker": (4, "bl"),
    },
    {
        "shape": (30, 30),
        "boxes": ((2, 2, 10, 9), (18, 20, 29, 29), (0, 15, 8, 22), (17, 0, 29, 8), (0, 25, 5, 29), (12, 11, 18, 17), (22, 11, 29, 16), (11, 24, 15, 29)),
        "selected": (0, 1), "distractor": (2, 3), "marker": (0, "tl"),
    },
)


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_scope(value: Any) -> str:
    if type(value) is not str or value not in SCOPES:
        raise ValueError(f"outline_scope must be one of {SCOPES}")
    return value


def program_for(scope: str) -> str:
    scope = validate_scope(scope)
    return (HERE / "rules" / f"{scope}.rkt").read_text(encoding="utf-8")


def grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width and (rr, cc) not in seen
                            and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "size": len(cells),
            })
    return result


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0] * width for _ in range(height)]


def _paint_boxes(
    grid: list[list[int]],
    objects: list[dict[str, Any]],
    *,
    fill: bool = False,
) -> list[list[int]]:
    output = _blank(len(grid), len(grid[0]))
    for obj in objects:
        r1, c1, r2, c2 = obj["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if fill or row in (r1, r2) or col in (c1, c2):
                    output[row][col] = obj["color"]
    return output


def _neighbors(row: int, col: int, height: int, width: int) -> list[tuple[int, int]]:
    return [
        (rr, cc)
        for rr, cc in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
        if 0 <= rr < height and 0 <= cc < width
    ]


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    objects = _objects(grid)
    marker_objects = [obj for obj in objects if obj["color"] == 9]
    outlined = _paint_boxes(grid, objects)
    marker = marker_objects[0] if len(marker_objects) == 1 else None
    hits: list[tuple[tuple[int, int], int]] = []
    if marker is not None and marker["cells"]:
        mr, mc = marker["cells"][0]
        for cell in _neighbors(mr, mc, len(grid), len(grid[0])):
            value = outlined[cell[0]][cell[1]]
            if value not in (0, 9):
                hits.append((cell, value))
    relay_cell = hits[0][0] if len(hits) == 1 else None
    relay_color = hits[0][1] if len(hits) == 1 else None
    nonmarker = [obj for obj in objects if obj["color"] != 9]
    counts = Counter(obj["color"] for obj in nonmarker)
    selected = [obj for obj in nonmarker if obj["color"] == relay_color]
    source = [
        obj for obj in selected
        if relay_cell is not None
        and obj["bbox"][0] <= relay_cell[0] <= obj["bbox"][2]
        and obj["bbox"][1] <= relay_cell[1] <= obj["bbox"][3]
    ]
    distractor_colors = [color for color, count in counts.items() if count == 2 and color != relay_color]
    return {
        "objects": objects,
        "objects_without_marker": nonmarker,
        "marker_objects": marker_objects,
        "outlined": outlined,
        "marker_neighbor_hits": len(hits),
        "relay_cell": relay_cell,
        "relay_color": relay_color,
        "selected_objects": selected,
        "selected_component_count": len(selected),
        "source_objects": source,
        "distractor_repeated_colors": sorted(distractor_colors),
        "distractor_repeated_component_count": sum(counts[color] for color in distractor_colors),
        "component_color_counts": dict(sorted(counts.items())),
    }


def validate_scene(grid: Any) -> list[str]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return ["grid height must be 1..30"]
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        return ["grid width must be 1..30"]
    width = len(grid[0])
    for row in grid:
        if type(row) is not list or len(row) != width:
            return ["grid must be rectangular"]
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            return ["grid cells must be literal integer colors 0..9"]

    analysis = analyze_scene(grid)
    errors: list[str] = []
    markers = analysis["marker_objects"]
    if len(markers) != 1 or markers[0]["size"] != 1:
        errors.append("scene requires exactly one single-cell color-9 marker")
    nonmarker = analysis["objects_without_marker"]
    if not 4 <= len(nonmarker) <= 8:
        errors.append("scene requires 4..8 non-marker components")
    for obj in nonmarker:
        r1, c1, r2, c2 = obj["bbox"]
        height, box_width = r2 - r1 + 1, c2 - c1 + 1
        if height < 3 or box_width < 3:
            errors.append(f"color {obj['color']} component needs a >=3x3 bbox")
            continue
        if obj["size"] >= height * box_width:
            errors.append(f"color {obj['color']} component must be non-solid")
        cells = set(obj["cells"])
        if not (
            any(row == r1 for row, _ in cells)
            and any(row == r2 for row, _ in cells)
            and any(col == c1 for _, col in cells)
            and any(col == c2 for _, col in cells)
        ):
            errors.append(f"color {obj['color']} component must establish every bbox side")
    counts = analysis["component_color_counts"]
    repeated = sorted(color for color, count in counts.items() if count > 1)
    if len(repeated) != 2 or any(counts[color] != 2 for color in repeated):
        errors.append("scene requires exactly two colors repeated across two components each")
    if analysis["marker_neighbor_hits"] != 1:
        errors.append("marker must have exactly one non-marker neighbor after outlining")
    relay_cell = analysis["relay_cell"]
    if relay_cell is None or grid[relay_cell[0]][relay_cell[1]] != 0:
        errors.append("relay cell must be blank in the input and newly painted by outlining")
    if analysis["selected_component_count"] != 2:
        errors.append("relayed color must select exactly two disconnected components")
    if len(analysis["source_objects"]) != 1:
        errors.append("relay cell must belong to exactly one selected component bbox")
    if analysis["distractor_repeated_component_count"] != 2:
        errors.append("scene requires one unselected repeated-color distractor pair")
    return errors


def output_for(grid: list[list[int]], scope: str) -> list[list[int]]:
    scope = validate_scope(scope)
    errors = validate_scene(grid)
    if errors:
        raise ValueError("invalid marker-relay scene: " + "; ".join(errors))
    analysis = analyze_scene(grid)
    if scope == "all_objects":
        return analysis["outlined"]
    return _paint_boxes(grid, analysis["selected_objects"])


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:marker-relay-v1:{seed}:{split}:{index}:{label}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _episode_palette(seed: int) -> list[int]:
    rng = random.Random(int.from_bytes(hashlib.sha256(f"{TASK_ID}:palette:{seed}".encode()).digest()[:16], "big"))
    palette = list(range(1, 9))
    rng.shuffle(palette)
    return palette


def _shape_cells(box: tuple[int, int, int, int], rng: random.Random) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    hub_row = rng.randint(r1 + 1, r2 - 1)
    hub_col = rng.randint(c1 + 1, c2 - 1)
    cells = {(hub_row, col) for col in range(c1, c2 + 1)}
    cells.update((row, hub_col) for row in range(r1, r2 + 1))
    # A short secondary arm varies density and breaks a pure centered-cross cue.
    if c2 - c1 >= 4:
        arm_row = r1 + 1 if hub_row != r1 + 1 else r2 - 1
        for col in range(min(hub_col, c1 + 1), max(hub_col, c1 + 1) + 1):
            cells.add((arm_row, col))
    if r2 - r1 >= 4:
        arm_col = c2 - 1 if hub_col != c2 - 1 else c1 + 1
        for row in range(min(hub_row, r2 - 1), max(hub_row, r2 - 1) + 1):
            cells.add((row, arm_col))
    return cells


def _corner_and_marker(box: tuple[int, int, int, int], corner: str) -> tuple[tuple[int, int], tuple[int, int]]:
    r1, c1, r2, c2 = box
    if corner == "tl":
        return (r1, c1), (r1 - 1, c1)
    if corner == "tr":
        return (r1, c2), (r1 - 1, c2)
    if corner == "bl":
        return (r2, c1), (r2 + 1, c1)
    if corner == "br":
        return (r2, c2), (r2 + 1, c2)
    raise ValueError(f"unknown marker corner {corner}")


def _colors(seed: int, scene_index: int, spec: dict[str, Any]) -> list[int]:
    palette = _episode_palette(seed)
    start = (2 * scene_index) % len(palette)
    pair = (palette[start], palette[(start + 1) % len(palette)])
    low, high = sorted(pair)
    selected_color, distractor_color = (low, high) if scene_index % 2 == 0 else (high, low)
    selected = set(spec["selected"])
    distractor = set(spec["distractor"])
    extras = [color for color in palette if color not in pair]
    colors: list[int] = []
    extra_index = 0
    for index in range(len(spec["boxes"])):
        if index in selected:
            colors.append(selected_color)
        elif index in distractor:
            colors.append(distractor_color)
        else:
            colors.append(extras[extra_index])
            extra_index += 1
    return colors


def _build_scene(seed: int, split: str, index: int, spec: dict[str, Any]) -> list[list[int]]:
    height, width = spec["shape"]
    grid = _blank(height, width)
    colors = _colors(seed, index + (0 if split == "train" else len(_DEMO_SPECS)), spec)
    selected_source, _payload = spec["selected"]
    marker_index, corner_name = spec["marker"]
    if marker_index != selected_source:
        raise RuntimeError("marker must identify the selected source component")
    relay_cell, marker_cell = _corner_and_marker(spec["boxes"][marker_index], corner_name)
    if not (0 <= marker_cell[0] < height and 0 <= marker_cell[1] < width):
        raise RuntimeError("marker lies outside scene")
    for object_index, (box, color) in enumerate(zip(spec["boxes"], colors, strict=True)):
        cells = _shape_cells(box, _rng(seed, split, index, f"shape:{object_index}"))
        if object_index == marker_index:
            cells.discard(relay_cell)
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("scene specification overlaps component cells")
            grid[row][col] = color
    if grid[marker_cell[0]][marker_cell[1]] != 0:
        raise RuntimeError("marker overlaps a component")
    grid[marker_cell[0]][marker_cell[1]] = 9
    errors = validate_scene(grid)
    if errors:
        raise RuntimeError("invalid constructed scene: " + "; ".join(errors))
    return grid


def generate_episode(seed: int, scope: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _literal_int("seed", seed, 0, 2**63 - 1)
    _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    scope = validate_scope(scope)
    train_inputs = [_build_scene(seed, "train", index, spec) for index, spec in enumerate(_DEMO_SPECS[:demos])]
    test_inputs = [_build_scene(seed, "test", index, spec) for index, spec in enumerate(_QUERY_SPECS)]
    episode = {
        "train": [{"input": grid, "output": output_for(grid, scope)} for grid in train_inputs],
        "test": [{"input": grid, "output": output_for(grid, scope)} for grid in test_inputs],
        "program_solution": program_for(scope),
    }
    digests = [grid_digest(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(set(digests)) != len(digests):
        raise RuntimeError("episode inputs must be distinct")
    return episode


def _box_area(obj: dict[str, Any]) -> int:
    r1, c1, r2, c2 = obj["bbox"]
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def _merge_same_color_boxes(grid: list[list[int]]) -> list[list[int]]:
    output = _blank(len(grid), len(grid[0]))
    objects = _objects(grid)
    colors = sorted({obj["color"] for obj in objects})
    for color in colors:
        cells = [cell for obj in objects if obj["color"] == color for cell in obj["cells"]]
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        merged = {"color": color, "bbox": (min(rows), min(cols), max(rows), max(cols))}
        output = _overlay_boxes(output, [merged])
    return output


def _overlay_boxes(base: list[list[int]], objects: list[dict[str, Any]], *, fill: bool = False) -> list[list[int]]:
    output = deepcopy(base)
    for obj in objects:
        r1, c1, r2, c2 = obj["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if fill or row in (r1, r2) or col in (c1, c2):
                    output[row][col] = obj["color"]
    return output


def _color_boxes(grid: list[list[int]], color: int, *, include_marker: bool = False) -> list[list[int]]:
    analysis = analyze_scene(grid)
    selected = [obj for obj in analysis["objects_without_marker"] if obj["color"] == color]
    if include_marker:
        selected += analysis["marker_objects"]
    return _paint_boxes(grid, selected)


def _repeated_colors(analysis: dict[str, Any]) -> list[int]:
    return sorted(color for color, count in analysis["component_color_counts"].items() if count == 2)


def _pair_area_color(analysis: dict[str, Any], *, largest: bool) -> int:
    candidates = []
    for color in _repeated_colors(analysis):
        area = sum(_box_area(obj) for obj in analysis["objects_without_marker"] if obj["color"] == color)
        candidates.append((area, color))
    return (max if largest else min)(candidates)[1]


def _rival_functions(demos: list[dict[str, Any]], scope: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    if scope == "all_objects":
        return {
            "marker_relay": lambda grid: output_for(grid, "marker_relay"),
            "fill_all_boxes": lambda grid: _paint_boxes(grid, analyze_scene(grid)["objects"], fill=True),
            "merge_same_color_boxes": _merge_same_color_boxes,
            "omit_marker": lambda grid: _paint_boxes(grid, analyze_scene(grid)["objects_without_marker"]),
        }
    fixed_color = analyze_scene(demos[0]["input"])["relay_color"]
    return {
        "all_objects": lambda grid: output_for(grid, "all_objects"),
        "source_only": lambda grid: _paint_boxes(grid, analyze_scene(grid)["source_objects"]),
        "smallest_repeated_color": lambda grid: _color_boxes(grid, min(_repeated_colors(analyze_scene(grid)))),
        "largest_repeated_color": lambda grid: _color_boxes(grid, max(_repeated_colors(analyze_scene(grid)))),
        "smallest_pair_area": lambda grid: _color_boxes(grid, _pair_area_color(analyze_scene(grid), largest=False)),
        "largest_pair_area": lambda grid: _color_boxes(grid, _pair_area_color(analyze_scene(grid), largest=True)),
        "fixed_first_demo_color": lambda grid: _color_boxes(grid, fixed_color),
        "include_marker": lambda grid: _color_boxes(grid, analyze_scene(grid)["relay_color"], include_marker=True),
    }


def audit_teaching_set(demos: list[dict[str, Any]], scope: str) -> dict[str, Any]:
    scope = validate_scope(scope)
    if type(demos) is not list or len(demos) < 2:
        raise ValueError("teaching audit needs at least two demonstrations")
    survivors = [
        candidate
        for candidate in SCOPES
        if all(output_for(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    rivals = {}
    for name, rival in _rival_functions(demos, scope).items():
        disagreements = [
            index for index, pair in enumerate(demos)
            if rival(pair["input"]) != pair["output"]
        ]
        rivals[name] = {
            "refuted": bool(disagreements),
            "first_disagreement_demo": disagreements[0] if disagreements else None,
        }
    return {"setting": scope, "setting_survivors": survivors, "rivals": rivals}


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index outside episode")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
