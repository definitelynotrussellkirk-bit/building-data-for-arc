"""Generator for ``cd29a4f28d02`` — colored corner pairs to outlines.

Each non-background color appears exactly twice.  The two cells are opposite
corners of an axis-aligned rectangle; the answer is a fresh zero grid with the
outline of every rectangle painted in its pair color.

The ordinary distribution keeps a strong canonical-profile prior while also
varying translation, palette, endpoint slant, border contact, and rectangle
morphology.  Every scene contains two independent colors and at least one
rectangle with a real interior, so solid-fill, one-global-box, identity, and
positive-diagonal-only shortcuts are falsifiable.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cd29a4f28d02"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "709391cb135e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.08

SUMMARY = (
    "A 7..10 by 8..10 zero-background grid contains exactly two distinct "
    "nonzero colors, each in exactly two cells at different rows and columns. "
    "Each same-color pair is the pair of opposite corners of a rectangle; the "
    "two rectangle bounding boxes are disjoint and at least one rectangle has "
    "a nonempty interior.  On a fresh zero grid of the same size, draw each "
    "rectangle's four border edges in its pair color and leave every interior "
    "cell zero."
)

INVARIANTS = [
    "exactly two distinct nonzero colors, each appearing exactly twice",
    "each pair occupies distinct rows and distinct columns",
    "pair bounding boxes are disjoint",
    "at least one rectangle is at least 3x3, so outline differs from solid fill",
    "output is a fresh same-size zero grid with both colored outlines",
]

PALETTE_KINDS = ("low", "high", "mixed")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 7..10", "valid": "7..10"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 8..10", "valid": "8..10"},
    "palette_kind": {
        "type": "str",
        "default": "rng low|high|mixed",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Linked empirical profiles from every canonical train and held-out test input.
# Colors, translation, border contact, and diagonal slant are lawful nuisances;
# dimensions and the multiset of pair-bbox morphologies remain linked.
_CANONICAL_PROFILES: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {
    (8, 9): ((3, 3), (5, 4)),
    (9, 9): ((4, 4), (5, 4)),
    (7, 10): ((3, 2), (5, 5)),
    (10, 8): ((4, 3), (5, 4)),
    (9, 10): ((6, 3), (6, 5)),
}
_CANONICAL_SIGNATURES = {
    (h, w, tuple(sorted(sizes)))
    for (h, w), sizes in _CANONICAL_PROFILES.items()
}

SLANT_PROFILES = ("positive", "negative", "mixed")
SCHEDULE_PROFILES = SLANT_PROFILES


def _scheduled_slant(sample_index: int) -> str:
    return SLANT_PROFILES[int(sample_index) % len(SLANT_PROFILES)]


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _scheduled_slant(sample_index)


def _positions(h: int, w: int, size: tuple[int, int]):
    bh, bw = size
    return [
        (r0, c0, r0 + bh - 1, c0 + bw - 1)
        for r0 in range(h - bh + 1)
        for c0 in range(w - bw + 1)
    ]


def _boxes_overlap(a, b) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _touches_border(box, h: int, w: int) -> bool:
    r0, c0, r1, c1 = box
    return r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1


def _placement_pairs(
    h: int,
    w: int,
    sizes: tuple[tuple[int, int], tuple[int, int]],
    contact_mode: str,
):
    first = _positions(h, w, sizes[0])
    second = _positions(h, w, sizes[1])
    all_pairs = [(a, b) for a in first for b in second if not _boxes_overlap(a, b)]
    if not all_pairs:
        return []

    def matches(pair) -> bool:
        ta = _touches_border(pair[0], h, w)
        tb = _touches_border(pair[1], h, w)
        if contact_mode == "touching":
            return ta or tb
        if contact_mode == "interior":
            return not ta and not tb
        if contact_mode == "mixed":
            return ta != tb
        return True

    preferred = [pair for pair in all_pairs if matches(pair)]
    return preferred or all_pairs


def _choose_generalized_sizes(h: int, w: int, rng):
    legal = [
        (bh, bw)
        for bh in range(3, min(6, h) + 1)
        for bw in range(2, min(5, w) + 1)
    ]
    canonical = _CANONICAL_PROFILES.get((h, w))
    for _ in range(240):
        a = rng.choice(legal)
        if rng.randrange(3) == 0:
            thin = [size for size in legal if size[1] == 2]
            b = rng.choice(thin or legal)
        else:
            b = rng.choice(legal)
        sizes = (a, b)
        if not any(bh >= 3 and bw >= 3 for bh, bw in sizes):
            continue
        if canonical is not None and tuple(sorted(sizes)) == tuple(sorted(canonical)):
            continue
        if _placement_pairs(h, w, sizes, "any"):
            return sizes
    fallback = ((3, 3), (3, 2))
    if not _placement_pairs(h, w, fallback, "any"):
        raise RuntimeError(f"no lawful two-rectangle layout fits {h}x{w}")
    return fallback


def _choose_colors(palette_kind: str, rng) -> tuple[int, int]:
    low = (1, 2, 3, 4)
    high = (5, 6, 7, 8, 9)
    if palette_kind == "low":
        return tuple(rng.sample(low, 2))
    if palette_kind == "high":
        return tuple(rng.sample(high, 2))
    return rng.choice(low), rng.choice(high)


def _slants_for_scene(kind: str) -> tuple[str, str]:
    if kind == "positive":
        return "positive", "positive"
    if kind == "negative":
        return "negative", "negative"
    return "positive", "negative"


def _endpoints(box, slant: str):
    r0, c0, r1, c1 = box
    if slant == "positive":
        return (r0, c0), (r1, c1)
    return (r0, c1), (r1, c0)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 7, 10)
    w = ctx.draw_int_diff("grid_w", 8, 10)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    layout_rng = ctx.draw_rng("layout")
    # Easy draws keep every reachable official morphology because that band
    # has only one canonical dimension profile.  Medium/hard alternate exact
    # and generalized morphology so every band still exercises thin and thick
    # rectangle branches while retaining strong canonical support.
    canonical_prior = (h, w) in _CANONICAL_PROFILES and (
        difficulty == "easy" or int(sample_index) % 2 == 0
    )
    if canonical_prior:
        sizes = _CANONICAL_PROFILES[(h, w)]
    else:
        sizes = _choose_generalized_sizes(h, w, layout_rng)

    # Keep color/shape assignment from becoming a reading-order shortcut.
    sizes = list(sizes)
    layout_rng.shuffle(sizes)
    sizes_tuple = (sizes[0], sizes[1])
    contact_mode = ("touching", "interior", "mixed")[int(sample_index) % 3]
    placements = _placement_pairs(h, w, sizes_tuple, contact_mode)
    if not placements:
        raise RuntimeError(f"failed to place {sizes_tuple!r} in {h}x{w}")
    boxes = layout_rng.choice(placements)

    colors = list(_choose_colors(palette_kind, ctx.draw_rng("palette")))
    layout_rng.shuffle(colors)
    slants = _slants_for_scene(_scheduled_slant(sample_index))

    grid = full_grid(h, w, 0)
    for color, box, slant in zip(colors, boxes, slants):
        for r, c in _endpoints(box, slant):
            grid[r][c] = color
    return grid


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 7 <= h <= 10:
        errors.append(f"grid height {h} outside 7..10")
    if not 8 <= w <= 10:
        errors.append(f"grid width {w} outside 8..10")

    cells_by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                continue
            if value != 0:
                cells_by_color[value].append((r, c))
    if any("invalid ARC color" in error for error in errors):
        return {"errors": errors}

    if len(cells_by_color) != 2:
        errors.append(
            f"expected exactly two nonzero colors, got {len(cells_by_color)}"
        )

    pairs = []
    for color, cells in sorted(cells_by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} must appear exactly twice, got {len(cells)}")
            continue
        ordered = sorted(cells)
        (r0, c_at_r0), (r1, c_at_r1) = ordered
        if r0 == r1 or c_at_r0 == c_at_r1:
            errors.append(f"color {color} endpoints must differ in row and column")
            continue
        c0, c1 = sorted((c_at_r0, c_at_r1))
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        if not 3 <= bh <= 6:
            errors.append(f"color {color} bbox height {bh} outside 3..6")
        if not 2 <= bw <= 5:
            errors.append(f"color {color} bbox width {bw} outside 2..5")
        slant = "positive" if c_at_r1 > c_at_r0 else "negative"
        pairs.append(
            {
                "color": color,
                "cells": tuple(cells),
                "box": (r0, c0, r1, c1),
                "size": (bh, bw),
                "slant": slant,
            }
        )

    if len(pairs) == 2 and _boxes_overlap(pairs[0]["box"], pairs[1]["box"]):
        errors.append("the two rectangle bounding boxes must be disjoint")
    if len(pairs) == 2 and not any(
        pair["size"][0] >= 3 and pair["size"][1] >= 3 for pair in pairs
    ):
        errors.append("at least one rectangle must have a nonempty interior")

    signature = None
    if len(pairs) == 2:
        signature = (h, w, tuple(sorted(pair["size"] for pair in pairs)))
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "pairs": pairs,
        "signature": signature,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def _palette_kind(colors) -> str:
    colors = tuple(colors)
    if all(color <= 4 for color in colors):
        return "low"
    if all(color >= 5 for color in colors):
        return "high"
    return "mixed"


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "palette_kind": _palette_kind(pair["color"] for pair in analysis["pairs"]),
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    pairs = analysis["pairs"]
    slants = tuple(pair["slant"] for pair in pairs)
    return {
        **observe_overrides(grid),
        "linked_profile": analysis["signature"],
        "strict_canonical": analysis["signature"] in _CANONICAL_SIGNATURES,
        "has_positive_slant": "positive" in slants,
        "has_negative_slant": "negative" in slants,
        "mixed_slants": len(set(slants)) == 2,
        "has_thin_rectangle": any(pair["size"][1] == 2 for pair in pairs),
        "has_interior_rectangle": any(
            pair["size"][0] >= 3 and pair["size"][1] >= 3 for pair in pairs
        ),
        "touches_border": any(
            _touches_border(pair["box"], analysis["grid_h"], analysis["grid_w"])
            for pair in pairs
        ),
        "two_independent_colors": len(pairs) == 2,
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    if analysis["signature"] not in _CANONICAL_SIGNATURES:
        return [f"linked profile {analysis['signature']!r} is not canonical"]
    return []


def _outline_cells(box):
    r0, c0, r1, c1 = box
    return {
        *((r0, c) for c in range(c0, c1 + 1)),
        *((r1, c) for c in range(c0, c1 + 1)),
        *((r, c0) for r in range(r0, r1 + 1)),
        *((r, c1) for r in range(r0, r1 + 1)),
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyze(grid)
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        for r, c in _outline_cells(pair["box"]):
            out[r][c] = pair["color"]
    return out


def _solid_fill(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        r0, c0, r1, c1 = pair["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = pair["color"]
    return out


def _positive_slant_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        cells = pair["cells"]
        if pair["slant"] == "positive":
            paint = _outline_cells(pair["box"])
        else:
            paint = set(cells)
        for r, c in paint:
            out[r][c] = pair["color"]
    return out


def _single_global_bbox(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    all_cells = [cell for pair in analysis["pairs"] for cell in pair["cells"]]
    r0 = min(r for r, _ in all_cells)
    r1 = max(r for r, _ in all_cells)
    c0 = min(c for _, c in all_cells)
    c1 = max(c for _, c in all_cells)
    color = min(pair["color"] for pair in analysis["pairs"])
    for r, c in _outline_cells((r0, c0, r1, c1)):
        out[r][c] = color
    return out


def _l_path_pairs(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        (r0, c0), (r1, c1) = sorted(pair["cells"])
        for c in range(min(c0, c1), max(c0, c1) + 1):
            out[r0][c] = pair["color"]
        for r in range(r0, r1 + 1):
            out[r][c1] = pair["color"]
    return out


def _identity(grid):
    return [row[:] for row in grid]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "solid_fill_each_pair_bbox": _solid_fill,
    "positive_slant_pairs_only": _positive_slant_only,
    "one_global_bbox": _single_global_bbox,
    "l_path_between_each_pair": _l_path_pairs,
    "identity": _identity,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "positive_slant_pairs_only": _positive_slant_only,
}


def _witness(grid, key: str) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(obs[key])


SEMANTIC_WITNESSES = {
    "strict_canonical_profile": lambda grid: _witness(grid, "strict_canonical"),
    "positive_slant": lambda grid: _witness(grid, "has_positive_slant"),
    "negative_slant": lambda grid: _witness(grid, "has_negative_slant"),
    "mixed_slants": lambda grid: _witness(grid, "mixed_slants"),
    "thin_rectangle": lambda grid: _witness(grid, "has_thin_rectangle"),
    "interior_rectangle": lambda grid: _witness(grid, "has_interior_rectangle"),
    "border_contact": lambda grid: _witness(grid, "touches_border"),
    "two_independent_colors": lambda grid: _witness(grid, "two_independent_colors"),
}
WITNESS_RIVALS = {
    "strict_canonical_profile": ["solid_fill_each_pair_bbox"],
    "positive_slant": ["solid_fill_each_pair_bbox"],
    "negative_slant": ["positive_slant_pairs_only"],
    "mixed_slants": ["positive_slant_pairs_only"],
    "thin_rectangle": ["solid_fill_each_pair_bbox"],
    "interior_rectangle": ["solid_fill_each_pair_bbox"],
    "border_contact": ["solid_fill_each_pair_bbox"],
    "two_independent_colors": ["solid_fill_each_pair_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful two-pair rectangle scene"]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the outline rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            alternative = competitor(query_input)
            if alternative != query_truth:
                reasons.append(
                    f"demos still fit competitor {name!r}, which changes the query answer"
                )
    return reasons
