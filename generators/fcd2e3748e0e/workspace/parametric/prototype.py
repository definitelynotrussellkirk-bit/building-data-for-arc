"""Matched-input family for the order of template reflection and rotation.

The byte-identical canonical setting reflects the normalized template first and
then applies the controlled clockwise rotation.  The alternate rotates first
and reflects the resulting intermediate.  Teaching scenes use asymmetric
shapes with a real reflection and an odd quarter-turn, so the two orders are
observably noncommutative.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

TASK_ID = "fcd2e3748e0e"
PARAMETER = "transform_order"
MODES = ("reflect_then_rotate", "rotate_then_reflect")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "reflect_then_rotate": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "rotate_then_reflect": (_DIR / "rotate_then_reflect.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((12, 14), (14, 16), (17, 19), (20, 22), (24, 26), (30, 30))
_QUERY_DIMS = ((13, 15), (18, 21), (25, 28), (30, 30))
_DEMO_SIZES = (6, 7, 9, 11, 15, 20)
_QUERY_SIZES = (7, 12, 17, 22)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly transform_order")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"transform_order must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape cannot be empty")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    height = max(r for r, _ in cells) + 1
    return _normalize((c, height - 1 - r) for r, c in cells)


def _rotate_ccw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    width = max(c for _, c in cells) + 1
    return _normalize((width - 1 - c, r) for r, c in cells)


def _flip_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    width = max(c for _, c in cells) + 1
    return _normalize((r, width - 1 - c) for r, c in cells)


def _flip_ud(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    height = max(r for r, _ in cells) + 1
    return _normalize((height - 1 - r, c) for r, c in cells)


def _rotate_n(cells: Iterable[tuple[int, int]], quarters: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(quarters % 4):
        result = _rotate_cw(result)
    return result


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _asymmetric(cells: Iterable[tuple[int, int]]) -> bool:
    base = _normalize(cells)
    images = set()
    current = base
    for _ in range(4):
        images.add(current)
        current = _rotate_cw(current)
    current = _flip_lr(base)
    for _ in range(4):
        images.add(current)
        current = _rotate_cw(current)
    return len(images) == 8


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        component = {start}
        stack = [start]
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width and neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    """Parse the exact catalog rule's row-major first-match semantics.

    Historical canonical examples contain color-5 distractor objects after the
    row-major rotation control.  They are ordinary preserved input, not extra
    controls.  Strict uniqueness and footprint checks belong to the new
    parametric grammar in :func:`validate_input`, not to canonical replay.
    """
    _validate_grid(grid)
    reflect_cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value in (2, 3)]
    rotate_cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value in (4, 5, 6, 7)]
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    templates = _components(grid, 1)
    if not reflect_cells:
        raise ValueError("missing reflection control")
    if not rotate_cells:
        raise ValueError("missing rotation control")
    if not anchors:
        raise ValueError("missing anchor")
    if not templates:
        raise ValueError("missing color-1 template")
    template_abs = min(templates, key=lambda component: min(component))
    template = _normalize(template_abs)
    reflect = reflect_cells[0]
    rotate = rotate_cells[0]
    anchor = anchors[0]
    return {
        "reflect_cell": list(reflect[:2]),
        "reflect_code": reflect[2],
        "rotate_cell": list(rotate[:2]),
        "rotate_code": rotate[2],
        "rotate_quarters": rotate[2] - 4,
        "anchor": list(anchor),
        "template_cells": [list(cell) for cell in template],
    }


def _stamp(grid: list[list[int]], shape: Iterable[tuple[int, int]], anchor: tuple[int, int]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    height, width = len(out), len(out[0])
    for dr, dc in _normalize(shape):
        r, c = anchor[0] + dr, anchor[1] + dc
        if not (0 <= r < height and 0 <= c < width):
            raise ValueError("transformed stamp leaves the grid")
        out[r][c] = 8
    return out


def intermediate(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    mode = _mode(settings)
    facts = scene_facts(grid)
    base = tuple(tuple(cell) for cell in facts["template_cells"])
    reflect = facts["reflect_code"] == 3
    quarters = facts["rotate_quarters"]
    if mode == "reflect_then_rotate":
        first_operation, second_operation = "reflect", "rotate"
        first_stage = _flip_lr(base) if reflect else _normalize(base)
    else:
        first_operation, second_operation = "rotate", "reflect"
        first_stage = _rotate_n(base, quarters)
    return {
        "mode": mode,
        "first_operation": first_operation,
        "second_operation": second_operation,
        "template_cells": [list(cell) for cell in base],
        "first_stage_cells": [list(cell) for cell in first_stage],
        "reflect_code": facts["reflect_code"],
        "rotate_code": facts["rotate_code"],
        "rotate_quarters": quarters,
        "anchor": facts["anchor"],
    }


def output_from_intermediate(grid: list[list[int]], value: dict[str, Any]) -> list[list[int]]:
    _validate_grid(grid)
    if type(value) is not dict or type(value.get("first_stage_cells")) is not list:
        raise ValueError("intermediate must contain first_stage_cells")
    shape = _normalize(tuple(cell) for cell in value["first_stage_cells"])
    second = value.get("second_operation")
    if second == "rotate":
        quarters = _integer("rotate_quarters", value.get("rotate_quarters"), 0, 3)
        shape = _rotate_n(shape, quarters)
    elif second == "reflect":
        reflect_code = _integer("reflect_code", value.get("reflect_code"), 2, 3)
        if reflect_code == 3:
            shape = _flip_lr(shape)
    else:
        raise ValueError("intermediate has an invalid second_operation")
    anchor_value = value.get("anchor")
    if type(anchor_value) is not list or len(anchor_value) != 2 or any(type(x) is not int for x in anchor_value):
        raise ValueError("intermediate anchor must be a coordinate")
    return _stamp(grid, shape, (anchor_value[0], anchor_value[1]))


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    return output_from_intermediate(grid, intermediate(grid, settings))


def validate_input(grid: Any) -> list[str]:
    try:
        _validate_grid(grid)
        facts = scene_facts(grid)
        values = [value for row in grid for value in row]
        reflect_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value in (2, 3)]
        rotate_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value in (4, 5, 6, 7)]
        anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
        templates = _components(grid, 1)
        if len(reflect_cells) != 1:
            return [f"parametric grammar requires one reflection control, found {len(reflect_cells)}"]
        if len(rotate_cells) != 1:
            return [f"parametric grammar requires one rotation control, found {len(rotate_cells)}"]
        if len(anchors) != 1:
            return [f"parametric grammar requires one anchor, found {len(anchors)}"]
        if len(templates) != 1:
            return [f"parametric grammar requires one color-1 component, found {len(templates)}"]
        if 8 in values:
            return ["parametric input must not contain output color 8"]
        template = tuple(tuple(cell) for cell in facts["template_cells"])
        if not _asymmetric(template):
            return ["template must have eight distinct dihedral images"]
        if facts["reflect_code"] != 3 or facts["rotate_code"] not in (5, 7):
            return ["parametric grammar requires a real reflection and an odd quarter-turn"]
        side = max(max(r for r, _ in template) + 1, max(c for _, c in template) + 1)
        anchor_r, anchor_c = facts["anchor"]
        if anchor_r + side > len(grid) or anchor_c + side > len(grid[0]):
            return ["anchor lacks room for every transformed orientation"]
        for r in range(anchor_r, anchor_r + side):
            for c in range(anchor_c, anchor_c + side):
                if (r, c) != (anchor_r, anchor_c) and grid[r][c] != 0:
                    return ["transformed footprint overlaps an input feature"]
        if solve(grid, {PARAMETER: MODES[0]}) == solve(grid, {PARAMETER: MODES[1]}):
            return ["declared transform orders must change the output"]
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|order-v1|{seed}|{split}|{index}|{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _random_poly(rng: random.Random, size: int, maxdim: int) -> tuple[tuple[int, int], ...]:
    for _ in range(1600):
        cells = {(0, 0)}
        while len(cells) < size:
            boundary = []
            for r, c in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    candidate = (r + dr, c + dc)
                    if candidate not in cells:
                        boundary.append(candidate)
            if not boundary:
                break
            cells.add(rng.choice(boundary))
        shape = _normalize(cells)
        if (
            len(shape) == size
            and max(r for r, _ in shape) + 1 <= maxdim
            and max(c for _, c in shape) + 1 <= maxdim
            and _asymmetric(shape)
        ):
            return shape
    raise RuntimeError(f"failed to build an asymmetric {size}-cell template")


def _candidate_scene(seed: int, split: str, index: int, attempt: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    sizes = _DEMO_SIZES if split == "train" else _QUERY_SIZES
    height, width = dims[index]
    size = sizes[index]
    rng = _rng(seed, split, index, attempt)
    maxdim = min(9, height - 3, width - 3)
    template = _random_poly(rng, size, maxdim)
    template_h = max(r for r, _ in template) + 1
    template_w = max(c for _, c in template) + 1
    side = max(template_h, template_w)
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()

    placements = [
        (r, c)
        for r in range(1, height - template_h)
        for c in range(1, width - template_w)
    ]
    rng.shuffle(placements)
    template_cells = None
    for top, left in placements:
        cells = [(top + dr, left + dc) for dr, dc in template]
        halo = {
            (r + dr, c + dc)
            for r, c in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if 0 <= r + dr < height and 0 <= c + dc < width
        }
        if not (halo & occupied):
            template_cells = cells
            occupied.update(halo)
            break
    if template_cells is None:
        raise RuntimeError("failed to place parametric template")
    for r, c in template_cells:
        grid[r][c] = 1

    anchors = []
    for top in range(height - side + 1):
        for left in range(width - side + 1):
            square = {(r, c) for r in range(top, top + side) for c in range(left, left + side)}
            if not square & occupied:
                anchors.append((top, left, square))
    rng.shuffle(anchors)
    if not anchors:
        raise RuntimeError("failed to place parametric anchor footprint")
    anchor_r, anchor_c, square = anchors[0]
    grid[anchor_r][anchor_c] = 9
    occupied.update(square)

    free_cells = [(r, c) for r in range(height) for c in range(width) if (r, c) not in occupied]
    rng.shuffle(free_cells)
    if len(free_cells) < 2:
        raise RuntimeError("failed to place controls")
    rotate_code = 5 if index % 2 == 0 else 7
    reflect_cell, rotate_cell = free_cells[:2]
    grid[reflect_cell[0]][reflect_cell[1]] = 3
    grid[rotate_cell[0]][rotate_cell[1]] = rotate_code
    return grid


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    if not 0 <= index < len(dims):
        raise ValueError(f"unsupported {split} index {index}")
    for attempt in range(256):
        grid = _candidate_scene(seed, split, index, attempt)
        if validate_input(grid):
            continue
        if len(grid) == 30:
            facts = scene_facts(grid)
            if len(facts["template_cells"]) < 20:
                continue
        return grid
    raise RuntimeError(f"failed to construct a lawful distinguishing {split} scene {index}")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = _scene(seed, split, index)
            key = json.dumps(grid, separators=(",", ":")).encode()
            if key in seen:
                raise AssertionError("deterministic schedule emitted a duplicate input")
            seen.add(key)
            target.append({"input": grid, "output": solve(grid, {PARAMETER: mode})})
    return {"train": train, "test": test, "program_solution": program({PARAMETER: mode})}


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def _solve_shape(grid: list[list[int]], transform: Callable[[tuple[tuple[int, int], ...], dict[str, Any]], tuple[tuple[int, int], ...]]) -> list[list[int]]:
    facts = scene_facts(grid)
    base = tuple(tuple(cell) for cell in facts["template_cells"])
    shape = transform(base, facts)
    return _stamp(grid, shape, tuple(facts["anchor"]))


def _rotate_only(grid):
    return _solve_shape(grid, lambda base, facts: _rotate_n(base, facts["rotate_quarters"]))


def _reflect_only(grid):
    return _solve_shape(grid, lambda base, facts: _flip_lr(base) if facts["reflect_code"] == 3 else base)


def _identity(grid):
    return _solve_shape(grid, lambda base, facts: base)


def _reflect_then_ccw(grid):
    def transform(base, facts):
        shape = _flip_lr(base) if facts["reflect_code"] == 3 else base
        for _ in range(facts["rotate_quarters"]):
            shape = _rotate_ccw(shape)
        return shape
    return _solve_shape(grid, transform)


def _flip_ud_then_rotate(grid):
    return _solve_shape(grid, lambda base, facts: _rotate_n(_flip_ud(base), facts["rotate_quarters"]))


def _erase_input(grid):
    out = [[0] * len(grid[0]) for _ in grid]
    facts = scene_facts(grid)
    return _stamp(out, facts["template_cells"], tuple(facts["anchor"]))


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    MODES[0]: lambda grid: solve(grid, {PARAMETER: MODES[0]}),
    MODES[1]: lambda grid: solve(grid, {PARAMETER: MODES[1]}),
    "rotate_only": _rotate_only,
    "reflect_only": _reflect_only,
    "identity": _identity,
    "reflect_then_counterclockwise": _reflect_then_ccw,
    "flip_ud_then_rotate": _flip_ud_then_rotate,
    "erase_input": _erase_input,
}


def audit_episode(seed: int, mode: str, *, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    survivors = []
    harmful = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER: mode},
        "fit_uses": "demonstrations_only",
        "rivals": sorted(RIVALS),
        "survivors": survivors,
        "harmful_survivors": harmful,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
        "intermediate": intermediate(episode["test"][0]["input"], {PARAMETER: mode}),
    }
