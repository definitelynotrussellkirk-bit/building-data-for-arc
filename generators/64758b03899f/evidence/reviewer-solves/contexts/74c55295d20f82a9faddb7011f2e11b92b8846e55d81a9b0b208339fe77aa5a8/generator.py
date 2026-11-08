"""Constructive sampler for task 64758b03899f — stamp the color-5 mask.

The unchanged Racket authority extracts every color-5 cell, normalizes that
mask by its bounding-box top-left, clears the input, and stamps the normalized
mask at each nonzero non-5 marker using the marker's own color.

The sampler covers all canonical mask families plus masks whose bounding-box
origin is empty.  The latter are essential: every canonical demonstration has
a 5-cell at the bounding-box origin, so the plausible shortcut "use the first
5-cell as origin" fits all canonical pairs unless the curriculum supplies a
counterexample.
"""
from __future__ import annotations

from collections.abc import Callable
from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "64758b03899f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "daa4a7279074"

SUMMARY = (
    "Place one connected color-5 mask and two or three isolated, distinctly "
    "colored anchor cells on a zero-background grid. Normalize the mask by its "
    "bounding-box top-left, clear the input, and stamp that mask at every anchor "
    "using the anchor's color. Canonical mask families and hollow-origin masks "
    "are scheduled twice per four slots so every five-pair query rotation retains "
    "a first-cell-origin counterexample; bbox-fill, marker-only, first-anchor, "
    "keep-source, and wrong-color shortcuts are observable."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4

INVARIANTS = [
    "grid is 9..13 by 12..18 with colors 0..9",
    "color 5 forms exactly one connected declared mask family",
    "the mask bounding-box origin is away from grid coordinate (0, 0)",
    "there are exactly 2 or 3 isolated anchors in distinct non-{0,5} colors",
    "every normalized stamp fits fully in bounds and stamp footprints are disjoint",
    "source cells and all projected stamp footprints are disjoint",
]

# The first four shapes are the four distinct canonical training families.
# Hollow-origin shapes deliberately omit normalized (0, 0).
MASKS: dict[str, tuple[tuple[int, int], ...]] = {
    "diag4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "tee4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "corner3": ((0, 0), (0, 1), (1, 0)),
    "cup5": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "hollow_corner3": ((0, 1), (1, 0), (1, 1)),
    "hollow_stair4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "hook5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "hollow_fork5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
}
MASK_FAMILIES = (
    "diag4",
    "tee4",
    "corner3",
    "cup5",
    "hollow_corner3",
    "hollow_stair4",
    "hook5",
    "hollow_fork5",
)
CANONICAL_MASK_FAMILIES = ("diag4", "tee4", "corner3", "cup5")
HOLLOW_ORIGIN_FAMILIES = ("hollow_corner3", "hollow_stair4", "hollow_fork5")

# Exact canonical size/palette profiles: n=2 gives palette size 4; n=3 gives 5.
_CANONICAL_TWO_ANCHOR_SIZES = ((10, 14), (11, 15), (10, 16))
_CANONICAL_THREE_ANCHOR_SIZES = ((9, 13), (11, 15))
_CANONICAL_SIZES = _CANONICAL_TWO_ANCHOR_SIZES + _CANONICAL_THREE_ANCHOR_SIZES

SCHEDULE_PROFILES = (
    "canonical_two",
    "hollow_origin",
    "canonical_three",
    "hollow_broad",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile or difficulty-weighted draw",
        "valid": "9..13",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile or difficulty-weighted draw",
        "valid": "12..18",
    },
    "mask_family": {
        "type": "str",
        "default": "scheduled canonical/hollow/broad family",
        "valid": "|".join(MASK_FAMILIES),
    },
    "n_anchors": {
        "type": "int",
        "default": "scheduled 2 or 3",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive slots contain a hollow-origin counterexample."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (("grid_h", 9, 13), ("grid_w", 12, 18), ("n_anchors", 2, 3)):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")

    family = overrides.get("mask_family")
    if family is not None and type(family) is not str:
        raise ValueError("mask_family must be a string")
    if family is not None and family not in MASKS:
        raise ValueError(f"unknown mask_family {family!r}")


def _draw_int_axis(ctx, label: str, lo: int, hi: int, default: int | None) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    if default is not None:
        return int(ctx.draw_choice(label, (default,)))
    return ctx.draw_int_strict(label, lo, hi)


def _draw_choice_axis(ctx, label: str, options: tuple[str, ...], defaults: tuple[str, ...]) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, defaults))


