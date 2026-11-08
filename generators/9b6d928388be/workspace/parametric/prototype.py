"""Native episode generator for keyed-frame assignment by topology or area rank.

The canonical setting assigns loose objects to keyed frames by enclosed-hole
count.  The alternative setting computes an input-dependent ascending area rank
for the three loose objects and uses key 1/2/3 as the rank selector.  Inputs are
matched across settings; every ordinary scene makes the two assignments differ.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
from pathlib import Path
import random
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"
CANONICAL_PATH = HERE / "canonical.rkt"
BASIS_VALUES = ("holes", "area_rank")


def _adjacent_generator():
    name = "_arc_9b6d928388be_base_" + hashlib.sha256(
        str(GENERATOR_PATH).encode()
    ).hexdigest()
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _adjacent_generator()

# Curated shape triples cover each non-identity ordering of object area.  Each
# tuple is (zero-hole, one-hole, two-hole).  Objects remain small enough for the
# 5x6 interiors used by the generated frames.
Z4 = ((1, 1), (1, 1))
Z12 = ((1, 1, 1, 1),) * 3
Z20 = ((1, 1, 1, 1, 1),) * 4
O8 = ((1, 1, 1), (1, 0, 1), (1, 1, 1))
O12 = (
    (1, 1, 1, 1),
    (1, 0, 0, 1),
    (1, 0, 0, 1),
    (1, 1, 1, 1),
)
O16 = (
    (1, 1, 1, 1, 1),
    (1, 0, 0, 0, 1),
    (1, 0, 0, 0, 1),
    (1, 0, 0, 0, 1),
    (1, 1, 1, 1, 1),
)
T11 = (
    (1, 1, 1, 1, 1),
    (1, 0, 1, 0, 1),
    (0, 1, 1, 1, 0),
)
T13 = (
    (1, 1, 1, 1, 1),
    (1, 0, 1, 0, 1),
    (1, 1, 1, 1, 1),
)
T16 = (
    (1, 1, 1, 1, 1),
    (1, 0, 1, 0, 1),
    (1, 0, 1, 0, 1),
    (1, 1, 1, 1, 1),
)
SHAPE_TRIPLES = (
    (Z4, O16, T13),   # zero < two < one
    (Z20, O8, T13),   # one < two < zero
    (Z12, O8, T16),   # one < zero < two
    (Z12, O16, T11),  # two < zero < one
    (Z20, O12, T11),  # two < one < zero
)
DIMS = ((24, 26), (25, 28), (27, 30), (29, 30), (30, 30))
PALETTES = (
    (4, 6, 8), (7, 9, 4), (8, 4, 7), (6, 9, 8), (9, 7, 6),
)
QUERY_SCENE_INDICES = (104, 101, 102, 103)


def _size(pattern):
    return sum(sum(row) for row in pattern)


for triple in SHAPE_TRIPLES:
    assert tuple(BASE._pattern_holes(pattern) for pattern in triple) == (0, 1, 2)
    assert all(BASE._connected(pattern) for pattern in triple)
    sizes = tuple(_size(pattern) for pattern in triple)
    assert len(set(sizes)) == 3
    assert sorted(range(3), key=lambda i: sizes[i]) != [0, 1, 2]


def _rng(seed: int, index: int) -> random.Random:
    digest = hashlib.sha256(f"9b6d928388be|{seed}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _frame_cells(frame):
    top, bottom, left, right = frame
    return {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }


def _mirror_lr(grid):
    return [row[::-1] for row in grid]


def scene(seed: int, index: int) -> list[list[int]]:
    """Return a lawful matched input; setting never enters this sampler."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer; bool is forbidden")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative integer; bool is forbidden")
    rng = _rng(seed, index)
    height, width = DIMS[index % len(DIMS)]
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Three 7x9 frames with 5x7 interiors.  Small keyed jitter and optional
    # horizontal reflection vary geometry while preserving the source grammar.
    jitter_a = rng.randrange(0, 2)
    jitter_b = rng.randrange(0, 2)
    frames = [
        (2 + jitter_a, 8 + jitter_a, width - 10, width - 2),
        (height - 9, height - 3, width - 10, width - 2),
        (height - 9, height - 3, 5 + jitter_b, 13 + jitter_b),
    ]
    frames.sort()
    keys = list((1, 2, 3))
    rng.shuffle(keys)
    for frame, key in zip(frames, keys):
        for row, col in _frame_cells(frame):
            grid[row][col] = 5
        top, _, left, right = frame
        grid[top - 1][(left + right) // 2] = key

    patterns = SHAPE_TRIPLES[(index + rng.randrange(len(SHAPE_TRIPLES))) % len(SHAPE_TRIPLES)]

    # Color is a deliberately independent nuisance variable.  Pick a numeric
    # color ordering that is neither topology order nor area order so a
    # color-sorting shortcut is refuted by every generated example.
    sorted_palette = sorted(PALETTES[(seed + index) % len(PALETTES)])
    topology_order = (0, 1, 2)
    area_order = tuple(sorted(range(3), key=lambda i: _size(patterns[i])))
    admissible_color_orders = [
        order for order in itertools.permutations(range(3))
        if order not in (topology_order, area_order)
    ]
    color_order = admissible_color_orders[rng.randrange(len(admissible_color_orders))]
    colors = [0, 0, 0]
    for rank, object_index in enumerate(color_order):
        colors[object_index] = sorted_palette[rank]

    placements = [(2, 2), (9, 2), (9, 9)]
    rng.shuffle(placements)
    for pattern, color, (top, left) in zip(patterns, colors, placements):
        BASE._paint_pattern(grid, top, left, pattern, color)

    if rng.randrange(2):
        grid = _mirror_lr(grid)
    return grid


def _basis(value: Any) -> str:
    if type(value) is not str or value not in BASIS_VALUES:
        raise ValueError("assignment_basis must be 'holes' or 'area_rank'")
    return value


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"assignment_basis"}:
        raise ValueError("settings must contain exactly assignment_basis")
    return _basis(settings["assignment_basis"])


