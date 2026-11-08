"""Native parametric family for 600284beb8e4.

All settings share identical inputs.  The canonical default fills the complete
intersection of the color-2 and color-3 bounding rectangles.  Alternative
settings first infer which side of that intersection is indicated by the unique
color-1 cue, then paint either the cue-near or cue-far overlap edge.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random

EDGE_POLICIES = ("full", "near_cue", "far_cue")
CUE_SIDES = ("north", "east", "south", "west")
SCENE_PROFILES = (
    "2_north",
    "2_south",
    "2_west",
    "2_east",
    "2_horizontal",
    "2_vertical",
)
_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "full": "canonical.rkt",
    "near_cue": "near_cue.rkt",
    "far_cue": "far_cue.rkt",
}
_DEMO_SIZES = ((9, 11), (10, 12), (12, 14), (13, 15), (15, 17), (16, 18))
_QUERY_SIZES = ((8, 10), (12, 15), (18, 20), (30, 30))


def _settings(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"edge_policy"}:
        raise ValueError("settings must contain exactly edge_policy")
    value = settings["edge_policy"]
    if type(value) is not str or value not in EDGE_POLICIES:
        raise ValueError(f"edge_policy must be one of {EDGE_POLICIES}")
    return value


def _integer(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def program(settings):
    policy = _settings(settings)
    return (_HOME / _PROGRAM_FILES[policy]).read_text(encoding="utf-8")


def _empty(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _draw_border(grid, box, color: int) -> None:
    top, left, bottom, right = box
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color


def _bbox(grid, color: int) -> tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        raise ValueError(f"scene is missing color {color}")
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def _overlap(grid) -> tuple[int, int, int, int]:
    b2, b3 = _bbox(grid, 2), _bbox(grid, 3)
    box = max(b2[0], b3[0]), max(b2[1], b3[1]), min(b2[2], b3[2]), min(b2[3], b3[3])
    if box[0] > box[2] or box[1] > box[3]:
        raise ValueError("rectangle bboxes do not overlap")
    return box


def _seeded(seed: int, lane: str, index: int) -> random.Random:
    return random.Random(f"600284beb8e4:{seed}:{lane}:{index}:v2")


def _side_orders(seed: int) -> tuple[list[str], list[str]]:
    rng = _seeded(seed, "side-order", 0)
    base = list(CUE_SIDES)
    rng.shuffle(base)
    demos = [*base, base[1], base[3]]
    queries = [base[2], base[0], base[3], base[1]]
    return demos, queries


def _profile_orders(seed: int) -> tuple[list[str], list[str]]:
    rng = _seeded(seed, "profile-order", 0)
    base = list(SCENE_PROFILES)
    rng.shuffle(base)
    queries = [base[3], base[0], base[4], base[1]]
    return base, queries


def _central_overlap(h: int, w: int, rng: random.Random) -> tuple[int, int, int, int]:
    oh = max(3, min(h // 3, h - 4))
    ow = max(3, min(w // 3, w - 4))
    top = (h - oh) // 2 + rng.choice((-1, 0, 1))
    left = (w - ow) // 2 + rng.choice((-1, 0, 1))
    top = min(max(2, top), h - oh - 2)
    left = min(max(2, left), w - ow - 2)
    return top, left, top + oh - 1, left + ow - 1


def _rectangles(h: int, w: int, profile: str, boundary: bool, rng: random.Random):
    r0, c0, r1, c1 = _central_overlap(h, w, rng)
    inner_top = max(1, r0 - max(2, h // 4))
    inner_bottom = min(h - 2, r1 + max(2, h // 4))
    inner_left = max(1, c0 - max(2, w // 4))
    inner_right = min(w - 2, c1 + max(2, w // 4))

    north_top = 0 if boundary else inner_top
    south_bottom = h - 1 if boundary else inner_bottom
    west_left = 0 if boundary else inner_left
    east_right = w - 1 if boundary else inner_right

    north = (north_top, inner_left, r1, inner_right)
    south = (r0, inner_left, south_bottom, inner_right)
    west = (inner_top, west_left, inner_bottom, c1)
    east = (inner_top, c0, inner_bottom, east_right)
    horizontal = (r0, west_left, r1, east_right)
    vertical = (north_top, c0, south_bottom, c1)

    if profile == "2_north":
        return north, south
    if profile == "2_south":
        return south, north
    if profile == "2_west":
        return west, east
    if profile == "2_east":
        return east, west
    if profile == "2_horizontal":
        return horizontal, vertical
    if profile == "2_vertical":
        return vertical, horizontal
    raise ValueError(profile)


def _place_cue(grid, side: str, rng: random.Random) -> tuple[int, int]:
    r0, c0, r1, c1 = _overlap(grid)
    if side == "north":
        candidates = [(r, c) for r in range(0, r0) for c in range(c0, c1 + 1)]
    elif side == "south":
        candidates = [(r, c) for r in range(r1 + 1, len(grid)) for c in range(c0, c1 + 1)]
    elif side == "west":
        candidates = [(r, c) for r in range(r0, r1 + 1) for c in range(0, c0)]
    elif side == "east":
        candidates = [(r, c) for r in range(r0, r1 + 1) for c in range(c1 + 1, len(grid[0]))]
    else:
        raise ValueError(side)
    candidates = [(r, c) for r, c in candidates if grid[r][c] == 0]
    if not candidates:
        raise ValueError(f"no lawful cue cell for {side}")
    # Prefer a cell away from the canvas edge when possible, while preserving
    # deterministic variety across seeds.
    interior = [(r, c) for r, c in candidates if 0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1]
    chosen = rng.choice(interior or candidates)
    grid[chosen[0]][chosen[1]] = 1
    return chosen


def _add_distractors(grid, rng: random.Random, count: int) -> None:
    h, w = len(grid), len(grid[0])
    candidates = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    rng.shuffle(candidates)
    for index, (r, c) in enumerate(candidates[:count]):
        grid[r][c] = 4 if index % 2 == 0 else 6


def _scene(seed: int, index: int, *, query: bool) -> list[list[int]]:
    sizes = _QUERY_SIZES if query else _DEMO_SIZES
    sides, query_sides = _side_orders(seed)
    profiles, query_profiles = _profile_orders(seed)
    h, w = sizes[index]
    side = (query_sides if query else sides)[index]
    profile = (query_profiles if query else profiles)[index]
    if not query and index < 2:
        # The minimum two-demo lesson must make the cue causally necessary.
        # Cross each cue against a color-2 rectangle extending on a
        # perpendicular axis, so neither "nearest color 2" nor "farthest from
        # color 2" can fit the demonstrations by accident.
        profile = {
            "north": "2_east",
            "south": "2_west",
            "east": "2_north",
            "west": "2_south",
        }[side]
    rng = _seeded(seed, "query" if query else "demo", index)
    boundary = query and index == 3 or ((index + seed) % 2 == 1)
    rect2, rect3 = _rectangles(h, w, profile, boundary, rng)
    grid = _empty(h, w)
    _draw_border(grid, rect2, 2)
    _draw_border(grid, rect3, 3)
    _place_cue(grid, side, rng)
    distractors = max(4, (h * w) // (22 if query and index == 3 else 35))
    _add_distractors(grid, rng, distractors)
    inspect_scene(grid)  # Construction assertion.
    return grid


def inspect_scene(grid) -> dict[str, object]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of lists")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    cues = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if len(cues) != 1:
        raise ValueError("scene needs exactly one color-1 cue")
    r0, c0, r1, c1 = _overlap(grid)
    cr, cc = cues[0]
    if cr < r0 and c0 <= cc <= c1:
        side = "north"
    elif cr > r1 and c0 <= cc <= c1:
        side = "south"
    elif cc < c0 and r0 <= cr <= r1:
        side = "west"
    elif cc > c1 and r0 <= cr <= r1:
        side = "east"
    else:
        raise ValueError("cue must indicate exactly one side of the overlap")
    return {
        "bbox2": _bbox(grid, 2),
        "bbox3": _bbox(grid, 3),
        "overlap": (r0, c0, r1, c1),
        "overlap_height": r1 - r0 + 1,
        "overlap_width": c1 - c0 + 1,
        "cue": cues[0],
        "cue_side": side,
    }


def _paint(grid, cells) -> list[list[int]]:
    output = _empty(len(grid), len(grid[0]))
    for r, c in cells:
        output[r][c] = 8
    return output


def _edge_cells(box, side: str):
    r0, c0, r1, c1 = box
    if side == "north":
        return [(r0, c) for c in range(c0, c1 + 1)]
    if side == "south":
        return [(r1, c) for c in range(c0, c1 + 1)]
    if side == "west":
        return [(r, c0) for r in range(r0, r1 + 1)]
    if side == "east":
        return [(r, c1) for r in range(r0, r1 + 1)]
    raise ValueError(side)


def _opposite(side: str) -> str:
    return {"north": "south", "south": "north", "west": "east", "east": "west"}[side]


def rule_mirror(grid, edge_policy: str) -> list[list[int]]:
    if edge_policy not in EDGE_POLICIES:
        raise ValueError(edge_policy)
    scene = inspect_scene(grid)
    box = scene["overlap"]
    if edge_policy == "full":
        r0, c0, r1, c1 = box
        cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
    else:
        side = scene["cue_side"]
        if edge_policy == "far_cue":
            side = _opposite(side)
        cells = _edge_cells(box, side)
    return _paint(grid, cells)


def fixed_edge_rival(grid, side: str) -> list[list[int]]:
    return _paint(grid, _edge_cells(inspect_scene(grid)["overlap"], side))


def color2_near_rival(grid) -> list[list[int]]:
    scene = inspect_scene(grid)
    r0, c0, r1, c1 = scene["overlap"]
    b2 = scene["bbox2"]
    extensions = {
        "north": r0 - b2[0],
        "south": b2[2] - r1,
        "west": c0 - b2[1],
        "east": b2[3] - c1,
    }
    side = max(CUE_SIDES, key=lambda name: (extensions[name], -CUE_SIDES.index(name)))
    return fixed_edge_rival(grid, side)


def color2_far_rival(grid) -> list[list[int]]:
    scene = inspect_scene(grid)
    r0, c0, r1, c1 = scene["overlap"]
    b2 = scene["bbox2"]
    extensions = {
        "north": r0 - b2[0],
        "south": b2[2] - r1,
        "west": c0 - b2[1],
        "east": b2[3] - c1,
    }
    near = max(CUE_SIDES, key=lambda name: (extensions[name], -CUE_SIDES.index(name)))
    return fixed_edge_rival(grid, _opposite(near))


def generate(seed, settings, demos, queries):
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    policy = _settings(settings)

    demo_inputs = [_scene(seed, index, query=False) for index in range(6)]
    query_inputs = [_scene(seed, index, query=True) for index in range(4)]
    train = [
        {"input": deepcopy(grid), "output": rule_mirror(grid, policy)}
        for grid in demo_inputs[:demos]
    ]
    test = [
        {"input": deepcopy(grid), "output": rule_mirror(grid, policy)}
        for grid in query_inputs[:queries]
    ]
    return {"program_solution": program({"edge_policy": policy}), "train": train, "test": test}
