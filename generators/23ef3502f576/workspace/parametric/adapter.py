"""Native parametric family for 23ef3502f576.

The canonical setting counts header markers.  The alternative counts horizontal
marker runs.  Both produce a selected-panel index which is then consumed by the
unchanged crop-and-recolor operation.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK = "23ef3502f576"
PARAMETER = "selector_measure"
SETTINGS = ("marker_count", "marker_runs")
RIVALS = SETTINGS + (
    "fixed_1", "fixed_2", "fixed_3", "largest_area", "smallest_area",
    "largest_color", "smallest_color", "header_span", "leftmost_bucket",
    "rightmost_bucket", "selector_color_mod3", "marker_rows",
)

_CANONICAL = (HERE / "canonical.rkt").read_text()
_CANONICAL_TAIL = (
    "(let* ((panels (split-rows-9 g)) (header (first panels)) "
    "(n (length (panel-occ header))) "
    "(chosen (list-ref (rest panels) (- n 1)))) (recolor-panel chosen 8))"
)
_RUN_TAIL = (
    "(let* ((panels (split-rows-9 g)) (header (first panels)) "
    "(cells (panel-occ header)) "
    "(n (if (empty? cells) 0 "
    "(let loop ((remaining (rest cells)) (previous (first cells)) (runs 1)) "
    "(if (empty? remaining) runs "
    "(let* ((current (first remaining)) "
    "(continues (and (= (first current) (first previous)) "
    "(= (second current) (+ (second previous) 1))))) "
    "(loop (rest remaining) current (+ runs (if continues 0 1)))))))) "
    "(chosen (list-ref (rest panels) (- n 1)))) (recolor-panel chosen 8))"
)
if _CANONICAL.count(_CANONICAL_TAIL) != 1:
    raise RuntimeError("canonical selector tail changed")
_ALTERNATE = _CANONICAL.replace(_CANONICAL_TAIL, _RUN_TAIL)


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in SETTINGS
    ):
        raise ValueError("settings must contain only a declared selector_measure")
    return settings[PARAMETER]


def program(settings):
    return _CANONICAL if _setting(settings) == "marker_count" else _ALTERNATE


def counterfactual_program():
    """Wrong intermediate for a marker-runs episode: use total marker count."""
    return _CANONICAL


def _validate_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    height, width = len(grid), len(grid[0])
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("grid dimensions must be within 1..30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid requires exact ARC integers in a rectangle")
    return height, width


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        row, col = stack.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def analyze(grid):
    height, width = _validate_grid(grid)
    dividers = [row for row, values in enumerate(grid) if all(value == 9 for value in values)]
    if len(dividers) != 3 or any(b == a + 1 for a, b in zip(dividers, dividers[1:])):
        raise ValueError("expected exactly three separated full color-9 divider rows")
    d0, d1, d2 = dividers
    segments = (grid[:d0], grid[d0 + 1:d1], grid[d1 + 1:d2], grid[d2 + 1:])
    if any(not segment for segment in segments):
        raise ValueError("header and all three candidate panels must be non-empty")
    header, *panels = segments
    if len({len(panel) for panel in panels}) != 1:
        raise ValueError("candidate panels must have equal height")
    if any(any(len(row) != width for row in panel) for panel in panels):
        raise ValueError("candidate panels must preserve the full width")

    markers = sorted(
        (row, col, value)
        for row, values in enumerate(header)
        for col, value in enumerate(values)
        if value != 0
    )
    if not 1 <= len(markers) <= 3:
        raise ValueError("header must contain one to three markers")
    colors = {value for _, _, value in markers}
    if len(colors) != 1 or next(iter(colors)) in (8, 9):
        raise ValueError("header markers must share one non-reserved color")
    if any(value not in (0, next(iter(colors))) for values in header for value in values):
        raise ValueError("header may contain only black and its marker color")
    runs = 1
    for previous, current in zip(markers, markers[1:]):
        if current[0] != previous[0] or current[1] != previous[1] + 1:
            runs += 1
    if not 1 <= runs <= 3:
        raise ValueError("header run count must select one of three panels")

    candidate_colors = []
    candidate_cells = []
    for index, panel in enumerate(panels, start=1):
        occupied = [(row, col) for row, values in enumerate(panel) for col, value in enumerate(values) if value != 0]
        panel_colors = {panel[row][col] for row, col in occupied}
        if not occupied or len(panel_colors) != 1 or next(iter(panel_colors)) in (8, 9):
            raise ValueError(f"candidate {index} must contain one non-reserved color")
        if not _connected(occupied):
            raise ValueError(f"candidate {index} must be one connected object")
        candidate_colors.append(next(iter(panel_colors)))
        candidate_cells.append(tuple(occupied))

    return {
        "height": height,
        "width": width,
        "header_height": len(header),
        "panel_height": len(panels[0]),
        "markers": tuple((row, col) for row, col, _ in markers),
        "selector_color": next(iter(colors)),
        "marker_count": len(markers),
        "marker_runs": runs,
        "candidate_colors": tuple(candidate_colors),
        "candidate_cells": tuple(candidate_cells),
    }


def _choice(info, mode):
    if mode == "marker_count":
        return info["marker_count"]
    if mode == "marker_runs":
        return info["marker_runs"]
    if mode.startswith("fixed_"):
        return int(mode.rsplit("_", 1)[1])
    areas = [len(cells) for cells in info["candidate_cells"]]
    colors = list(info["candidate_colors"])
    if mode == "largest_area":
        return max(range(3), key=lambda index: (areas[index], -index)) + 1
    if mode == "smallest_area":
        return min(range(3), key=lambda index: (areas[index], index)) + 1
    if mode == "largest_color":
        return max(range(3), key=lambda index: (colors[index], -index)) + 1
    if mode == "smallest_color":
        return min(range(3), key=lambda index: (colors[index], index)) + 1
    columns = [col for _, col in info["markers"]]
    if mode == "header_span":
        return ((max(columns) - min(columns)) % 3) + 1
    if mode == "leftmost_bucket":
        return (min(columns) % 3) + 1
    if mode == "rightmost_bucket":
        return (max(columns) % 3) + 1
    if mode == "selector_color_mod3":
        return ((info["selector_color"] - 1) % 3) + 1
    if mode == "marker_rows":
        return len({row for row, _ in info["markers"]})
    raise ValueError("unknown selector policy")


def claim(grid, mode):
    if mode not in RIVALS:
        raise ValueError("unknown selector policy")
    info = analyze(grid)
    choice = _choice(info, mode)
    if not 1 <= choice <= 3:
        raise ValueError("selector policy produced an invalid panel index")
    cells = set(info["candidate_cells"][choice - 1])
    return [
        [8 if (row, col) in cells else 0 for col in range(info["width"])]
        for row in range(info["panel_height"])
    ]


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK}:native-v1:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _connected_shape(height, width, target, rng):
    if not 1 <= target <= height * width:
        raise ValueError("invalid connected-shape target")
    start = (rng.randrange(height), rng.randrange(width))
    cells = {start}
    while len(cells) < target:
        frontier = sorted({
            neighbor
            for row, col in cells
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
            if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width and neighbor not in cells
        })
        if not frontier:
            raise RuntimeError("connected growth exhausted unexpectedly")
        cells.add(rng.choice(frontier))
    return cells


# header height, panel height, width, marker coordinates, candidate areas, panel colors, selector color
DEMO_SPECS = (
    (1, 5, 8, ((0, 0), (0, 1), (0, 4)), (14, 5, 9), (6, 2, 4), 7),
    (1, 6, 9, ((0, 3), (0, 4)), (11, 7, 16), (5, 7, 1), 3),
    (1, 4, 7, ((0, 0), (0, 3), (0, 6)), (8, 10, 6), (2, 6, 4), 1),
    (1, 7, 10, ((0, 1), (0, 8)), (18, 12, 21), (7, 3, 5), 2),
    (1, 5, 12, ((0, 6),), (9, 17, 13), (4, 1, 6), 5),
    (2, 6, 14, ((0, 1), (1, 5), (1, 6)), (22, 15, 27), (3, 6, 2), 7),
)
QUERY_SPECS = (
    (1, 5, 11, ((0, 2), (0, 3), (0, 4)), (10, 15, 7), (5, 2, 7), 1),
    (1, 7, 13, ((0, 0), (0, 12)), (20, 13, 24), (6, 4, 1), 3),
    (2, 6, 18, ((0, 1), (0, 2), (1, 13)), (19, 25, 16), (2, 7, 4), 5),
    (3, 8, 30, ((0, 0), (0, 1), (2, 29)), (52, 47, 60), (6, 2, 5), 7),
)


def _scene(seed, spec, stream):
    header_h, panel_h, width, markers, areas, colors, selector = spec
    rng = _rng(seed, stream)
    header = [[0] * width for _ in range(header_h)]
    for row, col in markers:
        header[row][col] = selector
    panels = []
    for index, (area, color) in enumerate(zip(areas, colors)):
        shape = _connected_shape(panel_h, width, area, _rng(seed, f"{stream}:shape:{index}"))
        panels.append([[color if (row, col) in shape else 0 for col in range(width)] for row in range(panel_h)])
    divider = [[9] * width]
    grid = header + divider + panels[0] + divider + panels[1] + divider + panels[2]
    info = analyze(grid)
    expected_runs = 1 + sum(
        current[0] != previous[0] or current[1] != previous[1] + 1
        for previous, current in zip(markers, markers[1:])
    )
    if info["marker_count"] != len(markers) or info["marker_runs"] != expected_runs:
        raise RuntimeError("constructed selector facts drifted")
    return grid


def generate(seed, settings, demos=3, queries=4):
    mode = _setting(settings)
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pair(spec, stream):
        grid = _scene(seed, spec, stream)
        return {"input": grid, "output": claim(grid, mode)}

    return {
        "train": [pair(spec, f"demo:{index}") for index, spec in enumerate(DEMO_SPECS[:demos])],
        "test": [pair(spec, f"query:{index}") for index, spec in enumerate(QUERY_SPECS[:queries])],
        "program_solution": program(settings),
        "settings": dict(settings),
    }


def teaching_check(episode):
    mode = _setting(episode["settings"])
    findings = []
    for rival in RIVALS:
        if rival == mode:
            continue
        fits = all(claim(pair["input"], rival) == pair["output"] for pair in episode["train"])
        if fits:
            changed = [
                index
                for index, pair in enumerate(episode["test"])
                if claim(pair["input"], rival) != pair["output"]
            ]
            if changed:
                findings.append({"rival": rival, "queries": changed})
    return findings


def public_turn(episode, index=0):
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index out of range")
    return deepcopy({
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in episode["train"]],
        "test": [{"input": episode["test"][index]["input"]}],
    })
