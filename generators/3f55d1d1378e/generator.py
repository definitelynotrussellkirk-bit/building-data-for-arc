"""Generator for 3f55d1d1378e — keep exact translated duplicates.

The input contains several monochrome, spatially separated objects.  Normalize
an object's occupied cells by subtracting only its top-left row and column.
Keep every object whose exact translation-normalized cell set occurs at least
twice; erase every shape that occurs once.

Rotation and reflection are deliberately *not* ignored.  Ordinary lessons
include rotated/reflected one-off distractors, equal-cell-count distractors,
and position counterexamples so that two shortcuts which fit every canonical
pair, plus a plausible fixed-position heuristic, do not fit the generated curriculum.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "3f55d1d1378e"
TASK_ID = "3f55d1d1378e"
VERSION = "3.0.0"
RULE_HASH = "d14af3f6ff73"

SUMMARY = (
    "On a 0-background grid, find the monochrome 4-connected objects and "
    "normalize each occupied-cell set by translation only. Keep every object "
    "whose exact normalized shape occurs at least twice, preserving its color "
    "and position; erase shapes that occur once. Rotation and reflection do "
    "not count as equality."
)

INVARIANTS = [
    "background is 0 and every object has its own non-zero color",
    "exactly one translation-normalized shape class occurs two or three times",
    "one or two other shape classes occur exactly once",
    "objects are monochrome, 4-connected, and separated by an 8-neighborhood gap",
    "the exact-duplicate rule keeps a non-empty proper subset of the objects",
]

# Only facts recoverable exactly from the returned input are public axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "13..18",
    },
    "duplicate_count": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "unique_count": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

Shape = tuple[tuple[int, int], ...]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


SQUARE_2X2 = _normalize(((0, 0), (0, 1), (1, 0), (1, 1)))
L3_CANONICAL = _normalize(((0, 0), (0, 1), (1, 1)))
LINE3 = _normalize(((0, 0), (0, 1), (0, 2)))
T4 = _normalize(((0, 0), (0, 1), (0, 2), (1, 1)))
L4 = _normalize(((0, 0), (1, 0), (2, 0), (2, 1)))
S4 = _normalize(((0, 1), (0, 2), (1, 0), (1, 1)))
HOOK5_CANONICAL = _normalize(((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)))
CROSS5 = _normalize(((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)))
U5 = _normalize(((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)))
HOOK6_CANONICAL = _normalize(
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2))
)

_SHAPE_POOL: tuple[Shape, ...] = (
    SQUARE_2X2,
    L3_CANONICAL,
    LINE3,
    T4,
    L4,
    S4,
    HOOK5_CANONICAL,
    CROSS5,
    U5,
    HOOK6_CANONICAL,
)
_ROTATION_BASES: tuple[Shape, ...] = (L3_CANONICAL, L4, S4, HOOK5_CANONICAL, U5)

_PROFILES = (
    {
        "name": "rotation_trap",
        "grid_h": 9,
        "grid_w": 13,
        "duplicate_count": 2,
        "unique_count": 1,
    },
    {
        "name": "unique_left",
        "grid_h": 10,
        "grid_w": 14,
        "duplicate_count": 2,
        "unique_count": 1,
    },
    {
        "name": "multiplicity_and_size",
        "grid_h": 11,
        "grid_w": 15,
        "duplicate_count": 3,
        "unique_count": 2,
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile used by semantic auditing."""
    del seed
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[(int(sample_index) + offsets[difficulty]) % len(_PROFILES)]["name"]


def _profile_for(sample_index: int, difficulty: str | None) -> dict[str, object]:
    name = schedule_profile(0, sample_index, difficulty)
    return next(profile for profile in _PROFILES if profile["name"] == name)


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use the profile default, but honor every declared boundary in every band."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _bbox_size(shape: Shape) -> tuple[int, int]:
    return 1 + max(r for r, _ in shape), 1 + max(c for _, c in shape)


def _rotate_cw(shape: Shape) -> Shape:
    h, _ = _bbox_size(shape)
    return _normalize((c, h - 1 - r) for r, c in shape)


def _flip_lr(shape: Shape) -> Shape:
    _, w = _bbox_size(shape)
    return _normalize((r, w - 1 - c) for r, c in shape)


def _dihedral_variants(shape: Shape) -> tuple[Shape, ...]:
    variants: set[Shape] = set()
    cur = shape
    for _ in range(4):
        variants.add(cur)
        variants.add(_flip_lr(cur))
        cur = _rotate_cw(cur)
    return tuple(sorted(variants))


