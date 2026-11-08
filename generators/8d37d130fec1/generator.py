"""Semantic generator for ARC task 8d37d130fec1.

A framed interior contains sparse fill-color evidence.  Among several colored
glyphs above the frame, select the first glyph whose scaled occupied cells
contain every evidence cell, then return the framed crop filled with the
scaled glyph pattern.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from puzzle_generators.base import gen_ctx

GENERATOR_ID = "8d37d130fec1"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "78df4fde8dc3"
SUMMARY = "Select the top glyph compatible with sparse frame-interior evidence and expand it blockwise inside the cropped frame."
INVARIANTS = [
    "background is literal color 8",
    "the largest non-background object is an exact rectangular frame",
    "interior evidence has one color distinct from background and frame",
    "at least one top 8-connected glyph is scale-compatible with every evidence cell",
    "the first compatible glyph in reading order determines the cropped output",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_test_1",
)
GENERAL_SPECS = {
    "two_first_2x2": (2, 0, ("10", "11"), False),
    "two_last_2x3": (2, 1, ("110", "011"), False),
    "three_middle_3x2": (3, 1, ("10", "11", "01"), False),
    "three_last_3x3": (3, 2, ("010", "111", "010"), False),
    "four_first_3x4": (4, 0, ("1110", "0111", "1010"), False),
    "four_middle_4x3": (4, 2, ("110", "010", "111", "001"), False),
    "five_last_3x3": (5, 4, ("101", "111", "010"), False),
    "ambiguous_first_3x3": (2, 0, ("111", "010", "111"), True),
}
GENERAL_PROFILES = tuple(GENERAL_SPECS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and generalized glyph-selection lessons",
        "valid": "public_train_1|public_train_2|public_train_3|public_test_1|two_first_2x2|two_last_2x3|three_middle_3x2|three_last_3x3|four_first_3x4|four_middle_4x3|five_last_3x3|ambiguous_first_3x3",
    }
}

_PUBLIC_BLOBS = {
    "public_train_1": "888888888888888888888/818182288388844886868/881888288333884486668/881182228883848886888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888999999999999998888/888955555555888898888/888955555555888898888/888955555555888898888/888955555555888898888/888988888888555598888/888988888888555598888/888988888888555598888/888988888888555598888/888988888888888898888/888988888888888898888/888988888888888898888/888988888888888898888/888999999999999998888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888",
    "public_train_2": "888888888888888888888/811182828848899886688/888182288448888986888/811888228844899988668/881188828848888988668/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888333333333338888888/888300000000038888888/888300000000038888888/888300000000038888888/888388888888838888888/888388888888838888888/888388888888838888888/888388888888838888888/888388888888838888888/888388888888838888888/888388888888838888888/888388888888838888888/888388888888838888888/888333333333338888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888",
    "public_train_3": "888888888888888888888/881111828888888888888/888118822228888888888/881111882828888888888/888888888888888888888/888888888888888888888/888888888888888888888/884444444444888888888/884888888884888888888/884888888884888888888/884888888884888888888/884888888884888888888/884888833334888888888/884888833334888888888/884444444444888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888",
    "public_test_1": "888888888888888888888/828228881886868844848/828288111188666884848/882288181886886884448/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/888888888888888888888/889999999999999999998/889888888887777888898/889888888887777888898/889888888887777888898/889888888887777888898/889888888888888888898/889888888888888888898/889888888888888888898/889888888888888888898/889888888888888777798/889888888888888777798/889888888888888777798/889888888888888777798/889999999999999999998",
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in blob.split("/")]
    for name, blob in _PUBLIC_BLOBS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}
_PROFILE_KEYS = {
    (count, index, mask): name
    for name, (count, index, mask, _ambiguous) in GENERAL_SPECS.items()
}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _components(grid, diagonal=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 8 or (r, c) in seen:
                continue
            todo = [(r, c)]
            cells = set()
            while todo:
                rr, cc = todo.pop()
                if (rr, cc) in seen or not (0 <= rr < h and 0 <= cc < w):
                    continue
                if grid[rr][cc] != color:
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                todo.extend((rr + dr, cc + dc) for dr, dc in directions)
            if cells:
                result.append({"color": color, "cells": cells, "bbox": _bbox(cells)})
    return sorted(result, key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))


def _bbox(cells):
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _mask(obj):
    r1, c1, r2, c2 = obj["bbox"]
    return tuple(
        "".join("1" if (r, c) in obj["cells"] else "0" for c in range(c1, c2 + 1))
        for r in range(r1, r2 + 1)
    )


def _frame_cells(r1, c1, r2, c2):
    return {
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    objects4 = _components(grid, diagonal=False)
    if not objects4:
        errors.append("missing frame and glyph objects")
        return result
    frame = max(objects4, key=lambda obj: len(obj["cells"]))
    fr1, fc1, fr2, fc2 = frame["bbox"]
    frame_color = frame["color"]
    if frame["cells"] != _frame_cells(fr1, fc1, fr2, fc2):
        errors.append("largest object must be an exact rectangular frame")
        return result
    inner_h, inner_w = fr2 - fr1 - 1, fc2 - fc1 - 1
    if inner_h <= 0 or inner_w <= 0:
        errors.append("frame must have a non-empty interior")
        return result
    fill_values = [
        grid[r][c] for r in range(fr1 + 1, fr2) for c in range(fc1 + 1, fc2)
        if grid[r][c] not in (8, frame_color)
    ]
    if not fill_values:
        errors.append("frame interior must contain fill evidence")
        return result
    counts = Counter(fill_values)
    fill_color = max(counts, key=lambda value: (counts[value], -fill_values.index(value)))
    if set(fill_values) != {fill_color}:
        errors.append("interior evidence must use exactly one non-frame/non-background color")
    existing_fill = [
        (r - fr1 - 1, c - fc1 - 1)
        for r in range(fr1 + 1, fr2) for c in range(fc1 + 1, fc2)
        if grid[r][c] == fill_color
    ]

    top_glyphs = []
    for obj in _components(grid, diagonal=True):
        r1, c1, r2, c2 = obj["bbox"]
        if r2 < fr1 and obj["color"] not in (8, frame_color, fill_color):
            obj = dict(obj)
            obj["mask"] = _mask(obj)
            top_glyphs.append(obj)
    top_glyphs.sort(key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    candidates = []
    for index, glyph in enumerate(top_glyphs):
        mask = glyph["mask"]
        gh, gw = len(mask), len(mask[0])
        if inner_h % gh or inner_w % gw:
            continue
        bh, bw = inner_h // gh, inner_w // gw
        if all(mask[rr // bh][cc // bw] == "1" for rr, cc in existing_fill):
            candidates.append((index, glyph, bh, bw))
    if not candidates:
        errors.append("no top glyph is compatible with all interior evidence")
        return result
    selected_index, glyph, bh, bw = candidates[0]
    mask = glyph["mask"]
    out_h, out_w = inner_h + 2, inner_w + 2
    output = []
    for r in range(out_h):
        row = []
        for c in range(out_w):
            if r in (0, out_h - 1) or c in (0, out_w - 1):
                row.append(frame_color)
            elif mask[(r - 1) // bh][(c - 1) // bw] == "1":
                row.append(fill_color)
            else:
                row.append(8)
        output.append(row)

    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None and not errors:
        profile = _PROFILE_KEYS.get((len(top_glyphs), selected_index, mask))
    if profile not in SCENE_PROFILES:
        errors.append("glyph-count/selection/mask tuple does not match a declared profile")
    result.update({
        "frame": frame,
        "frame_bbox": (fr1, fc1, fr2, fc2),
        "frame_color": frame_color,
        "inner_shape": (inner_h, inner_w),
        "fill_color": fill_color,
        "existing_fill": existing_fill,
        "top_glyphs": top_glyphs,
        "candidate_indices": tuple(index for index, *_ in candidates),
        "selected_index": selected_index,
        "selected_mask": mask,
        "block_shape": (bh, bw),
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def rule_mirror(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def _connected8(mask):
    cells = {(r, c) for r, row in enumerate(mask) for c, value in enumerate(row) if value == "1"}
    if not cells:
        return False
    todo, seen = [next(iter(cells))], set()
    while todo:
        cell = todo.pop()
        if cell in seen or cell not in cells:
            continue
        seen.add(cell)
        r, c = cell
        todo.extend((r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
    return seen == cells


def _full_bbox(mask):
    return (
        "1" in mask[0] and "1" in mask[-1]
        and any(row[0] == "1" for row in mask)
        and any(row[-1] == "1" for row in mask)
    )


@lru_cache(maxsize=None)
def _decoys(target, count):
    gh, gw = len(target), len(target[0])
    target_bits = {(r, c) for r, row in enumerate(target) for c, value in enumerate(row) if value == "1"}
    masks = []
    for bits in range(1, 1 << (gh * gw)):
        mask = tuple(
            "".join("1" if bits & (1 << (r * gw + c)) else "0" for c in range(gw))
            for r in range(gh)
        )
        cells = {(r, c) for r, row in enumerate(mask) for c, value in enumerate(row) if value == "1"}
        if mask != target and _connected8(mask) and _full_bbox(mask) and target_bits - cells:
            masks.append(mask)
    masks.sort(key=lambda mask: (sum(row.count("1") for row in mask), mask))
    if len(masks) < count:
        raise ValueError("not enough connected decoy masks")
    return masks[:count]


def _draw_mask(grid, top, left, mask, color):
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            if value == "1":
                grid[top + r][left + c] = color


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _general(rng, profile, band):
    glyph_count, selected_index, target, ambiguous = GENERAL_SPECS[profile]
    gh, gw = len(target), len(target[0])
    decoys = _decoys(target, glyph_count - 1)
    masks = []
    decoy_index = 0
    for index in range(glyph_count):
        if index == selected_index:
            masks.append(target)
        else:
            masks.append(decoys[decoy_index])
            decoy_index += 1
    target_cells = [(r, c) for r, row in enumerate(target) for c, value in enumerate(row) if value == "1"]
    if ambiguous:
        other = masks[1]
        logical_seeds = [cell for cell in target_cells if other[cell[0]][cell[1]] == "1"][:1]
        if not logical_seeds:
            raise ValueError("ambiguous decoy has no shared target cell")
    else:
        logical_seeds = []
        for index, mask in enumerate(masks):
            if index == selected_index:
                continue
            witness = next(cell for cell in target_cells if mask[cell[0]][cell[1]] == "0")
            if witness not in logical_seeds:
                logical_seeds.append(witness)
        remaining = [cell for cell in target_cells if cell not in logical_seeds]
        rng.shuffle(remaining)
        logical_seeds.extend(remaining[: rng.randint(0, max(0, len(remaining) // 2))])

    scale_ranges = {"easy": (1, 2), "medium": (2, 3), "hard": (3, 4)}
    lo, hi = scale_ranges[band]
    bh, bw = rng.randint(lo, hi), rng.randint(lo, hi)
    inner_h, inner_w = gh * bh, gw * bw
    frame_h, frame_w = inner_h + 2, inner_w + 2
    gap = 1
    glyph_span = glyph_count * gw + (glyph_count - 1) * gap
    frame_top = gh + 4 + rng.randint(0, 1)
    total_h = frame_top + frame_h + rng.randint(1, 2)
    total_w = max(glyph_span, frame_w) + 2
    grid = [[8] * total_w for _ in range(total_h)]
    palette = rng.sample((0, 1, 2, 3, 4, 5, 6, 7, 9), glyph_count + 2)
    frame_color, fill_color = palette[0], palette[1]
    glyph_colors = palette[2:]
    for index, mask in enumerate(masks):
        _draw_mask(grid, 1, 1 + index * (gw + gap), mask, glyph_colors[index])
    frame_left = rng.randint(1, total_w - frame_w - 1)
    fr1, fc1 = frame_top, frame_left
    fr2, fc2 = fr1 + frame_h - 1, fc1 + frame_w - 1
    for r, c in _frame_cells(fr1, fc1, fr2, fc2):
        grid[r][c] = frame_color
    for gr, gc in logical_seeds:
        # One witness cell identifies the occupied logical block.  Keeping the
        # clue sparse prevents it from competing with the rectangular frame as
        # the scene's largest object at hard scales.
        dr = rng.randrange(bh)
        dc = rng.randrange(bw)
        grid[fr1 + 1 + gr * bh + dr][fc1 + 1 + gc * bw + dc] = fill_color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=band, overrides=overrides,
    )
    weighted = list(PUBLIC_PROFILES) + [profile for profile in GENERAL_PROFILES for _ in range(3)]
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