def _difficulty_ranges(difficulty: str | None) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if difficulty == "easy":
        return tuple(range(9, 11)), tuple(range(12, 15))
    if difficulty == "hard":
        return tuple(range(11, 14)), tuple(range(15, 19))
    return tuple(range(9, 14)), tuple(range(12, 19))


def _scheduled_defaults(ctx, profile: str, difficulty: str | None):
    """Return defaults without narrowing the legal override domains."""
    if profile == "canonical_two":
        h, w = ctx.draw_rng("canonical_size").choice(_CANONICAL_TWO_ANCHOR_SIZES)
        families = CANONICAL_MASK_FAMILIES
        n_anchors = 2
    elif profile == "canonical_three":
        h, w = ctx.draw_rng("canonical_size").choice(_CANONICAL_THREE_ANCHOR_SIZES)
        families = CANONICAL_MASK_FAMILIES
        n_anchors = 3
    elif profile == "hollow_origin":
        h, w = ctx.draw_rng("canonical_size").choice(_CANONICAL_SIZES)
        families = HOLLOW_ORIGIN_FAMILIES
        n_anchors = 2 + (int(ctx.draw_rng("scheduled_anchor_count").random() >= 0.5))
    elif profile == "hollow_broad":
        hs, ws = _difficulty_ranges(difficulty)
        h = ctx.draw_rng("scheduled_grid_h").choice(hs)
        w = ctx.draw_rng("scheduled_grid_w").choice(ws)
        families = HOLLOW_ORIGIN_FAMILIES
        n_anchors = ctx.draw_rng("scheduled_anchor_count").choice((2, 3))
    else:
        raise ValueError(f"unknown schedule profile {profile!r}")
    return h, w, families, n_anchors


