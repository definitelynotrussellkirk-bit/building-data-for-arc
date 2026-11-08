"""Native first-vs-last object-selection family for ARC task 07eaf5f238ad.

The input grammar is shared across settings. The top row gives a sequence of
three or four distinct colours; row 1 is blank; the body contains one or two
halo-separated monochrome components of every header colour. At least one
header colour has two components with different crops. ``first`` is the exact
canonical authority and selects the first row-major component of each colour;
``last`` selects the last. Selected crops are packed in header order with one
blank column between pieces.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import cache
import hashlib
import random
from pathlib import Path
from typing import Any, Callable

from reviewer_support import find_root, load_selected_generator

TASK_ID = "07eaf5f238ad"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)

Grid = list[list[int]]
OBJECT_CHOICES = ("first", "last")
DEFAULT_OBJECT_CHOICE = "first"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

_DEMO_PROFILES = (
    {"h": 12, "w": 12, "n_header": 3, "duplicates": (0,), "tier": 3, "first_larger": True},
    {"h": 13, "w": 17, "n_header": 4, "duplicates": (3,), "tier": 3, "first_larger": False},
    {"h": 15, "w": 19, "n_header": 3, "duplicates": (0, 2), "tier": 3, "first_larger": True},
    {"h": 18, "w": 22, "n_header": 4, "duplicates": (1, 3), "tier": 4, "first_larger": False},
    {"h": 22, "w": 25, "n_header": 3, "duplicates": (0, 1, 2), "tier": 4, "first_larger": True},
    {"h": 26, "w": 28, "n_header": 4, "duplicates": (0, 1, 2, 3), "tier": 5, "first_larger": False},
)
_QUERY_PROFILES = (
    {"h": 14, "w": 18, "n_header": 3, "duplicates": (1,), "tier": 3, "first_larger": False},
    {"h": 18, "w": 22, "n_header": 4, "duplicates": (0, 3), "tier": 4, "first_larger": True},
    {"h": 24, "w": 27, "n_header": 3, "duplicates": (0, 1, 2), "tier": 4, "first_larger": False},
    {"h": 30, "w": 30, "n_header": 4, "duplicates": (0, 1, 2, 3), "tier": 5, "first_larger": True},
)


@cache
def _generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def _validate_choice(choice: Any) -> str:
    if type(choice) is not str:
        raise TypeError("object_choice must be an exact string")
    if choice not in OBJECT_CHOICES:
        raise ValueError(f"unknown object_choice: {choice!r}")
    return choice


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(value: Any, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def canonical_program() -> str:
    source = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if not source:
        raise ValueError("canonical.rkt is empty")
    return source


def program_for(choice: str) -> str:
    choice = _validate_choice(choice)
    path = HERE / ("canonical.rkt" if choice == DEFAULT_OBJECT_CHOICE else "last.rkt")
    source = path.read_text(encoding="utf-8")
    if not source:
        raise ValueError(f"{path.name} is empty")
    return source


def _perimeter(n: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r in range(n)
        for c in range(n)
        if r in {0, n - 1} or c in {0, n - 1}
    )


def _c_shape(n: int) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(
        {(r, 0) for r in range(n)}
        | {(0, c) for c in range(n)}
        | {(n - 1, c) for c in range(n)}
    ))


def _u_shape(n: int) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(
        {(r, 0) for r in range(n)}
        | {(r, n - 1) for r in range(n)}
        | {(n - 1, c) for c in range(n)}
    ))


def _h_shape(n: int) -> tuple[tuple[int, int], ...]:
    middle = n // 2
    return tuple(sorted(
        {(r, 0) for r in range(n)}
        | {(r, n - 1) for r in range(n)}
        | {(middle, c) for c in range(n)}
    ))


def _plus_shape(n: int) -> tuple[tuple[int, int], ...]:
    middle = n // 2
    return tuple(sorted(
        {(middle, c) for c in range(n)}
        | {(r, middle) for r in range(n)}
    ))


def _shape_sets(tier: int):
    perimeter = _perimeter(tier)
    middle = tier // 2
    center_bridge = {(row, middle) for row in range(1, middle + 1)}
    filled_center = tuple(sorted(set(perimeter) | center_bridge))
    larger = (perimeter, filled_center)
    smaller = (_c_shape(tier), _u_shape(tier))
    singles = (_h_shape(tier), _plus_shape(tier), _c_shape(tier), _u_shape(tier))
    return larger, smaller, singles


def _rng(seed: int, split: str, slot: int) -> random.Random:
    material = f"{TASK_ID}|object-choice-v1|{seed}|{split}|{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _available_slots(height: int, width: int, tier: int) -> list[tuple[int, int]]:
    step = tier + 2
    rows = list(range(2, height - tier + 1, step))
    cols = list(range(0, width - tier + 1, step))
    return [(row, col) for row in rows for col in cols]


def _spread_slots(slots: list[tuple[int, int]], count: int) -> list[tuple[int, int]]:
    if len(slots) < count:
        raise RuntimeError(f"only {len(slots)} placement slots for {count} objects")
    if count == 1:
        return [slots[len(slots) // 2]]
    indices = [round(i * (len(slots) - 1) / (count - 1)) for i in range(count)]
    if len(set(indices)) != count:
        raise RuntimeError("spread slot selection produced duplicate positions")
    return [slots[index] for index in indices]


def _put_shape(grid: Grid, top: int, left: int, colour: int, shape) -> None:
    for dr, dc in shape:
        if grid[top + dr][left + dc] != 0:
            raise RuntimeError("constructive placement collision")
        grid[top + dr][left + dc] = colour


def _make_input(seed: int, split: str, slot: int, profile: dict[str, Any]) -> Grid:
    rng = _rng(seed, split, slot)
    height = profile["h"]
    width = profile["w"]
    n_header = profile["n_header"]
    duplicates = tuple(profile["duplicates"])
    tier = profile["tier"]
    first_larger = bool(profile["first_larger"])

    header = rng.sample(range(1, 10), n_header)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    header_columns = sorted(rng.sample(range(width), n_header))
    for column, colour in zip(header_columns, header):
        grid[0][column] = colour

    larger, smaller, singles = _shape_sets(tier)
    first_shapes: dict[int, tuple[tuple[int, int], ...]] = {}
    last_shapes: dict[int, tuple[tuple[int, int], ...]] = {}
    for index, colour in enumerate(header):
        if index in duplicates:
            pair_index = (rng.randrange(2) + index) % 2
            big = larger[pair_index]
            small = smaller[(pair_index + slot) % 2]
            first_shapes[colour], last_shapes[colour] = (
                (big, small) if first_larger else (small, big)
            )
        else:
            first_shapes[colour] = singles[
                (rng.randrange(len(singles)) + index) % len(singles)
            ]

    # Primary components deliberately appear in reverse header order. All
    # duplicate second components appear later, fixing row-major first/last.
    specs: list[tuple[int, tuple[tuple[int, int], ...]]] = [
        (colour, first_shapes[colour]) for colour in reversed(header)
    ]
    specs.extend((header[index], last_shapes[header[index]]) for index in duplicates)

    slots = _spread_slots(_available_slots(height, width, tier), len(specs))
    for (colour, shape), (top, left) in zip(specs, slots):
        _put_shape(grid, top, left, colour, shape)

    input_facts(grid)
    return grid


def _coerce(grid: Any) -> Grid:
    clean, errors = _generator()._coerce_grid(grid)
    if errors or clean is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    return clean


def _crops_for(clean: Grid, header: list[int], components: list[dict[str, Any]]):
    body = clean[1:]
    by_colour = {
        colour: [obj for obj in components if obj["colour"] == colour]
        for colour in header
    }
    return body, by_colour


def input_facts(grid: Grid) -> dict[str, Any]:
    clean = _coerce(grid)
    height, width = len(clean), len(clean[0])
    errors: list[str] = []
    if not 8 <= height <= 30 or not 8 <= width <= 30:
        errors.append("dimensions must both lie in 8..30")
    if height < 2 or any(clean[1]):
        errors.append("row 1 must be a blank separator")

    header = _generator()._header(clean)
    if len(header) not in {3, 4} or len(set(header)) != len(header):
        errors.append("header must contain exactly 3 or 4 distinct nonzero colours")

    body = clean[1:]
    components = _generator()._objects(body)
    object_counts = Counter(obj["colour"] for obj in components)
    header_set = set(header)
    if any(obj["colour"] not in header_set for obj in components):
        errors.append("body may not contain non-header colours")
    if any(object_counts[colour] not in {1, 2} for colour in header):
        errors.append("every header colour must have one or two body components")
    duplicate_positions = [
        index for index, colour in enumerate(header) if object_counts[colour] == 2
    ]
    if not duplicate_positions:
        errors.append("at least one header colour must have two components")
    if len(components) != len(header) + len(duplicate_positions):
        errors.append("body component count disagrees with header multiplicities")

    occupied: dict[tuple[int, int], int] = {}
    for index, obj in enumerate(components):
        size = len(obj["cells"])
        top, left, bottom, right = obj["bbox"]
        if not 2 <= size <= 25:
            errors.append(f"component {index} size must lie in 2..25")
        if bottom - top + 1 > 5 or right - left + 1 > 5:
            errors.append(f"component {index} bbox exceeds 5x5")
        for cell in obj["cells"]:
            occupied[cell] = index
    for (row, col), owner in occupied.items():
        touched = False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                other = occupied.get((row + dr, col + dc))
                if other is not None and other != owner:
                    errors.append("body component halos touch")
                    touched = True
                    break
            if touched:
                break
        if touched:
            break

    body, by_colour = _crops_for(clean, header, components)
    for index in duplicate_positions:
        colour = header[index]
        hits = by_colour[colour]
        if (
            len(hits) == 2
            and _generator()._crop(body, hits[0])
            == _generator()._crop(body, hits[1])
        ):
            errors.append(f"duplicate colour {colour} has equal first/last crops")

    body_first_colour_order: list[int] = []
    for obj in components:
        colour = obj["colour"]
        if colour not in body_first_colour_order:
            body_first_colour_order.append(colour)
    body_order_differs = body_first_colour_order != header
    if not body_order_differs:
        errors.append("first body-component colour order must differ from header order")

    if not errors:
        for choice in OBJECT_CHOICES:
            pieces = []
            for colour in header:
                hits = by_colour[colour]
                chosen = hits[0] if choice == "first" else hits[-1]
                pieces.append(_generator()._crop(body, chosen))
            output = _generator()._pack(pieces)
            if len(output) > 30 or len(output[0]) > 30:
                errors.append(f"{choice} packed output exceeds 30x30")
    if errors:
        raise ValueError("invalid object-choice input: " + "; ".join(errors))

    relation = None
    if duplicate_positions:
        hits = by_colour[header[duplicate_positions[0]]]
        first_size, last_size = len(hits[0]["cells"]), len(hits[-1]["cells"])
        relation = (
            "larger" if first_size > last_size
            else "smaller" if first_size < last_size
            else "equal"
        )

    return {
        "height": height,
        "width": width,
        "header": list(header),
        "header_count": len(header),
        "components": components,
        "component_count": len(components),
        "object_counts": {colour: object_counts[colour] for colour in header},
        "duplicate_header_positions": duplicate_positions,
        "body_first_colour_order": body_first_colour_order,
        "body_order_differs": body_order_differs,
        "first_duplicate_size_relation": relation,
    }


def selection_facts(grid: Grid, choice: str) -> list[dict[str, Any]]:
    choice = _validate_choice(choice)
    clean = _coerce(grid)
    facts = input_facts(clean)
    header = facts["header"]
    body = clean[1:]
    components = facts["components"]
    selected: list[dict[str, Any]] = []
    for colour in header:
        hits = [obj for obj in components if obj["colour"] == colour]
        rank = 0 if choice == "first" else len(hits) - 1
        obj = hits[rank]
        selected.append({
            "colour": colour,
            "component_rank": rank,
            "component_index": components.index(obj),
            "bbox": tuple(obj["bbox"]),
            "size": len(obj["cells"]),
            "crop": _generator()._crop(body, obj),
        })
    return selected


def _pack_selected(
    grid: Grid,
    selector: Callable[[list[dict[str, Any]], int, int], dict[str, Any]],
    *,
    body_order: bool = False,
) -> Grid:
    clean = _coerce(grid)
    facts = input_facts(clean)
    body = clean[1:]
    components = facts["components"]
    selected: list[tuple[int, list[list[int]]]] = []
    for header_index, colour in enumerate(facts["header"]):
        hits = [obj for obj in components if obj["colour"] == colour]
        obj = selector(hits, colour, header_index)
        selected.append((components.index(obj), _generator()._crop(body, obj)))
    if body_order:
        selected.sort(key=lambda item: item[0])
    return _generator()._pack([piece for _, piece in selected])


def apply_choice(grid: Grid, choice: str) -> Grid:
    choice = _validate_choice(choice)
    return _pack_selected(
        grid,
        lambda hits, _colour, _index: hits[0] if choice == "first" else hits[-1],
    )


def apply_size_choice(grid: Grid, mode: str) -> Grid:
    if mode not in {"largest", "smallest"}:
        raise ValueError("mode must be largest or smallest")
    if mode == "largest":
        selector = lambda hits, _colour, _index: max(
            enumerate(hits), key=lambda item: (len(item[1]["cells"]), -item[0])
        )[1]
    else:
        selector = lambda hits, _colour, _index: min(
            enumerate(hits), key=lambda item: (len(item[1]["cells"]), item[0])
        )[1]
    return _pack_selected(grid, selector)


def apply_body_order(grid: Grid, choice: str) -> Grid:
    choice = _validate_choice(choice)
    return _pack_selected(
        grid,
        lambda hits, _colour, _index: hits[0] if choice == "first" else hits[-1],
        body_order=True,
    )


def episode_inputs(seed: int, demos: int = 2, queries: int = 4) -> list[Grid]:
    seed = _validate_seed(seed)
    demos = _validate_count(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _validate_count(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    train = [
        _make_input(seed, "train", index, _DEMO_PROFILES[index])
        for index in range(demos)
    ]
    test = [
        _make_input(seed, "test", index, _QUERY_PROFILES[index])
        for index in range(queries)
    ]
    return train + test


def generate_episode(
    seed: int,
    object_choice: str,
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    choice = _validate_choice(object_choice)
    grids = episode_inputs(seed, demos=demos, queries=queries)
    train_inputs, test_inputs = grids[:demos], grids[demos:]
    return {
        "train": [
            {"input": deepcopy(grid), "output": apply_choice(grid, choice)}
            for grid in train_inputs
        ],
        "test": [
            {"input": deepcopy(grid), "output": apply_choice(grid, choice)}
            for grid in test_inputs
        ],
        "program_solution": program_for(choice),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if (
        type(episode) is not dict
        or set(episode) != {"train", "test", "program_solution"}
    ):
        raise ValueError("episode has the wrong private shape")
    tests = episode["test"]
    if not 0 <= query_index < len(tests):
        raise IndexError("query_index outside available queries")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(tests[query_index]["input"])}],
    }
