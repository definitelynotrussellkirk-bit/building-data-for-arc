"""Semantic generator for ARC task 8ef6f191186d (bank H147).

The top-left cell is a geometric command.  Aligned nonzero entries from
columns two onward in rows zero and one define source-to-target color pairs.
Crop the object below the header, recolor mapped cells, apply the commanded
transform, and crop the result again.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "8ef6f191186d"
TASK_ID = "8ef6f191186d"
VERSION = "4.0.0"
RULE_HASH = "84c7e6d399c7"
SUMMARY = "Read a palette mapping and geometric command from the two-row header, then remap, transform, and tightly crop the object below."

INVARIANTS = [
    "cell (0,0) is a command from identity through transpose",
    "aligned contiguous entries in header rows zero and one define unique nonzero source/target pairs",
    "the object below the header is a compact one-to-six-component motif using every declared source color",
    "the object is cropped before recoloring and transformation",
    "the transformed result is cropped tightly and contains target rather than source colors",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "command_identity",
    "command_rotate_cw",
    "command_rotate_180",
    "command_rotate_ccw",
    "command_flip_lr",
    "command_flip_ud",
    "command_transpose",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five official families plus every command transform",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PROFILE_TO_COMMAND = {
    "command_identity": 1,
    "command_rotate_cw": 2,
    "command_rotate_180": 3,
    "command_rotate_ccw": 4,
    "command_flip_lr": 5,
    "command_flip_ud": 6,
    "command_transpose": 7,
}
_COMMAND_TO_PROFILE = {value: key for key, value in _PROFILE_TO_COMMAND.items()}
_PUBLIC_ROWS = {
    "public_1": ("202300", "008600", "230000", "023000", "200000"),
    "public_2": ("504500", "002700", "450000", "405000", "044000"),
    "public_3": ("306700", "003900", "670000", "607000", "006000"),
    "public_4": ("702300", "004800", "230000", "203000", "000300"),
    "public_5": ("402300", "007500", "230000", "203000", "033000"),
}
_PUBLIC_INPUTS = {name: [[int(value) for value in row] for row in rows] for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_PUBLIC_FAMILIES = {
    (2, 2, 3, 3, 5): "public_1",
    (5, 2, 3, 3, 6): "public_2",
    (3, 2, 3, 3, 5): "public_3",
    (7, 2, 3, 4, 5): "public_4",
    (4, 2, 3, 3, 6): "public_5",
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 3 <= len(grid) <= 30:
        return ["input must contain three through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 3 <= len(grid[0]) <= 30:
        return ["input must contain three through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _crop(grid):
    cells = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0]
    if not cells:
        raise ValueError("the executable rule requires nonzero object content below the header")
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    return [list(row[col0:col1 + 1]) for row in grid[row0:row1 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def apply_command(grid, command):
    return {
        1: lambda value: [row[:] for row in value],
        2: _rotate_cw,
        3: _rotate_180,
        4: _rotate_ccw,
        5: _flip_lr,
        6: _flip_ud,
    }.get(command, _transpose)(grid)


def rule_mirror(grid):
    """Exact Python mirror of the broad executable canonical Racket rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    command = grid[0][0]
    sources = [value for value in grid[0][2:] if value != 0]
    targets = [value for value in grid[1][2:] if value != 0]
    if len(sources) != len(targets):
        raise ValueError("the executable mapping requires equally many source and target entries")
    mapping = list(zip(sources, targets))
    obj = _crop([list(row) for row in grid[2:]])
    remapped = []
    for row in obj:
        values = []
        for value in row:
            hit = next((target for source, target in mapping if source == value), None)
            values.append(hit if value != 0 and hit is not None else value)
        remapped.append(values)
    return _crop(apply_command(remapped, command))


def _components(grid):
    points = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0}
    components = []
    while points:
        todo = [points.pop()]
        component = []
        while todo:
            row, col = todo.pop()
            component.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in points:
                    points.remove(neighbor)
                    todo.append(neighbor)
        components.append(component)
    return components


def _strict_facts(grid):
    errors = _valid_grid(grid)
    if errors:
        return errors, None
    height, width = len(grid), len(grid[0])
    command = grid[0][0]
    if command not in range(1, 8):
        errors.append("calibrated command must be an integer from one through seven")
    if grid[0][1] != 0 or grid[1][0] != 0 or grid[1][1] != 0:
        errors.append("reserved header cells (0,1), (1,0), and (1,1) must remain black")
    source_columns = [col for col in range(2, width) if grid[0][col] != 0]
    target_columns = [col for col in range(2, width) if grid[1][col] != 0]
    if source_columns != target_columns or not 2 <= len(source_columns) <= 4:
        errors.append("header must contain two through four aligned source/target pairs")
    if source_columns and source_columns != list(range(2, 2 + len(source_columns))):
        errors.append("mapping pairs must occupy contiguous header columns beginning at column two")
    sources = [grid[0][col] for col in source_columns]
    targets = [grid[1][col] for col in target_columns]
    if len(set(sources)) != len(sources) or len(set(targets)) != len(targets):
        errors.append("source colors and target colors must each be unique")
    if set(sources) & set(targets):
        errors.append("calibrated source and target palettes must be disjoint")
    body = [list(row) for row in grid[2:]]
    cells = [(row, col, value) for row, values in enumerate(body) for col, value in enumerate(values) if value != 0]
    if not cells:
        errors.append("a nonempty object is required below the header")
        return errors, None
    used = {value for _, _, value in cells}
    if used - set(sources):
        errors.append("object cells may use only declared source colors")
    if set(sources) - used:
        errors.append("every declared source color must occur in the object")
    component_count = len(_components(body))
    if not 1 <= component_count <= 6:
        errors.append("calibrated object must form one through six four-connected components")
    rows = [row for row, _, _ in cells]
    cols = [col for _, col, _ in cells]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    object_height, object_width = row1 - row0 + 1, col1 - col0 + 1
    if object_height < 2 or object_width < 2:
        errors.append("calibrated object bounding box must span at least two rows and columns")
    facts = {
        "height": height,
        "width": width,
        "command": command,
        "mapping_count": len(sources),
        "sources": sources,
        "targets": targets,
        "object_cells": len(cells),
        "object_height": object_height,
        "object_width": object_width,
        "object_components": component_count,
        "object_row0": row0 + 2,
        "object_col0": col0,
    }
    if not errors:
        output = rule_mirror(grid)
        if any(value in set(sources) for row in output for value in row):
            errors.append("all source-colored object cells must be remapped to target colors")
    return errors, facts


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def _family_key(facts):
    return facts["command"], facts["mapping_count"], facts["object_height"], facts["object_width"], facts["object_cells"]


