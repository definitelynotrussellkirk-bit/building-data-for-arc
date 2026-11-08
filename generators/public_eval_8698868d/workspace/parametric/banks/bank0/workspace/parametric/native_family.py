"""Match enclosed-region counts, then inset the matched pattern into each panel."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

TASK_ID = "public_eval_8698868d"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"pattern_orientation": ["as_observed", "clockwise90"]}
DEFAULT = {"pattern_orientation": "as_observed"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
TURN_BINDING = "(turn-pattern #f)"
assert CANONICAL.count(TURN_BINDING) == 1
ALTERNATIVE = CANONICAL.replace(TURN_BINDING, "(turn-pattern #t)", 1)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"pattern_orientation"}
            or type(settings["pattern_orientation"]) is not str
            or settings["pattern_orientation"] not in PARAMETERS["pattern_orientation"]):
        raise ValueError("settings must be exactly pattern_orientation=as_observed or clockwise90")
    return settings["pattern_orientation"]


def program(settings):
    return CANONICAL if _setting(settings) == "as_observed" else ALTERNATIVE


def _validate(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("need an exact-integer rectangular ARC grid with axes 1..30")
    ranking = Counter(v for row in grid for v in row).most_common()
    if len(ranking) < 2 or ranking[0][1] == ranking[1][1]:
        raise ValueError("need a unique modal background and foreground objects")
    return ranking[0][0]


def components(cells):
    remaining = set(cells)
    answer = []
    while remaining:
        first = min(remaining)
        group, pending = {first}, [first]
        remaining.remove(first)
        while pending:
            r, c = pending.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p); group.add(p); pending.append(p)
        answer.append(tuple(sorted(group)))
    return answer


def bbox(cells):
    return min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells)


def _crop(grid, box):
    r0, c0, r1, c1 = box
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def hole_count(patch, background):
    return len(components((r, c) for r, row in enumerate(patch) for c, v in enumerate(row) if v == background))


def _framed_color(patch, background):
    h, w = len(patch), len(patch[0])
    color = patch[0][0]
    if (h != w or h < 3 or color == background
            or any(v not in (background, color) for row in patch for v in row)
            or any(patch[r][c] != color for r in range(h) for c in range(w)
                   if r in (0, h - 1) or c in (0, w - 1))):
        raise ValueError("need monochrome square objects with a complete one-cell outer frame")
    return color


def plan(grid):
    background = _validate(grid)
    groups = components((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != background)
    if len(groups) < 3:
        raise ValueError("need one board and at least two detached patterns")
    boxes = [bbox(group) for group in groups]
    areas = [(b[2] - b[0] + 1) * (b[3] - b[1] + 1) for b in boxes]
    if areas.count(max(areas)) != 1:
        raise ValueError("the board must have the unique largest foreground-component bounding box")
    board_index = areas.index(max(areas))
    board_box = boxes[board_index]
    board = _crop(grid, board_box)
    patterns = {}
    side = None
    for i, box in enumerate(boxes):
        if i == board_index:
            continue
        patch = _crop(grid, box)
        color = _framed_color(patch, background)
        if side is None:
            side = len(patch)
        if len(patch) != side:
            raise ValueError("all detached patterns must have the same side length")
        count = hole_count(patch, background)
        if count in patterns:
            raise ValueError("detached patterns must have distinct enclosed-region counts")
        patterns[count] = {"pattern": patch, "pattern_color": color, "pattern_box": box}
    tile_side = side + 2
    if len(board) % tile_side or len(board[0]) % tile_side:
        raise ValueError("board dimensions must be multiples of pattern side plus two")
    matches = []
    for r in range(0, len(board), tile_side):
        for c in range(0, len(board[0]), tile_side):
            tile = _crop(board, (r, c, r + tile_side - 1, c + tile_side - 1))
            color = _framed_color(tile, background)
            count = hole_count(tile, background)
            if count not in patterns or count in {p["count"] for p in matches}:
                raise ValueError("tile counts must match patterns one-to-one")
            matches.append({"tile_origin": (r, c), "tile_color": color, "count": count, **patterns[count]})
    if len(matches) != len(patterns):
        raise ValueError("every detached pattern needs exactly one tile")
    return {"background": background, "board_box": board_box, "height": len(board), "width": len(board[0]),
            "pattern_side": side, "tile_side": tile_side, "matches": matches}


def solve(grid, pattern_orientation="as_observed"):
    _setting({"pattern_orientation": pattern_orientation})
    planned = plan(grid)
    output = [[planned["background"]] * planned["width"] for _ in range(planned["height"])]
    side = planned["tile_side"]
    for match in planned["matches"]:
        r0, c0 = match["tile_origin"]
        patch = match["pattern"]
        if pattern_orientation == "clockwise90":
            patch = [list(row) for row in zip(*patch[::-1])]
        for r in range(side):
            for c in range(side):
                color = match["tile_color"]
                if 0 < r < side - 1 and 0 < c < side - 1 and patch[r - 1][c - 1] != planned["background"]:
                    color = patch[r - 1][c - 1]
                output[r0 + r][c0 + c] = color
    return output


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


@lru_cache(maxsize=1)
def _templates():
    source = Path(__file__).with_name("scene_templates.py")
    spec = importlib.util.spec_from_file_location("pattern_scene_templates", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _augment(grid, rng):
    palette = list(range(10))
    rng.shuffle(palette)
    grid = [[palette[v] for v in row] for row in grid]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    demos, queries = _templates().input_templates()
    d, q = _rng(seed, "demonstrations"), _rng(seed, "queries")
    demos = [_augment(grid, d) for grid in demos]
    queries = [_augment(grid, q) for grid in queries]
    q.shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"pattern_orientation": _rng(seed, "settings").choice(PARAMETERS["pattern_orientation"])}
    mode = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, mode)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