def _dihedral_key(shape: Shape) -> Shape:
    return min(_dihedral_variants(shape))


def _nonidentical_dihedral(shape: Shape, rng) -> Shape:
    options = [candidate for candidate in _dihedral_variants(shape) if candidate != shape]
    if not options:
        raise ValueError("rotation-trap base shape has no non-identical D4 variant")
    return rng.choice(options)


def _choose_distinct_shape(
    rng,
    *,
    forbidden: set[Shape],
    preferred_cells: int | None = None,
    forbidden_dihedral: set[Shape] | None = None,
) -> Shape:
    options = [shape for shape in _SHAPE_POOL if shape not in forbidden]
    if preferred_cells is not None:
        matching = [shape for shape in options if len(shape) == preferred_cells]
        if matching:
            options = matching
    if forbidden_dihedral:
        filtered = [shape for shape in options if _dihedral_key(shape) not in forbidden_dihedral]
        if filtered:
            options = filtered
    if not options:
        raise ValueError("no lawful distinct shape remains")
    return rng.choice(options)


def _profile_shapes(profile_name: str, duplicate_count: int, unique_count: int, rng):
    """Return role-tagged shapes with exactly one repeated exact shape class."""
    if profile_name == "rotation_trap":
        duplicate = rng.choice(_ROTATION_BASES)
        uniques = [_nonidentical_dihedral(duplicate, rng)]
        if unique_count == 2:
            uniques.append(
                _choose_distinct_shape(
                    rng,
                    forbidden={duplicate, *uniques},
                    forbidden_dihedral={_dihedral_key(duplicate)},
                )
            )
    elif profile_name == "unique_left":
        duplicate = rng.choice((SQUARE_2X2, T4, HOOK5_CANONICAL))
        uniques = [
            _choose_distinct_shape(
                rng,
                forbidden={duplicate},
                preferred_cells=len(duplicate),
                forbidden_dihedral={_dihedral_key(duplicate)},
            )
        ]
        if unique_count == 2:
            uniques.append(
                _choose_distinct_shape(rng, forbidden={duplicate, *uniques})
            )
    elif profile_name == "multiplicity_and_size":
        if rng.randrange(2) == 0:
            duplicate = L3_CANONICAL
            first_unique = rng.choice((SQUARE_2X2, CROSS5, HOOK6_CANONICAL))
        else:
            duplicate = HOOK5_CANONICAL
            first_unique = rng.choice((L3_CANONICAL, SQUARE_2X2))
        uniques = [first_unique]
        if unique_count == 2:
            uniques.append(
                _choose_distinct_shape(rng, forbidden={duplicate, *uniques})
            )
    else:  # pragma: no cover - schedule_profile constrains this
        raise ValueError(f"unknown profile: {profile_name!r}")

    # Overrides may request one unique in a profile whose default has two.
    uniques = uniques[:unique_count]
    while len(uniques) < unique_count:
        uniques.append(_choose_distinct_shape(rng, forbidden={duplicate, *uniques}))

    return (
        [("duplicate", duplicate) for _ in range(duplicate_count)]
        + [("unique", shape) for shape in uniques]
    )


def _slot_anchors(h: int, w: int, n: int, rng) -> list[tuple[int, int]]:
    """Return up to six 3x3 slots separated by at least one blank row/column."""
    n_rows = 1 + (h - 3) // 4
    n_cols = 1 + (w - 3) // 4
    if n_rows * n_cols < n:
        raise ValueError(f"{h}x{w} cannot host {n} separated 3x3 slots")
    used_h = (n_rows - 1) * 4 + 3
    used_w = (n_cols - 1) * 4 + 3
    row_offset = rng.randint(0, h - used_h)
    col_offset = rng.randint(0, w - used_w)
    anchors = [
        (row_offset + 4 * rr, col_offset + 4 * cc)
        for rr in range(n_rows)
        for cc in range(n_cols)
    ]
    rng.shuffle(anchors)
    return anchors[:n]


