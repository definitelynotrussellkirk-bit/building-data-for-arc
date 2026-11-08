"""Semantic generator for ARC task 93ca517eac25.

Among the blue components, exactly one has the minority vertical-symmetry
status.  Recolor that complete component red while preserving the canvas and
all unrelated colored distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "93ca517eac25"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "4a154ae48e66"
SUMMARY = "Recolor the blue component whose normalized vertical-symmetry status is unique among all blue components."
INVARIANTS = [
    "background is literal color 0",
    "three through six 4-connected blue components are present",
    "exactly one blue component has the minority vertical-symmetry status",
    "the minority component alone changes from blue 1 to red 2",
    "unrelated non-blue colored distractors are preserved",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3",
    "public_train_4", "public_test_1",
)
GENERAL_SPECS = {
    "three_one_symmetric": (3, True),
    "three_one_asymmetric": (3, False),
    "four_one_symmetric": (4, True),
    "four_one_asymmetric": (4, False),
    "five_one_symmetric": (5, True),
    "five_one_asymmetric": (5, False),
    "six_one_symmetric": (6, True),
    "six_one_asymmetric": (6, False),
}
GENERAL_PROFILES = tuple(GENERAL_SPECS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and generalized minority-symmetry lessons",
        "valid": "public_train_1|public_train_2|public_train_3|public_train_4|public_test_1|three_one_symmetric|three_one_asymmetric|four_one_symmetric|four_one_asymmetric|five_one_symmetric|five_one_asymmetric|six_one_symmetric|six_one_asymmetric",
    }
}

_PUBLIC_BLOBS = {
    "public_train_1": "00001000000/00011100000/08801070010/08800070011/00001000000/00001000000/00001110000/00000000000/00066000000/00000000000/01000000000/01100000000/00000000000",
    "public_train_2": "000000000000000/000000000000000/000000000000000/007007710000000/000007711000000/000000000000000/000000000001000/000000000001000/000000000001110/000010000000000/110111000000000/110000000000000/100000000009000",
    "public_train_3": "00000010000/00000111000/00000010000/00000000000/00000100000/00001110000/00000100000/00005500000/00000000011/10100000011/11100000010/00000000000/00000060000",
    "public_train_4": "00000000000000/00000000010000/00000000110000/00000100100000/00001110000000/01000000080000/11000000080000/10000000000000/00000000000000/00000000000000/00066000100000/00066000100000/00000000111000/00000000000000",
    "public_test_1": "0000000000000/0080000000000/1000000000000/1000101000000/1110111000000/0000000000101/0000000000111/0000000000000/0000000100000/0000001110000/0000000000000/0000000000000",
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in blob.split("/")]
    for name, blob in _PUBLIC_BLOBS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}
_PROFILE_KEYS = {
    spec: name for name, spec in GENERAL_SPECS.items()
}

_SYMMETRIC_MASKS = (
    ("010", "111"),
    ("010", "111", "010"),
    ("101", "111", "101"),
    ("101", "101", "111"),
    ("111", "010", "010"),
    ("11", "11"),
    ("1", "1", "1", "1"),
    ("010", "111", "101"),
)
_ASYMMETRIC_MASKS = (
    ("10", "10", "11"),
    ("01", "01", "11"),
    ("110", "011"),
    ("011", "110"),
    ("100", "110", "011"),
    ("11", "10", "10"),
    ("100", "111", "001"),
    ("10", "11"),
)
_DISTRACTOR_MASKS = (
    ("1",), ("11",), ("1", "1"), ("11", "11"), ("10", "11"),
)


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


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            todo = [(r, c)]
            cells = set()
            while todo:
                rr, cc = todo.pop()
                if (
                    not 0 <= rr < h or not 0 <= cc < w
                    or (rr, cc) in seen or grid[rr][cc] != color
                ):
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                todo.extend(((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)))
            result.append(cells)
    return result


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _vertically_symmetric(cells):
    normalized = _normalize(cells)
    width = max(c for _, c in normalized) + 1
    return normalized == frozenset((r, width - 1 - c) for r, c in normalized)


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    if any(value == 2 for row in grid for value in row):
        errors.append("input must not contain the output marker color 2")
    blue_components = _components(grid, 1)
    flags = tuple(_vertically_symmetric(cells) for cells in blue_components)
    true_count = sum(flags)
    false_count = len(flags) - true_count
    if not 3 <= len(blue_components) <= 6:
        errors.append("scene must contain three through six blue components")
    if not (true_count > 0 and false_count > 0 and min(true_count, false_count) == 1):
        errors.append("exactly one blue component must have the minority vertical-symmetry status")
        return result
    target_is_symmetric = true_count == 1
    target_index = flags.index(target_is_symmetric)
    target = blue_components[target_index]
    output = [list(row) for row in grid]
    for r, c in target:
        output[r][c] = 2
    distractor_colors = sorted({value for row in grid for value in row if value not in (0, 1, 2)})
    if not distractor_colors:
        errors.append("scene must contain at least one unrelated colored distractor")
    signature = tuple(map(tuple, grid))
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None and not errors:
        profile = _PROFILE_KEYS.get((len(blue_components), target_is_symmetric))
    if profile not in SCENE_PROFILES:
        errors.append("component-count/minority-status tuple does not match a declared profile")
    result.update({
        "blue_components": blue_components,
        "symmetry_flags": flags,
        "symmetric_count": true_count,
        "asymmetric_count": false_count,
        "target_is_symmetric": target_is_symmetric,
        "target_index": target_index,
        "target_cells": target,
        "distractor_colors": distractor_colors,
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


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _mask_cells(mask):
    return {(r, c) for r, row in enumerate(mask) for c, value in enumerate(row) if value == "1"}


def _place_mask(grid, mask, color, rng, blue_occupied, *, separate_blue):
    h, w = len(grid), len(grid[0])
    cells = _mask_cells(mask)
    mh, mw = len(mask), len(mask[0])
    candidates = [(r, c) for r in range(h - mh + 1) for c in range(w - mw + 1)]
    rng.shuffle(candidates)
    for top, left in candidates:
        placed = {(top + r, left + c) for r, c in cells}
        if any(grid[r][c] != 0 for r, c in placed):
            continue
        if separate_blue and any(
            neighbor in blue_occupied
            for r, c in placed
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        ):
            continue
        for r, c in placed:
            grid[r][c] = color
        return placed
    raise ValueError("unable to place separated component")


def _general(rng, profile, band):
    component_count, target_is_symmetric = GENERAL_SPECS[profile]
    ranges = {"easy": (12, 14), "medium": (13, 16), "hard": (15, 18)}
    lo, hi = ranges[band]
    h, w = rng.randint(lo, hi), rng.randint(lo, hi + 1)
    grid = [[0] * w for _ in range(h)]
    flags = [target_is_symmetric] + [not target_is_symmetric] * (component_count - 1)
    rng.shuffle(flags)
    blue_occupied = set()
    for symmetric in flags:
        mask = rng.choice(_SYMMETRIC_MASKS if symmetric else _ASYMMETRIC_MASKS)
        placed = _place_mask(grid, mask, 1, rng, blue_occupied, separate_blue=True)
        blue_occupied.update(placed)
    distractor_count = {"easy": 1, "medium": 2, "hard": 3}[band]
    colors = rng.sample((3, 4, 5, 6, 7, 8, 9), distractor_count)
    for color in colors:
        mask = rng.choice(_DISTRACTOR_MASKS)
        _place_mask(grid, mask, color, rng, blue_occupied, separate_blue=False)
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
