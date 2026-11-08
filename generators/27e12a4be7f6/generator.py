"""Generator for 9b:hard_60 — select by hole count and scale to marker.

The literal key color encodes the required hole count: 2 selects the unique
one-hole color-4 component and 3 selects the unique two-hole component.  The
selected component is cropped, upscaled 2x, and stamped with its top-left cell
at the unique color-8 marker.  A third color-4 component has zero holes and is
a required distractor.

The canonical task uses three linked profiles that share the same one- and
two-hole shapes but vary the zero-hole distractor.  General profiles add
same-bbox/same-cell-count and asymmetric witnesses so size, area, position,
and marker-only shortcuts are unreliable while the topological rule remains
unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "27e12a4be7f6"
VERSION = "2.0.0"
TASK_ID = "27e12a4be7f6"
RULE_HASH = "f2ce15a3efe6"

SUMMARY = (
    "One key (2 or 3), one marker (8), and exactly three color-4 components "
    "with 0, 1, and 2 holes; select the key-matched component, scale it 2x, "
    "and place its top-left at the marker."
)

INVARIANTS = [
    "background is literal 0 and the only nonzero colors are 4, 8, and one key color in {2, 3}",
    "exactly one key cell and exactly one marker cell",
    "exactly three 4-connected color-4 components with hole counts {0, 1, 2}",
    "the key-selected component is unique and its 2x crop fits from the marker without clipping",
    "linked shape profiles vary topology, bbox, cell count, D4 orientation, and placement without changing the rule",
]

SCENE_PROFILES = (
    "canonical_square",
    "canonical_plus",
    "canonical_cup",
    "equal_bbox",
    "large_equal",
    "asymmetric",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band-aware keyed draw; easy includes canonical 14",
        "valid": "14..22",
    },
    "grid_w": {
        "type": "int",
        "default": "band-aware keyed draw; easy includes canonical 14",
        "valid": "14..22",
    },
    "key_color": {
        "type": "color",
        "default": "keyed choice 2|3",
        "valid": "2|3",
    },
    "scene_profile": {
        "type": "str",
        "default": "keyed choice across every linked profile",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _normalize(cells):
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _bbox_size(cells):
    cells = set(cells)
    return (
        max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
        max(c for _, c in cells) - min(c for _, c in cells) + 1,
    )


def _rect_border(height, width):
    return frozenset(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    )


def _filled_rect(height, width):
    return frozenset(
        (r, c) for r in range(height) for c in range(width)
    )


def _rotate(cells):
    return _normalize((c, -r) for r, c in cells)


def _flip(cells):
    return _normalize((r, -c) for r, c in cells)


def _d4_variants(cells):
    current = _normalize(cells)
    variants = []
    seen = set()
    for _ in range(4):
        for candidate in (current, _flip(current)):
            signature = tuple(sorted(candidate))
            if signature not in seen:
                seen.add(signature)
                variants.append(candidate)
        current = _rotate(current)
    return tuple(variants)


def _d4_signature(cells):
    return min(tuple(sorted(variant)) for variant in _d4_variants(cells))


_RING_3 = _rect_border(3, 3)
_DOUBLE_3X5 = _rect_border(3, 5) | {(1, 2)}
_SQUARE_2 = _filled_rect(2, 2)
_PLUS_3 = frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)})
_CUP_2X3 = frozenset({(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)})

_EQUAL_ONE = _rect_border(4, 5)
_EQUAL_TWO = _DOUBLE_3X5 | {(3, 2)}
_EQUAL_ZERO = _rect_border(4, 5) - {(0, 2)}

_LARGE_ONE = _rect_border(5, 5)
_LARGE_TWO = _rect_border(4, 5) | {(1, 2), (2, 2)}
_LARGE_ZERO = _filled_rect(4, 4)

_ASYMMETRIC_ONE = _rect_border(3, 4) | {(1, 4)}
_ASYMMETRIC_TWO = _rect_border(3, 6) | {(1, 2)}
_ASYMMETRIC_ZERO = _rect_border(4, 4) - {(1, 0)}

_PROFILE_SHAPES = {
    "canonical_square": (_SQUARE_2, _RING_3, _DOUBLE_3X5),
    "canonical_plus": (_PLUS_3, _RING_3, _DOUBLE_3X5),
    "canonical_cup": (_CUP_2X3, _RING_3, _DOUBLE_3X5),
    "equal_bbox": (_EQUAL_ZERO, _EQUAL_ONE, _EQUAL_TWO),
    "large_equal": (_LARGE_ZERO, _LARGE_ONE, _LARGE_TWO),
    "asymmetric": (_ASYMMETRIC_ZERO, _ASYMMETRIC_ONE, _ASYMMETRIC_TWO),
}

_PROFILE_BY_SIGNATURE = {
    tuple(_d4_signature(shape) for shape in shapes): profile
    for profile, shapes in _PROFILE_SHAPES.items()
}
if len(_PROFILE_BY_SIGNATURE) != len(_PROFILE_SHAPES):
    raise AssertionError("scene-profile signatures must be unique")


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == color
    }
    components = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _DIRS4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(frozenset(cells))
    return components


def _hole_count(cells):
    normalized = _normalize(cells)
    height, width = _bbox_size(normalized)
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in normalized
    }
    holes = 0
    while remaining:
        start = remaining.pop()
        stack = [start]
        touches_border = False
        while stack:
            r, c = stack.pop()
            if r in (0, height - 1) or c in (0, width - 1):
                touches_border = True
            for dr, dc in _DIRS4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        if not touches_border:
            holes += 1
    return holes


def profile_signature(grid):
    """Return the linked D4-invariant (0-hole, 1-hole, 2-hole) signature."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    by_holes = {}
    for component in _components(grid, 4):
        count = _hole_count(component)
        if count in by_holes:
            return None
        by_holes[count] = component
    if set(by_holes) != {0, 1, 2}:
        return None
    return tuple(_d4_signature(by_holes[count]) for count in (0, 1, 2))


