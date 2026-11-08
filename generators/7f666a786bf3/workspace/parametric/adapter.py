"""Native parametric family for 7f666a786bf3.

The default ``fill_only`` setting is the byte-exact canonical rule: every
nonzero color's tight bounding rectangle is filled on a zero background.
``highlight_largest_filled`` first performs that fill, measures the resulting
solid color components, and recolors the unique largest filled component 9.
The second step therefore consumes the input-dependent filled intermediate.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from itertools import permutations
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "7f666a786bf3"
HERE = Path(__file__).resolve().parent
SETTINGS = ("fill_only", "highlight_largest_filled")
RIVALS = (
    "identity",
    "highlight_smallest_filled",
    "highlight_largest_perimeter",
    "highlight_tallest",
    "highlight_widest",
    "highlight_most_markers",
    "highlight_first",
    "highlight_last",
    "highlight_highest_color",
    "highlight_lowest_color",
    "highlight_only_original_markers",
    "highlight_only_new_cells",
    "highlight_all_rectangles",
    "fill_global_bbox",
)
HYPOTHESES = SETTINGS + RIVALS

# (canvas h, canvas w, target, perimeter decoy, tall decoy, other decoy)
# Every target has uniquely largest area.  The perimeter decoy has uniquely
# largest perimeter; the tall and wide ranks also disagree with the target.
_DEMO_PROFILES = (
    (12, 16, (4, 6), (2, 9), (7, 2), (3, 5)),
    (14, 18, (5, 5), (2, 10), (8, 2), (4, 4)),
    (16, 20, (4, 7), (2, 11), (9, 2), (5, 5)),
    (18, 22, (6, 5), (2, 12), (10, 2), (4, 7)),
    (22, 26, (6, 7), (3, 13), (12, 3), (5, 8)),
    (26, 28, (8, 7), (3, 18), (15, 3), (6, 9)),
)
_QUERY_PROFILES = (
    (15, 20, (5, 6), (2, 14), (9, 3), (4, 7)),
    (20, 24, (6, 7), (3, 13), (12, 3), (5, 8)),
    (25, 28, (7, 8), (3, 18), (16, 3), (6, 9)),
    (30, 30, (8, 9), (5, 14), (14, 5), (7, 10)),
)
_ROLE_MARKERS = {"target": 3, "perimeter": 4, "tall": 2, "other": 4}


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    finish = value["finish"]
    if type(finish) is not str or finish not in SETTINGS:
        raise ValueError(f"finish must be one of {SETTINGS!r}")
    return {"finish": finish}


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


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
    digest = hashlib.sha256(f"{TASK_ID}:largest-filled-v1:{seed}:{role}".encode()).digest()
    return random.Random(digest)


def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


def alternative_program() -> str:
    return (HERE / "highlight_largest_filled.rkt").read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "highlight_largest_perimeter.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    finish = _settings(settings)["finish"]
    return canonical_program() if finish == "fill_only" else alternative_program()


def _records(value: object) -> list[dict[str, object]]:
    source = _grid(value)
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(source):
        for c, color in enumerate(row):
            if color:
                by_color.setdefault(color, []).append((r, c))
    if not by_color:
        raise ValueError("at least one nonzero color is required")
    records: list[dict[str, object]] = []
    for color, cells in sorted(by_color.items()):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
        h, w = r1 - r0 + 1, c1 - c0 + 1
        records.append(
            {
                "color": color,
                "cells": sorted(cells),
                "bbox": (r0, c0, r1, c1),
                "height": h,
                "width": w,
                "area": h * w,
                "perimeter": 2 * (h + w) - 4,
                "markers": len(cells),
            }
        )
    return records


def _overlap(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def observe(value: object) -> dict[str, object]:
    source = _grid(value)
    records = _records(source)
    if not 2 <= len(records) <= 4:
        raise ValueError("parametric grammar requires 2..4 nonzero colors")
    for record in records:
        if record["height"] < 2 or record["width"] < 2:
            raise ValueError("every color must span at least two rows and columns")
        if record["markers"] < 2 or record["markers"] >= record["area"]:
            raise ValueError("every color needs sparse markers within its rectangle")
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            if _overlap(left["bbox"], right["bbox"]):
                raise ValueError("different color bounding rectangles must not overlap")
    max_area = max(int(record["area"]) for record in records)
    winners = [record for record in records if record["area"] == max_area]
    touches: set[str] = set()
    h, w = len(source), len(source[0])
    for record in records:
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
        "colors": len(records),
        "foreground_cells": sum(int(record["markers"]) for record in records),
        "filled_cells": sum(int(record["area"]) for record in records),
        "areas": [int(record["area"]) for record in records],
        "perimeters": [int(record["perimeter"]) for record in records],
        "winner_count": len(winners),
        "winner_color": int(winners[0]["color"]) if len(winners) == 1 else None,
        "touches": sorted(touches),
        "records": records,
    }


def fill_rectangles(value: object) -> list[list[int]]:
    source = _copy(_grid(value))
    records = _records(source)
    out = [[0] * len(source[0]) for _ in source]
    for record in records:
        r0, c0, r1, c1 = record["bbox"]
        color = int(record["color"])
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def _choose(records: list[dict[str, object]], hypothesis: str) -> list[dict[str, object]]:
    ordered = sorted(records, key=lambda item: (*item["bbox"], int(item["color"])))
    if hypothesis in ("highlight_largest_filled", "highlight_only_original_markers", "highlight_only_new_cells"):
        key = "area"
        best = max(int(item[key]) for item in records)
        return [item for item in records if item[key] == best]
    if hypothesis == "highlight_smallest_filled":
        best = min(int(item["area"]) for item in records)
        return [item for item in records if item["area"] == best]
    if hypothesis == "highlight_largest_perimeter":
        best = max(int(item["perimeter"]) for item in records)
        return [item for item in records if item["perimeter"] == best]
    if hypothesis == "highlight_tallest":
        best = max(int(item["height"]) for item in records)
        return [item for item in records if item["height"] == best]
    if hypothesis == "highlight_widest":
        best = max(int(item["width"]) for item in records)
        return [item for item in records if item["width"] == best]
    if hypothesis == "highlight_most_markers":
        best = max(int(item["markers"]) for item in records)
        return [item for item in records if item["markers"] == best]
    if hypothesis == "highlight_first":
        return ordered[:1]
    if hypothesis == "highlight_last":
        return ordered[-1:]
    if hypothesis == "highlight_highest_color":
        return [max(records, key=lambda item: int(item["color"]))]
    if hypothesis == "highlight_lowest_color":
        return [min(records, key=lambda item: int(item["color"]))]
    if hypothesis == "highlight_all_rectangles":
        return records
    raise ValueError(f"hypothesis does not select records: {hypothesis}")


def _recolor_selected(
    source: list[list[int]],
    base: list[list[int]],
    selected: Iterable[dict[str, object]],
    *,
    only_original: bool = False,
    only_new: bool = False,
) -> list[list[int]]:
    out = _copy(base)
    for record in selected:
        r0, c0, r1, c1 = record["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if only_original and source[r][c] == 0:
                    continue
                if only_new and source[r][c] != 0:
                    continue
                out[r][c] = 9
    return out


def predict(value: object, hypothesis: str) -> list[list[int]]:
    source = _copy(_grid(value))
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}")
    if hypothesis == "identity":
        return source
    base = fill_rectangles(source)
    if hypothesis == "fill_only":
        return base
    records = _records(source)
    if hypothesis == "fill_global_bbox":
        cells = [(r, c) for r, row in enumerate(source) for c, cell in enumerate(row) if cell]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        out = _copy(base)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = 9
        return out
    selected = _choose(records, hypothesis)
    return _recolor_selected(
        source,
        base,
        selected,
        only_original=hypothesis == "highlight_only_original_markers",
        only_new=hypothesis == "highlight_only_new_cells",
    )


def explain_dependency(value: object) -> dict[str, object]:
    source = _copy(_grid(value))
    info = observe(source)
    records = info["records"]
    largest_area = _choose(records, "highlight_largest_filled")
    largest_perimeter = _choose(records, "highlight_largest_perimeter")
    return {
        "step_a": "fill each input color's tight bounding rectangle and measure the resulting solid components",
        "intermediate": fill_rectangles(source),
        "component_sizes": {str(item["color"]): int(item["area"]) for item in records},
        "component_perimeters": {str(item["color"]): int(item["perimeter"]) for item in records},
        "largest_area_color": int(largest_area[0]["color"]),
        "largest_perimeter_color": int(largest_perimeter[0]["color"]),
        "step_b": "recolor the complete unique largest filled component to 9",
        "final": predict(source, "highlight_largest_filled"),
    }


def _marker_cells(top: int, left: int, height: int, width: int, count: int, rng: random.Random) -> list[tuple[int, int]]:
    corners = [
        (top, left),
        (top, left + width - 1),
        (top + height - 1, left),
        (top + height - 1, left + width - 1),
    ]
    if count == 2:
        return [corners[0], corners[3]] if rng.randrange(2) == 0 else [corners[1], corners[2]]
    if count == 3:
        omitted = rng.randrange(4)
        return [cell for index, cell in enumerate(corners) if index != omitted]
    if count == 4:
        return corners
    raise ValueError("marker count must be 2..4")


def _layout(profile: tuple[object, ...], rng: random.Random) -> tuple[int, int, dict[str, tuple[int, int, int, int]]]:
    h, w, target, perimeter, tall, other = profile
    shapes = {
        "target": target,
        "perimeter": perimeter,
        "tall": tall,
        "other": other,
    }
    candidates: list[tuple[str, str, str, str]] = []
    for order in permutations(shapes):
        if order.index("target") not in (1, 2):
            continue
        top = order[:2]
        bottom = order[2:]
        top_h = max(shapes[name][0] for name in top)
        bottom_h = max(shapes[name][0] for name in bottom)
        if top_h + 1 + bottom_h > h:
            continue
        if sum(shapes[name][1] for name in top) + 1 > w:
            continue
        if sum(shapes[name][1] for name in bottom) + 1 > w:
            continue
        candidates.append(order)
    if not candidates:
        raise ValueError(f"profile is not packable: {profile!r}")
    order = rng.choice(candidates)
    boxes: dict[str, tuple[int, int, int, int]] = {}
    for row_index, names in enumerate((order[:2], order[2:])):
        row_h = max(shapes[name][0] for name in names)
        top = 0 if row_index == 0 else h - row_h
        first, second = names
        fh, fw = shapes[first]
        sh, sw = shapes[second]
        # Disperse vertical alignment while retaining top/bottom boundary contact.
        first_top = top if row_index == 0 else h - fh
        second_top = top if row_index == 0 else h - sh
        boxes[first] = (first_top, 0, first_top + fh - 1, fw - 1)
        boxes[second] = (second_top, w - sw, second_top + sh - 1, w - 1)
    return int(h), int(w), boxes


def _scene(seed: int, split: str, profile_index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    profile = profiles[profile_index]
    rng = _rng(seed, f"{split}:{profile_index}")
    for _ in range(256):
        h, w, boxes = _layout(profile, rng)
        palette = sorted(rng.sample(range(1, 9), 4))
        target_color = palette[1 + rng.randrange(2)]
        remaining = [color for color in palette if color != target_color]
        rng.shuffle(remaining)
        colors = {"target": target_color}
        for role, color in zip(("perimeter", "tall", "other"), remaining):
            colors[role] = color
        grid = [[0] * w for _ in range(h)]
        for role, (r0, c0, r1, c1) in boxes.items():
            cells = _marker_cells(
                r0,
                c0,
                r1 - r0 + 1,
                c1 - c0 + 1,
                _ROLE_MARKERS[role],
                rng,
            )
            for r, c in cells:
                grid[r][c] = colors[role]
        if rng.randrange(2):
            grid = grid[::-1]
        if rng.randrange(2):
            grid = [row[::-1] for row in grid]
        try:
            info = observe(grid)
        except ValueError:
            continue
        intended = predict(grid, "highlight_largest_filled")
        if info["winner_count"] != 1:
            continue
        if any(predict(grid, rival) == intended for rival in RIVALS):
            continue
        return grid
    raise RuntimeError(f"could not construct distinguishing {split} profile {profile_index}")


def _inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demo_order = list(range(len(_DEMO_PROFILES)))
    query_order = list(range(len(_QUERY_PROFILES)))
    _rng(seed, "demo-order").shuffle(demo_order)
    _rng(seed, "query-order").shuffle(query_order)
    demos = [_scene(seed, "demo", index) for index in demo_order]
    queries = [_scene(seed, "query", index) for index in query_order]
    return demos, queries


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", 2, 6)
    queries = _integer(queries, "queries", 1, 4)
    finish = selected["finish"]
    demo_inputs, query_inputs = _inputs(seed)
    train = [{"input": grid, "output": predict(grid, finish)} for grid in demo_inputs[:demos]]
    test = [{"input": grid, "output": predict(grid, finish)} for grid in query_inputs[:queries]]
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serialized) != len(set(serialized)):
        raise ValueError("all demonstration and query inputs must be distinct")
    if certificate(train, [pair["input"] for pair in test])["survivors"] != [finish]:
        raise ValueError("constructed demonstrations do not identify the chosen setting")
    return {"train": train, "test": test, "program_solution": program(selected)}


def certificate(train: object, query_inputs: object) -> dict[str, object]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("certificate requires 2..6 demonstrations")
    if type(query_inputs) is not list or not 1 <= len(query_inputs) <= 4:
        raise ValueError("certificate requires 1..4 query inputs")
    normalized_train: list[dict[str, list[list[int]]]] = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations need input and output")
        source = _copy(_grid(pair["input"]))
        output = _copy(_grid(pair["output"]))
        observe(source)
        normalized_train.append({"input": source, "output": output})
    normalized_queries = [_copy(_grid(value)) for value in query_inputs]
    for value in normalized_queries:
        observe(value)
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(predict(pair["input"], hypothesis) == pair["output"] for pair in normalized_train)
    ]
    selected = survivors[0] if len(survivors) == 1 and survivors[0] in SETTINGS else None
    disagreements: list[str] = []
    if selected is not None:
        expected = [predict(value, selected) for value in normalized_queries]
        for hypothesis in HYPOTHESES:
            if hypothesis == selected:
                continue
            if any(predict(value, hypothesis) != output for value, output in zip(normalized_queries, expected)):
                disagreements.append(hypothesis)
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demonstrations": len(normalized_train),
        "queries": len(normalized_queries),
        "query_disagreements": disagreements,
        "scope": "Finite declared rivals checked from demonstrations only; not a proof of universal uniqueness.",
    }
