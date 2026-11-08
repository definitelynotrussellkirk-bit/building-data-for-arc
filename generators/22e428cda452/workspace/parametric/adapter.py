"""Native parametric family for 22e428cda452.

The byte-exact default projects colored corner markers inward: top markers make
2x2 squares and bottom markers make three-cell bent diagonals.  The alternative
first constructs that complete projected grid, counts the projected footprint of
each source color, then recolors every projected cell of the unique largest-total
color with 1.  Generated scenes alternate between a single top-color winner and
a repeated bottom-color winner, preventing a fixed branch or source-frequency
shortcut from fitting the teaching prefix.
"""
from __future__ import annotations

from copy import deepcopy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "22e428cda452"
HERE = Path(__file__).resolve().parent
SETTINGS = ("project_only", "highlight_most_projected_color")
RIVALS = (
    "highlight_most_source_markers",
    "highlight_first_marker",
    "highlight_last_marker",
    "highlight_lowest_color",
    "highlight_highest_color",
    "highlight_first_top_color",
    "highlight_all",
)
HYPOTHESES = SETTINGS + RIVALS

# height, width, color-assignment pattern, single-top side (ignored by all-corner patterns)
_DEMO_PROFILES = (
    (10, 12, "distinct_three", "right"),
    (12, 15, "bottom_pair", "left"),
    (16, 19, "diagonal_pair", "right"),
    (20, 24, "all_top_pair", "both"),
    (26, 28, "all_bottom_pair", "both"),
    (30, 26, "all_cross_pair", "both"),
)
_QUERY_PROFILES = (
    (8, 11, "distinct_three", "left"),
    (14, 18, "bottom_pair", "right"),
    (23, 27, "diagonal_pair", "left"),
    (30, 30, "all_top_pair", "both"),
)
_COLOR_TRIOS = (
    (2, 4, 9),
    (3, 6, 8),
    (2, 5, 8),
    (4, 6, 9),
    (2, 3, 6),
    (3, 5, 9),
    (4, 5, 8),
)
_CORNERS = {
    "tl": lambda h, w: (0, 0),
    "tr": lambda h, w: (0, w - 1),
    "bl": lambda h, w: (h - 1, 0),
    "br": lambda h, w: (h - 1, w - 1),
}


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
        or not 8 <= len(value) <= 30
        or type(value[0]) is not list
        or not 8 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 8..30 with exact integer colors 0..9")
    return value


