"""Native parametric family for e685e65af79d.

The canonical setting closes every object under four rotations.  The alternative
has a genuine selector dependency:

Step A constructs every object's input-dependent four-rotation closure and
measures its unique-cell area.  Step B selects the unique largest closure and
adds only that object's horizontal reflection, yielding a dihedral completion
for the selected object while every other object remains rotationally closed.
"""
from __future__ import annotations

import copy
from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "e685e65af79d"
PARAMETER = "symmetry_closure"
CANONICAL = "rotational_4"
ALTERNATIVE = "largest_closure_dihedral"
SETTINGS = (CANONICAL, ALTERNATIVE)
HOME = Path(__file__).resolve().parent
OBJECT_SIDE = 5

DEMO_SPECS = (
    (11, 11, 2),
    (13, 15, 3),
    (16, 16, 4),
    (19, 21, 5),
    (23, 23, 6),
    (27, 29, 7),
)
QUERY_SPECS = (
    (12, 14, 3),
    (17, 19, 4),
    (25, 26, 6),
    (30, 30, 8),
)

# Four connected, chiral, square-bbox seeds.  Their rotational closure areas
# are respectively 13, 16, 17 and 20; reflection adds exactly four cells to
# each.  The distinct areas make the Step-A selector meaningful, while the
# distinct D4 masks refute fixed "fill the box" or fixed-mask shortcuts.
_CHIRAL_SEEDS = (
    (
        (0, 2), (1, 2),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
        (3, 0), (3, 2),
        (4, 2), (4, 3),
    ),
    (
        (0, 3), (1, 3),
        (2, 1), (2, 3),
        (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 0), (4, 1),
    ),
    (
        (0, 2),
        (1, 1), (1, 2), (1, 3),
        (2, 0), (2, 1), (2, 2), (2, 3),
        (3, 2), (3, 3), (3, 4),
        (4, 2),
    ),
    (
        (0, 0), (0, 1), (0, 2),
        (1, 1), (1, 2), (1, 3), (1, 4),
        (2, 0), (2, 1), (2, 3),
        (3, 1), (3, 2),
        (4, 2),
    ),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS}")
    return value


def program(settings: dict[str, Any]) -> str:
    closure = _setting(settings)
    name = "canonical.rkt" if closure == CANONICAL else "largest_closure_dihedral.rkt"
    return (HOME / name).read_text(encoding="utf-8")


def counterfactual_program() -> str:
    """Use the wrong row-major-first selector instead of Step A's largest."""
    return (HOME / "first_object_dihedral.rkt").read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be 1..30")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors")
    return height, width


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            result.append({"color": color, "cells": sorted(cells), "bbox": (r0, c0, r1, c1)})
    return result


def _rot90(cells, side: int):
    return tuple(sorted((c, side - 1 - r) for r, c in cells))


def _mirror_h(cells, side: int):
    return tuple(sorted((r, side - 1 - c) for r, c in cells))


def rotational_closure(cells, side: int) -> tuple[tuple[int, int], ...]:
    current = tuple(cells)
    result = set()
    for _ in range(4):
        result.update(current)
        current = _rot90(current, side)
    return tuple(sorted(result))


def dihedral_closure(cells, side: int) -> tuple[tuple[int, int], ...]:
    rotational = rotational_closure(cells, side)
    return tuple(sorted(set(rotational) | set(_mirror_h(rotational, side))))


def _half_turn_closure(cells, side: int):
    return tuple(sorted(set(cells) | set(_rot90(_rot90(cells, side), side))))


def _object_infos(grid: list[list[int]]) -> list[dict[str, Any]]:
    infos = []
    for obj in _components(grid):
        r0, c0, r1, c1 = obj["bbox"]
        height, width = r1 - r0 + 1, c1 - c0 + 1
        if height != width:
            raise ValueError("every object must have a square bounding box")
        normalized = tuple(sorted((r - r0, c - c0) for r, c in obj["cells"]))
        rotational = rotational_closure(normalized, height)
        infos.append({
            "object": obj,
            "side": height,
            "normalized": normalized,
            "rotational": rotational,
            "rotational_area": len(rotational),
            "original_area": len(normalized),
        })
    if not infos:
        raise ValueError("grid must contain at least one object")
    return infos


def _unique_largest_index(infos: list[dict[str, Any]]) -> int:
    largest = max(info["rotational_area"] for info in infos)
    indices = [index for index, info in enumerate(infos) if info["rotational_area"] == largest]
    if len(indices) != 1:
        raise ValueError("alternative requires a unique largest rotational closure")
    return indices[0]


