"""Semantic generator for ARC task 2602c3d31d21.

Read distinct key colors down the right edge.  Each key color identifies one
multi-cell body shape.  Compute the sum of squared distances over every pair
of cells in each shape, then emit a labeled comparison matrix: off-diagonal
cells are 2 when two signatures match and 5 otherwise.

Five linked public profiles preserve every unique published input geometry.
General profiles isolate equality, inequality, class order, multiplicity,
rotation/reflection invariance, and deliberate collisions of the scalar
pairwise-distance hash.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "2602c3d31d21"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "af35f40d51ca"
SUMMARY = (
    "Build the right-edge-keyed matrix of equal versus unequal pairwise-"
    "squared-distance shape signatures."
)

INVARIANTS = [
    "the background is zero and every nonzero input color is a distinct right-edge key",
    "each key color identifies exactly one multi-cell 4-connected body shape",
    "key order is top-to-bottom on the right edge",
    "shape signature is the sum of squared distances over every unordered cell pair",
    "output uses 2 for equal off-diagonal signatures and 5 for unequal signatures",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
    "public_test_2",
)
GENERAL_PROFILES = (
    "equal_pair",
    "unequal_pair",
    "one_pair_one_singleton",
    "two_pairs",
    "singleton_triple",
    "all_distinct_five",
    "mixed_six",
    "mixed_seven",
    "collision_same_size",
    "collision_different_size",
    "equal_nonadjacent",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng; five linked public profiles in sixteen",
        "valid": "|".join(SCENE_PROFILES),
    }
}


# Public specs are input-only descriptors:
# (height, width, key rows, ((anchor row, anchor col, normalized cells), ...)).
_PUBLIC_SPECS = {
    "public_train_1": (20, 20, (0, 1, 2, 3, 4), (
        (8, 12, ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0))),
        (0, 2, ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0))),
        (16, 4, ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2))),
        (10, 5, ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2))),
        (2, 12, ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2))),
    )),
    "public_train_2": (20, 20, (0, 1, 2, 3), (
        (2, 3, ((0, 1), (0, 3), (1, 1), (1, 3), (2, 1), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3), (4, 1))),
        (6, 14, ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2), (4, 1))),
        (14, 1, ((0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3))),
        (14, 11, ((0, 0), (1, 0), (1, 1), (2, 1), (3, 0), (3, 1), (4, 0))),
    )),
    "public_train_3": (20, 20, (0, 1, 2, 3), (
        (15, 2, ((0, 0), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (3, 1))),
        (3, 4, ((0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 0), (4, 1), (4, 2), (4, 3))),
        (11, 5, ((0, 0), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 4), (3, 4))),
        (4, 13, ((0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 2), (3, 3), (4, 0), (4, 1))),
    )),
    "public_test_1": (25, 21, (0, 1, 2, 3, 4, 5, 6), (
        (1, 1, ((0, 0), (0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 0), (2, 6))),
        (4, 16, ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 0), (6, 1), (6, 2))),
        (6, 3, ((0, 0), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 3), (4, 0), (4, 1), (4, 2), (4, 3))),
        (20, 3, ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 3))),
        (18, 12, ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2), (3, 3), (3, 4))),
        (15, 2, ((0, 0), (0, 6), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (2, 0), (2, 6))),
        (4, 9, ((0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2), (3, 0), (3, 2), (4, 0), (4, 2), (4, 3))),
    )),
    "public_test_2": (22, 23, (0, 1, 2, 3, 4, 5), (
        (8, 9, ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3))),
        (16, 14, ((0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0))),
        (15, 4, ((0, 0), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 4))),
        (2, 8, ((0, 0), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0))),
        (8, 16, ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 0), (4, 1))),
        (6, 2, ((0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 2))),
    )),
}


# Small connected bases with deliberately controlled scalar signatures.
_SHAPES = {
    "l3": ((0, 0), (1, 0), (1, 1)),                 # SPD 4
    "i3": ((0, 0), (0, 1), (0, 2)),                 # SPD 6
    "o4": ((0, 0), (0, 1), (1, 0), (1, 1)),         # SPD 8
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),         # SPD 11
    "i4": ((0, 0), (0, 1), (0, 2), (0, 3)),         # SPD 20
    "x5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)), # SPD 20
    "p5": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)), # SPD 20, noncongruent
    "b5": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)), # SPD 30
}

_GENERAL_SHAPE_NAMES = {
    "equal_pair": ("l3", "l3"),
    "unequal_pair": ("l3", "i3"),
    "one_pair_one_singleton": ("l3", "l3", "o4"),
    "two_pairs": ("l3", "l3", "o4", "o4"),
    "singleton_triple": ("o4", "l3", "l3", "l3"),
    "all_distinct_five": ("l3", "i3", "o4", "t4", "b5"),
    "mixed_six": ("l3", "l3", "o4", "o4", "o4", "b5"),
    "mixed_seven": ("l3", "l3", "l3", "o4", "o4", "b5", "b5"),
    "collision_same_size": ("x5", "p5"),
    "collision_different_size": ("i4", "x5"),
    "equal_nonadjacent": ("l3", "o4", "l3", "b5", "o4"),
}


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _normalize_cells(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _transform_cells(cells, transform):
    points = []
    for row, col in cells:
        x, y = row, -col if transform >= 4 else col
        for _ in range(transform % 4):
            x, y = y, -x
        points.append((x, y))
    return _normalize_cells(points)


def _congruence_signature(cells):
    return min(_transform_cells(cells, transform) for transform in range(8))


def _spd(cells):
    return sum(
        (row1 - row2) ** 2 + (col1 - col2) ** 2
        for index, (row1, col1) in enumerate(cells)
        for row2, col2 in cells[index + 1:]
    )


def _components(grid, color, *, body_only=False):
    height, width = len(grid), len(grid[0])
    col_limit = width - 1 if body_only else width
    seen = set()
    components = []
    for row in range(height):
        for col in range(col_limit):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for neighbor in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < col_limit
                        and grid[nr][nc] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(cells)
    return components


def _class_partition(values):
    seen = {}
    return tuple(seen.setdefault(value, len(seen)) for value in values)


def _public_mask_signature(grid, key_colors):
    roles = {color: index + 1 for index, color in enumerate(key_colors)}
    return (
        len(grid),
        len(grid[0]),
        tuple(tuple(roles.get(value, value) for value in row) for row in grid),
    )


def _grid_from_public_spec(profile, colors):
    height, width, key_rows, shapes = _PUBLIC_SPECS[profile]
    grid = _blank(height, width)
    for color, key_row, (anchor_row, anchor_col, cells) in zip(colors, key_rows, shapes):
        grid[key_row][width - 1] = color
        for row, col in cells:
            grid[anchor_row + row][anchor_col + col] = color
    return grid


_PUBLIC_SIGNATURES = {}
for _profile, (_height, _width, _key_rows, _shapes) in _PUBLIC_SPECS.items():
    _role_colors = tuple(range(1, len(_key_rows) + 1))
    _public_grid = _grid_from_public_spec(_profile, _role_colors)
    _signature = _public_mask_signature(_public_grid, _role_colors)
    if _signature in _PUBLIC_SIGNATURES:
        raise RuntimeError("public profile signatures collide")
    _PUBLIC_SIGNATURES[_signature] = _profile


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["empty grid"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["empty grid"]}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                break
        if errors:
            break
    if errors:
        return {"errors": errors, "height": height, "width": width, "scene_profile": None}

    key_cells = [(row, grid[row][width - 1]) for row in range(height) if grid[row][width - 1] != 0]
    key_colors = [color for _, color in key_cells]
    if not 2 <= len(key_colors) <= 7:
        errors.append(f"expected 2..7 right-edge keys, got {len(key_colors)}")
    if len(set(key_colors)) != len(key_colors):
        errors.append("right-edge key colors must be distinct")
    body_colors = {
        grid[row][col]
        for row in range(height)
        for col in range(width - 1)
        if grid[row][col] != 0
    }
    if body_colors != set(key_colors):
        errors.append("body colors must equal the right-edge key-color set")

    shapes = []
    for color in key_colors:
        components = _components(grid, color, body_only=True)
        if len(components) != 1 or len(components[0]) <= 1:
            errors.append(f"key color {color} needs exactly one multi-cell body shape")
            continue
        cells = components[0]
        shapes.append({
            "color": color,
            "cells": tuple(sorted(cells)),
            "normalized": _normalize_cells(cells),
            "congruence": _congruence_signature(cells),
            "size": len(cells),
            "spd": _spd(cells),
        })

    profile = None
    public_signature = None
    if not errors:
        public_signature = _public_mask_signature(grid, key_colors)
        profile = _PUBLIC_SIGNATURES.get(public_signature)
    if not errors and profile is None:
        spds = tuple(shape["spd"] for shape in shapes)
        sizes = tuple(shape["size"] for shape in shapes)
        partition = _class_partition(spds)
        congruent = (
            len(shapes) == 2
            and shapes[0]["congruence"] == shapes[1]["congruence"]
        )
        fingerprints = {
            ((0, 0), (3, 3), True): "equal_pair",
            ((0, 1), (3, 3), False): "unequal_pair",
            ((0, 0, 1), (3, 3, 4), False): "one_pair_one_singleton",
            ((0, 0, 1, 1), (3, 3, 4, 4), False): "two_pairs",
            ((0, 1, 1, 1), (4, 3, 3, 3), False): "singleton_triple",
            ((0, 1, 2, 3, 4), (3, 3, 4, 4, 5), False): "all_distinct_five",
            ((0, 0, 1, 1, 1, 2), (3, 3, 4, 4, 4, 5), False): "mixed_six",
            ((0, 0, 0, 1, 1, 2, 2), (3, 3, 3, 4, 4, 5, 5), False): "mixed_seven",
            ((0, 0), (5, 5), False): "collision_same_size",
            ((0, 0), (4, 5), False): "collision_different_size",
            ((0, 1, 0, 2, 1), (3, 4, 3, 5, 4), False): "equal_nonadjacent",
        }
        profile = fingerprints.get((partition, sizes, congruent))
        if profile is None:
            errors.append(
                f"unrecognized signature lesson partition={partition} sizes={sizes} congruent={congruent}"
            )
    if profile not in SCENE_PROFILES and not errors:
        errors.append(f"unrecognized scene profile {profile!r}")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "key_cells": key_cells,
        "key_colors": key_colors,
        "shapes": shapes,
        "signature_partition": _class_partition(tuple(shape["spd"] for shape in shapes)),
        "public_signature": public_signature,
        "scene_profile": profile,
    }


def canonical_profile_signature(grid):
    info = _analysis(grid)
    return info.get("scene_profile") if not info["errors"] and info.get("scene_profile") in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Independent Python transcription of the canonical comparison-table rule."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    colors = info["key_colors"]
    spds = [shape["spd"] for shape in info["shapes"]]
    total = (len(colors) + 1) * 3 - 1
    output = _blank(total, total)
    for row in range(total):
        for col in range(total):
            block_row, local_row = divmod(row, 3)
            block_col, local_col = divmod(col, 3)
            if local_row == 2 or local_col == 2:
                continue
            if block_row == 0 and block_col > 0:
                output[row][col] = colors[block_col - 1]
            elif block_col == 0 and block_row > 0:
                output[row][col] = colors[block_row - 1]
            elif block_row > 0 and block_col > 0 and block_row != block_col:
                output[row][col] = 2 if spds[block_row - 1] == spds[block_col - 1] else 5
    return output


def _difficulty_dimensions(rng, difficulty, count):
    if difficulty == "easy":
        return max(15, count * 2 + 3), rng.randint(18, 21)
    if difficulty == "hard":
        return rng.randint(25, 30), rng.randint(25, 30)
    return rng.randint(max(20, count * 2 + 4), 25), rng.randint(21, 27)


def _boxes_touch(first, second, moat=1):
    ar1, ac1, ar2, ac2 = first
    br1, bc1, br2, bc2 = second
    return not (
        ar2 + moat < br1
        or br2 + moat < ar1
        or ac2 + moat < bc1
        or bc2 + moat < ac1
    )


def _place_general_shapes(grid, rng, shapes, colors):
    height, width = len(grid), len(grid[0])
    boxes = []
    for cells, color in zip(shapes, colors):
        shape_height = max(row for row, _ in cells) + 1
        shape_width = max(col for _, col in cells) + 1
        placed = False
        for _ in range(1000):
            top = rng.randint(1, height - shape_height - 1)
            left = rng.randint(1, width - shape_width - 3)
            box = (top, left, top + shape_height - 1, left + shape_width - 1)
            if any(_boxes_touch(box, old) for old in boxes):
                continue
            for row, col in cells:
                grid[top + row][left + col] = color
            boxes.append(box)
            placed = True
            break
        if not placed:
            return False
    return True


def _general_grid(rng, difficulty, profile, colors):
    names = _GENERAL_SHAPE_NAMES[profile]
    for _ in range(100):
        height, width = _difficulty_dimensions(rng, difficulty, len(names))
        transforms = [rng.randrange(8) for _ in names]
        shapes = [
            _transform_cells(_SHAPES[name], transform)
            for name, transform in zip(names, transforms)
        ]
        grid = _blank(height, width)
        if not _place_general_shapes(grid, rng, shapes, colors):
            continue
        key_rows = sorted(rng.sample(range(height), len(colors)))
        for row, color in zip(key_rows, colors):
            grid[row][width - 1] = color
        info = _analysis(grid)
        if not info["errors"] and info["scene_profile"] == profile:
            return grid
    raise RuntimeError(f"could not construct scene profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    count = (
        len(_PUBLIC_SPECS[profile][2])
        if profile in PUBLIC_PROFILES
        else len(_GENERAL_SHAPE_NAMES[profile])
    )
    colors = tuple(context.draw_distinct_colors("key_colors", n=count, exclude={0}))
    rng = context.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        grid = _grid_from_public_spec(profile, colors)
    else:
        grid = _general_grid(rng, difficulty, profile, colors)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed key/shape/signature lessons and nearest impostors."""
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(
                f"requested scene_profile {requested}, observed {info['scene_profile']}"
            )
    if not errors:
        output = rule_mirror(grid)
        expected_size = (len(info["key_colors"]) + 1) * 3 - 1
        if len(output) != expected_size or any(len(row) != expected_size for row in output):
            errors.append("rule mirror emitted the wrong square matrix size")
        palette = {value for row in output for value in row}
        if not {0, *info["key_colors"]}.issubset(palette):
            errors.append("rule mirror lost background or key headers")
        if 5 not in palette and len(set(info["signature_partition"])) > 1:
            errors.append("rule mirror lost unequal-signature cells")
        if 2 not in palette and len(set(info["signature_partition"])) < len(info["signature_partition"]):
            errors.append("rule mirror lost equal-signature cells")
    return errors