def _rng(seed: int, role: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:projected-total-v1:{seed}:{role}".encode()).digest()
    return random.Random(digest)


def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


def alternative_program() -> str:
    return (HERE / "highlight_most_projected_color.rkt").read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "highlight_most_source_markers.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    finish = _settings(settings)
    return canonical_program() if finish == "project_only" else alternative_program()


def _markers(value: object) -> list[dict[str, int | str]]:
    source = _grid(value)
    h, w = len(source), len(source[0])
    corner_positions = {
        "tl": (0, 0),
        "tr": (0, w - 1),
        "bl": (h - 1, 0),
        "br": (h - 1, w - 1),
    }
    allowed = set(corner_positions.values())
    non_background = [
        (r, c, source[r][c])
        for r in range(h)
        for c in range(w)
        if source[r][c] != 7
    ]
    if not non_background or any((r, c) not in allowed for r, c, _ in non_background):
        raise ValueError("family inputs must contain only colored corner markers")
    if any(color in (1, 7) for _, _, color in non_background):
        raise ValueError("family marker colors exclude highlight 1 and background 7")
    result = []
    for name in ("tl", "tr", "bl", "br"):
        r, c = corner_positions[name]
        if source[r][c] != 7:
            result.append({"name": name, "row": r, "col": c, "color": source[r][c]})
    return result


def _project(value: object) -> list[list[int]]:
    source = _grid(value)
    markers = _markers(source)
    h, w = len(source), len(source[0])
    output = deepcopy(source)
    for marker in markers:
        output[int(marker["row"])][int(marker["col"])] = 7
    for marker in markers:
        row = int(marker["row"])
        col = int(marker["col"])
        color = int(marker["color"])
        top = row == 0
        left = col == 0
        dr = 1 if top else -1
        dc = 1 if left else -1
        if top:
            offsets = ((1, 1), (1, 2), (2, 1), (2, 2))
        else:
            offsets = ((3, 2), (2, 2), (1, 3))
        for rr, cc in offsets:
            nr, nc = row + dr * rr, col + dc * cc
            if not (0 <= nr < h and 0 <= nc < w):
                raise ValueError("corner projection leaves the grid")
            output[nr][nc] = color
    return output


def _projected_counts(projected: list[list[int]]) -> Counter[int]:
    return Counter(cell for row in projected for cell in row if cell != 7)


def observe(value: object) -> dict[str, Any]:
    source = _grid(value)
    markers = _markers(source)
    projected = _project(source)
    projected_counts = _projected_counts(projected)
    source_counts = Counter(int(marker["color"]) for marker in markers)
    max_projected = max(projected_counts.values())
    projected_winners = sorted(
        color for color, count in projected_counts.items() if count == max_projected
    )
    max_source = max(source_counts.values())
    source_winners = sorted(color for color, count in source_counts.items() if count == max_source)
    chosen_source = source_winners[0]
    top_colors = {int(marker["color"]) for marker in markers if int(marker["row"]) == 0}
    h, w = len(source), len(source[0])
    touches: set[str] = set()
    for marker in markers:
        row, col = int(marker["row"]), int(marker["col"])
        if row == 0:
            touches.add("top")
        if row == h - 1:
            touches.add("bottom")
        if col == 0:
            touches.add("left")
        if col == w - 1:
            touches.add("right")
    return {
        "height": h,
        "width": w,
        "markers": markers,
        "source_marker_count": len(markers),
        "top_marker_count": sum(int(marker["row"]) == 0 for marker in markers),
        "bottom_marker_count": sum(int(marker["row"]) == h - 1 for marker in markers),
        "source_counts": dict(sorted(source_counts.items())),
        "projected_counts": dict(sorted(projected_counts.items())),
        "projected_nonbackground_cells": sum(projected_counts.values()),
        "largest_projected_count": len(projected_winners),
        "largest_projected_color": projected_winners[0] if len(projected_winners) == 1 else None,
        "largest_projected_footprint": max_projected,
        "most_source_markers_color": chosen_source,
        "most_source_markers_tie_count": len(source_winners),
        "winner_has_top_marker": projected_winners[0] in top_colors if len(projected_winners) == 1 else None,
        "touches": sorted(touches),
        "projected": projected,
    }


def _recolor(projected: list[list[int]], selected: set[int]) -> list[list[int]]:
    return [[1 if cell in selected else cell for cell in row] for row in projected]


def predict(value: object, hypothesis: str) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}")
    state = observe(value)
    projected = state["projected"]
    markers = state["markers"]
    colors = sorted({int(marker["color"]) for marker in markers})
    if hypothesis == "project_only":
        return deepcopy(projected)
    if hypothesis == "highlight_all":
        return _recolor(projected, set(colors))
    if hypothesis == "highlight_most_projected_color":
        selected = {int(state["largest_projected_color"])}
    elif hypothesis == "highlight_most_source_markers":
        selected = {int(state["most_source_markers_color"])}
    elif hypothesis == "highlight_first_marker":
        selected = {int(markers[0]["color"])}
    elif hypothesis == "highlight_last_marker":
        selected = {int(markers[-1]["color"])}
    elif hypothesis == "highlight_lowest_color":
        selected = {min(colors)}
    elif hypothesis == "highlight_highest_color":
        selected = {max(colors)}
    elif hypothesis == "highlight_first_top_color":
        selected = {int(next(marker["color"] for marker in markers if int(marker["row"]) == 0))}
    else:  # pragma: no cover - guarded by HYPOTHESES
        raise AssertionError(hypothesis)
    return _recolor(projected, selected)


