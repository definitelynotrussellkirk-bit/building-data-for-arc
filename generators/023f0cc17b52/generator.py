"""Generator for bank task fe45a3aa7042:S11_E5 / 023f0cc17b52.

Find the unique largest non-blue monochrome component. Translate only its
4-connected boundary so the component's bounding-box top-left lands on the
single blue anchor. Draw on a blank canvas and clip cells beyond the bottom or
right edge. The source objects, anchor, and any smaller decoy disappear.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "023f0cc17b52"
VERSION = "3.0.0"
TASK_ID = "023f0cc17b52"
RULE_HASH = "72d627c3478b"

SUMMARY = (
    "Place one blue anchor and a uniquely largest solid rectangle or "
    "non-rectangular blob, optionally with one smaller decoy. The oracle "
    "returns only the largest object's boundary translated so its bbox "
    "top-left is the anchor, with edge clipping."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and there is exactly one blue(1) anchor",
    "there are one or two non-blue monochrome components",
    "the main component is uniquely largest and has an interior cell",
    "the optional decoy is strictly smaller than the main component",
    "the output is a blank canvas plus the translated main boundary",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted rng",
        "valid": "8..12",
        "doc": "Input/output grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted rng",
        "valid": "9..14",
        "doc": "Input/output grid width.",
    },
    "main_height": {
        "type": "int",
        "default": "difficulty-weighted rng",
        "valid": "3..5",
        "doc": "Main component bounding-box height.",
    },
    "main_width": {
        "type": "int",
        "default": "difficulty-weighted rng",
        "valid": "3..5",
        "doc": "Main component bounding-box width.",
    },
    "main_color": {
        "type": "color",
        "default": "rng non-background/non-anchor color",
        "valid": "2..9",
        "doc": "Color of the uniquely largest component.",
    },
    "shape_kind": {
        "type": "enum",
        "default": "rng rect|blob",
        "valid": "rect|blob",
        "doc": "Whether the main component fills its bbox.",
    },
    "has_decoy": {
        "type": "bool",
        "default": "difficulty-weighted rng",
        "valid": "false|true",
        "doc": "Whether one strictly smaller component is present.",
    },
    "clips_output": {
        "type": "bool",
        "default": "difficulty-weighted rng",
        "valid": "false|true",
        "doc": "Whether translated boundary cells cross a canvas edge.",
    },
}

_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = tuple(range(2, 10))

# (grid_h, grid_w, main_h, main_w, anchor delta from main bbox top-left)
_CANONICAL_PROFILES = (
    (8, 10, 3, 4, (3, 4)),
    (8, 11, 3, 3, (4, 4)),
    (9, 12, 3, 4, (4, -3)),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "main_height", "main_width", "main_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    for name in ("has_decoy", "clips_output"):
        value = overrides.get(name)
        if value is not None and type(value) is not bool:
            raise ValueError(f"{name} must be a boolean")
    value = overrides.get("shape_kind")
    if value is not None and type(value) is not str:
        raise ValueError("shape_kind must be a string")


def _weighted_values(axis, difficulty):
    if axis == "grid_h":
        return {
            "easy": (8, 8, 8, 9, 10, 11, 12),
            "medium": (8, 9, 9, 10, 10, 11, 12),
            "hard": (8, 9, 10, 11, 11, 12, 12),
        }.get(difficulty, (8, 9, 10, 11, 12))
    if axis == "grid_w":
        return {
            "easy": (9, 9, 10, 10, 11, 12, 13, 14),
            "medium": (9, 10, 11, 11, 12, 12, 13, 14),
            "hard": (9, 10, 11, 12, 13, 13, 14, 14),
        }.get(difficulty, (9, 10, 11, 12, 13, 14))
    if axis in ("main_height", "main_width"):
        return {
            "easy": (3, 3, 3, 4, 5),
            "medium": (3, 3, 4, 4, 5),
            "hard": (3, 4, 4, 5, 5),
        }.get(difficulty, (3, 4, 5))
    raise KeyError(axis)


def _norm(cells):
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINALS:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _has_interior(cells):
    cells = set(cells)
    return any(
        all((r + dr, c + dc) in cells for dr, dc in _CARDINALS)
        for r, c in cells
    )


def _blob_shape(height, width, rng):
    full = {(r, c) for r in range(height) for c in range(width)}
    boundary = [
        cell for cell in sorted(full)
        if cell[0] in (0, height - 1) or cell[1] in (0, width - 1)
    ]
    for _ in range(80):
        trial = set(full)
        count = rng.randint(1, min(3, max(1, len(boundary) // 3)))
        for cell in rng.sample(boundary, count):
            trial.discard(cell)
        rows = {r for r, _ in trial}
        cols = {c for _, c in trial}
        if (
            len(trial) < len(full)
            and rows == set(range(height))
            and cols == set(range(width))
            and _connected(trial)
            and _has_interior(trial)
        ):
            return tuple(sorted(trial))
    # Removing opposite corners is valid for every declared 3..5 bbox.
    trial = full - {(0, width - 1), (height - 1, 0)}
    if _connected(trial) and _has_interior(trial):
        return tuple(sorted(trial))
    raise AssertionError("could not build a valid blob")


def _shape_cells(kind, height, width, rng):
    if kind == "rect":
        return tuple((r, c) for r in range(height) for c in range(width))
    return _blob_shape(height, width, rng)


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 1) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINALS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            min_r = min(rr for rr, _ in cells)
            max_r = max(rr for rr, _ in cells)
            min_c = min(cc for _, cc in cells)
            max_c = max(cc for _, cc in cells)
            comps.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "size": len(cells),
                "r0": min_r,
                "c0": min_c,
                "height": max_r - min_r + 1,
                "width": max_c - min_c + 1,
                "shape": _norm(cells),
            })
    return tuple(comps)


def _boundary(cells):
    cell_set = set(cells)
    return tuple(sorted(
        (r, c) for r, c in cell_set
        if any((r + dr, c + dc) not in cell_set for dr, dc in _CARDINALS)
    ))


def _analyze(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    anchors = tuple(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 1
    )
    comps = _components(grid)
    ordered = tuple(sorted(comps, key=lambda comp: (-comp["size"], comp["r0"], comp["c0"])))
    target = ordered[0] if ordered else None
    if target is None or len(anchors) != 1:
        clips = None
    else:
        ar, ac = anchors[0]
        clips = ar + target["height"] > h or ac + target["width"] > w
    return {
        "grid": grid,
        "h": h,
        "w": w,
        "anchors": anchors,
        "components": ordered,
        "target": target,
        "clips_output": clips,
    }


def _decoy_shape(rng, max_size):
    shapes = (
        ((0, 0),),
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    )
    legal = [shape for shape in shapes if len(shape) <= max_size]
    return rng.choice(legal)


def _place_decoy(grid, occupied, anchor, main_color, main_size, rng):
    h, w = len(grid), len(grid[0])
    shape = _decoy_shape(rng, min(4, main_size - 1))
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    positions = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(positions)
    decoy_color = main_color if rng.random() < 0.5 else rng.choice(
        [color for color in _COLORS if color != main_color]
    )
    for r0, c0 in positions:
        cells = {(r0 + r, c0 + c) for r, c in shape}
        if anchor in cells or cells & occupied:
            continue
        if any(
            (r + dr, c + dc) in occupied
            for r, c in cells
            for dr, dc in _CARDINALS
        ):
            continue
        for r, c in cells:
            grid[r][c] = decoy_color
        return True
    return False


def _canonical_board(ctx, profile):
    h0, w0, main_h0, main_w0, delta = profile
    h = ctx.draw_choice("grid_h", (h0,))
    w = ctx.draw_choice("grid_w", (w0,))
    main_h = ctx.draw_choice("main_height", (main_h0,))
    main_w = ctx.draw_choice("main_width", (main_w0,))
    main_color = ctx.draw_choice("main_color", _COLORS)
    shape_kind = ctx.draw_choice("shape_kind", ("rect",))
    has_decoy = ctx.draw_choice("has_decoy", (False,))
    clips_output = ctx.draw_choice("clips_output", (False,))
    assert shape_kind == "rect" and not has_decoy and not clips_output

    dr, dc = delta
    placements = []
    for r0 in range(h - main_h + 1):
        for c0 in range(w - main_w + 1):
            ar, ac = r0 + dr, c0 + dc
            if not (0 <= ar < h and 0 <= ac < w):
                continue
            if ar + main_h > h or ac + main_w > w:
                continue
            if r0 <= ar < r0 + main_h and c0 <= ac < c0 + main_w:
                continue
            placements.append((r0, c0, ar, ac))
    if not placements:
        raise AssertionError("canonical profile has no legal nuisance translation")
    r0, c0, ar, ac = ctx.draw_rng("canonical_layout").choice(placements)
    grid = full_grid(h, w, 0)
    for r in range(main_h):
        for c in range(main_w):
            grid[r0 + r][c0 + c] = main_color
    grid[ar][ac] = 1
    return grid


def _general_board(ctx, difficulty, schedule_slot=None):
    h = ctx.draw_choice("grid_h", _weighted_values("grid_h", difficulty))
    w = ctx.draw_choice("grid_w", _weighted_values("grid_w", difficulty))
    main_h = ctx.draw_choice(
        "main_height", _weighted_values("main_height", difficulty)
    )
    main_w = ctx.draw_choice(
        "main_width", _weighted_values("main_width", difficulty)
    )
    main_color = ctx.draw_choice("main_color", _COLORS)
    if schedule_slot == 1:
        shape_options = ("blob",)
        decoy_options = (False,)
        clip_options = (False,)
    elif schedule_slot == 2:
        shape_options = ("rect", "blob")
        decoy_options = (True,)
        clip_options = (False,)
    elif schedule_slot == 3:
        shape_options = ("rect", "blob")
        decoy_options = (False, True)
        clip_options = (True,)
    else:
        shape_options = (
            ("rect", "rect", "blob")
            if difficulty == "easy"
            else ("rect", "blob")
        )
        decoy_options = {
            "easy": (False, False, False, True),
            "medium": (False, False, True, True),
            "hard": (False, True, True, True),
        }.get(difficulty, (False, True))
        clip_options = {
            "easy": (False, False, False, True),
            "medium": (False, False, True, True),
            "hard": (False, True, True, True),
        }.get(difficulty, (False, True))
    shape_kind = ctx.draw_choice("shape_kind", shape_options)
    has_decoy = ctx.draw_choice("has_decoy", decoy_options)
    clips_output = ctx.draw_choice("clips_output", clip_options)
    rng = ctx.draw_rng("layout")
    shape = _shape_cells(shape_kind, main_h, main_w, rng)

    main_positions = [
        (r0, c0)
        for r0 in range(h - main_h + 1)
        for c0 in range(w - main_w + 1)
    ]
    anchor_positions = [
        (ar, ac)
        for ar in range(h)
        for ac in range(w)
        if ((ar + main_h > h or ac + main_w > w) == clips_output)
    ]
    rng.shuffle(main_positions)
    rng.shuffle(anchor_positions)

    for r0, c0 in main_positions:
        main_cells = {(r0 + r, c0 + c) for r, c in shape}
        for ar, ac in anchor_positions:
            if (ar, ac) in main_cells:
                continue
            if r0 <= ar < r0 + main_h and c0 <= ac < c0 + main_w:
                continue
            grid = full_grid(h, w, 0)
            for r, c in main_cells:
                grid[r][c] = main_color
            grid[ar][ac] = 1
            if has_decoy and not _place_decoy(
                grid, main_cells, (ar, ac), main_color, len(main_cells), rng
            ):
                continue
            if not self_check(grid):
                return grid
    raise ValueError("could not realize requested boundary-translation scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    schedule_slot = sample_index % 4 if not overrides else None
    use_profile = schedule_slot == 0
    if use_profile:
        ctx.draw_choice("canonical_profile", (True,))
        profile = ctx.draw_choice("canonical_profile_id", _CANONICAL_PROFILES)
        grid = _canonical_board(ctx, profile)
    else:
        if not overrides:
            ctx.draw_choice("canonical_profile", (False,))
        grid = _general_board(ctx, difficulty, schedule_slot=schedule_slot)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]
    scene = _analyze(grid)
    errors = []
    if not 8 <= scene["h"] <= 12:
        errors.append("grid height must be 8..12")
    if not 9 <= scene["w"] <= 14:
        errors.append("grid width must be 9..14")
    if len(scene["anchors"]) != 1:
        errors.append("scene must contain exactly one blue(1) anchor")
    comps = scene["components"]
    if not 1 <= len(comps) <= 2:
        errors.append("scene must contain one main component and at most one decoy")
        return errors
    if len(comps) == 2 and comps[0]["size"] == comps[1]["size"]:
        errors.append("largest non-blue component must be unique")
    target = comps[0]
    if not 3 <= target["height"] <= 5 or not 3 <= target["width"] <= 5:
        errors.append("main component bbox dimensions must each be 3..5")
    if not _has_interior(target["cells"]):
        errors.append("main component must contain an interior cell")
    if len(comps) == 2 and comps[1]["size"] >= target["size"]:
        errors.append("decoy must be strictly smaller than the main component")
    if len(comps) == 2 and comps[1]["size"] > 4:
        errors.append("decoy may contain at most four cells")
    if len(scene["anchors"]) == 1 and not _boundary(target["cells"]):
        errors.append("main component boundary must be nonempty")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze(grid)
    target = scene["target"]
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "main_height": target["height"],
        "main_width": target["width"],
        "main_color": target["color"],
        "shape_kind": "rect" if target["size"] == target["height"] * target["width"] else "blob",
        "has_decoy": len(scene["components"]) == 2,
        "clips_output": scene["clips_output"],
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze(grid)
    target = scene["target"]
    ar, ac = scene["anchors"][0]
    dr = ar - target["r0"]
    dc = ac - target["c0"]
    output = full_grid(scene["h"], scene["w"], 0)
    for r, c in _boundary(target["cells"]):
        nr, nc = r + dr, c + dc
        if 0 <= nr < scene["h"] and 0 <= nc < scene["w"]:
            output[nr][nc] = target["color"]
    return output


def profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze(grid)
    target = scene["target"]
    ar, ac = scene["anchors"][0]
    return (
        scene["h"],
        scene["w"],
        target["shape"],
        (ar - target["r0"], ac - target["c0"]),
        len(scene["components"]) - 1,
        scene["clips_output"],
    )


def _profile_tuple(profile):
    h, w, main_h, main_w, delta = profile
    shape = tuple((r, c) for r in range(main_h) for c in range(main_w))
    return (h, w, shape, delta, 0, False)


CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_tuple(profile) for profile in _CANONICAL_PROFILES
)


def is_canonical_profile(grid):
    return profile_signature(grid) in CANONICAL_PROFILE_SIGNATURES
