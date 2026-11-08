"""Generator for ARC task 60b3a4fe8090 — command-controlled room slides.

A 13x13 color-9 frame and cross define four 5x5 rooms.  The top-left cell of
each room is a command (1 up, 2 right, 3 down, 4 left).  Objects colored 5..8
slide to the commanded edge.  Canonical examples also contain object-shaped
blobs colored 1..4; those are distractors ignored by the selected Racket rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "60b3a4fe8090"
VERSION = "1.2.0"
RULE_HASH = "ddfddf7b7076"
SUMMARY = (
    "Four walled rooms with a permutation of commands; distinct 1..8 blobs "
    "include both command-colored distractors and movable 5..8 objects."
)

INVARIANTS = [
    "13x13 outer frame and internal cross are color 9 (canonical divider spill is tolerated)",
    "room commands are a permutation of 1,2,3,4",
    "each room has one distinct 8-connected monochrome object of size 2..5",
    "at least one object is command-colored (ignored) and at least one is color 5..8 (moved)",
]

AXES = {
    "ignored_object_count": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "object_size": {"type": "int", "default": "difficulty-aware 2..5", "valid": "2..5"},
}

EXAMPLES_NEEDED = 3
ROOMS = ((0, 0), (0, 6), (6, 0), (6, 6))
_COMMANDS = (1, 2, 3, 4)
_DIRECTIONS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
_NEIGHBORS8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    for name in AXES:
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _normalise(cells):
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_variants(size):
    bases = {
        2: ((0, 0), (0, 1)),
        3: ((0, 0), (1, 0), (1, 1)),
        4: ((0, 0), (0, 1), (1, 0), (1, 1)),
        5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    }
    result = set()
    for reflect in (False, True):
        for rotations in range(4):
            transformed = []
            for row, col in bases[size]:
                if reflect:
                    col = -col
                for _ in range(rotations):
                    row, col = col, -row
                transformed.append((row, col))
            result.add(_normalise(transformed))
    # Include a diagonal chain so production actually covers the canonical
    # 8-connected-but-not-4-connected morphology.
    if size == 3:
        result.add(((0, 0), (1, 1), (2, 2)))
    return tuple(sorted(result))


def _connected8(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _NEIGHBORS8:
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def _room_payload(grid, r0, c0):
    command_pos = (r0 + 1, c0 + 1)
    payload = [(r, c, grid[r][c]) for r in range(r0 + 1, r0 + 6)
               for c in range(c0 + 1, c0 + 6)
               if (r, c) != command_pos and grid[r][c] not in (0, 9)]
    colors = {value for _, _, value in payload}
    if len(colors) != 1:
        raise ValueError(f"room at {(r0, c0)} must contain one monochrome object, got colors {sorted(colors)}")
    return grid[command_pos[0]][command_pos[1]], next(iter(colors)), {(r, c) for r, c, _ in payload}


def _analyse(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list:
        raise ValueError("grid is empty or not a 2D list")
    if len(grid) != 13 or any(type(row) is not list or len(row) != 13 for row in grid):
        raise ValueError("expected a 13x13 grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integers 0..9")

    for r in (0, 12):
        if any(grid[r][c] != 9 for c in range(13)):
            raise ValueError(f"outer wall row {r} must be color 9")
    for c in (0, 12):
        if any(grid[r][c] != 9 for r in range(13)):
            raise ValueError(f"outer wall column {c} must be color 9")

    divider_spill = []
    for c in range(1, 12):
        if grid[6][c] != 9:
            divider_spill.append((6, c, grid[6][c]))
    for r in range(1, 12):
        if r != 6 and grid[r][6] != 9:
            divider_spill.append((r, 6, grid[r][6]))
    if any(value not in range(1, 9) for _, _, value in divider_spill):
        raise ValueError("internal divider may only contain 9 or a canonical colored spill")

    commands, objects = [], []
    for r0, c0 in ROOMS:
        command, color, cells = _room_payload(grid, r0, c0)
        if command not in _COMMANDS:
            raise ValueError(f"room at {(r0, c0)} has invalid command {command}")
        if color not in range(1, 9):
            raise ValueError(f"room at {(r0, c0)} has invalid object color {color}")
        if not 2 <= len(cells) <= 5:
            raise ValueError(f"room at {(r0, c0)} object size must be 2..5, got {len(cells)}")
        if not _connected8(cells):
            raise ValueError(f"room at {(r0, c0)} object must be 8-connected")
        commands.append(command)
        objects.append((color, cells))
    if sorted(commands) != [1, 2, 3, 4]:
        raise ValueError(f"commands must be a permutation of 1..4, got {commands}")
    colors = [color for color, _ in objects]
    if len(set(colors)) != 4:
        raise ValueError(f"object colors must be distinct, got {colors}")
    if not any(color <= 4 for color in colors) or not any(color >= 5 for color in colors):
        raise ValueError("scene needs both ignored 1..4 and movable 5..8 objects")

    # The selected authority ignores a rare canonical object cell that spills
    # onto the divider.  Accept only spill that is adjacent to the same room
    # object, so a broken/missing wall is not silently accepted.
    for r, c, value in divider_spill:
        if not any(value == color and any(abs(r - rr) <= 1 and abs(c - cc) <= 1 for rr, cc in cells)
                   for color, cells in objects):
            raise ValueError(f"unattached divider spill at {(r, c)}")
    return {"commands": commands, "objects": objects, "divider_spill": divider_spill}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    try:
        _analyse(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid):
    info = _analyse(grid)
    sizes = {len(cells) for _, cells in info["objects"]}
    if len(sizes) != 1:
        raise ValueError("object_size is not a single realized value")
    return {
        "ignored_object_count": sum(color <= 4 for color, _ in info["objects"]),
        "object_size": next(iter(sizes)),
    }


def _distance_to_edge(local_cells, command):
    rows = [r for r, _ in local_cells]
    cols = [c for _, c in local_cells]
    if command == 1:
        return min(rows)
    if command == 2:
        return 4 - max(cols)
    if command == 3:
        return 4 - max(rows)
    return min(cols)


def _place_shape(rng, shape, command, require_motion):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = []
    for top in range(6 - sh):
        for left in range(6 - sw):
            cells = {(top + r, left + c) for r, c in shape}
            if (0, 0) in cells:
                continue
            if require_motion and _distance_to_edge(cells, command) == 0:
                continue
            candidates.append(cells)
    if not candidates:
        raise ValueError("no lawful placement for requested shape/command")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    ignored_count = ctx.draw_int_strict("ignored_object_count", 1, 3)
    size_bounds = {None: (2, 5), "easy": (2, 3), "medium": (2, 4), "hard": (3, 5)}[difficulty]
    if "object_size" in overrides and overrides["object_size"] is not None:
        object_size = ctx.draw_int_strict("object_size", 2, 5)
    else:
        object_size = ctx.draw_int_strict("object_size", *size_bounds)

    grid = full_grid(13, 13, 0)
    for c in range(13):
        grid[0][c] = grid[6][c] = grid[12][c] = 9
    for r in range(13):
        grid[r][0] = grid[r][6] = grid[r][12] = 9

    commands = list(_COMMANDS)
    ctx.draw_rng("commands").shuffle(commands)
    low = list(range(1, 5))
    high = list(range(5, 9))
    ctx.draw_rng("ignored-colors").shuffle(low)
    ctx.draw_rng("moving-colors").shuffle(high)
    colors = low[:ignored_count] + high[:4 - ignored_count]
    ctx.draw_rng("object-room-assignment").shuffle(colors)

    for index, ((r0, c0), command, color) in enumerate(zip(ROOMS, commands, colors)):
        grid[r0 + 1][c0 + 1] = command
        shape = ctx.draw_rng(f"shape-{index}").choice(_shape_variants(object_size))
        local = _place_shape(ctx.draw_rng(f"position-{index}"), shape, command, color <= 4)
        for r, c in local:
            grid[r0 + 1 + r][c0 + 1 + c] = color

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructed invalid instance: " + "; ".join(findings))
    return grid


def _slide_distance(cells, command, r0, c0):
    if command == 1:
        return min(r for r, _ in cells) - (r0 + 1)
    if command == 2:
        return (c0 + 5) - max(c for _, c in cells)
    if command == 3:
        return (r0 + 5) - max(r for r, _ in cells)
    return min(c for _, c in cells) - (c0 + 1)


def _apply(grid, *, slide_ignored):
    info = _analyse(grid)
    output = [[9 if value == 9 else 0 for value in row] for row in grid]
    for (r0, c0), command, (color, cells) in zip(ROOMS, info["commands"], info["objects"]):
        if color <= 4 and not slide_ignored:
            continue
        distance = _slide_distance(cells, command, r0, c0)
        dr, dc = _DIRECTIONS[command]
        for r, c in cells:
            output[r + dr * distance][c + dc * distance] = color
    return output


def rule_mirror(grid):
    return _apply(grid, slide_ignored=False)


def _slide_all_colored_objects(grid):
    return _apply(grid, slide_ignored=True)


def _has_ignored_object(grid):
    try:
        return any(color <= 4 for color, _ in _analyse(grid)["objects"])
    except (TypeError, ValueError):
        return False


strict_canonical_like = self_check
SEMANTIC_WITNESSES = {"ignored_command_color_object": _has_ignored_object}
SEMANTIC_RIVALS = {"slide_all_colored_objects": _slide_all_colored_objects}
WITNESS_RIVALS = {"ignored_command_color_object": ["slide_all_colored_objects"]}
LESSON_COMPETITORS = SEMANTIC_RIVALS
