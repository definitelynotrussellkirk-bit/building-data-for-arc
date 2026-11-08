"""Native parametric family for e250cb77a62e.

The canonical setting extracts the yellow exemplar from the blue frame and stamps
it as drawn at each orange seed.  The alternative consumes that same input-derived
exemplar, rotates it clockwise by one quarter turn, and stamps the rotated offsets.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK = "e250cb77a62e"
PARAMETER = "pattern_transform"
SETTINGS = ("as_drawn", "quarter_turn")
RIVALS = SETTINGS + (
    "half_turn",
    "counterclockwise",
    "reflect_horizontal",
    "reflect_vertical",
    "transpose",
    "first_seed_only",
    "last_seed_only",
    "quarter_turn_first_seed",
    "quarter_turn_last_seed",
    "every_other_seed",
    "seed_count_turn",
    "center_anchor",
    "solid_bbox",
)

_CANONICAL = (HERE / "canonical.rkt").read_text()
_TARGET_LAMBDA = "(lambda (p) (list (+ (fst seed) (fst p)) (+ (snd seed) (snd p))))"
_ROTATED_LAMBDA = (
    "(lambda (p) (list (+ (fst seed) (snd p)) "
    "(+ (snd seed) (- (- r1 r0 2) (fst p)))))"
)
if _CANONICAL.count(_TARGET_LAMBDA) != 1:
    raise RuntimeError("canonical stamping lambda changed")
_ALTERNATE = _CANONICAL.replace(_TARGET_LAMBDA, _ROTATED_LAMBDA)


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in SETTINGS
    ):
        raise ValueError("settings must contain only a declared pattern_transform")
    return settings[PARAMETER]


def program(settings):
    return _CANONICAL if _setting(settings) == "as_drawn" else _ALTERNATE


def counterfactual_program():
    """Wrong intermediate use for a quarter-turn episode: stamp it unrotated."""
    return _CANONICAL


def _validate_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height = len(grid)
    width = len(grid[0])
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("grid dimensions must be in 1..30")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid cells must be exact integer colors in 0..9")
    return height, width


def _border(r0, c0, r1, c1):
    return {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }


def _connected(cells):
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = set(pending)
    while pending:
        row, col = pending.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen == cells


def _transform(pattern, interior_h, interior_w, mode):
    if mode == "as_drawn":
        return tuple(sorted(pattern))
    if mode == "quarter_turn":
        return tuple(sorted((col, interior_h - 1 - row) for row, col in pattern))
    if mode == "half_turn":
        return tuple(sorted((interior_h - 1 - row, interior_w - 1 - col) for row, col in pattern))
    if mode == "counterclockwise":
        return tuple(sorted((interior_w - 1 - col, row) for row, col in pattern))
    if mode == "reflect_horizontal":
        return tuple(sorted((row, interior_w - 1 - col) for row, col in pattern))
    if mode == "reflect_vertical":
        return tuple(sorted((interior_h - 1 - row, col) for row, col in pattern))
    if mode == "transpose":
        return tuple(sorted((col, row) for row, col in pattern))
    raise ValueError("unknown geometric transform")


def _targets(seeds, offsets):
    return tuple(sorted({(sr + dr, sc + dc) for sr, sc in seeds for dr, dc in offsets}))


def analyze(grid):
    height, width = _validate_grid(grid)
    if any(value not in {0, 1, 4, 7} for row in grid for value in row):
        raise ValueError("admitted inputs use only colors 0, 1, 4, and 7")

    blue = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 1}
    if not blue:
        raise ValueError("input needs one complete blue frame")
    r0 = min(row for row, _ in blue)
    c0 = min(col for _, col in blue)
    r1 = max(row for row, _ in blue)
    c1 = max(col for _, col in blue)
    if r1 - r0 < 2 or c1 - c0 < 2 or blue != _border(r0, c0, r1, c1):
        raise ValueError("blue cells must form exactly one complete rectangular frame")

    yellow = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 4}
    if not yellow or any(not (r0 < row < r1 and c0 < col < c1) for row, col in yellow):
        raise ValueError("yellow exemplar must lie strictly inside the frame")
    interior_h = r1 - r0 - 1
    interior_w = c1 - c0 - 1
    pattern = tuple(sorted((row - r0 - 1, col - c0 - 1) for row, col in yellow))
    pattern_set = set(pattern)
    if (0, 0) not in pattern_set:
        raise ValueError("yellow exemplar must include its top-left anchor")
    if not _connected(pattern_set):
        raise ValueError("yellow exemplar must be four-connected")
    if max(row for row, _ in pattern) != interior_h - 1 or max(col for _, col in pattern) != interior_w - 1:
        raise ValueError("yellow exemplar must span the frame interior")

    seeds = tuple(sorted((row, col) for row in range(height) for col in range(width) if grid[row][col] == 7))
    if not 1 <= len(seeds) <= 4:
        raise ValueError("input needs 1..4 orange seeds")
    if any(r0 <= row <= r1 and c0 <= col <= c1 for row, col in seeds):
        raise ValueError("orange seeds must be outside the source frame")

    quarter = _transform(pattern, interior_h, interior_w, "quarter_turn")
    if pattern == quarter:
        raise ValueError("exemplar must distinguish as-drawn and quarter-turn transforms")

    by_mode = {}
    frame_box = {(row, col) for row in range(r0, r1 + 1) for col in range(c0, c1 + 1)}
    for mode, offsets in (("as_drawn", pattern), ("quarter_turn", quarter)):
        footprints = []
        for seed_r, seed_c in seeds:
            footprint = {(seed_r + dr, seed_c + dc) for dr, dc in offsets}
            if any(not (0 <= row < height and 0 <= col < width) for row, col in footprint):
                raise ValueError(f"{mode} stamp must fit inside the canvas")
            if footprint & frame_box:
                raise ValueError(f"{mode} stamp may not overlap the source frame")
            footprints.append(footprint)
        for index, footprint in enumerate(footprints):
            if any(footprint & other for other in footprints[index + 1 :]):
                raise ValueError(f"{mode} stamp footprints must be disjoint")
        by_mode[mode] = tuple(sorted(set().union(*footprints)))

    return {
        "height": height,
        "width": width,
        "frame_bbox": (r0, c0, r1, c1),
        "interior_height": interior_h,
        "interior_width": interior_w,
        "pattern": pattern,
        "quarter_turn_pattern": quarter,
        "seeds": seeds,
        "as_drawn_targets": by_mode["as_drawn"],
        "quarter_turn_targets": by_mode["quarter_turn"],
    }


def _policy(info, mode):
    seeds = info["seeds"]
    pattern = info["pattern"]
    h = info["interior_height"]
    w = info["interior_width"]
    if mode in {"as_drawn", "quarter_turn", "half_turn", "counterclockwise", "reflect_horizontal", "reflect_vertical", "transpose"}:
        return seeds, _transform(pattern, h, w, mode), False
    if mode == "first_seed_only":
        return seeds[:1], pattern, False
    if mode == "last_seed_only":
        return seeds[-1:], pattern, False
    if mode == "quarter_turn_first_seed":
        return seeds[:1], _transform(pattern, h, w, "quarter_turn"), False
    if mode == "quarter_turn_last_seed":
        return seeds[-1:], _transform(pattern, h, w, "quarter_turn"), False
    if mode == "every_other_seed":
        return seeds[::2], pattern, False
    if mode == "seed_count_turn":
        transforms = ("as_drawn", "quarter_turn", "half_turn", "counterclockwise")
        return seeds, _transform(pattern, h, w, transforms[len(seeds) % 4]), False
    if mode == "center_anchor":
        shifted = tuple(sorted((row - (h - 1) // 2, col - (w - 1) // 2) for row, col in pattern))
        return seeds, shifted, True
    if mode == "solid_bbox":
        return seeds, tuple((row, col) for row in range(h) for col in range(w)), True
    raise ValueError("unknown stamping policy")


def claim(grid, mode):
    if mode not in RIVALS:
        raise ValueError("unknown stamping policy")
    info = analyze(grid)
    seeds, offsets, clip = _policy(info, mode)
    output = deepcopy(grid)
    for seed_r, seed_c in seeds:
        for dr, dc in offsets:
            row, col = seed_r + dr, seed_c + dc
            if 0 <= row < info["height"] and 0 <= col < info["width"]:
                output[row][col] = 8
            elif not clip:
                raise ValueError("stamping policy escaped the canvas")
    return output


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK}:native-v1:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _pattern(interior_h, interior_w, target, rng):
    minimum = interior_h + interior_w - 1
    if not minimum <= target <= interior_h * interior_w:
        raise ValueError("invalid exemplar size")
    cells = {(0, col) for col in range(interior_w)}
    cells.update((row, interior_w - 1) for row in range(1, interior_h))
    while len(cells) < target:
        frontier = sorted({
            neighbor
            for row, col in cells
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
            if 0 <= neighbor[0] < interior_h
            and 0 <= neighbor[1] < interior_w
            and neighbor not in cells
        })
        if not frontier:
            raise RuntimeError("exemplar growth exhausted unexpectedly")
        cells.add(rng.choice(frontier))
    result = tuple(sorted(cells))
    if result == _transform(result, interior_h, interior_w, "quarter_turn"):
        raise RuntimeError("constructed exemplar failed to separate transforms")
    return result


# height, width, frame top, frame left, interior height, interior width,
# exemplar size, and orange seed coordinates.
DEMO_SPECS = (
    (12, 15, 0, 0, 3, 4, 7, ((6, 0), (6, 8))),
    (15, 18, 1, 1, 4, 3, 8, ((0, 10), (7, 9), (10, 0))),
    (16, 19, 0, 11, 3, 5, 9, ((0, 0), (6, 0), (10, 9))),
    (18, 20, 2, 0, 5, 4, 12, ((0, 11), (9, 9), (13, 0))),
    (21, 23, 0, 0, 4, 6, 13, ((7, 0), (7, 10), (14, 8))),
    (25, 25, 1, 1, 6, 5, 17, ((0, 13), (9, 0), (12, 13), (19, 6))),
)
QUERY_SPECS = (
    (13, 16, 0, 8, 3, 4, 8, ((0, 0), (7, 0), (8, 8))),
    (17, 20, 0, 12, 4, 5, 11, ((0, 0), (7, 0), (11, 10))),
    (25, 26, 2, 2, 6, 7, 20, ((0, 15), (11, 0), (16, 14))),
    (30, 30, 0, 0, 8, 10, 32, ((12, 0), (12, 11), (20, 20))),
)


def _scene(seed, spec, stream):
    height, width, top, left, interior_h, interior_w, target, seeds = spec
    bottom = top + interior_h + 1
    right = left + interior_w + 1
    if bottom >= height or right >= width:
        raise RuntimeError("frame spec exceeds canvas")
    grid = [[0] * width for _ in range(height)]
    for row, col in _border(top, left, bottom, right):
        grid[row][col] = 1
    pattern = _pattern(interior_h, interior_w, target, _rng(seed, f"{stream}:pattern"))
    for dr, dc in pattern:
        grid[top + 1 + dr][left + 1 + dc] = 4
    for row, col in seeds:
        if grid[row][col] != 0:
            raise RuntimeError("seed spec overlaps source")
        grid[row][col] = 7
    analyze(grid)  # construction contract: both settings are total on every draw
    return grid


def generate(seed, settings, demos=3, queries=4):
    mode = _setting(settings)
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pair(spec, stream):
        grid = _scene(seed, spec, stream)
        return {"input": grid, "output": claim(grid, mode)}

    return {
        "train": [pair(spec, f"demo:{index}") for index, spec in enumerate(DEMO_SPECS[:demos])],
        "test": [pair(spec, f"query:{index}") for index, spec in enumerate(QUERY_SPECS[:queries])],
        "program_solution": program(settings),
        "settings": dict(settings),
    }


def teaching_check(episode):
    mode = _setting(episode["settings"])
    findings = []
    for rival in RIVALS:
        if rival == mode:
            continue
        fits = all(claim(pair["input"], rival) == pair["output"] for pair in episode["train"])
        if fits:
            changed = [
                index
                for index, pair in enumerate(episode["test"])
                if claim(pair["input"], rival) != pair["output"]
            ]
            if changed:
                findings.append({"rival": rival, "queries": changed})
    return findings


def public_turn(episode, index=0):
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index out of range")
    return deepcopy({
        "train": [{"input": pair["input"], "output": pair["output"]} for pair in episode["train"]],
        "test": [{"input": episode["test"][index]["input"]}],
    })