def _analysis(grid):
    result = {
        "errors": [],
        "key_color": None,
        "marker": None,
        "scene_profile": None,
        "components_by_holes": {},
    }
    errors = result["errors"]
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a non-empty rectangular list")
        return result
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        errors.append("grid rows must be non-empty sequences")
        return result
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    height = len(grid)
    if not (14 <= height <= 22 and 14 <= width <= 22):
        errors.append(f"grid dimensions {height}x{width} outside 14..22")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return result

    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 2, 3, 4, 8})
    if unexpected:
        errors.append(f"unexpected colors: {unexpected}")
    keys = [
        (r, c, grid[r][c])
        for r in range(height)
        for c in range(width)
        if grid[r][c] in (2, 3)
    ]
    markers = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 8
    ]
    if len(keys) != 1:
        errors.append(f"expected exactly one key cell, found {len(keys)}")
    else:
        result["key_color"] = keys[0][2]
    if len(markers) != 1:
        errors.append(f"expected exactly one marker cell, found {len(markers)}")
    else:
        result["marker"] = markers[0]
    if 0 not in palette:
        errors.append("literal background 0 is missing")
    elif sum(value == 0 for row in grid for value in row) <= height * width // 2:
        errors.append("background 0 must occupy a strict majority of the grid")

    color_components = _components(grid, 4)
    if len(color_components) != 3:
        errors.append(
            f"expected exactly three color-4 components, found {len(color_components)}"
        )
    by_holes = {}
    for component in color_components:
        count = _hole_count(component)
        if count in by_holes:
            errors.append(f"multiple color-4 components have {count} holes")
        else:
            by_holes[count] = component
    result["components_by_holes"] = by_holes
    if set(by_holes) != {0, 1, 2}:
        errors.append(
            "color-4 component hole counts must be exactly {0, 1, 2}; "
            f"found {sorted(by_holes)}"
        )

    signature = profile_signature(grid)
    profile = _PROFILE_BY_SIGNATURE.get(signature)
    result["scene_profile"] = profile
    if signature is not None and profile is None:
        errors.append("linked component shapes do not match a declared scene profile")

    if result["key_color"] is not None and result["marker"] is not None:
        needed = 1 if result["key_color"] == 2 else 2
        target = by_holes.get(needed)
        if target is not None:
            target_h, target_w = _bbox_size(target)
            marker_r, marker_c = result["marker"]
            if marker_r + 2 * target_h > height or marker_c + 2 * target_w > width:
                errors.append(
                    "the key-selected component would clip when scaled 2x from the marker"
                )

    if keys and markers:
        special = {(keys[0][0], keys[0][1]), markers[0]}
        for r, c in special:
            if any(
                0 <= r + dr < height
                and 0 <= c + dc < width
                and grid[r + dr][c + dc] == 4
                for dr, dc in _DIRS4
            ):
                errors.append("key and marker cells must not touch a color-4 component")
                break
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete linked teaching-distribution structure."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {})
    for axis in ("key_color", "scene_profile"):
        if axis in requested and analysis.get(axis) != requested[axis]:
            errors.append(
                f"{axis} drifted from requested {requested[axis]!r} "
                f"to {analysis.get(axis)!r}"
            )
    return errors


