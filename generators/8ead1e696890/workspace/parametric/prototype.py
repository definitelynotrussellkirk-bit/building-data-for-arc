"""Border-selection and top-reference-area parametric episodes.

The canonical setting keeps all components touching an outer border.  The
alternate first measures the unique top-border reference component, then keeps
every component whose area matches that input-derived value.  Inputs are shared
across settings and demonstrations construct both directions of disagreement.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "8ead1e696890"
HOME = Path(__file__).resolve().parent
SELECTIONS = ("border", "top_area")
REFERENCE_AREAS = (1, 2, 3, 4, 5)
COLORS = tuple(range(1, 10))
DEMO_PROFILES = (
    (9, 10, 1),
    (9, 12, 2),
    (12, 10, 3),
    (16, 17, 4),
    (22, 18, 5),
    (30, 30, 4),
)
QUERY_PROFILES = (
    (8, 12, 2),
    (14, 11, 3),
    (23, 29, 5),
    (30, 30, 4),
)

# Connected shape variants, normalized to start at (0, 0).
SHAPES = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)), ((0, 0), (1, 0))),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)),
    ),
}


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"selection"}
            or type(settings["selection"]) is not str
            or settings["selection"] not in SELECTIONS):
        raise ValueError("settings must contain exactly selection=border|top_area")
    return {"selection": settings["selection"]}


def _strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a non-empty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must use rectangular exact integer colors 0..9")
    return grid


def program(settings):
    return (HOME / "rules" / f"{_settings(settings)['selection']}.rkt").read_text(
        encoding="utf-8"
    )


def components(grid):
    _strict_grid(grid)
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def touches_border(cells, height, width):
    return any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)


def top_reference_area(grid):
    top = [cells for _, cells in components(grid) if any(r == 0 for r, _ in cells)]
    if len(top) != 1:
        raise ValueError(f"input requires exactly one top-border reference component, found {len(top)}")
    return len(top[0])


def transform(grid, settings):
    selection = _settings(settings)["selection"]
    source = _strict_grid(grid)
    height, width = len(source), len(source[0])
    target_area = top_reference_area(source) if selection == "top_area" else None
    result = [[0] * width for _ in range(height)]
    for color, cells in components(source):
        keep = touches_border(cells, height, width) if selection == "border" else len(cells) == target_area
        if keep:
            for row, column in cells:
                result[row][column] = color
    return result


def kept_component_areas(grid):
    return sorted(len(cells) for _, cells in components(grid))


def _rng(seed, stream, index, attempt=0):
    payload = json.dumps([TASK_ID, seed, stream, index, attempt], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _reference_area_schedule(seed, stream, count):
    """Seed-keyed areas; profile dimensions carry no Step-A area signal."""
    result = []
    cycle_index = 0
    while len(result) < count:
        block = list(REFERENCE_AREAS)
        _rng(seed, f"{stream}:reference_area_schedule", cycle_index).shuffle(block)
        result.extend(block)
        cycle_index += 1
    return result[:count]


def _shape_bounds(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _translated(shape, row0, column0):
    return {(row0 + r, column0 + c) for r, c in shape}


def _separated(cells, occupied):
    if cells & occupied:
        return False
    return all((r + dr, c + dc) not in occupied
               for r, c in cells for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def _candidates(height, width, shape, side):
    shape_h, shape_w = _shape_bounds(shape)
    if side == "top":
        return [(0, c) for c in range(1, width - shape_w)]
    if side == "bottom":
        return [(height - shape_h, c) for c in range(1, width - shape_w)]
    if side == "left":
        return [(r, 0) for r in range(1, height - shape_h)]
    if side == "right":
        return [(r, width - shape_w) for r in range(1, height - shape_h)]
    if side == "interior":
        return [(r, c) for r in range(1, height - shape_h)
                for c in range(1, width - shape_w)]
    raise ValueError(f"unknown side: {side}")


def _region_score(side, row0, column0, shape, height, width):
    shape_h, shape_w = _shape_bounds(shape)
    center_r = row0 + (shape_h - 1) / 2
    center_c = column0 + (shape_w - 1) / 2
    if side == "top":
        return center_c
    if side == "right":
        return center_r
    if side == "bottom":
        return -center_c
    if side == "left":
        return -center_r
    return abs(center_r - height / 2) + abs(center_c - width / 2)


def _role_plan(reference_area):
    wrong_a = reference_area + 1
    wrong_b = reference_area + 2
    return (
        ("top_reference", reference_area, "top"),
        ("interior_match", reference_area, "interior"),
        ("bottom_match", reference_area, "bottom"),
        ("left_wrong", wrong_a, "left"),
        ("right_wrong", wrong_b, "right"),
        ("interior_wrong", wrong_b, "interior"),
    )


def sample_input(seed, stream, index, height, width, *, reference_area):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 1000, "index")
    _integer(height, 7, 30, "height")
    _integer(width, 7, 30, "width")
    _integer(reference_area, 1, 5, "reference_area")
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a non-empty string")
    roles = _role_plan(reference_area)
    for attempt in range(1024):
        rng = _rng(seed, stream, index, attempt)
        colors = rng.sample(COLORS, len(roles))
        occupied = set()
        placed = []
        failed = False
        for (name, area, side), color in zip(roles, colors):
            shapes = list(SHAPES[area])
            rng.shuffle(shapes)
            chosen = None
            for shape in shapes:
                candidates = _candidates(height, width, shape, side)
                rng.shuffle(candidates)
                # Border-side scores deliberately choose top-left, bottom-right,
                # left-bottom, and right-top, covering every large-grid quadrant.
                candidates.sort(key=lambda rc: _region_score(side, rc[0], rc[1], shape, height, width))
                for row0, column0 in candidates:
                    cells = _translated(shape, row0, column0)
                    if _separated(cells, occupied):
                        chosen = (cells, color, name)
                        break
                if chosen:
                    break
            if chosen is None:
                failed = True
                break
            cells, color, name = chosen
            occupied.update(cells)
            placed.append((name, color, cells))
        if failed:
            continue
        grid = [[0] * width for _ in range(height)]
        for _, color, cells in placed:
            for row, column in cells:
                grid[row][column] = color
        comps = components(grid)
        if len(comps) != len(roles) or top_reference_area(grid) != reference_area:
            continue
        if not any(len(cells) == reference_area and not touches_border(cells, height, width)
                   for _, cells in comps):
            continue
        if not any(len(cells) != reference_area and touches_border(cells, height, width)
                   for _, cells in comps):
            continue
        if transform(grid, {"selection": "border"}) == transform(grid, {"selection": "top_area"}):
            continue
        return grid
    raise ValueError("could not construct the requested top-reference-area grammar")


def retarget_reference_area(grid, new_area):
    _integer(new_area, 1, 5, "new_area")
    source = deepcopy(_strict_grid(grid))
    height, width = len(source), len(source[0])
    top = [(color, cells) for color, cells in components(source) if any(r == 0 for r, _ in cells)]
    if len(top) != 1:
        raise ValueError("retargeting requires one top reference")
    color, old_cells = top[0]
    for row, column in old_cells:
        source[row][column] = 0
    occupied = {(r, c) for r, row in enumerate(source) for c, value in enumerate(row) if value}
    for shape in SHAPES[new_area]:
        for row0, column0 in _candidates(height, width, shape, "top"):
            cells = _translated(shape, row0, column0)
            if _separated(cells, occupied):
                for row, column in cells:
                    source[row][column] = color
                if top_reference_area(source) == new_area:
                    return source
                for row, column in cells:
                    source[row][column] = 0
    raise ValueError("could not retarget the top reference without moving other components")


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    chosen = _settings(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "train": [],
        "test": [],
        "program_solution": program(chosen),
        "settings": chosen,
        "seed": seed,
    }
    seen = set()
    for split, profiles, count in (
        ("train", DEMO_PROFILES, demos),
        ("test", QUERY_PROFILES, queries),
    ):
        areas = _reference_area_schedule(seed, split, len(profiles))
        for index, (height, width, _fixture_area) in enumerate(profiles[:count]):
            grid = sample_input(
                seed, split, index, height, width, reference_area=areas[index]
            )
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("sampler produced a duplicate input")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, chosen)})
    return result


def verify_episode(episode):
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = _settings(episode.get("settings"))
    chosen = settings["selection"]
    if episode.get("program_solution") != program(settings):
        raise ValueError("program_solution differs from the selected rule")
    seen = set()
    for split, low, high in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not low <= len(pairs) <= high:
            raise ValueError(f"{split} count is outside supported limits")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("every pair needs input and output")
            _strict_grid(pair["input"])
            _strict_grid(pair["output"])
            key = json.dumps(pair["input"], separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate input")
            seen.add(key)
            if transform(pair["input"], settings) != pair["output"]:
                raise ValueError(f"{split} label differs from selected rule")
    survivors = [
        selection for selection in SELECTIONS
        if all(transform(pair["input"], {"selection": selection}) == pair["output"]
               for pair in episode["train"])
    ]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected setting: {survivors}")
    return {
        "schema": "border-top-area-self-review-v1",
        "survivors": survivors,
        "fit_uses": "demonstrations_only",
        "query_labels_checked": len(episode["test"]),
    }
