"""Semantic generator for ARC task b705ef68a501.

Count maroon cells in row zero to obtain a one-based rank.  Exclude maroon
components and components touching row zero, sort the remaining monochrome
4-connected components by size, row, column, height, width, and color, then
return the exact bounding-box crop of the selected component.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "b705ef68a501"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "998a777867df"
SUMMARY = "Use the row-zero maroon count to select the kth component in canonical size-and-position order."
INVARIANTS = [
    "k is the number of color-9 cells in row zero",
    "color-9 components and components touching row zero are excluded",
    "candidates sort by size, top, left, height, width, then color",
    "the output is the exact selected-component bbox crop with other cells zeroed",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "rank_smallest",
    "rank_middle",
    "rank_largest",
    "tie_by_row",
    "tie_by_column",
    "tie_by_height",
    "filter_color_nine",
    "filter_row_zero",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and eight observable rank/filter lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "9000000000000/0000000000000/0220003300000/0200003300000/0000000000000/0000000000400/0000000004440/0000000000400/0000000000000",
    "public_2": "99000000000000/00000000000000/00222000000000/00200000066600/00000000060600/05500000066600/05500000000000/05000000000000/00000000000000/00000000000000",
    "public_3": "9990000000000/0000000000000/0333000400000/0030004440000/0000000400000/0000000077770/0000000070070/0000000077770/0000000000000",
    "public_4": "990000000000000/000000000000000/000000000000000/002200005550000/002200005050000/066666000000000/060606000000000/060606000000000/060606000000000/066666000000000/000000000000000",
    "public_5": "99900000000000/00000000000000/02200044000000/02000044000000/00000000666660/00000000606060/00000000606060/00000000606060/00000000666660/00000000000000",
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
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _objects(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        seed = min(unseen)
        color = grid[seed[0]][seed[1]]
        stack = [seed]
        cells = set()
        while stack:
            cell = stack.pop()
            if cell not in unseen or grid[cell[0]][cell[1]] != color:
                continue
            unseen.remove(cell)
            cells.add(cell)
            row, col = cell
            stack.extend(
                neighbor
                for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                if neighbor in unseen
            )
        result.append({"color": color, "cells": cells})
    return result


def _feature(obj):
    rows = [row for row, _ in obj["cells"]]
    cols = [col for _, col in obj["cells"]]
    r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    return {
        "color": obj["color"],
        "cells": obj["cells"],
        "size": len(obj["cells"]),
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "height": height,
        "width": width,
        "key": (len(obj["cells"]), r1, c1, height, width, obj["color"]),
    }


def _candidate(feature):
    return feature["color"] != 9 and all(row > 0 for row, _ in feature["cells"])


def _crop_selected(grid, selected):
    cells = selected["cells"]
    return [
        [grid[row][col] if (row, col) in cells else 0 for col in range(selected["c1"], selected["c2"] + 1)]
        for row in range(selected["r1"], selected["r2"] + 1)
    ]


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rank = sum(value == 9 for value in grid[0])
    candidates = sorted((_feature(obj) for obj in _objects(grid) if _candidate(_feature(obj))), key=lambda f: f["key"])
    if not 1 <= rank <= len(candidates):
        raise ValueError(f"header rank {rank} is outside 1..{len(candidates)}")
    return _crop_selected(grid, candidates[rank - 1])


def _tie_dimension(candidates):
    groups = defaultdict(list)
    for candidate in candidates:
        groups[candidate["size"]].append(candidate)
    for group in groups.values():
        if len(group) < 2:
            continue
        if len({item["r1"] for item in group}) > 1:
            return "row"
        if len({item["c1"] for item in group}) > 1:
            return "column"
        if len({item["height"] for item in group}) > 1:
            return "height"
        if len({item["width"] for item in group}) > 1:
            return "width"
        if len({item["color"] for item in group}) > 1:
            return "color"
        return "identical"
    return None


def _general_profile(features, candidates, rank):
    if any(feature["color"] != 9 and feature["r1"] == 0 for feature in features):
        return "filter_row_zero"
    if any(feature["color"] == 9 and feature["r2"] > 0 for feature in features):
        return "filter_color_nine"
    tie = _tie_dimension(candidates)
    if tie in ("row", "column", "height"):
        return f"tie_by_{tie}"
    if tie is not None:
        return None
    if rank == 1:
        return "rank_smallest"
    if rank == len(candidates):
        return "rank_largest"
    return "rank_middle"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    if not any(value == 0 for row in grid for value in row):
        errors.append("expected literal-zero background")
    features = [_feature(obj) for obj in _objects(grid)]
    candidates = sorted((feature for feature in features if _candidate(feature)), key=lambda f: f["key"])
    rank = sum(value == 9 for value in grid[0])
    if not 1 <= rank <= len(candidates):
        errors.append(f"header rank must be in 1..candidate-count; got {rank} for {len(candidates)}")
        return result
    if not 3 <= len(candidates) <= 5:
        errors.append(f"expected 3..5 selectable components; got {len(candidates)}")
    selected = candidates[rank - 1]
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_profile(features, candidates, rank)
    if profile not in SCENE_PROFILES:
        errors.append("rank/filter structure does not match a declared scene profile")
    output = _crop_selected(grid, selected)
    result.update(
        {
            "rank": rank,
            "features": features,
            "candidates": candidates,
            "candidate_count": len(candidates),
            "candidate_sizes": [candidate["size"] for candidate in candidates],
            "selected": selected,
            "selected_index": rank - 1,
            "selected_key": selected["key"],
            "tie_dimension": _tie_dimension(candidates),
            "excluded_color_nine": sum(feature["color"] == 9 and feature["r2"] > 0 for feature in features),
            "excluded_row_zero": sum(feature["color"] != 9 and feature["r1"] == 0 for feature in features),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    return profile if profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _poly(rng, size, maximum=5):
    for _ in range(80):
        cells = {(maximum // 2, maximum // 2)}
        while len(cells) < size:
            frontier = {
                (row + dr, col + dc)
                for row, col in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 0 <= row + dr < maximum and 0 <= col + dc < maximum and (row + dr, col + dc) not in cells
            }
            if not frontier:
                break
            cells.add(rng.choice(sorted(frontier)))
        if len(cells) == size:
            r0 = min(row for row, _ in cells)
            c0 = min(col for _, col in cells)
            normalized = {(row - r0, col - c0) for row, col in cells}
            height, width = _shape_bbox(normalized)
            if len(normalized) < height * width:
                return normalized
    raise ValueError(f"could not construct connected polyomino of size {size}")


def _shape_bbox(cells):
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _boxes_clear(box, boxes):
    return all(
        box[2] + 1 < other[0]
        or other[2] + 1 < box[0]
        or box[3] + 1 < other[1]
        or other[3] + 1 < box[1]
        for other in boxes
    )


def _paint(grid, cells, color, top, left):
    for row, col in cells:
        if grid[top + row][left + col] != 0:
            return False
    for row, col in cells:
        grid[top + row][left + col] = color
    return True


def _place(rng, grid, cells, color, boxes, *, fixed_top=None, different_top=None):
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _shape_bbox(cells)
    positions = [
        (top, left)
        for top in range(2, height - shape_h)
        for left in range(1, width - shape_w)
        if (fixed_top is None or top == fixed_top) and (different_top is None or top != different_top)
    ]
    rng.shuffle(positions)
    for top, left in positions:
        box = top, left, top + shape_h - 1, left + shape_w - 1
        if _boxes_clear(box, boxes) and _paint(grid, cells, color, top, left):
            boxes.append(box)
            return box
    return None


_HEIGHT_TIE_A = {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)}
_HEIGHT_TIE_B = {(0, 3), (1, 3), (2, 2), (2, 3), (3, 0), (3, 1), (3, 2)}


def _candidate_count(band):
    return {"easy": 3, "medium": 4, "hard": 5}[band]


def _rank_scene(rng, profile, band, height, width, colors):
    count = _candidate_count(band)
    sizes = sorted(rng.sample(range(3, 14), count))
    grid = [[0] * width for _ in range(height)]
    boxes = []
    for size, color in zip(sizes, colors):
        if _place(rng, grid, _poly(rng, size), color, boxes) is None:
            return None
    rank = 1 if profile == "rank_smallest" else count if profile == "rank_largest" else rng.randint(2, count - 1)
    return grid, rank


def _tie_scene(rng, profile, band, height, width, colors):
    grid = [[0] * width for _ in range(height)]
    boxes = []
    tied = []
    if profile == "tie_by_height":
        top = rng.randint(2, height - 5)
        left = rng.randint(1, width - 6)
        if not _paint(grid, _HEIGHT_TIE_A, colors[0], top, left):
            return None
        if not _paint(grid, _HEIGHT_TIE_B, colors[1], top, left):
            return None
        boxes.append((top, left, top + 3, left + 3))
        tied = [(_HEIGHT_TIE_A, colors[0]), (_HEIGHT_TIE_B, colors[1])]
    else:
        shape_a, shape_b = _poly(rng, 6), _poly(rng, 6)
        first = _place(rng, grid, shape_a, colors[0], boxes)
        if first is None:
            return None
        second = _place(
            rng,
            grid,
            shape_b,
            colors[1],
            boxes,
            fixed_top=first[0] if profile == "tie_by_column" else None,
            different_top=first[0] if profile == "tie_by_row" else None,
        )
        if second is None:
            return None
        tied = [(shape_a, colors[0]), (shape_b, colors[1])]
    other_sizes = [3, 10] + ([13] if band == "hard" else [])
    for index, size in enumerate(other_sizes, start=2):
        if _place(rng, grid, _poly(rng, size), colors[index], boxes) is None:
            return None
    candidates = sorted((_feature(obj) for obj in _objects(grid) if _candidate(_feature(obj))), key=lambda f: f["key"])
    tied_size = 7 if profile == "tie_by_height" else 6
    tied_indices = [index + 1 for index, candidate in enumerate(candidates) if candidate["size"] == tied_size]
    rank = rng.choice(tied_indices)
    return grid, rank


def _filter_scene(rng, profile, band, height, width, colors):
    count = _candidate_count(band)
    sizes = sorted(rng.sample(range(3, 14), count))
    grid = [[0] * width for _ in range(height)]
    boxes = []
    for size, color in zip(sizes, colors):
        if _place(rng, grid, _poly(rng, size), color, boxes) is None:
            return None
    rank = rng.randint(1, count)
    if profile == "filter_color_nine":
        if _place(rng, grid, _poly(rng, 7), 9, boxes) is None:
            return None
    else:
        left = rng.randint(1, width - 4)
        decoy = {(0, 0), (1, 0), (1, 1), (2, 1)}
        if not _paint(grid, decoy, colors[-1], 0, left):
            return None
        boxes.append((0, left, 2, left + 1))
    return grid, rank


def _add_header(rng, grid, rank):
    available = [col for col, value in enumerate(grid[0]) if value == 0]
    if len(available) < rank:
        return False
    for col in rng.sample(available, rank):
        grid[0][col] = 9
    return True


def _general(rng, profile, band):
    ranges = {"easy": (13, 17), "medium": (17, 22), "hard": (22, 28)}
    low, high = ranges[band]
    for _ in range(50):
        height, width = rng.randint(low, high), rng.randint(low, high)
        colors = list(range(1, 9))
        rng.shuffle(colors)
        if profile.startswith("rank_"):
            built = _rank_scene(rng, profile, band, height, width, colors)
        elif profile.startswith("tie_"):
            built = _tie_scene(rng, profile, band, height, width, colors)
        else:
            built = _filter_scene(rng, profile, band, height, width, colors)
        if built is None:
            continue
        grid, rank = built
        if not _add_header(rng, grid, rank):
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise ValueError(f"could not construct scene profile {profile!r}")


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = requested or ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) + [name for name in GENERAL_PROFILES for _ in range(4)],
    )
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