def _analysis(grid):
    errors, facts = _strict_facts(grid)
    if errors:
        return {"errors": errors, "facts": facts, "scene_profile": None, "output": None}
    profile = canonical_profile_signature(grid) or _PUBLIC_FAMILIES.get(_family_key(facts)) or _COMMAND_TO_PROFILE[facts["command"]]
    return {"errors": [], "facts": facts, "scene_profile": profile, "output": rule_mirror(grid)}


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    return analysis["scene_profile"] if analysis["scene_profile"] in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {} if analysis["errors"] else {"scene_profile": analysis["scene_profile"]}


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    expected = (meta or {}).get("scene_profile")
    if expected in SCENE_PROFILES and not errors and analysis["scene_profile"] != expected:
        errors.append(f"scene_profile requested {expected!r}, observed {analysis['scene_profile']!r}")
    return errors


def _band_bounds(difficulty):
    return {
        None: ((7, 14), (8, 15), (2, 4), (3, 6)),
        "easy": ((5, 8), (6, 9), (2, 2), (3, 4)),
        "medium": ((8, 12), (9, 13), (2, 3), (3, 5)),
        "hard": ((12, 18), (13, 18), (2, 4), (4, 7)),
    }[difficulty]


def _shape_grid(cells, height, width):
    grid = [[0] * width for _ in range(height)]
    for row, col in cells:
        grid[row][col] = 1
    return grid


def _random_spanning_pattern(rng, height, width, count, command):
    for _ in range(1000):
        cells = set(rng.sample([(row, col) for row in range(height) for col in range(width)], count))
        if min(row for row, _ in cells) or min(col for _, col in cells):
            continue
        if max(row for row, _ in cells) != height - 1 or max(col for _, col in cells) != width - 1:
            continue
        shape = _shape_grid(cells, height, width)
        if len(_components(shape)) > 6:
            continue
        if command != 1 and apply_command(shape, command) == shape:
            continue
        return sorted(cells)
    raise ValueError("could not construct an asymmetric compact spanning object")


def _public_spec(profile):
    key = next(key for key, value in _PUBLIC_FAMILIES.items() if value == profile)
    command, mapping_count, object_height, object_width, object_cells = key
    return command, mapping_count, object_height, object_width, object_cells


def _make_scene(profile, difficulty, rng):
    (height_low, height_high), (width_low, width_high), (pair_low, pair_high), (side_low, side_high) = _band_bounds(difficulty)
    height, width = rng.randint(height_low, height_high), rng.randint(width_low, width_high)
    if profile in PUBLIC_PROFILES:
        command, mapping_count, object_height, object_width, object_cells = _public_spec(profile)
    else:
        command = _PROFILE_TO_COMMAND[profile]
        mapping_count = rng.randint(pair_low, pair_high)
        for _ in range(100):
            object_height = rng.randint(2, min(side_high, height - 2))
            object_width = rng.randint(2, min(side_high, width))
            minimum = max(7, object_height + object_width - 1)
            maximum = object_height * object_width - (command != 1)
            if minimum <= maximum:
                object_cells = rng.randint(minimum, min(maximum, minimum + 4))
                break
        else:
            raise ValueError("could not choose a general object bounding box")
    if height < object_height + 2 or width < max(object_width, mapping_count + 2):
        raise ValueError("difficulty canvas cannot hold the selected profile")
    cells = _random_spanning_pattern(rng, object_height, object_width, object_cells, command)
    palette = rng.sample(range(1, 10), 2 * mapping_count)
    sources, targets = palette[:mapping_count], palette[mapping_count:]
    grid = [[0] * width for _ in range(height)]
    grid[0][0] = command
    for index, (source, target) in enumerate(zip(sources, targets)):
        grid[0][2 + index] = source
        grid[1][2 + index] = target
    row0 = rng.randint(2, height - object_height)
    col0 = rng.randint(0, width - object_width)
    colors = [sources[index % mapping_count] for index in range(object_cells)]
    rng.shuffle(colors)
    for (row, col), color in zip(cells, colors):
        grid[row0 + row][col0 + col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
    if "scene_profile" in overrides and profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _make_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid, difficulty=difficulty, meta={"scene_profile": profile})
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid
