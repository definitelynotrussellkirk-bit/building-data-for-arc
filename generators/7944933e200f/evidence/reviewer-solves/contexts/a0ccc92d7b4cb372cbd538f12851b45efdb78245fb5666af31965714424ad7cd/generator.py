"""Semantic generator for ARC task 7944933e200f (source d9fac9be).

Find all 4-connected monochromatic non-black objects.  Rank each object by
the total number of cells of its color in the whole input, stably preserving
row-major object order on ties.  Return the unmasked input crop spanning the
first ranked object's bounding box.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "7944933e200f"
TASK_ID = "7944933e200f"
VERSION = "3.1.1"
RULE_HASH = "9b761bca5c45"
SUMMARY = "Crop the original grid to the first row-major object whose color has minimum global frequency."
INVARIANTS = [
    "background is black (0) and at least two non-black colors occur",
    "objects are maximal 4-connected components of one non-black color",
    "each object is ranked by the whole-grid count of its color, not by component size",
    "ties in whole-grid color count preserve row-major object discovery order",
    "the output is the original unmasked bbox crop of the selected object",
    "background holes or other colors inside the selected bbox remain in the crop",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "rare_singleton",
    "rare_domino_h",
    "rare_domino_v",
    "rare_polyomino",
    "rare_disconnected_color",
    "diagonal_split",
    "global_tie_first_object",
    "common_first_rare_later",
    "crop_with_intruder",
    "three_color_rank",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five official scatter/object fields and ten ranking/connectivity/crop contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = (
    "120002000/002000000/201202011/010020002/000000100/000000000/022200000/121200020/022200002/001000000/000200000",
    "808000008/000080000/008003330/800303830/000003330/008000000/300800080",
    "080000000038/300000080300/033800000008/000380000000/300000000080/000380000000/030000000000/000333008030/003383000000/000333000000/003000000000",
    "200002002/044400000/042400200/044400020/200002000",
    "000000000100/100000400100/000000000000/000014004000/040100000000/000001044001/100000000000/000100004000/000011100004/400014110000/000011100004/004400010000",
)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 5 <= len(grid) <= 30:
        return ["input must contain five through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 5 <= len(grid[0]) <= 30:
        return ["input must contain five through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _objects(grid):
    height, width = len(grid), len(grid[0])
    visited = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = start_row, start_col
            if color == 0 or start in visited:
                continue
            visited.add(start)
            cells = {start}
            frontier = [start]
            while frontier:
                row, col = frontier.pop()
                for dr, dc in _ORTHOGONAL:
                    neighbour = row + dr, col + dc
                    if (
                        0 <= neighbour[0] < height
                        and 0 <= neighbour[1] < width
                        and neighbour not in visited
                        and grid[neighbour[0]][neighbour[1]] == color
                    ):
                        visited.add(neighbour)
                        cells.add(neighbour)
                        frontier.append(neighbour)
            row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
            col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
            result.append({"color": color, "cells": frozenset(cells), "size": len(cells), "bbox": (row0, col0, row1, col1)})
    return tuple(result)


def _selection(grid):
    components = _objects(grid)
    counts = Counter(value for row in grid for value in row if value != 0)
    if not components:
        raise ValueError("at least one non-black object is required")
    selected = sorted(components, key=lambda item: counts[item["color"]])[0]
    return components, counts, selected


def rule_mirror(grid):
    """Exact Python mirror of global-color ranking and unmasked bbox crop."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    _, _, selected = _selection(grid)
    row0, col0, row1, col1 = selected["bbox"]
    return [list(row[col0 : col1 + 1]) for row in grid[row0 : row1 + 1]]