def explain_dependency(value: object) -> dict[str, Any]:
    state = observe(value)
    return {
        "step_a": "Project every corner marker with its top/bottom glyph and erase the source.",
        "intermediate": {
            "projected_counts": state["projected_counts"],
            "source_counts": state["source_counts"],
        },
        "step_b": "Recolor the projected cells of the unique largest-footprint color with 1.",
        "largest_projected_color": state["largest_projected_color"],
        "most_source_markers_color": state["most_source_markers_color"],
    }


def _choose_trio(seed: int, role: str, index: int) -> tuple[int, int, int]:
    rng = _rng(seed, f"{role}:{index}:colors")
    trio = list(_COLOR_TRIOS[rng.randrange(len(_COLOR_TRIOS))])
    trio.sort()
    return trio[0], trio[1], trio[2]


def _assignment(pattern: str, side: str, trio: tuple[int, int, int]) -> dict[str, int]:
    low, middle, high = trio
    top = "tl" if side == "left" else "tr"
    if pattern == "distinct_three":
        return {top: high, "bl": low, "br": middle}
    if pattern == "bottom_pair":
        return {top: high, "bl": low, "br": low}
    if pattern == "diagonal_pair":
        bottom_shared = "br" if top == "tl" else "bl"
        bottom_other = "bl" if bottom_shared == "br" else "br"
        return {top: low, bottom_shared: low, bottom_other: high}
    if pattern == "all_top_pair":
        return {"tl": middle, "tr": middle, "bl": low, "br": high}
    if pattern == "all_bottom_pair":
        return {"tl": low, "tr": high, "bl": middle, "br": middle}
    if pattern == "all_cross_pair":
        return {"tl": low, "tr": high, "bl": middle, "br": low}
    raise ValueError(f"unknown profile pattern {pattern!r}")


def _scene(seed: int, role: str, index: int, profile: tuple[int, int, str, str]) -> list[list[int]]:
    height, width, pattern, side = profile
    value = [[7] * width for _ in range(height)]
    assignment = _assignment(pattern, side, _choose_trio(seed, role, index))
    for name, color in assignment.items():
        row, col = _CORNERS[name](height, width)
        value[row][col] = color
    state = observe(value)
    if state["largest_projected_count"] != 1:
        raise AssertionError("constructed projected-total winner must be unique")
    return value


def input_banks(seed: object, demos: object = 3) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", 2, 6)
    train = [
        _scene(seed, "demo", index, profile)
        for index, profile in enumerate(_DEMO_PROFILES[:demos])
    ]
    query = [
        _scene(seed, "query", index, profile)
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in train + query]
    if len(encoded) != len(set(encoded)):
        raise AssertionError("constructed inputs must be distinct")
    return train, query


def _pair(value: list[list[int]], finish: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(value), "output": predict(value, finish)}


def certificate(train: object, query_inputs: object) -> dict[str, Any]:
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty pair list")
    if type(query_inputs) is not list:
        raise ValueError("query_inputs must be a list")
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(predict(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    query_changing = []
    if survivors:
        intended = survivors[0]
        query_changing = [
            hypothesis
            for hypothesis in survivors[1:]
            if any(predict(grid, hypothesis) != predict(grid, intended) for grid in query_inputs)
        ]
    return {
        "survivors": survivors,
        "query_changing_survivors": query_changing,
        "finite_hypotheses": list(HYPOTHESES),
    }


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, Any]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", 2, 6)
    queries = _integer(queries, "queries", 1, 4)
    selected = _settings(settings)
    train_inputs, query_inputs = input_banks(seed, demos)
    for finish in SETTINGS:
        proof = certificate([_pair(value, finish) for value in train_inputs], query_inputs)
        if proof["survivors"] != [finish]:
            raise AssertionError(f"teaching inputs do not identify {finish}: {proof['survivors']}")
    return {
        "train": [_pair(value, selected) for value in train_inputs],
        "test": [_pair(value, selected) for value in query_inputs[:queries]],
        "program_solution": program(settings),
    }
