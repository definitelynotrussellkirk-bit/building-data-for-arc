"""Native parametric family for clockwise/counterclockwise corner copying.

The exact canonical program is the clockwise setting.  Both settings use the
same deterministic input stream.  Demonstrations are constructive: the first
two cover all four corner classes, singleton handling, non-rectangular shapes,
multiple corner components, and a diagonal same-color decoy that distinguishes
4-connectivity from 8-connectivity.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "61c0bcd32328"
HERE = Path(__file__).resolve().parent
DIRECTIONS = ("clockwise", "counterclockwise")
DEFAULT_DIRECTION = "clockwise"
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
COUNTERCLOCKWISE = (HERE / "counterclockwise.rkt").read_text(encoding="utf-8")

PLAUSIBLE_RIVALS = (
    "identity",
    "move_instead_of_copy",
    "opposite_corner",
    "fill_bounding_box",
    "first_corner_only",
    "largest_corner_only",
    "ignore_singletons",
    "eight_connected_components",
)

# All shapes are normalized, 4-connected, and span their bounding box.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)),
)

# h, w, ((corner, shape_index), ...), clutter count, diagonal-decoy corner index,
# dense-clutter flag. Demo and query streams are intentionally independent.
_DEMO_PROFILES = (
    (12, 15, (("tl", 0), ("br", 7)), 6, None, False),
    (15, 12, (("tr", 5), ("bl", 6)), 6, 0, False),
    (16, 19, (("tl", 8), ("br", 9)), 10, None, False),
    (19, 16, (("tr", 7), ("bl", 8)), 10, None, False),
    (22, 24, (("tl", 10), ("br", 11)), 16, None, True),
    (24, 22, (("tr", 11), ("bl", 10)), 16, None, True),
)
_QUERY_PROFILES = (
    (18, 20, (("tl", 5), ("br", 6)), 12, None, False),
    (20, 18, (("tr", 8), ("bl", 9)), 12, None, False),
    (24, 27, (("tl", 7), ("br", 10)), 18, None, True),
    (30, 30, (("tl", 10), ("br", 11)), 26, None, True),
)

_CLOCKWISE_DESTINATION = {"tl": "tr", "tr": "br", "br": "bl", "bl": "tl"}
_COUNTERCLOCKWISE_DESTINATION = {"tl": "bl", "tr": "tl", "br": "tr", "bl": "br"}
_OPPOSITE_DESTINATION = {"tl": "br", "tr": "bl", "br": "tl", "bl": "tr"}

_TL_LABEL = """((and
                                                                               (zero? r1)
                                                                               (zero? c1)) 'tl)"""
_WRONG_TL_LABEL = """((and
                                                                               (zero? r1)
                                                                               (zero? c1)) 'tr)"""


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _direction(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"direction"}:
        raise ValueError("settings must contain exactly direction")
    value = settings["direction"]
    if type(value) is not str or value not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}")
    return value


def program(settings: dict[str, Any]) -> str:
    direction = _direction(settings)
    return CANONICAL if direction == "clockwise" else COUNTERCLOCKWISE


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return deepcopy(grid)


def _background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        raise ValueError("a nonzero modal background is required")
    return counts.most_common(1)[0][0]


def _neighbors(row: int, col: int, connectivity: int) -> Iterable[tuple[int, int]]:
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        yield row + dr, col + dc
    if connectivity == 8:
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            yield row + dr, col + dc


