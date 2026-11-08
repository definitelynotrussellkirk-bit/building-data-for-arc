"""Semantic generator for ARC task 5de3293e1bda.

Normalize the blue 1 and red 2 cell sets independently to their top-left
corners, intersect the normalized sets, crop to the intersection bounding
box, and paint intersection cells cyan 8 on zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5de3293e1bda"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "7cd0ccb1b858"
SUMMARY = "Crop and render the normalized overlap of the blue and red shapes in cyan."
INVARIANTS = [
    "input background is zero and foreground colors are exactly blue 1 and red 2",
    "each color forms one 4-connected shape",
    "the independently normalized shapes have a non-empty, non-identical overlap",
    "the output is the overlap bbox with cyan 8 at shared normalized cells and zero elsewhere",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_train_4", "public_test_1",
)
GENERAL_PROFILES = (
    "overlap_single_cell", "overlap_vertical_pair", "overlap_horizontal_pair", "overlap_l_three",
    "overlap_t_four", "overlap_sparse_wide", "overlap_sparse_tall", "second_shape_subset",
    "first_shape_subset", "large_partial_overlap", "same_row_placement",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng favoring varied subset and large-overlap lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_INPUTS = {
    "public_train_1": (
        "00000000000", "01100000000", "01100000000", "01000000200",
        "00000002220", "00000000000", "00000000000", "00000000000",
    ),
    "public_train_2": (
        "000000000000", "000000000100", "000000001100", "000000000110",
        "000000000000", "022000000000", "002200000000", "000000000000",
        "000000000000",
    ),
    "public_train_3": (
        "0000000000", "0000000000", "0101000000", "0111000000",
        "0000002220", "0000002000", "0000002000", "0000000000",
    ),
    "public_train_4": (
        "000000000000", "001000000000", "011100000000", "001000000000",
        "000000000000", "000000000200", "000000002220", "000000000000",
        "000000000000", "000000000000",
    ),
    "public_test_1": (
        "00000000000", "00000000000", "00110000000", "00110000000",
        "00100000200", "00000002200", "00000000220", "00000000000",
        "00000000000",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(cell) for cell in row) for row in rows): profile
    for profile, rows in _PUBLIC_INPUTS.items()
}

_PAIR_TEMPLATES = {
    "overlap_single_cell": (
        {(0, 0), (0, 1)}, {(0, 0), (1, 0)}),
    "overlap_vertical_pair": (
        {(0, 0), (1, 0), (0, 1)}, {(0, 0), (1, 0), (2, 0)}),
    "overlap_horizontal_pair": (
        {(0, 0), (0, 1), (1, 0)}, {(0, 0), (0, 1), (0, 2)}),
    "overlap_l_three": (
        {(0, 0), (1, 0), (1, 1), (0, 1)}, {(0, 0), (1, 0), (1, 1), (2, 1)}),
    "overlap_t_four": (
        {(0, 1), (1, 0), (1, 1), (1, 2), (0, 0)},
        {(0, 1), (1, 0), (1, 1), (1, 2), (0, 2)}),
    "overlap_sparse_wide": (
        {(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)},
        {(0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)}),
    "overlap_sparse_tall": (
        {(0, 0), (1, 0), (2, 0), (3, 0), (0, 1)},
        {(0, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)}),
    "second_shape_subset": (
        {(0, 0), (1, 0), (1, 1), (0, 1)}, {(0, 0), (1, 0), (1, 1)}),
    "first_shape_subset": (
        {(0, 0), (1, 0), (1, 1)}, {(0, 0), (1, 0), (1, 1), (0, 1)}),
    "large_partial_overlap": (
        {(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)},
        {(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2)}),
    "same_row_placement": (
        {(0, 0), (1, 0), (1, 1), (0, 1)}, {(0, 0), (1, 0), (1, 1), (2, 1)}),
}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


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
            if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1, 2):
                return ["input cells must be integer colors 0, 1, or 2"], h, w
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


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _crop(cells):
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def _classify(info):
    if info["blue_origin"][0] == info["red_origin"][0]:
        return "same_row_placement"
    blue, red, inter = info["blue_shape"], info["red_shape"], info["intersection"]
    if red < blue:
        return "second_shape_subset"
    if blue < red:
        return "first_shape_subset"
    if len(inter) >= 5:
        return "large_partial_overlap"
    rows = [r for r, _ in inter]; cols = [c for _, c in inter]
    dims = (max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)
    if len(inter) == 1:
        return "overlap_single_cell"
    if len(inter) == 2 and dims == (2, 1):
        return "overlap_vertical_pair"
    if len(inter) == 2 and dims == (1, 2):
        return "overlap_horizontal_pair"
    if len(inter) == 3 and dims == (2, 2):
        return "overlap_l_three"
    if len(inter) == 4 and dims == (2, 3):
        return "overlap_t_four"
    if len(inter) == 3 and dims == (2, 4):
        return "overlap_sparse_wide"
    if len(inter) == 3 and dims == (4, 2):
        return "overlap_sparse_tall"
    return None


def _analysis(grid):
    errors, h, w = _validate_grid(grid)
    result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors:
        return result
    blue_cells = tuple((r, c) for r in range(h) for c in range(w) if grid[r][c] == 1)
    red_cells = tuple((r, c) for r in range(h) for c in range(w) if grid[r][c] == 2)
    if not blue_cells or not red_cells:
        errors.append("both a blue shape and a red shape are required")
        return result
    if not _connected4(blue_cells) or not _connected4(red_cells):
        errors.append("each color must form one 4-connected shape")
    blue = _normalize(blue_cells); red = _normalize(red_cells); inter = blue & red
    if not inter:
        errors.append("normalized shapes must overlap")
    if blue == red:
        errors.append("normalized shapes must not be identical")
    output = _crop(inter) if inter else [[0]]
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    info = {
        "blue_cells": blue_cells,
        "red_cells": red_cells,
        "blue_shape": blue,
        "red_shape": red,
        "blue_origin": (min(r for r, _ in blue_cells), min(c for _, c in blue_cells)),
        "red_origin": (min(r for r, _ in red_cells), min(c for _, c in red_cells)),
        "intersection": frozenset(inter),
        "intersection_size": len(inter),
        "output": output,
    }
    if profile is None and not errors:
        profile = _classify(result | info)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared normalized-overlap lesson")
    result.update(info)
    result.update({"scene_profile": profile, "errors": errors})
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid); profile = info.get("scene_profile")
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
    return [row[:] for row in info["output"]]


def _dimensions(rng, band):
    bounds = {
        "easy": ((7, 9), (9, 12)),
        "medium": ((9, 12), (11, 14)),
        "hard": ((12, 16), (14, 18)),
    }
    (h1, h2), (w1, w2) = bounds[band]
    return rng.randint(h1, h2), rng.randint(w1, w2)


def _place_shape(grid, shape, color, r0, c0):
    for r, c in shape:
        grid[r0 + r][c0 + c] = color


def _random_polyomino(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(tuple(sorted(cells)))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        candidate = (r + dr, c + dc)
        if 0 <= candidate[0] <= 6 and 0 <= candidate[1] <= 6:
            cells.add(candidate)
    return cells


def _random_non_solid_polyomino(rng, size):
    """Return a connected shape whose cropped mask contains background too."""
    while True:
        cells = _random_polyomino(rng, size)
        height = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        width = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if len(cells) < height * width:
            return cells


def _pair_for_profile(rng, profile):
    if profile == "overlap_l_three":
        full = {(0, 0), (0, 1), (1, 0), (1, 1)}
        missing = rng.choice(tuple(sorted(full)))
        intersection = full - {missing}
        bottom_cols = [c for r, c in intersection if r == 1]
        red_unique = (2, rng.choice(bottom_cols))
        return set(full), set(intersection) | {red_unique}
    if profile == "overlap_t_four":
        full = {(r, c) for r in range(2) for c in range(3)}
        removed = rng.choice((((0, 0), (0, 2)), ((1, 0), (1, 2)),
                              ((0, 0), (1, 2)), ((0, 2), (1, 0))))
        intersection = full - set(removed)
        return set(intersection) | {removed[0]}, set(intersection) | {removed[1]}
    if profile == "overlap_sparse_wide":
        intersection = set(rng.choice((
            ((0, 0), (0, 3), (1, 0)), ((0, 0), (0, 3), (1, 3)),
            ((0, 0), (1, 1), (1, 3)), ((0, 3), (1, 0), (1, 2)),
        )))
        return intersection | {(0, c) for c in range(4)}, intersection | {(1, c) for c in range(4)}
    if profile == "overlap_sparse_tall":
        intersection = set(rng.choice((
            ((0, 0), (3, 0), (0, 1)), ((0, 0), (3, 0), (3, 1)),
            ((0, 0), (1, 1), (3, 1)), ((0, 1), (1, 0), (3, 0)),
        )))
        return intersection | {(r, 0) for r in range(4)}, intersection | {(r, 1) for r in range(4)}
    if profile == "second_shape_subset":
        small = _random_non_solid_polyomino(rng, rng.randint(3, 12))
        attachments = sorted({(r + dr, c + dc) for r, c in small
                              for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                              if 0 <= r + dr <= 7 and 0 <= c + dc <= 7
                              and (r + dr, c + dc) not in small})
        return set(small) | {rng.choice(attachments)}, set(small)
    if profile == "first_shape_subset":
        blue, red = _pair_for_profile(rng, "second_shape_subset")
        return red, blue
    if profile == "large_partial_overlap":
        intersection = _random_non_solid_polyomino(rng, rng.randint(5, 14))
        candidates = sorted({(r + dr, c + dc) for r, c in intersection
                             for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                             if 0 <= r + dr <= 7 and 0 <= c + dc <= 7
                             and (r + dr, c + dc) not in intersection})
        first, second = rng.sample(candidates, 2)
        return set(intersection) | {first}, set(intersection) | {second}
    if profile == "same_row_placement":
        intersection = _random_non_solid_polyomino(rng, rng.randint(3, 14))
        frontier = sorted({(r + dr, c + dc) for r, c in intersection
                           for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 0 <= r + dr <= 7 and 0 <= c + dc <= 7
                           and (r + dr, c + dc) not in intersection})
        first, second = rng.sample(frontier, 2)
        return set(intersection) | {first}, set(intersection) | {second}
    blue, red = _PAIR_TEMPLATES[profile]
    return set(blue), set(red)


def _general_grid(rng, profile, band):
    h, w = _dimensions(rng, band)
    blue, red = _pair_for_profile(rng, profile)
    bh = max(r for r, _ in blue) + 1; bw = max(c for _, c in blue) + 1
    rh = max(r for r, _ in red) + 1; rw = max(c for _, c in red) + 1
    h = max(h, bh, rh if profile == "same_row_placement" else rh + 1)
    w = max(w, bw + rw + 1)
    if profile == "same_row_placement":
        shared_row = rng.randint(0, h - max(bh, rh))
        r1 = r2 = shared_row
    else:
        r1 = rng.randint(0, h - bh)
        red_rows = [row for row in range(h - rh + 1) if row != r1]
        r2 = rng.choice(red_rows)
    c1 = rng.randint(0, max(0, w - bw - rw - 1))
    c2 = rng.randint(c1 + bw + 1, w - rw)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    _place_shape(grid, blue, 1, r1, c1)
    _place_shape(grid, red, 2, r2, c2)
    return grid


def _public_grid(profile):
    return [[int(cell) for cell in row] for row in _PUBLIC_INPUTS[profile]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                      difficulty=difficulty, overrides=overrides)
    fixed_profiles = ("overlap_single_cell", "overlap_vertical_pair", "overlap_horizontal_pair")
    moderate_profiles = ("overlap_l_three", "overlap_t_four", "overlap_sparse_wide", "overlap_sparse_tall")
    varied_profiles = ("second_shape_subset", "first_shape_subset", "large_partial_overlap", "same_row_placement")
    weighted_profiles = (PUBLIC_PROFILES + fixed_profiles + moderate_profiles * 2
                         + varied_profiles * 8)
    profile = context.draw_choice("scene_profile", list(weighted_profiles))
    rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, _band(difficulty))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid); errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors
