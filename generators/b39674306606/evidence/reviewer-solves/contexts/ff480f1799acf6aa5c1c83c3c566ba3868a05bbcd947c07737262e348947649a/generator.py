"""Generator for b39674306606 — find the unmatched exact shape.

Treat every non-zero monochrome 4-connected component as an object. Normalize
its occupied cells by translation only (subtract the top-left row and column).
One normalized shape occurs exactly once; every other shape occurs as a pair.
Return a blank grid with the singleton object's cells painted cyan (8).

Orientation matters. The ordinary three-example curriculum deliberately cycles
through a rotated/reflected trap, an equal-cell-count non-congruent trap, and a
canonical-scale pair-cancellation scene. This prevents size-only, D4-invariant,
and fixed-position shortcuts from replacing exact translation-normalized shape
comparison.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "b39674306606"
TASK_ID = "b39674306606"
VERSION = "3.0.0"
RULE_HASH = "c78264ef8c54"

SUMMARY = (
    "Find monochrome 4-connected objects, compare their occupied-cell sets after "
    "translation normalization only, and paint the sole shape occurring once cyan "
    "on a blank grid. Every other exact shape occurs in a matched pair; rotation "
    "and reflection do not count as equality."
)

INVARIANTS = [
    "background is 0 and input objects use colors 1..7 or 9",
    "there are either one or two exact matched shape pairs plus exactly one singleton",
    "objects are monochrome 4-connected components separated by blank space",
    "shape equality is translation-only; orientation remains significant",
    "the authoritative output is blank except for the singleton cells recolored 8",
]

# Every public axis is exactly recoverable from the returned input.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "12..16",
    },
    "pair_count": {
        "type": "int",
        "default": "scheduled 1..2 matched shape pairs",
        "valid": "1..2",
    },
    "singleton_size": {
        "type": "int",
        "default": "scheduled 4..5 cells",
        "valid": "3..6",
    },
    "odd_relation": {
        "type": "str",
        "default": "scheduled semantic curriculum",
        "valid": "different_size|rotated|same_size_distinct",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled canonical|monochrome|multicolor",
        "valid": "canonical|monochrome|multicolor",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

Shape = tuple[tuple[int, int], ...]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


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


# Connected polyominoes contained in a 3x3 placement slot.  Sizes 3..6 each
# have at least two non-D4-equivalent classes, which keeps every override
# combination constructive rather than silently falling back.
L3 = _normalize(((0, 0), (1, 0), (1, 1)))
LINE3 = _normalize(((0, 0), (0, 1), (0, 2)))
SQUARE4 = _normalize(((0, 0), (0, 1), (1, 0), (1, 1)))
T4 = _normalize(((0, 0), (0, 1), (0, 2), (1, 1)))
L4 = _normalize(((0, 0), (1, 0), (2, 0), (2, 1)))
S4 = _normalize(((0, 1), (0, 2), (1, 0), (1, 1)))
CROSS5 = _normalize(((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)))
U5 = _normalize(((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)))
HOOK5 = _normalize(((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)))
P5 = _normalize(((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)))
RECT6 = _normalize(((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)))
HOOK6 = _normalize(((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)))
ZIG6 = _normalize(((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)))
TALL6 = _normalize(((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)))
SEVEN_A = _normalize(((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)))
SEVEN_B = _normalize(((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)))
RING8 = _normalize(
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))
)
NOTCH8 = _normalize(
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1))
)
FULL9 = _normalize((r, c) for r in range(3) for c in range(3))

_SHAPES_BY_SIZE: dict[int, tuple[Shape, ...]] = {
    3: (L3, LINE3),
    4: (SQUARE4, T4, L4, S4),
    5: (CROSS5, U5, HOOK5, P5),
    6: (RECT6, HOOK6, ZIG6, TALL6),
    7: (SEVEN_A, SEVEN_B),
    8: (RING8, NOTCH8),
    9: (FULL9,),
}
_SHAPE_POOL = tuple(shape for shapes in _SHAPES_BY_SIZE.values() for shape in shapes)

_PROFILES = (
    {
        "name": "rotation_trap",
        "grid_h": 10,
        "grid_w": 12,
        "pair_count": 1,
        "singleton_size": 4,
        "odd_relation": "rotated",
        "palette_kind": "monochrome",
    },
    {
        "name": "same_size_trap",
        "grid_h": 10,
        "grid_w": 12,
        "pair_count": 2,
        "singleton_size": 4,
        "odd_relation": "same_size_distinct",
        "palette_kind": "canonical",
    },
    {
        "name": "pair_cancellation",
        "grid_h": 11,
        "grid_w": 13,
        "pair_count": 2,
        "singleton_size": 5,
        "odd_relation": "different_size",
        "palette_kind": "multicolor",
    },
)
SCHEDULE_PROFILES = tuple(str(profile["name"]) for profile in _PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic three-scene semantic curriculum profile."""
    del seed
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[(int(sample_index) + offsets[difficulty]) % len(_PROFILES)]["name"]