def _place_shapes(
    h: int,
    w: int,
    role_shapes: list[tuple[str, Shape]],
    colors: list[int],
    profile_name: str,
    rng,
) -> list[list[int]]:
    anchors = _slot_anchors(h, w, len(role_shapes), rng)

    # A plausible fixed-position heuristic is to erase the rightmost object.
    # This profile puts a unique distractor at the left and a true duplicate at
    # the right, so that shortcut is observably wrong.
    if profile_name == "unique_left":
        unique_index = next(i for i, (role, _) in enumerate(role_shapes) if role == "unique")
        duplicate_index = next(i for i, (role, _) in enumerate(role_shapes) if role == "duplicate")
        left_anchor = min(anchors, key=lambda p: (p[1], p[0]))
        right_anchor = max(anchors, key=lambda p: (p[1], p[0]))
        assigned: list[tuple[int, int] | None] = [None] * len(role_shapes)
        assigned[unique_index] = left_anchor
        assigned[duplicate_index] = right_anchor
        remaining = [a for a in anchors if a not in {left_anchor, right_anchor}]
        rng.shuffle(remaining)
        for i in range(len(assigned)):
            if assigned[i] is None:
                assigned[i] = remaining.pop()
        anchors = [a for a in assigned if a is not None]

    grid = full_grid(h, w, 0)
    for (_, shape), color, (slot_r, slot_c) in zip(role_shapes, colors, anchors):
        sh, sw = _bbox_size(shape)
        r0 = slot_r + rng.randint(0, 3 - sh)
        c0 = slot_c + rng.randint(0, 3 - sw)
        paint_at(grid, r0, c0, shape, color)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    profile = _profile_for(int(sample_index), difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", int(profile["grid_h"]), 9, 14)
    w = _draw_profile_int(ctx, overrides, "grid_w", int(profile["grid_w"]), 13, 18)
    duplicate_count = _draw_profile_int(
        ctx, overrides, "duplicate_count", int(profile["duplicate_count"]), 2, 3
    )
    unique_count = _draw_profile_int(
        ctx, overrides, "unique_count", int(profile["unique_count"]), 1, 2
    )

    rng = ctx.draw_rng("scene")
    role_shapes = _profile_shapes(
        str(profile["name"]), duplicate_count, unique_count, rng
    )
    rng.shuffle(role_shapes)
    colors = rng.sample(list(range(1, 10)), len(role_shapes))
    grid = _place_shapes(h, w, role_shapes, colors, str(profile["name"]), rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def _components(grid) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            key = _normalize(cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "key": key,
                    "d4_key": _dihedral_key(key),
                    "size": len(cells),
                    "bbox": (
                        min(r for r, _ in cells),
                        min(c for _, c in cells),
                        max(r for r, _ in cells),
                        max(c for _, c in cells),
                    ),
                }
            )
    return components


def _paint_components(grid, keep: Callable[[dict[str, object]], bool]):
    out = full_grid(len(grid), len(grid[0]), 0)
    for obj in _components(grid):
        if keep(obj):
            color = int(obj["color"])
            for r, c in obj["cells"]:
                out[r][c] = color
    return out


def _solve_exact(grid):
    comps = _components(grid)
    counts = Counter(obj["key"] for obj in comps)
    return _paint_components(grid, lambda obj: counts[obj["key"]] >= 2)


def _solve_count_only(grid):
    comps = _components(grid)
    counts = Counter(obj["size"] for obj in comps)
    return _paint_components(grid, lambda obj: counts[obj["size"]] >= 2)


def _solve_dihedral(grid):
    comps = _components(grid)
    counts = Counter(obj["d4_key"] for obj in comps)
    return _paint_components(grid, lambda obj: counts[obj["d4_key"]] >= 2)


def _solve_erase_rightmost(grid):
    comps = _components(grid)
    rightmost = max(
        comps,
        key=lambda obj: (obj["bbox"][3], obj["bbox"][1], obj["bbox"][2]),
    )
    return _paint_components(grid, lambda obj: obj is not rightmost)


def _solve_keep_largest(grid):
    comps = _components(grid)
    largest = max(int(obj["size"]) for obj in comps)
    return _paint_components(grid, lambda obj: int(obj["size"]) == largest)


def _solve_keep_smallest(grid):
    comps = _components(grid)
    smallest = min(int(obj["size"]) for obj in comps)
    return _paint_components(grid, lambda obj: int(obj["size"]) == smallest)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes; accept all four canonical inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"invalid ARC colors: {bad_values[:4]}")
        return errors

    comps = _components(grid)
    if not 3 <= len(comps) <= 5:
        errors.append(f"expected 3..5 objects, found {len(comps)}")
    colors = [int(obj["color"]) for obj in comps]
    if len(colors) != len(set(colors)):
        errors.append("each object must use a distinct non-zero color")

    for obj in comps:
        size = int(obj["size"])
        bh, bw = _bbox_size(obj["key"])
        if not 3 <= size <= 6:
            errors.append(f"object color {obj['color']} has unsupported size {size}")
        if bh > 3 or bw > 3:
            errors.append(f"object color {obj['color']} exceeds a 3x3 bounding box")

    # Separate colored objects in the 8-neighborhood.  This prevents diagonal
    # texture leakage and makes the Racket object decomposition unambiguous.
    owner = {
        cell: int(obj["color"])
        for obj in comps
        for cell in obj["cells"]
    }
    touching_pairs: set[tuple[int, int]] = set()
    for (r, c), color in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != color:
                    touching_pairs.add(tuple(sorted((color, other))))
    if touching_pairs:
        errors.append(f"objects touch in the 8-neighborhood: {sorted(touching_pairs)}")

    key_counts = Counter(obj["key"] for obj in comps)
    repeated = [count for count in key_counts.values() if count >= 2]
    unique = [count for count in key_counts.values() if count == 1]
    if len(repeated) != 1:
        errors.append(f"expected exactly one repeated shape class, found {len(repeated)}")
    elif repeated[0] not in (2, 3):
        errors.append(f"repeated shape multiplicity must be 2 or 3, found {repeated[0]}")
    if len(unique) not in (1, 2):
        errors.append(f"expected one or two unique shape classes, found {len(unique)}")

    if comps:
        exact = _solve_exact(grid)
        if exact == grid:
            errors.append("rule-hiding identity scene: no unique object is erased")
        if not any(value != 0 for row in exact for value in row):
            errors.append("rule-hiding empty output: no duplicate object survives")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public-axis value from the returned input."""
    comps = _components(grid)
    counts = Counter(obj["key"] for obj in comps)
    repeated = [count for count in counts.values() if count >= 2]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "duplicate_count": repeated[0] if len(repeated) == 1 else 0,
        "unique_count": sum(count == 1 for count in counts.values()),
    }


SEMANTIC_RIVALS: dict[str, Callable] = {
    "same_cell_count": _solve_count_only,
    "same_up_to_rotation_or_reflection": _solve_dihedral,
    "erase_rightmost_object": _solve_erase_rightmost,
    "keep_largest_objects": _solve_keep_largest,
    "keep_smallest_objects": _solve_keep_smallest,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "same_cell_count": _solve_count_only,
    "same_up_to_rotation_or_reflection": _solve_dihedral,
}


def _rival_differs(grid, name: str) -> bool:
    try:
        return _solve_exact(grid) != SEMANTIC_RIVALS[name](grid)
    except Exception:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "cell_count_shortcut_refuted": lambda grid: _rival_differs(grid, "same_cell_count"),
    "dihedral_shortcut_refuted": lambda grid: _rival_differs(
        grid, "same_up_to_rotation_or_reflection"
    ),
    "rightmost_shortcut_refuted": lambda grid: _rival_differs(
        grid, "erase_rightmost_object"
    ),
    "largest_shortcut_refuted": lambda grid: _rival_differs(grid, "keep_largest_objects"),
    "smallest_shortcut_refuted": lambda grid: _rival_differs(grid, "keep_smallest_objects"),
}

WITNESS_RIVALS = {
    "cell_count_shortcut_refuted": ["same_cell_count"],
    "dihedral_shortcut_refuted": ["same_up_to_rotation_or_reflection"],
    "rightmost_shortcut_refuted": ["erase_rightmost_object"],
    "largest_shortcut_refuted": ["keep_largest_objects"],
    "smallest_shortcut_refuted": ["keep_smallest_objects"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to eliminate every named plausible shortcut."""
    reasons: list[str] = []
    if not demos:
        return ["lesson has no demonstrations"]

    for index, pair in enumerate(demos):
        errors = strict_canonical_like(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} is not lawful: {errors[0]}")
    query_errors = strict_canonical_like(query.get("input"))
    if query_errors:
        reasons.append(f"query is not lawful: {query_errors[0]}")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if survives and rival(query["input"]) != query["output"]:
                reasons.append(f"competitor {name} fits every demo and changes the query answer")
        except Exception as exc:
            reasons.append(f"competitor {name} errored: {type(exc).__name__}: {exc}")
    return reasons
