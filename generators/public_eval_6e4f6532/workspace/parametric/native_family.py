"""Constructive native family for guide-directed keyed object relocation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

TASK_ID = "public_eval_6e4f6532"
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text()
PARAMETERS = {"orientation_mode": ["toward", "away"]}
DEFAULT = {"orientation_mode": "toward"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
assert CANONICAL.count("(define toward #t)") == 1
ALTERNATIVE = CANONICAL.replace("(define toward #t)", "(define toward #f)", 1)

_spec = importlib.util.spec_from_file_location("native_public_eval_6e4f6532_family", HERE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family implementation")
_family = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _family
_spec.loader.exec_module(_family)

_SIDES = ("T", "B", "L", "R")
_SIDE_VECTOR = {"T": (-1, 0), "B": (1, 0), "L": (0, -1), "R": (0, 1)}
_OPPOSITE = {"T": "B", "B": "T", "L": "R", "R": "L"}

# Relative to the first maroon cell.  String values are guide-tab side roles.
_TEMPLATES = (
    {
        **{(r, c): (9 if (r, c) == (0, 0) else 8) for r in range(-1, 2) for c in range(-1, 2)},
        (-2, 0): "T",
        (0, -2): "L",
    },
    {
        **{(r, c): (9 if (r, c) in {(0, 0), (0, 1)} else 8)
           for r in range(-1, 2) for c in range(-1, 3)},
        (2, 0): "B",
        (2, 1): "B",
        (0, 3): "R",
    },
)

# Six demonstration profiles followed by four query profiles.  The final query
# is deliberately 30x30.  The desired transform IDs cover all D4 branches.
_PROFILES = (
    (16, 18, (0, 1)),
    (17, 19, (3, 6)),
    (18, 20, (2, 5)),
    (20, 22, (7, 0)),
    (22, 24, (1, 4)),
    (24, 26, (6, 3)),
    (18, 22, (4, 7)),
    (20, 24, (5, 2)),
    (26, 28, (0, 6)),
    (30, 30, (3, 1)),
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"orientation_mode"}
        or type(settings["orientation_mode"]) is not str
        or settings["orientation_mode"] not in PARAMETERS["orientation_mode"]
    ):
        raise ValueError("settings must be exactly orientation_mode=toward or away")
    return settings["orientation_mode"]


def program(settings: object) -> str:
    return CANONICAL if _setting(settings) == "toward" else ALTERNATIVE


def _rng(seed: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _transform_point(tid: int, point: tuple[int, int]) -> tuple[int, int]:
    return _family._TRANSFORMS[tid](*point)


def _transform_side(tid: int, side: str) -> str:
    dr, dc = _transform_point(tid, _SIDE_VECTOR[side])
    if abs(dr) >= abs(dc):
        return "T" if dr < 0 else "B"
    return "L" if dc < 0 else "R"


def _stamp(grid: list[list[int]], cells: dict[tuple[int, int], int], origin: tuple[int, int]) -> None:
    for (dr, dc), value in cells.items():
        r, c = origin[0] + dr, origin[1] + dc
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            raise ValueError("constructed stamp escaped the canvas")
        if grid[r][c] != grid[2][2]:
            raise ValueError("constructed stamp collided with another non-background cell")
        grid[r][c] = value


def _guide_frame(height: int, width: int, background: int, guides: dict[str, int]) -> list[list[int]]:
    grid = [[background] * width for _ in range(height)]
    for r in (0, 1):
        grid[r] = [guides["T"]] * width
    for r in (height - 2, height - 1):
        grid[r] = [guides["B"]] * width
    for r in range(2, height - 2):
        grid[r][0] = grid[r][1] = guides["L"]
        grid[r][width - 2] = grid[r][width - 1] = guides["R"]
    return grid


def _coloured_template(template: dict[tuple[int, int], int | str], tid: int, guides: dict[str, int]) -> dict[tuple[int, int], int]:
    result: dict[tuple[int, int], int] = {}
    for point, value in template.items():
        if isinstance(value, str):
            result[point] = guides[_transform_side(tid, value)]
        else:
            result[point] = value
    return result


def _target_cells(template: dict[tuple[int, int], int | str], tid: int, top_left: tuple[int, int]) -> set[tuple[int, int]]:
    transformed = [_transform_point(tid, p) for p, value in template.items() if value == 9]
    min_r = min(r for r, _ in transformed)
    min_c = min(c for _, c in transformed)
    return {(top_left[0] + r - min_r, top_left[1] + c - min_c) for r, c in transformed}




def _palette_roles(seed: int, index: int) -> tuple[int, dict[str, int]]:
    rng = _rng(seed, f"scene:{index}")
    if index == 1:
        first_background = _rng(seed, "scene:0").sample(range(8), 5)[0]
        background = rng.choice([value for value in range(8) if value != first_background])
        guide_values = rng.sample([value for value in range(8) if value != background], 4)
    else:
        roles = rng.sample(range(8), 5)
        background, guide_values = roles[0], roles[1:]
    return background, dict(zip(_SIDES, guide_values))

def _make_scene(seed: int, index: int) -> list[list[int]]:
    height, width, tids = _PROFILES[index]
    background, guides = _palette_roles(seed, index)
    grid = _guide_frame(height, width, background, guides)

    # Four separated quadrants keep both the toward and 180-degree-opposite
    # stamps clear of every source, key, and guide even in the smallest scene.
    # Geometry still varies across profiles; palette and query order vary by seed.
    source_origins = [(5, 5), (height - 6, width - 7)]
    target_origins = [(5, width - 7), (height - 6, 5)]

    for template, tid, source, target_origin in zip(_TEMPLATES, tids, source_origins, target_origins):
        _stamp(grid, _coloured_template(template, tid, guides), source)
        for r, c in _target_cells(template, tid, target_origin):
            if grid[r][c] != background:
                raise ValueError("constructed target collided with a non-background cell")
            grid[r][c] = 9

    # The parser is the admission oracle: construction has no fallback/retry.
    for mode in PARAMETERS["orientation_mode"]:
        _family.solve_grid(grid, mode)
    return grid


def input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    grids = [_make_scene(seed, index) for index in range(len(_PROFILES))]
    demos = grids[:6]
    queries = grids[6:]
    _rng(seed, "query-order").shuffle(queries)
    return demos, queries


def generate(seed: int = 0, settings: object = None, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"orientation_mode": _rng(seed, "settings").choice(PARAMETERS["orientation_mode"])}
    mode = _setting(settings)
    train_inputs, test_inputs = input_bank(seed)

    def pairs(grids: list[list[list[int]]]) -> list[dict]:
        return [{"input": [row[:] for row in grid], "output": _family.solve_grid(grid, mode)} for grid in grids]

    return {
        "train": pairs(train_inputs[:demos]),
        "test": pairs(test_inputs[:queries]),
        "program_solution": program(settings),
    }


def _decompose(grid: list[list[int]]):
    background = _family._mode(grid)
    line_cells = _family._uniform_line_cells(grid, background)
    lines = _family._extract_lines(grid, line_cells)
    interior = {
        (r, c): value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background and (r, c) not in line_cells
    }
    objects, targets = [], []
    for component in _family._components(interior, diagonal=True):
        pixels = {p: interior[p] for p in component}
        values = set(pixels.values())
        if 8 in values:
            objects.append(pixels)
        elif values == {9}:
            targets.append(component)
    return background, line_cells, lines, objects, targets


def _toward_transform_id(obj, target, lines) -> int:
    anchors = [p for p, value in obj.items() if value == 9]
    origin = anchors[0]
    body = {p for p, value in obj.items() if value in (8, 9)}
    tab_groups = {}
    for p, value in obj.items():
        if value not in (8, 9):
            tab_groups.setdefault(value, []).append(p)
    source_sides = {color: _family._tab_side(body, points) for color, points in tab_groups.items()}
    target_sides = {
        color: _family._side_toward_nearest_line(lines, color, target, "toward")
        for color in tab_groups
    }
    for tid in range(8):
        if any(
            source_sides[color] is not None
            and target_sides[color] is not None
            and _family._transform_side(source_sides[color], tid) != target_sides[color]
            for color in tab_groups
        ):
            continue
        relative = _family._transform_pixels(obj, tid, origin)
        if _family._place_on_target(relative, target) is not None:
            return tid
    raise ValueError("scene has no toward transform")


def describe_scene(grid: list[list[int]]) -> dict:
    background, line_cells, lines, objects, targets = _decompose(grid)
    used: set[int] = set()
    transform_ids = []
    for obj in sorted(objects, key=lambda pixels: min(pixels)):
        target_index, target = _family._match_target(obj, targets, used)
        used.add(target_index)
        transform_ids.append(_toward_transform_id(obj, target, lines))
    return {
        "background": background,
        "guide_colors": sorted({grid[r][c] for r, c in line_cells}),
        "objects": [sorted(pixels) for pixels in objects],
        "targets": [sorted(target) for target in targets],
        "toward_transform_ids": transform_ids,
    }


solve = _family.solve_grid