def _profile_for(sample_index: int, difficulty: str | None) -> dict[str, object]:
    name = schedule_profile(0, sample_index, difficulty)
    return next(profile for profile in _PROFILES if profile["name"] == name)


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_profile_choice(ctx, overrides, label: str, default: str, values: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, values)
    return ctx.draw_choice(label, (default,))


def _nonidentical_dihedral(shape: Shape, rng) -> Shape:
    options = [candidate for candidate in _dihedral_variants(shape) if candidate != shape]
    if not options:
        raise ValueError("shape has no non-identical rotation/reflection")
    return rng.choice(options)


def _pick_shape(
    rng,
    *,
    size: int | None = None,
    forbidden_exact: set[Shape] | None = None,
    forbidden_d4: set[Shape] | None = None,
    exclude_sizes: set[int] | None = None,
) -> Shape:
    forbidden_exact = forbidden_exact or set()
    forbidden_d4 = forbidden_d4 or set()
    exclude_sizes = exclude_sizes or set()
    pool = _SHAPES_BY_SIZE.get(size, ()) if size is not None else _SHAPE_POOL
    choices = [
        shape
        for shape in pool
        if shape not in forbidden_exact
        and _dihedral_key(shape) not in forbidden_d4
        and len(shape) not in exclude_sizes
    ]
    if not choices:
        raise ValueError(
            f"no shape remains (size={size}, exact={len(forbidden_exact)}, "
            f"d4={len(forbidden_d4)}, excluded_sizes={sorted(exclude_sizes)})"
        )
    return rng.choice(choices)


def _build_role_shapes(pair_count: int, singleton_size: int, relation: str, rng):
    pair_shapes: list[Shape] = []
    if relation == "rotated":
        bases = [
            shape
            for shape in _SHAPES_BY_SIZE[singleton_size]
            if len(_dihedral_variants(shape)) > 1
        ]
        base = rng.choice(bases)
        singleton = _nonidentical_dihedral(base, rng)
        pair_shapes.append(base)
        if pair_count == 2:
            # Prefer the same size so a cell-count heuristic sees all five
            # objects in one non-singleton size class.
            pair_shapes.append(
                _pick_shape(
                    rng,
                    size=singleton_size,
                    forbidden_exact={base, singleton},
                    forbidden_d4={_dihedral_key(base)},
                )
            )
    elif relation == "same_size_distinct":
        base = rng.choice(_SHAPES_BY_SIZE[singleton_size])
        singleton = _pick_shape(
            rng,
            size=singleton_size,
            forbidden_exact={base},
            forbidden_d4={_dihedral_key(base)},
        )
        pair_shapes.append(base)
        if pair_count == 2:
            try:
                second = _pick_shape(
                    rng,
                    size=singleton_size,
                    forbidden_exact={base, singleton},
                    forbidden_d4={_dihedral_key(base), _dihedral_key(singleton)},
                )
            except ValueError:
                second = _pick_shape(
                    rng,
                    forbidden_exact={base, singleton},
                    forbidden_d4={_dihedral_key(base), _dihedral_key(singleton)},
                    exclude_sizes={singleton_size},
                )
            pair_shapes.append(second)
    elif relation == "different_size":
        singleton = rng.choice(_SHAPES_BY_SIZE[singleton_size])
        while len(pair_shapes) < pair_count:
            pair_shapes.append(
                _pick_shape(
                    rng,
                    forbidden_exact={singleton, *pair_shapes},
                    forbidden_d4={_dihedral_key(shape) for shape in pair_shapes},
                    exclude_sizes={singleton_size},
                )
            )
    else:  # pragma: no cover - draw_choice constrains this
        raise ValueError(f"unknown odd relation: {relation!r}")

    role_shapes: list[tuple[str, Shape]] = []
    for pair_index, shape in enumerate(pair_shapes):
        role_shapes.extend(((f"pair_{pair_index}", shape), (f"pair_{pair_index}", shape)))
    role_shapes.append(("singleton", singleton))
    return role_shapes


def _slot_anchors(h: int, w: int, n: int, rng) -> list[tuple[int, int]]:
    """Return 3x3 slots separated by a full blank row and column."""
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


