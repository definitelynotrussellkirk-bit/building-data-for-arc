"""Native selector-row rotational-equivalence family for 95be702ec4db."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "95be702ec4db"
MATRIX_VIEWS = ("full_matrix", "selector_row")
DEFAULT_VIEW = "full_matrix"
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8").rstrip("\n")
SELECTOR_ROW_PROGRAM = Path(__file__).with_name("selector_row.rkt").read_text(encoding="utf-8").rstrip("\n")
WRONG_SELECTOR_PROGRAM = Path(__file__).with_name("wrong_selector.rkt").read_text(encoding="utf-8").rstrip("\n")
_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))

_BASE_SHAPES = (
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 1), (0, 2), (1, 0), (1, 1)}),
    frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
)
_DEMO_SPECS = (
    (9, 18, (0, 0, 1), 1, False),
    (11, 24, (0, 1, 1, 2), 3, False),
    (13, 30, (0, 1, 2, 0, 3), 4, False),
    (10, 18, (0, 1, 0), 2, False),
    (12, 24, (0, 0, 1, 1), 4, False),
    (14, 30, (0, 1, 2, 2, 0), 3, False),
)
_QUERY_SPECS = (
    (10, 24, (0, 1, 0, 2), 3, False),
    (15, 30, (0, 1, 1, 2, 3), 2, False),
    (9, 18, (0, 1, 1), 1, False),
    (30, 30, (0, 1, 2, 0, 2), 5, True),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"matrix_view"}:
        raise ValueError("settings must contain exactly matrix_view")
    value = settings["matrix_view"]
    if type(value) is not str or value not in MATRIX_VIEWS:
        raise ValueError(f"matrix_view must be one of {MATRIX_VIEWS}")
    return {"matrix_view": value}


def rule_text(matrix_view: str) -> str:
    if matrix_view == "full_matrix":
        return CANONICAL_PROGRAM
    if matrix_view == "selector_row":
        return SELECTOR_ROW_PROGRAM
    raise ValueError(f"unknown matrix_view {matrix_view!r}")


def counterfactual_program() -> str:
    return WRONG_SELECTOR_PROGRAM


def _mix(*parts: object) -> int:
    text = ":".join(map(str, (TASK_ID, "selector-row-v1", *parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def _normalize(cells):
    cells = set(cells)
    if not cells:
        return frozenset()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _rotate(cells):
    cells = _normalize(cells)
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def _rotations(cells):
    result = []
    current = _normalize(cells)
    for _ in range(4):
        if current not in result:
            result.append(current)
        current = _rotate(current)
    return tuple(result)


_FAMILIES = tuple(_rotations(shape) for shape in _BASE_SHAPES)


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def _draw_frame(grid, top, left):
    for c in range(left, left + 5):
        grid[top][c] = 9
        grid[top + 4][c] = 9
    for r in range(top, top + 5):
        grid[r][left] = 9
        grid[r][left + 4] = 9


def _frame_positions(height: int, width: int, count: int, stress: bool, seed: int, split: str, index: int):
    if stress:
        if (height, width, count) != (30, 30, 5):
            raise ValueError("stress gallery must be 30x30 with five frames")
        return [(1 + 6 * i, 6 * i) for i in range(5)]
    columns = [1 + 6 * i for i in range(count)]
    if columns[-1] + 4 >= width:
        raise ValueError("gallery width is too small")
    max_top = height - 5
    return [
        (1 + _mix(seed, split, index, frame, "row") % max_top, column)
        for frame, column in enumerate(columns)
    ]


def _build_input(seed: int, split: str, index: int, spec):
    height, width, labels, selector, stress = spec
    count = len(labels)
    if not 1 <= selector <= count:
        raise ValueError("selector must address a frame")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    rng = random.Random(_mix(seed, split, index, "palette"))
    marker_column = rng.randrange(width)
    grid[0][marker_column] = selector
    positions = _frame_positions(height, width, count, stress, seed, split, index)
    colors = rng.sample(range(1, 9), count)
    for frame_index, ((top, left), label, color) in enumerate(zip(positions, labels, colors)):
        _draw_frame(grid, top, left)
        variants = _FAMILIES[label]
        shape = variants[_mix(seed, split, index, frame_index, "rotation") % len(variants)]
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        row_offset = _mix(seed, split, index, frame_index, "row-offset") % (4 - shape_h)
        col_offset = _mix(seed, split, index, frame_index, "col-offset") % (4 - shape_w)
        for r, c in shape:
            grid[top + 1 + row_offset + r][left + 1 + col_offset + c] = color
    facts = analyze(grid)
    observed = []
    for row in facts["matrix"]:
        observed.append(tuple(i for i, value in enumerate(row) if value == 8))
    expected = [tuple(i for i, other in enumerate(labels) if other == label) for label in labels]
    if observed != expected:
        raise ValueError(f"equivalence drift: {observed} != {expected}")
    return grid


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    frame_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9}
    frames = []
    for component in _components(frame_cells):
        r1 = min(r for r, _ in component)
        c1 = min(c for _, c in component)
        r2 = max(r for r, _ in component)
        c2 = max(c for _, c in component)
        shape = {(r - r1 - 1, c - c1 - 1) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2) if grid[r][c] not in (0, 9)}
        if not shape:
            raise ValueError("frame has no shape")
        frames.append({"bbox": (r1, c1, r2, c2), "shape": _normalize(shape)})
    frames.sort(key=lambda frame: (frame["bbox"][1], frame["bbox"][0]))
    count = len(frames)
    markers = [value for value in grid[0] if value != 0]
    if len(markers) != 1 or not 1 <= markers[0] <= count:
        raise ValueError("top row must contain exactly one selector in 1..frame-count")
    matrix = [
        [8 if right["shape"] in _rotations(left["shape"]) else 0 for right in frames]
        for left in frames
    ]
    return {"frames": frames, "selector_index": markers[0] - 1, "matrix": matrix}


def apply_view(grid: list[list[int]], matrix_view: str) -> list[list[int]]:
    facts = analyze(grid)
    if matrix_view == "full_matrix":
        return deepcopy(facts["matrix"])
    if matrix_view == "selector_row":
        return [facts["matrix"][facts["selector_index"]][:]]
    raise ValueError(f"unknown matrix_view {matrix_view!r}")


def apply_wrong_selector(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze(grid)
    wrong = (facts["selector_index"] + 1) % len(facts["matrix"])
    return [facts["matrix"][wrong][:]]


def _pair(seed: int, split: str, index: int, spec, matrix_view: str):
    grid = _build_input(seed, split, index, spec)
    return {"input": grid, "output": apply_view(grid, matrix_view)}


def generate_episode(seed: int, *, matrix_view: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1 (not bool)")
    if matrix_view not in MATRIX_VIEWS:
        raise ValueError(f"unknown matrix_view {matrix_view!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [_pair(seed, "train", i, _DEMO_SPECS[i], matrix_view) for i in range(demos)]
    test = [_pair(seed, "test", i, _QUERY_SPECS[i], matrix_view) for i in range(queries)]
    return {"train": train, "test": test, "program_solution": rule_text(matrix_view)}


def public_turn(episode: dict[str, Any], query_index: int = 0):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select a retained query")
    return {
        "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return (json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")) + "\n").encode()


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0):
    episode = generate_episode(seed, matrix_view="selector_row", demos=6, queries=4)
    pair = next(pair for pair in episode["train"] + episode["test"] if apply_wrong_selector(pair["input"]) != pair["output"])
    facts = analyze(pair["input"])
    wrong = (facts["selector_index"] + 1) % len(facts["matrix"])
    return {
        "settings": {"matrix_view": "selector_row"},
        "program": SELECTOR_ROW_PROGRAM,
        "input": deepcopy(pair["input"]),
        "output": deepcopy(pair["output"]),
        "intermediate_value": {
            "equivalence_matrix": facts["matrix"],
            "selector_index": facts["selector_index"],
            "wrong_next_index": wrong,
        },
        "counterfactual_program": WRONG_SELECTOR_PROGRAM,
        "counterfactual_output": apply_wrong_selector(pair["input"]),
        "ablation": "wrong_intermediate",
    }