def observe_overrides(grid):
    """Recover every exact non-dimension axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "key_color": analysis["key_color"],
        "scene_profile": analysis["scene_profile"],
    }


def _draw_dimension(ctx, label, difficulty, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, 14, 22)
    ranges = {
        None: (14, 18),
        "easy": (14, 15),
        "medium": (14, 18),
        "hard": (16, 22),
    }
    lo, hi = ranges[difficulty]
    return ctx.draw_int(label, lo, hi)


def _placement_candidates(grid, shape):
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _bbox_size(shape)
    candidates = []
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            absolute = {(top + r, left + c) for r, c in shape}
            if any(grid[r][c] != 0 for r, c in absolute):
                continue
            if any(
                0 <= r + dr < height
                and 0 <= c + dc < width
                and grid[r + dr][c + dc] != 0
                and (r + dr, c + dc) not in absolute
                for r, c in absolute
                for dr, dc in _DIRS8
            ):
                continue
            candidates.append((top, left))
    return candidates


def _place_shape(grid, shape, rng):
    candidates = _placement_candidates(grid, shape)
    if not candidates:
        return False
    top, left = rng.choice(candidates)
    for r, c in shape:
        grid[top + r][left + c] = 4
    return True


def _special_cell_candidates(grid, *, max_row=None, max_col=None):
    height, width = len(grid), len(grid[0])
    row_limit = height - 1 if max_row is None else max_row
    col_limit = width - 1 if max_col is None else max_col
    return [
        (r, c)
        for r in range(row_limit + 1)
        for c in range(col_limit + 1)
        if grid[r][c] == 0
        and all(
            not (
                0 <= r + dr < height
                and 0 <= c + dc < width
                and grid[r + dr][c + dc] == 4
            )
            for dr, dc in _DIRS8
        )
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_dimension(ctx, "grid_h", difficulty, overrides)
    width = _draw_dimension(ctx, "grid_w", difficulty, overrides)
    key_color = ctx.draw_int("key_color", 2, 3)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    rng = ctx.draw_rng("layout")

    base_shapes = _PROFILE_SHAPES[profile]
    for _attempt in range(200):
        shapes = [rng.choice(_d4_variants(shape)) for shape in base_shapes]
        grid = full_grid(height, width, 0)
        indexed = list(enumerate(shapes))
        rng.shuffle(indexed)
        indexed.sort(
            key=lambda item: _bbox_size(item[1])[0] * _bbox_size(item[1])[1],
            reverse=True,
        )
        if not all(_place_shape(grid, shape, rng) for _, shape in indexed):
            continue

        one_h, one_w = _bbox_size(shapes[1])
        two_h, two_w = _bbox_size(shapes[2])
        marker_candidates = _special_cell_candidates(
            grid,
            max_row=height - 2 * max(one_h, two_h),
            max_col=width - 2 * max(one_w, two_w),
        )
        if not marker_candidates:
            continue
        marker = rng.choice(marker_candidates)
        grid[marker[0]][marker[1]] = 8

        key_candidates = _special_cell_candidates(grid)
        if not key_candidates:
            continue
        key = rng.choice(key_candidates)
        grid[key[0]][key[1]] = key_color

        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(
        f"could not construct profile={profile} on {height}x{width}"
    )