def _assign_anchors(role_shapes, anchors, profile_name: str, rng):
    singleton_index = next(i for i, (role, _) in enumerate(role_shapes) if role == "singleton")
    assigned: list[tuple[int, int] | None] = [None] * len(role_shapes)
    if profile_name == "rotation_trap":
        assigned[singleton_index] = max(anchors, key=lambda p: (p[1], p[0]))
    elif profile_name == "same_size_trap":
        assigned[singleton_index] = min(anchors, key=lambda p: (p[1], p[0]))
    else:
        assigned[singleton_index] = rng.choice(anchors)
    remaining = [anchor for anchor in anchors if anchor != assigned[singleton_index]]
    rng.shuffle(remaining)
    for i in range(len(assigned)):
        if assigned[i] is None:
            assigned[i] = remaining.pop()
    return [anchor for anchor in assigned if anchor is not None]


def _colors_for(palette_kind: str, n: int, rng) -> list[int]:
    usable = [1, 2, 3, 4, 5, 6, 7, 9]
    if palette_kind == "canonical":
        return [6] * n
    if palette_kind == "monochrome":
        color = rng.choice([1, 2, 3, 4, 5, 7, 9])
        return [color] * n
    if palette_kind == "multicolor":
        return rng.sample(usable, n)
    raise ValueError(f"unknown palette kind: {palette_kind!r}")


def _place_shapes(h, w, role_shapes, colors, profile_name: str, rng):
    anchors = _assign_anchors(
        role_shapes,
        _slot_anchors(h, w, len(role_shapes), rng),
        profile_name,
        rng,
    )
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
    h = _draw_profile_int(ctx, overrides, "grid_h", int(profile["grid_h"]), 10, 14)
    w = _draw_profile_int(ctx, overrides, "grid_w", int(profile["grid_w"]), 12, 16)
    pair_count = _draw_profile_int(
        ctx, overrides, "pair_count", int(profile["pair_count"]), 1, 2
    )
    singleton_size = _draw_profile_int(
        ctx, overrides, "singleton_size", int(profile["singleton_size"]), 3, 6
    )
    relation = _draw_profile_choice(
        ctx,
        overrides,
        "odd_relation",
        str(profile["odd_relation"]),
        ("different_size", "rotated", "same_size_distinct"),
    )
    palette_kind = _draw_profile_choice(
        ctx,
        overrides,
        "palette_kind",
        str(profile["palette_kind"]),
        ("canonical", "monochrome", "multicolor"),
    )

    rng = ctx.draw_rng("scene")
    role_shapes = _build_role_shapes(pair_count, singleton_size, relation, rng)
    # Keep role identity while randomizing which pair appears first in scans.
    pair_roles = role_shapes[:-1]
    rng.shuffle(pair_roles)
    role_shapes = pair_roles + [role_shapes[-1]]
    colors = _colors_for(palette_kind, len(role_shapes), rng)
    grid = _place_shapes(h, w, role_shapes, colors, str(profile["name"]), rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "pair_count": pair_count,
        "singleton_size": singleton_size,
        "odd_relation": relation,
        "palette_kind": palette_kind,
    }
    if observed != expected:
        raise AssertionError(f"override observability drift: expected {expected}, got {observed}")
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
                    "color": int(color),
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


def _paint_singleton(grid, selector: Callable[[dict[str, object]], bool]):
    out = full_grid(len(grid), len(grid[0]), 0)
    selected = [obj for obj in _components(grid) if selector(obj)]
    if len(selected) != 1:
        return out
    for r, c in selected[0]["cells"]:
        out[r][c] = 8
    return out


def _solve_exact(grid):
    comps = _components(grid)
    counts = Counter(obj["key"] for obj in comps)
    return _paint_singleton(grid, lambda obj: counts[obj["key"]] == 1)


def _solve_count_only(grid):
    comps = _components(grid)
    counts = Counter(obj["size"] for obj in comps)
    return _paint_singleton(grid, lambda obj: counts[obj["size"]] == 1)


def _solve_dihedral(grid):
    comps = _components(grid)
    counts = Counter(obj["d4_key"] for obj in comps)
    return _paint_singleton(grid, lambda obj: counts[obj["d4_key"]] == 1)


