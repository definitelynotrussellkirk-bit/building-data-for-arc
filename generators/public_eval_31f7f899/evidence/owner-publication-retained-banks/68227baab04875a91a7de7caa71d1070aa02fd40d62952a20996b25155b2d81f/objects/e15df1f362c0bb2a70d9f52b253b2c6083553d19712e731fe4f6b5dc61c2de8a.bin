"""Sort solid bar heights across a common horizontal carrier line."""
from __future__ import annotations
from collections import Counter
import copy
from pathlib import Path

TASK_ID = "public_eval_31f7f899"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"height_order": ["ascending", "descending"]}
DEFAULT = {"height_order": "ascending"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
assert CANONICAL.count("(define descending #f)") == 1
ALTERNATIVE = CANONICAL.replace("(define descending #f)", "(define descending #t)", 1)


def _order(settings: dict) -> str:
    if (type(settings) is not dict or set(settings) != {"height_order"}
            or type(settings["height_order"]) is not str
            or settings["height_order"] not in PARAMETERS["height_order"]):
        raise ValueError("settings must be exactly height_order=ascending or descending")
    return settings["height_order"]


def program(settings: dict) -> str:
    return CANONICAL if _order(settings) == "ascending" else ALTERNATIVE


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)):
        raise ValueError("need an exact-integer rectangular ARC grid with axes 1..30")
    return [row[:] for row in grid]


def _unique_mode(values, label):
    counts = Counter(values)
    ranked = counts.most_common()
    if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        raise ValueError(f"need a unique {label}")
    return ranked[0][0]


def plan(grid, height_order="ascending"):
    _order({"height_order": height_order})
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    background = _unique_mode([v for row in grid for v in row], "background mode")
    axis_rows = [r for r, row in enumerate(grid) if all(v != background for v in row)]
    if len(axis_rows) != 1:
        raise ValueError("need one fully occupied horizontal carrier row")
    axis_row = axis_rows[0]
    axis_color = _unique_mode(grid[axis_row], "carrier color")
    slots = []
    c = 0
    while c < width:
        if grid[axis_row][c] == axis_color:
            c += 1
            continue
        color = grid[axis_row][c]
        start = c
        while c < width and grid[axis_row][c] == color:
            c += 1
        end = c
        top = axis_row
        while top > 0 and all(grid[top - 1][x] == color for x in range(start, end)):
            top -= 1
        bottom = axis_row
        while bottom + 1 < height and all(grid[bottom + 1][x] == color for x in range(start, end)):
            bottom += 1
        for r in range(top, bottom + 1):
            if any(grid[r][x] != color for x in range(start, end)):
                raise ValueError("bar rectangles must be solid")
        slots.append({"c0": start, "c1": end, "color": color, "top": top,
                      "bottom": bottom, "height": bottom - top + 1})
    if not 2 <= len(slots) <= 9:
        raise ValueError("need 2..9 bar slots")
    occupied = {(axis_row, c) for c in range(width)}
    for slot in slots:
        occupied.update((r, c) for r in range(slot["top"], slot["bottom"] + 1)
                        for c in range(slot["c0"], slot["c1"]))
    actual = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value != background}
    if actual != occupied:
        raise ValueError("only the carrier and its solid bars are admitted")
    measured = [slot["height"] for slot in slots]
    assigned = sorted(measured, reverse=height_order == "descending")
    for slot, new_height in zip(slots, assigned):
        top = axis_row - new_height // 2
        if top < 0 or top + new_height > height:
            raise ValueError("sorted bar height does not fit around the carrier")
    return {"grid": grid, "background": background, "axis_row": axis_row,
            "axis_color": axis_color, "slots": slots,
            "measured_heights": measured, "assigned_heights": assigned,
            "height_order": height_order}


def solve(grid, height_order="ascending"):
    state = plan(grid, height_order)
    output = [[state["background"] for _ in row] for row in state["grid"]]
    output[state["axis_row"]] = state["grid"][state["axis_row"]][:]
    for slot, new_height in zip(state["slots"], state["assigned_heights"]):
        top = state["axis_row"] - new_height // 2
        for r in range(top, top + new_height):
            for c in range(slot["c0"], slot["c1"]):
                output[r][c] = slot["color"]
    return output

_PROFILES = (
    (13, 17, 6, (1, 2, 1, 1), (11, 3, 9, 5)),
    (16, 20, 8, (2, 1, 1, 3, 1), (14, 4, 10, 2, 8)),
    (9, 13, 4, (1, 2, 1), (7, 3, 5)),
    (18, 24, 9, (1, 2, 1, 1, 2, 1), (16, 4, 14, 6, 12, 8)),
    (21, 25, 10, (2, 1, 2, 1, 1, 2, 1), (19, 3, 15, 5, 13, 7, 11)),
    (30, 30, 15, (2, 2, 2, 1, 2, 2, 1, 2), (25, 5, 21, 7, 17, 9, 13, 11)),
    (11, 15, 5, (1, 2, 1, 1), (9, 3, 7, 5)),
    (17, 22, 8, (2, 1, 2, 1, 1), (15, 3, 11, 5, 9)),
    (24, 30, 12, (1, 2, 1, 2, 1, 1, 2), (22, 4, 18, 6, 14, 8, 10)),
    (30, 30, 14, (2, 2, 2, 2, 1, 2, 2, 1, 2), (24, 4, 20, 6, 16, 8, 12, 10, 14)),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed, label):
    import hashlib
    import random
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _scene(profile_index, seed):
    height, width, axis, widths0, heights0 = _PROFILES[profile_index]
    rng = _rng(seed, f"scene:{profile_index}")
    widths = list(widths0)
    heights = list(heights0)
    if rng.randrange(2):
        heights.reverse()
    if rng.randrange(2):
        widths.reverse()
    count = len(widths)
    slack = width - sum(widths) - (count - 1)
    if slack < 0:
        raise AssertionError("profile cannot fit")
    gaps = [0] + [1] * (count - 1) + [0]
    for _ in range(slack):
        gaps[rng.randrange(count + 1)] += 1
    palette = list(range(10))
    rng.shuffle(palette)
    background, axis_color = palette[:2]
    available = palette[2:]
    colors = [available[i % len(available)] for i in range(count)]
    if count >= 4 and profile_index % 2 == 0:
        colors[2] = colors[0]
    grid = [[background] * width for _ in range(height)]
    grid[axis] = [axis_color] * width
    c = gaps[0]
    for index, (bar_width, bar_height, color) in enumerate(zip(widths, heights, colors)):
        top = axis - bar_height // 2
        for r in range(top, top + bar_height):
            for x in range(c, c + bar_width):
                grid[r][x] = color
        c += bar_width + gaps[index + 1]
    # Construction is validated by the same parser used by generation.
    plan(grid, "ascending")
    return grid


def input_bank(seed=0):
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    scenes = [_scene(index, seed) for index in range(len(_PROFILES))]
    demos = scenes[:6]
    queries = scenes[6:]
    _rng(seed, "query-order").shuffle(queries)
    return copy.deepcopy(demos), copy.deepcopy(queries)


def generate(seed=0, settings=None, demos=3, queries=4):
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, LIMITS["demos"][0], LIMITS["demos"][1], "demos")
    queries = _integer(queries, LIMITS["queries"][0], LIMITS["queries"][1], "queries")
    if settings is None:
        settings = {"height_order": _rng(seed, "setting").choice(PARAMETERS["height_order"])}
    order = _order(settings)
    demo_bank, query_bank = input_bank(seed)
    lesson = {
        "train": [{"input": grid, "output": solve(grid, order)} for grid in demo_bank[:demos]],
        "test": [{"input": grid, "output": solve(grid, order)} for grid in query_bank[:queries]],
        "program_solution": program({"height_order": order}),
    }
    return copy.deepcopy(lesson)