def canonical_source() -> str:
    return CANONICAL_PATH.read_text(encoding="utf-8")


_CANONICAL_SELECTION = """               (candidates
                (filter (lambda (obj)
                          (= (topo-count-holes source obj 0) (- value 1)))
                        loose))
               (chosen (if (empty? candidates)
                           #f
                           (first (sort candidates
                                        (lambda (a b)
                                          (> (obj-size a) (obj-size b)))))))"""


def _ranked_source(comparator: str) -> str:
    if type(comparator) is not str or not comparator.strip():
        raise ValueError("comparator must be nonempty Racket source")
    replacement = f"""               (ranked
                (sort loose {comparator}))
               (chosen
                (if (and (> value 0) (< value (+ (length ranked) 1)))
                    (list-ref ranked (- value 1))
                    #f))"""
    source = canonical_source()
    if source.count(_CANONICAL_SELECTION) != 1:
        raise ValueError("canonical assignment block changed or is ambiguous")
    return source.replace(_CANONICAL_SELECTION, replacement, 1)


def area_rank_source(*, descending: bool = False) -> str:
    comparison = ">" if descending else "<"
    return _ranked_source(
        f"(lambda (a b) ({comparison} (obj-size a) (obj-size b)))"
    )


def rival_programs() -> dict[str, str]:
    """Return executable named alternatives used by bounded teaching audits."""
    return {
        "area_descending": area_rank_source(descending=True),
        "source_order": _ranked_source(
            "(lambda (a b) "
            "(cell< (list (obj-r1 a) (obj-c1 a)) "
            "       (list (obj-r1 b) (obj-c1 b))))"
        ),
        "color_order": _ranked_source(
            "(lambda (a b) (< (obj-color a) (obj-color b)))"
        ),
    }


def program(settings: dict[str, Any]) -> str:
    basis = _settings(settings)
    return canonical_source() if basis == "holes" else area_rank_source()


def counterfactual_program(settings: dict[str, Any], ablation: str) -> str:
    basis = _settings(settings)
    if ablation != "wrong_intermediate":
        raise ValueError("only wrong_intermediate is supported")
    if basis == "area_rank":
        return area_rank_source(descending=True)
    return area_rank_source()


def _loose_state(grid):
    frames = sorted(
        (BASE._bbox(component["cells"]) for component in BASE._components(grid)
         if BASE._rect_frame(component))
    )
    source = BASE._erase_frames_and_keys(grid, frames)
    loose = BASE._components(source)
    return frames, source, loose


def _ranked(loose, order: str):
    if order not in {"ascending", "descending"}:
        raise ValueError("rank_order must be ascending or descending")
    reverse = order == "descending"
    return sorted(
        loose,
        key=lambda component: (
            len(component["cells"]),
            BASE._bbox(component["cells"]),
            component["color"],
        ),
        reverse=reverse,
    )


def assignment_intermediate(grid: list[list[int]], basis: str) -> list[dict[str, Any]]:
    basis = _basis(basis)
    frames, source, loose = _loose_state(grid)
    if basis == "area_rank":
        chosen = _ranked(loose, "ascending")
    else:
        by_holes = {
            BASE._pattern_holes(BASE._component_pattern(component)): component
            for component in loose
        }
        chosen = [by_holes[index] for index in range(3)]
    return [
        {
            "key": key,
            "color": component["color"],
            "cells": len(component["cells"]),
            "holes": BASE._pattern_holes(BASE._component_pattern(component)),
            "bbox": list(BASE._bbox(component["cells"])),
        }
        for key, component in enumerate(chosen, start=1)
    ]


def transform(
    grid: list[list[int]],
    basis: str,
    *,
    rank_order: str = "ascending",
) -> list[list[int]]:
    """Independent diagnostic mirror; qualification re-executes Racket labels."""
    basis = _basis(basis)
    errors = BASE._valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    frames, source, loose = _loose_state(grid)
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for frame in frames:
        for row, col in BASE._border_cells(frame):
            output[row][col] = 5
    if basis == "area_rank":
        ranked = _ranked(loose, rank_order)
    else:
        ranked = []
    for frame in frames:
        top, bottom, left, right = frame
        key_row, key_col = top - 1, (left + right) // 2
        value = grid[key_row][key_col]
        output[key_row][key_col] = value
        if basis == "holes":
            candidates = [
                component for component in loose
                if BASE._pattern_holes(BASE._component_pattern(component)) == value - 1
            ]
            chosen = max(candidates, key=lambda component: len(component["cells"]))
        else:
            chosen = ranked[value - 1]
        pattern = BASE._component_pattern(chosen)
        crop_h, crop_w = len(pattern), len(pattern[0])
        paste_top = top + 1 + BASE._floor_half((bottom - top - 1) - crop_h)
        paste_left = left + 1 + BASE._floor_half((right - left - 1) - crop_w)
        BASE._paint_pattern(output, paste_top, paste_left, pattern, chosen["color"])
    return output


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    basis = _settings(settings)
    train_inputs = [scene(seed, index) for index in range(demos)]
    test_inputs = [scene(seed, QUERY_SCENE_INDICES[index]) for index in range(queries)]
    return {
        "train": [
            {"input": grid, "output": transform(grid, basis)}
            for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": transform(grid, basis)}
            for grid in test_inputs
        ],
        "program_solution": program(settings),
    }


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an existing query; bool is forbidden")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