def _shape_size(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _stamp(anchor: tuple[int, int], shape: tuple[tuple[int, int], ...]) -> frozenset[tuple[int, int]]:
    ar, ac = anchor
    return frozenset((ar + dr, ac + dc) for dr, dc in shape)


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _compatible_anchor(
    anchor: tuple[int, int],
    footprint: frozenset[tuple[int, int]],
    selected: tuple[tuple[tuple[int, int], frozenset[tuple[int, int]]], ...],
) -> bool:
    for other_anchor, other_footprint in selected:
        if _manhattan(anchor, other_anchor) <= 1:
            return False
        if footprint & other_footprint:
            return False
        if anchor in other_footprint or other_anchor in footprint:
            return False
    return True


def _select_anchors(
    candidates: tuple[tuple[tuple[int, int], frozenset[tuple[int, int]]], ...],
    n_anchors: int,
) -> tuple[tuple[int, int], ...] | None:
    """Deterministic first-solution backtracking over an already shuffled pool."""
    def extend(start: int, selected):
        if len(selected) == n_anchors:
            return selected
        if len(candidates) - start < n_anchors - len(selected):
            return None
        for index in range(start, len(candidates)):
            anchor, footprint = candidates[index]
            if not _compatible_anchor(anchor, footprint, selected):
                continue
            result = extend(index + 1, selected + ((anchor, footprint),))
            if result is not None:
                return result
        return None

    result = extend(0, ())
    if result is None:
        return None
    return tuple(anchor for anchor, _ in result)


def _construct_scene(ctx, h: int, w: int, shape, n_anchors: int) -> tuple[list[list[int]], tuple[int, ...]]:
    sh, sw = _shape_size(shape)
    source_origins = [(r, c) for r in range(1, h - sh + 1) for c in range(1, w - sw + 1)]
    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(source_origins)

    for source_origin in source_origins:
        source_cells = _stamp(source_origin, shape)
        candidates = []
        for r in range(h - sh + 1):
            for c in range(w - sw + 1):
                anchor = (r, c)
                footprint = _stamp(anchor, shape)
                if footprint & source_cells:
                    continue
                if anchor in source_cells:
                    continue
                if any(_manhattan(anchor, cell) <= 1 for cell in source_cells):
                    continue
                candidates.append((anchor, footprint))
        layout_rng.shuffle(candidates)
        anchors = _select_anchors(tuple(candidates), n_anchors)
        if anchors is None:
            continue

        # Scheduled extremes guarantee full non-{0,5} palette support across a
        # four-slot lesson while retaining keyed randomness for the other colors.
        profile = schedule_profile(ctx.seed, ctx.sample_index, ctx.difficulty)
        legal = [1, 2, 3, 4, 6, 7, 8, 9]
        color_rng = ctx.draw_rng("anchor_colors")
        if profile == "hollow_origin":
            colors = [1]
        elif profile == "canonical_three":
            colors = [9]
        else:
            colors = []
        remaining = [color for color in legal if color not in colors]
        colors.extend(color_rng.sample(remaining, n_anchors - len(colors)))
        colors = tuple(colors)

        grid = full_grid(h, w, 0)
        for r, c in source_cells:
            grid[r][c] = 5
        for (r, c), color in zip(anchors, colors):
            grid[r][c] = color
        return grid, colors

    raise RuntimeError("constructive placement failed for a documented axis combination")


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
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, family_defaults, default_n = _scheduled_defaults(ctx, profile, difficulty)

    h = _draw_int_axis(ctx, "grid_h", 9, 13, default_h)
    w = _draw_int_axis(ctx, "grid_w", 12, 18, default_w)
    family = _draw_choice_axis(ctx, "mask_family", MASK_FAMILIES, tuple(family_defaults))
    n_anchors = _draw_int_axis(ctx, "n_anchors", 2, 3, default_n)

    grid, _ = _construct_scene(ctx, h, w, MASKS[family], n_anchors)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced malformed scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {name: ctx.axis_value(name) for name in AXES}
    if observed != expected:
        raise AssertionError(f"observable axes drifted: expected {expected!r}, observed {observed!r}")
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return None
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return None
    return len(grid), w


def _component(cells: set[tuple[int, int]], start: tuple[int, int]) -> set[tuple[int, int]]:
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen


def _raw_facts(grid):
    shape = _grid_shape(grid)
    if shape is None:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = shape
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    mask = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    anchors = tuple((r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
                    if value not in (0, 5))
    return h, w, mask, anchors


def _analyze_grid(grid):
    errors: list[str] = []
    try:
        h, w, mask, anchors = _raw_facts(grid)
    except ValueError as exc:
        return {}, [str(exc)]

    if not mask:
        return {}, ["missing color-5 mask"]
    if _component(mask, next(iter(mask))) != mask:
        errors.append("color-5 mask must be one 4-connected component")

    r0 = min(r for r, _ in mask)
    c0 = min(c for _, c in mask)
    normalized = tuple(sorted((r - r0, c - c0) for r, c in mask))
    reverse = {tuple(sorted(shape)): name for name, shape in MASKS.items()}
    family = reverse.get(normalized)
    if family is None:
        errors.append(f"mask is not a declared family: {normalized!r}")
    if (r0, c0) == (0, 0):
        errors.append("mask bounding-box origin must not be grid origin")

    if not 2 <= len(anchors) <= 3:
        errors.append(f"expected 2 or 3 anchors, got {len(anchors)}")
    colors = [value for _, _, value in anchors]
    if len(set(colors)) != len(colors):
        errors.append("anchor colors must be distinct")

    projected: list[frozenset[tuple[int, int]]] = []
    if family is not None:
        shape_offsets = MASKS[family]
        for r, c, color in anchors:
            if color in (0, 5):
                errors.append(f"illegal anchor color {color} at {(r, c)}")
            footprint = _stamp((r, c), shape_offsets)
            if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in footprint):
                errors.append(f"stamp at {(r, c)} crosses the grid boundary")
            if footprint & mask:
                errors.append(f"stamp at {(r, c)} overlaps source mask")
            projected.append(footprint)

        for (left_anchor, left), (right_anchor, right) in combinations(
            [((r, c), projected[i]) for i, (r, c, _) in enumerate(anchors)], 2
        ):
            if _manhattan(left_anchor, right_anchor) <= 1:
                errors.append(f"anchors {left_anchor} and {right_anchor} are not isolated")
            if left & right:
                errors.append(f"stamp footprints at {left_anchor} and {right_anchor} overlap")
            if left_anchor in right or right_anchor in left:
                errors.append("an anchor lies inside another anchor's stamp footprint")

        for r, c, _ in anchors:
            if any(_manhattan((r, c), cell) <= 1 for cell in mask):
                errors.append(f"anchor {(r, c)} is not isolated from source mask")

    return {
        "h": h,
        "w": w,
        "mask": frozenset(mask),
        "mask_origin": (r0, c0),
        "normalized": normalized,
        "mask_family": family,
        "anchors": anchors,
        "projected": tuple(projected),
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, Any]:
    info, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe malformed mask-stamping grid: " + "; ".join(errors))
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "mask_family": info["mask_family"],
        "n_anchors": len(info["anchors"]),
    }