def _rotated(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transforms(grid):
    result = []
    current = [row[:] for row in grid]
    for _ in range(4):
        result.append([row[:] for row in current])
        result.append([row[::-1] for row in current])
        current = _rotated(current)
    return result


def _normalized_shape(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_transforms(cells):
    current = set(_normalized_shape(cells))
    result = []
    for _ in range(4):
        for candidate in (current, {(row, -col) for row, col in current}):
            normalized = _normalized_shape(candidate)
            if normalized not in result:
                result.append(normalized)
        current = {(col, -row) for row, col in current}
    return tuple(result)


def _canonical_shape(cells):
    return min(_shape_transforms(cells))


def _public_family_key(grid):
    errors = _valid_grid(grid)
    if errors:
        return None
    try:
        components, counts, selected = _selection(grid)
    except ValueError:
        return None
    groups = []
    by_color = {}
    for component in components:
        by_color.setdefault(component["color"], []).append(component)
    for color, members in by_color.items():
        groups.append((counts[color], tuple(sorted(_canonical_shape(item["cells"]) for item in members))))
    selected_group = (
        counts[selected["color"]],
        tuple(sorted(_canonical_shape(item["cells"]) for item in by_color[selected["color"]])),
    )
    row0, col0, row1, col1 = selected["bbox"]
    return (
        tuple(sorted((len(grid), len(grid[0])))),
        tuple(sorted(groups)),
        selected_group,
        _canonical_shape(selected["cells"]),
        tuple(sorted((row1 - row0 + 1, col1 - col0 + 1))),
    )


_PUBLIC_FAMILIES = {
    _public_family_key(transformed): profile
    for profile, grid in _PUBLIC_INPUTS.items()
    for transformed in _transforms(grid)
}


def _general_profile(facts):
    if facts["minimum_tie"]:
        return "global_tie_first_object"
    if facts["color_count"] >= 3:
        return "three_color_rank"
    selected = facts["selected"]
    selected_objects = facts["selected_color_objects"]
    if selected["size"] == 1 and any(
        max(abs(row - other_row), abs(col - other_col)) == 1
        for row, col in selected["cells"]
        for item in selected_objects[1:]
        for other_row, other_col in item["cells"]
    ):
        return "diagonal_split"
    if len(selected_objects) >= 2:
        return "rare_disconnected_color"
    if facts["intruder_count"]:
        return "crop_with_intruder"
    if facts["selected_object_index"] != 0:
        return "common_first_rare_later"
    if selected["size"] == 1:
        return "rare_singleton"
    row0, col0, row1, col1 = selected["bbox"]
    if selected["size"] == 2 and row0 == row1:
        return "rare_domino_h"
    if selected["size"] == 2 and col0 == col1:
        return "rare_domino_v"
    return "rare_polyomino"


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    try:
        components, counts, selected = _selection(grid)
    except ValueError as exc:
        return {"errors": [str(exc)], "scene_profile": None, "facts": None, "output": None}
    if len(counts) < 2:
        errors.append("at least two non-black colors are required")
    minimum = min(counts.values())
    minimum_colors = frozenset(color for color, count in counts.items() if count == minimum)
    selected_color_objects = tuple(item for item in components if item["color"] == selected["color"])
    row0, col0, row1, col1 = selected["bbox"]
    intruders = [
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if grid[row][col] not in (0, selected["color"])
    ]
    facts = {
        "height": len(grid),
        "width": len(grid[0]),
        "color_counts": dict(sorted(counts.items())),
        "color_count": len(counts),
        "object_count": len(components),
        "objects": components,
        "selected": selected,
        "selected_object_index": components.index(selected),
        "selected_color_count": counts[selected["color"]],
        "selected_color_objects": selected_color_objects,
        "minimum_colors": minimum_colors,
        "minimum_tie": len(minimum_colors) > 1,
        "intruder_count": len(intruders),
        "output_shape": (row1 - row0 + 1, col1 - col0 + 1),
    }
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None:
        profile = _PUBLIC_FAMILIES.get(_public_family_key(grid))
    if profile is None:
        profile = _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared ranking, connectivity, or crop profile")
    if facts["output_shape"] == (len(grid), len(grid[0])):
        errors.append("selected object bbox must be smaller than the full input")
    output = None if errors else rule_mirror(grid)
    if output is not None:
        expected = [list(row[col0 : col1 + 1]) for row in grid[row0 : row1 + 1]]
        if output != expected:
            errors.append("output must be the original unmasked selected-object bbox crop")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def canonical_family_signature(grid):
    return _PUBLIC_FAMILIES.get(_public_family_key(grid))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return 6, 10
    if difficulty == "medium":
        return 9, 14
    if difficulty == "hard":
        return 13, 19
    return 8, 16


def _random_polyomino(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(sorted(cells))
        dr, dc = rng.choice(_ORTHOGONAL)
        cells.add((row + dr, col + dc))
    row0, col0 = min(row for row, _ in cells), min(col for _, col in cells)
    return {(row - row0, col - col0) for row, col in cells}


def _fill_cells(grid, color, count, forbidden, rng, *, after_index=0):
    width = len(grid[0])
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(width)
        if grid[row][col] == 0 and (row, col) not in forbidden and row * width + col >= after_index
    ]
    rng.shuffle(candidates)
    if len(candidates) < count:
        raise AssertionError("not enough cells for distractor counts")
    for row, col in candidates[:count]:
        grid[row][col] = color


def _general_scene_once(profile, difficulty, rng):
    lo, hi = _limits(difficulty)
    height, width = rng.randint(lo, hi), rng.randint(lo, hi)
    grid = [[0] * width for _ in range(height)]
    palette = rng.sample(range(1, 10), 3 if profile == "three_color_rank" else 2)
    rare, common = palette[0], palette[1]

    if profile == "rare_domino_h":
        shape = {(0, 0), (0, 1)}
    elif profile == "rare_domino_v":
        shape = {(0, 0), (1, 0)}
    elif profile in ("rare_polyomino", "three_color_rank"):
        shape = _random_polyomino(rng, rng.randint(3, 8))
    elif profile == "crop_with_intruder":
        shape = {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}
    else:
        shape = {(0, 0)}

    if profile == "common_first_rare_later":
        anchor_row, anchor_col = 2, 2
        grid[0][0] = common
    elif profile == "diagonal_split":
        anchor_row, anchor_col = 0, 0
    else:
        anchor_row, anchor_col = 0, 0
    selected_cells = {(anchor_row + row, anchor_col + col) for row, col in shape}
    if max(row for row, _ in selected_cells) >= height or max(col for _, col in selected_cells) >= width:
        raise AssertionError("selected object does not fit")
    for row, col in selected_cells:
        grid[row][col] = rare

    extra_rare = set()
    if profile == "diagonal_split":
        extra_rare = {(1, 1)}
    elif profile == "rare_disconnected_color":
        extra_rare = {(height - 2, width - 2), (height - 1, width - 2)}
    elif profile == "global_tie_first_object":
        extra_rare = set()
    for row, col in extra_rare:
        grid[row][col] = rare

    row0, row1 = min(row for row, _ in selected_cells), max(row for row, _ in selected_cells)
    col0, col1 = min(col for _, col in selected_cells), max(col for _, col in selected_cells)
    bbox = {(row, col) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1)}
    if profile == "crop_with_intruder":
        grid[row0 + 1][col0 + 1] = common

    rare_count = sum(value == rare for row in grid for value in row)
    common_existing = sum(value == common for row in grid for value in row)
    if profile == "global_tie_first_object":
        target = rng.randint(6, 10)
        _fill_cells(grid, rare, target - rare_count, bbox | extra_rare, rng, after_index=1)
        _fill_cells(grid, common, target - common_existing, bbox | extra_rare, rng, after_index=1)
    else:
        target = rare_count + rng.randint(4, 12)
        forbidden = bbox if profile != "crop_with_intruder" else selected_cells | {(row0 + 1, col0 + 1)}
        _fill_cells(grid, common, target - common_existing, forbidden | extra_rare, rng, after_index=1)
        if profile == "three_color_rank":
            third = palette[2]
            _fill_cells(grid, third, target + rng.randint(1, 5), forbidden | extra_rare, rng, after_index=1)
    return grid


def _general_scene(profile, difficulty, rng):
    for _ in range(100):
        try:
            grid = _general_scene_once(profile, difficulty, rng)
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct valid scene profile {profile!r}")


def _public_scene_once(profile, rng):
    source = _PUBLIC_INPUTS[profile]
    height, width = len(source), len(source[0])
    components, counts, _ = _selection(source)
    minimum = min(counts.values())
    target_candidates = [item for item in components if counts[item["color"]] == minimum and item["size"] == 1]
    target = rng.choice(target_candidates)
    target_col = rng.randint(0, min(2, width - 1))
    target_cell = (0, target_col)
    grid = [[0] * width for _ in range(height)]
    grid[target_cell[0]][target_cell[1]] = target["color"]
    placed_by_color = {target["color"]: {target_cell}}
    remaining = [item for item in components if item is not target]
    remaining.sort(key=lambda item: (-item["size"], item["color"], min(item["cells"])))
    target_index = target_col
    for component in remaining:
        shape = rng.choice(_shape_transforms(component["cells"]))
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        candidates = []
        for top in range(height - shape_height + 1):
            for left in range(width - shape_width + 1):
                cells = {(top + row, left + col) for row, col in shape}
                if min(row * width + col for row, col in cells) <= target_index:
                    continue
                if any(grid[row][col] != 0 for row, col in cells):
                    continue
                same_color = placed_by_color.get(component["color"], set())
                if any((row + dr, col + dc) in same_color for row, col in cells for dr, dc in _ORTHOGONAL):
                    continue
                candidates.append(cells)
        if not candidates:
            raise AssertionError("could not relocate complete public component multiset")
        cells = rng.choice(candidates)
        for row, col in cells:
            grid[row][col] = component["color"]
        placed_by_color.setdefault(component["color"], set()).update(cells)
    colors = sorted(counts)
    replacement = rng.sample(range(1, 10), len(colors))
    mapping = dict(zip(colors, replacement))
    return [[0 if value == 0 else mapping[value] for value in row] for row in grid]


def _public_nuisance(profile, rng):
    for _ in range(100):
        try:
            grid = _public_scene_once(profile, rng)
        except AssertionError:
            continue
        if canonical_family_signature(grid) == profile and _selection(grid)[2]["size"] == 1:
            return grid
    raise AssertionError(f"could not construct public-family scene {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index)
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
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES if overrides else (scheduled,))
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if not overrides and sample_index % 2 == 0:
        grid = _teaching_scene(difficulty, ctx.draw_rng("teaching"))
    elif profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
        else:
            grid = _public_nuisance(profile, ctx.draw_rng("public_transform"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid global-rank crop lesson: " + "; ".join(errors))
    return grid


# A lesson has three demonstrations and one query. Rich scenes occupy every
# even index, so every consecutive four-pair window has two of them, including
# windows crossing the period boundary. Every query rotation retains one rich
# demonstration that independently refutes all declared finite rivals.
EXAMPLES_NEEDED = 3
# The rich slots already cover global_tie_first_object. Eleven public slots
# and the nine other general slots retain every profile and >=27.5% family
# support. Public nuisance scenes retain canonical profile tuples without
# forcing pixel-identical replay into ordinary lessons.
_OTHER_GENERAL = tuple(profile for profile in GENERAL_PROFILES if profile != "global_tie_first_object")
_OTHER_SCHEDULE = (
    PUBLIC_PROFILES + _OTHER_GENERAL[:4]
    + PUBLIC_PROFILES + _OTHER_GENERAL[4:] + PUBLIC_PROFILES[:1]
)
LESSON_SCHEDULE_PERIOD = 2 * len(_OTHER_SCHEDULE)
SCHEDULE_PROFILES = SCENE_PROFILES
MIN_STRICT_FRAC = 0.25


def _validate_request(seed, sample_index):
    # Seeds are arbitrary literal Python integers in the shared GenCtx API;
    # sample indexes are literal nonnegative integers. Do not coerce scalars.
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a literal nonnegative integer")


def schedule_profile(seed, sample_index, difficulty=None):
    _validate_request(seed, sample_index)
    if sample_index % 2 == 0:
        return "global_tie_first_object"
    return _OTHER_SCHEDULE[(sample_index % LESSON_SCHEDULE_PERIOD) // 2]


def _teaching_scene(difficulty, rng):
    """Construct simultaneous ranking, connectivity, tie and crop contrasts."""
    lo, hi = _limits(difficulty)
    # Three minimum-frequency populations plus a strictly common fourth color
    # need at most 69 colored cells. A 9x9 scene leaves room for every contrast.
    height, width = rng.randint(max(9, lo), max(9, hi)), rng.randint(max(9, lo), max(9, hi))
    ring_height, ring_width = rng.randint(3, 5), rng.randint(3, 5)
    shape = {(row, col) for row in range(ring_height) for col in range(ring_width)
             if row in (0, ring_height - 1) or col in (0, ring_width - 1)}
    target = len(shape) + 1
    # Exclude the ring, detached diagonal and interior intruder from the
    # post-first-cell positions. Retain all feasible spatial placements.
    anchors = [(top, left)
               for top in range(1, height - ring_height)
               for left in range(1, width - ring_width)
               if height * width - (top * width + left) - len(shape) - 2 >= 2 * target]
    if not anchors:
        raise AssertionError("no anchor leaves room for both tied distractor colors")
    top, left = rng.choice(anchors)
    ring = {(top + row, left + col) for row, col in shape}
    palette = rng.sample(range(1, 10), 4)
    common = rng.choice(palette)
    # Both numeric extremes must disagree with stable spatial tie-breaking.
    # Choose the common color independently, avoiding a fixed numerical role
    # for the selected color among all four foreground colors.
    tied_low, selected, tied_high = sorted(color for color in palette if color != common)
    grid = [[0] * width for _ in range(height)]
    grid[0][0] = common  # first object is not globally rare
    for row, col in ring:
        grid[row][col] = selected
    diagonal = (top + ring_height, left + ring_width)
    grid[diagonal[0]][diagonal[1]] = selected
    intruder = (top + 1, left + 1)
    grid[intruder[0]][intruder[1]] = common
    # All other minimum-color cells follow the selected ring's first cell.
    # The detached selected-color cell is diagonal, never four-connected.
    forbidden = ring | {diagonal, intruder}
    first_index = top * width + left
    for tied in (tied_low, tied_high):
        _fill_cells(grid, tied, target, forbidden, rng, after_index=first_index + 1)
    _fill_cells(grid, common, target - 1, forbidden, rng)
    return grid


def strict_canonical_like(grid):
    """Canonical family support preserves dimensions and component multiset."""
    errors = self_check(grid)
    if errors:
        return errors
    if canonical_family_signature(grid) is None:
        return ["not one of the five canonical component-multiset families"]
    return []


def _crop(grid, cells):
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    return [list(row[col0:col1 + 1]) for row in grid[row0:row1 + 1]]


def _first_minimum_frequency_cell_only(grid):
    _, counts, _ = _selection(grid)
    minimum = min(counts.values())
    return next([[value]] for row in grid for value in row if value and counts[value] == minimum)


def _smallest_component(grid):
    return _crop(grid, min(_objects(grid), key=lambda item: item["size"])["cells"])


def _first_nonblack_object(grid):
    return _crop(grid, _objects(grid)[0]["cells"])


def _whole_selected_color_bbox(grid):
    _, _, selected = _selection(grid)
    return _crop(grid, {(row, col) for row in range(len(grid)) for col in range(len(grid[0]))
                        if grid[row][col] == selected["color"]})


def _masked_component_crop(grid):
    _, _, selected = _selection(grid)
    row0, col0, row1, col1 = selected["bbox"]
    return [[grid[row][col] if (row, col) in selected["cells"] else 0
             for col in range(col0, col1 + 1)] for row in range(row0, row1 + 1)]


def _last_minimum_object(grid):
    objects, counts, _ = _selection(grid)
    minimum = min(counts.values())
    return _crop(grid, [item for item in objects if counts[item["color"]] == minimum][-1]["cells"])


def _numeric_color_tie(grid):
    objects, counts, _ = _selection(grid)
    return _crop(grid, min(objects, key=lambda item: (counts[item["color"]], item["color"]))["cells"])


def _highest_numeric_color_tie(grid):
    objects, counts, _ = _selection(grid)
    return _crop(grid, min(objects, key=lambda item: (counts[item["color"]], -item["color"]))["cells"])


def _eight_connected_crop(grid):
    _, _, selected = _selection(grid)
    start = min(selected["cells"])
    cells, frontier = {start}, [start]
    while frontier:
        row, col = frontier.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                neighbour = row + dr, col + dc
                if (neighbour not in cells and 0 <= neighbour[0] < len(grid)
                        and 0 <= neighbour[1] < len(grid[0])
                        and grid[neighbour[0]][neighbour[1]] == selected["color"]):
                    cells.add(neighbour)
                    frontier.append(neighbour)
    return _crop(grid, cells)


SEMANTIC_RIVALS = {
    "first_minimum_frequency_cell_only": _first_minimum_frequency_cell_only,
    "smallest_component": _smallest_component,
    "first_nonblack_object": _first_nonblack_object,
    "whole_selected_color_bbox": _whole_selected_color_bbox,
    "masked_component_crop": _masked_component_crop,
    "last_minimum_object": _last_minimum_object,
    "numeric_color_tie": _numeric_color_tie,
    "highest_numeric_color_tie": _highest_numeric_color_tie,
    "eight_connected_crop": _eight_connected_crop,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only this rival is asserted to fit all five canonical labeled examples.
CANONICAL_SHORTCUTS = {
    "first_minimum_frequency_cell_only": _first_minimum_frequency_cell_only,
}


def _rival_differs(grid, rival):
    return not self_check(grid) and rival(grid) != rule_mirror(grid)


def _singleton_crop(grid):
    return not self_check(grid) and _selection(grid)[2]["size"] == 1


def _unique_minimum(grid):
    analysis = _analysis(grid)
    return not analysis["errors"] and not analysis["facts"]["minimum_tie"]


# Bind each witness to the exact rival callable rather than late-bound names.
def _counterexample_predicate(rival):
    def predicate(grid):
        return _rival_differs(grid, rival)
    return predicate


SEMANTIC_WITNESSES = {
    name: _counterexample_predicate(rival) for name, rival in SEMANTIC_RIVALS.items()
}
SEMANTIC_WITNESSES.update({"singleton_crop": _singleton_crop, "unique_minimum": _unique_minimum})
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
BRANCH_WITNESSES = ("singleton_crop", "unique_minimum")


def _valid_output_label(grid):
    """Output crops may be 1x1; labels still require literal ARC integers."""
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["output must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["output must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["output must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["output cells must be literal ARC color integers from zero through nine"]
    return []


def lesson_identifiable(demos, query):
    """Validate labels and reject ambiguity under the declared finite rivals.

    This is an executable finite-rival contract, not a proof that arbitrary
    alternative programs are excluded by finitely many examples.
    """
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} labeled demonstrations are required"]
    reasons = []
    for name, pair in [(f"demo {index}", pair) for index, pair in enumerate(demos)] + [("query", query)]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{name} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{name} input is invalid: {errors[0]}")
        elif _valid_output_label(pair["output"]):
            reasons.append(f"{name} {_valid_output_label(pair['output'])[0]}")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{name} output disagrees with the canonical rule mirror")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits all demonstrations but changes the query answer")
    return reasons