def _paint_info(output: list[list[int]], info: dict[str, Any], cells) -> None:
    obj = info["object"]
    r0, c0, _r1, _c1 = obj["bbox"]
    for r, c in cells:
        output[r0 + r][c0 + c] = obj["color"]


def transform(grid: list[list[int]], closure: str) -> list[list[int]]:
    if closure not in SETTINGS:
        raise ValueError(f"unknown closure: {closure!r}")
    _validate_grid(grid)
    infos = _object_infos(grid)
    selected = _unique_largest_index(infos) if closure == ALTERNATIVE else None
    output = copy.deepcopy(grid)
    for index, info in enumerate(infos):
        completed = info["rotational"]
        if index == selected:
            completed = dihedral_closure(info["normalized"], info["side"])
        _paint_info(output, info, completed)
    return output


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    infos = _object_infos(grid)
    areas = [info["rotational_area"] for info in infos]
    largest = max(areas)
    selected = [i for i, area in enumerate(areas) if area == largest]
    return {
        "shape": [height, width],
        "component_count": len(infos),
        "colors": [info["object"]["color"] for info in infos],
        "nonzero_cells": sum(cell != 0 for row in grid for cell in row),
        "bboxes": [list(info["object"]["bbox"]) for info in infos],
        "original_areas": [info["original_area"] for info in infos],
        "rotational_closure_areas": areas,
        "selected_object_index": selected[0] if len(selected) == 1 else None,
    }


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "native-largest-closure-v2", seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _shape_variants(seed_shape) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = []
    current = tuple(seed_shape)
    for _ in range(4):
        variants.append(tuple(sorted(current)))
        variants.append(_mirror_h(current, OBJECT_SIDE))
        current = _rot90(current, OBJECT_SIDE)
    unique = tuple(dict.fromkeys(variants))
    if len(unique) != 8:
        raise RuntimeError("each chiral seed must have eight D4 variants")
    return unique


_SHAPE_FAMILIES = tuple(_shape_variants(shape) for shape in _CHIRAL_SEEDS)
_ROTATIONAL_AREAS = tuple(len(rotational_closure(shape, OBJECT_SIDE)) for shape in _CHIRAL_SEEDS)
_DIHEDRAL_AREAS = tuple(len(dihedral_closure(shape, OBJECT_SIDE)) for shape in _CHIRAL_SEEDS)
if _ROTATIONAL_AREAS != (13, 16, 17, 20) or _DIHEDRAL_AREAS != (17, 20, 21, 24):
    raise RuntimeError("selector shape-bank closure areas changed")


def _positions(height: int, width: int, count: int) -> list[tuple[int, int]]:
    bottom, right = height - OBJECT_SIDE, width - OBJECT_SIDE
    middle_r = (height - OBJECT_SIDE) // 2
    middle_c = (width - OBJECT_SIDE) // 2
    candidates = [
        (0, 0),
        (0, right),
        (bottom, 0),
        (bottom, right),
        (0, middle_c),
        (bottom, middle_c),
        (middle_r, 0),
        (middle_r, right),
        (middle_r, middle_c),
    ]
    selected = []
    for candidate in candidates:
        if all(
            abs(candidate[0] - r) >= OBJECT_SIDE + 1
            or abs(candidate[1] - c) >= OBJECT_SIDE + 1
            for r, c in selected
        ):
            selected.append(candidate)
        if len(selected) == count:
            return sorted(selected)
    raise ValueError(
        f"cannot place {count} separated {OBJECT_SIDE}x{OBJECT_SIDE} objects "
        f"in {height}x{width}"
    )


def sample_input(
    seed: int,
    index: int,
    spec: tuple[int, int, int],
) -> tuple[list[list[int]], dict[str, Any]]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    index = _exact_int(index, 0, 1000, "index")
    height, width, count = spec
    if not (11 <= height <= 30 and 11 <= width <= 30 and 2 <= count <= 8):
        raise ValueError("invalid sampler spec")
    grid = [[0] * width for _ in range(height)]
    rng = _rng(seed, index, spec)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    positions = _positions(height, width, count)

    # Family 1/2/3 is the unique closure-area winner.  Index 0 always gets a
    # lower-area family, so the row-major-first shortcut is visibly false.
    winner_family = 1 + (index % 3)
    winner_index = 1 + ((seed + index) % (count - 1))
    family_indices = []
    for object_index in range(count):
        if object_index == winner_index:
            family = winner_family
        else:
            family = (seed + index + object_index) % winner_family
        family_indices.append(family)
        variants = _SHAPE_FAMILIES[family]
        shape = variants[rng.randrange(len(variants))]
        top, left = positions[object_index]
        for dr, dc in shape:
            grid[top + dr][left + dc] = colors[object_index]

    facts = analyze(grid)
    if facts["selected_object_index"] != winner_index:
        raise RuntimeError((facts, winner_index, family_indices))
    if transform(grid, CANONICAL) == transform(grid, ALTERNATIVE):
        raise RuntimeError("constructed input does not distinguish closure settings")
    return grid, {
        "object_count": count,
        "chiral_object_count": count,
        "positions": [list(position) for position in positions],
        "family_indices": family_indices,
        "rotational_closure_areas": facts["rotational_closure_areas"],
        "winner_object_index": winner_index,
        "input_shape": [height, width],
    }