def _render(grid, *, offsets=None, first_anchor_only=False, keep_source=False,
            color_mode="anchor"):
    h, w, mask, anchors = _raw_facts(grid)
    if not mask:
        return full_grid(h, w, 0)
    if offsets is None:
        r0 = min(r for r, _ in mask)
        c0 = min(c for _, c in mask)
        offsets = {(r - r0, c - c0) for r, c in mask}
    out = full_grid(h, w, 0)
    if keep_source:
        for r, c in mask:
            out[r][c] = 5
    if first_anchor_only:
        anchors = anchors[:1]
    for ar, ac, anchor_color in anchors:
        color = 5 if color_mode == "mask" else anchor_color
        for dr, dc in offsets:
            r, c = ar + dr, ac + dc
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = color
    return out


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket authority."""
    return _render(grid)


def _marker_only_rival(grid):
    h, w, _, anchors = _raw_facts(grid)
    out = full_grid(h, w, 0)
    for r, c, color in anchors:
        out[r][c] = color
    return out


def _bbox_fill_rival(grid):
    _, _, mask, _ = _raw_facts(grid)
    r0 = min(r for r, _ in mask)
    c0 = min(c for _, c in mask)
    normalized = {(r - r0, c - c0) for r, c in mask}
    max_r = max(r for r, _ in normalized)
    max_c = max(c for _, c in normalized)
    offsets = {(r, c) for r in range(max_r + 1) for c in range(max_c + 1)}
    return _render(grid, offsets=offsets)


def _first_anchor_only_rival(grid):
    return _render(grid, first_anchor_only=True)


def _keep_source_rival(grid):
    return _render(grid, keep_source=True)


def _first_mask_cell_origin_rival(grid):
    _, _, mask, _ = _raw_facts(grid)
    first_r, first_c = min(mask)
    offsets = {(r - first_r, c - first_c) for r, c in mask}
    return _render(grid, offsets=offsets)


def _mask_color_rival(grid):
    return _render(grid, color_mode="mask")


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "leave_only_anchor_markers": _marker_only_rival,
    "fill_mask_bounding_box": _bbox_fill_rival,
    "stamp_only_first_anchor": _first_anchor_only_rival,
    "keep_source_mask": _keep_source_rival,
    "use_first_mask_cell_as_origin": _first_mask_cell_origin_rival,
    "stamp_in_mask_color": _mask_color_rival,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _info(grid):
    info, errors = _analyze_grid(grid)
    return info if not errors else {}


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "multiple_mask_cells": lambda grid: len(_info(grid).get("mask", ())) > 1,
    "nonrectangular_mask": lambda grid: bool(_info(grid)) and (
        len(_info(grid)["normalized"])
        < (max(r for r, _ in _info(grid)["normalized"]) + 1)
        * (max(c for _, c in _info(grid)["normalized"]) + 1)
    ),
    "multiple_anchors": lambda grid: len(_info(grid).get("anchors", ())) > 1,
    "source_removed": lambda grid: bool(_info(grid).get("mask")),
    "bbox_origin_without_mask_cell": lambda grid: bool(_info(grid))
    and (0, 0) not in _info(grid)["normalized"],
    "anchor_recoloring": lambda grid: bool(_info(grid).get("anchors")),
}

WITNESS_RIVALS = {
    "multiple_mask_cells": ["leave_only_anchor_markers"],
    "nonrectangular_mask": ["fill_mask_bounding_box"],
    "multiple_anchors": ["stamp_only_first_anchor"],
    "source_removed": ["keep_source_mask"],
    "bbox_origin_without_mask_cell": ["use_first_mask_cell_as_origin"],
    "anchor_recoloring": ["stamp_in_mask_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject generated lessons that leave a declared shortcut viable."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is malformed: {'; '.join(errors)}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with mask-stamping rule")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(f"demonstrations leave rival answer-equivalent on query: {name}")
    return reasons