def _components(
    grid: list[list[int]], background: int, *, connectivity: int = 4
) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    result: list[dict[str, Any]] = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for candidate in _neighbors(row, col, connectivity):
                if candidate in remaining and grid[candidate[0]][candidate[1]] == color:
                    remaining.remove(candidate)
                    cells.add(candidate)
                    stack.append(candidate)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        result.append(
            {
                "color": color,
                "cells": frozenset(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            }
        )
    return result


def _corner(component: dict[str, Any], height: int, width: int) -> str | None:
    row1, col1, row2, col2 = component["bbox"]
    if row1 == 0 and col1 == 0:
        return "tl"
    if row1 == 0 and col2 == width - 1:
        return "tr"
    if row2 == height - 1 and col2 == width - 1:
        return "br"
    if row2 == height - 1 and col1 == 0:
        return "bl"
    return None


def _translation_to(
    bbox: tuple[int, int, int, int], target: str, height: int, width: int
) -> tuple[int, int]:
    row1, col1, row2, col2 = bbox
    return {
        "tl": (-row1, -col1),
        "tr": (-row1, width - 1 - col2),
        "br": (height - 1 - row2, width - 1 - col2),
        "bl": (height - 1 - row2, -col1),
    }[target]


def _translation_for_label(
    bbox: tuple[int, int, int, int], label: str, direction: str, height: int, width: int
) -> tuple[int, int]:
    """Mirror the Racket branch formulas exactly, even for a corrupted label."""
    row1, col1, row2, col2 = bbox
    if direction == "clockwise":
        return {
            "tl": (0, width - 1 - col2),
            "tr": (height - 1 - row2, 0),
            "br": (0, -col1),
            "bl": (-row1, 0),
        }[label]
    return {
        "tl": (height - 1 - row2, 0),
        "tr": (0, -col1),
        "br": (-row1, 0),
        "bl": (0, width - 1 - col2),
    }[label]


def analyze(grid: Any) -> dict[str, Any]:
    normalized = _validate_grid(grid)
    background = _background(normalized)
    components = _components(normalized, background)
    height, width = len(normalized), len(normalized[0])
    corner_parts = [
        {**part, "corner": corner}
        for part in components
        if (corner := _corner(part, height, width)) is not None
    ]
    return {
        "height": height,
        "width": width,
        "background": background,
        "background_count": sum(value == background for row in normalized for value in row),
        "foreground_count": sum(value != background for row in normalized for value in row),
        "components": components,
        "corner_parts": corner_parts,
        "corner_labels": [part["corner"] for part in corner_parts],
    }


def _solve_variant(
    grid: Any,
    direction: str,
    *,
    rival: str | None = None,
    corner_override: dict[str, str] | None = None,
) -> list[list[int]]:
    normalized = _validate_grid(grid)
    height, width = len(normalized), len(normalized[0])
    background = _background(normalized)
    connectivity = 8 if rival == "eight_connected_components" else 4
    parts = _components(normalized, background, connectivity=connectivity)
    corner_parts: list[tuple[str, dict[str, Any]]] = []
    for part in parts:
        label = _corner(part, height, width)
        if label is not None:
            if corner_override and label in corner_override:
                label = corner_override[label]
            corner_parts.append((label, part))

    if rival == "identity":
        return normalized
    if rival == "first_corner_only":
        corner_parts = corner_parts[:1]
    elif rival == "largest_corner_only" and corner_parts:
        largest = max(range(len(corner_parts)), key=lambda i: len(corner_parts[i][1]["cells"]))
        corner_parts = [corner_parts[largest]]
    elif rival == "ignore_singletons":
        corner_parts = [(corner, part) for corner, part in corner_parts if len(part["cells"]) > 1]

    output = deepcopy(normalized)
    if rival == "move_instead_of_copy":
        for _, part in corner_parts:
            for row, col in part["cells"]:
                output[row][col] = background

    destinations = (
        _CLOCKWISE_DESTINATION if direction == "clockwise" else _COUNTERCLOCKWISE_DESTINATION
    )
    for corner, part in corner_parts:
        if rival == "opposite_corner":
            delta_row, delta_col = _translation_to(
                part["bbox"], _OPPOSITE_DESTINATION[corner], height, width
            )
        else:
            delta_row, delta_col = _translation_for_label(
                part["bbox"], corner, direction, height, width
            )
        cells = part["cells"]
        if rival == "fill_bounding_box":
            row1, col1, row2, col2 = part["bbox"]
            cells = frozenset(
                (row, col)
                for row in range(row1, row2 + 1)
                for col in range(col1, col2 + 1)
            )
        for row, col in cells:
            new_row, new_col = row + delta_row, col + delta_col
            if 0 <= new_row < height and 0 <= new_col < width:
                output[new_row][new_col] = part["color"]
    return output


def solve_python(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    return _solve_variant(grid, _direction(settings))


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:corner-direction-native-v1:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _corner_anchor(corner: str, shape: tuple[tuple[int, int], ...], height: int, width: int) -> tuple[int, int]:
    shape_height, shape_width = _shape_size(shape)
    return {
        "tl": (0, 0),
        "tr": (0, width - shape_width),
        "br": (height - shape_height, width - shape_width),
        "bl": (height - shape_height, 0),
    }[corner]


def _paint(grid: list[list[int]], shape: Iterable[tuple[int, int]], row0: int, col0: int, color: int) -> None:
    for dr, dc in shape:
        grid[row0 + dr][col0 + dc] = color


def _can_paint_with_moat(
    grid: list[list[int]], cells: set[tuple[int, int]], background: int
) -> bool:
    height, width = len(grid), len(grid[0])
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    if any(grid[row][col] != background for row, col in cells):
        return False
    for row, col in cells:
        for nr, nc in _neighbors(row, col, 4):
            if (nr, nc) not in cells and 0 <= nr < height and 0 <= nc < width:
                if grid[nr][nc] != background:
                    return False
    return True


def _sample_input(seed: int, label: str, profile: tuple[Any, ...]) -> list[list[int]]:
    height, width, corner_specs, clutter_count, diagonal_index, dense = profile
    rng = _rng(seed, label)
    background = rng.choice((4, 5, 7, 8, 9))
    palette = [color for color in range(1, 10) if color != background]
    rng.shuffle(palette)
    grid = [[background for _ in range(width)] for _ in range(height)]

    corner_records: list[dict[str, Any]] = []
    for index, (corner, shape_index) in enumerate(corner_specs):
        shape = _SHAPES[shape_index]
        row0, col0 = _corner_anchor(corner, shape, height, width)
        color = palette[index]
        _paint(grid, shape, row0, col0, color)
        corner_records.append(
            {"corner": corner, "shape": shape, "row0": row0, "col0": col0, "color": color}
        )

    if diagonal_index is not None:
        record = corner_records[diagonal_index]
        if record["corner"] != "tr" or record["shape"] != _SHAPES[5]:
            raise RuntimeError("diagonal-decoy profile drifted")
        # Diagonal to the lower-right tip, but not 4-connected to the corner object.
        grid[2][width - 2] = record["color"]

    candidates = [
        (row, col)
        for row in range(3, height - 2, 3)
        for col in range(3, width - 2, 3)
    ]
    rng.shuffle(candidates)
    clutter_shapes = (3, 4, 8, 9) if dense else (0, 1, 2, 3, 4, 8, 9)
    placed = 0
    for row0, col0 in candidates:
        shape = _SHAPES[rng.choice(clutter_shapes)]
        cells = {(row0 + dr, col0 + dc) for dr, dc in shape}
        if not _can_paint_with_moat(grid, cells, background):
            continue
        color = palette[(placed + len(corner_records)) % len(palette)]
        _paint(grid, shape, row0, col0, color)
        placed += 1
        if placed == clutter_count:
            break
    if placed != clutter_count:
        raise RuntimeError(
            f"could not place {clutter_count} clutter components on {height}x{width}; placed {placed}"
        )

    info = analyze(grid)
    expected = [corner for corner, _ in corner_specs]
    if sorted(info["corner_labels"]) != sorted(expected):
        raise RuntimeError(
            f"constructed corner labels differ: expected {expected}, got {info['corner_labels']}"
        )
    clockwise = _solve_variant(grid, "clockwise")
    counterclockwise = _solve_variant(grid, "counterclockwise")
    if clockwise == counterclockwise:
        raise RuntimeError("constructed input failed to distinguish direction settings")
    return grid


def _selected_direction(episode: dict[str, Any]) -> str:
    source = episode.get("program_solution")
    matches = [direction for direction in DIRECTIONS if source == program({"direction": direction})]
    if len(matches) != 1:
        raise ValueError("episode program_solution does not identify one direction")
    return matches[0]


def teaching_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    train = episode.get("train") if isinstance(episode, dict) else None
    if not isinstance(train, list) or not train:
        raise ValueError("nonempty train demonstrations are required")
    selected = _selected_direction(episode)
    setting_survivors = [
        direction
        for direction in DIRECTIONS
        if all(_solve_variant(pair["input"], direction) == pair["output"] for pair in train)
    ]
    rival_survivors = [
        rival
        for rival in PLAUSIBLE_RIVALS
        if all(
            _solve_variant(pair["input"], selected, rival=rival) == pair["output"]
            for pair in train
        )
    ]
    return {
        "setting_survivors": setting_survivors,
        "plausible_rival_survivors": rival_survivors,
        "demonstrations_checked": len(train),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    tests = episode.get("test") if isinstance(episode, dict) else None
    if not isinstance(tests, list):
        raise ValueError("episode test split is required")
    _integer(query_index, 0, len(tests) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(tests[query_index]["input"])}],
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    direction = _direction(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")

    train = []
    for index in range(demos):
        grid = _sample_input(seed, f"demo:{index}", _DEMO_PROFILES[index])
        train.append({"input": grid, "output": _solve_variant(grid, direction)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, f"query:{index}", _QUERY_PROFILES[index])
        test.append({"input": grid, "output": _solve_variant(grid, direction)})
    episode = {
        "train": train,
        "test": test,
        "program_solution": program({"direction": direction}),
    }
    certificate = teaching_certificate(episode)
    if certificate != {
        "setting_survivors": [direction],
        "plausible_rival_survivors": [],
        "demonstrations_checked": demos,
    }:
        raise RuntimeError("demonstrations failed teaching certificate: " + json.dumps(certificate))
    serialized = [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in (train, test)
        for pair in split
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all episode inputs must be distinct")
    return episode


def wrong_intermediate_program(settings: dict[str, Any]) -> str:
    source = program(settings)
    if source.count(_TL_LABEL) != 1:
        raise ValueError("selected program no longer has one pinned TL classification")
    return source.replace(_TL_LABEL, _WRONG_TL_LABEL, 1)


def dependency_witness() -> dict[str, Any]:
    settings = {"direction": "clockwise"}
    episode = generate(0, settings, 3, 4)
    grid = deepcopy(episode["train"][0]["input"])
    info = analyze(grid)
    component = next(part for part in info["corner_parts"] if part["corner"] == "tl")
    correct = solve_python(grid, settings)
    wrong = _solve_variant(grid, "clockwise", corner_override={"tl": "tr"})
    skipped = deepcopy(grid)
    if correct == wrong or correct == skipped:
        raise RuntimeError("causal draft failed to change the final output")
    return {
        "schema": "61c0bcd32328-causal-draft-v1",
        "settings": settings,
        "step_a": "segment same-color 4-connected foreground components and classify each component from its input-derived bounding box corner",
        "intermediate": "the component record containing its cells, color, bounding box, and corner label",
        "step_b": "use that corner label plus the episode direction to choose the adjacent destination corner and translate every component cell",
        "why_b_depends_on_a": "the destination translation cannot be selected until A reveals which corner the input-specific component bounding box touches",
        "input": grid,
        "intermediate_value": {
            "corner": "tl",
            "color": component["color"],
            "bbox": list(component["bbox"]),
            "cells": [list(cell) for cell in sorted(component["cells"])],
        },
        "wrong_intermediate_value": {
            "corner": "tr",
            "color": component["color"],
            "bbox": list(component["bbox"]),
            "cells": [list(cell) for cell in sorted(component["cells"])],
        },
        "program": program(settings),
        "correct_output": correct,
        "counterfactual_program": wrong_intermediate_program(settings),
        "counterfactual_output": wrong,
        "skip_a_output": skipped,
        "ablation": "wrong_intermediate",
    }
