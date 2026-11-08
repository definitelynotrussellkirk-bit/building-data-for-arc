"""Native parametric family for ARC task 6fde852adb54.

The family keeps every movement mechanic fixed while varying only how a
bottom-connected obstacle component is scored by column:

* ``total_cells`` counts all component cells in a column (the canonical rule).
* ``longest_vertical_run`` scores the longest contiguous vertical run.

Inputs are constructed independently of the requested setting.  The first
lesson example is a deliberate count-versus-run discriminator, and the next
two examples rule out several tempting mechanics shortcuts.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "6fde852adb54"
METRICS = ("total_cells", "longest_vertical_run")
_MODEL_NAMES = (
    "total_cells",
    "longest_vertical_run",
    "stay_in_source_column",
    "leftmost_best_column",
    "rightmost_best_column",
    "no_shelf_clearing",
    "tips_ignore_obstacles",
    "bottom_touching_run",
)
_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_PROGRAM_FILES = {
    "total_cells": HERE / "canonical.rkt",
    "longest_vertical_run": HERE / "longest_vertical_run.rkt",
}


def _integer(value: Any) -> bool:
    return type(value) is int


def _validated_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"landing_metric"}:
        raise ValueError("settings must contain exactly landing_metric")
    metric = settings["landing_metric"]
    if type(metric) is not str or metric not in METRICS:
        raise ValueError("landing_metric must be a declared string setting")
    return metric


def _validated_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 14 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 14 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid dimensions must be in 14..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC integer colors")
    return [list(row) for row in grid]


def program(settings: dict[str, Any]) -> str:
    """Return exact standalone Racket source for one declared setting."""
    metric = _validated_settings(settings)
    return _PROGRAM_FILES[metric].read_text(encoding="utf-8")


def _components(cells: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(cells)
    result: list[list[tuple[int, int]]] = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        stack = [seed]
        component: list[tuple[int, int]] = []
        while stack:
            point = stack.pop()
            component.append(point)
            row, col = point
            for dr, dc in _DIRECTIONS:
                neighbor = row + dr, col + dc
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append(sorted(component))
    return sorted(result, key=lambda component: component[0])


def analyze(grid: Any) -> dict[str, Any]:
    """Parse semantic roles and components from one family input."""
    grid = _validated_grid(grid)
    height, width = len(grid), len(grid[0])
    counts = Counter(cell for row in grid for cell in row)
    background = min(counts, key=lambda color: (-counts[color], color))
    top = [cell for cell in grid[0] if cell != background]
    if not top:
        raise ValueError("top mover is missing")
    body = Counter(top).most_common(1)[0][0]
    mover_cols = tuple(col for col, cell in enumerate(grid[0]) if cell == body)
    if len(mover_cols) != 3 or mover_cols != tuple(range(mover_cols[0], mover_cols[0] + 3)):
        raise ValueError("mover must occupy three contiguous columns")
    if any(grid[row][col] != body for row in (0, 1) for col in mover_cols):
        raise ValueError("first two mover rows must be body color")
    bottom = [grid[2][col] for col in mover_cols]
    tip_values = {cell for cell in bottom if cell not in (background, body)}
    if len(tip_values) != 1:
        raise ValueError("mover needs exactly one tip color")
    tip = next(iter(tip_values))
    if any(cell not in (body, tip) for cell in bottom):
        raise ValueError("third mover row may contain only body and tip")
    colors = set(counts)
    obstacle_values = colors - {background, body, tip}
    if len(colors) != 4 or len(obstacle_values) != 1:
        raise ValueError("family inputs must use exactly four semantic colors")
    obstacle = next(iter(obstacle_values))
    obstacle_cells = sorted(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == obstacle
    )
    obstacle_components = _components(obstacle_cells)
    by_cell = {
        point: component
        for component in obstacle_components
        for point in component
    }
    return {
        "height": height,
        "width": width,
        "background": background,
        "body": body,
        "tip": tip,
        "obstacle": obstacle,
        "mover_cols": mover_cols,
        "tip_mask": tuple(int(cell == tip) for cell in bottom),
        "obstacle_cells": obstacle_cells,
        "obstacle_components": obstacle_components,
        "component_by_cell": by_cell,
        "palette": (background, body, tip, obstacle),
    }


def _longest_vertical_runs(component: Iterable[tuple[int, int]]) -> dict[int, int]:
    rows_by_col: dict[int, list[int]] = defaultdict(list)
    for row, col in component:
        rows_by_col[col].append(row)
    result: dict[int, int] = {}
    for col, rows in rows_by_col.items():
        current = best = 0
        previous: int | None = None
        for row in sorted(set(rows)):
            current = current + 1 if previous is not None and row == previous + 1 else 1
            best = max(best, current)
            previous = row
        result[col] = best
    return result


def _scores(
    component: list[tuple[int, int]], metric: str, height: int
) -> dict[int, int]:
    if metric == "total_cells":
        return dict(Counter(col for _, col in component))
    if metric == "longest_vertical_run":
        return _longest_vertical_runs(component)
    if metric == "bottom_touching_run":
        rows_by_col: dict[int, set[int]] = defaultdict(set)
        for row, col in component:
            rows_by_col[col].add(row)
        result = {}
        for col, rows in rows_by_col.items():
            length = 0
            row = height - 1
            while row in rows:
                length += 1
                row -= 1
            result[col] = length
        return result
    raise ValueError(f"unknown score metric: {metric}")


def _predict_policy(
    grid: Any,
    metric: str,
    *,
    candidate_policy: str = "nearest",
    clear_shelf: bool = True,
    honor_tip_obstacles: bool = True,
    stay_in_source: bool = False,
) -> dict[str, Any]:
    facts = analyze(grid)
    grid = _validated_grid(grid)
    height, width = facts["height"], facts["width"]
    background, body, tip, obstacle = facts["palette"]
    mover_cols = facts["mover_cols"]
    output = [list(row) for row in grid]
    for col in mover_cols:
        for row in range(3):
            output[row][col] = background

    traces: list[dict[str, Any]] = []
    for col in mover_cols:
        hits = [row for row in range(3, height) if grid[row][col] == obstacle]
        if grid[2][col] == tip:
            considered = hits if honor_tip_obstacles else []
            landing = considered[0] - 1 if considered else height - 1
            for row, value in ((landing - 2, body), (landing - 1, body), (landing, tip)):
                output[row][col] = value
            traces.append(
                {
                    "kind": "tip",
                    "source_col": col,
                    "hits": hits,
                    "component": None,
                    "scores": {},
                    "landing_col": col,
                    "landing_row": landing,
                }
            )
            continue

        landing_col = col
        component: list[tuple[int, int]] | None = None
        scores: dict[int, int] = {}
        candidates: list[int] = []
        shelf_cleared: list[tuple[int, int]] = []
        if not stay_in_source and hits and hits[-1] >= height - 2:
            component = facts["component_by_cell"][(hits[-1], col)]
            scores = _scores(component, metric, height)
            maximum = max(scores.values())
            candidates = sorted(candidate for candidate, score in scores.items() if score == maximum)
            if candidate_policy == "nearest":
                landing_col = min(candidates, key=lambda candidate: (abs(candidate - col), candidate))
            elif candidate_policy == "leftmost":
                landing_col = min(candidates)
            elif candidate_policy == "rightmost":
                landing_col = max(candidates)
            else:
                raise ValueError(f"unknown candidate policy: {candidate_policy}")

            counts = Counter(cell_col for _, cell_col in component)
            if clear_shelf and set(counts.values()) == {1}:
                bar_row = component[0][0]
                left = sum(candidate < landing_col for candidate in counts)
                right = sum(candidate > landing_col for candidate in counts)
                step = 1 if right >= left else -1
                for offset in range(1, len(mover_cols)):
                    candidate = landing_col + step * offset
                    if 0 <= candidate < width and grid[bar_row][candidate] == obstacle:
                        output[bar_row][candidate] = background
                        shelf_cleared.append((bar_row, candidate))
        for row in range(height - 3, height):
            output[row][landing_col] = body
        traces.append(
            {
                "kind": "body",
                "source_col": col,
                "hits": hits,
                "component": component,
                "scores": dict(sorted(scores.items())),
                "candidates": candidates,
                "landing_col": landing_col,
                "landing_row": height - 1,
                "shelf_cleared": shelf_cleared,
            }
        )
    return {"output": output, "columns": traces}


def predict_with_trace(grid: Any, metric: str) -> dict[str, Any]:
    if type(metric) is not str or metric not in METRICS:
        raise ValueError("metric must be a declared setting")
    return _predict_policy(grid, metric)


def predict(grid: Any, metric: str) -> list[list[int]]:
    return predict_with_trace(grid, metric)["output"]


def _model_prediction(name: str, grid: Any, selected_metric: str) -> list[list[int]]:
    if name in METRICS:
        return _predict_policy(grid, name)["output"]
    if name == "stay_in_source_column":
        return _predict_policy(grid, selected_metric, stay_in_source=True)["output"]
    if name == "leftmost_best_column":
        return _predict_policy(grid, selected_metric, candidate_policy="leftmost")["output"]
    if name == "rightmost_best_column":
        return _predict_policy(grid, selected_metric, candidate_policy="rightmost")["output"]
    if name == "no_shelf_clearing":
        return _predict_policy(grid, selected_metric, clear_shelf=False)["output"]
    if name == "tips_ignore_obstacles":
        return _predict_policy(grid, selected_metric, honor_tip_obstacles=False)["output"]
    if name == "bottom_touching_run":
        return _predict_policy(grid, "bottom_touching_run")["output"]
    raise ValueError(f"unknown model: {name}")


def teaching_report(
    train: Any, query_inputs: Any, metric: str
) -> dict[str, Any]:
    """Audit a lesson against a finite, explicit family of shortcut rules.

    Query labels are recomputed from the selected rule and are never read from
    the episode.  A survivor is harmful only if it also changes a query answer.
    """
    if metric not in METRICS:
        raise ValueError("metric must be declared")
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty list")
    if type(query_inputs) is not list or not query_inputs:
        raise ValueError("query_inputs must be a nonempty list")
    for pair in train:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("each demonstration needs input and output")
        _validated_grid(pair["input"])
        _validated_grid(pair["output"])
    for grid in query_inputs:
        _validated_grid(grid)

    survivors: list[str] = []
    harmful: list[str] = []
    query_reference = [predict(grid, metric) for grid in query_inputs]
    details: dict[str, Any] = {}
    for name in _MODEL_NAMES:
        demo_matches = [
            _model_prediction(name, pair["input"], metric) == pair["output"]
            for pair in train
        ]
        survives = all(demo_matches)
        query_differences = []
        if survives:
            query_differences = [
                _model_prediction(name, grid, metric) != expected
                for grid, expected in zip(query_inputs, query_reference)
            ]
            survivors.append(name)
            if any(query_differences):
                harmful.append(name)
        details[name] = {
            "demo_matches": demo_matches,
            "survives": survives,
            "query_differences": query_differences,
        }
    return {
        "schema": "arcpuzzles-finite-rival-audit-v1",
        "selected_metric": metric,
        "tested_models": list(_MODEL_NAMES),
        "setting_survivors": [name for name in METRICS if name in survivors],
        "all_survivors": survivors,
        "harmful_survivors": harmful,
        "details": details,
    }


def _seeded_rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"6fde852adb54-parametric-v1|{seed}|{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _base_grid(
    height: int,
    width: int,
    start: int,
    tip_mask: tuple[int, int, int],
    palette: tuple[int, int, int, int],
) -> tuple[list[list[int]], set[tuple[int, int]]]:
    background, body, tip, _ = palette
    grid = [[background for _ in range(width)] for _ in range(height)]
    for row in (0, 1):
        for col in range(start, start + 3):
            grid[row][col] = body
    for offset, is_tip in enumerate(tip_mask):
        grid[2][start + offset] = tip if is_tip else body
    return grid, set()


def _add_component(
    obstacles: set[tuple[int, int]],
    cells: Iterable[tuple[int, int]],
    *,
    height: int,
    width: int,
    reserved: set[tuple[int, int]],
    require_isolated: bool = False,
) -> None:
    cells = set(cells)
    if not cells:
        raise ValueError("component must be nonempty")
    if any(not (3 <= row < height and 0 <= col < width) for row, col in cells):
        raise ValueError("obstacle cell out of bounds")
    if cells & reserved:
        raise ValueError("obstacle overlaps mover")
    if require_isolated:
        halo = {
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in _DIRECTIONS
        }
        if cells & obstacles or halo & obstacles:
            return
    obstacles.update(cells)


def _boundary_components(height: int, width: int) -> list[set[tuple[int, int]]]:
    middle = height // 2
    return [
        {(3, 0), (4, 0), (4, 1)},
        {(3, width - 1), (4, width - 1), (5, width - 1)},
        {(middle, 0), (middle, 1), (middle + 1, 1)},
        {(middle, width - 2), (middle, width - 1), (middle + 1, width - 2)},
        {(height - 3, 0), (height - 2, 0), (height - 1, 0)},
        {(height - 3, width - 1), (height - 2, width - 1), (height - 1, width - 1)},
    ]


def _finish_scene(
    grid: list[list[int]],
    obstacles: set[tuple[int, int]],
    palette: tuple[int, int, int, int],
) -> list[list[int]]:
    obstacle = palette[3]
    for row, col in obstacles:
        grid[row][col] = obstacle
    facts = analyze(grid)
    if not 5 <= len(facts["obstacle_components"]) <= 12:
        raise RuntimeError("constructed scene has an invalid component count")
    if predict(grid, "total_cells") == grid or predict(grid, "longest_vertical_run") == grid:
        raise RuntimeError("constructed scene must move the object")
    return grid


def _add_standard_distractors(
    obstacles: set[tuple[int, int]],
    *,
    height: int,
    width: int,
    reserved: set[tuple[int, int]],
    dense: bool,
) -> None:
    for component in _boundary_components(height, width):
        _add_component(
            obstacles,
            component,
            height=height,
            width=width,
            reserved=reserved,
            require_isolated=True,
        )
    interior = {
        (height // 2 - 3, 3),
        (height // 2 - 3, 4),
        (height // 2 - 2, 4),
        (height // 2 - 1, 4),
        (height // 2 - 1, 5),
    }
    _add_component(
        obstacles,
        interior,
        height=height,
        width=width,
        reserved=reserved,
        require_isolated=True,
    )
    if dense:
        extra = {
            (height // 2 - 5, width - 6),
            (height // 2 - 5, width - 5),
            (height // 2 - 4, width - 5),
            (height // 2 - 3, width - 5),
            (height // 2 - 3, width - 4),
        }
        _add_component(
            obstacles,
            extra,
            height=height,
            width=width,
            reserved=reserved,
            require_isolated=True,
        )


def _discriminator_scene(
    height: int,
    width: int,
    start: int,
    palette: tuple[int, int, int, int],
    *,
    direction: int,
    dense: bool = False,
) -> list[list[int]]:
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    tip_mask = (1, 1, 0) if direction == 1 else (0, 1, 1)
    grid, obstacles = _base_grid(height, width, start, tip_mask, palette)
    mover = {(row, col) for row in range(3) for col in range(start, start + 3)}
    source = start + 2 if direction == 1 else start
    c1, c2, c3 = source + direction, source + 2 * direction, source + 3 * direction
    main = {
        (height - 2, source),
        (height - 1, source),
        *( (row, c1) for row in range(height - 5, height - 1) ),
        (height - 7, c2),
        (height - 5, c2),
        (height - 3, c2),
        (height - 2, c2),
        (height - 1, c2),
        (height - 7, c3),
        (height - 6, c3),
        (height - 5, c3),
    }
    _add_component(obstacles, main, height=height, width=width, reserved=mover)
    _add_standard_distractors(
        obstacles,
        height=height,
        width=width,
        reserved=mover,
        dense=dense,
    )
    return _finish_scene(grid, obstacles, palette)


def _bar_scene(
    height: int,
    width: int,
    start: int,
    palette: tuple[int, int, int, int],
) -> list[list[int]]:
    grid, obstacles = _base_grid(height, width, start, (1, 0, 1), palette)
    mover = {(row, col) for row in range(3) for col in range(start, start + 3)}
    source = start + 1
    bar = {(height - 1, col) for col in range(source - 4, source + 5)}
    stopper = {(6, start), (6, start - 1), (7, start - 1)}
    _add_component(obstacles, bar, height=height, width=width, reserved=mover)
    _add_component(obstacles, stopper, height=height, width=width, reserved=mover)
    _add_standard_distractors(
        obstacles,
        height=height,
        width=width,
        reserved=mover,
        dense=False,
    )
    return _finish_scene(grid, obstacles, palette)


def _bottom_run_scene(
    height: int,
    width: int,
    start: int,
    palette: tuple[int, int, int, int],
    *,
    direction: int,
) -> list[list[int]]:
    tip_mask = (1, 1, 0) if direction == 1 else (0, 1, 1)
    grid, obstacles = _base_grid(height, width, start, tip_mask, palette)
    mover = {(row, col) for row in range(3) for col in range(start, start + 3)}
    source = start + 2 if direction == 1 else start
    candidate = source + direction
    main = {
        (height - 3, source),
        (height - 2, source),
        (height - 1, source),
        (height - 6, candidate),
        (height - 5, candidate),
        (height - 4, candidate),
        (height - 3, candidate),
    }
    _add_component(obstacles, main, height=height, width=width, reserved=mover)
    _add_standard_distractors(
        obstacles,
        height=height,
        width=width,
        reserved=mover,
        dense=False,
    )
    return _finish_scene(grid, obstacles, palette)


def _palette(seed: int, label: str) -> tuple[int, int, int, int]:
    rng = _seeded_rng(seed, label)
    return tuple(rng.sample(range(10), 4))  # type: ignore[return-value]


def _all_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [
        _discriminator_scene(16, 18, 4, _palette(seed, "d0"), direction=1),
        _bar_scene(18, 20, 8, _palette(seed, "d1")),
        _bottom_run_scene(20, 18, 5, _palette(seed, "d2"), direction=1),
        _discriminator_scene(22, 22, 10, _palette(seed, "d3"), direction=-1),
        _bar_scene(24, 24, 10, _palette(seed, "d4")),
        _bottom_run_scene(16, 24, 12, _palette(seed, "d5"), direction=-1),
    ]
    queries = [
        _discriminator_scene(14, 14, 6, _palette(seed, "q0"), direction=-1),
        _bar_scene(18, 20, 9, _palette(seed, "q1")),
        _bottom_run_scene(24, 24, 10, _palette(seed, "q2"), direction=1),
        _discriminator_scene(30, 30, 12, _palette(seed, "q3"), direction=1, dense=True),
    ]
    return demos, queries


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Generate one deterministic, setting-identifying episode."""
    metric = _validated_settings(settings)
    if not _integer(seed) or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if not _integer(demos) or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if not _integer(queries) or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    demo_inputs, query_inputs = _all_inputs(seed)
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"landing_metric": metric},
        "train": [
            {"input": deepcopy(grid), "output": predict(grid, metric)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": deepcopy(grid), "output": predict(grid, metric)}
            for grid in query_inputs
        ],
        "program_solution": program({"landing_metric": metric}),
    }
    serialized = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in episode["train"] + episode["test"]
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all generated inputs must be distinct")
    return episode


def public_turn(episode: Any, query_index: int) -> dict[str, Any]:
    """Project exactly one query input plus all demonstrations."""
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if not _integer(query_index) or not 0 <= query_index < len(episode["test"]):
        raise ValueError("query_index is out of range")
    train = []
    for pair in episode["train"]:
        train.append(
            {
                "input": _validated_grid(pair["input"]),
                "output": _validated_grid(pair["output"]),
            }
        )
    query = _validated_grid(episode["test"][query_index]["input"])
    return {"train": train, "test": [{"input": query}]}


def public_turn_bytes(episode: Any, query_index: int) -> bytes:
    return public_challenge_bytes(public_turn(episode, query_index))


def public_turn_id(episode: Any, query_index: int) -> str:
    return public_challenge_id(public_turn(episode, query_index))
