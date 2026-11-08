"""Native sequential parametric family for ARC task d377a54f20c6.

``redraw_only`` is the byte-exact canonical program.  The alternate setting
first performs the canonical per-object frame-and-stroke redraw, then measures
the number of marker-color stroke cells produced inside every original object
box.  It recolors the complete stroke of the unique maximum object to color 9.
The selector therefore consumes a genuine input-dependent intermediate rather
than a fixed cue or an input-only proxy.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

TASK_ID = "d377a54f20c6"
HERE = Path(__file__).resolve().parent
SETTINGS = ("redraw_only", "highlight_most_stroke_cells")
RIVALS = (
    "identity",
    "highlight_most_input_markers",
    "highlight_fewest_input_markers",
    "highlight_largest_area",
    "highlight_largest_perimeter",
    "highlight_tallest",
    "highlight_widest",
    "highlight_first",
    "highlight_last",
    "highlight_highest_marker_color",
    "highlight_lowest_marker_color",
    "highlight_smallest_stroke",
    "highlight_all_strokes",
    "highlight_selected_frame",
    "highlight_selected_bbox",
)
HYPOTHESES = SETTINGS + RIVALS

# canvas height, canvas width, target dimensions, taller decoy dimensions,
# wider/area/perimeter decoy dimensions.  In every profile the target has the
# unique largest *post-redraw stroke count* while deliberately losing every
# input-only selector represented in RIVALS.
_DEMO_PROFILES = (
    (14, 18, (6, 10), (7, 5), (5, 13)),
    (18, 20, (8, 9), (9, 5), (7, 11)),
    (16, 22, (6, 14), (7, 5), (5, 17)),
    (23, 24, (10, 11), (11, 5), (9, 13)),
    (27, 28, (12, 13), (13, 5), (11, 15)),
    (30, 30, (14, 15), (15, 5), (13, 17)),
)
_QUERY_PROFILES = (
    (20, 24, (8, 18), (9, 5), (7, 21)),
    (22, 26, (10, 16), (11, 5), (9, 18)),
    (28, 28, (12, 14), (13, 5), (9, 19)),
    (30, 30, (6, 23), (7, 5), (7, 24)),
)


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


def _copy(value: object) -> list[list[int]]:
    return [row[:] for row in _grid(value)]


def _rng(seed: int, role: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:stroke-relay-v1:{seed}:{role}".encode()).digest()
    return random.Random(digest)


def canonical_program() -> str:
    return (HERE / "rules" / "canonical.rkt").read_text(encoding="utf-8")


def alternative_program() -> str:
    return (HERE / "rules" / "highlight_most_stroke_cells.rkt").read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "rules" / "highlight_most_input_markers.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    finish = _settings(settings)["finish"]
    return canonical_program() if finish == "redraw_only" else alternative_program()


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: min(cells))


def _stroke(ir: int, ic: int, ih: int, iw: int) -> bool:
    dr = min(ir, ih - 1 - ir)
    dc = min(ic, iw - 1 - ic)
    max_dr = (ih - 1) // 2
    max_dc = (iw - 1) // 2
    return dr == dc or (dr == max_dr and dc >= dr) or (dc == max_dc and dr >= dc)


def canonical_redraw(value: object) -> list[list[int]]:
    grid = _copy(value)
    output = [row[:] for row in grid]
    for record in _input_records(grid):
        r0, c0, r1, c1 = record["bbox"]
        height, width = int(record["height"]), int(record["width"])
        main, marker = int(record["main"]), int(record["marker"])
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                rr, cc = r - r0, c - c0
                if rr in (0, height - 1) or cc in (0, width - 1):
                    output[r][c] = main
                else:
                    output[r][c] = marker if _stroke(rr - 1, cc - 1, height - 2, width - 2) else 0
    return output


def _input_records(value: object) -> list[dict[str, object]]:
    grid = _grid(value)
    records: list[dict[str, object]] = []
    for index, cells in enumerate(_components(grid)):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
        height, width = r1 - r0 + 1, c1 - c0 + 1
        frequencies = Counter(grid[r][c] for r, c in cells)
        ordered = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))
        if len(cells) != height * width:
            raise ValueError("every object must fill its rectangular bounding box")
        if height < 5 or width < 5:
            raise ValueError("every object must be at least 5 by 5")
        if len(ordered) != 2 or ordered[0][1] <= ordered[1][1]:
            raise ValueError("every object needs exactly two colors and a unique majority")
        main, marker = ordered[0][0], ordered[1][0]
        if 9 in (main, marker):
            raise ValueError("color 9 is reserved for the alternate finishing step")
        marker_cells = sorted((r, c) for r, c in cells if grid[r][c] == marker)
        records.append(
            {
                "index": index,
                "cells": cells,
                "bbox": (r0, c0, r1, c1),
                "height": height,
                "width": width,
                "area": height * width,
                "perimeter": 2 * (height + width) - 4,
                "main": main,
                "marker": marker,
                "input_marker_count": len(marker_cells),
                "input_marker_cells": marker_cells,
            }
        )
    if not 2 <= len(records) <= 3:
        raise ValueError("parametric grammar requires two or three objects")
    return records


def _records(value: object) -> tuple[list[list[int]], list[dict[str, object]]]:
    grid = _copy(value)
    base = canonical_redraw(grid)
    records = _input_records(grid)
    for record in records:
        r0, c0, r1, c1 = record["bbox"]
        marker = int(record["marker"])
        stroke_cells = [
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if base[r][c] == marker
        ]
        record["stroke_cells"] = stroke_cells
        record["stroke_count"] = len(stroke_cells)
    return base, records


def _unique_index(records: list[dict[str, object]], key: Callable[[dict[str, object]], int], *, maximum: bool) -> int | None:
    values = [key(record) for record in records]
    best = (max if maximum else min)(values)
    winners = [int(record["index"]) for record, value in zip(records, values) if value == best]
    return winners[0] if len(winners) == 1 else None


def observe(value: object) -> dict[str, object]:
    grid = _copy(value)
    base, records = _records(grid)
    stroke_winner = _unique_index(records, lambda r: int(r["stroke_count"]), maximum=True)
    marker_order = sorted(records, key=lambda r: (int(r["marker"]), int(r["index"])))
    touches: set[str] = set()
    h, w = len(grid), len(grid[0])
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
        "records": records,
        "intermediate": base,
        "stroke_winner": stroke_winner,
        "stroke_winner_count": sum(int(r["index"]) == stroke_winner for r in records),
        "largest_area": _unique_index(records, lambda r: int(r["area"]), maximum=True),
        "largest_perimeter": _unique_index(records, lambda r: int(r["perimeter"]), maximum=True),
        "tallest": _unique_index(records, lambda r: int(r["height"]), maximum=True),
        "widest": _unique_index(records, lambda r: int(r["width"]), maximum=True),
        "most_input_markers": _unique_index(records, lambda r: int(r["input_marker_count"]), maximum=True),
        "fewest_input_markers": _unique_index(records, lambda r: int(r["input_marker_count"]), maximum=False),
        "first_object": int(records[0]["index"]),
        "last_object": int(records[-1]["index"]),
        "highest_marker_color": int(marker_order[-1]["index"]),
        "lowest_marker_color": int(marker_order[0]["index"]),
        "smallest_stroke": _unique_index(records, lambda r: int(r["stroke_count"]), maximum=False),
        "touches": sorted(touches),
        "foreground_cells": sum(len(record["cells"]) for record in records),
    }


def _recolor_strokes(base: list[list[int]], selected: list[dict[str, object]]) -> list[list[int]]:
    output = [row[:] for row in base]
    for record in selected:
        for r, c in record["stroke_cells"]:
            output[r][c] = 9
    return output


def _selected(records: list[dict[str, object]], hypothesis: str) -> list[dict[str, object]]:
    if hypothesis in ("highlight_most_stroke_cells", "highlight_selected_frame", "highlight_selected_bbox"):
        field, maximum = "stroke_count", True
    elif hypothesis == "highlight_most_input_markers":
        field, maximum = "input_marker_count", True
    elif hypothesis == "highlight_fewest_input_markers":
        field, maximum = "input_marker_count", False
    elif hypothesis == "highlight_largest_area":
        field, maximum = "area", True
    elif hypothesis == "highlight_largest_perimeter":
        field, maximum = "perimeter", True
    elif hypothesis == "highlight_tallest":
        field, maximum = "height", True
    elif hypothesis == "highlight_widest":
        field, maximum = "width", True
    elif hypothesis == "highlight_smallest_stroke":
        field, maximum = "stroke_count", False
    elif hypothesis == "highlight_first":
        return records[:1]
    elif hypothesis == "highlight_last":
        return records[-1:]
    elif hypothesis == "highlight_highest_marker_color":
        return [max(records, key=lambda r: int(r["marker"]))]
    elif hypothesis == "highlight_lowest_marker_color":
        return [min(records, key=lambda r: int(r["marker"]))]
    else:
        raise ValueError(f"hypothesis does not select one record: {hypothesis}")
    best = (max if maximum else min)(int(record[field]) for record in records)
    return [record for record in records if int(record[field]) == best]


def predict(value: object, hypothesis: str) -> list[list[int]]:
    grid = _copy(value)
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}")
    if hypothesis == "identity":
        return grid
    base, records = _records(grid)
    if hypothesis == "redraw_only":
        return base
    if hypothesis == "highlight_all_strokes":
        return _recolor_strokes(base, records)
    selected = _selected(records, hypothesis)
    if hypothesis == "highlight_selected_frame":
        output = [row[:] for row in base]
        for record in selected:
            r0, c0, r1, c1 = record["bbox"]
            main = int(record["main"])
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if output[r][c] == main:
                        output[r][c] = 9
        return output
    if hypothesis == "highlight_selected_bbox":
        output = [row[:] for row in base]
        for record in selected:
            r0, c0, r1, c1 = record["bbox"]
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    output[r][c] = 9
        return output
    return _recolor_strokes(base, selected)


def explain_dependency(value: object) -> dict[str, object]:
    grid = _copy(value)
    info = observe(grid)
    records = info["records"]
    intended = _selected(records, "highlight_most_stroke_cells")
    wrong = _selected(records, "highlight_most_input_markers")
    return {
        "step_a": "redraw each filled two-color rectangle as its local-majority frame and local-minority edge-distance X with centered extension",
        "intermediate": info["intermediate"],
        "stroke_counts": {str(r["index"]): int(r["stroke_count"]) for r in records},
        "input_marker_counts": {str(r["index"]): int(r["input_marker_count"]) for r in records},
        "correct_object": int(intended[0]["index"]),
        "wrong_input_marker_object": int(wrong[0]["index"]),
        "step_b": "recolor every produced stroke cell of the unique maximum-stroke object to 9",
        "final": predict(grid, "highlight_most_stroke_cells"),
    }


def _marker_positions(r0: int, c0: int, height: int, width: int, count: int, rng: random.Random) -> list[tuple[int, int]]:
    candidates = [
        (r0, c0),
        (r0 + height - 1, c0 + width - 1),
        (r0, c0 + width - 1),
        (r0 + height - 1, c0),
        (r0 + height // 2, c0 + width // 2),
        (r0 + 1, c0 + max(1, width // 3)),
    ]
    rng.shuffle(candidates)
    return candidates[:count]


def _scene(seed: int, split: str, profile_index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    canvas_h, canvas_w, target_dims, tall_dims, wide_dims = profiles[profile_index]
    rng = _rng(seed, f"{split}:{profile_index}")
    target_h, target_w = target_dims
    tall_h, tall_w = tall_dims
    wide_h, wide_w = wide_dims
    top_h = max(target_h, tall_h)
    if top_h + 1 + wide_h > canvas_h or tall_w + 1 + target_w > canvas_w or wide_w > canvas_w:
        raise AssertionError("invalid static profile packing")

    # Object order is deliberately tall decoy, target, wide decoy.
    top = 0
    tall_box = (top, 0, top + tall_h - 1, tall_w - 1)
    target_box = (top, canvas_w - target_w, top + target_h - 1, canvas_w - 1)
    bottom = canvas_h - wide_h
    wide_left = 0 if rng.randrange(2) == 0 else canvas_w - wide_w
    wide_box = (bottom, wide_left, bottom + wide_h - 1, wide_left + wide_w - 1)
    boxes = {"tall": tall_box, "target": target_box, "wide": wide_box}

    palette = sorted(rng.sample(range(1, 9), 6))
    marker_colors = {"tall": palette[0], "target": palette[3], "wide": palette[5]}
    if rng.randrange(2):
        marker_colors["tall"], marker_colors["wide"] = marker_colors["wide"], marker_colors["tall"]
    main_colors = [palette[1], palette[2], palette[4]]
    rng.shuffle(main_colors)
    roles = ("tall", "target", "wide")
    marker_counts = {"tall": 3, "target": 2, "wide": 1}
    grid = [[0] * canvas_w for _ in range(canvas_h)]
    for role, main in zip(roles, main_colors):
        r0, c0, r1, c1 = boxes[role]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                grid[r][c] = main
        for r, c in _marker_positions(r0, c0, r1 - r0 + 1, c1 - c0 + 1, marker_counts[role], rng):
            grid[r][c] = marker_colors[role]

    info = observe(grid)
    intended = predict(grid, "highlight_most_stroke_cells")
    if info["stroke_winner"] != 1 or info["stroke_winner_count"] != 1:
        raise AssertionError("static profile lost its unique target")
    proxies = (
        "largest_area", "largest_perimeter", "tallest", "widest",
        "most_input_markers", "fewest_input_markers", "first_object", "last_object",
        "highest_marker_color", "lowest_marker_color", "smallest_stroke",
    )
    if any(info[name] == info["stroke_winner"] for name in proxies):
        raise AssertionError("static profile no longer separates an input-only proxy")
    if any(predict(grid, rival) == intended for rival in RIVALS):
        raise AssertionError("static profile failed to separate a declared rival")
    return grid


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
    demo_inputs, query_inputs = _inputs(seed)
    finish = selected["finish"]
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
        source = _copy(pair["input"])
        output = _copy(pair["output"])
        observe(source)
        normalized_train.append({"input": source, "output": output})
    queries = [_copy(value) for value in query_inputs]
    for value in queries:
        observe(value)
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(predict(pair["input"], hypothesis) == pair["output"] for pair in normalized_train)
    ]
    selected = survivors[0] if len(survivors) == 1 and survivors[0] in SETTINGS else None
    disagreements: list[str] = []
    if selected is not None:
        expected = [predict(value, selected) for value in queries]
        for hypothesis in HYPOTHESES:
            if hypothesis != selected and any(
                predict(value, hypothesis) != output for value, output in zip(queries, expected)
            ):
                disagreements.append(hypothesis)
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demonstrations": len(normalized_train),
        "queries": len(queries),
        "query_disagreements": disagreements,
        "scope": "Finite declared rivals checked from demonstrations only; not universal uniqueness.",
    }
