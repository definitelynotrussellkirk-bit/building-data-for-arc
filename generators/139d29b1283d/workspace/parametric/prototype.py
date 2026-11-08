"""Matched native family for canonical stamp intersection and overlap-size relay.

The production generator is unchanged.  The alternative first computes the
canonical visible intersection, uses its input-dependent cell count as a relay,
and then adds the unique color-4 payload component with that size.  Python
outputs are deterministic claims; native qualification re-executes every label
through protected Racket.
"""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "139d29b1283d"
VERSION = "overlap-size-relay-v1"
FINISHES = ("intersection_only", "overlap_size_payload")
DEFAULT_SETTINGS = {"finish": "intersection_only"}
DEMO_DIMS = ((12, 14), (13, 16), (16, 18), (18, 20), (22, 24), (26, 27))
QUERY_DIMS = ((15, 17), (20, 21), (27, 28), (30, 30))

_TEMPLATES = (
    ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2)),
    ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 0), (2, 2), (2, 3), (3, 2)),
)
_OFFSETS = ((0, 1), (1, 0), (1, 1), (-1, 1), (2, 0), (0, 2))
_STEPS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _finish(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return value


def _validate_grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or len(grid) > 30 or len(grid[0]) > 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return grid


def _components(grid: list[list[int]], color: int) -> list[tuple[tuple[int, int], ...]]:
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    groups: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            point = queue.popleft()
            cells.append(point)
            r, c = point
            for dr, dc in _STEPS:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        groups.append(tuple(sorted(cells)))
    return sorted(groups, key=lambda cells: (min(cells), len(cells), cells))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shift(cells: Iterable[tuple[int, int]], anchor: tuple[int, int]) -> set[tuple[int, int]]:
    return {(r + anchor[0], c + anchor[1]) for r, c in cells}


def _bbox_area(cells: set[tuple[int, int]]) -> int:
    return ((max(r for r, _ in cells) - min(r for r, _ in cells) + 1)
            * (max(c for _, c in cells) - min(c for _, c in cells) + 1))


def _visible(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    return {(r, c) for r, c in cells if 0 <= r < h and 0 <= c < w}


def _anchors(grid: list[list[int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    result = []
    for color in (1, 2):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) != 1:
            raise ValueError(f"expected exactly one color-{color} anchor")
        result.append(cells[0])
    return result[0], result[1]


def _largest_green(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    groups = _components(grid, 3)
    if not groups:
        raise ValueError("missing color-3 template")
    ordered = sorted(groups, key=lambda cells: (-len(cells), min(cells), cells))
    if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
        raise ValueError("largest green template must be unique")
    return ordered[0]


def _scene(grid: list[list[int]], *, first_component: bool = False,
           first_cell_origin: bool = False) -> dict:
    groups = _components(grid, 3)
    component = groups[0] if first_component else _largest_green(grid)
    if first_cell_origin:
        origin = min(component)
        shape = tuple(sorted((r - origin[0], c - origin[1]) for r, c in component))
    else:
        shape = _normalize(component)
    a1, a2 = _anchors(grid)
    stamp1, stamp2 = _shift(shape, a1), _shift(shape, a2)
    overlap = _visible(grid, stamp1 & stamp2)
    return {
        "component": component,
        "shape": shape,
        "anchors": (a1, a2),
        "stamp1": stamp1,
        "stamp2": stamp2,
        "overlap": overlap,
    }


def overlap_intermediate(grid: list[list[int]]) -> dict:
    scene = _scene(grid)
    payloads = _components(grid, 4)
    selected = [cells for cells in payloads if len(cells) == len(scene["overlap"])]
    if len(selected) != 1:
        raise ValueError("expected one payload matching visible overlap size")
    return {
        "visible_overlap": tuple(sorted(scene["overlap"])),
        "visible_overlap_count": len(scene["overlap"]),
        "selected_payload": selected[0],
    }


def _blank_like(grid: list[list[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in grid]


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int = 8) -> list[list[int]]:
    output = [row[:] for row in grid]
    for r, c in cells:
        if 0 <= r < len(output) and 0 <= c < len(output[0]):
            output[r][c] = color
    return output


def transform(grid: list[list[int]], settings: dict) -> list[list[int]]:
    finish = _finish(settings)
    scene = _scene(_validate_grid(grid))
    output = _paint(_blank_like(grid), scene["overlap"])
    if finish == "overlap_size_payload":
        output = _paint(output, overlap_intermediate(grid)["selected_payload"])
    return output


def counterfactual_transform(grid: list[list[int]]) -> list[list[int]]:
    scene = _scene(_validate_grid(grid))
    payloads = _components(grid, 4)
    selected = [cells for cells in payloads if len(cells) == len(scene["shape"])]
    if len(selected) != 1:
        raise ValueError("expected one payload matching template size")
    return _paint(_paint(_blank_like(grid), scene["overlap"]), selected[0])


def program(settings: dict) -> str:
    finish = _finish(settings)
    filename = "canonical.rkt" if finish == "intersection_only" else "relay.rkt"
    return Path(__file__).with_name(filename).read_bytes().decode("utf-8")


def counterfactual_program() -> str:
    return Path(__file__).with_name("counterfactual-template-size.rkt").read_bytes().decode("utf-8")


def _compact_path(size: int, variant: int = 0) -> tuple[tuple[int, int], ...]:
    _integer(size, 1, 12, "component size")
    width = 3 + (variant % 2)
    path: list[tuple[int, int]] = []
    row = 0
    while len(path) < size:
        columns = range(width) if row % 2 == 0 else range(width - 1, -1, -1)
        for column in columns:
            path.append((row, column))
            if len(path) == size:
                return tuple(path)
        row += 1
    raise AssertionError("unreachable")


def _place(grid: list[list[int]], shape: Iterable[tuple[int, int]], origin: tuple[int, int],
           color: int) -> tuple[tuple[int, int], ...]:
    cells = tuple((origin[0] + r, origin[1] + c) for r, c in shape)
    if any(not (0 <= r < len(grid) and 0 <= c < len(grid[0])) for r, c in cells):
        raise RuntimeError("constructed shape escaped grid")
    if any(grid[r][c] != 0 for r, c in cells):
        raise RuntimeError("constructed shapes overlapped")
    for r, c in cells:
        grid[r][c] = color
    return tuple(sorted(cells))


def _valid_offsets(shape: tuple[tuple[int, int], ...]) -> list[tuple[int, int]]:
    first = set(shape)
    result = []
    for offset in _OFFSETS:
        second = _shift(shape, offset)
        overlap = first & second
        if 2 <= len(overlap) < len(shape) and _bbox_area(overlap) > len(overlap):
            result.append(offset)
    if not result:
        raise RuntimeError("template has no nonrectangular overlap offset")
    return result


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    dims = DEMO_DIMS if split == "train" else QUERY_DIMS
    h, w = dims[index]
    rng = _rng(seed, split, index)
    grid = [[0] * w for _ in range(h)]

    template = _TEMPLATES[rng.randrange(len(_TEMPLATES))]
    offset = rng.choice(_valid_offsets(template))
    template_size = len(template)
    overlap_size = len(set(template) & _shift(template, offset))

    # An earlier smaller green object makes largest-component selection necessary.
    early = _compact_path(template_size - 2, variant=index)
    _place(grid, early, (0, 0), 3)
    template_left = 5 if w >= 16 else 4
    _place(grid, template, (1, template_left), 3)
    late = _compact_path(max(3, template_size - 3), variant=index + 1)
    late_width = max(c for _, c in late) + 1
    _place(grid, late, (0, w - late_width), 3)

    a1 = (h // 2, max(template_left + 1, w // 2 - 2))
    a2 = (a1[0] + offset[0], a1[1] + offset[1])
    if any(not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0 for r, c in (a1, a2)):
        raise RuntimeError("anchor construction collided")
    grid[a1[0]][a1[1]] = 1
    grid[a2[0]][a2[1]] = 2

    decoy_size = next(size for size in (7, 6, 5, 4, 3, 2)
                      if size not in {template_size, overlap_size})
    payload_sizes = (template_size, overlap_size, decoy_size)
    origins = (0, max(5, w // 2 - 2), w - 4)
    for payload_index, (size, left) in enumerate(zip(payload_sizes, origins)):
        shape = _compact_path(size, variant=payload_index + index)
        height = max(r for r, _ in shape) + 1
        width = max(c for _, c in shape) + 1
        left = min(left, w - width)
        _place(grid, shape, (h - height, left), 4)

    # Substantive boundary-spanning stress without changing either rule.
    if (h, w) == (30, 30):
        for r in range(9, 17):
            if grid[r][0] == 0:
                grid[r][0] = 5
            if grid[r][w - 1] == 0:
                grid[r][w - 1] = 6
        for c in range(10, 20):
            if grid[0][c] == 0:
                grid[0][c] = 7
    return grid


def analyze(grid: list[list[int]]) -> dict:
    errors: list[str] = []
    try:
        _validate_grid(grid)
        greens = _components(grid, 3)
        if len(greens) < 2:
            errors.append("need at least two green components")
        largest = _largest_green(grid)
        scene = _scene(grid)
        payloads = _components(grid, 4)
        sizes = [len(cells) for cells in payloads]
        if not 2 <= len(scene["overlap"]) < len(scene["shape"]):
            errors.append("visible overlap must be a proper multi-cell subset")
        if sizes.count(len(scene["overlap"])) != 1:
            errors.append("need one overlap-size payload")
        if sizes.count(len(scene["shape"])) != 1:
            errors.append("need one template-size payload")
        if greens and greens[0] == largest:
            errors.append("first green component must be a smaller distractor")
        if (min(r for r, _ in largest), min(c for _, c in largest)) in largest:
            errors.append("largest template bbox corner must be empty")
    except (ValueError, RuntimeError) as exc:
        errors.append(str(exc))
        largest, scene, sizes = (), {"shape": (), "overlap": ()}, []
    h, w = (len(grid), len(grid[0])) if isinstance(grid, list) and grid and isinstance(grid[0], list) else (0, 0)
    sides = set()
    if h and w:
        points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        if any(r == 0 for r, _ in points): sides.add("top")
        if any(r == h - 1 for r, _ in points): sides.add("bottom")
        if any(c == 0 for _, c in points): sides.add("left")
        if any(c == w - 1 for _, c in points): sides.add("right")
    return {
        "errors": errors,
        "template_size": len(scene["shape"]),
        "visible_overlap_count": len(scene["overlap"]),
        "payload_sizes": sizes,
        "nonzero_count": sum(value != 0 for row in grid for value in row) if h and w else 0,
        "boundary_sides": sorted(sides),
    }


def _wrong_first_origin(grid: list[list[int]]) -> list[list[int]]:
    return _paint(_blank_like(grid), _scene(grid, first_cell_origin=True)["overlap"])


def _wrong_first_component(grid: list[list[int]]) -> list[list[int]]:
    return _paint(_blank_like(grid), _scene(grid, first_component=True)["overlap"])


def _wrong_bbox_fill(grid: list[list[int]]) -> list[list[int]]:
    overlap = _scene(grid)["overlap"]
    box = {(r, c) for r in range(min(r for r, _ in overlap), max(r for r, _ in overlap) + 1)
           for c in range(min(c for _, c in overlap), max(c for _, c in overlap) + 1)}
    return _paint(_blank_like(grid), box)


def _wrong_union(grid: list[list[int]]) -> list[list[int]]:
    scene = _scene(grid)
    return _paint(_blank_like(grid), _visible(grid, scene["stamp1"] | scene["stamp2"]))


def _wrong_first_payload(grid: list[list[int]]) -> list[list[int]]:
    scene = _scene(grid)
    return _paint(_paint(_blank_like(grid), scene["overlap"]), _components(grid, 4)[0])


SHORTCUTS = {
    "first_occupied_template_cell_origin": _wrong_first_origin,
    "first_color3_component": _wrong_first_component,
    "fill_overlap_bbox": _wrong_bbox_fill,
    "union_instead_of_intersection": _wrong_union,
    "first_payload_component": _wrong_first_payload,
    "template_size_instead_of_overlap_size": counterfactual_transform,
}


def lesson_certificate(demos: list[dict], settings: dict) -> dict:
    finish = _finish(settings)
    expected = [pair["output"] for pair in demos]
    survivors = []
    for candidate in FINISHES:
        if all(transform(pair["input"], {"finish": candidate}) == output
               for pair, output in zip(demos, expected)):
            survivors.append({"finish": candidate})
    surviving_shortcuts = [name for name, rival in SHORTCUTS.items()
                           if all(rival(pair["input"]) == output
                                  for pair, output in zip(demos, expected))]
    return {
        "selected": {"finish": finish},
        "surviving_settings": survivors,
        "surviving_shortcuts": surviving_shortcuts,
        "query_outputs_consulted": False,
    }


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    finish = _finish(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = [_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_input(seed, "test", index) for index in range(queries)]
    chosen = {"finish": finish}
    return {
        "train": [{"input": grid, "output": transform(grid, chosen)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, chosen)} for grid in test_inputs],
        "program_solution": program(chosen),
    }
