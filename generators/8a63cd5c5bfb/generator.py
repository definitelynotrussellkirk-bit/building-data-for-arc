"""Semantic generator for ARC task 8a63cd5c5bfb.

Two green cells define opposite corners of an axis-aligned rectangle.  Paint
only its empty border cells cyan, preserving both green corners and every
pre-existing distractor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "8a63cd5c5bfb"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "4e08f58254c0"
SUMMARY = "Draw a cyan outline through two opposite green corners while preserving every occupied cell."
INVARIANTS = [
    "exactly two green cells define opposite rectangle corners",
    "only empty cells on the implied rectangle border become cyan",
    "green corners and all outside, border, and interior distractors are preserved",
    "all non-border background cells remain zero",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_ROLE_COUNTS = {
    "no_distractor": (0, 0, 0),
    "outside_one": (1, 0, 0),
    "outside_pair": (2, 0, 0),
    "border_one": (0, 1, 0),
    "border_pair": (0, 2, 0),
    "interior_one": (0, 0, 1),
    "interior_pair": (0, 0, 2),
    "mixed_three": (1, 1, 1),
}
GENERAL_PROFILES = tuple(GENERAL_ROLE_COUNTS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and generalized distractor-role lessons",
        "valid": "public_train_1|public_train_2|public_train_3|public_train_4|public_test_1|no_distractor|outside_one|outside_pair|border_one|border_pair|interior_one|interior_pair|mixed_three",
    }
}

_PUBLIC_ROWS = {
    "public_train_1": (
        "000000002", "030000000", "000000000", "000000000",
        "000000000", "000030000", "000000000", "000000000",
    ),
    "public_train_2": (
        "0000000000", "0000000000", "0000003000", "0000000000",
        "0000000000", "0000000000", "0000000000", "0000000030",
        "7000000000",
    ),
    "public_train_3": (
        "00000000000", "00000000300", "00000000000", "00000000000",
        "00030000000", "00000000000", "00000000004",
    ),
    "public_train_4": (
        "500000000", "000000000", "000000000", "003000000",
        "000000000", "000000000", "000000000", "000000000",
        "000000300", "000000000",
    ),
    "public_test_1": (
        "0000000000", "0300000000", "0000000000", "0000000000",
        "0000000000", "0000000000", "0000000300", "0000000009",
    ),
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in rows]
    for name, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}
_COUNTS_TO_PROFILE = {counts: name for name, counts in GENERAL_ROLE_COUNTS.items()}


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


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    greens = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if len(greens) != 2:
        errors.append(f"expected exactly two green corner markers, found {len(greens)}")
        return result
    (ar, ac), (br, bc) = greens
    r0, r1, c0, c1 = min(ar, br), max(ar, br), min(ac, bc), max(ac, bc)
    if r1 - r0 < 2 or c1 - c0 < 2:
        errors.append("green markers must define a rectangle with an interior")
        return result
    if {greens[0], greens[1]} not in (
        {(r0, c0), (r1, c1)}, {(r0, c1), (r1, c0)}
    ):
        errors.append("green markers must occupy opposite rectangle corners")

    outside, border, interior = [], [], []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 3):
                continue
            if not (r0 <= r <= r1 and c0 <= c <= c1):
                outside.append((r, c, value))
            elif r in (r0, r1) or c in (c0, c1):
                border.append((r, c, value))
            else:
                interior.append((r, c, value))
    role_counts = (len(outside), len(border), len(interior))
    output = [list(row) for row in grid]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (r in (r0, r1) or c in (c0, c1)) and output[r][c] == 0:
                output[r][c] = 8

    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None and not errors:
        profile = _COUNTS_TO_PROFILE.get(role_counts)
    if profile not in SCENE_PROFILES:
        errors.append(f"distractor role counts {role_counts!r} do not match a declared profile")
    result.update({
        "greens": tuple(greens),
        "rectangle": (r0, c0, r1, c1),
        "diagonal": "main" if {greens[0], greens[1]} == {(r0, c0), (r1, c1)} else "anti",
        "outside_distractors": outside,
        "border_distractors": border,
        "interior_distractors": interior,
        "role_counts": role_counts,
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


def _general(rng, profile, band):
    ranges = {
        "easy": ((7, 9), (8, 10)),
        "medium": ((8, 12), (9, 13)),
        "hard": ((11, 16), (12, 17)),
    }
    (h0, h1), (w0, w1) = ranges[band]
    h, w = rng.randint(h0, h1), rng.randint(w0, w1)
    grid = [[0] * w for _ in range(h)]
    requested = GENERAL_ROLE_COUNTS[profile]
    for _ in range(200):
        r0, r1 = sorted(rng.sample(range(h), 2))
        c0, c1 = sorted(rng.sample(range(w), 2))
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        corners = ((r0, c0), (r1, c1)) if rng.choice((False, True)) else ((r0, c1), (r1, c0))
        corner_set = set(corners)
        outside = [
            (r, c) for r in range(h) for c in range(w)
            if not (r0 <= r <= r1 and c0 <= c <= c1)
        ]
        border = [
            (r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if (r in (r0, r1) or c in (c0, c1)) and (r, c) not in corner_set
        ]
        interior = [
            (r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)
        ]
        pools = (outside, border, interior)
        if all(len(pool) >= count for pool, count in zip(pools, requested)):
            break
    else:
        raise ValueError("could not construct requested rectangle profile")
    for r, c in corners:
        grid[r][c] = 3
    palette = (1, 2, 4, 5, 6, 7, 8, 9)
    if profile in ("outside_pair", "border_pair", "interior_pair"):
        shared_color = rng.choice(palette)
    else:
        shared_color = None
    for pool, count in zip(pools, requested):
        for r, c in rng.sample(pool, count):
            grid[r][c] = shared_color if shared_color is not None else rng.choice(palette)
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
