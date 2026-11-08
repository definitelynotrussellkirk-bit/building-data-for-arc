"""Semantic generator for ARC task c235e3da14f4 (source 23b5c85d).

Color 2 is the only excluded value.  Every same-color 4-connected component
of every other value—including zero—is an object.  The first minimum-area
object in row-major discovery order is selected, and the original grid is
cropped to that object's bounding box (the crop is not an object mask).
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from itertools import permutations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "c235e3da14f4"
TASK_ID = "c235e3da14f4"
VERSION = "3.0.0"
RULE_HASH = "f44de8fa965f"
SUMMARY = "Crop the original grid to the bounding box of the first smallest same-color 4-connected component when color 2 alone is excluded."
INVARIANTS = [
    "color 2 alone is excluded from object detection; zero remains a candidate object",
    "objects are same-color 4-connected components discovered in row-major order",
    "the calibrated smallest object is unique and every other candidate component is larger",
    "the output is the original bounding-box crop, not a mask of the selected component",
    "official scenes use large zero regions, two through five candidate objects, and solid rectangular targets",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 7))
GENERAL_PROFILES = (
    "rectangular_contrast",
    "excluded_smaller",
    "shape_crop",
    "diagonal_components",
    "excluded_inside_crop",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "six complete official scenes plus five labeled object/crop contrasts",
        "valid": "public_1|public_2|public_3|public_4|public_5|public_6|rectangular_contrast|excluded_smaller|shape_crop|diagonal_components|excluded_inside_crop",
    }
}

DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
NON_SPECIAL_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)

_PUBLIC_ROWS = {
    "public_1": (
        "000000000000000", "000000000000000", "022222222222220", "022222222222220",
        "022777722222220", "022777722222220", "022777722222220", "022222222222220",
        "022222222222220", "022222333333320", "000000333333300", "000000333333300",
        "000000333333300",
    ),
    "public_2": (
        "00000000000000000000", "00000000000000000000", "00000000000088888880",
        "03333333304444448880", "03333333304444448880", "03333333304444448880",
        "03333333304444448880", "03333333300088888880", "03333333300088888880",
        "03333333300000000000", "03332222220000000000", "03332222220000000000",
        "00002222220000000000", "00002222220000000000", "00002222220000000000",
        "00000000000000111000", "00000000000000111000", "00000000000000000000",
        "00000000000000000000", "00000000000000000000",
    ),
    "public_3": (
        "000000000222000", "003333000222000", "003333000222000", "003333000222000",
        "003333000000000", "003336600000000", "003336600000000", "003336600000000",
        "003333000000000", "003333000000000",
    ),
    "public_4": (
        "000000000000000", "000000000000000", "011111111000000", "011111111004400",
        "011111111004400", "011111111000000", "011111111000000", "011111111000000",
        "011111111000000", "000000000000000", "000000000000000", "000066666660000",
        "000066666660000", "000066666660000", "000066666660000", "000000000000000",
        "000000000000000", "000000000000000",
    ),
    "public_5": (
        "0000000000", "0222222000", "0222222000", "0222222000", "0222222000",
        "0228882000", "0228882000", "0008880000", "0000000000", "0000000000",
    ),
    "public_6": (
        "000000000000000000", "000000000000000000", "001111110000000000",
        "001111110444444440", "001111110444444440", "001111110444444440",
        "001111110444444440", "001111110444444440", "000000000444444440",
        "000000066644444440", "000000066644444440", "000000066644444440",
        "000000000444444440", "003333300444444440", "003333300000000000",
        "003333300000000000", "003333300000000000", "000000000000000000",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _objects(grid, excluded=2):
    """Exact row-major, same-color, 4-connected object extraction."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == excluded or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                here = queue.popleft()
                cells.append(here)
                for row_delta, col_delta in DELTAS:
                    neighbor = (here[0] + row_delta, here[1] + col_delta)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            found.append({
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "bbox": (
                    min(r for r, _ in cells), min(c for _, c in cells),
                    max(r for r, _ in cells), max(c for _, c in cells),
                ),
            })
    return found


