"""Parametric object-order family for 73906110dd67.

The canonical setting keeps the exact source rule: sort extracted objects by
occupied cell area, then stack their tight crops vertically.  The alternative
sorts by bounding-box area.  Inputs deliberately contain a sparse 3x3 object
and a denser 4x2 object, so the two input-derived orderings disagree.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import load_selected_generator

TASK_ID = "73906110dd67"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE, BASE_PATH, BASE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_text(encoding="utf-8")
ORDER_METRICS = ("cell_area", "bbox_area")
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
_LIMIT = 2**63 - 1

_SORT_NEEDLE = "(sort (objects g 0) (lambda (a b) (> (obj-size a) (obj-size b))))"
_BBOX_SORT = """(sort (objects g 0)
                    (lambda (a b)
                      (let ((aa (* (+ 1 (- (obj-r2 a) (obj-r1 a)))
                                   (+ 1 (- (obj-c2 a) (obj-c1 a)))))
                            (bb (* (+ 1 (- (obj-r2 b) (obj-r1 b)))
                                   (+ 1 (- (obj-c2 b) (obj-c1 b))))))
                        (if (= aa bb)
                            (> (obj-size a) (obj-size b))
                            (> aa bb)))))"""

# Areas / bbox areas: 8/8, 5/9, 6/6, 3/3.  Thus cell-area and
# bbox-area descending orders necessarily disagree.
_BASE_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    tuple((r, c) for r in range(4) for c in range(2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    tuple((r, c) for r in range(2) for c in range(3)),
    ((0, 0), (1, 0), (2, 0)),
)

_PROFILES: tuple[dict[str, Any], ...] = (
    {"name": "compact_10", "h": 10, "w": 10},
    {"name": "wide_12x15", "h": 12, "w": 15},
    {"name": "tall_15x12", "h": 15, "w": 12},
    {"name": "medium_16", "h": 16, "w": 16},
    {"name": "wide_18x22", "h": 18, "w": 22},
    {"name": "tall_22x18", "h": 22, "w": 18},
    {"name": "query_13x19", "h": 13, "w": 19},
    {"name": "query_20x24", "h": 20, "w": 24},
    {"name": "query_26x28", "h": 26, "w": 28},
    {"name": "query_30", "h": 30, "w": 30},
)


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must lie in {low}..{high}")
    return value


def _metric(value: Any) -> str:
    if type(value) is not str or value not in ORDER_METRICS:
        raise ValueError(f"order_metric must be one of {ORDER_METRICS}")
    return value


def program_for(metric: str) -> str:
    metric = _metric(metric)
    if metric == "cell_area":
        return CANONICAL_PROGRAM
    if CANONICAL_PROGRAM.count(_SORT_NEEDLE) != 1:
        raise RuntimeError("canonical source no longer contains the expected sort expression")
    return CANONICAL_PROGRAM.replace(_SORT_NEEDLE, _BBOX_SORT)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = list(cells)
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return tuple(sorted((r - r0, c - c0) for r, c in values))


def _transform(shape: tuple[tuple[int, int], ...], code: int) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    code %= 8
    for _ in range(code % 4):
        cells = [(c, -r) for r, c in cells]
    if code >= 4:
        cells = [(r, -c) for r, c in cells]
    return _normalize(cells)


def _dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _rng(seed: int, slot: int, attempt: int = 0) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{slot}|{attempt}|order-metric-v1".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _metric_order(components: list[dict[str, Any]], metric: str) -> list[int]:
    metric = _metric(metric)
    if metric == "cell_area":
        return sorted(range(len(components)), key=lambda i: (-components[i]["size"], i))
    return sorted(
        range(len(components)),
        key=lambda i: (-components[i]["bbox_area"], -components[i]["size"], i),
    )


def render_order(grid: list[list[int]], order: Iterable[int], *, gap: int = 1,
                 alignment: str = "left") -> list[list[int]]:
    components = BASE._components(deepcopy(grid))
    indices = list(order)
    if sorted(indices) != list(range(len(components))):
        raise ValueError("order must be a permutation of every object index")
    return BASE._stack_components(components, order=indices, gap=gap, alignment=alignment)


def output_for(grid: list[list[int]], metric: str) -> list[list[int]]:
    components = BASE._components(deepcopy(grid))
    if len(components) != 4:
        raise ValueError("order-metric family requires exactly four objects")
    return BASE._stack_components(components, order=_metric_order(components, metric))


def dependency_intermediate(grid: list[list[int]], metric: str) -> dict[str, Any]:
    components = BASE._components(deepcopy(grid))
    selected = _metric_order(components, metric)
    return {
        "order_metric": _metric(metric),
        "objects_scan_order": [
            {
                "index": index,
                "color": comp["color"],
                "cell_area": comp["size"],
                "bbox_area": comp["bbox_area"],
                "bbox": list(comp["bbox"]),
            }
            for index, comp in enumerate(components)
        ],
        "selected_object_indices": selected,
        "selected_metric_values": [
            components[index]["size" if metric == "cell_area" else "bbox_area"]
            for index in selected
        ],
        "cell_area_order": _metric_order(components, "cell_area"),
        "bbox_area_order": _metric_order(components, "bbox_area"),
    }


def _candidate_names() -> tuple[str, ...]:
    return (
        "setting:cell_area",
        "setting:bbox_area",
        "shortcut:scan_order",
        "shortcut:smallest_first",
        "shortcut:color_desc",
        "shortcut:no_gap",
        "shortcut:center_align",
        "shortcut:reverse_selected",
    )


def _prediction(grid: list[list[int]], selected: str, candidate: str) -> list[list[int]]:
    comps = BASE._components(deepcopy(grid))
    selected_order = _metric_order(comps, selected)
    if candidate.startswith("setting:"):
        return output_for(grid, candidate.split(":", 1)[1])
    if candidate == "shortcut:scan_order":
        return render_order(grid, range(len(comps)))
    if candidate == "shortcut:smallest_first":
        return render_order(grid, sorted(range(len(comps)), key=lambda i: (comps[i]["size"], i)))
    if candidate == "shortcut:color_desc":
        return render_order(grid, sorted(range(len(comps)), key=lambda i: (-comps[i]["color"], i)))
    if candidate == "shortcut:no_gap":
        return render_order(grid, selected_order, gap=0)
    if candidate == "shortcut:center_align":
        return render_order(grid, selected_order, alignment="center")
    if candidate == "shortcut:reverse_selected":
        return render_order(grid, list(reversed(selected_order)))
    raise KeyError(candidate)


def audit_episode(episode: dict[str, Any], selected: str) -> dict[str, Any]:
    selected = _metric(selected)
    survivors: list[str] = []
    refutations: dict[str, int | str] = {}
    for candidate in _candidate_names():
        first_failure = None
        try:
            for index, pair in enumerate(episode["train"]):
                if _prediction(pair["input"], selected, candidate) != pair["output"]:
                    first_failure = index
                    break
        except (KeyError, TypeError, ValueError) as exc:
            refutations[candidate] = f"invalid prediction: {exc}"
            continue
        if first_failure is None:
            survivors.append(candidate)
        else:
            refutations[candidate] = first_failure
    ambiguous = []
    for candidate in survivors:
        if candidate == f"setting:{selected}":
            continue
        if any(_prediction(pair["input"], selected, candidate) != pair["output"]
               for pair in episode["test"]):
            ambiguous.append(candidate)
    return {
        "selected": selected,
        "rivals": list(_candidate_names()),
        "survivors": survivors,
        "ambiguous_query_rivals": ambiguous,
        "refutations": refutations,
        "scope": "finite declared setting and shortcut family; not universal uniqueness",
    }


def _strong(grid: list[list[int]]) -> bool:
    outputs: dict[str, str] = {}
    for metric in ORDER_METRICS:
        expected = output_for(grid, metric)
        outputs[metric] = json.dumps(expected, separators=(",", ":"))
        for candidate in _candidate_names():
            if candidate == f"setting:{metric}":
                continue
            try:
                if _prediction(grid, metric, candidate) == expected:
                    return False
            except (TypeError, ValueError):
                continue
    return outputs["cell_area"] != outputs["bbox_area"]


def _scene(seed: int, slot: int, profile: dict[str, Any]) -> list[list[int]]:
    h, w = profile["h"], profile["w"]
    for attempt in range(512):
        rng = _rng(seed, slot, attempt)
        shapes = [_transform(shape, rng.randrange(8)) for shape in _BASE_SHAPES]
        shape_order = list(range(4))
        rng.shuffle(shape_order)
        colors = rng.sample(list(range(1, 10)), 4)
        grid = [[0 for _ in range(w)] for _ in range(h)]
        anchors: list[tuple[int, int]] = []
        for corner, shape_index in enumerate(shape_order):
            shape = shapes[shape_index]
            sh, sw = _dims(shape)
            if corner == 0:
                top, left = 1, 1
            elif corner == 1:
                top, left = 1, w - sw - 1
            elif corner == 2:
                top, left = h - sh - 1, 1
            else:
                top, left = h - sh - 1, w - sw - 1
            anchors.append((top, left))
            for dr, dc in shape:
                if grid[top + dr][left + dc] != 0:
                    raise AssertionError("corner placement collision")
                grid[top + dr][left + dc] = colors[shape_index]
        comps = BASE._components(grid)
        if len(comps) != 4:
            continue
        if sorted(comp["size"] for comp in comps) != [3, 5, 6, 8]:
            continue
        if sorted(comp["bbox_area"] for comp in comps) != [3, 6, 8, 9]:
            continue
        if not _strong(grid):
            continue
        return grid
    raise RuntimeError(f"could not construct strong scene {profile['name']}")


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _thaw(grid: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    return [list(row) for row in grid]


@lru_cache(maxsize=64)
def _episode_inputs(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(_freeze(_scene(seed, index, profile)) for index, profile in enumerate(_PROFILES))


def generate_episode(seed: int, metric: str, demos: int, queries: int) -> dict[str, Any]:
    seed = _literal_int("seed", seed, 0, _LIMIT)
    metric = _metric(metric)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    stored = _episode_inputs(seed)
    demo_inputs = [_thaw(grid) for grid in stored[:demos]]
    query_inputs = [_thaw(grid) for grid in stored[len(_PROFILES) - QUERY_COUNT:]]
    pairs = [
        {"input": deepcopy(grid), "output": output_for(grid, metric)}
        for grid in [*demo_inputs, *query_inputs]
    ]
    episode = {
        "train": pairs[:demos],
        "test": pairs[demos:demos + queries],
        "program_solution": program_for(metric),
    }
    audit = audit_episode(episode, metric)
    if audit["survivors"] != [f"setting:{metric}"] or audit["ambiguous_query_rivals"]:
        raise RuntimeError(f"teaching audit failed: {audit}")
    return deepcopy(episode)
