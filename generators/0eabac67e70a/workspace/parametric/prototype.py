"""Constructive parametric pair-span episodes for task 0eabac67e70a."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = "0eabac67e70a"
SCOPES = ("all_pairs", "junction_cluster")
COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4

# The first two demonstrations form the teaching core. Demo 0 includes one
# distractor longer than both selected spans, one shorter than both, and a
# center-nearer distractor. Demo 1 moves demo 0's selected colors onto
# distractors and uses a disjoint selected-color pair.
_DEMO_SPECS = (
    {"shape": (11, 15), "pairs": 4, "junction": (3, 4), "main": "short"},
    {"shape": (13, 12), "pairs": 5, "junction": (9, 8), "main": "long"},
    {"shape": (16, 18), "pairs": 3, "junction": (5, 12), "main": "horizontal_long"},
    {"shape": (18, 14), "pairs": 6, "junction": (12, 4), "main": "vertical_long"},
    {"shape": (24, 21), "pairs": 5, "junction": (7, 15), "main": "medium"},
    {"shape": (27, 18), "pairs": 4, "junction": (20, 12), "main": "medium"},
)
_QUERY_SPECS = (
    {"shape": (7, 7), "pairs": 3, "junction": (3, 3), "main": "short"},
    {"shape": (12, 16), "pairs": 4, "junction": (8, 5), "main": "medium"},
    {"shape": (22, 26), "pairs": 5, "junction": (6, 18), "main": "horizontal_long"},
    {"shape": (30, 30), "pairs": 6, "junction": (21, 9), "main": "long"},
)


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_scope(value: Any) -> str:
    if type(value) is not str or value not in SCOPES:
        raise ValueError(f"span_scope must be one of {SCOPES}")
    return value


def grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"pair-span-scope-v1:{seed}:{label}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def span_cells(first: tuple[int, int], second: tuple[int, int]) -> list[tuple[int, int]]:
    r1, c1 = first
    r2, c2 = second
    dr, dc = _sign(r2 - r1), _sign(c2 - c1)
    steps = max(abs(r2 - r1), abs(c2 - c1))
    return [(r1 + i * dr, c1 + i * dc) for i in range(steps + 1)]


def _color_points(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value:
                result[value].append((row_index, col_index))
    return dict(result)


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    for color, cells in sorted(_color_points(grid).items()):
        points = sorted(cells)
        if len(points) != 2:
            continue
        pairs.append({"color": color, "points": points, "span": span_cells(points[0], points[1])})
    coverage = Counter(cell for pair in pairs for cell in pair["span"])
    junctions = sorted(cell for cell, count in coverage.items() if count >= 2)
    selected_colors: list[int] = []
    if len(junctions) == 1:
        junction = junctions[0]
        selected_colors = [pair["color"] for pair in pairs if junction in pair["span"]]
    return {
        "pairs": pairs,
        "spans": [pair["span"] for pair in pairs],
        "coverage": coverage,
        "junctions": junctions,
        "selected_colors": selected_colors,
        "distractor_colors": [pair["color"] for pair in pairs if pair["color"] not in selected_colors],
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
    errors: list[str] = []
    points = _color_points(grid)
    if 8 in points:
        errors.append("input color 8 is reserved for output")
    if not 3 <= len(points) <= len(COLORS):
        errors.append("scene must contain 3..8 endpoint colors")
    for color, cells in sorted(points.items()):
        if color not in COLORS:
            errors.append(f"unsupported endpoint color {color}")
        if len(cells) != 2:
            errors.append(f"color {color} must occur exactly twice")
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        if max(abs(r2 - r1), abs(c2 - c1)) < 2:
            errors.append(f"color {color} endpoints need an interior cell")
        if not (r1 == r2 or c1 == c2 or abs(r2 - r1) == abs(c2 - c1)):
            errors.append(f"color {color} endpoints do not define a clean sign-step span")
    if errors:
        return errors
    analysis = analyze_scene(grid)
    if len(analysis["junctions"]) != 1:
        errors.append("scene must have exactly one multiply covered junction cell")
    if len(analysis["selected_colors"]) != 2:
        errors.append("exactly two spans must pass through the unique junction")
    if not analysis["distractor_colors"]:
        errors.append("scene needs at least one distractor span")
    return errors


def junction_of(grid: list[list[int]]) -> tuple[int, int]:
    errors = validate_scene(grid)
    if errors:
        raise ValueError("invalid pair-span scene: " + "; ".join(errors))
    return analyze_scene(grid)["junctions"][0]


def _paint_pairs(grid: list[list[int]], colors: set[int] | None = None) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for pair in analyze_scene(grid)["pairs"]:
        if colors is not None and pair["color"] not in colors:
            continue
        for row, col in pair["span"]:
            output[row][col] = 8
    return output


def output_for(grid: list[list[int]], scope: str) -> list[list[int]]:
    scope = validate_scope(scope)
    errors = validate_scene(grid)
    if errors:
        raise ValueError("invalid pair-span scene: " + "; ".join(errors))
    if scope == "all_pairs":
        return _paint_pairs(grid)
    return _paint_pairs(grid, set(analyze_scene(grid)["selected_colors"]))


def _nearest_unused_row(target: int, height: int, used: set[int]) -> int:
    options = sorted((abs(row - target), row) for row in range(height) if row not in used)
    if not options:
        raise RuntimeError("no unused distractor row")
    return options[0][1]


def _main_segments(height: int, width: int, junction: tuple[int, int], mode: str):
    row, col = junction
    if mode == "short":
        return ((row, col - 2), (row, col + 2)), ((row - 2, col), (row + 2, col))
    if mode == "long":
        return ((row, 0), (row, width - 1)), ((0, col), (height - 1, col))
    if mode == "horizontal_long":
        return ((row, 0), (row, width - 1)), ((row - 2, col), (row + 2, col))
    if mode == "vertical_long":
        return ((row, col - 2), (row, col + 2)), ((0, col), (height - 1, col))
    if mode == "medium":
        horizontal_reach = max(2, width // 4)
        vertical_reach = max(2, height // 4)
        return (
            ((row, max(0, col - horizontal_reach)), (row, min(width - 1, col + horizontal_reach))),
            ((max(0, row - vertical_reach), col), (min(height - 1, row + vertical_reach), col)),
        )
    raise ValueError(f"unknown main mode {mode}")


def _segment_on_side(row: int, width: int, junction_col: int, side: str, style: str,
                     rng: random.Random) -> tuple[tuple[int, int], tuple[int, int]]:
    if side == "left":
        lo, hi = 0, junction_col - 1
    elif side == "right":
        lo, hi = junction_col + 1, width - 1
    else:
        raise ValueError(f"unknown side {side}")
    if hi - lo < 2:
        raise RuntimeError("junction side is too narrow for a distractor span")
    if style == "full":
        first, second = lo, hi
    elif style == "short":
        first = lo if rng.randrange(2) == 0 else hi - 2
        second = first + 2
    elif style == "medium":
        maximum = hi - lo
        length = max(2, min(maximum, 2 + rng.randrange(maximum - 1)))
        first = rng.randint(lo, hi - length)
        second = first + length
    else:
        raise ValueError(f"unknown distractor style {style}")
    return (row, first), (row, second)


def _episode_palette(seed: int) -> tuple[int, ...]:
    shift = hashlib.sha256(f"pair-span-palette:{seed}".encode("utf-8")).digest()[0] % len(COLORS)
    return COLORS[shift:] + COLORS[:shift]


def _colors_for(seed: int, scene_index: int, count: int) -> tuple[int, ...]:
    palette = _episode_palette(seed)
    if scene_index == 0:
        order = (palette[0], palette[2], palette[1], palette[3], palette[4], palette[5], palette[6], palette[7])
    elif scene_index == 1:
        order = (palette[1], palette[3], palette[0], palette[2], palette[4], palette[5], palette[6], palette[7])
    else:
        shift = scene_index % len(palette)
        order = palette[shift:] + palette[:shift]
    return tuple(order[:count])


def _build_scene(seed: int, scene_index: int, spec: dict[str, Any]) -> list[list[int]]:
    height, width = spec["shape"]
    pair_count = spec["pairs"]
    row, col = spec["junction"]
    if not (2 <= row <= height - 3 and 2 <= col <= width - 3):
        raise RuntimeError("scene specification lacks a two-cell junction margin")
    rng = _rng(seed, f"scene:{scene_index}:{height}x{width}")
    segments = list(_main_segments(height, width, (row, col), spec["main"]))
    used_rows = {row}
    for index in range(pair_count - 2):
        if scene_index == 0 and index == 0:
            target_row, side, style = height // 2, "right", "full"
        elif scene_index == 0 and index == 1:
            target_row, side, style = height - 1, "left", "short"
        else:
            target_row = (height // 2 + (index + 1) * (2 if index % 2 == 0 else -2)) % height
            side = "left" if (scene_index + index) % 2 == 0 else "right"
            style = ("full", "short", "medium")[(scene_index + index) % 3]
        distractor_row = _nearest_unused_row(target_row, height, used_rows)
        used_rows.add(distractor_row)
        segments.append(_segment_on_side(distractor_row, width, col, side, style, rng))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, segment in zip(_colors_for(seed, scene_index, pair_count), segments):
        for endpoint_row, endpoint_col in segment:
            if grid[endpoint_row][endpoint_col] != 0:
                raise RuntimeError("constructive endpoint collision")
            grid[endpoint_row][endpoint_col] = color
    errors = validate_scene(grid)
    if errors:
        raise RuntimeError("constructed invalid pair-span scene: " + "; ".join(errors))
    return grid


def _selected_color_output(grid: list[list[int]], colors: set[int]) -> list[list[int]]:
    return _paint_pairs(grid, colors)


def _two_by_length(grid: list[list[int]], *, longest: bool) -> list[list[int]]:
    pairs = analyze_scene(grid)["pairs"]
    ordered = sorted(
        pairs,
        key=lambda row: ((-len(row["span"])) if longest else len(row["span"]), row["color"]),
    )
    return _selected_color_output(grid, {row["color"] for row in ordered[:2]})


def _two_center_nearest(grid: list[list[int]]) -> list[list[int]]:
    center_row = (len(grid) - 1) / 2
    center_col = (len(grid[0]) - 1) / 2
    pairs = analyze_scene(grid)["pairs"]

    def key(row: dict[str, Any]):
        first, second = row["points"]
        midpoint_row = (first[0] + second[0]) / 2
        midpoint_col = (first[1] + second[1]) / 2
        return abs(midpoint_row - center_row) + abs(midpoint_col - center_col), row["color"]

    ordered = sorted(pairs, key=key)
    return _selected_color_output(grid, {row["color"] for row in ordered[:2]})


def audit_teaching_set(demos: list[dict[str, Any]]) -> dict[str, Any]:
    if type(demos) is not list or len(demos) < 2:
        raise ValueError("teaching audit requires at least two demonstrations")
    setting_survivors = [
        scope
        for scope in SCOPES
        if all(output_for(pair["input"], scope) == pair["output"] for pair in demos)
    ]
    first_colors = set(analyze_scene(demos[0]["input"])["selected_colors"])
    rivals = {
        "fixed_first_demo_colors": lambda grid: _selected_color_output(grid, first_colors),
        "two_longest_spans": lambda grid: _two_by_length(grid, longest=True),
        "two_shortest_spans": lambda grid: _two_by_length(grid, longest=False),
        "two_center_nearest_spans": _two_center_nearest,
    }
    records = {}
    for name, rival in rivals.items():
        disagreements = [
            index
            for index, pair in enumerate(demos)
            if rival(pair["input"]) != pair["output"]
        ]
        records[name] = {
            "refuted": bool(disagreements),
            "disagreement_demo_indices": disagreements,
        }
    return {"setting_survivors": setting_survivors, "rivals": records}


def program_for(scope: str) -> str:
    scope = validate_scope(scope)
    return (HERE / "rules" / f"{scope}.rkt").read_text(encoding="utf-8")


def generate_episode(seed: int, *, span_scope: str, demos: int = 3,
                     queries: int = 4) -> dict[str, Any]:
    seed = _literal_int("seed", seed, 0, 2**63 - 1)
    span_scope = validate_scope(span_scope)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    demo_grids = [_build_scene(seed, index, _DEMO_SPECS[index]) for index in range(demos)]
    query_grids = [_build_scene(seed, 100 + index, spec) for index, spec in enumerate(_QUERY_SPECS)]
    all_grids = demo_grids + query_grids
    if len({grid_digest(grid) for grid in all_grids}) != len(all_grids):
        raise RuntimeError("episode contains duplicate inputs")

    def labeled(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": grid, "output": output_for(grid, span_scope)}

    train = [labeled(grid) for grid in demo_grids]
    test = [labeled(grid) for grid in query_grids]
    survivors = [
        scope
        for scope in SCOPES
        if all(output_for(pair["input"], scope) == pair["output"] for pair in train)
    ]
    if survivors != [span_scope]:
        raise RuntimeError(f"demonstrations do not identify span_scope: {survivors}")
    if span_scope == "junction_cluster":
        audit = audit_teaching_set(train)
        if not all(row["refuted"] for row in audit["rivals"].values()):
            raise RuntimeError("teaching core leaves a declared shortcut unrefuted")
    return {"train": train, "test": test, "program_solution": program_for(span_scope)}
