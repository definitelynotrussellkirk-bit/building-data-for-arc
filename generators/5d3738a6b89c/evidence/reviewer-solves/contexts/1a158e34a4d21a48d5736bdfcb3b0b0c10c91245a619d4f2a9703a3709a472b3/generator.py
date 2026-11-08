"""Input sampler for prototype-dictionary stamping.

The unchanged Racket authority reads 3x3 colored prototypes above a full
color-9 separator.  Each prototype's center color is its lookup key.  Every
matching key cell below the separator receives that prototype's nonzero mask,
centered on the key and clipped at the grid boundary.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d3738a6b89c"
TASK_ID = GENERATOR_ID
RULE_HASH = "f9d79bf79624"
VERSION = "4.0.0"
SUMMARY = (
    "Two to four 3x3 prototypes sit above a full color-9 separator row. "
    "Each prototype uses one distinct nonzero, non-9 key color and includes "
    "its center.  Below the separator, every key appears twice in disjoint "
    "3x3 placement tiles.  Stamp the matching prototype mask around every "
    "key, retaining only in-bounds cells below the separator."
)

INVARIANTS = [
    "the unique full color-9 separator is row 3",
    "2..4 width-3 prototypes are separated above it by single color-9 columns",
    "prototype keys are distinct colors 1..8 and every mask includes its center",
    "generated instances contain exactly two anchors per key",
    "all realized stamp footprints are pairwise disjoint",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "11..15; canonical-profile draws favor 11",
        "valid": "11..15",
    },
    "n_boxes": {
        "type": "int",
        "default": "2..4; canonical-profile draws favor 3",
        "valid": "2..4",
    },
    "mask_size": {
        "type": "int",
        "default": "2..6; canonical-profile draws favor 3",
        "valid": "2..6",
    },
    "edge_mode": {
        "type": "str",
        "default": "interior|mixed; canonical-profile draws favor interior",
        "valid": "interior|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_INT_AXES = {
    "grid_h": (11, 15),
    "n_boxes": (2, 4),
    "mask_size": (2, 6),
}
_EDGE_MODES = ("interior", "mixed")
_COLORS = tuple(range(1, 9))
_CENTER = (0, 0)
_NEIGHBORS = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != _CENTER
)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_AXES:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
            lo, hi = _INT_AXES[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "edge_mode":
            if type(value) is not str:
                raise TypeError(
                    f"edge_mode must be a string, not {type(value).__name__}"
                )
            if value not in _EDGE_MODES:
                raise ValueError(
                    f"edge_mode={value!r} not in {list(_EDGE_MODES)!r}"
                )


def _draw_axis(ctx, name, domain, *, profile, anchor, favored=()):
    """Draw an exact observable axis while retaining its full override domain."""
    options = list(domain)
    if profile == "canonical":
        options.extend([anchor] * 8)
    else:
        options.extend(list(favored) * 3)
    return ctx.draw_choice(name, options)


def _difficulty_favorites(difficulty):
    if difficulty == "easy":
        return {
            "grid_h": (11, 12),
            "n_boxes": (2, 3),
            "mask_size": (2, 3),
            "edge_mode": ("interior",),
        }
    if difficulty == "hard":
        return {
            "grid_h": (14, 15),
            "n_boxes": (3, 4),
            "mask_size": (5, 6),
            "edge_mode": ("mixed",),
        }
    if difficulty == "medium":
        return {
            "grid_h": (12, 13, 14),
            "n_boxes": (3,),
            "mask_size": (3, 4, 5),
            "edge_mode": _EDGE_MODES,
        }
    return {name: () for name in AXES}


def _choose_masks(ctx, n_boxes, mask_size, edge_mode):
    patterns = [(_CENTER,) + tail for tail in combinations(_NEIGHBORS, mask_size - 1)]
    rng = ctx.draw_rng("prototype_masks")
    if edge_mode == "mixed":
        clipped = [mask for mask in patterns if any(dr == -1 for dr, _ in mask)]
        first = rng.choice(clipped)
        remaining = [mask for mask in patterns if mask != first]
        return [first] + rng.sample(remaining, n_boxes - 1)
    return rng.sample(patterns, n_boxes)


def _anchor_positions(ctx, height, width, keys, edge_mode):
    tiles = [
        (top, left)
        for top in range(4, height - 2, 3)
        for left in range(0, width - 2, 3)
    ]
    needed = 2 * len(keys)
    if len(tiles) < needed:
        raise RuntimeError(
            f"constructive anchor lattice has {len(tiles)} slots, needs {needed}"
        )
    rng = ctx.draw_rng("anchor_tiles")
    positions = []
    if edge_mode == "mixed":
        top_tiles = [tile for tile in tiles if tile[0] == 4]
        clipped_tile = rng.choice(top_tiles)
        rest = rng.sample([tile for tile in tiles if tile != clipped_tile], needed - 1)
        chosen = [clipped_tile] + rest
    else:
        chosen = rng.sample(tiles, needed)

    cursor = 0
    for key_index, key in enumerate(keys):
        for copy_index in range(2):
            top, left = chosen[cursor]
            cursor += 1
            if edge_mode == "mixed" and key_index == 0 and copy_index == 0:
                positions.append((key, top, left + 1))
            else:
                positions.append((key, top + 1, left + 1))
    return positions


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "curriculum_profile", ("canonical", "canonical", "broad", "broad")
    )
    favored = _difficulty_favorites(difficulty)
    height = _draw_axis(
        ctx,
        "grid_h",
        range(11, 16),
        profile=profile,
        anchor=11,
        favored=favored["grid_h"],
    )
    n_boxes = _draw_axis(
        ctx,
        "n_boxes",
        range(2, 5),
        profile=profile,
        anchor=3,
        favored=favored["n_boxes"],
    )
    mask_size = _draw_axis(
        ctx,
        "mask_size",
        range(2, 7),
        profile=profile,
        anchor=3,
        favored=favored["mask_size"],
    )
    edge_mode = _draw_axis(
        ctx,
        "edge_mode",
        _EDGE_MODES,
        profile=profile,
        anchor="interior",
        favored=favored["edge_mode"],
    )

    width = 4 * n_boxes - 1
    grid = full_grid(height, width, 0)
    for box_index in range(1, n_boxes):
        divider = 4 * box_index - 1
        for row in range(3):
            grid[row][divider] = 9
    for column in range(width):
        grid[3][column] = 9

    keys = ctx.draw_rng("prototype_colors").sample(_COLORS, n_boxes)
    masks = _choose_masks(ctx, n_boxes, mask_size, edge_mode)
    for box_index, (key, mask) in enumerate(zip(keys, masks)):
        center_column = 4 * box_index + 1
        for dr, dc in mask:
            grid[1 + dr][center_column + dc] = key

    for key, row, column in _anchor_positions(ctx, height, width, keys, edge_mode):
        grid[row][column] = key
    return grid


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["expected a rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    if not 11 <= height <= 15:
        errors.append(f"grid height {height} outside [11, 15]")
    if (width + 1) % 4:
        return None, errors + [f"grid width {width} is not 4*n_boxes-1"]
    n_boxes = (width + 1) // 4
    if not 2 <= n_boxes <= 4:
        return None, errors + [f"prototype count {n_boxes} outside [2, 4]"]

    separator_rows = [
        row_index for row_index, row in enumerate(grid) if all(value == 9 for value in row)
    ]
    if separator_rows != [3]:
        return None, errors + [
            f"expected unique full color-9 separator at row 3, found {separator_rows}"
        ]
    separator = 3
    expected_dividers = [4 * index - 1 for index in range(1, n_boxes)]
    actual_dividers = [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(separator))
    ]
    if actual_dividers != expected_dividers:
        errors.append(
            f"expected top divider columns {expected_dividers}, found {actual_dividers}"
        )
    for row in range(separator):
        for column, value in enumerate(grid[row]):
            if value == 9 and column not in expected_dividers:
                errors.append(f"unexpected color 9 in prototype at {(row, column)}")

    prototypes = []
    keys = []
    for box_index in range(n_boxes):
        left = 4 * box_index
        key = grid[1][left + 1]
        if key in (0, 9):
            errors.append(f"prototype {box_index} has invalid center key {key}")
            continue
        mask = []
        for local_row in range(3):
            for local_column in range(3):
                value = grid[local_row][left + local_column]
                if value not in (0, key):
                    errors.append(
                        f"prototype {box_index} mixes key {key} with color {value}"
                    )
                if value == key:
                    mask.append((local_row - 1, local_column - 1))
        if _CENTER not in mask:
            errors.append(f"prototype {box_index} omits its center")
        if not 2 <= len(mask) <= 6:
            errors.append(
                f"prototype {box_index} mask size {len(mask)} outside [2, 6]"
            )
        keys.append(key)
        prototypes.append(
            {
                "index": box_index,
                "left": left,
                "right": left + 3,
                "key": key,
                "offsets": tuple(mask),
            }
        )
    if len(prototypes) != n_boxes:
        return None, errors
    if len(set(keys)) != len(keys):
        errors.append(f"prototype center keys must be distinct, found {keys}")

    anchor_map = {key: [] for key in keys}
    for row in range(separator + 1, height):
        for column, value in enumerate(grid[row]):
            if value == 0:
                continue
            if value not in anchor_map:
                errors.append(
                    f"below separator has unknown color {value} at {(row, column)}"
                )
            else:
                anchor_map[value].append((row, column))

    counts = [len(anchor_map[key]) for key in keys]
    if any(count not in (1, 2) for count in counts):
        errors.append(f"each prototype key needs one or two anchors, found {counts}")
    if len(set(counts)) > 1:
        errors.append(f"all prototype keys need equal anchor counts, found {counts}")

    lookup = {prototype["key"]: prototype["offsets"] for prototype in prototypes}
    footprints = []
    for key in keys:
        for anchor in anchor_map[key]:
            footprint = frozenset(
                (anchor[0] + dr, anchor[1] + dc)
                for dr, dc in lookup[key]
                if anchor[0] + dr >= separator + 1
                and 0 <= anchor[0] + dr < height
                and 0 <= anchor[1] + dc < width
            )
            footprints.append((key, anchor, footprint))
    for index, left in enumerate(footprints):
        for right in footprints[index + 1 :]:
            overlap = left[2] & right[2]
            if overlap:
                errors.append(
                    "stamp footprints overlap at "
                    f"{sorted(overlap)} for anchors {left[1]} and {right[1]}"
                )
                break
        if errors and errors[-1].startswith("stamp footprints overlap"):
            break

    info = {
        "height": height,
        "width": width,
        "separator": separator,
        "n_boxes": n_boxes,
        "prototypes": prototypes,
        "anchors": anchor_map,
        "footprints": footprints,
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid):
    """Validate the lawful sampler manifold, including the canonical pairs."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError("invalid generator grid: " + "; ".join(errors))
    mask_sizes = {len(prototype["offsets"]) for prototype in info["prototypes"]}
    if len(mask_sizes) != 1:
        raise ValueError(f"prototype mask sizes differ: {sorted(mask_sizes)}")
    edge = any(
        row in (info["separator"] + 1, info["height"] - 1)
        or column in (0, info["width"] - 1)
        for anchors in info["anchors"].values()
        for row, column in anchors
    )
    return {
        "grid_h": info["height"],
        "n_boxes": info["n_boxes"],
        "mask_size": next(iter(mask_sizes)),
        "edge_mode": "mixed" if edge else "interior",
    }


