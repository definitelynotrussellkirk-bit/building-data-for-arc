"""Constructive sampler for the symmetry-signature recolor task.

Each nonzero 4-connected monochrome object is classified by reflection symmetry
inside its tight bounding box:

* left-right and up-down symmetric -> color 2
* left-right symmetric only        -> color 3
* up-down symmetric only           -> color 4
* neither                           -> color 6

The canonical demonstrations also admit a stronger-looking but wrong shortcut:
classify only by ``(bbox height, bbox width, area)``.  The normal three-example
schedule therefore contains a non-canonical shape that refutes that shortcut.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a40ab695e6e"
TASK_ID = GENERATOR_ID
RULE_HASH = "5e6364f401b5"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Three or four separated monochrome objects are recolored from their tight-"
    "mask reflection signature: both left-right and up-down symmetric -> 2, "
    "left-right only -> 3, up-down only -> 4, and neither -> 6.  Canonical-scale "
    "examples recur in every difficulty band, while every three-example lesson "
    "also contains a larger-shape counterexample to the canonical-fitting "
    "bounding-box/area lookup shortcut."
)

INVARIANTS = [
    "background is color 0; source colors are distinct and reserved from result colors 2/3/4/6",
    "objects are 4-connected and separated by at least one cell, including diagonals",
    "every object fits a 3x3 tight bounding box and has between 3 and 9 cells",
    "the ordinary three-profile schedule refutes the declared canonical shortcut",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted canonical heights with full 9..14 support",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted canonical widths with full 10..16 support",
        "valid": "10..16",
    },
    "n_objects": {
        "type": "int",
        "default": "profile-weighted 3 or 4",
        "valid": "3..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

Shape = tuple[tuple[int, int], ...]
Grid = list[list[int]]


def _shape(*cells: tuple[int, int]) -> Shape:
    return tuple(sorted(cells))


# Canonical masks.
_BOTH_SQUARE = _shape((0, 0), (0, 1), (1, 0), (1, 1))
_LR_CANONICAL = _shape((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))
_UD_CANONICAL = _shape((0, 0), (0, 1), (1, 1), (2, 0), (2, 1))
_NONE_CANONICAL = _shape((0, 0), (1, 0), (1, 1), (2, 1))

# Counterfactual and broad-domain masks.  All remain at most 3x3 so every
# advertised size/count combination is constructively placeable.
_BOTH_PLUS = _shape((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_BOTH_RING = _shape(
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)
_LR_T = _shape((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_LR_CROWN = _shape((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1))
_UD_T = _shape((0, 0), (1, 0), (1, 1), (1, 2), (2, 0))
_UD_CROWN = _shape((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1))
_NONE_L = _shape((0, 0), (1, 0), (1, 1))
_NONE_STAIR = _shape((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))

SHAPE_BANKS: dict[str, tuple[Shape, ...]] = {
    "both": (_BOTH_SQUARE, _BOTH_PLUS, _BOTH_RING),
    "lr": (_LR_CANONICAL, _LR_T, _LR_CROWN),
    "ud": (_UD_CANONICAL, _UD_T, _UD_CROWN),
    "none": (_NONE_CANONICAL, _NONE_L, _NONE_STAIR),
}

_CANONICAL_MASKS = frozenset(
    {_BOTH_SQUARE, _LR_CANONICAL, _UD_CANONICAL, _NONE_CANONICAL}
)
_CANONICAL_PROFILES = frozenset({(9, 10), (10, 10), (9, 11), (10, 11)})
_CLASS_COLOR = {"both": 2, "lr": 3, "ud": 4, "none": 6}
_SOURCE_COLORS = (1, 5, 7, 8, 9)

SCHEDULE_PROFILES = ("canonical_lr", "bbox_trap", "canonical_ud", "bbox_trap")


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _bbox_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize(cells)
    if not normalized:
        return 0, 0
    return (
        max(r for r, _ in normalized) + 1,
        max(c for _, c in normalized) + 1,
    )


def _symmetry_class(cells: Iterable[tuple[int, int]]) -> str:
    normalized = set(_normalize(cells))
    if not normalized:
        raise ValueError("cannot classify an empty object")
    height = max(r for r, _ in normalized)
    width = max(c for _, c in normalized)
    left_right = {(r, width - c) for r, c in normalized} == normalized
    up_down = {(height - r, c) for r, c in normalized} == normalized
    if left_right and up_down:
        return "both"
    if left_right:
        return "lr"
    if up_down:
        return "ud"
    return "none"


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle all teaching profiles in every consecutive three draws.

    A seed/band offset prevents one profile from always occupying a fixed lesson
    slot while preserving the consecutive-window guarantee.
    """
    band = "none" if difficulty is None else str(difficulty)
    digest = hashlib.sha256(f"{seed}|{band}|symmetry-profile".encode()).digest()
    offset = int.from_bytes(digest[:2], "big") % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % len(SCHEDULE_PROFILES)]


def _weighted_axis(ctx, name: str, legal: Sequence[int], anchor: int) -> int:
    """Favor an anchor without narrowing the exact override domain."""
    options = tuple(legal) + (anchor,) * 32
    return int(ctx.draw_choice(name, options))


def _target_dimensions(ctx, profile: str) -> tuple[int, int]:
    # All three teaching profiles recur at one of the exact canonical
    # size/palette profiles.  The independent keyed draw varies which one.
    preferred = {
        "canonical_lr": ((9, 10), (10, 10)),
        "bbox_trap": ((10, 10), (10, 11)),
        "canonical_ud": ((9, 11), (10, 11)),
    }[profile]
    return ctx.draw_rng("canonical_dimension_anchor").choice(preferred)


def _profile_shapes(profile: str, n_objects: int, rng) -> list[Shape]:
    if profile == "canonical_lr":
        shapes = [_BOTH_SQUARE, _LR_CANONICAL, _NONE_CANONICAL]
        if n_objects == 4:
            shapes.append(_UD_CANONICAL)
    elif profile == "canonical_ud":
        shapes = [_BOTH_SQUARE, _UD_CANONICAL, _NONE_CANONICAL]
        if n_objects == 4:
            shapes.append(_LR_CANONICAL)
    elif profile == "bbox_trap":
        # PLUS has (3,3,5): the canonical size/area lookup predicts 6, while
        # actual reflection symmetry requires 2.  The 3x3 T adds a second
        # independently shaped disagreement in every four-object draw.
        single_axis_class = rng.choice(("lr", "ud"))
        other_axis_class = "ud" if single_axis_class == "lr" else "lr"
        shapes = [
            rng.choice((_BOTH_PLUS, _BOTH_RING)),
            rng.choice(SHAPE_BANKS[single_axis_class][1:]),
            rng.choice(SHAPE_BANKS["none"][1:]),
        ]
        if n_objects == 4:
            shapes.append(rng.choice(SHAPE_BANKS[other_axis_class][1:]))
    else:  # defensive: profiles are internal, so this signals source drift
        raise ValueError(f"unknown schedule profile: {profile!r}")
    rng.shuffle(shapes)
    return shapes


def _corner_placements(
    h: int,
    w: int,
    shapes: Sequence[Shape],
    rng,
) -> list[tuple[int, int]]:
    """Place up to four 3x3 masks in separated corner regions.

    A one-cell jitter gives layout variation.  At the minimum 9x10 canvas,
    opposite regions still retain at least one blank row/column between masks.
    """
    slots = ["tl", "tr", "bl", "br"]
    rng.shuffle(slots)
    placements = []
    for shape, slot in zip(shapes, slots):
        sh, sw = _bbox_dims(shape)
        row_jitter = rng.randint(0, min(1, h - sh))
        col_jitter = rng.randint(0, min(1, w - sw))
        if slot[0] == "t":
            r0 = row_jitter
        else:
            r0 = h - sh - row_jitter
        if slot[1] == "l":
            c0 = col_jitter
        else:
            c0 = w - sw - col_jitter
        placements.append((r0, c0))
    return placements


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    target_h, target_w = _target_dimensions(ctx, profile)
    h = _weighted_axis(ctx, "grid_h", tuple(range(9, 15)), target_h)
    w = _weighted_axis(ctx, "grid_w", tuple(range(10, 17)), target_w)

    desired_count = 3
    if profile == "bbox_trap" and difficulty in ("medium", "hard"):
        desired_count = 4
    n_objects = _weighted_axis(ctx, "n_objects", (3, 4), desired_count)

    shape_rng = ctx.draw_rng("shape_selection")
    shapes = _profile_shapes(profile, n_objects, shape_rng)
    colors = ctx.draw_rng("object_colors").sample(list(_SOURCE_COLORS), n_objects)
    placements = _corner_placements(h, w, shapes, ctx.draw_rng("layout"))

    grid = full_grid(h, w, 0)
    for shape, color, (r0, c0) in zip(shapes, colors, placements):
        for r, c in shape:
            if grid[r0 + r][c0 + c] != 0:
                raise RuntimeError("constructive corner placement overlapped")
            grid[r0 + r][c0 + c] = color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError("constructive generator emitted invalid grid: " + "; ".join(errors))
    return grid


def _components_nonzero(grid: Sequence[Sequence[int]]):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, list[tuple[int, int]]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, sorted(cells)))
    return components


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact axis from returned pixels."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_objects": len(_components_nonzero(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty  # Difficulty changes sampling weights, never legality.
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors: list[str] = []
    h, w = len(grid), width
    if not 9 <= h <= 14:
        errors.append(f"grid_h={h} outside [9,14]")
    if not 10 <= w <= 16:
        errors.append(f"grid_w={w} outside [10,16]")

    components = _components_nonzero(grid)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected 3 or 4 nonzero objects, found {len(components)}")
    colors = [color for color, _ in components]
    if len(colors) != len(set(colors)):
        errors.append("each object must have a distinct nonzero color")

    for index, (_, cells) in enumerate(components):
        bh, bw = _bbox_dims(cells)
        if not 3 <= len(cells) <= 9:
            errors.append(
                f"object {index} must contain 3..9 cells, found {len(cells)}"
            )
        if bh > 3 or bw > 3:
            errors.append(
                f"object {index} tight bounding box {bh}x{bw} exceeds 3x3"
            )

    # Require a full Chebyshev cell of separation between different objects.
    component_sets = [set(cells) for _, cells in components]
    for left in range(len(component_sets)):
        for right in range(left + 1, len(component_sets)):
            if any(
                abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1
                for r1, c1 in component_sets[left]
                for r2, c2 in component_sets[right]
            ):
                errors.append(
                    f"objects {left} and {right} lack one-cell including-diagonal padding"
                )

    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for name, requested in meta["overrides"].items():
            if requested is not None and name in AXES and observed[name] != requested:
                errors.append(
                    f"override {name}={requested!r} realized as {observed[name]!r}"
                )
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical size/palette and canonical mask envelope."""
    errors = list(self_check(grid))
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in _CANONICAL_PROFILES:
        errors.append("grid dimensions are outside the four canonical profiles")
    components = _components_nonzero(grid)
    if len(components) != 3:
        errors.append("canonical-like profile requires exactly three objects")
    masks = [_normalize(cells) for _, cells in components]
    if any(mask not in _CANONICAL_MASKS for mask in masks):
        errors.append("canonical-like profile contains a noncanonical object mask")
    if _BOTH_SQUARE not in masks:
        errors.append("canonical-like profile requires the 2x2 symmetric square")
    return sorted(set(errors))


def rule_mirror(grid) -> Grid:
    """Independent Python mirror of the selected Racket authority."""
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for _, cells in _components_nonzero(grid):
        output_color = _CLASS_COLOR[_symmetry_class(cells)]
        for r, c in cells:
            output[r][c] = output_color
    return output


def _bbox_area_lookup(grid) -> Grid:
    """Plausible wrong rule that exactly fits every canonical pair.

    It memorizes the canonical component signatures instead of testing symmetry:
    2x2 area-4 -> 2, 2x3 area-5 -> 3, 3x2 area-5 -> 4, otherwise -> 6.
    """
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    lookup = {
        (2, 2, 4): 2,
        (2, 3, 5): 3,
        (3, 2, 5): 4,
    }
    for _, cells in _components_nonzero(grid):
        bh, bw = _bbox_dims(cells)
        output_color = lookup.get((bh, bw, len(cells)), 6)
        for r, c in cells:
            output[r][c] = output_color
    return output


def _refutes_bbox_area_shortcut(grid) -> bool:
    try:
        return not self_check(grid) and rule_mirror(grid) != _bbox_area_lookup(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "bbox_area_shortcut_counterexample": _refutes_bbox_area_shortcut,
}
SEMANTIC_RIVALS = {
    "bbox_area_lookup": _bbox_area_lookup,
}
WITNESS_RIVALS = {
    "bbox_area_shortcut_counterexample": ["bbox_area_lookup"],
}
CANONICAL_SHORTCUTS = {
    "bbox_area_lookup": _bbox_area_lookup,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    errors: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demonstration {index} is not an input/output pair")
            continue
        input_errors = self_check(pair["input"])
        if input_errors:
            errors.append(f"demonstration {index} invalid: {'; '.join(input_errors)}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"demonstration {index} output disagrees with authority mirror")
    if isinstance(query, dict) and "input" in query:
        query_errors = self_check(query["input"])
        if query_errors:
            errors.append("query invalid: " + "; ".join(query_errors))
    if errors:
        return errors

    survivors = [
        name
        for name, competitor in LESSON_COMPETITORS.items()
        if all(competitor(pair["input"]) == pair["output"] for pair in demos)
    ]
    if survivors:
        return [
            "demonstrations do not refute declared competitor(s): "
            + ", ".join(sorted(survivors))
        ]
    return []
