"""Tail-order variants for the path-concatenation task 664a918eb273.

The exact canonical rule keeps the input left-to-right order.  Two nearby
settings keep the first path fixed and order only the remaining paths by their
input-derived cell counts before the same sequential endpoint-to-entry packing.
Python outputs are deterministic authoring claims; native qualification replays
all labels with protected Racket.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import load_selected_generator

TASK_ID = "664a918eb273"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE, BASE_PATH, BASE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_text(encoding="utf-8")
TAIL_ORDERS = ("left_to_right", "shortest_first", "longest_first")
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
_LIMIT = 2**63 - 1
_INFO_DECLARATION = "(define infos (map obj-info sorted-objs))"

_DEMO_PROFILES = (
    {"name": "strong_mixed", "overrides": {"grid_h": 8, "grid_w": 22, "n_paths": 5,
        "n_distinct_colors": 3, "gap": 2, "anchor_col": 1}, "strong": True},
    {"name": "canonical_scale", "overrides": {"grid_h": 3, "grid_w": 11, "n_paths": 4,
        "n_distinct_colors": 2, "gap": 1, "anchor_col": 0}},
    {"name": "medium_reuse", "overrides": {"grid_h": 6, "grid_w": 18, "n_paths": 4,
        "n_distinct_colors": 2, "gap": 2, "anchor_col": 1}},
    {"name": "single_color", "overrides": {"grid_h": 10, "grid_w": 25, "n_paths": 5,
        "n_distinct_colors": 1, "gap": 3, "anchor_col": 1}},
    {"name": "distinct_palette", "overrides": {"grid_h": 12, "grid_w": 28, "n_paths": 4,
        "n_distinct_colors": 4, "gap": 3, "anchor_col": 3}},
    {"name": "dense_five", "overrides": {"grid_h": 7, "grid_w": 20, "n_paths": 5,
        "n_distinct_colors": 2, "gap": 1, "anchor_col": 2}},
)
_QUERY_PROFILES = (
    {"name": "small_transfer", "overrides": {"grid_h": 4, "grid_w": 15, "n_paths": 4,
        "n_distinct_colors": 2, "gap": 1, "anchor_col": 1}},
    {"name": "five_path_interaction", "overrides": {"grid_h": 9, "grid_w": 24, "n_paths": 5,
        "n_distinct_colors": 3, "gap": 2, "anchor_col": 2}},
    {"name": "large_repeated", "overrides": {"grid_h": 12, "grid_w": 29, "n_paths": 4,
        "n_distinct_colors": 1, "gap": 3, "anchor_col": 3}},
    {"name": "boundary_30x30", "overrides": {"grid_h": 12, "grid_w": 30, "n_paths": 5,
        "n_distinct_colors": 5, "gap": 3, "anchor_col": 3}, "lift_30": True},
)


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must lie in {low}..{high}")
    return value


def _tail_order(value: Any) -> str:
    if type(value) is not str or value not in TAIL_ORDERS:
        raise ValueError(f"tail_order must be one of {TAIL_ORDERS}")
    return value


def _replace_info_declaration(replacement: str) -> str:
    if CANONICAL_PROGRAM.count(_INFO_DECLARATION) != 1:
        raise RuntimeError("canonical Racket source no longer has the expected info declaration")
    return CANONICAL_PROGRAM.replace(_INFO_DECLARATION, replacement)


def program_for(order: str) -> str:
    order = _tail_order(order)
    if order == "left_to_right":
        return CANONICAL_PROGRAM
    multiplier = "100" if order == "shortest_first" else "-100"
    replacement = f"""(define left-to-right-infos (map obj-info sorted-objs))
             (define infos
               (cons (first left-to-right-infos)
                     (sort-by (cdr left-to-right-infos)
                              (lambda (info)
                                (+ (* {multiplier} (length (nth info 0)))
                                   (second (nth info 1)))))))"""
    return _replace_info_declaration(replacement)


def _infos(grid: list[list[int]]) -> list[dict[str, Any]]:
    errors, infos, _ = BASE._analyze(deepcopy(grid))
    if errors:
        raise ValueError("input is outside the selected generator grammar: " + "; ".join(errors))
    if len(infos) < 4:
        raise ValueError("tail-order family needs at least four paths")
    return infos


def _ordered_indices(infos: list[dict[str, Any]], order: str) -> list[int]:
    order = _tail_order(order)
    indices = list(range(len(infos)))
    if order == "left_to_right":
        return indices
    if order == "shortest_first":
        key = lambda index: (len(infos[index]["cells"]), infos[index]["entry"][1], index)
    else:
        key = lambda index: (-len(infos[index]["cells"]), infos[index]["entry"][1], index)
    return [0, *sorted(indices[1:], key=key)]


def _render_indices(
    grid: list[list[int]],
    indices: Iterable[int],
    *,
    left_justify: bool = False,
    horizontal_only: bool = False,
) -> list[list[int]]:
    infos = _infos(grid)
    order = list(indices)
    if sorted(order) != list(range(len(infos))) or order[0] != 0:
        raise ValueError("render order must preserve the first path and permute every tail path once")
    occupied: set[tuple[int, int]] = set()
    colored: list[tuple[int, int, int]] = []
    previous_exit: tuple[int, int] | None = None
    height = len(grid)
    for index in order:
        info = infos[index]
        if previous_exit is None:
            dr = 0
            dc = -info["entry"][1] if left_justify else 0
        else:
            dr = 0 if horizontal_only else previous_exit[0] - info["entry"][0]
            dc = previous_exit[1] + 1 - info["entry"][1]
        placed = {(row + dr, col + dc) for row, col in info["cells"]}
        if any(row < 0 or row >= height or col < 0 for row, col in placed):
            raise ValueError("tail order would clip a path")
        if placed & occupied:
            raise ValueError("tail order would overlap paths")
        occupied.update(placed)
        colored.extend((row + dr, col + dc, info["color"]) for row, col in info["cells"])
        previous_exit = info["exit"][0] + dr, info["exit"][1] + dc
    width = max(col for _, col, _ in colored) + 1
    if not 1 <= width <= 30:
        raise ValueError("tail order output width must lie in 1..30")
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col, color in colored:
        output[row][col] = color
    return output


def output_for(grid: list[list[int]], order: str) -> list[list[int]]:
    infos = _infos(grid)
    return _render_indices(grid, _ordered_indices(infos, order))


def dependency_intermediate(grid: list[list[int]], order: str) -> dict[str, Any]:
    infos = _infos(grid)
    selected = _ordered_indices(infos, order)
    path_rows = [
        {
            "original_index": index,
            "length": len(info["cells"]),
            "entry": list(info["entry"]),
            "exit": list(info["exit"]),
            "color": info["color"],
        }
        for index, info in enumerate(infos)
    ]
    return {
        "tail_order": _tail_order(order),
        "paths_left_to_right": path_rows,
        "selected_tail_indices": selected[1:],
        "selected_tail_lengths": [len(infos[index]["cells"]) for index in selected[1:]],
    }


def _rival_names() -> tuple[str, ...]:
    return (
        *(f"setting:{order}" for order in TAIL_ORDERS),
        "shortcut:left_justify_selected_order",
        "shortcut:horizontal_only_selected_order",
        "shortcut:color_ascending_tail",
        "shortcut:reverse_tail",
        "shortcut:identity",
    )


def _rival_prediction(
    grid: list[list[int]], selected: str, candidate: str
) -> list[list[int]]:
    infos = _infos(grid)
    selected_indices = _ordered_indices(infos, selected)
    if candidate.startswith("setting:"):
        return output_for(grid, candidate.removeprefix("setting:"))
    if candidate == "shortcut:left_justify_selected_order":
        return _render_indices(grid, selected_indices, left_justify=True)
    if candidate == "shortcut:horizontal_only_selected_order":
        return _render_indices(grid, selected_indices, horizontal_only=True)
    if candidate == "shortcut:color_ascending_tail":
        return _render_indices(
            grid,
            [0, *sorted(
                range(1, len(infos)),
                key=lambda i: (infos[i]["color"], infos[i]["entry"][1], i),
            )],
        )
    if candidate == "shortcut:reverse_tail":
        return _render_indices(grid, [0, *reversed(range(1, len(infos)))])
    if candidate == "shortcut:identity":
        return deepcopy(grid)
    raise ValueError(f"unknown rival: {candidate}")


def _rival_predictions(grid: list[list[int]], selected: str) -> dict[str, list[list[int]]]:
    """Return only valid finite-rival predictions for exploratory callers.

    Auditing uses ``_rival_prediction`` directly so one invalid shortcut cannot
    poison the prediction of an otherwise valid candidate.
    """
    predictions: dict[str, list[list[int]]] = {}
    for candidate in _rival_names():
        try:
            predictions[candidate] = _rival_prediction(grid, selected, candidate)
        except (TypeError, ValueError):
            continue
    return predictions


def audit_episode(episode: dict[str, Any], selected: str) -> dict[str, Any]:
    selected = _tail_order(selected)
    candidates = sorted(_rival_names())
    survivors: list[str] = []
    refutations: dict[str, int | str] = {}
    for candidate in candidates:
        failure: int | None = None
        try:
            for index, pair in enumerate(episode["train"]):
                if _rival_prediction(pair["input"], selected, candidate) != pair["output"]:
                    failure = index
                    break
        except (TypeError, ValueError) as exc:
            refutations[candidate] = f"invalid prediction: {exc}"
            continue
        if failure is None:
            survivors.append(candidate)
        else:
            refutations[candidate] = failure
    ambiguous: list[str] = []
    for candidate in survivors:
        if candidate == f"setting:{selected}":
            continue
        try:
            if any(_rival_prediction(pair["input"], selected, candidate) != pair["output"]
                   for pair in episode["test"]):
                ambiguous.append(candidate)
        except (TypeError, ValueError):
            ambiguous.append(candidate)
    return {
        "selected": selected,
        "rivals": candidates,
        "survivors": survivors,
        "ambiguous_query_rivals": ambiguous,
        "refutations": refutations,
        "scope": "finite declared setting and shortcut family; not universal uniqueness",
    }


def _distinct_native_outputs(grid: list[list[int]]) -> bool:
    try:
        outputs = [output_for(grid, order) for order in TAIL_ORDERS]
    except (TypeError, ValueError):
        return False
    return len({json.dumps(output, separators=(",", ":")) for output in outputs}) == len(TAIL_ORDERS)


def _strongly_distinguishing(grid: list[list[int]]) -> bool:
    if not _distinct_native_outputs(grid):
        return False
    try:
        for selected in TAIL_ORDERS:
            expected = output_for(grid, selected)
            for name in _rival_names():
                if name == f"setting:{selected}":
                    continue
                try:
                    prediction = _rival_prediction(grid, selected, name)
                except (TypeError, ValueError):
                    continue
                if prediction == expected:
                    return False
    except (TypeError, ValueError):
        return False
    return True


def _lift_to_30(grid: list[list[int]]) -> list[list[int]]:
    infos = _infos(grid)
    if len(grid[0]) != 30 or len(infos) != 5:
        raise ValueError("30x30 lift requires a width-30 five-path source")
    output = [[0 for _ in range(30)] for _ in range(30)]
    tail_slots = (0, 7, 18, None)
    for index, info in enumerate(infos):
        min_row = min(row for row, _ in info["cells"])
        max_row = max(row for row, _ in info["cells"])
        shape_height = max_row - min_row + 1
        if index == 0:
            entry_offset = info["entry"][0] - min_row
            top = max(0, min(30 - shape_height, 14 - entry_offset))
        else:
            requested = tail_slots[index - 1]
            top = 30 - shape_height if requested is None else min(requested, 30 - shape_height)
        for row, col in info["cells"]:
            target = top + row - min_row, col
            if output[target[0]][target[1]] != 0:
                raise ValueError("30x30 lift collision")
            output[target[0]][target[1]] = info["color"]
    if BASE.self_check(output):
        raise ValueError("30x30 lift left the selected generator grammar")
    return output


def _mixed_seed(seed: int, slot: int, attempt: int) -> int:
    return (seed * 1_000_003 + slot * 97_409 + attempt * 7_919 + 0x664A918) % (_LIMIT + 1)


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _thaw(grid: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    return [list(row) for row in grid]


def _sample_input(seed: int, slot: int, profile: dict[str, Any], seen: set[str]) -> list[list[int]]:
    for attempt in range(768):
        mixed = _mixed_seed(seed, slot, attempt)
        try:
            grid = BASE.generate(
                mixed,
                2 * (slot + attempt) + 1,
                difficulty="hard",
                **profile["overrides"],
            )
            if profile.get("lift_30"):
                grid = _lift_to_30(grid)
            if BASE.self_check(grid):
                continue
            if not _distinct_native_outputs(grid):
                continue
            if profile.get("strong") and not _strongly_distinguishing(grid):
                continue
            if profile.get("lift_30"):
                rows = [r for r, row in enumerate(grid) if any(row)]
                if min(rows) != 0 or max(rows) != 29:
                    continue
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                continue
            seen.add(key)
            return grid
        except (RuntimeError, TypeError, ValueError):
            continue
    raise RuntimeError(f"could not construct profile {profile['name']} after bounded search")


@lru_cache(maxsize=32)
def _episode_inputs(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    for index, profile in enumerate(_DEMO_PROFILES):
        grids.append(_sample_input(seed, 100 + index, profile, seen))
    for index, profile in enumerate(_QUERY_PROFILES):
        grids.append(_sample_input(seed, 200 + index, profile, seen))
    return tuple(_freeze(grid) for grid in grids)


def generate_episode(seed: int, order: str, demos: int, queries: int) -> dict[str, Any]:
    seed = _literal_int("seed", seed, 0, _LIMIT)
    order = _tail_order(order)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    stored = _episode_inputs(seed)
    demo_inputs = [_thaw(grid) for grid in stored[:demos]]
    query_inputs = [_thaw(grid) for grid in stored[len(_DEMO_PROFILES):]]
    pairs = [
        {"input": deepcopy(grid), "output": output_for(grid, order)}
        for grid in [*demo_inputs, *query_inputs]
    ]
    episode = {
        "train": pairs[:demos],
        "test": pairs[demos:demos + queries],
        "program_solution": program_for(order),
    }
    audit = audit_episode(episode, order)
    if audit["survivors"] != [f"setting:{order}"] or audit["ambiguous_query_rivals"]:
        raise RuntimeError("constructed demonstrations did not identify the finite rule family")
    return deepcopy(episode)