def _color_components(grid, color):
    if color == 2:
        mask = [[0 if value == 2 else 9 for value in row] for row in grid]
        return [item for item in _objects(mask, excluded=9) if item["color"] == 0]
    return [item for item in _objects(grid, excluded=2) if item["color"] == color]


def rule_mirror(grid):
    """Broad, input-pure mirror of objects/pick-min/crop-object."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    candidates = _objects(grid, excluded=2)
    if not candidates:
        raise ValueError("crop-smallest rule requires at least one non-2 object")
    selected = min(candidates, key=lambda item: item["size"])
    row0, col0, row1, col1 = selected["bbox"]
    return [list(row[col0:col1 + 1]) for row in grid[row0:row1 + 1]]


def _normalize_colored(cells):
    row0 = min(row for row, _, _ in cells)
    col0 = min(col for _, col, _ in cells)
    return tuple(sorted((row - row0, col - col0, value) for row, col, value in cells))


def _canonicalize_colors(cells):
    mapping = {2: 2}
    next_label = 10
    normalized = []
    for row, col, value in sorted(cells):
        if value not in mapping:
            mapping[value] = next_label
            next_label += 1
        normalized.append((row, col, mapping[value]))
    return tuple(normalized)


def _nonzero_signature(grid):
    cells = tuple(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )
    return _normalize_colored(cells)


def _d4_family_key(signature):
    variants = set()
    base = tuple(signature)
    for mirrored in (False, True):
        transformed = tuple(
            (row, -col, value) if mirrored else (row, col, value)
            for row, col, value in base
        )
        for _ in range(4):
            variants.add(_canonicalize_colors(_normalize_colored(transformed)))
            transformed = tuple((col, -row, value) for row, col, value in transformed)
    return min(variants)


_PUBLIC_FAMILY_KEYS = {
    _d4_family_key(_nonzero_signature(grid)): profile
    for profile, grid in _PUBLIC_INPUTS.items()
}
if len(_PUBLIC_FAMILY_KEYS) != len(PUBLIC_PROFILES):
    raise AssertionError("official foreground families must be distinct")


def _public_family(grid):
    try:
        signature = _nonzero_signature(grid)
    except (TypeError, ValueError):
        return None
    return _PUBLIC_FAMILY_KEYS.get(_d4_family_key(signature))


def _is_solid_rectangle(obj):
    row0, col0, row1, col1 = obj["bbox"]
    return obj["size"] == (row1 - row0 + 1) * (col1 - col0 + 1)


def _diagonal_same_color(candidates, selected):
    selected_cells = set(selected["cells"])
    for other in candidates:
        if other is selected or other["color"] != selected["color"]:
            continue
        other_cells = set(other["cells"])
        if any(
            (row + dr, col + dc) in other_cells
            for row, col in selected_cells
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
        ):
            return True
    return False


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 30 or not 8 <= width <= 30:
        errors.append("calibrated canvas dimensions must be eight through thirty")
    palette = {value for row in grid for value in row}
    if 0 not in palette or len(palette) < 3 or len(palette) > 7:
        errors.append("calibrated lessons need zero plus two through six additional colors")
    candidates = _objects(grid, excluded=2)
    if not 2 <= len(candidates) <= 6:
        errors.append(f"expected two through six candidate objects including zero, got {len(candidates)}")
    selected = min(candidates, key=lambda item: item["size"]) if candidates else None
    sizes = [item["size"] for item in candidates]
    if selected is not None and sizes.count(selected["size"]) != 1:
        errors.append("the calibrated smallest object must be unique")
    if len(set(sizes)) != len(sizes):
        errors.append("calibrated candidate object sizes must be pairwise distinct")
    zero_objects = [item for item in candidates if item["color"] == 0]
    if len(zero_objects) != 1:
        errors.append("calibrated zero background must remain one connected candidate object")
    if selected is not None:
        row0, col0, row1, col1 = selected["bbox"]
        box_height, box_width = row1 - row0 + 1, col1 - col0 + 1
        if not 2 <= box_height <= 8 or not 2 <= box_width <= 8:
            errors.append("selected crop dimensions must each be two through eight")
        if not 4 <= selected["size"] <= 48:
            errors.append("selected object size must be four through forty-eight")
        if selected["color"] in (0, 2):
            errors.append("the selected calibrated object must use a nonzero, non-2 color")
    output = rule_mirror(grid) if candidates else None
    if output == [list(row) for row in grid]:
        errors.append("calibrated crop must be visibly smaller than the input")
    exact = None
    try:
        exact = _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        pass
    public = exact or _public_family(grid)
    profile = public
    color2_components = _color_components(grid, 2) if 2 in palette else []
    selected_crop_contains_2 = False
    diagonal = False
    solid = False
    if selected is not None:
        row0, col0, row1, col1 = selected["bbox"]
        selected_crop_contains_2 = any(
            grid[row][col] == 2
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
        )
        diagonal = _diagonal_same_color(candidates, selected)
        solid = _is_solid_rectangle(selected)
    if profile is None and selected is not None:
        if selected_crop_contains_2:
            profile = "excluded_inside_crop"
        elif diagonal:
            profile = "diagonal_components"
        elif any(item["size"] < selected["size"] for item in color2_components):
            profile = "excluded_smaller"
        elif not solid:
            profile = "shape_crop"
        else:
            profile = "rectangular_contrast"
    if profile not in SCENE_PROFILES and not errors:
        errors.append("unsupported calibrated smallest-object/crop signature")
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": {
            "objects": tuple(candidates),
            "object_count": len(candidates),
            "object_sizes": tuple(sizes),
            "selected": selected,
            "selected_index": candidates.index(selected) if selected in candidates else None,
            "selected_solid_rectangle": solid,
            "selected_crop_contains_2": selected_crop_contains_2,
            "diagonal_same_color": diagonal,
            "excluded_color2_component_sizes": tuple(item["size"] for item in color2_components),
            "palette": tuple(sorted(palette)),
            "zero_object_size": zero_objects[0]["size"] if len(zero_objects) == 1 else None,
        },
        "output": output,
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _transform_colored(cells, rng):
    transformed = tuple(cells)
    for _ in range(rng.randrange(4)):
        transformed = tuple((col, -row, value) for row, col, value in transformed)
    if rng.random() < 0.5:
        transformed = tuple((row, -col, value) for row, col, value in transformed)
    return _normalize_colored(transformed)


def _unique_d4_transforms(cells):
    variants = set()
    base = tuple(cells)
    for mirrored in (False, True):
        transformed = tuple(
            (row, -col, value) if mirrored else (row, col, value)
            for row, col, value in base
        )
        for _ in range(4):
            variants.add(_normalize_colored(transformed))
            transformed = tuple((col, -row, value) for row, col, value in transformed)
    return tuple(sorted(variants))


@lru_cache(maxsize=None)
def _replacement_orders(count):
    return tuple(permutations(NON_SPECIAL_COLORS, count))


def _public_padding_states(transformed):
    motif_height = max(row for row, _, _ in transformed) + 1
    motif_width = max(col for _, col, _ in transformed) + 1
    max_extra_height = min(10, 30 - motif_height)
    max_extra_width = min(10, 30 - motif_width)
    min_extra_height = min(max(2, 8 - motif_height), max_extra_height)
    min_extra_width = min(max(2, 8 - motif_width), max_extra_width)
    return tuple(
        (extra_height, extra_width, row0, col0)
        for extra_height in range(min_extra_height, max_extra_height + 1)
        for extra_width in range(min_extra_width, max_extra_width + 1)
        for row0 in range(1, extra_height)
        for col0 in range(1, extra_width)
    )


def _indexed_public_configuration(profile, uniqueness_index):
    transforms = _unique_d4_transforms(_nonzero_signature(_PUBLIC_INPUTS[profile]))
    source_colors = sorted({
        value for _, _, value in transforms[0] if value != 2
    })
    replacements = _replacement_orders(len(source_colors))
    padding_by_transform = tuple(_public_padding_states(item) for item in transforms)
    block_sizes = tuple(len(replacements) * len(states) for states in padding_by_transform)
    position = uniqueness_index % sum(block_sizes)
    for transformed, padding_states, block_size in zip(transforms, padding_by_transform, block_sizes):
        if position < block_size:
            replacement_index, padding_index = divmod(position, len(padding_states))
            return transformed, source_colors, replacements[replacement_index], padding_states[padding_index]
        position -= block_size
    raise AssertionError("public configuration index escaped its finite state space")


def _embed_public(profile, difficulty, rng, uniqueness_index=None):
    if uniqueness_index is None:
        transformed = _transform_colored(_nonzero_signature(_PUBLIC_INPUTS[profile]), rng)
        source_colors = sorted({value for _, _, value in transformed if value != 2})
        replacement = rng.sample(NON_SPECIAL_COLORS, len(source_colors))
        padding_states = _public_padding_states(transformed)
        extra_height, extra_width, row0, col0 = rng.choice(padding_states)
    else:
        transformed, source_colors, replacement, padding = _indexed_public_configuration(
            profile, uniqueness_index
        )
        extra_height, extra_width, row0, col0 = padding
    color_map = dict(zip(source_colors, replacement))
    transformed = tuple(
        (row, col, 2 if value == 2 else color_map[value])
        for row, col, value in transformed
    )
    motif_height = max(row for row, _, _ in transformed) + 1
    motif_width = max(col for _, col, _ in transformed) + 1
    height, width = motif_height + extra_height, motif_width + extra_width
    grid = [[0] * width for _ in range(height)]
    for row, col, value in transformed:
        grid[row0 + row][col0 + col] = value
    return grid


def _random_polyomino(height, width, rng):
    path = [(0, 0)]
    row = col = 0
    moves = [(1, 0)] * (height - 1) + [(0, 1)] * (width - 1)
    rng.shuffle(moves)
    for row_delta, col_delta in moves:
        row += row_delta
        col += col_delta
        path.append((row, col))
    cells = set(path)
    target = rng.randint(len(cells), max(len(cells), min(height * width - 1, (height * width * 4) // 5)))
    while len(cells) < target:
        base = rng.choice(tuple(cells))
        row_delta, col_delta = rng.choice(DELTAS)
        candidate = (base[0] + row_delta, base[1] + col_delta)
        if 0 <= candidate[0] < height and 0 <= candidate[1] < width:
            cells.add(candidate)
    return tuple(sorted(cells))


def _can_place(grid, tokens, clearance=1):
    height, width = len(grid), len(grid[0])
    cells = {(row, col) for row, col, _ in tokens}
    if len(cells) != len(tokens):
        return False
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    if any(grid[row][col] != 0 for row, col in cells):
        return False
    return not any(
        grid[row][col] != 0
        for token_row, token_col in cells
        for row in range(max(0, token_row - clearance), min(height, token_row + clearance + 1))
        for col in range(max(0, token_col - clearance), min(width, token_col + clearance + 1))
    )


def _place_tokens(grid, base_tokens, rng, clearance=1):
    motif_height = max(row for row, _, _ in base_tokens) + 1
    motif_width = max(col for _, col, _ in base_tokens) + 1
    if motif_height + 2 > len(grid) or motif_width + 2 > len(grid[0]):
        return None
    for _ in range(200):
        row0 = rng.randint(1, len(grid) - motif_height - 1)
        col0 = rng.randint(1, len(grid[0]) - motif_width - 1)
        tokens = tuple((row + row0, col + col0, value) for row, col, value in base_tokens)
        if _can_place(grid, tokens, clearance=clearance):
            for row, col, value in tokens:
                grid[row][col] = value
            return row0, col0
    return None


def _place_larger_rectangle(grid, color, minimum_area, used_sizes, rng):
    options = [
        (height, width)
        for height in range(2, min(9, len(grid) - 1))
        for width in range(2, min(9, len(grid[0]) - 1))
        if height * width > minimum_area and height * width not in used_sizes
    ]
    rng.shuffle(options)
    for height, width in options:
        tokens = tuple(
            (row, col, color) for row in range(height) for col in range(width)
        )
        if _place_tokens(grid, tokens, rng) is not None:
            return height * width
    return None


def _general_canvas(difficulty, rng):
    low, high = {"easy": (13, 17), "hard": (23, 30)}.get(difficulty, (17, 24))
    return rng.randint(low, high), rng.randint(low, high)


def _target_tokens(profile, color, difficulty, rng):
    limit = {"easy": 5, "hard": 7}.get(difficulty, 6)
    if profile == "rectangular_contrast":
        height, width = rng.randint(2, limit), rng.randint(2, limit)
        return tuple((row, col, color) for row in range(height) for col in range(width))
    if profile == "diagonal_components":
        height, width = rng.randint(3, min(5, limit)), rng.randint(3, min(5, limit))
        target = [(row, col, color) for row, col in _random_polyomino(height, width, rng)]
        other_height, other_width = height + 1, width + 1
        target.extend(
            (height + row, width + col, color)
            for row in range(other_height) for col in range(other_width)
        )
        return tuple(target)
    if profile == "excluded_inside_crop":
        height, width = rng.randint(3, limit), rng.randint(3, limit)
        tokens = []
        for row in range(height):
            for col in range(width):
                if row in (0, height - 1) or col in (0, width - 1):
                    value = color
                else:
                    value = color if rng.random() < 0.35 else 2
                tokens.append((row, col, value))
        if all(value == color for _, _, value in tokens):
            tokens[(height // 2) * width + width // 2] = (height // 2, width // 2, 2)
        return tuple(tokens)
    height, width = rng.randint(3, limit), rng.randint(3, limit)
    return tuple((row, col, color) for row, col in _random_polyomino(height, width, rng))


def _random_general(profile, difficulty, rng):
    for _ in range(300):
        height, width = _general_canvas(difficulty, rng)
        grid = [[0] * width for _ in range(height)]
        colors = rng.sample(NON_SPECIAL_COLORS, 5)
        target_tokens = _target_tokens(profile, colors[0], difficulty, rng)
        if _place_tokens(grid, target_tokens, rng) is None:
            continue
        initial = _objects(grid, excluded=2)
        nonzero = [item for item in initial if item["color"] != 0]
        if not nonzero:
            continue
        target = min(nonzero, key=lambda item: item["size"])
        target_size = target["size"]
        used_sizes = {target_size}
        if profile == "diagonal_components":
            same_color = [item for item in nonzero if item["color"] == colors[0]]
            if len(same_color) != 2:
                continue
            used_sizes.update(item["size"] for item in same_color)
            minimum = max(used_sizes)
            already_non2 = 2
        else:
            minimum = target_size
            already_non2 = 1
        desired_non2 = (
            2 if difficulty == "easy"
            else rng.randint(3, 5) if difficulty == "hard"
            else rng.randint(2, 3)
        )
        success = True
        for index in range(already_non2, desired_non2):
            size = _place_larger_rectangle(grid, colors[index], minimum, used_sizes, rng)
            if size is None:
                success = False
                break
            used_sizes.add(size)
            minimum = size
        if not success:
            continue
        if profile == "excluded_smaller":
            side = max(1, min(3, int(target_size ** 0.5) - 1))
            tokens = tuple((row, col, 2) for row in range(side) for col in range(side))
            if _place_tokens(grid, tokens, rng) is None:
                continue
        elif profile not in ("excluded_inside_crop",) and rng.random() < 0.8:
            side = min(6, max(2, int(target_size ** 0.5) + 1))
            tokens = tuple((row, col, 2) for row in range(side) for col in range(side))
            if _place_tokens(grid, tokens, rng) is None:
                continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct smallest-object lesson {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) + list(GENERAL_PROFILES) * 2,
    )
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    rng = ctx.draw_rng("scene")
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    # Allocate each band a disjoint 10k window.  The coprime-ish seed/sample
    # mix stays collision-free for the repository's sequential and strided
    # samplers, rather than relying on birthday-prone independent draws.
    uniqueness_index = band_index * 10_000 + (seed + 11 * sample_index) % 10_000
    grid = (
        _embed_public(profile, difficulty, rng, uniqueness_index)
        if profile in PUBLIC_PROFILES
        else _random_general(profile, difficulty, rng)
    )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid smallest-object lesson: " + "; ".join(errors))
    return grid