def _solve_leftmost(grid):
    comps = _components(grid)
    target = min(comps, key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    return _paint_singleton(grid, lambda obj: obj is target)


def _solve_rightmost(grid):
    comps = _components(grid)
    target = max(comps, key=lambda obj: (obj["bbox"][3], obj["bbox"][2]))
    return _paint_singleton(grid, lambda obj: obj is target)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical pair-cancellation grammar and reject near-misses."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
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
        return [f"invalid ARC colors: {bad_values[:4]}"]
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    if any(value == 8 for row in grid for value in row):
        errors.append("input reserves color 8 for the output highlight")

    comps = _components(grid)
    if len(comps) not in (3, 5):
        errors.append(f"expected 3 or 5 objects (pairs plus singleton), found {len(comps)}")
    colors = [int(obj["color"]) for obj in comps]
    if colors and len(set(colors)) not in (1, len(colors)):
        errors.append("object colors must be all shared or all distinct")

    key_counts = Counter(obj["key"] for obj in comps)
    frequency_signature = sorted(key_counts.values())
    if frequency_signature not in ([1, 2], [1, 2, 2]):
        errors.append(
            "expected exactly one singleton shape and one or two matched pairs; "
            f"shape multiplicities are {frequency_signature}"
        )

    # Different-color objects may not touch orthogonally: if they did, the
    # monochrome object decomposition would depend on palette rather than shape.
    owner = {cell: int(obj["color"]) for obj in comps for cell in obj["cells"]}
    touching: set[tuple[int, int]] = set()
    for (r, c), color in owner.items():
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            other = owner.get((r + dr, c + dc))
            if other is not None and other != color:
                touching.add(tuple(sorted((color, other))))
    if touching:
        errors.append(f"different-color objects touch orthogonally: {sorted(touching)}")

    if frequency_signature in ([1, 2], [1, 2, 2]):
        answer = _solve_exact(grid)
        if not any(value == 8 for row in answer for value in row):
            errors.append("rule output is empty despite a declared singleton")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every ordinary draw stays on the exact canonical pair-cancellation rule."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    comps = _components(grid)
    counts = Counter(obj["key"] for obj in comps)
    singleton = next((obj for obj in comps if counts[obj["key"]] == 1), None)
    pairs = [obj for obj in comps if counts[obj["key"]] == 2]
    colors = [int(obj["color"]) for obj in comps]
    if colors and set(colors) == {6}:
        palette_kind = "canonical"
    elif colors and len(set(colors)) == 1:
        palette_kind = "monochrome"
    elif colors and len(set(colors)) == len(colors):
        palette_kind = "multicolor"
    else:
        palette_kind = "invalid"

    relation = "invalid"
    if singleton is not None:
        if any(obj["d4_key"] == singleton["d4_key"] for obj in pairs):
            relation = "rotated"
        elif any(obj["size"] == singleton["size"] for obj in pairs):
            relation = "same_size_distinct"
        else:
            relation = "different_size"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "pair_count": sum(count == 2 for count in counts.values()),
        "singleton_size": int(singleton["size"]) if singleton is not None else 0,
        "odd_relation": relation,
        "palette_kind": palette_kind,
    }


SEMANTIC_RIVALS: dict[str, Callable] = {
    "same_cell_count": _solve_count_only,
    "same_up_to_rotation_or_reflection": _solve_dihedral,
    "pick_leftmost_object": _solve_leftmost,
    "pick_rightmost_object": _solve_rightmost,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# The real canonical examples already refute size-only and fixed-position rules,
# but do not include a rotated/reflected singleton; this is the surviving
# canonical ambiguity generated lessons must kill.
CANONICAL_SHORTCUTS = {
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
    "leftmost_shortcut_refuted": lambda grid: _rival_differs(grid, "pick_leftmost_object"),
    "rightmost_shortcut_refuted": lambda grid: _rival_differs(grid, "pick_rightmost_object"),
}
WITNESS_RIVALS = {
    "cell_count_shortcut_refuted": ["same_cell_count"],
    "dihedral_shortcut_refuted": ["same_up_to_rotation_or_reflection"],
    "leftmost_shortcut_refuted": ["pick_leftmost_object"],
    "rightmost_shortcut_refuted": ["pick_rightmost_object"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate every named plausible shortcut."""
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


def mutation_fixtures():
    """Task-local malformed scenes that the structural checker must reject."""
    def grid():
        return full_grid(10, 12, 0)

    def paint(g, shape, r0, c0, color):
        paint_at(g, r0, c0, shape, color)

    all_match = grid()
    for shape, r0, c0, color in (
        (L3, 0, 0, 1), (L3, 0, 5, 2), (L3, 5, 2, 3), (L3, 5, 8, 4)
    ):
        paint(all_match, shape, r0, c0, color)

    two_singletons = grid()
    for shape, r0, c0, color in (
        (L3, 0, 0, 1), (L3, 0, 5, 2), (T4, 5, 1, 3), (SQUARE4, 5, 7, 4)
    ):
        paint(two_singletons, shape, r0, c0, color)

    no_pair = grid()
    for shape, r0, c0, color in (
        (L3, 0, 0, 1), (LINE3, 0, 5, 2), (T4, 5, 1, 3)
    ):
        paint(no_pair, shape, r0, c0, color)

    partial_palette = grid()
    for shape, r0, c0, color in (
        (L3, 0, 0, 1), (L3, 0, 5, 1), (T4, 5, 1, 2)
    ):
        paint(partial_palette, shape, r0, c0, color)

    return [
        ("all_shapes_matched_no_singleton", all_match),
        ("two_unmatched_shapes", two_singletons),
        ("no_matched_pair", no_pair),
        ("partially_reused_palette", partial_palette),
    ]
