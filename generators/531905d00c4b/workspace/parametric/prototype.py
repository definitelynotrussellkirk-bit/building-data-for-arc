"""Input-dependent reflection while decoding a prototype mosaic.

Python labels are claims, independently replayed by native protected Racket
qualification. The selected canonical program is preserved byte-for-byte.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK = "531905d00c4b"
POLICIES = ("canonical", "larger_left", "larger_right")
DEFAULT = {"reflection_policy": "canonical"}

# Keep the pure reused reconstruction inside the native source closure.
_path = HERE / "grid.py"
_spec = importlib.util.spec_from_file_location("_531905d00c4b_parametric_grid", _path)
reference = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reference)


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"reflection_policy"}:
        raise ValueError("settings must contain only reflection_policy")
    policy = settings["reflection_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"reflection_policy must be one of {POLICIES}")
    return policy


def _integer(value, minimum, maximum, name):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an exact integer in {minimum}..{maximum}")
    return value


def canonical_program():
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


def _replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Canonical source changed; review the parametric transformation")
    return text.replace(old, new, 1)


def program(settings):
    policy = validate_settings(settings)
    source = canonical_program()
    if policy == "canonical":
        return source
    # Keep tight crops in the library. Each occurrence is reflected before
    # common-frame padding, so one color can behave differently by context.
    source = _replace_once(source,
        "(s17b-pad-top-left (s17b-object-crop lib-area obj) ph pw)",
        "(s17b-object-crop lib-area obj)")
    helpers = (
        "(define (s17p-mass tile) (length (nonzero-cells tile))) "
        "(define (s17p-neighbor-mass lib index r c) "
        "(if (in-bounds? r c (rows index) (cols index)) "
        "(s17p-mass (s17b-lookup-grid lib (at index r c))) 0)) "
    )
    source = _replace_once(source, "(let* ((sep ", helpers + "(let* ((sep ")
    comparison = ">" if policy == "larger_left" else "<"
    expression = (
        "(let* ((tile (s17b-lookup-grid lib (at index-area r c))) "
        "(left-mass (s17p-neighbor-mass lib index-area r (- c 1))) "
        "(right-mass (s17p-neighbor-mass lib index-area r (+ c 1))) "
        f"(oriented (if ({comparison} left-mass right-mass) (flip-lr tile) tile))) "
        "(s17b-pad-top-left oriented ph pw))"
    )
    return _replace_once(source, "(s17b-lookup-grid lib (at index-area r c))", expression)


def parse(grid):
    parts = reference.parse(grid)
    parts["crops"] = {
        color: reference._crop_component(parts["library"], color, cells)
        for color, cells in parts["components"]
    }
    parts["masses"] = {color: len(cells) for color, cells in parts["components"]}
    return parts


def intermediate(grid):
    """Private diagnostic only: the resolved neighbor masses and decisions."""
    parts = parse(grid)
    index, masses = parts["index"], parts["masses"]
    contexts = []
    for r, row in enumerate(index):
        for c, token in enumerate(row):
            left = masses[row[c - 1]] if c > 0 else 0
            right = masses[row[c + 1]] if c + 1 < len(row) else 0
            contexts.append({"position": [r, c], "token": token,
                "left_mass": left, "right_mass": right,
                "larger_left": left > right, "larger_right": left < right})
    return {"component_cells": {str(k): v for k, v in sorted(masses.items())},
            "index": deepcopy(index), "contexts": contexts}


def label(grid, settings):
    policy = validate_settings(settings)
    if policy == "canonical":
        return reference.intended_output(grid)
    parts = parse(grid)
    index, crops, masses = parts["index"], parts["crops"], parts["masses"]
    ph, pw = parts["tile_h"], parts["tile_w"]
    out = [[0] * (len(index[0]) * pw) for _ in range(len(index) * ph)]
    for r, row in enumerate(index):
        for c, token in enumerate(row):
            left = masses[row[c - 1]] if c else 0
            right = masses[row[c + 1]] if c + 1 < len(row) else 0
            reflect = left > right if policy == "larger_left" else left < right
            crop = crops[token]
            oriented = [list(reversed(line)) for line in crop] if reflect else crop
            for rr, line in enumerate(oriented):
                out[r * ph + rr][c * pw:c * pw + len(line)] = line
    return out


def _rng(seed, split, slot):
    digest = hashlib.sha256(f"{TASK}/neighbor-mass-v1/{seed}/{split}/{slot}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _shape(height, width, color, density, rng):
    """Connected asymmetric crops with exact bounding boxes and varied mass."""
    if density == "sparse":
        # A randomized monotone path varies geometry at fixed occupied mass.
        # Every row/column is touched; target shapes with h,w>1 are asymmetric.
        steps = [(1, 0)] * (height - 1) + [(0, 1)] * (width - 1)
        rng.shuffle(steps)
        tile = [[0] * width for _ in range(height)]
        r = c = 0
        tile[r][c] = color
        for dr, dc in steps:
            r += dr
            c += dc
            tile[r][c] = color
    elif density == "dense":
        # Keep a full vertical/horizontal backbone, then vary removed cells.
        # A fixed removal count preserves the intended neighbor ordering.
        candidates = [(r, c) for r in range(height - 1) for c in range(1, width)]
        tile = None
        for _ in range(32):
            removed = set(rng.sample(candidates, height - 1))
            candidate = [[0 if (r, c) in removed else color for c in range(width)]
                         for r in range(height)]
            if (len(reference._components(candidate)) == 1
                    and candidate != [line[::-1] for line in candidate]):
                tile = candidate
                break
        if tile is None:
            tile = [[color if c < width - 1 or r == height - 1 else 0
                     for c in range(width)] for r in range(height)]
    else:
        raise ValueError("unknown shape density")
    if rng.randrange(2):
        tile = [list(reversed(row)) for row in tile]
    if rng.randrange(2):
        tile = list(reversed(tile))
    return tile


def _put(grid, crop, row, col):
    for rr, line in enumerate(crop):
        grid[row + rr][col:col + len(line)] = line


def _index(rng, colors, height, width, equal_mass_pair=False):
    low, target, high, distractor = colors
    result = [[rng.choice(colors) for _ in range(width)] for _ in range(height)]
    # Both directions for the SAME target; equal-size neighbor boxes have
    # different occupied masses. No setting information enters the sampler.
    result[0][:3] = [low, target, high]
    result[1][:3] = [high, target, low]
    if width >= 5:
        result[0][3:] = [target, low] + result[0][5:]
        result[1][3:] = [target, high] + result[1][5:]
    if height > 2:
        result[2][:3] = [low, target, low]  # explicit equal-neighbor tie
        result[-1][-1] = distractor
        if equal_mass_pair and width >= 5:
            # Target/other have different colors and crop shapes but equal
            # occupied mass. Both high occurrences must remain unreflected.
            result[2][:5] = [target, high, distractor, high, target]
    return result


def _ordinary_grid(rng, height, width, index_h, index_w, shifted=True, padding=True,
                   palette_order=None):
    colors = rng.sample(range(1, 10), 4)
    if palette_order is not None and (colors[0] < colors[2]) != palette_order:
        colors[0], colors[2] = colors[2], colors[0]
    # Low/high have identical bounding boxes. The target is narrower and
    # shorter: reflecting the padded tile is observably the wrong operation.
    low = _shape(height, width, colors[0], "sparse", rng)
    target = _shape(height - 1, width - 1, colors[1], "sparse", rng)
    high = _shape(height, width, colors[2], "dense", rng)
    # Its cell count equals the target's h+w-3, with a different crop shape.
    other = _shape(height - 2, width, colors[3], "sparse", rng)
    crops = [low, target, high, other]
    order = list(range(4))
    rng.shuffle(order)
    gap = 1
    library_w = sum(len(crops[i][0]) for i in order) + 3 * gap
    top_pad = 1 + rng.randrange(2) if padding else 0
    left_pad = 1 + rng.randrange(2) if padding else 0
    grid = [[0] * max(library_w, left_pad + index_w)
            for _ in range(height + 1 + top_pad + index_h)]
    col = 0
    for i in order:
        crop = crops[i]
        offset = height - len(crop) if shifted and i == 1 else rng.randrange(height - len(crop) + 1)
        _put(grid, crop, offset, col)
        col += len(crop[0]) + gap
    for r, row in enumerate(_index(rng, colors, index_h, index_w, equal_mass_pair=True)):
        grid[height + 1 + top_pad + r][left_pad:left_pad + index_w] = row
    return grid


def _stress_grid(rng):
    colors = rng.sample(range(1, 10), 4)
    # Four separate 6x6 prototypes genuinely span the 24-row library. Their
    # union has no blank row, even without any full-library-height object.
    thicknesses = [2, 3, 5, 4]  # masses: low16, target21, high31, other26
    crops = []
    for color, thickness in zip(colors, thicknesses):
        crop = [[color if c < thickness or r == 5 else 0 for c in range(6)]
                for r in range(6)]
        if rng.randrange(2):
            crop = [list(reversed(row)) for row in crop]
        if rng.randrange(2):
            crop = list(reversed(crop))
        crops.append(crop)
    order = list(range(4))
    rng.shuffle(order)
    grid = [[0] * 30 for _ in range(30)]
    for slot, index in enumerate(order):
        _put(grid, crops[index], slot * 6, slot * 8)
    for r, row in enumerate(_index(rng, colors, 5, 5)):
        grid[25 + r][:5] = row
    return grid


def sample_inputs(seed, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    # Split/slot seeds make prefixes invariant to requested counts and setting.
    demo_profiles = [(4, 4, 2, 5), (5, 4, 3, 5), (3, 3, 3, 5),
                     (4, 5, 4, 5), (5, 3, 3, 4), (6, 4, 4, 5)]
    query_profiles = [(3, 3, 2, 3), (4, 5, 4, 4), (6, 6, 5, 5)]
    train = [_ordinary_grid(_rng(seed, "demo", i), *demo_profiles[i],
                            palette_order=bool(i % 2)) for i in range(demos)]
    test = [_ordinary_grid(_rng(seed, "query", i), *query_profiles[i],
                          shifted=True, padding=(i != 0))
            if i < 3 else _stress_grid(_rng(seed, "query", i)) for i in range(queries)]
    return train, test


def generate(seed, settings, demos, queries):
    validate_settings(settings)
    train, test = sample_inputs(seed, demos, queries)
    return {"train": [{"input": g, "output": label(g, settings)} for g in train],
            "test": [{"input": g, "output": label(g, settings)} for g in test],
            "program_solution": program(settings)}


def public_turn(episode, query_index=0):
    """One controller-selected query; no answers, future inputs or count hint."""
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return deepcopy({"train": [{"input": p["input"], "output": p["output"]}
                               for p in episode["train"]],
                     "test": [{"input": episode["test"][query_index]["input"]}]})
