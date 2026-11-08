"""Semantic generator for ARC task cddbee92b2f3.

Select the first full-height column of color 5.  Copy every nonzero,
non-5 cell strictly left of that guide to its in-bounds horizontal mirror,
preserving all original content and overwriting any occupied target cell.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "cddbee92b2f3"
TASK_ID = "cddbee92b2f3"
VERSION = "3.0.0"
RULE_HASH = "44af655891ad"
SUMMARY = "Mirror eligible cells left of the first full-height color-5 guide, preserving originals and clipping off-canvas targets."
INVARIANTS = [
    "literal color 0 is background and a guide column is entirely color 5",
    "the first (leftmost) full-height guide is selected when several exist",
    "only nonzero non-5 cells strictly left of the selected guide are sources",
    "each source is copied to column 2*guide_col-source_col when in bounds",
    "original cells and unrelated right-side content are preserved",
    "a mirrored source overwrites pre-existing content at its target",
    "sources whose reflected columns are off-canvas have no effect",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "offset_axis",
    "multicolor_pattern",
    "clustered_shape",
    "edge_rows",
    "existing_right_preserved",
    "existing_right_overwritten",
    "out_of_bounds_sources",
    "multiple_guides_first",
    "literal_five_ignored",
    "near_and_far_sources",
    "dense_pattern",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and eleven observable mirror lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|offset_axis|multicolor_pattern|clustered_shape|edge_rows|existing_right_preserved|existing_right_overwritten|out_of_bounds_sources|multiple_guides_first|literal_five_ignored|near_and_far_sources|dense_pattern",
    }
}

_PUBLIC_ROWS = {
    "public_1": "000050000/020050000/007050000/000050000/000050000/030050000/000050000/000050000",
    "public_2": "00000500000/00400500000/00000500000/08000500000/00000500000/00000500000/00002500000/00060500000/00000500000",
    "public_3": "0000500000/0900500000/0003500000/0000500000/0000500000/0070500000/0000500000/0000500000",
    "public_4": "00000500000/00000500000/02000500000/00000500000/00080500000/00000500000/00000500000/00004500000/00600500000/00000500000",
    "public_5": "00000500000/00700500000/00000500000/04000500000/00000500000/00000500000/00002500000/00000500000/00090500000/00000500000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _guide_columns(grid):
    return [col for col in range(len(grid[0])) if all(row[col] == 5 for row in grid)]


def _eligible_sources(grid, guide_col):
    return [(row, col) for row in range(len(grid)) for col in range(guide_col) if grid[row][col] not in (0, 5)]


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    guides = _guide_columns(grid)
    output = [list(row) for row in grid]
    if not guides:
        return output
    guide_col = guides[0]
    height, width = len(grid), len(grid[0])
    for row, col in _eligible_sources(grid, guide_col):
        mirror_col = 2 * guide_col - col
        if 0 <= row < height and 0 <= mirror_col < width:
            output[row][mirror_col] = grid[row][col]
    return output


def _general_profile(grid, guides, sources, in_bounds, out_of_bounds):
    height, width = len(grid), len(grid[0])
    guide_col = guides[0]
    if len(guides) > 1:
        return "multiple_guides_first"
    if out_of_bounds:
        return "out_of_bounds_sources"
    if any(grid[row][col] == 5 for row in range(height) for col in range(guide_col)):
        return "literal_five_ignored"
    targets = {(row, 2 * guide_col - col) for row, col in in_bounds}
    right_content = {
        (row, col)
        for row in range(height)
        for col in range(guide_col + 1, width)
        if grid[row][col] != 0 and col not in guides
    }
    if right_content:
        return "existing_right_overwritten" if right_content & targets else "existing_right_preserved"
    if len({grid[row][col] for row, col in sources}) >= 5:
        return "multicolor_pattern"
    if len(sources) >= 10:
        return "dense_pattern"
    if any(abs(row - rr) + abs(col - cc) == 1 for row, col in sources for rr, cc in sources if (row, col) != (rr, cc)):
        return "clustered_shape"
    if {row for row, _ in sources} >= {0, height - 1}:
        return "edge_rows"
    if guide_col != width // 2:
        return "offset_axis"
    if len({guide_col - col for _, col in sources}) >= 3:
        return "near_and_far_sources"
    return "near_and_far_sources"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    guides = _guide_columns(grid)
    if not guides:
        errors.append("expected at least one full-height color-5 guide")
        return result
    guide_col = guides[0]
    sources = _eligible_sources(grid, guide_col)
    in_bounds = [(row, col) for row, col in sources if 0 <= 2 * guide_col - col < width]
    out_of_bounds = [cell for cell in sources if cell not in in_bounds]
    if len(sources) < 3:
        errors.append("expected at least three eligible left-side sources")
    if len(in_bounds) < 3:
        errors.append("expected at least three visible in-bounds reflections")
    if len(guides) > 2:
        errors.append("expected at most two full-height guides")
    output = rule_mirror(grid)
    changed = sum(a != b for row_a, row_b in zip(grid, output) for a, b in zip(row_a, row_b))
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public or _general_profile(grid, guides, sources, in_bounds, out_of_bounds)
    if not public and changed / (height * width) < 0.01:
        errors.append("reflections must visibly change at least one percent of the canvas")
    if profile not in SCENE_PROFILES:
        errors.append("scene does not match a declared semantic profile")
    result.update({
        "guides": guides,
        "guide_col": guide_col,
        "sources": sources,
        "in_bounds_sources": in_bounds,
        "out_of_bounds_sources": out_of_bounds,
        "targets": {(row, 2 * guide_col - col) for row, col in in_bounds},
        "output": output,
        "changed": changed,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _choose_positions(rng, candidates, mandatory, target, *, separated):
    best = []
    for _ in range(80):
        selected = list(dict.fromkeys(mandatory))
        shuffled = list(candidates)
        rng.shuffle(shuffled)
        for cell in shuffled:
            if cell in selected:
                continue
            if separated and any(abs(cell[0] - row) + abs(cell[1] - col) <= 1 for row, col in selected):
                continue
            selected.append(cell)
            if len(selected) >= target:
                return selected
        if len(selected) > len(best):
            best = selected
    raise AssertionError(f"insufficient source positions for lesson ({len(best)}/{target})")


def _general_scene(ctx, profile):
    ranges = {None: (10, 18), "easy": (8, 12), "medium": (12, 18), "hard": (18, 24)}
    low, high = ranges[ctx.difficulty]
    height = ctx.draw_int("canvas_height", low, high)
    width = ctx.draw_int("canvas_width", low, high)
    rng = ctx.draw_rng("geometry")
    grid = _blank(height, width)

    if profile == "offset_axis":
        guide_col = max(3, width // 2 - 2)
    elif profile == "out_of_bounds_sources":
        guide_col = min(width - 3, width // 2 + 2)
    elif profile == "multiple_guides_first":
        guide_col = max(2, width // 3)
    else:
        guide_col = width // 2
    guides = [guide_col]
    if profile == "multiple_guides_first":
        guides.append(min(width - 2, 2 * guide_col))
    for col in guides:
        for row in range(height):
            grid[row][col] = 5

    legal_min = max(0, 2 * guide_col - width + 1)
    legal = [(row, col) for row in range(height) for col in range(legal_min, guide_col)]
    middle = height // 2
    mandatory = []
    if profile == "clustered_shape":
        mandatory = [(middle, guide_col - 1), (middle, guide_col - 2), (min(height - 1, middle + 1), guide_col - 1)]
    elif profile == "edge_rows":
        mandatory = [(0, guide_col - 1), (height - 1, guide_col - 2)]
    elif profile == "near_and_far_sources":
        mandatory = [(max(0, middle - 3), guide_col - 1), (middle, guide_col - 2), (min(height - 1, middle + 3), max(legal_min, guide_col - 4))]
    elif profile == "out_of_bounds_sources":
        legal_edge = max(0, 2 * guide_col - width + 1)
        mandatory = [
            (middle, 0),
            (max(0, middle - 2), 1),
            (min(height - 1, middle + 2), guide_col - 1),
            (max(0, middle - 3), legal_edge),
            (min(height - 1, middle + 3), min(guide_col - 1, legal_edge + 1)),
        ]
    elif profile == "multiple_guides_first":
        mandatory = [(middle, 0), (max(0, middle - 2), guide_col - 1), (min(height - 1, middle + 2), guide_col - 2)]

    target = min(9, max(5, math.ceil(height * width * 0.018)))
    if profile == "out_of_bounds_sources":
        target = min(11, target + 2)
    if profile == "dense_pattern":
        target = max(10, math.ceil(height * width * 0.035))
    candidates = list(legal)
    if profile != "edge_rows":
        candidates = [(row, col) for row, col in candidates if 0 < row < height - 1]
    separated = profile not in ("clustered_shape", "dense_pattern")
    positions = _choose_positions(rng, candidates, mandatory, target, separated=separated)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 8)
    if profile == "multicolor_pattern":
        colors = palette[: max(5, min(len(positions), 8))]
    else:
        colors = palette[: max(2, min(4, len(positions)))]
    for index, (row, col) in enumerate(positions):
        grid[row][col] = colors[index % len(colors)]

    if profile == "literal_five_ignored":
        occupied = set(positions)
        cell = next((cell for cell in legal if cell not in occupied), None)
        if cell is None:
            raise AssertionError("no room for literal-five decoy")
        grid[cell[0]][cell[1]] = 5
    elif profile in ("existing_right_preserved", "existing_right_overwritten"):
        targets = {(row, 2 * guide_col - col) for row, col in positions if 0 <= 2 * guide_col - col < width}
        if profile == "existing_right_overwritten":
            row, col = sorted(targets)[0]
        else:
            row, col = next(
                (cell for cell in ((r, c) for r in range(height) for c in range(guide_col + 1, width)) if cell not in targets),
                (0, width - 1),
            )
        grid[row][col] = next(color for color in palette if color != grid[row][2 * guide_col - col] if 0 <= 2 * guide_col - col < width) if profile == "existing_right_overwritten" else palette[-1]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES + GENERAL_PROFILES)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