def _query_order(seed: int) -> list[int]:
    offset = (seed + 1) % len(QUERY_SPECS)
    order = list(range(len(QUERY_SPECS)))
    return order[offset:] + order[:offset]


def _rival_transform(grid: list[list[int]], mode: str) -> list[list[int]]:
    infos = _object_infos(grid)
    output = copy.deepcopy(grid)
    areas = [info["rotational_area"] for info in infos]
    originals = [info["original_area"] for info in infos]
    if mode == "smallest_closure_dihedral":
        selected = areas.index(min(areas))
    elif mode == "largest_original_area_dihedral":
        selected = originals.index(max(originals))
    elif mode == "first_object_dihedral":
        selected = 0
    else:
        selected = None

    for index, info in enumerate(infos):
        if mode == "original_only":
            completed = info["normalized"]
        elif mode == "half_turn_only":
            completed = _half_turn_closure(info["normalized"], info["side"])
        elif mode == "first_object_only":
            completed = info["rotational"] if index == 0 else info["normalized"]
        elif mode == "fill_each_bbox":
            completed = tuple(
                (r, c) for r in range(info["side"]) for c in range(info["side"])
            )
        elif mode == "all_dihedral":
            completed = dihedral_closure(info["normalized"], info["side"])
        elif mode in {
            "first_object_dihedral",
            "smallest_closure_dihedral",
            "largest_original_area_dihedral",
        }:
            completed = (
                dihedral_closure(info["normalized"], info["side"])
                if index == selected
                else info["rotational"]
            )
        else:
            raise ValueError(mode)
        _paint_info(output, info, completed)
    return output


def lesson_certificate(train: list[dict[str, Any]], chosen: str) -> dict[str, Any]:
    settings = [
        {PARAMETER: closure}
        for closure in SETTINGS
        if all(transform(pair["input"], closure) == pair["output"] for pair in train)
    ]
    rival_names = (
        "original_only",
        "half_turn_only",
        "first_object_only",
        "fill_each_bbox",
        "all_dihedral",
        "first_object_dihedral",
        "smallest_closure_dihedral",
        "largest_original_area_dihedral",
    )
    ambiguous = [
        name
        for name in rival_names
        if all(_rival_transform(pair["input"], name) == pair["output"] for pair in train)
    ]
    return {
        "chosen": {PARAMETER: chosen},
        "surviving_settings": settings,
        "ambiguous_rivals": ambiguous,
        "tested_rivals": sorted(rival_names),
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    closure = _setting(settings)
    demo_rows = [sample_input(seed, i, DEMO_SPECS[i]) for i in range(demos)]
    query_rows = [sample_input(seed, 100 + i, spec) for i, spec in enumerate(QUERY_SPECS)]
    query_rows = [query_rows[i] for i in _query_order(seed)][:queries]

    def pair(row):
        grid, _meta = row
        return {"input": copy.deepcopy(grid), "output": transform(grid, closure)}

    train = [pair(row) for row in demo_rows]
    test = [pair(row) for row in query_rows]
    certificate = lesson_certificate(train, closure)
    if certificate["surviving_settings"] != [{PARAMETER: closure}]:
        raise ValueError("visible demonstrations do not uniquely teach the selected setting")
    if certificate["ambiguous_rivals"]:
        raise ValueError(f"finite shortcut ambiguity: {certificate['ambiguous_rivals']}")
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
        "certificate": certificate,
        "sampling": {
            "demo_specs": [list(spec) for spec in DEMO_SPECS[:demos]],
            "query_order": _query_order(seed),
        },
        "status": "proposed",
        "training_admitted": False,
    }


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    index = _exact_int(index, 0, len(episode["test"]) - 1, "query index")
    return json.loads(
        public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})
    )
