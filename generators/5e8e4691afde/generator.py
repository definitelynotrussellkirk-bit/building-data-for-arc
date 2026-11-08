"""Semantic generator for ARC task 5e8e4691afde.

Use the vector from the colored path indicator to the path's extra maroon
endpoint to relocate a maroon 3x3 frame.  Fill the canvas with the indicator
color, preserve the relocated frame's colored center, and draw both complete
maroon diagonals through that center.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5e8e4691afde"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ee2251228926"
SUMMARY = "Relocate a framed center by a path vector, then draw both diagonals."
INVARIANTS = [
    "the input has one maroon 3x3 frame with a nonzero, non-maroon, non-gray center",
    "the center color occurs once more as an indicator at one endpoint of a gray path",
    "one extra maroon cell terminates the other end of that path",
    "the indicator-to-extra-maroon vector keeps the relocated frame inside the canvas",
    "the output fills with the center color and draws the relocated frame and both diagonals maroon",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_test_1", "public_test_2",
)
GENERAL_SHIFTS = {
    "straight_down": (3, 0),
    "straight_up": (-3, 0),
    "straight_right": (0, 3),
    "straight_left": (0, -3),
    "diagonal_down_right": (3, 3),
    "diagonal_down_left": (3, -3),
    "diagonal_up_right": (-3, 3),
    "diagonal_up_left": (-3, -3),
    "long_down_right": (5, 2),
    "long_up_right": (-2, 5),
    "long_down_left": (4, -2),
}
GENERAL_PROFILES = tuple(GENERAL_SHIFTS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng over public and generalized path-vector lessons",
        "valid": "public_train_1|public_train_2|public_train_3|public_test_1|public_test_2|straight_down|straight_up|straight_right|straight_left|diagonal_down_right|diagonal_down_left|diagonal_up_right|diagonal_up_left|long_down_right|long_up_right|long_down_left",
    }
}

# (height, width, frame center row/col, color, indicator, extra maroon, gray cells)
_PUBLIC_SPECS = {
    "public_train_1": (15, 20, 8, 5, 7, (1, 14), (4, 15),
                       ((1, 15), (1, 16), (1, 17), (2, 17), (3, 17), (4, 16), (4, 17))),
    "public_train_2": (30, 30, 13, 16, 3, (25, 7), (28, 10),
                       ((25, 8), (25, 9), (25, 10), (26, 10), (27, 10))),
    "public_train_3": (30, 30, 12, 11, 8, (19, 24), (24, 24),
                       ((20, 24), (21, 24), (22, 24), (23, 24))),
    "public_test_1": (12, 13, 2, 6, 1, (2, 2), (7, 6),
                      ((3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (7, 3), (7, 4), (7, 5))),
    "public_test_2": (25, 20, 10, 7, 6, (21, 17), (19, 14),
                      ((19, 15), (19, 16), (20, 16), (21, 16))),
}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _blank(h, w):
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint_spec(spec):
    h, w, sr, sc, color, indicator, extra, gray = spec
    grid = _blank(h, w)
    for r in range(sr - 1, sr + 2):
        for c in range(sc - 1, sc + 2):
            grid[r][c] = 4
    grid[sr][sc] = color
    grid[indicator[0]][indicator[1]] = color
    for r, c in gray:
        grid[r][c] = 5
    grid[extra[0]][extra[1]] = 4
    return grid


_PUBLIC_INPUTS = {name: _paint_spec(spec) for name, spec in _PUBLIC_SPECS.items()}
_PUBLIC_SIGNATURES = {
    tuple(tuple(row) for row in grid): name for name, grid in _PUBLIC_INPUTS.items()
}


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors"], h, w
    return [], h, w


def _connected4(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _analysis(grid):
    errors, h, w = _validate_grid(grid)
    result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors:
        return result
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            if value in (0, 4, 5):
                continue
            if all(grid[r + dr][c + dc] == 4 for dr in (-1, 0, 1)
                   for dc in (-1, 0, 1) if (dr, dc) != (0, 0)):
                centers.append((r, c, value))
    if len(centers) != 1:
        errors.append("exactly one colored center inside a maroon 3x3 frame is required")
        return result
    sr, sc, color = centers[0]
    colored = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
    if len(colored) != 2:
        errors.append("frame-center color must occur exactly twice")
        return result
    indicator = next(position for position in colored if position != (sr, sc))
    border = {(r, c) for r in range(sr - 1, sr + 2) for c in range(sc - 1, sc + 2)} - {(sr, sc)}
    extra_cells = [(r, c) for r in range(h) for c in range(w)
                   if grid[r][c] == 4 and (r, c) not in border]
    if len(extra_cells) != 1:
        errors.append("exactly one extra maroon path endpoint is required")
        return result
    extra = extra_cells[0]
    gray = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    path = gray | {indicator, extra}
    if not gray or not _connected4(path):
        errors.append("indicator, gray cells, and extra maroon endpoint must form a connected path")
    if set(value for row in grid for value in row) - {0, 4, 5, color}:
        errors.append("input may contain only background, maroon, gray, and the center color")
    dr, dc = extra[0] - indicator[0], extra[1] - indicator[1]
    nr, nc = sr + dr, sc + dc
    if not (1 <= nr < h - 1 and 1 <= nc < w - 1):
        errors.append("path vector must keep the relocated frame inside the grid")
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None:
        profile = next((name for name, shift in GENERAL_SHIFTS.items() if shift == (dr, dc)), None)
    if profile not in SCENE_PROFILES:
        errors.append("path vector does not match a declared semantic lesson")
    result.update({
        "center": (sr, sc), "color": color, "indicator": indicator, "extra": extra,
        "gray": frozenset(gray), "shift": (dr, dc), "new_center": (nr, nc),
        "scene_profile": profile, "errors": errors,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    h, w, color = info["height"], info["width"], info["color"]
    nr, nc = info["new_center"]
    return [[
        color if (r, c) == (nr, nc) else
        4 if (abs(r - nr) <= 1 and abs(c - nc) <= 1) else
        4 if (r - c == nr - nc or r + c == nr + nc) else
        color
        for c in range(w)
    ] for r in range(h)]


def _path_between(start, extra, horizontal_first):
    r, c = start
    er, ec = extra
    cells = []
    if horizontal_first:
        while c != ec:
            c += 1 if ec > c else -1
            if (r, c) != extra:
                cells.append((r, c))
        while r != er:
            r += 1 if er > r else -1
            if (r, c) != extra:
                cells.append((r, c))
    else:
        while r != er:
            r += 1 if er > r else -1
            if (r, c) != extra:
                cells.append((r, c))
        while c != ec:
            c += 1 if ec > c else -1
            if (r, c) != extra:
                cells.append((r, c))
    return tuple(cells)


def _dimensions(rng, band):
    bounds = {"easy": (12, 16), "medium": (17, 23), "hard": (24, 30)}
    low, high = bounds[band]
    return rng.randint(low, high), rng.randint(low, high)


def _general_grid(rng, profile, band):
    h, w = _dimensions(rng, band)
    dr, dc = GENERAL_SHIFTS[profile]
    valid_centers = [
        (r, c) for r in range(1, h - 1) for c in range(1, w - 1)
        if 1 <= r + dr < h - 1 and 1 <= c + dc < w - 1
    ]
    sr, sc = rng.choice(valid_centers)
    frame = {(r, c) for r in range(sr - 1, sr + 2) for c in range(sc - 1, sc + 2)}
    nr, nc = sr + dr, sc + dc
    target = {(r, c) for r in range(nr - 1, nr + 2) for c in range(nc - 1, nc + 2)}
    candidates = []
    for ir in range(h):
        for ic in range(w):
            extra = (ir + dr, ic + dc)
            if not (0 <= extra[0] < h and 0 <= extra[1] < w):
                continue
            for horizontal_first in (True, False):
                gray = _path_between((ir, ic), extra, horizontal_first)
                occupied = {(ir, ic), extra, *gray}
                if gray and occupied.isdisjoint(frame | target):
                    candidates.append(((ir, ic), extra, gray))
    indicator, extra, gray = rng.choice(candidates)
    color = rng.choice((1, 2, 3, 6, 7, 8, 9))
    return _paint_spec((h, w, sr, sc, color, indicator, extra, gray))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    # Validate before GenCtx stringifies recipe identities for keyed draws.
    # Keep VERSION stable: every previously valid integer recipe is unchanged.
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=band, overrides=overrides)
    weighted = list(PUBLIC_PROFILES) + [profile for profile in GENERAL_PROFILES for _ in range(2)]
    profile = ctx.draw_choice("scene_profile", weighted)
    rng = ctx.draw_rng("layout")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_grid(rng, profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    if info["errors"]:
        return list(info["errors"])
    try:
        output = rule_mirror(grid)
    except Exception as exc:
        return [f"rule mirror failed: {type(exc).__name__}: {exc}"]
    if len(output) != info["height"] or any(len(row) != info["width"] for row in output):
        return ["output must preserve input dimensions"]
    if any(value not in (4, info["color"]) for row in output for value in row):
        return ["output palette must contain only maroon and the center color"]
    return []