def _stamp(grid, *, first_anchor_only=False):
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError("cannot stamp invalid grid: " + "; ".join(errors))
    lookup = {
        prototype["key"]: prototype["offsets"] for prototype in info["prototypes"]
    }
    output = [list(row) for row in grid]
    used = set()
    for row in range(info["separator"] + 1, info["height"]):
        for column in range(info["width"]):
            key = grid[row][column]
            if key not in lookup:
                continue
            if first_anchor_only and key in used:
                continue
            used.add(key)
            for dr, dc in lookup[key]:
                target_row, target_column = row + dr, column + dc
                if (
                    target_row >= info["separator"] + 1
                    and 0 <= target_row < info["height"]
                    and 0 <= target_column < info["width"]
                ):
                    output[target_row][target_column] = key
    return output


def _first_anchor_per_key_only(grid):
    """Rival: wrongly stamps only the first row-major anchor of each key."""
    return _stamp(grid, first_anchor_only=True)


def _has_repeated_key_anchors(grid):
    info, errors = _analyze(grid)
    return bool(
        info is not None
        and not errors
        and any(len(anchors) > 1 for anchors in info["anchors"].values())
    )


SEMANTIC_WITNESSES = {"repeated_key_anchors": _has_repeated_key_anchors}
SEMANTIC_RIVALS = {"first_anchor_per_key_only": _first_anchor_per_key_only}
WITNESS_RIVALS = {"repeated_key_anchors": ["first_anchor_per_key_only"]}
CANONICAL_SHORTCUTS = {"first_anchor_per_key_only": _first_anchor_per_key_only}
LESSON_COMPETITORS = {"first_anchor_per_key_only": _first_anchor_per_key_only}
